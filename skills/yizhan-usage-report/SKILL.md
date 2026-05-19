---
name: yizhan-usage-report
description: Generate 生涯翼站/Yizhan school usage analytics reports from monthly statistics Excel files and SaaS backend aggregate data. Use for 生涯翼站数据统计分析、学期分析报告、学校使用情况报告、网站后台取数、数据登记表、Word 报告输出 workflows.
---

# 生涯翼站数据统计分析报告

Use this skill to run the recurring 生涯翼站 report workflow end to end with minimal human intervention.

## Inputs

Required:

- Monthly statistics Excel file, usually named like `学校-统计查询按月.xlsx`.
- Website backend access or a pre-collected `website_data.json`.

Optional:

- Login credential document. Read it only for the current login attempt; never persist credentials.
- Existing template-field inventory JSON.

## Mandatory Execution Contract

Before doing any work, show the user an 8-task checklist with statuses. Update it after each task. Do not hide the execution flow.

Fixed tool policy:

- Environment/files/scripts: use shell + bundled Python scripts.
- Website login default on WorkBuddy/Codex: run the stable API login check first:
  `npm install` once, then `npm run login:check -- --credentials "<登录信息.txt>" --target-school "<学校名>" --out "output/login_check.json"`.
- The login helper uses `/api/login_platform` to avoid the unstable webpage captcha form. It only persists login check metadata, never credentials, cookies, tokens, or authorization headers.
- If a same-run browser session is required, run the helper with `--open-browser`; do not persist the browser profile after handoff.
- If automatic login fails, captcha/MFA blocks progress, credentials are unclear, or authenticated school identity cannot be confirmed, stop and ask the user to complete login manually or provide `website_data.json`.
- Do not loop through browser tools, do not repeatedly open/close browsers, and do not retry credential submission. One automatic attempt is the default budget for Task 3.
- After automatic or user-assisted login succeeds, use the active authenticated session only to confirm backend school identity and collect aggregate website data.
- If `website_data.json` fails validation, stop and ask for website login/data collection assistance. Do not generate a report.

## Required Task List

### Task 1 - Preflight

Check inputs, output folders, Python packages, Node/npm availability, optional browser availability, and templates.

```bash
python scripts/preflight_check.py --input-dir "input" --output-dir "output" --install
```

Completion gate:

- Monthly statistics Excel is identified.
- Python dependencies are available.
- Node.js/npm are available for the stable Task 3 login helper, or the user can provide manual login/`website_data.json`.
- Browser availability is reported as a warning only. If no browser is available, still run the API login helper; skip only browser-session injection and ask the user for manual browser login if the downstream collection requires it.
- If any required input is missing, ask the user to provide it and stop.

### Task 2 - Excel Extraction

Extract and validate monthly Excel metrics.

```bash
python scripts/extract_excel_metrics.py --xlsx "input/学校-统计查询按月.xlsx" --out "output/excel_metrics.json"
```

Completion gate:

- `output/excel_metrics.json` exists.
- School name, data period, `总计` row, cumulative interactions, and active peak are present.

### Task 3 - Website Login

Read `references/website_collection.md`, then run the controlled login flow:

1. If a valid `output/website_data.json` already exists, skip login and proceed to Task 4 validation.
2. Otherwise run the stable login helper once:
   ```bash
   npm install
   npm run login:check -- --credentials "../登录信息.txt" --target-school "学校名" --out "output/login_check.json"
   ```
3. If `output/login_check.json` returns `status: ok`, confirm `backend_school` and continue to Task 4.
4. If the downstream website collection needs an active browser, run the same helper with `--open-browser` for the current run only.
5. If automatic login fails or identity cannot be confirmed, pause and ask the user to complete login manually, then reply with: `我已完成生涯翼站后台登录，可以继续取数。`
6. Do not keep trying browser automation while waiting for the user.

Completion gate:

- Automatic login succeeds, or the user confirms manual login is complete.
- Backend school identity is confirmed and matches the Excel school or the user confirms the difference.
- If neither automatic nor user-assisted login produces a confirmed backend identity, stop at Task 3 and ask the user to provide `website_data.json`. Do not proceed to Task 4.

### Task 4 - Website Data Collection

Collect only aggregate website data and save `output/website_data.json`. Then validate it:

```bash
python scripts/validate_website_data.py --website "output/website_data.json" --excel-metrics "output/excel_metrics.json"
```

Completion gate:

- Student account total, module aggregates, content stats, and backend record trend are non-empty.
- Validation returns `status: ok`.
- If validation fails, ask the user for login/data-collection assistance and stop. Do not create empty reports.

### Task 5 - Data Registry

```bash
python scripts/build_registry.py \
  --excel "output/excel_metrics.json" \
  --website "output/website_data.json" \
  --out-dir "output"
```

Completion gate:

- Registry JSON and XLSX are generated.
- `build_registry.py` succeeds. It will fail if website data is incomplete.

### Task 6 - Report Generation

Render the Word report from the registry only. The Word report is the default final deliverable; do not generate HTML or PDF unless the user explicitly asks for them.

```bash
python scripts/render_word_report.py \
  --registry "output/学校-生涯翼站报告数据汇总.json" \
  --out "output/学校-生涯翼站使用情况学期分析报告.docx"
```

Completion gate:

- DOCX exists and is non-empty.
- The Word report follows the provided template structure: same chapter order, same table count, same table row/column structure, and no agent-added modules.
- Render scripts do not report incomplete registry errors.

### Task 7 - QA

```bash
python scripts/qa_report_bundle.py \
  --registry "output/学校-生涯翼站报告数据汇总.json" \
  --docx "output/学校-生涯翼站使用情况学期分析报告.docx"
```

Completion gate:

- QA returns `status: ok`.
- If QA fails, fix the failure and rerun Task 7 before handoff.

### Task 8 - Handoff

Summarize final outputs, unresolved limitations, and any user-assisted login steps. Provide file paths for the Word report, registry XLSX, and registry JSON.

## Non-negotiable Rules

- All report numbers must come from the data registry, not directly from raw Excel, website JSON, or old report text.
- Never generate Word reports from missing, empty, or unvalidated website data.
- Never continue after failed website login. Task 3 allows one controlled automatic login attempt; if it fails, ask the user to finish login, then resume from Task 3/4 only after the user confirms.
- Never keep opening and closing browsers in an attempt to solve login. If the first automatic attempt does not produce an authenticated session, stop and ask for user help or a pre-collected `website_data.json`.
- Every task must have an explicit completion gate before moving to the next task.
- Read `references/data_contract.md` before changing formulas or report wording.
- Read `references/qa_checklist.md` before final delivery.
- Read `references/user_guide.md` when the user asks how to prepare files, operate the skill, or migrate it to another agent.
- Do not save credentials, cookies, tokens, student-level rows, phone numbers, ID numbers, or student account lists.
- Word is the default final report. Registry XLSX/JSON are audit and archive files. HTML/PDF are not default deliverables.
- Tables should stay on one page where the template allows it. Do not enable repeated table headers that make one logical table look like two tables after pagination.
- Analysis paragraphs must vary by grade, module, risk level, or operational action. Even when two rows have similar values, do not reuse the same explanatory sentence or suffix.
- AI 模拟面试分析只能使用登记表中已获取的服务学生、使用人次、生成报告、报告转化等聚合字段。不得擅自写“港澳高校申请”、具体申请类型、年级主力用户等未在系统数据中开放或未取证的场景判断。
- 正式报告必须按学校领导汇报口径写作。不要把内部审计式限制说明、泛泛功能介绍或“提供不了决策信息”的句子放进正文；每段分析至少要回答“这对学校管理/年级运营/心理支持/升学服务意味着什么，下一步怎么做”。

## Assets

- `assets/templates/yizhan-report-template.docx`: Word template using the approved report structure. When a user-provided template exists, copy and fill that template instead of rebuilding a similar-looking document.
