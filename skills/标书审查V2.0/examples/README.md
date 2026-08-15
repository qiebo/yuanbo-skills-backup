# examples/ — 脱敏虚构样例库（标书审查 V2.1）

> 全部数据均为**脱敏虚构**（公司名「示例科技股份有限公司」、项目「虚构智慧校园平台」、金额/日期虚构），**不涉及任何真实标书**。
> 双重用途：① 作为子代理输出格式范本，稳定审查/终审报告结构；② 作为端到端测试夹具（抽取 → 补遗合并 → 评分估算 → 渲染）。

## 文件
| 文件 | 内容 | 用途 |
|---|---|---|
| `baseline.md` | 一份虚构招标文件的**审查基准**（含「补遗与澄清清单」字段、§五「技术参数响应证明材料要求汇总表」、带 分项/分值/权重/评分标准 列的评分表） | 子代理对齐基准格式；`score_estimate.py` 的 `--baseline` 夹具 |
| `subagent_report_01.md` | 一份虚构响应文件（甲）的**子代理报告**（含【原文】【位置：第X节约Y页】、③·五 证明材料核查表、评分逐项估分表） | 稳定子代理输出 |
| `final_report.md` | 一份虚构**终审汇总报告**（含「得分对比」「三·五 证明材料汇总对比」章节、零分项预警） | 稳定终审格式 |
| `report_data.json` | 上述终审报告各 section 拼成的 HTML 片段（键=汇总模板全部 **19** 个 token，含 TECH_PROOF_TABLE / TECH_PROOF_NOTES） | `render_report.py` 汇总渲染的 `--data` 输入 |
| `final_report.html` | 由 `render_report.py` 渲染 `report_data.json` + `assets/report-template.html` 的结果（视觉对照） | 汇总渲染对照 |
| `file_report_01_data.json` | 文件甲单份报告各 section 拼成的 HTML 片段（键=每份模板全部 **15** 个 token，与 subagent_report_01.md 自洽） | `render_report.py` 每份渲染的 `--data` 输入 |
| `file_report_01.html` | 由 `render_report.py` 渲染 `file_report_01_data.json` + `assets/file-report-template.html` 的结果 | 每份独立报告渲染对照 |

## 端到端验证（V2.1）
```bat
PY="C:\Users\qiebo\.workbuddy\binaries\python\versions\3.13.12\python.exe"
%PY% -m venv .venv && .venv\Scripts\activate && pip install python-docx olefile pdfplumber

REM 1) 评分估算（读 baseline.md + 示例响应）
.venv\Scripts\python.exe scripts/score_estimate.py --baseline examples/baseline.md --docs examples/subagent_report_01.md --limit 600000 --out output/评分估算.md

REM 2) 每份响应独立 HTML 报告（15 token，残留兜底）
.venv\Scripts\python.exe scripts/render_report.py --template assets/file-report-template.html --data examples/file_report_01_data.json --out examples/file_report_01.html --strict

REM 3) 汇总 HTML 报告（19 token，残留兜底）
.venv\Scripts\python.exe scripts/render_report.py --template assets/report-template.html --data examples/report_data.json --out examples/final_report.html --strict

REM 4) 残留校验（期望无输出）
grep -n "{{" examples/file_report_01.html examples/final_report.html
```
