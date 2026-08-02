#!/usr/bin/env python3
"""对方案项目执行确定性校验，并输出 JSON/Markdown 报告。"""
from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable

import yaml

CLOSED = {"closed", "covered", "verified", "done", "accepted", "active", "complete"}
PLACEHOLDER_PATTERNS = [
    r"待确认", r"TODO", r"TBD", r"XX学校", r"示例内容", r"示例设备", r"占位符", r"example\.invalid"
]
HIGH_RISK_WORDS = ["全国首个", "全市首个", "区域首个", "唯一", "率先", "领先", "填补空白", "示范标杆"]
OVERCOMMIT_WORDS = ["必然", "百分之百", "绝对保证"]

# 阶段 6.5：正式方案语言净化（去 AI 味）。
# 复用通用去 AI 味的*检测*目录，但**不**套用其口语化注入配方（口语锚点/语气词/句子碎片等）
# ——正式文档保留庄重文风、完整句与必要标点。全部 warning 级，不阻断交付。
FORMAL_AI_TELL_PATTERNS = [
    ("AI_TELL_TOXIC", r"不是[，,]\s*而是", "“不是A，而是B”最毒句式，直接写结论"),
    ("AI_TELL_TOXIC", r"心中涌起|眼中闪过|声音不大，却", "情绪告知式空壳描写，用具体行为替代"),
    ("AI_TELL_TOXIC", r"仿佛.{0,8}一般|犹如.{0,8}一般|宛若.{0,8}一般", "比喻陈词，改为白描"),
    ("AI_TELL_TOXIC", r"(?:他|她)(?:知道|明白|终于明白了)", "认知告知，用行为展现"),
    ("AI_TELL_OPEN", r"很高兴|当然可以|好的，我来|这是一个非常好的问题|感谢您的提问|非常感谢您", "客套开场，第一句直接给内容"),
    ("AI_TELL_CLOSE", r"综上所述|总的来看|总而言之|总之，?|希望以上|如有任何疑问|希望对您|通过以上分析|这一刻", "结尾总结/升华套话，在最后一个有实质内容的句子结束"),
    ("AI_TELL_TRANS", r"值得注意的是|需要指出的是|值得一提的是|不可忽视的是", "模板过渡词，直接接内容"),
    ("AI_TELL_VAGUE", r"在某种程度上|从某种意义(?:上|来说)|一般来说|通常情况下|可以认为|可以说|总体而言", "模糊限定，删去或给出具体边界"),
    ("AI_TELL_VAGUE", r"在相关部门的共同努力下|为.{0,12}奠定.{0,6}基础|持续赋能|强化.{0,8}能力建设|打造.{0,8}新格局|具有重要意义|具有重要的意义", "官腔空话，用主体+具体结果替代"),
    ("AI_TELL_OVERCLAIM", r"打造区域标杆|全面领先|行业领先|国内一流|世界一流|对标一流", "无证据强词，改为可核实表述或降级为“拟/重点建设/对标”"),
]
FORMAL_FILLER_WORDS = [
    "高质量", "显著提升", "显著增强", "扎实", "有力", "全方位", "多层次", "系统性",
]
FORMAL_CONNECTORS = ["此外", "然而", "因此", "与此同时", "另一方面"]


@dataclass
class Finding:
    severity: str
    code: str
    message: str
    location: str = ""


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [{k: (v or "").strip() for k, v in row.items()} for row in csv.DictReader(f)]


def dec(value: str, field: str, item_id: str, findings: list[Finding]) -> Decimal | None:
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError):
        findings.append(Finding("error", "BUDGET_NUMBER", f"{item_id} 的 {field} 不是有效数字：{value}", "data/预算明细.csv"))
        return None


def is_closed(value: str) -> bool:
    return value.lower() in CLOSED


def require_files(project: Path, findings: list[Finding]) -> None:
    required = [
        "project.yaml", "07_方案终稿.md", "data/需求响应矩阵.csv", "data/事实证据台账.csv",
        "data/预算明细.csv", "data/待确认事项.csv", "data/实施验收矩阵.csv"
    ]
    for rel in required:
        if not (project / rel).exists():
            findings.append(Finding("error", "MISSING_FILE", f"缺少必需文件：{rel}", rel))


