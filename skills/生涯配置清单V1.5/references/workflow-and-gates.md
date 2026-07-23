# 工作流与闸门

按 A–H 顺序推进。可以回退到前一阶段修订，但不得绕过闸门把未批准草案当作正式版。

## A. 资料和模板接收

- 接收需求资料、标准产品库、四份 references、`assets/project-intake-template.yaml`、历史依据和用户模板，建立 `source_manifest`。固定资源使用原始字节的 SHA-256 `content_fingerprint` 作为权威技术版本；intake asset 还必须记录固定路径和 `schema_version=1.1`。自带 `business_version`/`effective_date` 时原样记录，缺失只记 warning，不编造、不自动停止。内容不可读、指纹无法生成或与批准指纹不一致才阻断。使用 intake template 指纹与排序后的输入内容指纹按 `sha256-intake-run-v1` 确定性生成 `intake_run_id`，并在 `source_manifest` 中记录算法、模板指纹和排序后的输入指纹。不得使用时间、随机值、文件名、临时项目 ID 或业务推测。
- 标准产品库的 `image_catalog` 与 `assets/product-images/` 是只读固定图片资源。阶段 A 在 `template_profile` 中记录 `产品图片` 列、行高、打印区域和样式策略；不在此阶段将图片映射到项目行，也不得把图片当作产品身份或需求证据。
- `project-intake-template.yaml` 仅按输入采集 schema 1.1 解析。阶段 A 只创建 `source_manifest` 与初始 `template_profile`，两者必须共用同一 `intake_run_id` 并记录相同生成输入；在 `requirement_baseline.project_id` 确认前，其必填 `project_id` 字段允许为 `null`。本阶段不创建 `requirement_baseline`、`space_plan`、`candidate_plan` 或 `final_release`；所有 intake 字段留待阶段 B 先写入需求基线。
- intake asset 的 SHA-256 指纹变化时，必须重新解析 schema 1.1，并从阶段 B 重建新基线版本；只有新基线批准后才按 C–H 重放下游映射。不得静默沿用旧映射、旧审批推断或旧项目状态。
- 阶段 A 初始 `source_manifest` 和 `template_profile` 必须同时记录 `project_id=null`、`version`、同一 `intake_run_id`、`origin_version_ref=null` 与按 `resource_ref` 排序的 `content_fingerprint_refs`。其每项使用 `resource_ref`、`fingerprint_algorithm=SHA-256`、`content_fingerprint`、`origin_content_version_ref` 四字段。在本阶段生成 `template_profile`：分析工作表/章节结构、字段、必填项、公式、合并单元格、打印区域、样式保真要求、汇总逻辑和敏感信息边界，并绑定 `template_origin`、`template_id`、`template_version` 与 SHA-256 `content_fingerprint`；复制 `source_manifest` 的 `intake_run_id`、算法和生成输入。默认模板指纹还必须写入 `final_release.input_versions`。
- 只有用户未提供模板时才使用固定底座的默认模板；默认模板也必须有版本和内容指纹。不得在已有用户模板的情况下擅自换成默认结构。
- 用户模板无法可靠解析时，可以生成默认模板结果并附字段映射建议，但必须保留原模板、标明解析限制，且不得把“无法解析”视为“未提供”，不得写回或破坏用户模板。
- 建立来源清单并标记缺失、冲突、过期或不可解析的资料。

## B. 需求提取与澄清

