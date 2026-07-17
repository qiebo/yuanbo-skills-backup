# 远播方案助手 V2.0

这是从 V1.0 重构后的教育项目方案生产 Skill。核心变化是把“写得像方案”升级为“有证据、可校验、可实施、可渲染验收”。

## 核心升级

- 事实证据台账：区分已核实事实、用户提供信息、推断、方案、目标和预期成效；
- 需求响应矩阵：确保用户强制要求覆盖率 100%；
- 课程—设备—空间映射与实施验收矩阵；
- 预算计算、证据覆盖、占位符和高风险表述的硬校验；
- 按文类选择评审角色，不再固定三方自评；
- Pandoc + python-docx 的 Word 构建器，支持 Markdown 表格、图片、链接和脚注；
- Word 逐页渲染和视觉检查；
- 批注、修订、高亮、颜色标记提取；
- 版本文字差异比较。

## 运行环境

- Python 3.10+
- Pandoc
- LibreOffice（渲染检查）
- Poppler / `pdftoppm`（逐页 PNG）
- Python 依赖：`pip install -r requirements.txt`

## 快速开始

```bash
python scripts/create_stylepacks.py
python scripts/init_project.py --name "人工智能实验室建设" --type A --client "某某中学" --output ./某某中学AI实验室
```

完成项目材料和台账后：

```bash
python scripts/validate_project.py ./某某中学AI实验室
python scripts/build_docx.py ./某某中学AI实验室
python scripts/render_review.py ./某某中学AI实验室/output/xxx.docx --output-dir ./某某中学AI实验室/qa/render
```

也可执行：

```bash
python scripts/run_pipeline.py ./某某中学AI实验室
```

流水线不会代替人工视觉检查。必须打开 `qa/render/page-*.png` 检查全部页面。

## 重要边界

- 找不到 `07_方案终稿.md` 时立即失败，不生成硬编码示例；
- Word 仅作为交付物，修改应回到 Markdown 和 CSV 台账；
- 政策、赛事、价格、产品规格等时效性内容必须在每个项目中重新核验；
- `references/top_design_playbook.md` 中的学校案例仅说明结构方法，不可当作当前事实直接复用。

## 目录模式

`project.yaml` 中 `output.toc_mode` 支持：

- `static`：默认。生成跨渲染器稳定的静态目录，适合自动化交付；
- `field`：使用 Word TOC 域，需在 Microsoft Word 中更新域后显示完整页码；
- `none`：不生成目录。
