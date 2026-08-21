#!/usr/bin/env python3
"""Hard gate for client-facing deliverables: detect internal-info leakage.

Features
--------
- Loads generic regex patterns from tests/leak_terms.txt.
- Accepts project-specific regex files via --terms PATH (repeatable).
- Accepts project-specific *literal* terms via --term TEXT (repeatable).
- Scans .docx Word body, headers, footers, footnotes, endnotes and comments.
- Scans text/markdown files and stdin ('-').
- Read/parse failure is a hard failure, never treated as clean.

Exit codes
----------
0 = clean
1 = leaks found
2 = usage/read/parse/config error (also blocks delivery)
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TERMS_FILE = ROOT / "tests" / "leak_terms.txt"
DOCX_PART_RE = re.compile(
    r"^word/(?:document\.xml|header\d*\.xml|footer\d*\.xml|footnotes\.xml|endnotes\.xml|comments\.xml)$"
)
TEXT_TAGS = {"t", "instrText", "delText"}


class ScanError(RuntimeError):
    pass


def load_regex_file(path: Path) -> list[tuple[str, str]]:
    if not path.exists():
        raise ScanError(f"terms file not found: {path}")
    result: list[tuple[str, str]] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            re.compile(line, flags=re.DOTALL)
        except re.error as exc:
            raise ScanError(f"bad regex {path}:{line_no}: {line!r} ({exc})") from exc
        result.append((f"regex:{path.name}:{line_no}", line))
    return result


def build_patterns(default_terms: bool, extra_files: Iterable[str], literal_terms: Iterable[str]):
    items: list[tuple[str, str]] = []
    if default_terms:
        items.extend(load_regex_file(DEFAULT_TERMS_FILE))
    for raw_path in extra_files:
        items.extend(load_regex_file(Path(raw_path)))
    for idx, term in enumerate(literal_terms, 1):
        if term:
            items.append((f"literal:{idx}:{term}", re.escape(term)))

    seen: set[tuple[str, str]] = set()
    deduped = []
    for item in items:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    if not deduped:
        raise ScanError("no leak patterns configured")
    return deduped


def xml_visible_text(xml_bytes: bytes, part: str) -> str:
    try:
        root = ET.fromstring(xml_bytes)
        chunks: list[str] = []
        for elem in root.iter():
            local = elem.tag.rsplit("}", 1)[-1]
            if local in TEXT_TAGS and elem.text:
                chunks.append(elem.text)
        return "\n".join(chunks)
    except ET.ParseError:
        decoded = xml_bytes.decode("utf-8", errors="replace")
        chunks = re.findall(
            r"<(?:w|a):(?:t|instrText|delText)[^>]*>(.*?)</(?:w|a):(?:t|instrText|delText)>",
            decoded,
            flags=re.S,
        )
        if not chunks:
            raise ScanError(f"cannot parse XML part: {part}")
        return "\n".join(html.unescape(x) for x in chunks)


def extract_docx(path: Path) -> list[tuple[str, str]]:
    try:
        with zipfile.ZipFile(path) as zf:
            names = [n for n in zf.namelist() if DOCX_PART_RE.match(n)]
            if "word/document.xml" not in names:
                raise ScanError(f"invalid docx (missing word/document.xml): {path}")
            return [(name, xml_visible_text(zf.read(name), name)) for name in sorted(names)]
    except zipfile.BadZipFile as exc:
        raise ScanError(f"invalid/unreadable docx: {path}") from exc
    except OSError as exc:
        raise ScanError(f"cannot read docx {path}: {exc}") from exc


def extract_input(arg: str) -> list[tuple[str, str]]:
    if arg == "-":
        data = sys.stdin.read()
        if data == "":
            raise ScanError("stdin is empty")
        return [("stdin", data)]

    path = Path(arg)
    if not path.exists() or not path.is_file():
        raise ScanError(f"file not found: {arg}")
    if path.suffix.lower() == ".docx":
        return extract_docx(path)
    try:
        return [(path.name, path.read_text(encoding="utf-8", errors="replace"))]
    except OSError as exc:
        raise ScanError(f"cannot read {path}: {exc}") from exc


def scan_parts(parts: list[tuple[str, str]], patterns: list[tuple[str, str]]):
    hits = []
    compiled = [(label, src, re.compile(src, flags=re.DOTALL)) for label, src in patterns]
    for component, text in parts:
        for label, src, rx in compiled:
            for m in rx.finditer(text):
                start = max(0, m.start() - 24)
                end = min(len(text), m.end() + 24)
                hits.append(
                    {
                        "component": component,
                        "pattern": label,
                        "pattern_source": src,
                        "match": m.group(0),
                        "context": text[start:end].replace("\n", " ").strip(),
                    }
                )
    return hits


def parse_args():
    ap = argparse.ArgumentParser(description="Scan client deliverables for internal-info leakage")
    ap.add_argument("files", nargs="+", help="files to scan; use '-' for stdin")
    ap.add_argument("--terms", action="append", default=[], help="additional regex terms file; repeatable")
    ap.add_argument("--term", action="append", default=[], help="additional literal internal-only term; repeatable")
    ap.add_argument("--no-default-terms", action="store_true", help="do not load tests/leak_terms.txt")
    ap.add_argument("--json", action="store_true", dest="as_json", help="emit machine-readable JSON")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    try:
        patterns = build_patterns(not args.no_default_terms, args.terms, args.term)
        reports = []
        total = 0
        for item in args.files:
            parts = extract_input(item)
            hits = scan_parts(parts, patterns)
            total += len(hits)
            reports.append({"input": item, "hits": hits})

        if args.as_json:
            print(json.dumps({"ok": total == 0, "total_hits": total, "reports": reports}, ensure_ascii=False, indent=2))
        else:
            for report in reports:
                if report["hits"]:
                    print(f"\n❌ LEAK in {report['input']} ({len(report['hits'])} hit(s))")
                    for i, hit in enumerate(report["hits"], 1):
                        print(f"  {i}. component: {hit['component']}")
                        print(f"     pattern: {hit['pattern']}")
                        print(f"     match: {hit['match']}")
                        print(f"     context: …{hit['context']}…")
                else:
                    print(f"✅ clean: {report['input']}")
            print("\n" + "=" * 56)
            print(
                f"RESULT: FAIL — {total} internal-info leak(s) found. BLOCK DELIVERY."
                if total
                else "RESULT: PASS — 0 internal-info leaks. Safe to deliver."
            )
        raise SystemExit(1 if total else 0)
    except ScanError as exc:
        if args.as_json:
            print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
            print("RESULT: ERROR — scanner could not complete. BLOCK DELIVERY.", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
