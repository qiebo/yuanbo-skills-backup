# 项目状态对象规范

所有项目特定值只允许进入本文件定义的项目状态对象，不得写入固定产品库或通用规则。对象必须带 `project_id`、`version`、`updated_at`，并保留历史版本；时间使用带时区的 ISO 8601 格式。允许 `project_id=null` 的例外仅有：尚未绑定已确认项目身份的阶段 A `source_manifest`/`template_profile`，以及项目标识尚未确认且 `status=pending | rejected` 的 `requirement_baseline`。这些对象仍必须存在 `project_id` 字段并共用同一 `intake_run_id`；其他项目状态对象的 `project_id` 必须非空。

## 通用枚举

- 审批状态 `approval_status`：仅允许 `pending | approved | rejected | not_applicable`。
- 需求状态 `requirement_status`：仅允许 `confirmed | ambiguous | conflicting | missing | assumption`。
- 置信度 `confidence`：仅允许 `high | medium | low`。
- 配置模式 `mode`：仅允许 `spatial | non_spatial | hybrid`。
- 候选行状态 `candidate_status`：仅允许 `draft | pending_confirmation | confirmed | rejected | waived`。这是候选生命周期状态，不是审批状态。
- 配置等级 `configuration_level`：仅允许 `required | recommended | optional`，分别表示必配、推荐、选配。

## 输入采集契约

`project-intake-template.yaml` 仅是输入采集模板，固定 `schema_version=1.1`，不是项目状态、审批记录或发布证明。映射采用分阶段映射/重放：阶段 A 只登记来源与模板画像，阶段 B 才将所有 intake 项写入 `requirement_baseline`；下游对象只能在基线批准后按确认需求重放。不能把 intake 的空值、自由文本或提交动作解释为已确认/已批准。

| Intake 路径 | 阶段 B 的基线目标 | 后续重放规则 |
|---|---|---|
| `project.id` | 项目标识需求项；确认后写入 `requirement_baseline.project_id` | 原样保存为未确认 source fact，不得因 intake 提交自动确认/批准；后续对象仅从批准基线复制 |
| `project.name`、`project.client` | `requirement_baseline.project_identity.name/client` | 保留证据，批准后作为项目身份引用 |
| `project.objective` | “项目目标”需求项 | 后续对象按 confirmed `requirement_refs` 使用 |
| `budget_limits` | `requirement_baseline.budget_limits` | 在基线批准前完成稳定标识、确认和预算专用审批 |
| `pricing.basis`、`pricing.currency` | 计价基础与币种需求项 | 阶段 E 按 confirmed 引用生成金额口径 |
| `scope.reuse_policy`、`scope.inclusions`、`scope.exclusions` | 复用、纳入、排除范围需求项 | 后续按 confirmed 引用执行项目边界 |
| `priorities` | 项目侧重点需求项 | 阶段 E 按 confirmed 引用生成选品评分/取舍依据 |
| `mode_hint` | `requirement_baseline.mode_hint` | C/D 在基线批准后用于路由，不等于自动批准模式 |
| `space_inputs` | `requirement_baseline.space_inputs` 及空间需求项 | C/D 从批准基线创建 `space_plan` |
| `required_functions`、`optional_functions` | 必配/选配功能需求项 | E 按 confirmed 引用派生 `required`/`optional` 配置等级 |
| `project_rules` | `project_only=true` 的项目规则需求项 | 后续按 confirmed 引用使用，不回写固定规则 |
| `output.user_template`、`output.use_default_template` | 输出模板需求项 | A 仅生成画像，确认后的模板需求在 G 执行 |
| `intake_evidence` | 需求证据与 `source_manifest` 引用 | 每次下游复制保留 `evidence_refs` 和来源版本 |

所有 intake 输入都必须先进入 `requirement_baseline` 并经过证据关联、状态判定和必要确认。即使 intake 提供 `project.id`，对应需求项也只保留原值与证据作为未确认 source fact，不得据此填入顶层 `project_id`。此时可建立 `project_id=null`、`status=pending | rejected` 的基线版本，但必须带与 Stage A 产物相同的 `intake_run_id`。项目标识授权确认后，必须新建 `project_id` 非空的绑定基线版本，保留同一 `intake_run_id` 和旧基线版本引用，不得原地覆盖；只有该绑定版本可为 `approved`。阶段 A/B 不创建 `space_plan`、`candidate_plan` 或 `final_release`；`approval_log`、基线 `version`/`updated_at`、`unresolved_items`、稳定内部标识及初始审批状态由 Agent 新建。

## 1. `requirement_baseline`

需求基线保存原始要求、证据、澄清结果和阻断关系。

