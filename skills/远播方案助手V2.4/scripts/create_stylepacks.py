#!/usr/bin/env python3
"""生成 Pandoc reference-doc 样式包。"""
from __future__ import annotations

from pathlib import Path
from io import BytesIO
import shutil
import subprocess

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


def set_font(style, east_asia: str, size: float, bold: bool = False, color: str | None = None):
    style.font.name = east_asia
    style.font.size = Pt(size)
    style.font.bold = bold
    if color:
        style.font.color.rgb = RGBColor.from_string(color)
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.rFonts
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    rfonts.set(qn("w:eastAsia"), east_asia)
    rfonts.set(qn("w:ascii"), "Arial")
    rfonts.set(qn("w:hAnsi"), "Arial")


def find_style(doc: Document, name: str):
    for style in doc.styles:
        if style.name == name:
            return style
    raise KeyError(name)


def ensure_style(doc: Document, name: str, base: str, size: float, bold=False, align=None, color=None, before=0, after=0, line=1.5):
    styles = doc.styles
    try:
        style = find_style(doc, name)
    except KeyError:
        style = styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        style.base_style = find_style(doc, base)
    set_font(style, "微软雅黑", size, bold, color)
    pf = style.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = line
    if align is not None:
        pf.alignment = align
    return style


def make_pack(path: Path, pack: str, default_reference: bytes):
    doc = Document(BytesIO(default_reference))
    section = doc.sections[0]
    section.top_margin = Cm(2.6)
    section.bottom_margin = Cm(2.4)
    section.left_margin = Cm(2.7)
    section.right_margin = Cm(2.5)

    normal = find_style(doc, "Normal")
    set_font(normal, "微软雅黑", 12)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_after = Pt(4)
    normal.paragraph_format.first_line_indent = Pt(24)

    if pack == "government":
        accent = "1F4E79"
        h1_size, h2_size, h3_size = 18, 16, 14
    elif pack == "budget":
        accent = "333333"
        h1_size, h2_size, h3_size = 17, 15, 13
        section.left_margin = section.right_margin = Cm(2.0)
    else:
        accent = "1F4E79"
        h1_size, h2_size, h3_size = 18, 16, 14

    for style_name, size, before, after in [
        ("Title", 26, 0, 18),
        ("Subtitle", 14, 0, 8),
        ("Heading 1", h1_size, 18, 10),
        ("Heading 2", h2_size, 14, 8),
        ("Heading 3", h3_size, 10, 6),
    ]:
        style = find_style(doc, style_name)
        set_font(style, "微软雅黑", size, style_name != "Subtitle", accent if "Heading" in style_name else None)
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.keep_with_next = True
        if style_name in {"Title", "Subtitle"}:
            style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER

    ensure_style(doc, "Cover Title", "Title", 26, True, WD_ALIGN_PARAGRAPH.CENTER, accent, 80, 24, 1.25)
    ensure_style(doc, "Cover Client", "Subtitle", 16, False, WD_ALIGN_PARAGRAPH.CENTER, None, 20, 8, 1.25)
    ensure_style(doc, "Cover Meta", "Subtitle", 12, False, WD_ALIGN_PARAGRAPH.CENTER, None, 8, 4, 1.25)
    ensure_style(doc, "Table Caption", "Normal", 10.5, True, WD_ALIGN_PARAGRAPH.CENTER, None, 8, 4, 1.0)
    ensure_style(doc, "Image Caption", "Normal", 10.5, False, WD_ALIGN_PARAGRAPH.CENTER, None, 4, 8, 1.0)

    table_style = find_style(doc, "Table")
    set_font(table_style, "微软雅黑", 9.5)

    doc.core_properties.title = "远播方案助手参考样式"
    doc.core_properties.subject = pack
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(path)


def main():
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise SystemExit("生成样式包需要 Pandoc。")
    default_reference = subprocess.check_output([pandoc, "--print-default-data-file", "reference.docx"])
    root = Path(__file__).resolve().parents[1] / "stylepacks"
    make_pack(root / "学校建设方案版.docx", "school", default_reference)
    make_pack(root / "政府申报正式版.docx", "government", default_reference)
    make_pack(root / "预算配置简洁版.docx", "budget", default_reference)
    print(f"已生成样式包：{root}")


if __name__ == "__main__":
    main()