- 创建 `requirement_baseline`，将项目身份/目标、预算限制、计价、范围、优先级、模式提示、空间输入、必配/选配功能、项目规则、输出需求和证据全部拆成带证据的结构化需求；不得提前创建 `space_plan`、`candidate_plan` 或 `final_release`。Intake 提供的 `project.id` 必须原样写入项目标识需求项作为未确认 source fact，未经授权确认时其需求状态不得为 `confirmed`，也不得自动复制为顶层 `project_id` 或批准事实。项目标识尚未确认时，基线可为 `project_id=null`，但其 `status` 只能为 `pending | rejected`，且必须携带与 Stage A 两种产物相同的 `intake_run_id`。
- 使用 `confirmed | ambiguous | conflicting | missing | assumption` 标记需求状态，并填写 `blocking` 与 `affects`。
- 只询问会影响本轮配置或输出结果的未决事项，一次聚焦一个可回答问题；优先询问会阻断模式、空间、数量、预算或必配功能的事项。每个问题应附从资料推导的 `suggested_answer` 与 `suggested_basis`，无可靠建议时明确说明证据不足。
- 不影响本轮配置或输出结果的未决事项仍写入 `unresolved_items`，但必须标记 `blocking=false`，不得阻断本轮结果，也不主动占用本轮澄清提问。
- 答复必须写入 `answer`、`confirmed_by`、`confirmed_at`，不得以无来源推断替代确认。
- 项目标识需求确认后，新建 `project_id` 非空的基线版本，保留同一 `intake_run_id`、用 `origin_version_ref` 指向直接上一基线版本并完整保留证据链；不得原地填写或覆盖空 ID 版本。只有该绑定版本允许 `status=approved`。
- 为每个 `budget_limits` 建立同一基线内 `category=budget AND status=confirmed` 的专用预算需求项，并用 `requirement_id` 双向一对一绑定。校验全部 `requirement_id`、`budget_limit_id`、`budget_bucket` 各自唯一；每个 limit 恰好引用一个此类需求，每个此类需求也恰好被一个 limit 引用，不得为 0 个或多个。反向集合仅限 `category=budget AND status=confirmed` 的需求；其他 `category` 的需求即使 `affects` 含预算桶，也不进入双射，无需并不得据此强制建立独立 `budget_limit`。预算限制的证据和答案必须与需求项一致，不得编造。随后完成 `gate=requirement_baseline`、`target_type=budget_limit` 审批；任一唯一性、双射或审批不合规时，需求基线闸门不得通过。
- 绑定基线成为 `status=approved` 后，分别生成绑定该项目 ID 的新 `source_manifest` 和 `template_profile` 版本。首个 project-bound 版本的 `origin_version_ref` 必须指向 Stage A initial 版；每个后续 bound 版本必须指向直接上一 bound 版。各版保持同一 `intake_run_id` 并逐项原样复制未变内容的 `content_fingerprint_refs`；不修改、不覆盖 `project_id=null` 的初始版本。从 C 阶段起，`space_plan`、`candidate_plan` 及其他下游状态的 `project_id` 必须非空，且与 project-bound 版本一致；Stage A initial 的 `project_id=null` 只通过 `origin_version_ref`、`intake_run_id` 和内容指纹链连接，不与非空 ID 比较。

## C. 模式路由

模式定义如下，必须按定义选择并在 `mode_reason` 中说明依据：

- `spatial`：多个功能空间，且产品或数量依赖房间、面积、人数或活动。
- `non_spatial`：一个或没有有意义的空间维度，且空间不影响产品或数量。
- `hybrid`：至少一个空间依赖项，且至少一个项目级平台、软件或通用项。

只有基线同时满足 `status=approved`、`project_id` 非空、项目标识需求已 `confirmed` 且其绑定版本链可追溯时，阶段 C/D 才可从其 `mode_hint`、`space_inputs`、功能及其他 confirmed `requirement_refs` 创建 `space_plan`。`space_plan.project_id` 必须非空且与该基线一致，并必填 `requirement_baseline_version_ref`、`source_manifest_version_ref`、`template_profile_version_ref`；三者指向同项目绑定版本，共用 `intake_run_id` 且指纹引用不变。

若包含家具、装修、墙布、窗帘或面积计价内容，即使没有图纸，也不得跳过空间和工程量确认。应请求空间清单、尺寸/面积、数量规则或授权暂估，并记录其影响。

## D. 条件与空间规划

