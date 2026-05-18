import argparse
import json
from pathlib import Path
from zipfile import ZipFile


FORBIDDEN_REPORT_TOKENS = ["{{", "}}", "TODO", "<TODO>", "xxxx", "###"]
SENSITIVE_TERMS = ["password", "passwd", "authorization", "cookie", "token", "身份证", "手机号"]


def check_text_file(path, forbidden):
    text = Path(path).read_text(encoding="utf-8", errors="ignore")
    return [term for term in forbidden if term in text]


def check_pdf(path):
    data = Path(path).read_bytes()
    return {
        "exists": Path(path).exists(),
        "size": len(data),
        "header_ok": data.startswith(b"%PDF"),
        "page_markers": data.count(b"/Type /Page"),
    }


def extract_docx_text(path):
    with ZipFile(path) as z:
        parts = [name for name in z.namelist() if name.startswith("word/") and name.endswith(".xml")]
        return "\n".join(z.read(name).decode("utf-8", errors="ignore") for name in parts)


def check_docx(path):
    text = extract_docx_text(path)
    return {
        "exists": Path(path).exists(),
        "size": Path(path).stat().st_size,
        "forbidden_hits": [term for term in FORBIDDEN_REPORT_TOKENS if term in text],
        "font_has_microsoft_yahei": "微软雅黑" in text,
        "header_has_white_text": 'w:val="FFFFFF"' in text or "FFFFFF" in text,
        "header_has_dark_fill": "1F4E78" in text,
    }


def main():
    parser = argparse.ArgumentParser(description="QA 生涯翼站 report output bundle.")
    parser.add_argument("--registry", required=True)
    parser.add_argument("--html", required=True)
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--docx", required=False)
    args = parser.parse_args()

    registry = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    registry_text = json.dumps(registry, ensure_ascii=False)
    sensitive_hits = [term for term in SENSITIVE_TERMS if term.lower() in registry_text.lower()]

    result = {
        "registry": {
            "school_name": registry.get("school_name"),
            "schema_version": registry.get("schema_version"),
            "sensitive_term_hits": sensitive_hits,
            "core_metric_count": len(registry.get("core_metrics", [])),
            "module_metric_count": len(registry.get("module_metrics", [])),
            "trend_row_count": len(registry.get("website_backend_record_trend", [])),
        },
        "html": {
            "exists": Path(args.html).exists(),
            "size": Path(args.html).stat().st_size if Path(args.html).exists() else 0,
            "forbidden_hits": check_text_file(args.html, FORBIDDEN_REPORT_TOKENS),
        },
        "pdf": check_pdf(args.pdf),
    }
    if args.docx:
        result["docx"] = check_docx(args.docx)

    failures = []
    if sensitive_hits:
        failures.append("registry contains sensitive terms")
    if result["html"]["forbidden_hits"]:
        failures.append("html contains forbidden placeholder/debug tokens")
    if not result["pdf"]["header_ok"] or result["pdf"]["size"] == 0:
        failures.append("pdf is invalid or empty")
    if "docx" in result and result["docx"]["forbidden_hits"]:
        failures.append("docx contains forbidden placeholder/debug tokens")
    result["status"] = "fail" if failures else "ok"
    result["failures"] = failures
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
