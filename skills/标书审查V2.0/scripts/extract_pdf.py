#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract a .pdf into structured Markdown for bid/tender review (V1.1).
Usage:
    python extract_pdf.py <input.pdf> [output.md] [--extract-images] [--image-dir output/images]
Uses pdfplumber. Preserves heading hierarchy (inferred from font size), tables,
and exports images as `[IMAGE: images/<safe>/img_NNN.png]` markers, matching the
docx extractor's output style so the same downstream pipeline can consume both.
"""
import sys
import os
import argparse
import hashlib
import pdfplumber
def median_font(pdf):
    sizes = []
    for page in pdf.pages:
        for c in page.chars:
            if c.get('size'):
                sizes.append(c['size'])
    if not sizes:
        return 10.0
    sizes.sort()
    return sizes[len(sizes) // 2]
def font_size_of_line(chars):
    sizes = [c.get('size') or 0 for c in chars if c.get('size')]
    return max(sizes) if sizes else 0
def heading_level(size, body_size):
    if size >= body_size * 1.5:
        return 1
    if size >= body_size * 1.25:
        return 2
    if size >= body_size * 1.1:
        return 3
    return None
def group_lines(chars, tol=1.0):
    """Group chars into visual lines ordered by (top, x0)."""
    if not chars:
        return []
    schars = sorted(chars, key=lambda c: (round(c['top']), c['x0']))
    lines = []
    cur = [schars[0]]
    cur_top = schars[0]['top']
    for c in schars[1:]:
        if abs(c['top'] - cur_top) <= tol:
            cur.append(c)
        else:
            lines.append(cur)
            cur = [c]
            cur_top = c['top']
    lines.append(cur)
    return lines
def table_to_md(tbl):
    if not tbl:
        return ""
    out = []
    for i, row in enumerate(tbl):
        cells = [(c or "").replace("\n", " ").replace("|", "\\|").strip() for c in row]
        out.append("| " + " | ".join(cells) + " |")
        if i == 0:
            out.append("|" + "|".join(["---"] * max(len(cells), 1)) + "|")
    return "\n".join(out)
def in_any_table(chars, bboxes):
    """True if every char of the line sits inside some table bbox."""
    if not bboxes or not chars:
        return False
    for c in chars:
        inside = False
        for (x0, top, x1, bottom) in bboxes:
            if c['x0'] >= x0 and c['top'] >= top and c['x1'] <= x1 and c['bottom'] <= bottom:
                inside = True
                break
        if not inside:
            return False
    return True
def extract(pdf_path, out_path=None, extract_images=False, image_dir="output/images"):
    lines = []
    with pdfplumber.open(pdf_path) as pdf:
        body = median_font(pdf)
        stem = os.path.splitext(os.path.basename(pdf_path))[0]
        # Hash the source absolute path so images of two different files that
        # share a base name land in separate subdirs instead of overwriting
        # each other (mirrors extract_docx.py).
        safe = stem + "_" + hashlib.md5(os.path.abspath(pdf_path).encode("utf-8")).hexdigest()[:6]
        counter = [0]
        for pi, page in enumerate(pdf.pages, 1):
            bboxes = [t.bbox for t in page.find_tables()]
            for tbl in page.extract_tables():
                md = table_to_md(tbl)
                if md:
                    lines.append(f"\n<!-- PDF p.{pi} TABLE -->")
                    lines.append(md)
            for line in group_lines(page.chars):
                if in_any_table(line, bboxes):
                    continue
                lvl = heading_level(font_size_of_line(line), body)
                txt = "".join(c['text'] for c in line).strip()
                if not txt:
                    continue
                lines.append(("#" * lvl + " " + txt) if lvl else txt)
            if extract_images:
                for img in page.images:
                    bbox = (img['x0'], img['top'], img['x1'], img['bottom'])
                    counter[0] += 1
                    fn = f"img_{counter[0]:03d}.png"
                    d = os.path.join(image_dir, safe)
                    os.makedirs(d, exist_ok=True)
                    p = os.path.join(d, fn)
                    page.within_bbox(bbox).to_image(resolution=150).save(p)
                    lines.append(f"[IMAGE: images/{safe}/{fn}]")
    content = "\n".join(lines).strip() + "\n"
    if out_path:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Extracted -> {out_path} ({len(content)} chars, ~{counter[0]} images)")
    else:
        print(content)
    return content
def main():
    ap = argparse.ArgumentParser(description="Extract a .pdf into Markdown (V1.1).")
    ap.add_argument("input", help="input .pdf path")
    ap.add_argument("output", nargs="?", help="output .md path (stdout if omitted)")
    ap.add_argument("--extract-images", action="store_true",
                    help="export images to <image-dir>/<safe>/img_NNN.png")
    ap.add_argument("--image-dir", default="output/images",
                    help="base dir for exported images (default: output/images)")
    args = ap.parse_args()
    extract(args.input, args.output, args.extract_images, args.image_dir)
if __name__ == "__main__":
    main()