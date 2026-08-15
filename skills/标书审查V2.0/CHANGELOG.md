# Changelog

## [2.1.0]
### Added
- 技术参数证明材料汇总：references/review-baseline-template.md §五新增「技术参数响应证明材料要求汇总表」（无论是否 ★/▲ 均提取并标注出处）；references/report-template.md 新增「三·五、证明材料汇总对比」章节；子代理提示词新增 ③·五 逐项核查指引
- 每份响应独立 HTML 报告：新增 assets/file-report-template.html（15 token，复用汇总模板暗色 CSS）；SKILL.md 第5步拆为 5a 每份渲染 / 5b 汇总渲染
- 汇总模板 assets/report-template.html 新增证明材料汇总对比 section 与 TECH_PROOF_TABLE / TECH_PROOF_NOTES 两个 token（17 → 19 token）
- examples/ 新增 file_report_01_data.json + file_report_01.html（每份报告样例）；baseline.md / subagent_report_01.md / final_report.md / report_data.json 同步补证明材料表并保持自洽

### Changed
- SKILL.md frontmatter version 2.0.0 → 2.1.0；description 增补「技术参数证明材料汇总与每份独立HTML报告」
- examples/README.md 更新文件清单与端到端命令（含每份渲染命令）

### Notes
- 纯模板/文档改动：render_report.py 等脚本零改动、零新增依赖；渲染 token 数由模板动态扫描，脚本无需感知

## [2.0.0]
### Added
- P2-8 补遗/澄清合并：scripts/merge_addenda.py + 审查基准「补遗与澄清清单」字段 + SKILL.md 多输入/合并工作流
- P2-9 评分量化：scripts/score_estimate.py + 报告「得分对比」章节 + 子代理逐项估分指引
- P2-14 电子标：checklist 电子标专用核查项（CA/加密/回执/签章完整性）+ SKILL.md 局限说明
- P2-10 法律依据：checklist 废标情形条文锚定（标注「依据：…」，不替代法律意见）
- P2-12 examples/ 脱敏样例库（基准 + 子代理报告 + 终审报告 + 渲染对照）
- P2-13 HTML 渲染脚本化：scripts/render_report.py + 占位符残留兜底

### Changed
- SKILL.md frontmatter version 1.1.0 → 2.0.0
- references/report-template.md 增加「得分对比」章节；评分标准列对齐脚本（分项/分值/权重/评分标准）
- assets/report-template.html 增加得分对比 section 与 SCORE_TABLE / SCORE_NOTES token（共 17 token）
- references/review-baseline-template.md 增加「补遗与澄清清单」字段

### Notes
- 无新增运行时依赖（merge_addenda / score_estimate / render_report 仅用标准库）
- 评分估算为保守辅助估分，非评标结论；补遗语义合并由 LLM 按后发优先裁决

## [1.1.0]
### Added
- P0 环境/路径修复（托管 Python + venv，清除失效 miniconda/DELL 路径）
- P0 PDF 支持：scripts/extract_pdf.py（pdfplumber）
- P0 图片导出 + 视觉核查：extract_docx.py --extract-images + 图片目检步骤
- P1 抽取保真度（表格内图/页眉页脚/文本框/VML/合并单元格/位置标记）
- P1 机检脚本：verify_prices.py / consistency_check.py
- P1 证据引用强制化（【原文】【位置】+ 终审回读）
- P2 HTML 占位符 `{{` grep 检查
