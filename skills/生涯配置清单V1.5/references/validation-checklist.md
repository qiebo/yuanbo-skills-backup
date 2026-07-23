# 验证清单

验证分为硬错误、警告和发布闸门。硬错误必须修复或取得规则明确允许的书面豁免；警告必须披露并评估，但不自动阻断草案。自动验证结果不替代业务签核。

## Hard errors（硬错误）

出现任一项即不得正式发布：

- [ ] 阶段 A 创建了 `requirement_baseline`、`space_plan`、`candidate_plan` 或 `final_release`，或阶段 B 在需求基线批准前创建了后三者。
- [ ] 阶段 A `source_manifest` 或 `template_profile` 缺少 `intake_run_id`、`intake_run_id_algorithm=sha256-intake-run-v1`、`intake_template_fingerprint` 或排序后的 `input_content_fingerprints`；两者记录不一致，或按规定公式重算所得 SHA-256 与 `intake_run_id` 不一致；标识混入了时间、随机值、文件名、临时项目 ID 或业务推测。
- [ ] `source_manifest` 或 `template_profile` 缺少对象级 `project_id`、`version`、`intake_run_id`、`origin_version_ref` 或 `content_fingerprint_refs`；Stage A initial 的 `origin_version_ref` 不为 `null`；首个 project-bound 版本未指向 Stage A initial；任一后续 bound 版本未指向直接上一 bound 版；或链上 `intake_run_id` 不一致。
- [ ] `content_fingerprint_refs` 为空、未按 `resource_ref` 字典序排序、`resource_ref` 重复，或任一项缺少 `resource_ref`、`fingerprint_algorithm=SHA-256`、`content_fingerprint`、`origin_content_version_ref`；未接收新内容时，项目绑定版与 Stage A 初始版的该数组不完全一致。
- [ ] 仅因 intake `project.id` 就将任一项目状态的顶层 `project_id` 绑定到该 ID 或视为批准事实；intake `project.id` 未原样保存为未确认需求 source fact，或未经授权确认就标记为 `confirmed`。
- [ ] `requirement_baseline.project_id=null` 时，其 `status` 不是 `pending | rejected`，项目标识需求已为 `confirmed`，或 `intake_run_id` 缺失/与 Stage A `source_manifest`/`template_profile` 不一致；或除这三类有限例外外的任一项目状态对象 `project_id` 为空。
- [ ] 项目标识需求已 `confirmed` 后，未新建 `project_id` 非空的绑定基线版本，新版本未保持同一 `intake_run_id` 或未用 `origin_version_ref` 指向直接上一基线版本，或原空 ID 基线被原地修改/覆盖；非绑定基线或 `project_id=null` 基线被标记为 `approved`。
- [ ] `requirement_baseline.status=approved` 且项目标识需求已 `confirmed`、`requirement_baseline.project_id` 非空后，未新建绑定该 ID 的 `source_manifest`/`template_profile` 版本；首个 project-bound 版未指向 Stage A initial，或后续 bound 版未指向直接上一 bound 版；新版本未保持同一 `intake_run_id` 或未变内容的 `content_fingerprint_refs`；原 `project_id=null` 版本被修改/覆盖；或 C–H 下游直接引用了 `project_id=null` 的阶段 A 版本。
- [ ] `space_plan`、`candidate_plan` 或输出对象直接消费 intake 字段，而非引用已批准基线版本及 confirmed `requirement_refs`。
- [ ] `space_plan` 缺少 `requirement_baseline_version_ref`、`source_manifest_version_ref` 或 `template_profile_version_ref`；`candidate_plan` 缺少上述三项或 `space_plan_version_ref`；任一引用未指向同一非空 `project_id` 的项目绑定版本，或 `non_spatial` 候选未引用 approved `space_plan`。
- [ ] `space_plan`、`candidate_plan` 或任一基线批准后的下游状态 `project_id` 为空/与 project-bound 基线不一致，未绑定 `status=approved`、`project_id` 非空且项目标识需求已 `confirmed` 的确切 `requirement_baseline_version_ref`、`requirement_refs` 和 `evidence_refs`，或 Stage A initial → project-bound → downstream 的 `origin_version_ref`、`intake_run_id`、`content_fingerprint_refs` 链无法确定性验证。Stage A initial 的 `project_id=null` 不是 ID 不一致错误；它只要求上述三类链接一致。
- [ ] `candidate_plan.requirement_refs` 未覆盖计价、币种、优先级、范围、项目规则、输出要求及其他计划级约束，或其中任一需求在绑定基线版本中不是 `confirmed`。
- [ ] 任一计划级派生字段未通过 `plan_field_requirement_refs` 指向顶层 `requirement_refs` 中的具体需求，映射为空/越界，或仅使用笼统 `evidence_refs` 代替需求引用。
- [ ] `requirement_baseline.status=approved`，但任一 `requirement_baseline.budget_limits` 尚未确认，或缺少有效的 `gate=requirement_baseline`、`target_type=budget_limit` 审批。
- [ ] 任一 `requirement_baseline.budget_limits.requirement_id` 缺失，未指向同一基线中 `status=confirmed` 的预算需求项，或预算限制的证据/答案与该需求项不一致、存在编造或改写。
- [ ] 同一基线中 `budget_limits[].requirement_id`、`budget_limit_id` 或 `budget_bucket` 任一重复；每个 limit 未恰好引用一个 `category=budget AND status=confirmed` 的专用预算需求，或任一此类需求被 0 个或多个 limit 反向引用；反向集合误纳入了其他 `category` 的需求，或仅因其 `affects` 含预算桶而强制建立独立 `budget_limit`。
- [ ] 已选输出行存在同名多型号但尚未由用户或授权方确认。
- [ ] 被 `internal_product_mapping`、`confirmed_totals` 或最终输出引用的行不是 `status=confirmed AND selected_for_output=true`，或任一 `selected_for_output=true` 行为 `draft | pending_confirmation | rejected | waived`。
- [ ] `selected_for_output=true` 的产品行缺少标准产品库来源、SHA-256 指纹或稳定记录定位。
- [ ] 已插入的产品图片未通过稳定 `catalog_product_key` 绑定，缺少 `role=primary`、`confidence=exact` 或 `match_rule=normalized-name-brand-model-v1`，相对路径逃逸 `assets/product-images/`，图片 SHA-256 不匹配，或图片单元格/来源图片单元格未写入 `internal_product_mapping` 与追溯审计。
- [ ] 正式输出涉及的产品缺少 `source_spaces`、`function_tags` 或 `product_intro` 任一关键字段，或未生成对应质量问题而进入正式清单。
- [ ] `selected_for_output=true` 的非产品行缺少规则来源、计价依据或批准依据。
- [ ] `selected_for_output=true` 行的单位或价格与已绑定来源不一致，且无有效批准记录。
- [ ] `confirmed` 产品行的名称、品牌、型号、单位、单价、数量、参数、身份或来源任一缺失/为 `null`，或彼此不匹配；非产品行未满足已批准规则的完整性要求。
- [ ] 总额或预算桶金额超过项目批准的预算容差。
- [ ] 任一 `budget_limits` 缺少稳定 `budget_limit_id`，或其 `approval_ref` 未指向 `status=approved`、`gate=requirement_baseline`、`target_type=budget_limit`、`target_refs` 精确包含该标识且 `confirmed_content` 快照逐项匹配 `budget_bucket`、`target_amount`、`tolerance_type`、`tolerance_value` 的记录；无关已批准记录不得通过。此时不得执行正式容差判断或正式发布，`validation_status` 必须为 `draft | unresolved`。
- [ ] 百分比容差不在 0–100，未按 `target_amount * tolerance_value / 100` 转为允许绝对偏差；绝对容差为负数或货币单位不同；未按默认对称范围逐预算桶校验 `confirmed_totals`，或未经批准采用不对称范围、跨桶抵消。
- [ ] 预算桶重复，`approved_budget_total` 不是 `budget_limits[].target_amount` 的只读求和，或逐桶 gap、总 gap、正式校验使用了 `budget_limits` 之外的预算来源。
- [ ] `candidate_plan.budget_limits` 与已批准 `requirement_baseline.budget_limits` 的 `requirement_id`、`budget_limit_id`、`approval_ref`、预算桶、目标、容差或证据引用不完全一致，或预算在候选阶段另填、编造或变更。
- [ ] `candidate_plan.budget_limits` 未保持基线仅针对 `category=budget AND status=confirmed` 专用预算需求的 `requirement_id ↔ budget_limit_id` 双射及 `requirement_id`、`budget_limit_id`、`budget_bucket` 三类唯一性，或出现多复制/漏复制；其他 `category` 的需求因 `affects` 含预算桶而被纳入双射或据此新增独立 `budget_limit`。
- [ ] `candidate_plan.requirement_refs` 未包含全部预算快照的 `requirement_id`，或 `plan_field_requirement_refs.budget_limits` 未逐项覆盖这些预算需求引用。
- [ ] 预算变更未创建并批准新的 `requirement_baseline` 版本，或未据此重建 `space_plan`/`candidate_plan` 快照。
- [ ] `blocking=true` 的需求仍未解决。
- [ ] 必配功能缺失且无明确豁免记录。
- [ ] 已选输出配置与项目特定禁配清单、适用边界、品牌/类型限制或其他已确认边界规则冲突。
- [ ] 输出模板的必填字段缺失。
- [ ] 公式错误、引用断裂、汇总范围错误或计算值与明细不一致。
- [ ] 敏感信息或供应商信息违反模板、合同、授权范围或交付规则。
- [ ] 面积或人数直接决定数量，但面积、人数或换算规则未确认，也没有批准的暂估依据。
- [ ] 已选输出行的产品名称、品牌、型号、类型、参数、数量或身份键与来源/批准状态冲突。
- [ ] 正式输出覆盖了源文件、固定来源或既有批准版本。
- [ ] `selected_for_output=false` 的行进入 `internal_product_mapping`、正式输出或 `confirmed_totals`，或正式输出未与 `confirmed_totals` 对账。
- [ ] 被正式输出或阻断需求引用的 `rejected | waived` 行缺少审批依据，或 `waived` 被误解释为已选产品而非经审批免配。
- [ ] 影响已选输出行、最终来源记录或阻断需求的 `resolved | waived` 质量问题，其 `approval_ref` 未指向 `gate=product_plan`、`target_type=quality_issue` 且 `target_refs` 含对应 `quality_issue_id` 的已批准记录。
- [ ] 固定资源内容不可读、SHA-256 指纹无法生成，或实际指纹与批准/发布绑定指纹不一致。
- [ ] `assets/project-intake-template.yaml` 未在 `source_manifest`/`final_release.input_versions` 中绑定固定路径、SHA-256 指纹和 `schema_version=1.1`，或其指纹变化后未重新解析、映射和校验受影响项目状态。
- [ ] 正式 `final_release.input_versions` 缺少 `requirement_baseline_version_ref`、`source_manifest_version_ref`、`template_profile_version_ref`、`space_plan_version_ref` 或 `candidate_plan_version_ref`；前四项与 `candidate_plan` 同名字段不同值，直接引用了 `project_id=null`/其他项目版本，或 `content_fingerprint_refs` 与所绑 Stage A 初始版在内容未变时不一致。只是通过链回溯到 `project_id=null` 的 Stage A initial 不属于错误。
- [ ] Intake 指纹变化后未从 A/B 重建新基线版本，或未在基线批准后按 C–H 分阶段重放并保留 `evidence_refs`/版本引用。
- [ ] `status=open` 的质量问题影响 `selected_for_output=true` 行、最终输出使用的来源记录或 `blocking=true` 需求。
- [ ] `space_plan.mode=spatial|hybrid`，但正式/草案清单未按目标空间分组、未以空间名称作为分组标题或专列逐行标注、未按空间给出小计，或仅按功能类别分组而丢失空间维度；跨空间/项目级行未归入显式"项目级·通用"或"跨空间共用"分组而被随意并入单一房间；或任一输出行的所属空间无法回溯到其候选行目标空间、分组小计与 `space_plan` 不一致。
- [ ] 已生成候选产品行、数量、单价或预算合计（或将其写入工作簿/清单）早于 `requirement_baseline.status=approved` 且未先向用户提请确认；或在用户未显式确认的情况下将任一前置闸门（`requirement_baseline`/`space_mode`/`product_plan`/`final_release`）标记为 `approved` 或跳过其确认检查点（静默通过）。

