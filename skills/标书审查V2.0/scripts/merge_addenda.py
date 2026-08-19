#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补遗/澄清机械装配 + 冲突提醒脚手架 (V2.0, P2-8).
定位：**只做机械装配 + 冲突提醒**，不做语义法条合并。语义裁决（哪条条款被
修改、新文本为何、哪版生效）由 LLM 在基准提取阶段按「后发布者优先」完成。
本脚本仅提供可审计、可测试、不漏项的拼接/清单/冲突扫描。
Usage:
    python merge_addenda.py --tender output/招标文件.md \
        --addenda output/补遗1.md output/补遗2.md \
        --out output/审查基准_合并输入.md
    python merge_addenda.py --tender output/招标文件.md \
        --addenda-glob "output/补遗*.md" --out output/审查基准_合并输入.md
CLI 顺序（或 glob 排序后）即「发布次序」：越靠后 = 越晚发布 = 优先级越高。
输出（写到 --out，并在 stdout 打印摘要）：
  1) 补遗清单：| 序号 | 文件名 | 次序 | 行数 |
  2) 拼接全文：招标文件全文 + 每份【补遗N·次序M】来源标记 + 补遗全文
  3) 疑似冲突条款清单：机械启发式扫描（只提示"哪里可能冲突"，不裁决、不改写）
仅用 Python 标准库（re / argparse / glob / os）。
"""
import argparse
import glob
import os
import re
# 条款号 / 前附表项 正则（机械命中，不判定语义）
CLAUSE_RE = re.compile(r'第[一二三四五六七八九十百零\d]+条|前附表第.+?项')
# 常见易冲突关键词
KEYWORDS = ['最高限价', '限价', '预算', '控制价', '截止', '递交', '保证金',
            '资格', '签字', '盖章', '有效期', '工期', '交付']
def read_text(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()
def list_addenda(paths):
    """返回 [(seq, filename, order_label, n_lines)]，seq/次序按 CLI/glob 顺序。"""
    items = []
    n = len(paths)
    for i, p in enumerate(paths):
        seq = i + 1
        text = read_text(p)
        n_lines = len(text.splitlines())
        if n == 1:
            order_label = '1'
        elif seq == 1:
            order_label = '1（最先）'
        elif seq == n:
            order_label = f'{seq}（最后·最高优先）'
        else:
            order_label = str(seq)
        items.append((seq, os.path.basename(p), order_label, n_lines, text))
    return items
def render_addenda_list(items):
    out = ['## 补遗清单', '',
           '> 合并规则：补遗/澄清「后发布者优先」；CLI/glob 顺序即发布次序。',
           '',
           '| 序号 | 文件名 | 发布次序 | 行数 |',
           '| --- | --- | --- | --- |']
    for seq, fname, order_label, n_lines, _ in items:
        out.append(f'| {seq} | {fname} | {order_label} | {n_lines} |')
    return '\n'.join(out)
def assemble(tender_text, items):
    """拼接全文：招标文件 + 各补遗（带来源标记），供 LLM 通读裁决。"""
    parts = ['## 拼接全文（招标文件 + 各补遗，按发布次序）', '',
             '### 【招标文件·原始】', '', tender_text.rstrip(), '']
    for seq, fname, order_label, _, text in items:
        parts.append(f'### 【补遗{seq}·次序{order_label}】来源: {fname}')
        parts.append('')
        parts.append(text.rstrip())
        parts.append('')
    return '\n'.join(parts)
def _hits(text):
    """返回文本中命中的条款号与关键词集合。"""
    clauses = set(CLAUSE_RE.findall(text))
    kws = set(kw for kw in KEYWORDS if kw in text)
    return clauses, kws
def scan_conflicts(tender_text, items):
    """疑似冲突条款清单（轻量启发式）。
    对每份补遗，取其命中的条款号/关键词，若同一条款号或关键词也出现在招标文件，
    则视为「疑似被修改条款」，列入清单，附「建议 LLM 按后发优先裁决」。
    只提示可能冲突，不改写、不判定生效版本。
    """
    t_clauses, t_kws = _hits(tender_text)
    conflicts = []
    for seq, fname, order_label, _, text in items:
        a_clauses, a_kws = _hits(text)
        shared_clauses = sorted(a_clauses & t_clauses)
        shared_kws = sorted(a_kws & t_kws)
        for c in shared_clauses:
            conflicts.append((fname, order_label, f'条款号 {c}',
                              '招标文件与本补遗均提及，疑似被修改'))
        for k in shared_kws:
            conflicts.append((fname, order_label, f'关键词「{k}」',
                              '招标文件与本补遗均提及，疑似冲突'))
    return conflicts
def render_conflicts(conflicts):
    out = ['## 疑似冲突条款清单（机械启发式·供裁决参考）', '',
           '> 仅提示"哪里可能冲突"，**不**自动改写条款文本、不判定哪版生效；',
           '> 请 LLM 在基准提取时按「后发布者优先」裁决。', '']
    if not conflicts:
        out.append('（未扫描到疑似冲突条款）')
        return '\n'.join(out), 0
    out.append('| 来源补遗 | 发布次序 | 疑似冲突点 | 说明 |')
    out.append('| --- | --- | --- | --- |')
    for fname, order_label, point, note in conflicts:
        out.append(f'| {fname} | {order_label} | {point} | {note} |')
    return '\n'.join(out), len(conflicts)
def build_report(tender_text, items):
    addenda_list = render_addenda_list(items)
    assembled = assemble(tender_text, items)
    conflicts = scan_conflicts(tender_text, items)
    conflict_block, k = render_conflicts(conflicts)
    report = '\n\n'.join([
        '# 审查基准·合并输入（机械装配，非最终基准）',
        '> 本文件由 merge_addenda.py 机械生成，供 LLM 提取审查基准时通读裁决。'
        '语义合并与「后发优先」裁决由 LLM 完成。',
        addenda_list,
        conflict_block,
        assembled,
    ])
    return report, len(items), k
def main():
    ap = argparse.ArgumentParser(description='补遗/澄清机械装配 + 冲突提醒 (V2.0).')
    ap.add_argument('--tender', required=True, help='招标文件抽取 .md')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--addenda', nargs='+', help='补遗抽取 .md（CLI 顺序=发布次序）')
    g.add_argument('--addenda-glob', help='补遗 glob（排序后=发布次序）')
    ap.add_argument('--out', help='输出 .md（默认 stdout）')
    args = ap.parse_args()
    if args.addenda:
        paths = args.addenda
    else:
        paths = sorted(glob.glob(args.addenda_glob))
    if not paths:
        ap.error('未找到任何补遗文件（--addenda / --addenda-glob 为空）')
    tender_text = read_text(args.tender)
    items = list_addenda(paths)
    report, n_addenda, k = build_report(tender_text, items)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, 'w', encoding='utf-8') as f:
            f.write(report + '\n')
        print(f'[written] {args.out}')
    else:
        print(report)
    print(f'已合并 {n_addenda} 份补遗，疑似冲突 {k} 处')
if __name__ == '__main__':
    main()