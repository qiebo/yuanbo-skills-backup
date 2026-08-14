# 通用强约束

本文件只定义跨项目不变的强约束。项目需求、空间名称、预算、候选方案、审批结论等项目特定值必须写入项目状态对象，不得回写本文件或薄映射层。

## 1. 来源与版本

- 本技能的数据来源分为三层：
  1. **薄映射层 `assets/product-mapping.json`**（人维护的只读固定资源）：仅含语义映射（`tag_routing` / `category_fallback` / `space_to_query`）、查询路由（`query_routing.business_lines`：业务线 → ERP 启用大类，人工维护）、需求词同义词（`keyword_aliases`：需求词 → ERP tags/小类/分组关键词，人工维护）、主键映射（`key_map`）、价格策略（`price_policy`）与图片策略（`image_policy`）。自动派生部分由 `scripts/build_product_mapping.py` 从 ERP 全量实测生成；人工知识经 `assets/product-mapping.overlay.json` 深合并进入，重跑 build 不丢失。每次运行必须对其原始字节计算 SHA-256 `content_fingerprint`，该指纹是权威技术版本，并记录资源名称、路径和指纹算法。
  2. **运行期 ERP 快照**（运行期生成的只读固定资源）：产品内容经 `scripts/fetch_erp_catalog.py` 从 ERP §6 按需切片拉取（按业务线、目标空间或关键词对应的 `category_id` / `classification_id` / `name` 查询，可再经 `--keywords` 客户端按 产品名+tags+小类名+分组名 收窄），生成为 `assets/erp-runs/<run_id>/snapshot.json`。**该快照即本次运行的"标准产品库"等价物**，必须 SHA-256 指纹化，并记入 `source_manifest.content_fingerprint_refs` 与 `final_release.input_versions`；快照内含 `products[]`，每条为归一化产品记录。产品事实（名称、编号、品牌、型号、价格、tags、小类/分组、图片 URL）**只**存在于本层，技能包不附带任何产品数据。
- 固定资源若自带 `business_version` 或 `effective_date`，必须原样一并记录；缺失时不得编造，也不因缺失自动停止，只生成 warning。只有内容不可读、SHA-256 指纹无法生成，或实际指纹与已批准/已绑定指纹不一致时才阻断。
- 阶段 A 的 `source_manifest` 和 `template_profile` 必须共用稳定 `intake_run_id`。该标识必须由 intake template 指纹与排序后的全部输入内容指纹确定性组合并使用 SHA-256 生成，同时记录算法版本和输入指纹；不得使用时间、随机值、文件名或业务推测。
- 项目标识确认前，阶段 A `source_manifest`/`template_profile` 及 `status=pending | rejected` 的 `requirement_baseline` 必填 `project_id` 字段允许为 `null`；三者必须保留同一 `intake_run_id`。项目 ID 确认后必须新建 `project_id` 非空的基线版本，保留 `intake_run_id` 和旧版本引用，不得原地覆盖；只有该绑定基线可为 `approved`。除上述有限例外外，其他项目状态对象必须携带非空 `project_id`。
- 输出必须另存为新版本，不得覆盖用户源文件、薄映射层、references、intake asset、默认模板、ERP 快照或已批准版本。
- 设备产品行必须 100% 可追溯到 ERP 快照中的唯一来源记录；追溯信息至少包含快照的 SHA-256 `content_fingerprint`、稳定记录标识 `product_key`（= ERP `product_no`）与 `erp_id`。禁止把本地旧 `standard-products.json` 当作来源。
- 产品图片是 ERP 产品记录的可选视觉资产（远程 `image_url`），不是产品事实或身份依据。仅当来源快照记录的 `image_refs` 含 `role=primary`、`confidence=remote`、`match_rule=erp-image-url-v1` 且 `locally_verified=false` 时，才可引用其远程 URL；图片只作视觉支持，绝不以图片、同名、外观相似、网络检索或生成图推断、替换或确认名称、品牌、型号、价格、参数或来源。**禁止下载图片到本地、禁止本地 SHA-256 核验、禁止替换 ERP `image_url`。**
- 图片缺失只作为 warning 并在交付说明中披露；除非已批准的输出要求把图片设为必填字段，不得因图片缺失阻断选品或发布。反之，若正式输出已插入图片引用但其 `product_key`、URL 或来源快照无法追溯，则该图片行不得发布。
- 非产品行（如工程、服务、辅材或暂估项）必须注明规则来源、计价依据或用户批准依据，不得伪装成 ERP 快照产品。
- 自动校验只能发现结构性和一致性问题，不能替代需求方、业务方或授权审批人的业务签核。

## 2. 产品身份与阻断条件

- 产品身份必须使用"名称 + 品牌 + 型号"，并生成稳定的 `product_identity_key`；不得仅以名称、简称或展示文案判定同一产品。当 ERP `brand` / `model` 为 `/` 或空时，仅用名称生成。
- 稳定记录标识 `product_key` = ERP `product_no`（产品编号），用于唯一定位来源快照记录与图片引用；不得以 `product_identity_key` 或产品名称替代 `product_key`。
- 同名多型号时必须停止该项的正式确认并请求用户选择；未确认前不得自动挑选、合并或以价格推断型号。
- 名称、单位、价格、类型和参数均不得猜测。来源缺失、冲突或不完整时，标记为待澄清或阻断，不得用常识补齐。
- 对外品目名称必须原样使用 ERP 快照的标准 `product_name`，不得整理、缩写、扩写或项目化改写。项目化名称只能写入用途或说明字段，不得替代或改变产品名；品牌、型号及可追溯身份不得被隐藏、替换或混淆。
- 对外参数只可从已确认来源中摘取或删减；不得改写技术含义、扩大能力、组合不同型号参数或补造来源未声明的指标。
- `source_spaces` / `function_tags` / `product_role` 由 ERP `tags` 经薄映射层 `tag_routing` 派生；`tags` 为空的产品回退到 `category_fallback`（按类目词频派生的低置信补充，不得作为主锚点）。产品语义以多信号为准（见 §4）：小类名（`category`）与分组名（`product_group`）、`function_tags`、产品名、`product_intro` 四者皆无有效语义时，必须生成 `blocking` 质量问题并阻断该产品进入正式候选或正式清单，不得仅以降低置信度处理；`source_spaces` 缺失不属于语义缺失，不生成质量问题、不阻断。

