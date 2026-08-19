#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HTML 报告渲染 + 占位符残留兜底 (V2.0, P2-13).
定位：**只做 `{{token}}` 字符串替换 + 残留兜底，不生成内容**。各 section 的
HTML 片段由主代理/LLM 拼好塞进 JSON；脚本**绝不静默丢弃**未提供的 token
（缺失即留 `{{}}` 被兜底检出）。
Usage:
    python render_report.py --template assets/report-template.html \
        --data output/report_data.json \
        --out output/终审汇总报告.html [--strict]
report_data.json：JSON 对象，键 = token 名（**不含** 大括号），值 = HTML 片段字符串。
退出码：
    0  无残留占位符（或有残留但未加 --strict）
    2  --strict 且存在残留占位符
仅用 Python 标准库（json / re / argparse / os / sys）。
"""
import argparse
import json
import os
import re
import sys
TOKEN_RE = re.compile(r'\{\{[A-Za-z_]+\}\}')
def find_tokens(text):
    """返回模板中出现的 token 名列表（去重、保持出现顺序）。"""
    seen = []
    for m in TOKEN_RE.findall(text):
        name = m[2:-2]
        if name not in seen:
            seen.append(name)
    return seen
def render(template, data):
    """替换所有 {{key}}；返回 (html, 残留 token 列表)。"""
    html = template
    for key, value in data.items():
        html = html.replace('{{' + key + '}}', '' if value is None else str(value))
    residual = find_tokens(html)
    return html, residual
def main():
    ap = argparse.ArgumentParser(description='HTML 报告渲染 + 残留兜底 (V2.0).')
    ap.add_argument('--template', required=True, help='HTML 模板（含 {{token}}）')
    ap.add_argument('--data', required=True, help='report_data.json（键=token 名）')
    ap.add_argument('--out', required=True, help='输出 HTML')
    ap.add_argument('--strict', action='store_true',
                    help='存在残留占位符时以退出码 2 失败')
    args = ap.parse_args()
    with open(args.template, 'r', encoding='utf-8') as f:
        template = f.read()
    with open(args.data, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, dict):
        print('ERROR: --data 必须是 JSON 对象（键=token 名，值=HTML 片段）',
              file=sys.stderr)
        sys.exit(1)
    expected = find_tokens(template)
    html, residual = render(template, data)
    out_dir = os.path.dirname(os.path.abspath(args.out))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'[template] {len(expected)} 个 token: {", ".join(expected)}')
    unused = [k for k in data if k not in expected]
    if unused:
        print(f'NOTE: data 中有 {len(unused)} 个键未出现在模板: '
              f'{", ".join(sorted(unused))}')
    print(f'[written] {args.out}')
    if residual:
        print(f'WARNING: 未替换占位符: {residual}')
        print(f'WARNING: 共 {len(residual)} 个 token 在 --data 中缺失，'
              f'渲染结果仍含 {{{{}}}} 残留，不可交付。')
        if args.strict:
            sys.exit(2)
    else:
        print('OK: 0 残留占位符')
if __name__ == '__main__':
    main()