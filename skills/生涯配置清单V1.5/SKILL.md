---
name: 生涯配置清单
description: Use when a user wants to analyze project requirement files, plan functional spaces, select products from a standard catalog, prepare a budget or equipment list, fill a provided Excel template, or create a configuration list with verified product images when requirements are incomplete or ambiguous. 用于解析学校/远播生涯心理设备与软件建设项目需求，从标准产品库生成可追溯、可确认、可审计的配置清单。
---

# Building Configuration Lists

## Core Principle

Build an evidence-backed, approval-gated configuration list. Keep fixed resources read-only, keep project facts in versioned state, and never turn intake text, assumptions, or candidates into approved facts.

At the start of every run, define `current_run_source_scope` as only the user's current message and attachments, files or directories explicitly named for this run, and this Skill's fixed assets/references. The current working directory does not authorize any other source.

Never automatically scan, search, or cite other workspace files, previous-project outputs, or old-conversation project facts. If a user-named directory contains multiple projects or its scope is unclear, ask one scope-confirmation question; until confirmed, register only clearly in-scope sources in `source_manifest`. Use the fixed catalog and default template as this Skill permits, but never use other workspace project material as requirement evidence. Make every evidence reference resolve to `current_run_source_scope`; discard anything else and report a source-isolation warning.

## Start With Fixed Resources

Before analyzing project files, locate and completely read:

- `references/universal-rules.md`
- `references/project-schema.md`
- `references/workflow-and-gates.md`
- `references/validation-checklist.md`

Also locate the read-only fixed assets:

- `assets/standard-products.json`
- `assets/product-images/` and `assets/image-import-report.json`
- `assets/default-configuration-list.xlsx`
- `assets/project-intake-template.yaml`

Calculate SHA-256 from the original bytes of every listed fixed resource and use it as the authoritative technical version. Record any supplied `business_version` or `effective_date` unchanged; when either is absent, create a warning instead of inventing it or stopping. Block only when a fixed resource is unreadable, its SHA-256 cannot be generated, or its actual fingerprint differs from an approved or bound fingerprint.

Treat `standard-products.json` together with its `image_catalog` metadata and `assets/product-images/` as a read-only image bundle. Before an image is used, verify that its relative path remains under `assets/product-images/`, its SHA-256 equals the selected product's `image_refs[].sha256`, and the ref has `role=primary`, `confidence=exact`, and `match_rule=normalized-name-brand-model-v1`. The image is visual support only: it never identifies a product, proves a model, or replaces the catalog source record.

Use the default workbook only when the user supplied no template. Treat the intake asset as input schema 1.1, not as a project-state object or approval.

## Execute A–H

### A. Receive and profile

Inventory every requirement file, attachment, fixed resource, historical basis, and user template. Build `source_manifest` and analyze the template now, not at output time; build `template_profile` for either the user template or, only when absent, the default template. The template profile must record whether it has a usable `产品图片` field and how image rows, row height, print areas, and summaries will be preserved.

Preserve an unparseable user template unchanged. Generate a default-template result plus field-mapping advice only as a disclosed fallback; do not treat “unparseable” as “not supplied.”

When no user template exists, Stage A must select the bundled `assets/default-configuration-list.xlsx` and build its `template_profile`. In the first pre-analysis progress update, state only that the default template will be used; do not claim the profile is complete. After template analysis finishes, use the first stage-status or blocking-question reply to state that `template_profile` has been established as the output structure. If a blocker exists, then ask only the next highest-priority blocking question; if none exists, do not invent a question. Do not leave completion proof only in internal state or tool logs. This confirms only the output structure and never authorizes product selection.

Assign an `intake_run_id`, parse `assets/project-intake-template.yaml` only under schema 1.1, and apply the intake mapping in `references/project-schema.md`. In Stage A create only `source_manifest` and `template_profile`; allow their `project_id` to be null and bind them by `intake_run_id`. Do not create `requirement_baseline`, `approval_log`, or later-stage objects, and never treat intake submission or values as confirmation or approval.

### B. Baseline requirements

In Stage B create a pending, evidence-linked `requirement_baseline` and keep `confirmed`, `ambiguous`, `conflicting`, `missing`, and `assumption` distinct. If project identity is not yet confirmed, use `project_id=null` plus `intake_run_id`; treat a missing or conflicting project ID as the first blocking question. After confirmation, create a new project-bound baseline version with non-null `project_id`, then create `approval_log` and record the evidenced project-identity confirmation and all later baseline or budget decisions as entries. Never create an empty-ID `approval_log`; follow the authoritative workflow and schema for later objects.