| 字段 | 类型/允许值 | 必填 | 说明 |
|---|---|---:|---|
| `project_id` | 字符串或空值 | 是 | 项目标识；仅项目标识尚未确认且 `status=pending | rejected` 的基线版本可为空 |
| `intake_run_id` | SHA-256 字符串 | 是 | 必须与产生本基线的 Stage A `source_manifest`/`template_profile` 相同 |
| `origin_version_ref` | 基线版本引用或空值 | 是 | 初始空 ID 版本为空；项目绑定版本必须指向前一个未覆盖基线版本 |
| `version` | 字符串 | 是 | 基线版本 |
| `updated_at` | ISO 8601 时间 | 是 | 最近更新时间 |
| `status` | `approval_status` | 是 | 需求基线闸门审批状态 |
| `mode_hint` | `mode` 或空值 | 是 | 当前模式判断；未完成路由时为空 |
| `requirements` | 需求项数组 | 是 | 结构化需求 |
| `open_blockers` | `requirement_id` 数组 | 是 | 尚未解决的阻断项 |
| `project_identity` | 对象 | 是 | 含项目 `name`、`client` 及其证据引用；未确认值显式标记 |
| `space_inputs` | 结构化输入数组 | 是 | Intake 空间输入、证据与状态；C/D 仅从批准版本读取 |
| `budget_limits` | 预算限制数组 | 是 | 基线内确认和审批的唯一预算源；结构见下文 |

`requirement_baseline.project_id=null` 时，`status` 只能为 `pending | rejected`，项目标识需求不得为 `confirmed`，且 `intake_run_id` 必须与对应 Stage A 产物一致。项目标识确认后必须新建非空 `project_id` 版本，复制同一 `intake_run_id`、用 `origin_version_ref` 指向直接上一基线版本并保留其全部证据/版本链。旧版本不得改写；只有该 `project_id` 非空、项目标识需求已 `confirmed` 的绑定版本才允许 `status=approved`。

每个 `requirement_baseline.budget_limits` 条目必须包含稳定唯一的 `budget_limit_id`、必填 `requirement_id`、`budget_bucket`、`target_amount`、`tolerance_type`（仅 `absolute | percent`）、`tolerance_value`、`approval_ref`、`evidence_refs` 和需求状态。`requirement_id` 必须指向同一 `requirement_baseline.requirements` 中 `status=confirmed` 的预算需求项；预算限制的 `evidence_refs` 必须与该需求项 `evidence` 对应，预算桶、目标、容差及批准内容必须与该需求项 `answer` 一致，不得补造或改写。预算审批仍使用 `gate=requirement_baseline`、`target_type=budget_limit`，并在需求基线批准前完成；审批快照必须匹配预算桶、目标和容差。任一预算限制未确认、绑定需求不合规或审批引用无效时，`requirement_baseline.status` 不得为 `approved`。

同一基线内，`budget_limits[].requirement_id` 全数组唯一，`budget_limit_id` 全数组唯一，`budget_bucket` 全数组唯一。每个 budget limit 恰好引用一个 `category=budget AND status=confirmed` 的专用预算需求；反向集合仅由 `category=budget AND status=confirmed` 的需求构成，每个此类需求必须恰好被一个 budget limit 引用，不能为 0 个或多个。两集合按 `requirement_id` 构成双射。任何 `category!=budget` 的需求均不进入该双射；即使其 `affects` 含预算桶，也无需并不得据此强制建立独立 `budget_limit`。任一唯一性或双射条件不满足时，基线不得批准。

每个需求项包含：

| 字段 | 类型/允许值 | 必填 | 说明 |
|---|---|---:|---|
| `requirement_id` | 唯一字符串 | 是 | 稳定需求引用 |
| `topic` | 字符串 | 是 | 需求主题 |
| `category` | `identity / objective / budget / pricing / scope / priority / mode / space / function / project_rule / output / other` | 是 | 需求分类；预算需求使用 `budget` |
| `statement` | 字符串 | 是 | 不改变原意的结构化表述 |
| `status` | `requirement_status` | 是 | 需求状态 |
| `evidence` | 证据数组 | 是 | 每项含 `source_name`、`source_version`、`location`、`excerpt` |
| `blocking` | 布尔值 | 是 | 未解决时是否阻断后续闸门 |
| `project_only` | 布尔值 | 是 | 项目特定需求/规则为 `true`，不得写回固定规则或跨项目复用 |
| `affects` | 字符串数组 | 是 | 受影响的模式、空间、数量、预算桶、候选项或输出字段引用 |
| `question` | 字符串或空值 | 是 | 需要向用户逐项确认的问题 |
| `suggested_answer` | 字符串或空值 | 是 | 从现有资料推导的建议答案；无可靠建议时为空 |
| `suggested_basis` | 证据引用数组 | 是 | 建议答案的来源、推导条件和限制 |
| `answer` | 字符串或空值 | 是 | 用户或授权方答复；未答复为空 |
| `confirmed_by` | 字符串或空值 | 是 | 确认人；未确认为空 |
| `confirmed_at` | ISO 8601 时间或空值 | 是 | 确认时间；未确认为空 |

