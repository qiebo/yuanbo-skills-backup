#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract a .docx into structured Markdown for bid/tender review.

Usage:
    python extract_docx.py <input.docx> [output.md]

Design notes (built from real bid-review experience):
- Preserves Heading / Title styles as Markdown '#'..'######' so the reviewer
  can navigate the document structure.
- Tables are emitted as Markdown tables.
- Paragraphs/sections that contain an image (certificates, screenshots, seals,
  contracts, PPT) are flagged with an [IMAGE] marker, because such evidence is
  NOT readable as text and MUST be verified against the original file.
"""
import sys
import os
from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph


def iter_block_items(parent):
    """Yield (kind, item) for paragraphs and tables in document order."""
    body = parent.element.body
    for child in body.iterchildren():
        if child.tag == qn('w:p'):
            yield ('p', Paragraph(child, parent))
        elif child.tag == qn('w:tbl'):
            yield ('t', Table(child, parent))


def style_level(p):
    """Return heading level (1-6) for heading/title styles, else None."""
    try:
        s = p.style.name
    except Exception:
        return None
    if not s:
        return None
    if s == 'Title' or s == '标题':
        return 1
    if 'Heading' in s or '标题' in s:
        digits = ''.join(ch for ch in s if ch.isdigit())
        return int(digits) if digits else 2
    return None


def has_image(para):
    """Detect inline drawing (image) inside a paragraph."""
    if para._element.find('.//' + qn('w:drawing')) is not None:
        return True
    for run in para.runs:
        if run._element.find(qn('w:drawing')) is not None:
            return True
    return False


def table_to_md(table):
    rows = table.rows
    if not rows:
        return ""
    out = []
    hdr = [c.text.strip().replace("\n", " ") for c in rows[0].cells]
    out.append("| " + " | ".join(hdr) + " |")
    out.append("|" + "|".join(["---"] * len(hdr)) + "|")
    for r in rows[1:]:
        cells = [c.text.strip().replace("\n", " ") for c in r.cells]
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def extract(docx_path, out_path=None):
    doc = Document(docx_path)
    lines = []
    img_count = 0
    for kind, item in iter_block_items(doc):
        if kind == 'p':
            txt = item.text.strip()
            lvl = style_level(item)
            if lvl:
                lines.append("\n" + "#" * min(lvl, 6) + " " + txt)
            elif txt:
                lines.append(txt)
            if has_image(item):
                lines.append("> [IMAGE] 本节含图片证据（如证书/截图/签章/合同/PPT），文本无法读取，需核对原件")
                img_count += 1
        else:
            lines.append("\n[TABLE]")
            lines.append(table_to_md(item))
            lines.append("[/TABLE]\n")

    content = "\n".join(lines).strip() + "\n"
    if out_path:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Extracted -> {out_path} ({len(content)} chars, ~{img_count} image paragraphs)")
    else:
        print(content)
    return content


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_docx.py <input.docx> [output.md]")
        sys.exit(1)
    inp = sys.argv[1]
    outp = sys.argv[2] if len(sys.argv) > 2 else None
    extract(inp, outp)
