---
name: yizhan-usage-report
description: Generate 生涯翼站/Yizhan school usage analytics reports from monthly statistics Excel files and SaaS backend aggregate data. Use for 生涯翼站数据统计分析、学期分析报告、学校使用情况报告、网站后台取数、数据登记表、HTML/PDF/Word 报告输出 workflows.
---

# 生涯翼站数据统计分析报告

Use this skill to run the recurring 生涯翼站 report workflow end to end with minimal human intervention.

## Inputs

Required:

- Monthly statistics Excel file, usually named like `学校-统计查询按月.xlsx`.
- Website backend access or a pre-collected `website_data.json`.

Optional:

- Login credential document. Read it only to log in; never persist credentials.
- Existing template-field inventory JSON.

## Workflow

1. Create a run folder with `input/`, `output/`, and `logs/`.
2. Extract Excel metrics:

```bash
python scripts/extract_excel_metrics.py --xlsx "input/学校-统计查询按月.xlsx" --out "output/excel_metrics.json"
```

3. Collect website aggregate data.
   - First read `references/website_collection.md`.
   - Prefer browser-use / browser agent login. Use Playwright or DevTools as fallback.
   - If login fails 3 times or captcha/credential ambiguity blocks progress, ask the user to complete login manually, then continue.
   - Persist only aggregate JSON as `output/website_data.json`.

4. Build the data registry:

```bash
python scripts/build_registry.py \
  --excel "output/excel_metrics.json" \
  --website "output/website_data.json" \
  --out-dir "output"
```

5. Render the HTML report:

```bash
python scripts/render_html_report.py \
  --registry "output/学校-生涯翼站报告数据汇总.json" \
  --out "output/学校-生涯翼站使用情况学期分析报告.html"
```

6. Export mobile-friendly PDF:

```bash
python scripts/export_html_pdf.py \
  --html "output/学校-生涯翼站使用情况学期分析报告.html" \
  --pdf "output/学校-生涯翼站使用情况学期分析报告.pdf"
```

7. Render the editable Word report:

```bash
python scripts/render_word_report.py \
  --registry "output/学校-生涯翼站报告数据汇总.json" \
  --out "output/学校-生涯翼站使用情况学期分析报告.docx"
```

8. Run QA:

```bash
python scripts/qa_report_bundle.py \
  --registry "output/学校-生涯翼站报告数据汇总.json" \
  --html "output/学校-生涯翼站使用情况学期分析报告.html" \
  --pdf "output/学校-生涯翼站使用情况学期分析报告.pdf" \
  --docx "output/学校-生涯翼站使用情况学期分析报告.docx"
```

## Non-negotiable Rules

- All report numbers must come from the data registry, not directly from raw Excel, website JSON, or old report text.
- Read `references/data_contract.md` before changing formulas or report wording.
- Read `references/qa_checklist.md` before final delivery.
- Read `references/user_guide.md` when the user asks how to prepare files, operate the skill, or migrate it to another agent.
- Do not save credentials, cookies, tokens, student-level rows, phone numbers, ID numbers, or student account lists.
- HTML + PDF are the default delivery files. Word and Excel/JSON are archive/editing files.

## Assets

- `assets/templates/yizhan-report-template.html`: offline HTML template.
- `assets/templates/yizhan-report-template.docx`: fixed Word template using 微软雅黑, white bold table headers, vertical cell alignment, and colored key metrics.