def check_requirements(rows: list[dict[str, str]], findings: list[Finding]) -> dict[str, float]:
    mandatory = [r for r in rows if r.get("type", "").lower() in {"mandatory", "constraint", "forbidden"} or r.get("priority", "").upper() == "P0"]
    closed = [r for r in mandatory if is_closed(r.get("status", ""))]
    for r in mandatory:
        if not is_closed(r.get("status", "")):
            findings.append(Finding("error", "REQ_OPEN", f"强制需求未关闭：{r.get('requirement_id')} {r.get('original_text')}", "data/需求响应矩阵.csv"))
        for field in ["response", "target_section", "acceptance_method"]:
            if not r.get(field):
                findings.append(Finding("error", "REQ_FIELD", f"{r.get('requirement_id')} 缺少字段 {field}", "data/需求响应矩阵.csv"))
    return {"mandatory_total": len(mandatory), "mandatory_closed": len(closed), "coverage": len(closed) / len(mandatory) if mandatory else 1.0}


def check_pending(rows: list[dict[str, str]], findings: list[Finding]) -> None:
    for r in rows:
        blocking = r.get("blocking", "").lower() in {"true", "1", "yes", "是"}
        if blocking and not is_closed(r.get("status", "")):
            findings.append(Finding("error", "BLOCKING_PENDING", f"阻断型待确认事项未关闭：{r.get('issue_id')} {r.get('issue')}", "data/待确认事项.csv"))
        elif not is_closed(r.get("status", "")):
            findings.append(Finding("warning", "PENDING_OPEN", f"待确认事项未关闭：{r.get('issue_id')} {r.get('issue')}", "data/待确认事项.csv"))


def check_evidence(rows: list[dict[str, str]], findings: list[Finding]) -> dict[str, float]:
    external_types = {"verified_fact", "user_provided", "inference"}
    relevant = [r for r in rows if r.get("claim_type") in external_types]
    verified = [r for r in relevant if r.get("status") == "verified"]
    high = [r for r in relevant if r.get("risk_level") == "high"]
    high_verified = [r for r in high if r.get("status") == "verified"]
    for r in rows:
        cid = r.get("claim_id", "(无编号)")
        if r.get("risk_level") == "high" and r.get("status") != "verified":
            findings.append(Finding("error", "HIGH_RISK_UNVERIFIED", f"高风险主张未核实：{cid} {r.get('claim')}", "data/事实证据台账.csv"))
        if r.get("status") == "verified":
            for field in ["source_title", "source_locator", "checked_at", "allowed_wording"]:
                if not r.get(field):
                    findings.append(Finding("error", "EVIDENCE_FIELD", f"已核实主张 {cid} 缺少 {field}", "data/事实证据台账.csv"))
        if r.get("status") in {"expired", "rejected"}:
            findings.append(Finding("warning", "EVIDENCE_INACTIVE", f"存在失效/拒绝主张，确认未进入终稿：{cid}", "data/事实证据台账.csv"))
    return {
        "external_total": len(relevant),
        "external_verified": len(verified),
        "coverage": len(verified) / len(relevant) if relevant else 1.0,
        "high_total": len(high),
        "high_verified": len(high_verified),
        "high_coverage": len(high_verified) / len(high) if high else 1.0,
    }


def check_budget(rows: list[dict[str, str]], findings: list[Finding], tolerance: Decimal) -> dict[str, str]:
    total = Decimal("0")
    active_rows = 0
    for r in rows:
        item = r.get("item_id", "(无编号)")
        if not r.get("name"):
            continue
        if r.get("status") == "pending":
            findings.append(Finding("error", "BUDGET_PENDING", f"预算项仍待确认：{item} {r.get('name')}", "data/预算明细.csv"))
        q = dec(r.get("quantity", ""), "quantity", item, findings)
        u = dec(r.get("unit_price", ""), "unit_price", item, findings)
        s = dec(r.get("subtotal", ""), "subtotal", item, findings)
        if None in (q, u, s):
            continue
        active_rows += 1
        expected = q * u
        if abs(expected - s) > tolerance:
            findings.append(Finding("error", "BUDGET_MATH", f"{item} 小计错误：{q} × {u} = {expected}，表中为 {s}", "data/预算明细.csv"))
        total += s
        for field in ["currency", "tax_included", "price_basis"]:
            if not r.get(field):
                findings.append(Finding("warning", "BUDGET_FIELD", f"{item} 缺少 {field}", "data/预算明细.csv"))
    return {"active_rows": str(active_rows), "total": str(total)}


def check_mapping(rows: list[dict[str, str]], findings: list[Finding]) -> None:
    for r in rows:
        if not r.get("map_id"):
            continue
        for field in ["ability_goal", "course_module", "practice_task", "periods", "equipment", "space", "assessment_artifact"]:
            if not r.get(field):
                findings.append(Finding("warning", "MAPPING_FIELD", f"{r.get('map_id')} 缺少 {field}", "data/课程设备空间映射.csv"))
        if not is_closed(r.get("status", "")):
            findings.append(Finding("warning", "MAPPING_OPEN", f"映射项未确认：{r.get('map_id')}", "data/课程设备空间映射.csv"))