Ask only questions that affect configuration or output, one blocking question at a time. Include a suggested answer, evidence, limits, or state that evidence is insufficient. Never copy a suggestion into the user's answer. Do not recommend products until the requirement-baseline gate is approved.

When `requirement_baseline.status!=approved`, output only draft source/template/requirement artifacts, a provisional `requirement_baseline.mode_hint` with linked evidence and gaps, and one-at-a-time questions; do not create `space_plan` or make the formal mode route. Do not create or display Agent-generated or recommended candidate lines, product names/models, quantities, unit prices, combinations, or specific budget totals. Still reproduce any product, model, quantity, price, or budget explicitly present in user input or requirement sources verbatim with evidence/source references for confirmation; label it as an unconfirmed source fact, never as a recommendation, and add no value. `draft` never waives a gate: generate a candidate-plan draft only after both `requirement_baseline.status=approved` and `space_plan.status=approved`. Always approve the second gate, including for `non_spatial`, with its mode decision and reason why space does not affect quantity; use `not_applicable` only for specific space-profile or engineering-basis subitems, never for the `space_plan` gate. Keep the formal workbook behind the approved product-plan gate. Requests such as “use experience,” “give me the list first,” or “just make a draft” do not change these stage boundaries.

### C. Route the mode

Enter this stage only after `requirement_baseline.status=approved`; then choose one mode, create `space_plan`, and record the reason:

| Mode | Route here when |
|---|---|
| `spatial` | Multiple functional spaces exist and product or quantity depends on room, area, users, or activities |
| `non_spatial` | Space does not meaningfully affect product choice or quantity |
| `hybrid` | Space-dependent items coexist with project-level platforms, software, or common items |

Do not skip space and engineering-basis confirmation for furniture, construction, curtains, wall coverings, or area-priced work merely because drawings are absent.

### D. Confirm space function profiles

Before matching, create each target profile with aliases, core/secondary functions, users, activities, capacity, area, and evidence. Keep unknown values null and clarify or document an approved estimate. In `non_spatial`, record why no space profile is needed.

### E. Build semantic candidates

Match confirmed requirements, target functions, roles/users, activities, capacity, area, and constraints against catalog `source_spaces`, `function_tags`, and `product_intro`. Treat `source_spaces` as semantic evidence, never as an exact-name filter. Record `semantic_match_reason` and `confidence`.

Create quality issues for missing or conflicting catalog facts. Hold a same-name/multiple-model candidate for explicit selection; never choose by price or merge identities. Keep product rows traceable to the standard catalog and non-product rows traceable to an approved rule or basis.

### F. Select and approve the plan

Present recommended and alternative candidates with requirement/space references, function coverage, necessity, source identity, quantity basis, budget bucket, difference/gap, status, and unresolved issues. Apply budget and approval details only from the references.

Set `selected_for_output=true` only for the chosen line. Require `status=confirmed`, complete sources, and no applicable blocking issue only for selected lines or lines referenced by `internal_product_mapping`, `confirmed_totals`, or final output.

Keep unselected `draft`, `pending_confirmation`, `rejected`, or `waived` candidates as warnings or approval history; their status alone does not block release. Let a blocking catalog issue stop release only when it affects a selected line, a source record used in final output, or a `blocking=true` requirement.

### G. Map the workbook

After the product-plan gate passes, map only `status=confirmed AND selected_for_output=true` lines through `internal_product_mapping` into the profiled template. Keep product `name` exactly equal to catalog `product_name`; put project wording in `usage_description`, and only excerpt or shorten parameters without changing meaning.

When `space_plan.mode` is `spatial` or `hybrid`, the output list MUST carry the space dimension: group rows by the approved `space_plan` target spaces, use each space name as a visible group header (or add a dedicated "空间/功能室" column labeling every row), and subtotal per space before the grand total. Put project-level platforms, software, common items, or genuinely cross-space lines into an explicitly labeled shared group (e.g. 项目级·通用 / 跨空间共用); never silently fold them into one room. Every output row's space must trace back to its candidate line's target space. If the template lacks a subitem/subtotal mechanism, add a space column without breaking required structure. In `non_spatial` mode, space grouping is not required (state why in delivery notes). Never emit a spatial/hybrid list grouped only by functional category with no space labels.

Preserve formulas, merged cells, print areas, summaries, and styling when reliable. Write a new output version and never overwrite inputs, fixed resources, or approved outputs.