- 为每个目标空间建立功能画像，至少填写 `aliases`、`core_functions`、`secondary_functions`、`users`、`activities`、`capacity`、`area` 和 `evidence`。
- 功能画像必须在产品或来源空间的语义匹配之前完成。
- 空间规划建议必须同时说明功能、总面积、人数和项目重点四方面的依据；缺失项应进入 `unresolved_items`，不得以常识补齐。
- 确认面积、人数、活动强度、安装条件、共享关系和工程量依据；未知值保持为空并进入澄清，不得猜测。
- `non_spatial` 可无空间画像，但必须有空间不影响产品和数量的明确理由，仍须生成并批准 `space_plan`，供下游通过 `space_plan_version_ref` 引用。

## E. 候选配置

- 仅在 approved 绑定需求基线和空间/模式闸门通过后创建 `candidate_plan`；`candidate_plan.project_id` 必须非空并与该基线一致。顶层必填 `requirement_baseline_version_ref`、`source_manifest_version_ref`、`template_profile_version_ref`、`space_plan_version_ref`，指向同一项目、同一 `intake_run_id` 链上的确切版本；`non_spatial` 也必须引用 approved `space_plan`。将已批准 `requirement_baseline.budget_limits` 复制为不可编辑快照，保持相同 `requirement_id`、`budget_limit_id`、`approval_ref` 与证据/版本引用，并保持基线中 `category=budget AND status=confirmed` 专用预算需求与 limit 的双射及三类唯一性；其他 `category` 的需求即使 `affects` 含预算桶，也不得纳入该双射或据此新增独立 `budget_limit`。顶层 `candidate_plan.requirement_refs` 必须包含全部预算 `requirement_id`。不得多复制、漏复制、另填、编造或变更；预算变化必须回到新基线版本重新批准后再重建候选方案。
- 候选行必须引用需求与目标空间，并记录功能模块、`configuration_level`、产品身份、选择理由、必要性、功能覆盖、来源、数量依据、预算桶、`budget_delta` 和替代项。
- `candidate_plan` 顶层必须记录 confirmed `requirement_refs`，覆盖计价、币种、优先级、范围、项目规则、输出要求及其他计划级约束；`plan_field_requirement_refs` 必须将每个派生字段确定性映射到其中具体引用。`evidence_refs` 不能替代该映射，候选行级 `requirement_refs` 仍须独立保留。不得从 intake 直接写入候选或输出对象。
- 空间依赖项必须同时使用来源的 `source_spaces`、`function_tags` 和 `product_intro`，再结合目标空间的功能、对象、活动、容量和条件进行语义匹配，记录 `semantic_match_reason` 与 `confidence`。任一关键语义字段缺失时，必须生成数据质量问题并阻断受影响产品进入正式候选或正式清单；只有字段齐全但语义相关性不足时才可标记为弱匹配。
- 产品行必须来自固定产品库；非产品行必须有规则或批准依据。
- `internal_product_mapping` 只能连接 `status=confirmed AND selected_for_output=true` 的候选与需求、空间、产品来源和输出位置；同步维护 `unresolved_items`。
- 建立 `catalog_quality_issues`；关键语义或产品字段缺失/冲突时创建 `open` 问题并写入候选行。只有问题影响已选输出行、最终输出使用的来源记录或阻断需求时才阻断发布；只影响未选/已排除候选时作为 warning/质量记录保留，不能目录级全局阻断。
- 预算用于约束和取舍，不得成为堆入无关产品或反推型号、单位、价格、参数的理由。`budget_limits` 是唯一预算来源：每桶唯一，`approved_budget_total` 只读派生为各桶 `target_amount` 之和，逐桶/总 `budget_gap` 和正式校验均由同一数组计算。
- 每个预算桶必须有稳定 `budget_limit_id`。其 `approval_ref` 只有指向 `status=approved`、`gate=requirement_baseline`、`target_type=budget_limit`、`target_refs` 精确包含该标识且 `confirmed_content` 完整匹配预算桶、目标和容差快照的记录时才有效；无关已批准记录不得通过。引用缺失或无效时，草案可展示目标与容差，但 `validation_status` 必须为 `draft | unresolved`；必须阻断正式发布且不得执行正式容差判断。
- 容差逐预算桶计算：`percent` 的 `tolerance_value` 限 0–100，允许绝对偏差为 `target_amount * tolerance_value / 100`；`absolute` 的 `tolerance_value` 为同货币单位非负数。默认允许范围是目标值加减允许绝对偏差，逐桶比较 `confirmed_totals`，不得跨桶抵消；除非存在另行批准的上下界规则，不得采用不对称范围。预算无法满足时列明差额/缺口、原因和至少一个可执行调整方案，且不得虚构价格。