def check_implementation(rows: list[dict[str, str]], findings: list[Finding]) -> None:
    for r in rows:
        if not r.get("phase_id"):
            continue
        for field in ["responsible", "task", "deliverable", "acceptance_criteria"]:
            if not r.get(field):
                findings.append(Finding("error", "IMPLEMENT_FIELD", f"{r.get('phase_id')} 缺少 {field}", "data/实施验收矩阵.csv"))


def check_final_text(text: str, evidence: list[dict[str, str]], findings: list[Finding]) -> None:
    for pattern in PLACEHOLDER_PATTERNS:
        for m in re.finditer(pattern, text, flags=re.I):
            line = text.count("\n", 0, m.start()) + 1
            findings.append(Finding("error", "PLACEHOLDER", f"终稿残留占位/待确认内容：{m.group(0)}", f"07_方案终稿.md:{line}"))
    verified_wording = "\n".join(r.get("allowed_wording", "") + " " + r.get("claim", "") for r in evidence if r.get("status") == "verified")
    for word in HIGH_RISK_WORDS:
        if word in text and word not in verified_wording:
            findings.append(Finding("error", "HIGH_RISK_WORD", f"终稿使用高风险词“{word}”，但证据台账无对应已核实表述", "07_方案终稿.md"))
    for word in OVERCOMMIT_WORDS:
        if word in text:
            findings.append(Finding("warning", "OVERCOMMIT_WORD", f"终稿存在过度承诺词“{word}”，请确认是否可控", "07_方案终稿.md"))
    if re.search(r"(?:竞赛|赛事|比赛)", text) and not any(r.get("status") == "verified" and ("竞赛" in r.get("claim", "") or "赛事" in r.get("claim", "")) for r in evidence):
        findings.append(Finding("warning", "COMPETITION_EVIDENCE", "终稿提及竞赛/赛事，但未发现已核实的赛事证据记录", "07_方案终稿.md"))


def check_formal_ai_tells(text: str, findings: list[Finding]) -> None:
    """阶段 6.5：正式方案语言净化（去 AI 味）。

    复用通用去 AI 味的*检测*目录（最毒句式/客套开场结尾/模板过渡/模糊限定/官腔空话/无证据强词/
    空泛修饰/机械化连接词），但**不**套用其口语化注入配方——正式文档保留庄重文风、完整句与必要标点。
    全部以 warning 级呈现，作为质量门禁提示，不阻断交付（语言润色非一票否决项）。
    完整策略见 references/formal_dereification.md。
    """
    for code, pattern, suggestion in FORMAL_AI_TELL_PATTERNS:
        for m in re.finditer(pattern, text):
            line = text.count("\n", 0, m.start()) + 1
            findings.append(Finding("warning", code, f"语言AI味（{m.group(0)}）：{suggestion}", f"07_方案终稿.md:{line}"))
    for w in FORMAL_FILLER_WORDS:
        for m in re.finditer(re.escape(w), text):
            line = text.count("\n", 0, m.start()) + 1
            findings.append(Finding("warning", "AI_TELL_FILLER", f"空泛修饰词『{w}』：建议补充对象与可量化尺度，或删除", f"07_方案终稿.md:{line}"))
    conn = sum(len(re.findall(re.escape(c), text)) for c in FORMAL_CONNECTORS)
    if conn > 3:
        findings.append(Finding("warning", "AI_TELL_CONNECTOR", f"机械化连接词（此外/然而/因此/与此同时/另一方面）出现 {conn} 次，建议精简，避免模板感", "07_方案终稿.md"))


def check_stage_docs(project: Path, findings: list[Finding]) -> None:
    """阶段文档完整性门槛：防止 00/01/02 等文档停留在空模板就推进。

    - 01_需求确认.md、02_调研与证据报告.md 为硬门槛（疑似空模板→error，阻断交付）；
    - 其余阶段文档为软提示（warning）。
    判定以"去除标题后的实质字数"低于阈值为准（裸模板通常只有 30~50 字）。
    """
    hard = {"01_需求确认.md": 60, "02_调研与证据报告.md": 80}
    soft = {
        "00_执行计划.md": 80, "03_顶层设计决策.md": 80, "04_方案大纲.md": 60,
        "05_方案初稿.md": 60, "06_评审汇总.md": 60, "08_交付说明.md": 40,
    }
    markers = ("以 `data/", "为准", "工作区", "TODO", "待确认", "示例")

    def body_len(text: str) -> int:
        body = re.sub(r"(?m)^\s*#.*$", "", text)
        return len(re.sub(r"\s", "", body))

    for name, minlen in hard.items():
        p = project / name
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        if body_len(text) < minlen:
            findings.append(Finding("error", "STAGE_DOC_EMPTY", f"{name} 实质内容不足（去除标题后 {body_len(text)} 字），疑似空模板，请填写实质内容后再推进", name))
    for name, minlen in soft.items():
        p = project / name
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        if body_len(text) < minlen and any(m in text for m in markers):
            findings.append(Finding("warning", "STAGE_DOC_THIN", f"{name} 内容偏薄（去除标题后 {body_len(text)} 字），建议补充实质内容", name))