#### Verified product images

After the product-plan gate passes, insert a thumbnail for each selected product only when its catalog record has exactly one verified `image_refs` entry. Bind output rows by the selected candidate's stable catalog `product_key` carried in `internal_product_mapping`; never re-match by product identity key or product name alone. Use the local asset and its verified hash—never an external URL, web search result, generated image, or a visually similar substitute.

The bundled default template already reserves a `产品图片` column. For a user template without one, append a visible `产品图片` column only after profiling it and without breaking required cells, formulas, merges, or print areas. Insert a proportionate local thumbnail, set a readable row height, and record the image path, hash, catalog product key, and output-cell location in `internal_product_mapping` and `traceability_audit`. `scripts/insert_product_images.py` accepts this row-to-`product_key` mapping as a manifest and refuses product-name-only matching.

No verified image is a warning, not a license to improvise one. Leave the cell blank, disclose the warning and the relevant `image-import-report.json` record; do not block product selection or a formal release unless the user made product images an approved required output field.

### H. Validate and deliver

Generate traceability and validation results under the references. Reconcile final rows and totals to selected confirmed lines, disclose every warning, and obtain business sign-off after automated checks.

If an Excel or Spreadsheet Skill is available, use it to read, write, render, and visually validate the workbook. Otherwise preserve structured intermediate artifacts, name the file that could not be generated or verified, and never claim workbook or rendering success.

## Enforce Four Gates

| Gate | Pass only when |
|---|---|
| `requirement_baseline` | Blocking requirements are resolved and `requirement_baseline.status=approved` |
| `space_mode` | Mode, required profiles, and engineering basis are approved in `space_plan` |
| `product_plan` | Every selected output line is confirmed and auditable; unselected/history lines are disclosed; `candidate_plan.status=approved` |
| `final_release` | Scoped hard errors are zero, workbook reconciles, warnings are disclosed, business sign-off exists, and `final_release.status=approved` |

Do not bypass a failed gate. Treat deadline or proceed-by-experience instructions as delivery pressure, not approval.

## Mandatory Confirmation Checkpoints（强制确认检查点）

四道闸门不是内部状态标记，而是**必须暂停并向用户显式确认的节点**。任何阶段都不得"静默通过"——即便产出的是草案，也必须在每个闸门前先提请用户确认，否则不得进入下一阶段或生成候选/清单。

- **闸门即 STOP**：在 `requirement_baseline`、`space_mode`、`product_plan`、`final_release` 四道闸门处，agent 必须停止自动推进，向用户呈现该闸门的**决策摘要**（具体待确认项 + 证据 + 建议口径），并以直接提问方式请求确认；未收到用户明确答复前，不得标记 `status=approved`，也不得生成下游候选行、工作簿或清单。
- **草案不等于批准**：以"先出草案""用经验做""给我清单先""只是草稿不用确认"等理由直接产出候选产品行、数量、单价或预算合计，均**不构成闸门批准**，仍须回到对应闸门提请确认。此类请求视为交付压力，不是批准。
- **每个闸门需用户确认的具体事项**：
  - 需求基线闸门：项目标识、预算桶与金额/口径、计价币种、范围边界、模式提示、必配功能、输出要求。
  - 空间/模式闸门：模式（spatial/non_spatial/hybrid）、目标空间清单与功能画像、面积/人数/工程量依据（含装修/家具等暂估授权）。
  - 产品方案闸门：逐行确认名称、品牌、型号、单位、价格、数量、参数、替代关系、暂估工程量与必配缺口。
  - 最终发布闸门：硬错误清零、金额对账、警告披露、业务签核。
- **记录确认**：每次用户确认须写入 `approval_log`（`gate`、`target_type`、`target_refs`、`confirmed_content`、`confirmed_by`、`confirmed_at`），未记录的确认无效。
- **Stage B 阻断提问**：需求基线批准前，只输出草案级 source/template/requirement 产物；凡影响配置或输出的未决事项，一次聚焦一个阻断问题向用户提出（附 `suggested_answer` 与 `suggested_basis`），不得先生成候选/清单再"补确认"。

## STOP and Draft Rules

Do not label or deliver a formal result when:

- a fixed resource is unreadable, cannot be SHA-256 fingerprinted, or mismatches an approved/bound fingerprint;
- a `blocking=true` requirement or its mandatory approval remains unresolved;
- any `selected_for_output=true` line, `internal_product_mapping` line, `confirmed_totals` line, or final-output line is not confirmed and complete;
- a selected/referenced line has unresolved identity, model, source, price, unit, quantity, parameter, or approval conflict;
- an open blocking quality issue affects a selected line, a final-output source record, or a blocking requirement;
- a selected quantity depends on unconfirmed area, users, activity intensity, or conversion rules without approved estimation;
- a required gate, formula/total reconciliation, template requirement, traceability check, or business sign-off fails under `references/validation-checklist.md`.

Do not globally block because an unselected candidate is `draft`, `pending_confirmation`, `rejected`, or `waived`, or because a quality issue affects only unselected/excluded candidates. Treat these, missing business metadata, and `blocking=false` unresolved items as warnings: preserve them, assess impact, and disclose them in validation and delivery notes.

If a blocking question is unanswered, keep unknowns null and deliver only a conspicuously labeled draft with open questions and assumptions. Never invent values or approval. If only warnings remain, evaluate the other gate conditions normally.

## Artifact and Rule Navigation

Generate `source_manifest`, `template_profile`, `requirement_baseline`, `space_plan`, `candidate_plan`, `approval_log`, `internal_product_mapping`, `catalog_quality_issues`, `unresolved_items`, final-list output, `traceability_audit`, `validation_result`, and `final_release`.

- Use `references/universal-rules.md` for immutable source, identity, fact, semantic, and release constraints.
- Use `references/project-schema.md` for intake mapping, state fields, enums, versions, selected-line semantics, budgets, approvals, artifacts, and fingerprints.
- Use `references/workflow-and-gates.md` for the authoritative A–H sequence, gate behavior, and exceptions.
- Use `references/validation-checklist.md` for scoped hard errors, warnings, and release acceptance.

Do not restate or improvise detailed schema, approval fields, budget formulas, or the complete hard-error list.

## Semantic Match Example

```yaml
target_space_profile:
  name: 学生成长探索区
  core_functions: [自我认知, 成长探索]
  users: [学生]
  activities: [反思, 探索任务]
  capacity: null
  area: null
  evidence: [REQ-SPACE-01]
catalog_evidence:
  source_spaces: [自我认知室]
  function_tags: [自我认知, 探索]
  product_intro: 支持个体反思与探索活动
assessment:
  semantic_match_reason: 名称不同，但核心功能、用户与活动语义重合，因此进入候选。
  confidence: medium
  status: pending_confirmation
  selected_for_output: false
```

Use shared functions to admit this record as an unselected candidate, not to approve it. Confirm constraints, unique model identity, installation conditions, quantity basis, capacity, and area before selecting it.

## Quick Reference

| Situation | Action |
|---|---|
| Business version/date absent | Warn; use SHA-256 and do not invent metadata |
| Intake/project ID | Stage A creates only source/template records with `intake_run_id`; Stage B creates the pending baseline, confirms ID, then creates a project-bound baseline and `approval_log` |
| Baseline pending | Profile the template, quote source facts with evidence, record only `mode_hint` and gaps, ask the next blocker if one exists, and create no `space_plan` or candidates |
| Workspace has other projects | Ignore them; confirm ambiguous directory scope and use only `current_run_source_scope` |
| Space names differ | Compare functions, users, activities, and catalog semantics |
| Mode is spatial/hybrid | Output must be grouped by space with space-name headers (or a space column) and per-space subtotals; cross-space/project-level rows go in a labeled shared group |
| Unselected candidate is pending | Preserve and disclose; do not globally block |
| Selected candidate is pending | Stop formal release |
| Template missing/unparseable | Missing: first update says the default will be used; after analysis say its profile is established and ask only if a blocker exists; unparseable: preserve the user template and disclose the fallback |

## Common Mistakes

- Do not confuse business metadata with the authoritative SHA-256 technical version.
- Do not treat a shared workspace, current directory, previous project, or old conversation as source authorization.
- Do not use the intake asset as project state or proof of approval.
- Do not apply selected-line hard errors to the entire candidate catalog.
- Do not let unselected candidates enter mapping, confirmed totals, or final output.
- Do not exact-match space names, guess product facts, or rewrite standard product names.
- In spatial/hybrid mode, do not deliver a list grouped only by functional category — it must be grouped and subtotaled by space with space names shown.
- Do not duplicate reference rules in this Skill or call a draft an approved release.
- Do not silently pass a gate without pausing to confirm with the user; draft generation is not approval, and a gate may only be marked `approved` after the user explicitly confirms its decision summary.
