# Changelog
## [1.0.0] — 2026-08-18
首个可迁移发布包（打包自本地最新版，含全部历史迭代成果）。

### 核心能力
- 抽取：.docx / .pdf / .doc 文本抽取（extract_docx / extract_pdf / extract_doc_text），docx 图片证据导出为 `output/images/<safe>/img_NNN.png` 并插入 `[IMAGE: ...]` 标记
- 审查基准：按 `references/review-baseline-template.md` 提取废标条款、资格/形式要求、★/▲ 重点条款、评分标准、偏离表要求、技术参数证明材料要求汇总表、**明示允许/豁免条款清单（§七·五）**；补遗/澄清按「后发优先」合并（merge_addenda.py）
- 并行审查：每份响应文件一个独立子代理，对照基准产出逐份报告（7 项结构 + 图片目检）
- 机械核查：价格合规（verify_prices.py）、跨文件一致性（consistency_check.py）、评分估算（score_estimate.py）
- 终审交叉校验：audit_risks.py 对照明示允许清单复核风险项，防误判
- HTML 呈现：每份独立报告 + 汇总报告（render_report.py + 模板渲染）

### 四条铁律
1. 废标优先；2. 图片证据不可臆断；3. 偏离表诚信红线；4. **招标文件明示优先**（明示允许形式不得列为风险，风险必须有条款依据，形式合规≠实质响应）

### 关键改进（历史沉淀）
- 技术参数证明材料汇总对比（含出处）
- 每份响应独立 HTML 报告
- 补遗/澄清合并、评分量化、电子标核查、法律条文锚定
- 子代理提示词 R1-R4 硬性规则（明示允许不列为风险 / 风险必须有条款依据 / 明示条款优先于通用经验 / 形式合规≠实质响应）
- 案例沉淀：references/lessons-learned.md（含"偏离表空白=完全响应"误判案例）

### 依赖
- python-docx / olefile / pdfplumber（仅标准库脚本无需额外依赖）
