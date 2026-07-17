---
name: building-configuration-lists
description: Use when a user wants to analyze project requirement files, plan functional spaces, select products from a standard catalog, prepare a budget or equipment list, fill a provided Excel template, or create a configuration list when requirements are incomplete or ambiguous.
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
- `assets/default-configuration-list.xlsx`
- `assets/project-intake-template.yaml`

Calculate SHA-256 from the original bytes of all seven fixed resources and use it as the authoritative technical version. Record any supplied `business_version` or `effective_date` unchanged; when either is absent, create a warning instead of inventing it or stopping. Block only when a fixed resource is unreadable, its SHA-256 cannot be generated, or its actual fingerprint differs from an approved or bound fingerprint.

Use the default workbook only when the user supplied no template. Treat the intake asset as input schema 1.1, not as a project-state object or approval.

## Execute A–H

### A. Receive and profile

Inventory every requirement file, attachment, fixed resource, historical basis, and user template. Build `source_manifest` and analyze the template now, not at output time; build `template_profile` for either the user template or, only when absent, the default template.

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

Preserve formulas, merged cells, print areas, summaries, and styling when reliable. Write a new output version and never overwrite inputs, fixed resources, or approved outputs.

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
- Do not duplicate reference rules in this Skill or call a draft an approved release.
