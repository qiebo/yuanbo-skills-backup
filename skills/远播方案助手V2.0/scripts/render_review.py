#!/usr/bin/env python3
"""将 DOCX 渲染为 PDF 与逐页 PNG，供视觉检查。"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def require(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise SystemExit(f"缺少工具：{name}")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="渲染 DOCX 进行视觉验收")
    parser.add_argument("docx")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--dpi", type=int, default=150)
    args = parser.parse_args()

    docx = Path(args.docx).expanduser().resolve()
    out = Path(args.output_dir).expanduser().resolve()
    if not docx.exists():
        raise SystemExit(f"文件不存在：{docx}")
    out.mkdir(parents=True, exist_ok=True)
    for stale in list(out.glob("page-*.png")) + list(out.glob("*.pdf")):
        stale.unlink()
    libreoffice = shutil.which("libreoffice") or shutil.which("soffice")
    if not libreoffice:
        raise SystemExit("缺少工具：libreOffice 或 soffice（Windows 下通常为 soffice）")
    pdftoppm = require("pdftoppm")

    with tempfile.TemporaryDirectory(prefix="yb_lo_") as profile:
        env = os.environ.copy()
        env["HOME"] = profile
        cmd = [libreoffice, "--headless", f"-env:UserInstallation=file://{profile}/profile", "--convert-to", "pdf", "--outdir", str(out), str(docx)]
        proc = subprocess.run(cmd, text=True, capture_output=True, env=env)
        pdf = out / f"{docx.stem}.pdf"
        if proc.returncode != 0 or not pdf.exists():
            raise SystemExit(f"LibreOffice 渲染失败：\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}")

    prefix = out / "page"
    proc = subprocess.run([pdftoppm, "-png", "-r", str(args.dpi), str(pdf), str(prefix)], text=True, capture_output=True)
    if proc.returncode != 0:
        raise SystemExit(f"PDF 转 PNG 失败：{proc.stderr}")

    pages = sorted(out.glob("page-*.png"))
    if not pages:
        raise SystemExit("没有生成页面图片。")
    checklist = out / "视觉检查清单.md"
    lines = [
        "# 视觉检查清单", "", f"- DOCX：`{docx.name}`", f"- 页面数：{len(pages)}", "",
        "逐页以 100% 缩放检查：", "",
        "- [ ] 封面独立且无不应出现的页眉页脚", "- [ ] 目录存在且不为空", "- [ ] 正文标题层级和分页正确",
        "- [ ] 表格无越界、缺列、断裂或小字不可读", "- [ ] 图片无变形、遮挡和低清晰度", "- [ ] 无空白页、占位符或未替换标记",
        "- [ ] 页眉页脚、页码、字体和行距一致", "", "## 页面", ""
    ]
    lines.extend(f"- [ ] {p.name}" for p in pages)
    checklist.write_text("\n".join(lines) + "\n", encoding="utf-8")
    report = {"docx": str(docx), "pdf": str(pdf), "pages": [str(p) for p in pages], "page_count": len(pages), "checklist": str(checklist)}
    (out / "render_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"渲染完成：{len(pages)} 页")
    print(checklist)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
