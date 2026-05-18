import argparse
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from docx import Document


TZ = timezone(timedelta(hours=8))


def default_template_path():
    return Path(__file__).resolve().parents[1] / "assets" / "templates" / "yizhan-report-template.docx"


def fmt_num(value, decimals=0):
    if value is None or value == "":
        return "未获取"
    if isinstance(value, str):
        return value
    if isinstance(value, float) and not value.is_integer():
        return f"{value:,.{decimals}f}"
    return f"{int(value):,}"


def fmt_pct(value, decimals=1):
    if value is None or value == "":
        return "未获取"
    if isinstance(value, str):
        return value if value.endswith("%") else value
    return f"{value * 100:.{decimals}f}%"


def fmt_month(month):
    if not month or "-" not in month:
        return str(month or "")
    year, raw_month = month.split("-", 1)
    return f"{int(year)} 年 {int(raw_month)} 月"


def num(value):
    if value is None or value == "":
        return 0
    if isinstance(value, (int, float)):
        return value
    text = str(value).replace(",", "").replace("%", "")
    try:
        n = float(text)
    except ValueError:
        return 0
    return n / 100 if str(value).strip().endswith("%") else n


def core_metric(registry, name):
    for row in registry.get("core_metrics", []):
        if row.get("指标名称") == name or row.get("指标") == name:
            return row
    return {"数值": None}


def module_metric(registry, module, name):
    for row in registry.get("module_metrics", []):
        if row.get("模块") == module and row.get("指标") == name:
            return row
    return {"数值": None}


def content_rows(registry, module=None, dimension=None):
    rows = registry.get("content_and_grade_stats", [])
    if module:
        rows = [r for r in rows if r.get("模块") == module]
    if dimension:
        rows = [r for r in rows if r.get("维度") == dimension]
    return rows


def report_date():
    now = datetime.now(TZ)
    return f"{now.year} 年 {now.month} 月 {now.day} 日"


def top_items(rows, label_field="分类或指标", value_field="数值", limit=3):
    sorted_rows = sorted(rows, key=lambda r: num(r.get(value_field)), reverse=True)
    return "、".join(str(r.get(label_field)) for r in sorted_rows[:limit] if r.get(label_field))