`confirmed_by` 与 `confirmed_at` 必须同时有值或同时为空。`status=confirmed` 时二者及 `answer` 必须有值；`status=assumption` 时必须在 `evidence` 中记录假设依据且不得伪装为确认。`suggested_answer` 不是用户确认，不能自动复制为 `answer`。

## 2. `space_plan`

空间计划保存模式路由、空间清单、功能画像及空间/工程量确认。

| 字段 | 类型/允许值 | 必填 | 说明 |
|---|---|---:|---|
| `project_id` | 字符串 | 是 | 项目标识 |
| `version` | 字符串 | 是 | 空间计划版本 |
| `updated_at` | ISO 8601 时间 | 是 | 最近更新时间 |
| `status` | `approval_status` | 是 | 空间/模式闸门审批状态 |
| `mode` | `mode` | 是 | 已路由模式 |
| `mode_reason` | 字符串 | 是 | 按模式定义给出的判断依据 |
| `requirement_baseline_version_ref` | 已批准绑定基线版本引用 | 是 | 创建此计划所用的 `requirement_baseline.version`；基线 `project_id` 必须与本对象一致且非空 |
| `source_manifest_version_ref` | 项目绑定 `source_manifest.version` | 是 | 必须指向与基线相同非空 `project_id` 的绑定版本 |
| `template_profile_version_ref` | 项目绑定 `template_profile.version` | 是 | 必须指向与基线相同非空 `project_id` 的绑定版本 |
| `requirement_refs` | confirmed `requirement_id` 数组 | 是 | 模式、空间、功能和工程量依据 |
| `evidence_refs` | 稳定证据引用数组 | 是 | 从基线需求复制的 intake/source 证据链 |
| `spaces` | 空间画像数组 | 是 | 无有意义空间维度时可为空数组 |
| `engineering_basis` | 依据数组 | 是 | 面积计价或工程量相关的确认、暂估与证据；不适用时为空数组 |
| `planning_suggestion` | 字符串或空值 | 是 | 从资料推导的空间规划建议 |
| `suggestion_basis` | 对象 | 是 | 至少分别记录功能、总面积、人数、项目重点四方面的证据或缺失状态 |

`space_plan` 的三个版本引用必须指向同一 `project_id` 的 approved 绑定基线和两个项目绑定 Stage A 新版本，并保持同一 `intake_run_id` 及未变的 `content_fingerprint_refs`。`mode=non_spatial` 时 `spaces` 可为空数组，但仍必须生成并批准该空间/模式计划，不得跳过版本链。

每个空间画像包含：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `space_id` | 唯一字符串 | 是 | 稳定空间引用 |
| `name` | 字符串 | 是 | 项目内目标空间名称 |
| `aliases` | 字符串数组 | 是 | 别名或原文称呼 |
| `core_functions` | 字符串数组 | 是 | 必须支持的核心功能 |
| `secondary_functions` | 字符串数组 | 是 | 可选或次要功能 |
| `users` | 字符串数组 | 是 | 服务对象或使用角色 |
| `activities` | 字符串数组 | 是 | 典型活动 |
| `capacity` | 数值、范围或空值 | 是 | 已确认容量或显式未知 |
| `area` | 数值、范围或空值 | 是 | 已确认面积或显式未知，单位随证据记录 |
| `evidence` | 证据数组 | 是 | 每项含 `source_name`、`source_version`、`location`、`excerpt` |

## 3. `candidate_plan`

候选方案保存产品、工程、服务等候选行及其需求、空间、数量和预算依据。

