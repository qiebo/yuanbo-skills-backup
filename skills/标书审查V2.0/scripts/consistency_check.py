#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cross-file consistency scan for bid/tender review (V1.1).
Usage:
    python consistency_check.py output/a.md output/b.md
    python consistency_check.py --dir output
Scans for suspected inconsistencies across the provided documents:
  - 公司名差异: company-name candidates that differ across files
  - 产品型号变体: model strings that normalise to the same key but differ raw
  - 日期格式: which date formats each file uses, plus simple logic checks
                (future dates, mixed formats across files)
Outputs suspected inconsistencies for human confirmation -- never auto-judges
a violation. Also writes output/机检_一致性.md when writable.
"""
import sys
import os
import re
import argparse
from datetime import datetime
DATE_PATTERNS = {
    "年月日": r'(\d{4})年(\d{1,2})月(\d{1,2})日',
    "横线": r'(\d{4})-(\d{1,2})-(\d{1,2})',
    "斜杠": r'(\d{4})/(\d{1,2})/(\d{1,2})',
    "点分隔": r'(\d{4})\.(\d{1,2})\.(\d{1,2})',
}
COMPANY_RE = re.compile(r'[一-鿿]{2,}(?:公司|有限公司|有限责任公司|集团|厂)')
MODEL_RE = re.compile(r'[A-Za-z]{1,4}[\-\s]?\d{2,}[A-Za-z0-9\-]*')
def norm_model(m):
    return re.sub(r'[\s\-]', '', m).lower()
def parse_date(y, mo, d):
    try:
        return datetime(int(y), int(mo), int(d))
    except ValueError:
        return None
def scan_file(path):
    text = open(path, "r", encoding="utf-8").read()
    companies = set(COMPANY_RE.findall(text))
    models = set(MODEL_RE.findall(text))
    date_fmt = {}
    dates = []
    for name, pat in DATE_PATTERNS.items():
        ms = re.findall(pat, text)
        if ms:
            date_fmt[name] = len(ms)
            for g in ms:
                dt = parse_date(*g)
                if dt:
                    dates.append(dt)
    return {
        "company": companies,
        "model": models,
        "date_fmt": date_fmt,
        "dates": dates,
    }
def fmt_date_set(date_fmt):
    return ", ".join(f"{k}({v})" for k, v in date_fmt.items()) or "无"
def diff(per_file):
    lines = ["# 机检_一致性", ""]
    # 1. company names
    lines.append("## 公司名（按文件）")
    all_companies = set()
    for path, d in per_file:
        lines.append(f"- {os.path.basename(path)}: {', '.join(sorted(d['company'])) or '无'}")
        all_companies |= d['company']
    # cross-file: any company not appearing in every file
    if len(per_file) > 1:
        suspicious = []
        for c in sorted(all_companies):
            present = [os.path.basename(p) for p, d in per_file if c in d['company']]
            if len(present) < len(per_file):
                suspicious.append(f"{c}（仅见于 {', '.join(present)}）")
        if suspicious:
            lines.append("")
            lines.append("**疑似公司名差异**：" + "；".join(suspicious))
    lines.append("")
    # 2. model variants
    lines.append("## 产品型号（按文件）")
    for path, d in per_file:
        lines.append(f"- {os.path.basename(path)}: {', '.join(sorted(d['model'])) or '无'}")
    norm_map = {}
    for path, d in per_file:
        for m in d['model']:
            norm_map.setdefault(norm_model(m), set()).add(m)
    variants = [(k, v) for k, v in norm_map.items() if len(v) > 1]
    if variants:
        lines.append("")
        lines.append("**疑似型号变体**（归一化后相同但原文不同）：")
        for k, v in variants:
            lines.append(f"- {' / '.join(sorted(v))}")
    lines.append("")
    # 3. date formats
    lines.append("## 日期格式（按文件）")
    for path, d in per_file:
        lines.append(f"- {os.path.basename(path)}: {fmt_date_set(d['date_fmt'])}")
    all_dates = [dt for _, d in per_file for dt in d['dates']]
    fmt_names = set()
    for _, d in per_file:
        fmt_names |= set(d['date_fmt'].keys())
    if len(fmt_names) > 1:
        lines.append("")
        lines.append(f"**疑似日期格式混用**：涉及 {', '.join(sorted(fmt_names))}")
    today = datetime.now()
    future = [dt for dt in all_dates if dt > today]
    if future:
        lines.append(f"**疑似未来日期**：{', '.join(dt.strftime('%Y-%m-%d') for dt in sorted(future))}")
    lines.append("")
    return "\n".join(lines)
def main():
    ap = argparse.ArgumentParser(description="Cross-file consistency scan (V1.1).")
    ap.add_argument("files", nargs="*", help="one or more .md files")
    ap.add_argument("--dir", help="scan all .md files in a directory")
    args = ap.parse_args()
    paths = list(args.files)
    if args.dir:
        for fn in sorted(os.listdir(args.dir)):
            if fn.endswith(".md"):
                paths.append(os.path.join(args.dir, fn))
    if not paths:
        print("Usage: consistency_check.py <a.md> <b.md>  |  --dir output")
        sys.exit(1)
    per_file = [(p, scan_file(p)) for p in paths]
    report = diff(per_file)
    print(report)
    out_dir = os.path.dirname(os.path.abspath(paths[0]))
    out_path = os.path.join(out_dir, "机检_一致性.md")
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(report + "\n")
        print(f"\n[written] {out_path}")
    except OSError:
        pass
if __name__ == "__main__":
    main()