def write_reports(project: Path, findings: list[Finding], metrics: dict) -> None:
    qa = project / "qa"
    qa.mkdir(exist_ok=True)
    report = {
        "passed": not any(f.severity == "error" for f in findings),
        "summary": {
            "errors": sum(f.severity == "error" for f in findings),
            "warnings": sum(f.severity == "warning" for f in findings),
            "info": sum(f.severity == "info" for f in findings),
        },
        "metrics": metrics,
        "findings": [asdict(f) for f in findings],
    }
    (qa / "validation_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# 项目确定性校验报告", "", f"- 结果：{'通过' if report['passed'] else '不通过'}", f"- 错误：{report['summary']['errors']}", f"- 警告：{report['summary']['warnings']}", "", "## 指标", "", "```json", json.dumps(metrics, ensure_ascii=False, indent=2), "```", "", "## 问题", ""]
    if findings:
        lines += ["| 严重级别 | 代码 | 位置 | 问题 |", "|---|---|---|---|"]
        for f in findings:
            lines.append(f"| {f.severity} | {f.code} | {f.location} | {f.message.replace('|', '／')} |")
    else:
        lines.append("未发现问题。")
    (qa / "validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="校验远播方案项目")
    parser.add_argument("project_dir")
    args = parser.parse_args()
    project = Path(args.project_dir).expanduser().resolve()
    findings: list[Finding] = []
    require_files(project, findings)
    if findings:
        write_reports(project, findings, {})
        return 1

    config = yaml.safe_load((project / "project.yaml").read_text(encoding="utf-8")) or {}
    tolerance = Decimal(str(config.get("validation", {}).get("amount_tolerance", 0.01)))
    requirements = read_csv(project / "data/需求响应矩阵.csv")
    evidence = read_csv(project / "data/事实证据台账.csv")
    pending = read_csv(project / "data/待确认事项.csv")
    budget = read_csv(project / "data/预算明细.csv")
    mapping = read_csv(project / "data/课程设备空间映射.csv")
    implementation = read_csv(project / "data/实施验收矩阵.csv")

    metrics = {
        "requirements": check_requirements(requirements, findings),
        "evidence": check_evidence(evidence, findings),
        "budget": check_budget(budget, findings, tolerance),
    }
    check_pending(pending, findings)
    check_mapping(mapping, findings)
    check_implementation(implementation, findings)
    check_stage_docs(project, findings)
    final_text = (project / "07_方案终稿.md").read_text(encoding="utf-8")
    check_final_text(final_text, evidence, findings)
    check_formal_ai_tells(final_text, findings)

    val_cfg = config.get("validation", {})
    if metrics["requirements"]["coverage"] < float(val_cfg.get("require_requirement_coverage", 1.0)):
        findings.append(Finding("error", "REQ_COVERAGE", f"强制需求覆盖率不足：{metrics['requirements']['coverage']:.2%}", "data/需求响应矩阵.csv"))
    if metrics["evidence"]["coverage"] < float(val_cfg.get("required_claim_coverage", 0.95)):
        findings.append(Finding("error", "EVIDENCE_COVERAGE", f"普通外部事实证据覆盖率不足：{metrics['evidence']['coverage']:.2%}", "data/事实证据台账.csv"))
    if metrics["evidence"]["high_coverage"] < float(val_cfg.get("high_risk_claim_coverage", 1.0)):
        findings.append(Finding("error", "HIGH_EVIDENCE_COVERAGE", f"高风险事实证据覆盖率不足：{metrics['evidence']['high_coverage']:.2%}", "data/事实证据台账.csv"))

    write_reports(project, findings, metrics)
    errors = sum(f.severity == "error" for f in findings)
    print(f"校验完成：{errors} 个错误，{sum(f.severity == 'warning' for f in findings)} 个警告")
    print(project / "qa/validation_report.md")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
