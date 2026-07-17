#!/usr/bin/env python3
"""初始化一个远播方案助手 V2.0 项目目录。"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import yaml


def main() -> int:
    parser = argparse.ArgumentParser(description="初始化方案项目目录")
    parser.add_argument("--name", required=True, help="项目名称")
    parser.add_argument("--type", default="A", choices=list("ABCDEF"), help="文档类型")
    parser.add_argument("--client", default="待确认", help="客户/学校名称")
    parser.add_argument("--output", required=True, help="项目目录")
    args = parser.parse_args()

    skill_root = Path(__file__).resolve().parents[1]
    template_root = skill_root / "templates"
    project_dir = Path(args.output).expanduser().resolve()
    if project_dir.exists() and any(project_dir.iterdir()):
        raise SystemExit(f"目标目录非空，拒绝覆盖：{project_dir}")

    project_dir.mkdir(parents=True, exist_ok=True)
    for folder in ["data", "sources", "assets", "reviews", "output", "qa"]:
        (project_dir / folder).mkdir(exist_ok=True)

    mapping = {
        "project.yaml": project_dir / "project.yaml",
        "需求响应矩阵.csv": project_dir / "data" / "需求响应矩阵.csv",
        "事实证据台账.csv": project_dir / "data" / "事实证据台账.csv",
        "课程设备空间映射.csv": project_dir / "data" / "课程设备空间映射.csv",
        "预算明细.csv": project_dir / "data" / "预算明细.csv",
        "实施验收矩阵.csv": project_dir / "data" / "实施验收矩阵.csv",
        "待确认事项.csv": project_dir / "data" / "待确认事项.csv",
        "07_方案终稿.md": project_dir / "07_方案终稿.md",
        "评审报告.md": project_dir / "reviews" / "评审报告模板.md",
    }
    for source_name, target in mapping.items():
        shutil.copy2(template_root / source_name, target)

    config_path = project_dir / "project.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["project"]["name"] = args.name
    config["project"]["document_type"] = args.type
    config["project"]["client"] = args.client
    config["project"]["title"] = f"{args.client}{args.name}方案" if args.client != "待确认" else args.name
    safe_name = "".join(c if c not in '\\/:*?\"<>|' else "_" for c in config["project"]["title"])
    config["output"]["filename"] = f"{safe_name}_v1.0.docx"
    config["output"]["header_text"] = config["project"]["title"]
    config_path.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8")

    stage_files = {
        "00_执行计划.md": "# 执行计划\n\n- 文档类型：\n- 交付目标：\n- 已有资料：\n- 缺失资料：\n- 调研任务：\n- 风险与约束：\n",
        "01_需求确认.md": "# 需求确认\n\n以 `data/需求响应矩阵.csv` 为准。\n",
        "02_调研与证据报告.md": "# 调研与证据报告\n\n以 `data/事实证据台账.csv` 为准，正文记录关键结论与来源。\n",
        "03_顶层设计决策.md": "# 顶层设计决策\n\n记录学校基因卡、设计备选、采用理由和被放弃方案。\n",
        "04_方案大纲.md": "# 方案大纲\n\n按文类确定章节，不机械套用固定六章。\n",
        "05_方案初稿.md": "# 方案初稿\n\n初稿工作区。\n",
        "06_评审汇总.md": "# 评审汇总\n\n记录独立评审结论、问题关闭状态和最终通过条件。\n",
        "08_交付说明.md": "# 交付说明\n\n- 交付版本：\n- 主要依据：\n- QA 结果：\n- 未纳入范围：\n",
    }
    for name, content in stage_files.items():
        (project_dir / name).write_text(content, encoding="utf-8")

    print(f"项目已初始化：{project_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