| 字段 | 类型/允许值 | 必填 | 说明 |
|---|---|---:|---|
| `project_id` | 字符串 | 是 | 项目标识 |
| `version` | 字符串 | 是 | 候选方案版本 |
| `updated_at` | ISO 8601 时间 | 是 | 最近更新时间 |
| `status` | `approval_status` | 是 | 产品方案闸门审批状态 |
| `lines` | 候选行数组 | 是 | 全部候选项 |
| `amount_summary` | 对象 | 是 | 必须分别包含 `proposed_totals` 和 `confirmed_totals`；两者均按 `budget_bucket` 汇总并含总计 |
| `approved_budget_total` | 只读派生数值 | 是 | 唯一从 `budget_limits[].target_amount` 求和生成；不得独立填写或编辑 |
| `budget_gap` | 对象或空值 | 是 | 分别包含按预算桶及总计计算的 `proposed_gap` 与 `confirmed_gap`；均为对应汇总金额减 `budget_limits` 目标，正值表示超额，输入不足时为空 |
| `budget_gap_reason` | 字符串或空值 | 是 | 差额/缺口形成原因 |
| `adjustment_options` | 调整方案数组 | 是 | 预算无法满足时至少一个不虚构价格的调整方案；否则可为空 |
| `budget_limits` | 预算限制快照数组 | 是 | 从已批准基线原样复制，不可编辑 |
| `pricing_basis` | 字符串 | 是 | 从 confirmed 计价需求引用派生 |
| `currency` | 字符串 | 是 | 从 confirmed 币种需求引用派生的统一金额口径 |
| `selection_scoring_basis` | 结构化数组 | 是 | 从 confirmed priorities 需求引用派生 |
| `requirement_baseline_version_ref` | 已批准绑定基线版本引用 | 是 | 创建候选方案所用的 `requirement_baseline.version`；基线 `project_id` 必须与本对象一致且非空 |
| `source_manifest_version_ref` | 项目绑定 `source_manifest.version` | 是 | 必须与基线及本对象的非空 `project_id` 一致 |
| `template_profile_version_ref` | 项目绑定 `template_profile.version` | 是 | 必须与基线及本对象的非空 `project_id` 一致 |
| `space_plan_version_ref` | 已批准 `space_plan.version` | 是 | 必须指向同一项目的 approved 空间/模式计划；`non_spatial` 也必填 |
| `requirement_refs` | confirmed `requirement_id` 数组 | 是 | 覆盖计价、币种、优先级、范围、项目规则、输出要求及其他计划级约束 |
| `plan_field_requirement_refs` | 对象 | 是 | 将每个计划级派生字段名映射到 `requirement_refs` 中一个或多个具体引用 |
| `evidence_refs` | 稳定证据引用数组 | 是 | 从 confirmed 需求及预算快照复制的证据链 |

`plan_field_requirement_refs` 必须至少覆盖 `pricing_basis`、`currency`、`selection_scoring_basis`、`budget_limits`、范围约束、项目规则、输出要求和所有其他计划级派生字段；每个值必须是非空 `requirement_id` 数组、属于顶层 `requirement_refs`，且在绑定的 `requirement_baseline.version` 中均为 `confirmed`。`evidence_refs` 只提供证据定位，不能替代计划级 `requirement_refs` 或逐字段映射。候选行自身的 `requirement_refs` 继续保留，并独立追溯该行满足的具体需求。

`candidate_plan` 的四个版本引用必须可确定性验证为同一 `project_id`、同一 `intake_run_id` 的单一链路：approved 绑定 `requirement_baseline` →项目绑定 `source_manifest`/`template_profile` → approved `space_plan` → `candidate_plan`。任一引用不得指向 `project_id=null`、其他项目或指纹链已改变的版本；`mode=non_spatial` 也必须引用 approved `space_plan_version_ref`。

`candidate_plan.requirement_refs` 必须包含每个预算快照条目的 `requirement_id`，且 `plan_field_requirement_refs.budget_limits` 必须逐项覆盖这些引用；不得仅引用预算审批或 `budget_limit_id` 而遗漏预算需求项。

`candidate_plan.budget_limits` 必须由已批准 `requirement_baseline.budget_limits` 逐项复制为不可编辑快照，保持相同 `requirement_id`、`budget_limit_id`、`approval_ref`、预算桶、目标、容差和 `evidence_refs`，并增加 `validation_status`（仅 `draft | unresolved | passed | failed`）。不允许另填、删除、编造或变更；预算变更必须回到新的 `requirement_baseline` 版本重新确认、审批，再重建下游快照。同一 `budget_bucket` 只能出现一次；`approved_budget_total` 是快照中全部桶 `target_amount` 的只读求和。

候选预算快照必须保持基线在 `category=budget AND status=confirmed` 专用预算需求集合上的 `requirement_id ↔ budget_limit_id` 双射，以及 `requirement_id`、`budget_limit_id`、`budget_bucket` 三类唯一性；不得多复制、漏复制或改变配对。其他 `category` 的需求即使 `affects` 含预算桶，也不得纳入该双射或据此新增独立 `budget_limit`。

正式发布时，每个 `approval_ref` 必须沿用基线审批，并指向 `approval_log` 中同时满足以下条件的记录：`status=approved`、`gate=requirement_baseline`、`target_type=budget_limit`、`target_refs` 精确包含对应 `budget_limit_id`，且 `confirmed_content` 快照逐项匹配该限制的 `budget_bucket`、`target_amount`、`tolerance_type`、`tolerance_value`。任何字段不匹配、无关记录、缺失或未批准均为硬错误；预算内容不得在候选阶段重新审批或改写。