## Warnings（警告）

以下项目需在草案和验证摘要中披露，并说明影响与处理建议：

- [ ] 使用暂估面积或暂估工程量。
- [ ] 关键语义字段齐全但 `confidence=low` 的弱空间语义匹配；关键字段缺失不是警告，必须按硬错误阻断受影响产品。
- [ ] 缺少采购历史或供应历史，无法进行历史可得性佐证。
- [ ] 价格来源日期过旧，超出项目定义的时效阈值。
- [ ] 可选功能未覆盖。
- [ ] 固定资源未提供 `business_version` 或 `effective_date`；不得编造，且缺失本身不阻断。
- [ ] 已选产品没有已验证的本地图片引用；留空图片单元格，并披露 `image-import-report.json` 中的原因。除非已批准输出要求把图片设为必填字段，否则不阻断发布。
- [ ] 仅影响 `selected_for_output=false` 或 `rejected | waived` 候选的 open 质量问题；保留质量记录但不全局阻断。
- [ ] 未选中的 `draft | pending_confirmation | rejected | waived` 候选仍保留在方案中；披露其状态、未决项或审批历史，但不因状态本身阻断发布。
- [ ] 仅关联未选/已排除候选的 `rejected | waived` 行缺少审批依据，或其质量问题的解决/豁免审批引用不完整；作为历史质量 warning 修正，不全局阻断正式发布。
- [ ] `confidence=medium` 且会显著影响数量、成本或适用性的候选项。
- [ ] 存在未选定的替代项或非阻断需求仍处于模糊、冲突、缺失、假设状态。