## F. 产品确认

- 逐行确认名称、品牌、型号、单位、价格、类型、参数、数量与替代关系。
- 同名多型号、来源冲突、弱语义匹配、暂估工程量和必配功能缺口必须显式呈现。
- 用户或授权方的选择和豁免写入 `approval_log`；未确认项保持 `pending_confirmation`，不得进入正式发布。
- 质量问题的解决或豁免必须使用 `gate=product_plan`、`target_type=quality_issue` 的审批记录，`target_refs` 包含 `quality_issue_id`；无候选行时 `candidate_line_refs` 可为空，问题的 `approval_ref` 必须回指该记录。
- 只有 `status=confirmed AND selected_for_output=true` 的行进入正式输出和 `confirmed_totals`。未选 `draft | pending_confirmation` 只可参与可计算的 `proposed_totals`；`rejected | waived` 排除在两类金额和正式输出之外，其中 `waived` 仅表示经审批免配。未选/已排除候选可保留且不因状态本身阻断，但必须披露 warning 或审批历史。

## G. 模板输出

- 按 A 阶段分析过的用户模板输出；仅在无用户模板时使用默认模板。
- 按已绑定确认 `project_id` 的 `template_profile` 新版本映射内部字段到模板字段，正式输出和 `internal_product_mapping` 只引用 `status=confirmed AND selected_for_output=true` 的行，并只与 `confirmed_totals` 对账；保留内容指纹和可追溯引用，并校验公式、单位、价格、数量、金额和汇总。应保留合并单元格、打印区域及样式保真，无法保真处必须披露。
- 仅在产品方案闸门通过后，才可按 `internal_product_mapping.catalog_product_key` 为已选行插入图片。图片必须来自该产品唯一的本地 `image_refs` 主图，并校验相对路径及 SHA-256；在映射和追溯审计中记录图片源单元格、资源路径、哈希和输出单元格。禁止按名称重新匹配、使用外部链接、网络搜索或生成图。没有已验证图片时留空并披露 warning；除非已批准输出要求把图片设为必填字段，否则不阻断。
- 输出结构必须反映空间维度：`space_plan.mode=spatial|hybrid` 时，按已批准 `space_plan` 的目标空间分组落表，分组标题使用空间名称（或专设"空间/功能室"列逐行标注），并按空间给出小计，再汇总总计。项目级/软件/通用/跨空间共用行归入显式"项目级·通用"或"跨空间共用"分组；不得只按功能类别分组、不得省略空间名称、不得把跨空间行随意塞入单一房间。模板若无子项/小计机制，则在保持必填结构前提下新增"空间/功能室"列。每条输出行的所属空间必须可回溯到其候选行的目标空间引用，分组与小计须与 `space_plan` 一致。`non_spatial` 模式免空间分组，但须在交付说明记录原因。

### 未匹配需求的强制输出

- 未匹配需求是有来源、但没有可靠且已批准的产品库映射或非产品规则依据的需求警示行；它不是替代产品，也不得作为 `selected_for_output=true` 的产品行。
- `spatial|hybrid` 时，必须在对应空间中已匹配产品行之后、空间小计之前保留该行；`non_spatial` 时，必须放入明确标注的“项目级·未匹配”分组并位于总计之前。主清单保留有证据的需求名称、单位、数量、技术约束和未匹配原因；不得补造产品名称、品牌、型号、参数、图片、价格或数量。
- 未匹配主清单行的 `产品图片`、所有单价与金额单元格必须留空，不参与任何空间小计、总计、`confirmed_totals` 或 `internal_product_mapping`。
- `未匹配需求汇总`工作表必须为每条未匹配需求生成一行，记录序号、目标空间、来源需求、已知单位/数量/技术约束、未匹配原因和后续处理说明；主表和汇总表均需通过 `unresolved_items` 与 `traceability_audit` 保留同一追溯引用。
- `blocking=true` 的未匹配需求必须在标注的草案中可见，且继续阻断正式发布；非阻断未匹配需求必须作为 warning 披露，不能静默省略。
- 对无法可靠解析的用户模板，只能输出默认模板结果和字段映射建议，不得覆盖、改写或破坏用户模板。
- 每次输出生成新版本。草案必须标识未决项、假设和警告，不覆盖源文件或已批准文件。