容差数学按预算桶独立执行：

- `tolerance_type=percent` 时，`tolerance_value` 是 0–100 的百分数，例如 5 表示 5%；允许绝对偏差为 `target_amount * tolerance_value / 100`。
- `tolerance_type=absolute` 时，`tolerance_value` 是与 `target_amount` 相同货币单位的非负数，允许绝对偏差即该值。
- 默认允许范围对称为 `target_amount ± 允许绝对偏差`。除非另有已批准的上下界规则，否则不得使用不对称范围；首版不增加不对称字段。
- 正式校验必须逐 `budget_bucket` 比较 `confirmed_totals` 与该桶允许范围；任一桶失败则其 `validation_status=failed`，不得用其他桶余额抵消。

每个候选行必须包含以下字段：

| 字段 | 类型/允许值 | 说明 |
|---|---|---|
| `line_id` | 唯一字符串 | 稳定候选行引用 |
| `line_type` | `product | engineering | service | material | allowance` | 行类型 |
| `function_module` | 字符串 | 所属功能模块；用于汇总功能覆盖 |
| `configuration_level` | `configuration_level` | 必配、推荐或选配等级 |
| `requirement_refs` | `requirement_id` 数组 | 该行满足的需求 |
| `space_refs` | `space_id` 数组 | 目标空间；项目级项可为空 |
| `product_identity_key` | 字符串或空值 | 产品行为“名称+品牌+型号”的稳定键；非产品行为空 |
| `source_spaces` | 字符串数组 | 来源中的所属/适用空间语义证据 |
| `function_tags` | 字符串数组 | 来源产品的功能标签；非产品行可为空 |
| `product_intro` | 字符串或空值 | 来源产品介绍；非产品行可为空 |
| `semantic_match_reason` | 字符串或空值 | 空间语义匹配理由；无空间依赖时为空 |
| `confidence` | `confidence` | 候选结论置信度 |
| `selection_reason` | 字符串 | 选择该项的来源证据、适配理由和取舍 |
| `necessity` | 字符串 | 说明该项为何为必配、推荐或选配，以及不配置的影响 |
| `function_coverage` | 字符串数组 | 实际覆盖的核心或次要功能引用 |
| `quantity_basis` | 字符串 | 数量、面积或工程量的计算/确认依据 |
| `budget_bucket` | 字符串 | 项目预算归类 |
| `budget_delta` | 数值或空值 | 该行相对已批准基准/替代项的金额差额；无可比基准时为空并说明 |
| `status` | `candidate_status` | 候选生命周期状态 |
| `selected_for_output` | 布尔值 | 是否选择进入正式输出；必填，且只有 `status=confirmed` 时可为 `true` |
| `alternatives` | `line_id` 或外部候选引用数组 | 可替代项；无替代项时为空数组 |
| `unresolved_item_refs` | `unresolved_items.item_id` 数组 | 该行关联的未决事项；无则为空数组 |
| `quality_issue_refs` | `catalog_quality_issues.quality_issue_id` 数组 | 该行关联的数据质量问题；无则为空数组 |
| `source_refs` | 来源引用数组 | 产品行指向固定产品库；非产品行指向规则或批准依据 |
| `name` | 字符串 | 产品行必须精确等于固定产品库标准 `product_name`；非产品行使用规则或批准依据中的标准品目名 |
| `usage_description` | 字符串或空值 | 项目化用途、场景或说明；不得用于替代、拼接或改写产品 `name` |
| `brand` | 字符串或空值 | 产品品牌；非产品行为空 |
| `model` | 字符串或空值 | 产品型号；非产品行为空 |
| `unit` | 字符串或空值 | 来源或已批准计价单位 |
| `unit_price` | 数值或空值 | 来源或已批准单价 |
| `quantity` | 数值或空值 | 按 `quantity_basis` 得出的数量 |
| `parameters` | 字符串、结构化映射或空值 | 仅来自已确认来源的参数摘录 |

候选状态、字段完整性与金额口径必须同时满足：

