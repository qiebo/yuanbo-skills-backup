#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""终审交叉校验：对照基准『明示允许/豁免条款清单』复核子代理报告风险项 (V1.0).
Usage:
    python audit_risks.py --baseline output/审查基准.md --reports output/子代理报告_01.md output/子代理报告_02.md
    python audit_risks.py --baseline output/审查基准.md --reports-dir output
机械列出"允许清单 vs 风险项"对照表，供主代理终审时剔除/降级误判风险项。
本脚本只做机械提示，不自动判定；命中豁免信号词的风险项须由主代理按 R1-R4 人工复核
（命中 ≠ 自动剔除：若存在清单外实质问题如正文参数不达标，仍保留为风险）。
"""
import sys
import os
import re
import argparse

# 豁免句式（用于兜底提取允许清单）：仅"视为/无需/不构成/允许"等豁免语义，避免误抓废标条款
ALLOW_PATTERNS = [
    "视为完全响应", "视为满足", "视为已满足", "视为无偏离",
    "不作无效响应", "不构成无效", "无需提供", "允许空白",
]
# 豁免信号词（用于风险项复核提示）：含裸"完全响应/空白/无偏离"等
SIGNAL_WORDS = ALLOW_PATTERNS + ["完全响应", "信用承诺函", "空白", "无偏离", "无需填写"]


def extract_allowance(baseline_path):
    text = open(baseline_path, "r", encoding="utf-8").read()
    lines = text.splitlines()
    in_section = False
    rows = []
    for ln in lines:
        if re.search(r"##\s*七·五", ln):
            in_section = True
            continue
        if in_section:
            if re.match(r"^##\s", ln):
                break
            if ln.startswith("|") and not re.match(r"^\|\s*-", ln):
                cells = [c.strip() for c in ln.strip("|").split("|")]
                if len(cells) >= 3 and cells[0].strip().isdigit():
                    rows.append((cells[1], cells[2], cells[3] if len(cells) > 3 else ""))
    if rows:
        return rows, "基准 §七·五 表格"
    # 兜底：全文扫描豁免句式
    pat = "|".join(ALLOW_PATTERNS)
    fallback = []
    for m in re.finditer(r"[^。\n]*?(?:%s)[^。\n]*。" % pat, text):
        s = m.group(0).strip()
        if s and s not in fallback:
            fallback.append(s)
    return [("（全文兜底）", s, "（全文扫描）") for s in fallback[:20]], "全文兜底扫描"


def extract_risks(report_path):
    lines = open(report_path, "r", encoding="utf-8").read().splitlines()
    out = []
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith("###") or s.startswith("##") or "标记说明" in s:
            continue
        if ("🔴" in s or "🟠" in s or "【风险】" in s or "【原文】" in s) and s not in out:
            out.append(s)
    return out


def main():
    ap = argparse.ArgumentParser(description="终审交叉校验：允许清单 vs 风险项 (V1.0).")
    ap.add_argument("--baseline", required=True, help="审查基准.md 路径")
    ap.add_argument("--reports", nargs="*", help="子代理报告 .md 路径")
    ap.add_argument("--reports-dir", help="扫描目录下所有 子代理报告_*.md")
    args = ap.parse_args()
    if not os.path.exists(args.baseline):
        print(f"[error] 基准不存在: {args.baseline}")
        sys.exit(1)
    reports = list(args.reports or [])
    if args.reports_dir:
        for fn in sorted(os.listdir(args.reports_dir)):
            if fn.startswith("子代理报告_") and fn.endswith(".md"):
                reports.append(os.path.join(args.reports_dir, fn))
    if not reports:
        print("Usage: audit_risks.py --baseline <基准> --reports <报告...> | --reports-dir output")
        sys.exit(1)

    allowance, src = extract_allowance(args.baseline)
    lines = ["# 机检_终审交叉校验（允许清单 vs 风险项）", ""]
    lines.append(f"## 一、明示允许/豁免条款清单（来源：{src}）")
    if allowance:
        for i, (scope, content, s) in enumerate(allowance, 1):
            lines.append(f"{i}. [{scope}] {content}（{s}）")
    else:
        lines.append("（未找到明示允许/豁免条款，请人工确认基准是否已按模板提取 §七·五）")
    lines.append("")
    lines.append("## 二、风险项复核（命中豁免信号词 → ⚠️ 疑似误判，须主代理按 R1-R4 复核）")
    any_flag = False
    for rp in reports:
        risks = extract_risks(rp)
        if not risks:
            continue
        lines.append(f"### {os.path.basename(rp)}")
        for r in risks:
            hit = [w for w in SIGNAL_WORDS if w in r]
            if hit:
                any_flag = True
                lines.append(f"- ⚠️ 命中信号词[{', '.join(hit)}]：{r}")
            else:
                lines.append(f"- {r}")
        lines.append("")
    if not any_flag:
        lines.append("（未发现命中豁免信号词的风险项；仍请人工逐条核对风险项是否引用招标文件条款依据）")
    report = "\n".join(lines)
    print(report)
    out_dir = os.path.dirname(os.path.abspath(args.baseline))
    out_path = os.path.join(out_dir, "机检_终审交叉校验.md")
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(report + "\n")
        print(f"\n[written] {out_path}")
    except OSError:
        pass


if __name__ == "__main__":
    main()
