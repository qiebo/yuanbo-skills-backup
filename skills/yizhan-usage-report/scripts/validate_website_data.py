import argparse
import json
from pathlib import Path


REQUIRED_NUMERIC_PATHS = [
    ("manual_dom_aggregates.student_management_total_accounts", 1),
    ("manual_dom_aggregates.ai_career.total_users", 1),
    ("manual_dom_aggregates.ai_career.total_uses", 1),
    ("manual_dom_aggregates.ai_partner_history.total_uses", 1),
    ("manual_dom_aggregates.message_bottle.published_count", 1),
    ("manual_dom_aggregates.ai_interview.total_records", 1),
]

REQUIRED_OBJECT_PATHS = [
    "api_aggregates.planner_content_stats",
    "api_aggregates.partner_content_stats",
    "api_aggregates.message_bottle_stats",
    "api_aggregates.ai_interview_info",
    "completeness_audit.website_full_list_monthly_record_trend.rows",
]


def get_path(data, dotted):
    cur = data
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def is_empty(value):
    return value is None or value == {} or value == [] or value == ""


def validate(data, expected_school=None):
    issues = []
    if not isinstance(data, dict):
        return ["website_data is not a JSON object"]

    backend_school = data.get("backend_school")
    if not backend_school:
        issues.append("backend_school is missing; login probably did not succeed")
    if expected_school and backend_school and expected_school not in backend_school and backend_school not in expected_school:
        issues.append(f"backend_school does not match Excel school: backend={backend_school}, excel={expected_school}")

    for dotted, minimum in REQUIRED_NUMERIC_PATHS:
        value = get_path(data, dotted)
        if not isinstance(value, (int, float)) or value < minimum:
            issues.append(f"required aggregate missing or too small: {dotted}={value!r}")

    for dotted in REQUIRED_OBJECT_PATHS:
        value = get_path(data, dotted)
        if is_empty(value):
            issues.append(f"required website object/list is empty: {dotted}")

    trend_rows = get_path(data, "completeness_audit.website_full_list_monthly_record_trend.rows")
    if isinstance(trend_rows, list):
        useful = [r for r in trend_rows if isinstance(r, dict) and (r.get("total_backend_records") or 0) > 0]
        if not useful:
            issues.append("website backend trend rows have no positive total_backend_records")

    return issues


def main():
    parser = argparse.ArgumentParser(description="Validate yizhan website_data.json before report generation.")
    parser.add_argument("--website", required=True, help="Path to website_data.json.")
    parser.add_argument("--excel-metrics", default=None, help="Optional excel_metrics.json for school-name consistency check.")
    args = parser.parse_args()

    website = json.loads(Path(args.website).read_text(encoding="utf-8"))
    expected_school = None
    if args.excel_metrics:
        expected_school = json.loads(Path(args.excel_metrics).read_text(encoding="utf-8")).get("school_name")
    issues = validate(website, expected_school)
    result = {
        "status": "fail" if issues else "ok",
        "issues": issues,
        "backend_school": website.get("backend_school"),
        "expected_school": expected_school,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