- `draft | pending_confirmation`：在来源冲突或尚未确认时，`unit`、`unit_price`、`quantity`、`parameters` 可为 `null`，但至少关联一个 `unresolved_item_refs` 或 `quality_issue_refs`，且 `selected_for_output=false`。只有非空且可计算的值可进入 `proposed_totals`，不可计算行须单独列出而不得按 0 金额混入。
- `confirmed`：产品行的名称、品牌、型号、单位、单价、数量、参数、产品身份和来源必须完整且相互匹配，以上字段不得为 `null`；非产品行必须按已批准规则满足其必需字段和来源要求。只有同时满足 `status=confirmed AND selected_for_output=true` 的行进入正式输出和 `confirmed_totals`。
- `rejected`：必须 `selected_for_output=false`，不进入正式输出、`proposed_totals` 或 `confirmed_totals`，但保留拒绝审批依据。
- `waived`：必须 `selected_for_output=false`，仅表示经审批免配，不代表已选产品；不进入正式输出、`proposed_totals` 或 `confirmed_totals`，且保留豁免审批依据。
- `proposed_totals` 汇总 `draft | pending_confirmation | confirmed` 中字段完整且可计算的方案行，用于评审；`confirmed_totals` 只汇总 `status=confirmed AND selected_for_output=true` 的行。正式输出金额只能与 `confirmed_totals` 对账。
- 未选中的 `draft | pending_confirmation | rejected | waived` 候选可作为方案或历史记录保留，其自身不阻断正式发布，但必须按 warning/审批历史规则披露。

## 4. `approval_log`

审批日志是只追加记录，不覆盖历史结论。

| 字段 | 类型/允许值 | 必填 | 说明 |
|---|---|---:|---|
| `project_id` | 字符串 | 是 | 项目标识 |
| `version` | 字符串 | 是 | 日志版本 |
| `updated_at` | ISO 8601 时间 | 是 | 最近更新时间 |
| `entries` | 审批记录数组 | 是 | 按时间追加 |

每条 `entries` 记录使用以下结构：

| 字段 | 类型/允许值 | 必填 | 允许空值 | 说明 |
|---|---|---:|---:|---|
| `approval_id` | 唯一字符串 | 是 | 否 | 稳定审批引用 |
| `gate` | `requirement_baseline | space_mode | product_plan | final_release` | 是 | 否 | 所属闸门 |
| `target_type` | `baseline | space_plan | candidate_plan | candidate_line | budget_limit | quality_issue | release` | 是 | 否 | 被审批对象类型 |
| `target_version` | 字符串 | 是 | 否 | 被审批对象版本 |
| `target_refs` | 稳定对象引用数组 | 是 | 可为空数组 | 被确认对象；候选行审批不得只依赖此字段 |
| `candidate_line_refs` | `line_id` 数组 | 是 | 可为空数组 | `target_type=candidate_line` 时至少一个；质量问题尚无候选行时可为空 |
| `confirmed_content` | 结构化对象数组 | 是 | 否 | 每项含 `subject_ref`、`decision`、`confirmed_value`、`reason`；`pending` 时 `decision`、`confirmed_value` 可为 `null`，其他状态的 `decision` 仅 `approve | reject | waive | not_applicable` 且不得为空 |
| `impact_scope` | 结构化对象 | 是 | 否 | 含 `requirement_refs`、`space_refs`、`function_modules`、`candidate_line_refs`、`budget_buckets`、`output_fields` 数组 |
| `project_only` | 布尔值且只能为 `true` | 是 | 否 | 仅适用于当前项目，不得回写固定规则/产品库或跨项目复用 |
| `status` | `approval_status` | 是 | 否 | 仅 `pending | approved | rejected | not_applicable` |
| `decided_by` | 字符串或空值 | 是 | 仅 `pending` 可空 | 决定人；`approved`、`rejected`、`not_applicable` 均必填 |
| `decided_at` | ISO 8601 时间或空值 | 是 | 仅 `pending` 可空 | 决定时间；`approved`、`rejected`、`not_applicable` 均必填 |
| `comment` | 字符串或空值 | 是 | 可空 | 补充说明；`not_applicable` 时必须填写不适用原因 |
| `evidence_refs` | 稳定证据引用数组 | 是 | `pending` 可为空数组 | 指向需求证据、来源记录、会议纪要或批准文件，不得存放不可定位描述 |

候选行级审批必须使用 `target_type=candidate_line` 并填写 `candidate_line_refs`。质量问题审批必须使用 `gate=product_plan`、`target_type=quality_issue`，且 `target_refs` 必须包含对应 `quality_issue_id`；质量问题尚未产生候选行时 `candidate_line_refs` 可为空。预算限制审批必须使用 `gate=requirement_baseline`、`target_type=budget_limit`，`target_refs` 精确包含对应 `budget_limit_id`，并在 `confirmed_content` 中保存逐项匹配 `budget_bucket`、`target_amount`、`tolerance_type`、`tolerance_value` 的结构化快照。非 `pending` 状态必须有决定人、决定时间和至少一个 `evidence_refs`。

## 5. `final_release`

最终发布对象绑定获批状态、输入版本、输出文件和校验结果。

