import argparse
import json
import re
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET


FORBIDDEN_REPORT_TOKENS = ["{{", "}}", "TODO", "<TODO>", "xxxx", "###"]
SENSITIVE_TERMS = ["password", "passwd", "authorization", "cookie", "token", "身份证", "手机号"]
MISLEADING_TIME_LABEL_PATTERNS = [
    r"20\d{2}年\d{1,2}月数据",
    r"20\d{2}年\d{1,2}月各年级互动内容分类",
    r"使用人数年级分布占比（20\d{2}年\d{1,2}月）",
    r"心理状态分级预警（20\d{2}年数据）",
]
ANALYSIS_KEYWORDS = ["学校", "学生", "年级", "班级", "建议", "应", "适合", "帮助", "支持", "复核", "关注"]
UNSUPPORTED_INTERVIEW_CLAIM_PATTERNS = [
    r"港澳",
    r"用户以高三为主",
    r"高三升学备考刚需工具",
    r"集中在强基计划、综合评价",
]
LEADERSHIP_UNSUITABLE_PATTERNS = [
    r"当前已获取数据只能说明",
    r"不能推断具体申请类型或年级分布",
    r"用于反复演练与复盘，单用户多次使用特征明显",
    r"提供无压力、匿名、即时的陪伴渠道",
    r"提供全真模拟、智能评分、语音回听与改进建议",
    r"痛点",
    r"直接提升面试竞争力",
]


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


def extract_docx_paragraph_texts(path):
    with ZipFile(path) as z:
        document_xml = z.read("word/document.xml")
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    root = ET.fromstring(document_xml)
    paragraphs = []
    for paragraph in root.findall(".//w:p", ns):
        text = "".join(node.text or "" for node in paragraph.findall(".//w:t", ns)).strip()
        if text:
            paragraphs.append(text)
    return paragraphs


def repeated_analysis_fragments(paragraphs):
    seen = {}
    repeated = []
    for paragraph in paragraphs:
        for fragment in re.split(r"[，,；;。]", paragraph):
            fragment = re.sub(r"\s+", "", fragment).strip()
            if len(fragment) < 18:
                continue
            if not any(keyword in fragment for keyword in ANALYSIS_KEYWORDS):
                continue
            seen.setdefault(fragment, 0)
            seen[fragment] += 1
            if seen[fragment] == 2:
                repeated.append(fragment)
    return repeated[:10]


def check_docx(path):
    with ZipFile(path) as z:
        document_xml = z.read("word/document.xml")
    text = extract_docx_text(path)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    root = ET.fromstring(document_xml)
    paragraph_count = len(root.findall(".//w:p", ns))
    table_count = len(root.findall(".//w:tbl", ns))
    table_header_repeat_count = len(root.findall(".//w:tblHeader", ns))
    page_break_count = sum(
        1
        for br in root.findall(".//w:br", ns)
        if br.attrib.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type") == "page"
    )
    paragraphs = extract_docx_paragraph_texts(path)
    return {
        "exists": Path(path).exists(),
        "size": Path(path).stat().st_size,
        "paragraph_count": paragraph_count,
        "table_count": table_count,
        "table_header_repeat_count": table_header_repeat_count,
        "page_break_count": page_break_count,
        "forbidden_hits": [term for term in FORBIDDEN_REPORT_TOKENS if term in text],
        "misleading_time_label_hits": [pattern for pattern in MISLEADING_TIME_LABEL_PATTERNS if re.search(pattern, text)],
        "unsupported_interview_claim_hits": [pattern for pattern in UNSUPPORTED_INTERVIEW_CLAIM_PATTERNS if re.search(pattern, text)],
        "leadership_unsuitable_hits": [pattern for pattern in LEADERSHIP_UNSUITABLE_PATTERNS if re.search(pattern, text)],
        "repeated_analysis_fragments": repeated_analysis_fragments(paragraphs),
        "font_has_microsoft_yahei": "微软雅黑" in text,
        "header_has_white_text": 'w:val="FFFFFF"' in text or "FFFFFF" in text,
        "header_has_dark_fill": "1F4E78" in text,
    }


def main():
    parser = argparse.ArgumentParser(description="QA 生涯翼站 report output bundle.")
    parser.add_argument("--registry", required=True)
    parser.add_argument("--html", required=False, help="Optional legacy HTML report path.")
    parser.add_argument("--pdf", required=False, help="Optional legacy PDF report path.")
    parser.add_argument("--docx", required=True, help="Word report path.")
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
    }
    if args.html:
        result["html"] = {
            "exists": Path(args.html).exists(),
            "size": Path(args.html).stat().st_size if Path(args.html).exists() else 0,
            "forbidden_hits": check_text_file(args.html, FORBIDDEN_REPORT_TOKENS),
        }
    if args.pdf:
        result["pdf"] = check_pdf(args.pdf)
    result["docx"] = check_docx(args.docx)

    failures = []
    if sensitive_hits:
        failures.append("registry contains sensitive terms")
    if "html" in result and result["html"]["forbidden_hits"]:
        failures.append("html contains forbidden placeholder/debug tokens")
    if "pdf" in result and (not result["pdf"]["header_ok"] or result["pdf"]["size"] == 0):
        failures.append("pdf is invalid or empty")
    if result["docx"]["forbidden_hits"]:
        failures.append("docx contains forbidden placeholder/debug tokens")
    if result["docx"]["misleading_time_label_hits"]:
        failures.append("docx contains misleading single-month/time labels for aggregate content stats")
    if result["docx"]["unsupported_interview_claim_hits"]:
        failures.append("docx contains unsupported AI interview scenario or grade claims")
    if result["docx"]["leadership_unsuitable_hits"]:
        failures.append("docx contains low-information or internal-audit wording unsuitable for school leadership reporting")
    if result["docx"]["repeated_analysis_fragments"]:
        failures.append("docx contains repeated analysis wording fragments; analysis should be varied by grade/module context")
    if result["docx"]["table_header_repeat_count"]:
        failures.append("docx contains repeated table header markers; tables should stay together where possible")
    if result["docx"]["paragraph_count"] < 60:
        failures.append("docx is too short; expected a long-form analysis report with at least 60 paragraphs")
    if result["docx"]["table_count"] != 14:
        failures.append("docx table count changed; expected the approved template structure with exactly 14 tables")
    result["status"] = "fail" if failures else "ok"
    result["failures"] = failures
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
