#!/usr/bin/env python3
"""Local structural lint for yuanbo-school-proposal-team.

Stdlib-only. Validates package invariants we control locally. It does NOT
replace WorkBuddy's official validate_expert.py.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / ".codebuddy-plugin" / "plugin.json"
SETTINGS = ROOT / "settings.json"


def fail(msg: str) -> None:
    print(f"ERROR: {msg}")
    raise SystemExit(1)


def warn(msg: str) -> None:
    print(f"WARN: {msg}")


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"cannot parse JSON {path}: {exc}")


def frontmatter(text: str) -> str:
    m = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, flags=re.S)
    return m.group(1) if m else ""


def fm_scalar(fm: str, key: str):
    m = re.search(rf"(?m)^{re.escape(key)}:\s*['\"]?([^'\"\n]+)['\"]?\s*$", fm)
    return m.group(1).strip() if m else None


def fm_skills(fm: str):
    m = re.search(r"(?m)^skills:\s*\[(.*?)\]\s*$", fm)
    if not m:
        return []
    return [x.strip().strip("'\"") for x in m.group(1).split(",") if x.strip()]


def must_contain(path: Path, needles: list[str]):
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            fail(f"{path.relative_to(ROOT)} missing required mechanism: {needle}")


def main() -> None:
    if not PLUGIN.exists():
        fail("missing .codebuddy-plugin/plugin.json")
    if not SETTINGS.exists():
        fail("missing settings.json")

    plugin = load_json(PLUGIN)
    settings = load_json(SETTINGS)
    required = [
        "name", "version", "expertType", "agentName", "teamInfo", "agents",
        "skills", "displayName", "profession", "displayDescription",
        "categoryId", "defaultInitPrompt", "tags", "quickPrompts", "members", "plugin"
    ]
    for k in required:
        if k not in plugin:
            fail(f"plugin.json missing key: {k}")
    if plugin["expertType"] != "team":
        fail("expertType must be team")
    lead = plugin["agentName"]
    if plugin["teamInfo"].get("leadAgent") != lead:
        fail("teamInfo.leadAgent must equal agentName")
    if settings.get("agent") != lead:
        fail("settings.json agent must equal plugin agentName")
    if len(plugin.get("tags", [])) != 3:
        fail("tags must contain exactly 3 items")
    if len(plugin.get("quickPrompts", [])) != 3:
        fail("quickPrompts must contain exactly 3 items")
    if plugin.get("defaultInitPrompt") != plugin.get("quickPrompts", [None])[0]:
        fail("defaultInitPrompt must equal quickPrompts[0]")

    agent_paths = [ROOT / p.removeprefix("./") for p in plugin["agents"]]
    for p in agent_paths:
        if not p.exists():
            fail(f"missing agent file: {p.relative_to(ROOT)}")

    member_ids = [m["id"] for m in plugin["members"]]
    if len(member_ids) != len(set(member_ids)):
        fail("duplicate member id")
    if lead not in member_ids:
        fail("lead missing from members")
    declared_members = plugin["teamInfo"].get("memberAgents", [])
    if set(declared_members) != set(member_ids) - {lead}:
        fail("teamInfo.memberAgents does not match non-lead members")

    agent_ids = []
    all_referenced_skills = set()
    for p in agent_paths:
        text = p.read_text(encoding="utf-8")
        if "[TODO]" in text or "<TODO>" in text:
            fail(f"TODO placeholder in {p.name}")
        fm = frontmatter(text)
        if not fm:
            fail(f"missing YAML frontmatter: {p.name}")
        name = fm_scalar(fm, "name")
        if not name:
            fail(f"missing frontmatter name: {p.name}")
        if p.stem != name:
            fail(f"filename/name mismatch: {p.name} vs {name}")
        agent_ids.append(name)
        all_referenced_skills.update(fm_skills(fm))
        if len(text) > 14000:
            warn(f"agent prompt is long ({len(text)} chars): {p.name}")

    # V0.8.0 prompt budget: keep dispatch prompts executable instead of
    # repeating the deep method already carried by shared Skills.
    prompt_budgets = {
        "proposal-team-lead.md": 8000,
        "requirement-analyst.md": 7000,
    }
    for filename, budget in prompt_budgets.items():
        path = ROOT / "agents" / filename
        if len(path.read_text(encoding="utf-8")) > budget:
            fail(f"{path.relative_to(ROOT)} exceeds V0.8.0 prompt budget: {budget} chars")

    if set(agent_ids) != set(member_ids):
        fail("plugin members do not match agent frontmatter names")

    skill_dirs = [ROOT / p.removeprefix("./") for p in plugin["skills"]]
    skill_names = set()
    for d in skill_dirs:
        f = d / "SKILL.md"
        if not f.exists():
            fail(f"missing skill file: {f.relative_to(ROOT)}")
        text = f.read_text(encoding="utf-8")
        fm = frontmatter(text)
        if not fm:
            fail(f"missing skill frontmatter: {f.relative_to(ROOT)}")
        name = fm_scalar(fm, "name")
        if not name:
            fail(f"missing skill name: {f.relative_to(ROOT)}")
        skill_names.add(name)
        if len(text) > 11000:
            warn(f"skill is long ({len(text)} chars): {name}")

    missing_refs = all_referenced_skills - skill_names
    if missing_refs:
        fail(f"agents reference missing skills: {sorted(missing_refs)}")

    # V0.2.1 critical mechanisms must not regress.
    must_contain(ROOT / "agents/proposal-team-lead.md", [
        "QA_CLOSURE_REPORT", "artifact_meta.producer", "clientization_guard", "--term"
    ])
    must_contain(ROOT / "agents/requirement-analyst.md", [
        "clientization_guard", "internal_only_terms", "artifact_meta"
    ])
    # V0.6.0 requirement clarification gate must not regress.
    must_contain(ROOT / "agents/proposal-team-lead.md", [
        "CLARIFY_PLAN", "mode: intake", "mode: final", "clarify_trace",
        "clarify_waived", "AskUserQuestion", "requirement_assessment",
        "按需", "首轮 pass，或 revise 后 closure pass",
    ])
    must_contain(ROOT / "agents/requirement-analyst.md", [
        "CLARIFY_PLAN", "gap_analysis", "material_request", "direction_options",
        "clarify_trace", "non_blocking", "requirement_assessment", "候选评估维度",
    ])
    must_contain(ROOT / "skills/proposal-core/SKILL.md", [
        "CLARIFY_PLAN", "clarify_waived", "需求澄清三段式", "评估在前", "按需",
    ])
    must_contain(ROOT / "agents/quality-reviewer.md", [
        "review_mode: closure", "QA_CLOSURE_REPORT", "dynamic_terms_checked"
    ])
    must_contain(ROOT / "agents/proposal-writer.md", [
        "REVISED_DRAFT", "claimed_closed_revision_ids", "clientization_checked",
        "SECTION_OUTLINE", "DRAFT_part",
    ])
    # V0.7.0 contract-field completeness must not regress.
    must_contain(ROOT / "agents/top-design-architect.md", [
        "downstream_dispatch", "depth_plan",
    ])
    must_contain(ROOT / "agents/proposal-team-lead.md", [
        "downstream_dispatch", "depth_plan", "direction_confirmed",
        "SECTION_OUTLINE", "门禁矩阵", "路线裁剪", "C-single", "C-multi",
        "design_approved", "outline_approved", "present_files",
    ])
    must_contain(ROOT / "skills/proposal-core/SKILL.md", [
        "SECTION_OUTLINE", "门禁按路线裁剪", "A-single_space", "A-multi_space",
        "A-center_level", "C-single", "C-multi", "design_approved",
        "outline_approved", "present_files",
    ])
    for rel in ["tests/leak_scan.py", "tests/leak_terms.txt", "tests/test_leak_scan.py"]:
        if not (ROOT / rel).exists():
            fail(f"missing V0.2.1 gate file: {rel}")

    # V0.7.0 cross-file consistency: the two leak_scan.py copies must stay in
    # lockstep except for the default-terms-path lines.
    _allow = ("leak_terms.txt", "Path(__file__)", "next to this script", "the bundled")
    _scan_a = [ln for ln in (ROOT / "tests" / "leak_scan.py").read_text(encoding="utf-8").splitlines()
               if not any(k in ln for k in _allow)]
    _scan_b = [ln for ln in (ROOT / "skills" / "proposal-qa" / "scripts" / "leak_scan.py").read_text(encoding="utf-8").splitlines()
               if not any(k in ln for k in _allow)]
    if _scan_a != _scan_b:
        fail("leak_scan.py copies drifted apart (tests/ vs skills/proposal-qa/scripts/)")

    print("OK: local package structure is internally consistent")
    print(f"  version: {plugin['version']}")
    print(f"  agents: {len(agent_ids)} (1 lead + {len(agent_ids)-1} members)")
    print(f"  skills: {len(skill_names)}")
    print("  critical gates: artifact proof + clientization + QA closure + dynamic leak scan")
    print("  next: run tests/test_leak_scan.py and WorkBuddy official validate_expert.py")


if __name__ == "__main__":
    main()
