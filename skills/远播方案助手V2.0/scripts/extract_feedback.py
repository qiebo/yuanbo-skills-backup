#!/usr/bin/env python3
"""提取 DOCX 中的批注、修订、高亮和颜色标记，不直接修改 OOXML。"""
from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def text_of(node) -> str:
    return "".join(t.text or "" for t in node.findall(".//w:t", NS))


def main() -> int:
    parser = argparse.ArgumentParser(description="提取 Word 反馈")
    parser.add_argument("docx")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    path = Path(args.docx).expanduser().resolve()
    if not path.exists():
        raise SystemExit(f"文件不存在：{path}")

    result = {"comments": [], "insertions": [], "deletions": [], "highlights": [], "colored_text": []}
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        if "word/comments.xml" in names:
            root = ET.fromstring(z.read("word/comments.xml"))
            for c in root.findall("w:comment", NS):
                result["comments"].append({
                    "id": c.get(W + "id"), "author": c.get(W + "author", ""), "date": c.get(W + "date", ""), "text": text_of(c)
                })
        if "word/document.xml" in names:
            root = ET.fromstring(z.read("word/document.xml"))
            for node in root.findall(".//w:ins", NS):
                result["insertions"].append({"author": node.get(W + "author", ""), "date": node.get(W + "date", ""), "text": text_of(node)})
            for node in root.findall(".//w:del", NS):
                deleted = "".join(t.text or "" for t in node.findall(".//w:delText", NS))
                result["deletions"].append({"author": node.get(W + "author", ""), "date": node.get(W + "date", ""), "text": deleted})
            for run in root.findall(".//w:r", NS):
                txt = text_of(run)
                if not txt:
                    continue
                highlight = run.find("w:rPr/w:highlight", NS)
                color = run.find("w:rPr/w:color", NS)
                if highlight is not None:
                    result["highlights"].append({"color": highlight.get(W + "val"), "text": txt})
                if color is not None:
                    val = color.get(W + "val", "")
                    if val and val.upper() not in {"000000", "AUTO"}:
                        result["colored_text"].append({"color": val, "text": txt})

    out = Path(args.output).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    md = out.with_suffix(".md")
    lines = ["# Word 反馈提取", ""]
    for key, title in [("comments", "批注"), ("insertions", "修订新增"), ("deletions", "修订删除"), ("highlights", "高亮"), ("colored_text", "颜色标记")]:
        lines += [f"## {title}", ""]
        items = result[key]
        if not items:
            lines.append("无。")
        else:
            for i, item in enumerate(items, 1):
                lines.append(f"{i}. {item}")
        lines.append("")
    md.write_text("\n".join(lines), encoding="utf-8")
    print(f"反馈已提取：{out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
