# 工作流：校验、评审与交付

1. 运行 `python scripts/validate_project.py 项目目录`。
2. 关闭所有 error 和一票否决问题。
3. 按文类选择评审角色，输出独立评审报告与 `06_评审汇总.md`。
4. 运行 `python scripts/build_docx.py 项目目录`。
5. 运行 `python scripts/render_review.py 输出.docx --output-dir qa/render`。
6. 逐页检查并在 `qa/视觉检查清单.md` 记录结果。
7. 输出 `08_交付说明.md`，列明版本、依据、未纳入范围和后续修改入口。