| 字段 | 类型/允许值 | 必填 | 说明 |
|---|---|---:|---|
| `project_id` | 字符串 | 是 | 项目标识 |
| `version` | 字符串 | 是 | 发布版本，不得覆盖旧版本 |
| `updated_at` | ISO 8601 时间 | 是 | 最近更新时间 |
| `status` | `approval_status` | 是 | 最终发布闸门状态；正式版必须为 `approved` |
| `release_kind` | `draft | formal` | 是 | 草案或正式版 |
| `input_versions` | 对象 | 是 | 必含 `requirement_baseline_version_ref`、`source_manifest_version_ref`、`template_profile_version_ref`、`space_plan_version_ref`、`candidate_plan_version_ref`，并绑定标准产品库、四份 references、`assets/project-intake-template.yaml`、默认/用户模板；固定资源和模板均记录路径与 SHA-256 `content_fingerprint`，intake asset 另含 `schema_version=1.1` |
| `output_files` | 文件清单 | 是 | 文件名、格式、校验摘要和生成时间 |
| `validation_result` | 对象 | 是 | `hard_error_count`、`warning_count`、金额核对和公式检查结果 |
| `approved_by` | 字符串或空值 | 是 | 正式发布批准人 |
| `approved_at` | ISO 8601 时间或空值 | 是 | 正式发布批准时间 |

`release_kind=formal` 时，`status` 必须为 `approved`，`approved_by` 与 `approved_at` 必须有值，且 `hard_error_count` 必须为 0。草案可为 `pending` 或 `rejected`，不得标记为 `approved` 的正式发布。

`final_release.input_versions` 中前四个字段与 `candidate_plan` 同名字段的语义和值必须完全一致，`candidate_plan_version_ref` 指向实际生成本发布的 approved `candidate_plan.version`。全部五个项目状态引用必须具有与 `final_release.project_id` 一致的非空 `project_id`，并使 Stage A initial → project-bound → downstream 的 `origin_version_ref`、`intake_run_id` 和 `content_fingerprint_refs` 链可重算验证。

## 6. 主要中间产物

以下产物属于项目状态的一部分，均需带 `project_id`、`version`、`updated_at`，并由相关主对象通过版本引用绑定。在项目标识尚未确认时，仅阶段 A 初始 `source_manifest`/`template_profile` 和 `status=pending | rejected` 的 `requirement_baseline` 允许 `project_id=null`，且三者必须共用同一 `intake_run_id`。表中其他产物、`space_plan`、`candidate_plan` 及一切基线批准后的下游状态对象的 `project_id` 必须非空：

| 产物 | 必需字段与用途 |
|---|---|
| `source_manifest` | 对象级必需 `project_id`、`version`、`intake_run_id`、`origin_version_ref`、`content_fingerprint_refs`、`updated_at`、`intake_run_id_algorithm`、`intake_template_fingerprint`、排序后的 `input_content_fingerprints`；条目需 `source_id`、名称、类型、SHA-256 `content_fingerprint`、可选 `business_version`/`effective_date`、路径/定位、解析状态、质量问题。Stage A 初始版 `project_id=null`、`origin_version_ref=null`；首个 project-bound 版本的 `project_id` 非空且 `origin_version_ref` 必须指向 Stage A 初始版；每个后续 bound 版本必须指向直接上一 bound 版本。`assets/project-intake-template.yaml` 必须记录固定路径、指纹和 `schema_version=1.1`；业务版本或生效日期缺失记 warning，不得编造或自动阻断 |
| `template_profile` | 对象级必需 `project_id`、`version`、`intake_run_id`、`origin_version_ref`、`content_fingerprint_refs`、`updated_at`、`intake_run_id_algorithm`、`intake_template_fingerprint`、排序后的 `input_content_fingerprints`、`template_origin`（仅 `default | user`）、`template_id`、`template_version`、SHA-256 `content_fingerprint`、工作表/章节、字段映射、必填项、公式、合并单元格 `merged_cells`、打印区域 `print_areas`、样式指纹/规则 `style_fidelity`、解析状态与限制。Stage A 初始版 `project_id=null`、`origin_version_ref=null`；首个 project-bound 版本的 `project_id` 非空且 `origin_version_ref` 必须指向 Stage A 初始版；每个后续 bound 版本必须指向直接上一 bound 版本；默认模板与用户模板都必须绑定身份和指纹 |
| `internal_product_mapping` | 仅映射 `status=confirmed AND selected_for_output=true` 的行；记录 `line_id`、`product_identity_key`、`product_name`、来源指纹/记录、`function_module`、`requirement_refs`、`space_refs`、输出行定位 |
| `unresolved_items` | 未确认事项的 `item_id`、类型、`requirement_refs`、`candidate_line_refs`、问题、`suggested_answer`、`suggested_basis`、`blocking`、`affects`、责任方和状态 |
| `traceability_audit` | 对每个输出行记录需求、空间、产品/规则来源、审批、内部映射、输出定位和金额核对结果，并汇总覆盖率与缺口 |
| `catalog_quality_issues` | 产品库缺失或冲突问题的结构化清单；字段和状态规则见下表 |