## Release gate（发布闸门）

正式版必须同时满足：

- [ ] 硬错误数量为 0。
- [ ] 所有审批状态字段仅使用 `pending | approved | rejected | not_applicable`。
- [ ] 需求状态字段仅使用 `confirmed | ambiguous | conflicting | missing | assumption`。
- [ ] 需求基线、空间/模式、产品方案三个前置闸门均为 `approved`；其中需求基线必须是 `project_id` 非空、项目标识需求已 `confirmed` 且版本链可追溯的绑定版本。
- [ ] 输出明细、预算桶、税费/折扣（如适用）和总额与内部 `candidate_plan.amount_summary.confirmed_totals` 映射一致。
- [ ] 所有公式可计算且结果与内部金额核对一致。
- [ ] 必填字段完整，产品行 100% 可追溯，非产品行均有规则或批准依据。
- [ ] 所有警告已写入交付说明并由责任方审阅。
- [ ] 业务签核已记录在 `approval_log`。
- [ ] 正式版的 `final_release.status=approved`，并记录批准人、批准时间及所绑定输入版本。
- [ ] `final_release.input_versions` 的五个项目状态版本引用齐全，前四项与 `candidate_plan` 同名字段同值，所有引用对象的非空 `project_id` 与 `final_release.project_id` 一致，并可通过 `origin_version_ref`、`content_fingerprint_refs` 和相同 `intake_run_id` 从 downstream 确定性追溯到未覆盖的 Stage A initial 版本。

## 通过标准

草案可以在保留警告和非阻断未决项的情况下生成，但必须明确标记为草案。正式版仅在硬错误为 0、审批与需求状态值合规、输出金额和公式与内部映射一致、业务签核完成且 `final_release.status=approved` 时通过。
