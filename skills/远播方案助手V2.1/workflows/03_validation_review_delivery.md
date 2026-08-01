# 工作流：校验、评审与交付

1. 运行 `python scripts/validate_project.py 项目目录`。
2. 关闭所有 error 和一票否决问题（含 01/02 空模板硬门槛 STAGE_DOC_EMPTY）。
3. 处理 `validate_project.py` 产出的 **语言 AI 味 warning 项**（`AI_TELL_*` / `AI_TELL_FILLER` / `AI_TELL_CONNECTOR`）：逐项通读 `07_方案终稿.md` 对应行，按 `references/formal_dereification.md` 改写为正式、有据、有节奏的表达；warning 项不阻断交付，但应在交付前尽量减少。
4. 按文类选择评审角色，输出独立评审报告与 `06_评审汇总.md`。（核心/逐节点确认模式下，呈现评审结论请用户确认。）
4. 运行 `python scripts/build_docx.py 项目目录`；构建器已内建统一字体（默认微软雅黑）与正文段首缩进（默认 2 字符），覆盖正文、表格单元格与页眉页脚。需要覆盖写同名输出时加 `--overwrite`，旧版自动备份为 `_备份_时间戳`，避免时间戳改名导致后处理错位。
5. 运行 `python scripts/render_review.py 输出.docx --output-dir qa/render`；本机无 LibreOffice/soffice 时自动执行结构化降级验收（非视觉渲染），须人工复核版式。
6. 逐页检查并在 `qa/视觉检查清单.md`（降级时为 `结构降级检查清单.md`）记录结果。
7. 输出 `08_交付说明.md`，列明版本、依据、未纳入范围和后续修改入口。