每个 `catalog_quality_issues` 条目必须包含：

| 字段 | 类型/允许值 | 必填 | 说明 |
|---|---|---:|---|
| `quality_issue_id` | 唯一字符串 | 是 | 稳定质量问题引用 |
| `product_identity_key` | 字符串或空值 | 是 | 可识别产品时填写；与 `source_record_ref` 至少一个非空 |
| `source_record_ref` | 稳定来源记录引用或空值 | 是 | 可定位来源记录时填写；与 `product_identity_key` 至少一个非空 |
| `missing_or_conflicting_fields` | 字段名数组 | 是 | 缺失或冲突字段，不得为空 |
| `severity` | `blocking | warning` | 是 | 关键语义、身份、单位、价格或参数问题必须为 `blocking` |
| `status` | `open | resolved | waived` | 是 | 问题状态 |
| `candidate_line_refs` | `line_id` 数组 | 是 | 受影响候选行 |
| `requirement_refs` | `requirement_id` 数组 | 是 | 受影响需求；无则为空数组 |
| `resolution` | 结构化对象或空值 | 是 | `resolved | waived` 时记录处理内容、证据引用和处理时间；`open` 时为空 |
| `approval_ref` | `approval_id` 或空值 | 是 | `resolved | waived` 必须指向该质量问题的专用已批准审批记录；`open` 时为空 |

关键语义字段缺失必须创建 `severity=blocking`、`status=open` 的问题并阻断相关行。正式发布只在 open 问题影响 `selected_for_output=true` 行、被 `internal_product_mapping`/最终输出使用的 `source_record_ref`，或 `blocking=true` 的需求时阻断。仅影响未选/已排除候选的问题保留为 warning/质量记录，不全局阻断；`severity=blocking` 也必须结合上述实际影响范围判定，不能目录级全局阻断。`resolved` 必须有来源修复证据，`waived` 必须有豁免证据；两者的 `approval_ref` 都必须指向 `gate=product_plan`、`target_type=quality_issue` 且 `target_refs` 含本条 `quality_issue_id` 的已批准记录。不得借豁免补造缺失的产品事实。

`content_fingerprint` 必须基于原始文件字节使用 SHA-256 生成，不能只使用文件名、修改时间或业务版本。固定资源实际指纹变化时，旧版中间产物必须保留并生成新版本，不能原地覆盖。`assets/project-intake-template.yaml` 指纹变化时必须按 schema 1.1 重新解析，并从阶段 A/B 开始重建新 `requirement_baseline` 版本；基线批准后再按阶段 C–H 重放下游映射。每次复制必须保留 intake/source `evidence_refs`、来源指纹和基线 `version` 引用，不得静默沿用旧映射或旧状态。

`content_fingerprint_refs` 是按 `resource_ref` 字典序排序的非空数组，每项必含 `resource_ref`（`source_id`、`template_id` 或其他稳定资源标识）、`fingerprint_algorithm=SHA-256`、`content_fingerprint` 和 `origin_content_version_ref`（首次登记该指纹的对象版本）。`resource_ref` 在同一数组内唯一。项目绑定版必须从 Stage A 初始版逐项原样复制该数组；只要未接收新内容，项数、顺序和四个字段值都不得变化。

`intake_run_id` 的标准生成式为 `SHA-256(UTF-8("intake-run-v1\n" + intake_template_fingerprint + "\n" + join("\n", sort(input_content_fingerprints))))`。`source_manifest` 与 `template_profile` 必须记录相同的 `intake_run_id_algorithm=sha256-intake-run-v1`、`intake_template_fingerprint` 和排序后的 `input_content_fingerprints`，以便重算验证；不得混入时间戳、随机数、文件名、临时/推测 `project_id` 或其他业务推测。

当且仅当已经存在 `status=approved`、项目标识需求已确认、`project_id` 非空的绑定 `requirement_baseline` 版本时，必须分别生成绑定该 `project_id` 的新 `source_manifest` 和 `template_profile` 版本。首个 project-bound 版的 `origin_version_ref` 指向 Stage A initial；后续 bound 版指向直接上一 bound 版。各版保持同一 `intake_run_id` 和未变内容的 `content_fingerprint_refs`，原始 `project_id=null` 版本不可修改或覆盖。`space_plan`、`candidate_plan`、阶段 C–H 其他对象与 `final_release.input_versions` 只能引用该 approved 绑定基线及这两个已绑定项目 ID 的新版本。它们与 project-bound 版本之间必须共用同一非空 `project_id`；Stage A initial 保持 `project_id=null`，只通过 `origin_version_ref`、`intake_run_id` 和内容指纹链连接，不参与非空 ID 相等性检查。