def build_context(registry):
    school = registry.get("school_name", "学校")
    period = registry.get("data_period", {})
    period_text = f"{fmt_month(period.get('start_month'))} - {fmt_month(period.get('end_month'))}"

    served = core_metric(registry, "累计服务学生").get("数值")
    total_interactions = core_metric(registry, "累计交互总量").get("数值")
    service_coverage = core_metric(registry, "全校覆盖率").get("数值")
    login_intensity = core_metric(registry, "登录人次覆盖强度").get("数值")
    if login_intensity is None:
        login_intensity = service_coverage
    active_peak = core_metric(registry, "本学期活跃峰值").get("数值")
    highest_module = core_metric(registry, "全平台覆盖率最高模块").get("数值")

    career_users = module_metric(registry, "AI生涯规划", "覆盖学生").get("数值")
    career_uses = module_metric(registry, "AI生涯规划", "累计使用次数").get("数值")
    partner_dialogs = module_metric(registry, "AI心语伙伴", "累计对话").get("数值")
    partner_users = module_metric(registry, "AI心语伙伴", "覆盖学生").get("数值")
    bottle_posts = module_metric(registry, "漂流瓶", "发布数量").get("数值")
    bottle_replies = module_metric(registry, "漂流瓶", "回复数量").get("数值")
    bottle_total = (bottle_posts or 0) + (bottle_replies or 0)
    bottle_reply_rate = (bottle_replies or 0) / bottle_posts if bottle_posts else None
    bottle_unique = module_metric(registry, "漂流瓶", "发瓶学生去重数").get("数值")
    interview_users = module_metric(registry, "AI模拟面试", "服务学生").get("数值")
    interview_records = module_metric(registry, "AI模拟面试", "累计使用人次").get("数值")
    interview_reports = module_metric(registry, "AI模拟面试", "生成报告").get("数值")
    interview_depth = (interview_reports or 0) / interview_records if interview_records else None

    ctx = {
        "school_name": school,
        "period_text": period_text,
        "report_date": report_date(),
        "served_students": f"{fmt_num(served)} 人",
        "total_interactions": f"{fmt_num(total_interactions)} 次",
        "service_coverage_rate": fmt_pct(service_coverage, 2),
        "login_intensity_rate": fmt_pct(login_intensity, 2),
        "active_peak": f"{fmt_num(active_peak)} 人",
        "executive_summary": f"本报告基于 {period_text} 的生涯翼站聚合数据，分析{school}学生使用行为、功能价值与学校行动建议。当前累计服务学生 {fmt_num(served)} 人，累计交互总量 {fmt_num(total_interactions)} 次，去重服务覆盖率 {fmt_pct(service_coverage, 2)}，登录人次覆盖强度 {fmt_pct(login_intensity, 2)}。",
        "finding_1": f"平台已形成生涯规划、心理陪伴、校园互助与升学面试训练的综合服务结构。",
        "finding_2": f"{highest_module or '高频模块'}为本周期使用贡献最高模块，适合在报告中重点解释其学生需求与学校价值。",
        "finding_3": f"AI 生涯规划覆盖 {fmt_num(career_users)} 人，累计使用 {fmt_num(career_uses)} 次，体现选科、专业与升学咨询的持续需求。",
        "finding_4": f"漂流瓶累计收发 {fmt_num(bottle_total)} 条，回复率 {fmt_pct(bottle_reply_rate, 1)}，说明匿名表达和同伴回应具有运营价值。",
        "trend_summary": "趋势数据来自网站后台列表记录数聚合，适合观察活跃峰值与阶段变化，不应写作功能使用次数趋势。",
    }

    trend_rows = registry.get("website_backend_record_trend", [])
    for idx in range(1, 7):
        row = trend_rows[idx - 1] if idx <= len(trend_rows) else {}
        ctx.update({
            f"trend_month_{idx}": row.get("month", ""),
            f"career_records_{idx}": fmt_num(row.get("ai_career_dialog_records")),
            f"partner_records_{idx}": fmt_num(row.get("ai_partner_analysis_records")),
            f"bottle_records_{idx}": fmt_num(row.get("message_bottle_posts")),
            f"interview_reports_{idx}": fmt_num(row.get("ai_interview_reports")),
            f"total_records_{idx}": fmt_num(row.get("total_backend_records")),
        })

    module_specs = {
        "career": ("AI生涯规划", "AI 生涯规划模块用于承接学生选科、专业、职业与升学路径探索。", "结合年级节点开展主题化生涯课或班会，引导学生带着问题使用。"),
        "partner": ("AI心语伙伴", "AI 心语伙伴用于即时陪伴和心理状态初筛，报告中必须区分历史分析与内容统计口径。", "建立 AI 初筛、教师核验、分级干预的闭环，不直接把比例解释为全校风险率。"),
        "bottle": ("漂流瓶", "漂流瓶承接匿名表达与同伴回应，是观察校园互助氛围的重要入口。", "围绕高频主题开展正向引导，保留匿名低门槛表达空间。"),
        "interview": ("AI模拟面试", "AI 模拟面试对接升学面试训练和反馈复盘需求。", "面向高三和综评、强基等场景开展集中训练，并复盘报告生成率。"),
    }
    kpis = {
        "career": [("覆盖学生", f"{fmt_num(career_users)} 人", "网站后台汇总卡片。"), ("累计使用次数", f"{fmt_num(career_uses)} 次", "网站后台汇总卡片。"), ("人均使用次数", f"{(career_uses / career_users):.1f} 次" if career_users else "未获取", "累计使用次数 / 覆盖学生。")],
        "partner": [("累计对话", f"{fmt_num(partner_dialogs)} 次", "历史分析口径。"), ("覆盖学生", f"{fmt_num(partner_users)} 人", "历史分析口径。"), ("内容统计用户数", f"{fmt_num(module_metric(registry, 'AI心语伙伴', '内容统计用户数').get('数值'))} 人", "内容统计口径。")],
        "bottle": [("累计收发", f"{fmt_num(bottle_total)} 条", "发布数量 + 回复数量。"), ("回复率", fmt_pct(bottle_reply_rate, 1), "回复数量 / 发布数量。"), ("覆盖学生", f"{fmt_num(bottle_unique)} 人", "发瓶学生去重口径。")],
        "interview": [("服务学生", f"{fmt_num(interview_users)} 人", "网站后台统计。"), ("累计使用人次", f"{fmt_num(interview_records)} 人次", "网站后台统计。"), ("生成报告", f"{fmt_num(interview_reports)} 份", "报告列表分页总数。")],
    }
    for key, (module_name, analysis, action) in module_specs.items():
        ctx[f"{key}_analysis"] = analysis
        ctx[f"{key}_action"] = action
        for idx, (name, value, note) in enumerate(kpis[key], start=1):
            ctx[f"{key}_kpi_{idx}_name"] = name
            ctx[f"{key}_kpi_{idx}_value"] = value
            ctx[f"{key}_kpi_{idx}_note"] = note

    ctx.update({
        "career_profile_dimension": "年级使用与高频问题",
        "career_profile_finding": top_items(content_rows(registry, "AI生涯规划", "高频提问")) or "围绕专业选择、生涯方向、学业规划形成咨询需求。",
        "career_profile_action": "将高频问题转化为年级化生涯课程和答疑主题。",
        "partner_profile_dimension": "心理状态与困扰因子",
        "partner_profile_finding": "心理状态比例仅代表已互动样本，适合做初筛线索。",
        "partner_profile_action": "建立 AI 线索复核机制，避免把样本比例外推为全校风险率。",
        "bottle_profile_dimension": "匿名表达与回复互动",
        "bottle_profile_finding": "发布与回复数据可用于观察学生表达需求和同伴互助活跃度。",
        "bottle_profile_action": "围绕积极回应、情绪支持和校园文化开展运营。",
        "interview_profile_dimension": "训练与报告转化",
        "interview_profile_finding": f"报告生成率 {fmt_pct(interview_depth, 1)} 可作为深度使用观察指标。",
        "interview_profile_action": "结合升学节点开展集中模拟和报告复盘。",
        "grade_operation_advice": "按高一适应探索、高二选科深化、高三升学准备拆分运营主题。",
        "grade_operation_priority": "高",
        "mental_support_advice": "AI 心语伙伴只做线索和陪伴入口，关键个案需要人工核验。",
        "mental_support_priority": "高",
        "data_review_advice": "每月保留 Excel、网站聚合 JSON、登记表和报告四类产物，持续复盘口径。",
        "data_review_priority": "中",
        "additional_limitation_note": "如网站字段缺失，应在登记表中标记未获取，不得在报告中推断补齐。",
    })
    return ctx


def replace_placeholders(doc, context):
    replacements = {f"{{{{{key}}}}}": str(value) for key, value in context.items()}
    containers = list(doc.paragraphs)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                containers.extend(cell.paragraphs)
    for section in doc.sections:
        containers.extend(section.header.paragraphs)
        containers.extend(section.footer.paragraphs)

    for paragraph in containers:
        for run in paragraph.runs:
            for old, new in replacements.items():
                if old in run.text:
                    run.text = run.text.replace(old, new)


def render_word_report(template_path, registry_path, output_path):
    registry = json.loads(Path(registry_path).read_text(encoding="utf-8"))
    doc = Document(str(template_path))
    replace_placeholders(doc, build_context(registry))
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output))
    return output


def main():
    parser = argparse.ArgumentParser(description="Render 生涯翼站 Word report from registry JSON.")
    parser.add_argument("--registry", required=True, help="Registry JSON generated by build_registry.py.")
    parser.add_argument("--out", required=True, help="Output .docx path.")
    parser.add_argument("--template", default=str(default_template_path()), help="Word template path.")
    args = parser.parse_args()
    print(render_word_report(args.template, args.registry, args.out))


if __name__ == "__main__":
    main()
