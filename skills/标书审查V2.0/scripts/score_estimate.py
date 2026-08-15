#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""评分量化与保守估分 (V2.0, P2-9).

定位：**辅助保守估分**，不是自动评标。四条硬边界（实现与输出均遵守）：
  ① 任何定位不到的项记 `?` 或 `0`，**绝不臆造分值**；
  ② 主观分只给区间、明标不确定性；
  ③ 输出顶部固定免责声明；
  ④ 报价项复用 verify_prices.py 的价格机检结论，不让 LLM 心算。

Usage:
    python score_estimate.py --baseline output/审查基准.md \
        --docs output/响应文件_01.md output/响应文件_02.md \
        [--out output/评分估算.md] [--limit 650000]

单元格取值：
    X     客观项保守点估（有材料，按 max*0.8 保守成数）
    X~Y   主观项区间估（max*0.5 ~ max*0.8，不确定性高）
    0     零分风险（未见材料 / 报价超限）
    ?     UNKNOWN（证据仅为图片、或价格机检未定位）——需核对原件，不臆断

仅用 Python 标准库；复用同目录 verify_prices 的 extract_md_tables / parse_num / check。
"""
import argparse
import os
import re
import sys

# 复用同目录 verify_prices 的纯函数（Markdown 表格解析 + 价格机检）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify_prices  # noqa: E402
from verify_prices import extract_md_tables, parse_num  # noqa: E402

DISCLAIMER = (
    '> **免责声明 / 保守估分原则**：本表为机械辅助**保守估分**，'
    '**非评标结论**，最终得分以评标/磋商小组评审为准。\n'
    '> 有材料按保守成数估（max*0.8）；无材料记 `0`；'
    '证据仅为图片或不可定位记 `?`（需核对原件，**不臆断**）；'
    '主观分只给区间（max*0.5~max*0.8）并标注不确定性；'
    '报价项以 verify_prices 价格机检结论为准。'
)

# 评分标准表 表头候选关键词
HEADER_KEYS = ['评审项', '评分项', '评审内容', '评审因素', '评分标准',
               '得分标准', '分值', '权重']
MAX_RE = re.compile(r'分值|满分|标准分|分数')
WEIGHT_RE = re.compile(r'权重')
CRITERIA_RE = re.compile(r'评分标准|得分标准|评审标准')

# 分类关键词
PRICE_KW = ['报价', '投标报价', '价格']
OBJECTIVE_KW = ['资质', '证书', '业绩', '人员', '社保', '纳税', '授权', '合同']
SUBJECTIVE_KW = ['方案', '实施', '服务', '培训', '售后', '整体', '技术']

T_PRICE = '报价'
T_OBJ = '客观证据'
T_SUBJ = '主观'
T_UNKNOWN = 'UNKNOWN'


def parse_max(s):
    """解析满分，支持 `X-Y` / `X～Y` / `X至Y` 区间（取上界）。取不到返回 None。"""
    if s is None:
        return None
    t = str(s).replace('分', '').replace(' ', '').strip()
    if not t:
        return None
    parts = re.split(r'[-~～—–至]', t)
    parts = [p for p in parts if p.strip()]
    if len(parts) >= 2:
        return parse_num(parts[-1])
    return parse_num(t)


def fmt_num(v):
    """整数显示为整数，否则最多 2 位小数并去掉尾随 0（不得损失权重精度）。"""
    if v is None:
        return '?'
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f'{v:.2f}'.rstrip('0').rstrip('.')


# ---------------------------------------------------------------- 解析评分标准表

def pick_scoring_table(baseline_text):
    """在所有 Markdown 表中选评分标准表：表头命中关键词，多候选取行数最多者。"""
    best = None
    for header, rows, line0 in extract_md_tables(baseline_text):
        if not any(any(k in h for k in HEADER_KEYS) for h in header):
            continue
        data_rows = [r for r in rows if any(c.strip() for c in r)]
        if not data_rows:
            continue
        if best is None or len(data_rows) > len(best[1]):
            best = (header, data_rows, line0)
    return best


def classify(name, criteria):
    blob = f'{name} {criteria}'
    if any(k in blob for k in PRICE_KW):
        return T_PRICE
    hit_obj = [k for k in OBJECTIVE_KW if k in blob]
    if hit_obj:
        return T_OBJ
    if any(k in blob for k in SUBJECTIVE_KW):
        return T_SUBJ
    return T_SUBJ


def search_terms(name, criteria, kind):
    """搜索词 = 分项名 + 该类别在 name/criteria 中命中的关键词（机械派生）。"""
    blob = f'{name} {criteria}'
    terms = [name.strip()] if name.strip() else []
    pool = OBJECTIVE_KW if kind == T_OBJ else SUBJECTIVE_KW
    for k in pool:
        if k in blob and k not in terms:
            terms.append(k)
    return terms


def parse_scoring(baseline_text):
    """返回 (items, table_line) ；item = dict(name,max,weight,criteria,kind,terms)."""
    picked = pick_scoring_table(baseline_text)
    if picked is None:
        return [], None
    header, rows, line0 = picked

    max_idx = weight_idx = criteria_idx = None
    for i, h in enumerate(header):
        if max_idx is None and MAX_RE.search(h):
            max_idx = i
        elif weight_idx is None and WEIGHT_RE.search(h):
            weight_idx = i
        elif criteria_idx is None and CRITERIA_RE.search(h):
            criteria_idx = i
    # 分项名 = 首个非 分值/权重/评分标准 的列
    taken = {max_idx, weight_idx, criteria_idx}
    name_idx = next((i for i in range(len(header)) if i not in taken), 0)

    def cell(row, idx):
        if idx is None or idx >= len(row):
            return ''
        return row[idx].strip()

    items = []
    for r in rows:
        name = cell(r, name_idx)
        if not name or re.search(r'合计|总计|总分', name):
            continue
        criteria = cell(r, criteria_idx)
        mx = parse_max(cell(r, max_idx))
        wt = parse_num(cell(r, weight_idx)) if weight_idx is not None else None
        kind = classify(name, criteria) if mx is not None else T_UNKNOWN
        items.append({
            'name': name,
            'max': mx,
            'weight': wt,
            'criteria': criteria,
            'kind': kind,
            'terms': search_terms(name, criteria, kind) if mx is not None else [],
        })
    return items, line0


# ---------------------------------------------------------------- 逐项估分

HEADING_RE = re.compile(r'^\s{0,3}#{1,6}\s')


def find_term_lines(doc_text, terms):
    """返回 (body_hits, image_hits, heading_hits)，元素为 (lineno, line, term)。

    三类分开，是因为**章节标题不是材料证据**（铁律 2：严禁因「文件里有这一章」
    就默认合规）。仅标题命中 → UNKNOWN，不得按「材料齐」给分。
    """
    body, image, heading = [], [], []
    for i, line in enumerate(doc_text.splitlines(), 1):
        for t in terms:
            if t and t in line:
                rec = (i, line.strip(), t)
                if '[IMAGE:' in line:
                    image.append(rec)
                elif HEADING_RE.match(line):
                    heading.append(rec)
                else:
                    body.append(rec)
                break
    return body, image, heading


def price_verdict(doc_text, baseline_text, cli_limit):
    """取 verify_prices 的「总报价≤限价」结论：PASS / FAIL / UNKNOWN + 数值。"""
    try:
        results = verify_prices.check(doc_text, baseline_text, cli_limit)
    except Exception as e:  # 机检异常 -> UNKNOWN，绝不臆断
        return 'UNKNOWN', f'价格机检异常：{e}'
    for name, verdict, val, src in results:
        if '限价' in name:
            return verdict, f'{val}（{src}）'
    return 'UNKNOWN', '价格机检未返回限价结论'


def estimate_item(item, doc_text, baseline_text, cli_limit):
    """返回 dict(cell, low, high_for_total, zero, note)。绝不臆造分值。"""
    mx = item['max']
    kind = item['kind']
    if mx is None or kind == T_UNKNOWN:
        return {'cell': '?', 'low': 0.0, 'cap': 0.0, 'zero': False,
                'note': '评分标准未解析出满分，记 ?（不臆断）'}

    if kind == T_PRICE:
        verdict, detail = price_verdict(doc_text, baseline_text, cli_limit)
        if verdict == 'PASS':
            v = round(mx * 0.9, 1)
            return {'cell': fmt_num(v), 'low': v, 'cap': mx, 'zero': False,
                    'note': f'价格机检 PASS：{detail}；近满分保守估（max*0.9）'}
        if verdict == 'FAIL':
            return {'cell': '0', 'low': 0.0, 'cap': 0.0, 'zero': True,
                    'note': f'价格机检 FAIL（报价超限→可能 0 分）：{detail}'}
        return {'cell': '?', 'low': 0.0, 'cap': 0.0, 'zero': False,
                'note': f'价格机检 UNKNOWN，记 ?（不臆断）：{detail}'}

    body, image, heading = find_term_lines(doc_text, item['terms'])
    terms_s = '/'.join(item['terms'])

    if not (body or image or heading):
        return {'cell': '0', 'low': 0.0, 'cap': 0.0, 'zero': True,
                'note': f'未见材料（搜索词 {terms_s} 全文未命中）→ 可能得 0 分'}

    if not body:
        # 只有图片证据、或只有章节标题命中 —— 两者都不足以判定「已满足」
        if image:
            return {'cell': '?', 'low': 0.0, 'cap': 0.0, 'zero': False,
                    'note': f'证据仅为图片（L{image[0][0]}），需核对原件，'
                            f'记 ?（不臆断）'}
        return {'cell': '?', 'low': 0.0, 'cap': 0.0, 'zero': False,
                'note': f'仅章节标题命中（L{heading[0][0]}「{heading[0][2]}」），'
                        f'正文未见实质内容；按铁律 2 不得因「有这一章」默认合规，'
                        f'记 ?（需核对原件）'}

    where = '、'.join(f'L{n}「{t}」' for n, _, t in body[:3])
    if image:
        where += f'（另有图片证据 L{image[0][0]}，需核对原件）'
    if kind == T_OBJ:
        v = round(mx * 0.8, 1)
        return {'cell': fmt_num(v), 'low': v, 'cap': mx, 'zero': False,
                'note': f'正文有材料（命中 {where}），保守 8 成估；实际以评标为准'}
    lo = round(mx * 0.5, 1)
    hi = round(mx * 0.8, 1)
    return {'cell': f'{fmt_num(lo)}~{fmt_num(hi)}', 'low': lo, 'cap': hi,
            'zero': False,
            'note': f'主观分（命中 {where}），估分区间 50%~80%，不确定性高'}


# ---------------------------------------------------------------- 渲染

def render(items, docs, est, table_line):
    labels = [os.path.basename(d) for d in docs]
    out = ['# 评分估算（多份响应文件）', '', DISCLAIMER, '']

    out.append('## 评分标准解析')
    out.append('')
    if not items:
        out.append('**未能在审查基准中定位「评分标准」表** —— 全部分项记 `?`，'
                   '请人工补充评分标准表（表头需含 分项/分值[/权重/评分标准]）。')
        out.append('')
    else:
        out.append(f'> 来源：审查基准 Markdown 表 @L{table_line}'
                   f'（表头关键词命中，多候选取行数最多者）')
        out.append('')
        out.append('| 分项 | 满分 | 权重 | 类型 | 评分标准(摘要) |')
        out.append('| --- | --- | --- | --- | --- |')
        for it in items:
            brief = (it['criteria'] or '')[:40].replace('|', '/')
            out.append(f'| {it["name"]} | {fmt_num(it["max"])} | '
                       f'{fmt_num(it["weight"]) if it["weight"] is not None else "-"} | '
                       f'{it["kind"]} | {brief} |')
        if all(it['weight'] is None for it in items):
            out.append('')
            out.append('> 权重列缺失：按分值等权估算（不臆造权重）。')
        out.append('')

    out.append('## 得分对比')
    out.append('')
    out.append('| 分项 | 满分 | ' + ' | '.join(labels) + ' |')
    out.append('| --- | --- | ' + ' | '.join(['---'] * len(labels)) + ' |')
    for idx, it in enumerate(items):
        cells = [est[d][idx]['cell'] for d in docs]
        out.append(f'| {it["name"]} | {fmt_num(it["max"])} | ' + ' | '.join(cells) + ' |')
    total_max = sum(it['max'] for it in items if it['max'] is not None)
    totals = []
    for d in docs:
        low = sum(e['low'] for e in est[d])
        cap = sum(e['cap'] for e in est[d])
        totals.append(f'{fmt_num(low)}~{fmt_num(cap)}')
    out.append(f'| **总分区间** | {fmt_num(total_max)} | ' + ' | '.join(totals) + ' |')
    out.append('')
    out.append('> 总分区间 = 保守下界（`0`/`?` 均记 0）~ 理论上界'
               '（仅计非 `0`、非 `?` 项的满分/区间上界）。')
    out.append('')

    out.append('## 零分项预警')
    out.append('')
    any_zero = False
    for d in docs:
        zeros = [(items[i]['name'], e['note'])
                 for i, e in enumerate(est[d]) if e['zero']]
        if zeros:
            any_zero = True
            detail = '；'.join(f'**{n}**（{note}）' for n, note in zeros)
            out.append(f'- {os.path.basename(d)}：{detail}')
    if not any_zero:
        out.append('- （未发现估为 0 分的分项）')
    out.append('')

    out.append('## 估分说明与不确定性')
    out.append('')
    out.append('- 报价项以 `verify_prices.py` 价格机检结论为准（PASS→近满分 max*0.9；'
               'FAIL→0；UNKNOWN→`?`），不由本脚本心算价格。')
    out.append('- 客观证据类（资质/证书/业绩/人员/社保/纳税/授权/合同）：'
               '正文命中→保守 8 成估；全文未命中→`0`；仅图片承载→`?` 需核对原件。')
    out.append('- **章节标题命中不算材料证据**（铁律 2：严禁因「文件里有这一章」'
               '就默认合规）：仅标题命中的分项记 `?`，需核对原件。')
    out.append('- 主观类（方案/实施/服务/培训/售后/整体/技术）：只给 50%~80% 区间，'
               '不确定性高，实际以评标小组打分为准。')
    out.append('- 权重缺失时按分值等权估算；满分解析失败的分项记 `?` 并排除出总分上限。')
    out.append('- **每个非零估分均附命中行号与搜索词**，便于人工回读原文审计'
               '（机械关键词命中可能误判，请以原文为准）。')
    out.append('')

    out.append('### 逐项估分依据（可审计）')
    out.append('')
    for d in docs:
        out.append(f'**{os.path.basename(d)}**')
        out.append('')
        out.append('| 分项 | 估分 | 依据 / 不确定性 |')
        out.append('| --- | --- | --- |')
        for i, e in enumerate(est[d]):
            out.append(f'| {items[i]["name"]} | {e["cell"]} | '
                       f'{e["note"].replace("|", "/")} |')
        out.append('')
    return '\n'.join(out)


def main():
    ap = argparse.ArgumentParser(description='评分量化与保守估分 (V2.0).')
    ap.add_argument('--baseline', required=True, help='审查基准 .md（含评分标准表）')
    ap.add_argument('--docs', nargs='+', required=True, help='1~N 份响应文件抽取 .md')
    ap.add_argument('--out', help='输出 .md（默认 stdout）')
    ap.add_argument('--limit', type=float, default=None,
                    help='最高限价（覆盖 baseline 解析，透传 verify_prices）')
    args = ap.parse_args()

    with open(args.baseline, 'r', encoding='utf-8') as f:
        baseline_text = f.read()

    items, table_line = parse_scoring(baseline_text)

    est = {}
    for d in args.docs:
        with open(d, 'r', encoding='utf-8') as f:
            doc_text = f.read()
        est[d] = [estimate_item(it, doc_text, baseline_text, args.limit)
                  for it in items]

    report = render(items, args.docs, est, table_line)

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, 'w', encoding='utf-8') as f:
            f.write(report + '\n')
        print(f'[written] {args.out}')
    else:
        print(report)

    n_zero = sum(1 for d in args.docs for e in est[d] if e['zero'])
    n_unk = sum(1 for d in args.docs for e in est[d] if e['cell'] == '?')
    print(f'已估算 {len(args.docs)} 份响应文件 × {len(items)} 个评分分项，'
          f'零分风险 {n_zero} 处，UNKNOWN {n_unk} 处')


if __name__ == '__main__':
    main()
