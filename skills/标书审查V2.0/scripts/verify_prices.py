#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mechanical price / consistency checks for bid/tender review (V1.1).
Usage:
    python verify_prices.py --baseline output/审查基准.md --doc output/<响应>.md [--limit 650000]
Three checks (numbers, not LLM arithmetic):
  1. 明细合计 = 一览表总价   (detail table amount column sum == headline total)
  2. 总报价 <= 限价          (total <= limit; --limit overrides baseline parse)
  3. 大小写一致              (Chinese uppercase amount == Arabic lowercase amount)
Each check prints PASS / FAIL / UNKNOWN with the values and source line numbers.
UNKNOWN means the value could not be located -- never assume PASS.
Output is also written to output/机检_价格.md when an output dir is writable.
"""
import sys
import os
import re
import argparse
def parse_num(s):
    if s is None:
        return None
    s = s.replace(',', '').replace('，', '').replace(' ', '').strip()
    try:
        return float(s)
    except ValueError:
        return None
CN_DIGITS = {
    '零': 0, '〇': 0, '0': 0,
    '一': 1, '壹': 1, '1': 1,
    '二': 2, '贰': 2, '两': 2, '2': 2,
    '三': 3, '叁': 3, '3': 3,
    '四': 4, '肆': 4, '4': 4,
    '五': 5, '伍': 5, '5': 5,
    '六': 6, '陆': 6, '6': 6,
    '七': 7, '柒': 7, '7': 7,
    '八': 8, '捌': 8, '8': 8,
    '九': 9, '玖': 9, '9': 9,
}
CN_UNITS = {
    '十': 10, '拾': 10,
    '百': 100, '佰': 100,
    '千': 1000, '仟': 1000,
    '万': 10000, '萬': 10000,
    '亿': 100000000, '億': 100000000,
}
def parse_amount_cn(cn):
    """Parse a Chinese uppercase amount (with 元/角/分) to a float, or None.
    Accumulates by position: 拾/佰/仟 multiply into the current integer section,
    万/亿 roll the section up; 元 finalises the integer part; 角 (×0.1) and
    分 (×0.01) add directly to the decimal part. Handles 零/整 and mixed
    integer+decimal forms (e.g. 壹拾贰元叁角肆分 -> 12.34).
    """
    if cn is None:
        return None
    s = re.sub(r'[¥￥\s]', '', cn)
    s = re.sub(r'人民币|圆|整|正|（|）|\(|\)', '', s)
    int_total = int_section = int_num = 0
    decimal = 0.0
    for ch in s:
        if ch == '元':
            int_total += int_section + int_num
            int_section = 0
            int_num = 0
        elif ch in CN_DIGITS:
            int_num = int_num * 10 + CN_DIGITS[ch]
        elif ch in CN_UNITS:
            u = CN_UNITS[ch]
            if u < 10000:
                int_section += (int_num if int_num > 0 else 1) * u
                int_num = 0
            elif u == 10000:
                int_section = (int_section + int_num) * u
                int_num = 0
            elif u >= 100000000:
                int_total += (int_section + int_num) * u
                int_section = 0
                int_num = 0
        elif ch == '角':
            decimal += (int_num if int_num > 0 else 0) * 0.1
            int_num = 0
        elif ch == '分':
            decimal += (int_num if int_num > 0 else 0) * 0.01
            int_num = 0
    total = int_total + decimal + int_section + int_num
    return total if total > 0 else None
def split_row(line):
    line = line.strip()
    if line.startswith('|'):
        line = line[1:]
    if line.endswith('|'):
        line = line[:-1]
    return [c.strip() for c in line.split('|')]
def extract_md_tables(md):
    lines = md.splitlines()
    tables = []
    i = 0
    while i < len(lines):
        if (lines[i].strip().startswith('|') and i + 1 < len(lines)
                and '-' in lines[i + 1]
                and re.match(r'^\s*\|?[\s:|-]+\|?\s*$', lines[i + 1])):
            header = split_row(lines[i])
            rows = []
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith('|'):
                rows.append(split_row(lines[j]))
                j += 1
            tables.append((header, rows, i + 1))
            i = j
        else:
            i += 1
    return tables
def find_amount_column(header):
    for idx, h in enumerate(header):
        if re.search(r'小计|金额|合计|单价|报价|价格|费用|总价|预算', h):
            return idx
    return None
def sum_detail_tables(md):
    best = None
    for header, rows, line0 in extract_md_tables(md):
        ci = find_amount_column(header)
        if ci is None:
            continue
        total = 0.0
        cnt = 0
        for r in rows:
            if ci >= len(r):
                continue
            first = r[0].strip()
            if re.search(r'合计|总计|小计', first):
                continue
            v = parse_num(r[ci])
            if v is not None:
                total += v
                cnt += 1
        if cnt > 0 and (best is None or cnt > best[2]):
            best = (total, line0, cnt)
    if best is None:
        return None, None, 0
    return best[0], best[1], best[2]
def find_total(md):
    pats = [
        r'投标总报价[^\n]*?[¥￥]?\s*([\d,]+\.?\d*)',
        r'报价一览表[^\n]*?[¥￥]?\s*([\d,]+\.?\d*)',
        r'总报价[^\n]*?[¥￥]?\s*([\d,]+\.?\d*)',
    ]
    for i, line in enumerate(md.splitlines(), 1):
        for p in pats:
            m = re.search(p, line)
            if m:
                v = parse_num(m.group(1))
                if v is not None:
                    return v, i, line.strip()
    return None, None, None
def find_uppercase(md):
    m = re.search(r'大写.{0,8}?[：:]\s*(?:人民币)?\s*([零一二三四五六七八九壹贰叁肆伍陆柒捌玖拾佰仟万亿万〇两0-9元圆整角分]+)',
                  md)
    if m:
        line = md[:m.start()].count('\n') + 1
        return parse_amount_cn(m.group(1)), line
    return None, None
def find_lowercase(md):
    m = re.search(r'小写.{0,8}?[：:]\s*[¥￥]?\s*([\d,]+\.?\d*)', md)
    if m:
        line = md[:m.start()].count('\n') + 1
        return parse_num(m.group(1)), line
    return None, None
# 限价裁决/调整词：基准中若写明「最高限价：650000 元（经补遗第2号调减为
# 600000 元）」，限价关键词后的第一个数字是**过期旧值**；须取最后一次裁决词
# 后的数字（后发布者优先），否则超裁决限价的报价会被静默误判 PASS。
_ADJUDICATE_RE = re.compile(
    r'(?:调减为|调增为|调整为|更正为|修改为|改为|顺延至|确定为|更新为|最终以|最终为)'
    r'[^\d]{0,15}[¥￥]?\s*([\d,]+\.?\d*)')
def find_limit(baseline_text, cli_limit):
    if cli_limit is not None:
        return cli_limit, None, "CLI --limit"
    if not baseline_text:
        return None, None, None
    limit_kw = re.compile(r'(?:最高限价|预算|采购预算|控制价)')
    for i, line in enumerate(baseline_text.splitlines(), 1):
        if not limit_kw.search(line):
            continue
        cands = list(_ADJUDICATE_RE.finditer(line))
        v = None
        if cands:
            v = parse_num(cands[-1].group(1))
        else:
            m = re.search(r'(?:最高限价|预算|采购预算|控制价)[^\n]*?[¥￥]?\s*([\d,]+\.?\d*)', line)
            if m:
                v = parse_num(m.group(1))
        if v is not None:
            return v, i, line.strip()
    return None, None, None
def check(doc_text, baseline_text, cli_limit):
    results = []
    dsum, dline, dcnt = sum_detail_tables(doc_text)
    total, tline, tline_txt = find_total(doc_text)
    if dsum is not None and total is not None:
        ok = abs(dsum - total) <= 0.01
        results.append((
            "明细合计=一览表总价",
            "PASS" if ok else "FAIL",
            f"明细合计={dsum:g} 一览表总价={total:g} 差异={dsum - total:g}",
            f"明细@L{dline} 总价@L{tline}",
        ))
    else:
        results.append((
            "明细合计=一览表总价", "UNKNOWN",
            "未定位明细表或一览表总价",
            f"明细={'有' if dsum is not None else '无'} 总价={'有' if total is not None else '无'}",
        ))
    limit, lline, lsrc = find_limit(baseline_text, cli_limit)
    if total is not None and limit is not None:
        ok = total <= limit
        lsrc_s = f"L{lline}" if lline else str(lsrc)
        results.append((
            "总报价≤限价",
            "PASS" if ok else "FAIL",
            f"总报价={total:g} 限价={limit:g}",
            f"总价@L{tline} 限价@{lsrc_s}",
        ))
    else:
        results.append((
            "总报价≤限价", "UNKNOWN",
            "未定位总报价或限价",
            f"总价={'有' if total is not None else '无'} 限价={'有' if limit is not None else '无'}",
        ))
    upper, uline = find_uppercase(doc_text)
    lower, lline2 = find_lowercase(doc_text)
    if upper is not None and lower is not None:
        tol = max(1.0, abs(upper) * 0.001)
        ok = abs(upper - lower) <= tol
        results.append((
            "大小写一致",
            "PASS" if ok else "FAIL",
            f"大写={upper:g} 小写={lower:g}",
            f"大写@L{uline} 小写@L{lline2}",
        ))
    else:
        results.append((
            "大小写一致", "UNKNOWN",
            "未定位大写或小写金额",
            f"大写={'有' if upper is not None else '无'} 小写={'有' if lower is not None else '无'}",
        ))
    return results
def render(results):
    out = ["# 机检_价格", "", "| 检查项 | 结论 | 数值 | 依据 |", "| --- | --- | --- | --- |"]
    overall = "PASS"
    for name, verdict, val, src in results:
        if verdict == "FAIL":
            overall = "FAIL"
        elif verdict == "UNKNOWN" and overall == "PASS":
            overall = "UNKNOWN"
        out.append(f"| {name} | **{verdict}** | {val} | {src} |")
    out.append("")
    out.append(f"总体结论： **{overall}**")
    return "\n".join(out)
def main():
    ap = argparse.ArgumentParser(description="Mechanical price checks (V1.1).")
    ap.add_argument("--baseline", help="审查基准 .md (for limit)")
    ap.add_argument("--doc", required=True, help="响应文件抽取 .md")
    ap.add_argument("--limit", type=float, default=None, help="最高限价 (覆盖 baseline 解析)")
    args = ap.parse_args()
    doc_text = open(args.doc, "r", encoding="utf-8").read()
    baseline_text = open(args.baseline, "r", encoding="utf-8").read() if args.baseline else ""
    results = check(doc_text, baseline_text, args.limit)
    report = render(results)
    print(report)
    out_path = os.path.join(os.path.dirname(os.path.abspath(args.doc)), "机检_价格.md")
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(report + "\n")
        print(f"\n[written] {out_path}")
    except OSError:
        pass
    if any(v == "FAIL" for _, v, _, _ in results):
        sys.exit(2)
if __name__ == "__main__":
    main()