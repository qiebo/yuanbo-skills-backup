#!/usr/bin/env python3
"""Regression tests for tests/leak_scan.py (stdlib only)."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN = ROOT / "tests" / "leak_scan.py"


def run(*args, input_text=None):
    return subprocess.run(
        [sys.executable, str(SCAN), *map(str, args)],
        input=input_text,
        text=True,
        capture_output=True,
        cwd=ROOT,
    )


def make_docx(path: Path, body: str = "正式方案正文", header: str | None = None, footer: str | None = None):
    def body_xml(text):
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            f'<w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>'
        )

    def part_xml(text, tag):
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:{tag} xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            f'<w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:{tag}>'
        )

    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("word/document.xml", body_xml(body))
        if header is not None:
            zf.writestr("word/header1.xml", part_xml(header, "hdr"))
        if footer is not None:
            zf.writestr("word/footer1.xml", part_xml(footer, "ftr"))


class LeakScanTests(unittest.TestCase):
    def test_clean_text_passes(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "clean.txt"
            p.write_text("项目将建设生涯发展课程与咨询空间。", encoding="utf-8")
            r = run(p)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_default_pattern_catches_teacher_alias(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "leak.txt"
            p.write_text("本项目沿用乔老师课程并扩展模块。", encoding="utf-8")
            r = run(p)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("乔老师课程", r.stdout)

    def test_dynamic_literal_term(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "dynamic.txt"
            p.write_text("后续沿用火种计划相关内容。", encoding="utf-8")
            r = run("--term", "火种计划", p)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("火种计划", r.stdout)

    def test_docx_header_is_scanned(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "header.docx"
            make_docx(p, body="正式方案正文", header="内部资料")
            r = run(p)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("word/header1.xml", r.stdout)

    def test_invalid_docx_is_error_not_clean(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "bad.docx"
            p.write_text("not a zip", encoding="utf-8")
            r = run(p)
            self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
            self.assertIn("BLOCK DELIVERY", r.stderr)

    def test_stdin_dynamic_term(self):
        r = run("--term", "王总方案", "-", input_text="正文包含王总方案")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