## 3. 需求、预算与事实边界

- Intake 只是输入证据；空间计划、候选方案和最终发布不得直接消费 intake 字段，必须引用已批准 `requirement_baseline` 的确认需求与版本证据。
- Intake 提供的 `project.id` 只能原样作为未确认 source fact 写入需求项，不得直接视为项目归属或批准事实，也不要求阶段 A 产物据此填入 `project_id`。
- 不得为了填满预算增加与已确认需求无关的产品、工程或服务。
- 假设、暂估和推断必须显式标记，并记录依据、影响范围、置信度和所需确认；不得把假设写成事实。
- 面积、人数、活动强度、班级数、课时数、参赛队数等条件只能按已确认规则或已批准暂估影响数量，不能未经确认直接转换为数量。

## 4. 语义匹配与空间数量

- 产品语义匹配采用**多信号分层**，不以任何单一字段为唯一锚点，业务线（生涯/科创/……）均适用同一套框架：
  1. **业务线大类**（映射层 `query_routing.business_lines` → ERP 父分类）决定拉数切片入口；
  2. **小类名（`category`）与分组名（`product_group`）**是 ERP 必填的受控词表（如"科创中心-课程""心理设备""航空硬件和耗材"），提供粗粒度功能定位，是一等匹配锚点；
  3. **`function_tags`**（ERP `tags` 派生）提供细粒度主题匹配（如"立方星""宣泄""四足机器人"）；
  4. **产品名**本身携带主题词（ERP `name` 参数模糊匹配 name+tags 时已覆盖）；
  5. **`product_intro`** 作补充佐证；
  6. **`source_spaces`**（tags 中的空间词）仅表示来源资料中该产品的常见或适用空间，是参考证据，不是目标空间名称的硬约束；其缺失不生成质量问题、不阻断。
- 需求侧功能词来自已批准基线的 confirmed 功能需求（`required_functions`/`optional_functions`）与空间画像的 `core_functions`/`secondary_functions`，经映射层 `keyword_aliases` 同义词扩展后与上述信号匹配。制作清单人员不熟悉产品名称时，可直接按需求功能词/标签词检索匹配，这是预期用法而非绕过流程。
- 每条候选必须记录 `semantic_match_reason` 和 `confidence`；理由应说明命中了哪些信号（小类/分组、tags、名称、介绍）以及它们与需求功能词/目标空间画像的对应关系，置信度必须使用项目状态定义的允许值。弱匹配只适用于主锚点信号齐全但语义相关性不足的情况。
- 小类名/分组名、`function_tags`、产品名、`product_intro` 四者皆无有效语义时，必须生成质量问题并阻断受影响产品进入正式候选或正式清单，不得仅以降低置信度处理；仅部分信号缺失（含 `source_spaces` 为空）不阻断，按需生成 warning 或弱匹配备注。
- 空间维度不承担匹配守门职责，只承担三件事：**数量推导**（spatial/hybrid 模式下按空间、面积、人数、班级数等已确认依据推导数量）、**物理适配**（面积、容量、安装条件与产品的匹配确认）、**输出分组**（清单按空间分组并小计）。
- 合理的多数量配置和跨空间重复不是重复数据，不得仅因名称或身份相同而误删；应结合目标空间、功能用途和 `quantity_basis` 判断。
- 空间维度必须贯穿到最终交付物：当 `space_plan.mode` 为 `spatial` 或 `hybrid` 时，正式/草案清单必须按已批准 `space_plan` 的目标空间分组呈现，每个分组以空间名称作为可见标题（或专设"空间/功能室"列逐行标注），并按空间给出小计。项目级平台、软件、通用件或确属跨空间共用的行，必须归入显式标注的"项目级/通用"或"跨空间共用"分组，不得静默并入某个房间。禁止在 `spatial`/`hybrid` 模式下只按功能类别（如"测评类/宣泄类"）分组而不标注空间名称。`non_spatial` 模式不要求空间分组，但需在交付说明中说明原因。若目标模板缺少可复用的子项/小计机制，必须在不破坏模板必填结构的前提下新增"空间/功能室"列承载该维度。

## 5. 发布纪律

- 草案必须清楚标识未决事项、暂估和未审批内容，不得以正式版名义交付。
- 正式发布前必须完成规定闸门、自动校验和业务签核；任一通过均不能替代其他项。
- `space_plan`、`candidate_plan` 及其他基线批准后的 C–H 下游状态严禁 `project_id=null`，且只能引用同一项目的 `status=approved`、`project_id` 非空绑定基线，以及已绑定该 ID 的 `source_manifest`/`template_profile` 新版本。下游必须使用显式版本引用字段，按 `origin_version_ref` 逐跳从绑定版回溯 Stage A 初始版。`intake_run_id` 与未变内容的 `content_fingerprint_refs` 必须跨 initial→bound→downstream 一致；非空 `project_id` 一致性只检查 project-bound→downstream。Stage A initial 的 `project_id=null` 是合法例外，通过 `origin_version_ref`、`intake_run_id` 和内容指纹链连接，不要求与 bound 的非空 ID 相等。