## H. 验证与交付

- 生成 `traceability_audit`，执行硬错误、警告和发布闸门检查，并核对输出金额与 `candidate_plan.amount_summary.confirmed_totals`；未确认事项必须与 `unresolved_items` 一致。
- 在 H 阶段验证通过后创建/批准 `final_release`；阶段 A/B 不得预建或预批最终发布对象。`final_release.input_versions` 必含与 `candidate_plan` 同名同值的 `requirement_baseline_version_ref`、`source_manifest_version_ref`、`template_profile_version_ref`、`space_plan_version_ref`，并用 `candidate_plan_version_ref` 引用实际发布候选版本。所有 project-bound 和 downstream 引用的 `project_id` 必须与发布对象一致且非空；回溯所到 Stage A initial 的 `project_id=null` 不参与该相等性检查。任一下游直接引用 `project_id=null` 版本、`origin_version_ref` 未逐跳链接或 `content_fingerprint_refs` 无内容变化却不一致均阻断正式发布。
- 自动校验通过后仍需业务签核；校验与签核缺一不可。
- 仅当最终发布闸门批准时交付正式版；否则只能交付明确标记的草案或问题清单。

## 四个闸门

| 闸门 | 最晚位置 | 通过条件 | 未通过处理 |
|---|---|---|---|
| 需求基线 | B 后、C 前 | 阻断需求已回答或获明确处理决定；项目标识需求已 `confirmed`；基线 `project_id` 非空且绑定版本链可追溯；预算限制均已确认并专用审批；证据、状态和影响范围完整；`requirement_baseline.status=approved` | 回到 B，继续逐项澄清 |
| 空间/模式 | D 后、E 前 | 模式符合精确定义；所需空间画像与工程量依据完整；`space_plan.status=approved` | 回到 C 或 D 修订 |
| 产品方案 | F 后、G 前 | 所有 `selected_for_output=true` 行均为 `confirmed` 且来源/数量/预算依据可审计；未选/已排除候选已披露；`candidate_plan.status=approved` | 回到 E 或 F 调整 |
| 最终发布 | H | 硬错误为零、金额与公式一致、业务签核完成；`final_release.status=approved`；Stage A 输入版本已绑定相同非空 `project_id` | 仅保留草案，不得正式发布 |

## 草案与正式版

- 草案用于评审、澄清和迭代，可以包含 `pending` 审批、假设、暂估、警告或未选替代项，但必须醒目标识且不得声称已批准。
- 正式版只能基于已批准的需求基线、空间/模式和产品方案生成；必须通过最终发布闸门并具有 `final_release.status=approved`。

## 异常处理

- 标准产品库缺失、不可读取、SHA-256 指纹无法生成或与已批准指纹不一致时，立即停止选品；只输出问题说明和所需资料，不得用历史记忆、网络信息或假设替代。仅缺少 `business_version`/`effective_date` 时记录 warning，不停止选品。
- 产品库字段不完整时生成数据质量报告，列出缺失字段、来源记录、影响的功能/空间/候选行和修复建议；所有受影响产品必须阻断，不能以空值或推测继续确认。
- 预算无法满足时，输出明确的 `budget_gap`、缺口原因和至少一个调整方案；调整可改变范围、等级、数量或替代关系，但不得虚构价格或擅自删除必配功能。
- 标准产品库 SHA-256 `content_fingerprint` 发生变化时，保留旧版 `candidate_plan`、`internal_product_mapping` 和 `traceability_audit`，基于新指纹重新执行候选配置、产品确认与追溯审计，并标记指纹差异；不得覆盖旧版。
