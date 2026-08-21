# Changelog

## 0.8.0

将 0.7.1 的提示词执行层收敛成果正式定版为大版本 0.8.0，并规范化打包：

- **版本定版**：0.7.1 的"单一事实源 + 职责下沉"精简（总师 24.4k→7.2k、需求分析 16k→5.5k、A 三规模 / C 两形态路线矩阵、single_space 合并卡双 approval、提示词预算守卫、Windows UTF-8 兼容）正式并入 0.8.0。
- **打包规范化**：zip 根目录名统一为 `name`（`yuanbo-school-proposal-team`），不再带版本后缀，避免覆盖安装时目录名与 name 不一致。

## 0.7.1

在不改变 0.7.0 关键门禁和 Artifact 合同的前提下，做提示词执行层收敛：

- **共享规则单一事实源**：把路线、规模、确认卡、交接和交付规则集中到 `proposal-core`；Agent MD 只保留角色动作、输入、输出和停止条件。
- **总师提示词精简**：从约 14k 字符压到约 4.6k；改为短状态机 + 路线矩阵 + 门禁表，补齐 `A-single_space/A-multi_space/A-center_level` 与 `C-single/C-multi`。
- **成员提示词精简**：压缩需求分析、调研、顶层设计、主笔、QA 的重复说明，保留原有字段、分片、客户化、QA closure 和泄漏规则。
- **single_space 合并卡明确化**：卡②③合并时必须分别记录 `design_approved` 与 `outline_approved`，不因合并界面跳过任一合同。
- **提示词回归预算**：lint 对总师 ≤8000 字符、需求分析 ≤7000 字符设置硬预算，并守卫路线矩阵与合并卡字段。
- **Windows 输出兼容**：`leak_scan.py`、`check_env.py` 和泄漏测试统一使用 UTF-8 诊断输出，避免 GBK 控制台把门禁误判为失败。

## 0.7.0

针对 v0.6.3 设计评审（1 P0 + 8 P1 + 9 P2）的一致性债收敛，逐条落地 18 项修复。

### P0
- **P0-1 交付前门禁改按路线裁剪的门禁矩阵**：门禁从"全部为是"的单一全量清单改为按路线裁剪（A 全量 / B 卡①+QA闭环+扫描+精排版 / C 最小集）；B 路线补精排版步骤并注明无卡②③④；proposal-core 同步；WORKFLOW_LOG 注明未列门禁项按路线不适用。

### P1（合同字段补齐 + 一致性）
- **P1-1** closure 表述统一为"首轮 pass，或 revise 后 closure pass"（lead 卡④ / proposal-core 卡④ / L10.8 三处）。
- **P1-2** proposal-writer 新增 SECTION_OUTLINE 输出合同（章节树 + depth/budget_ratio + draft_part_plan），并入 proposal-core artifact 枚举，卡③加前置校验。
- **P1-3** DESIGN_BRIEF 合同增 `downstream_dispatch`（program_needed/space_needed/rationale）与 `depth_plan`（逐板块 depth/budget_ratio）；卡②渲染两字段；门禁校验；lint 守卫。
- **P1-4** WORKFLOW_LOG 卡①行加 `direction_confirmed: Dx`；Phase 2 规定派发 evidence/top-design 必附卡①方向结论。
- **P1-5** 总师 MD 瘦身至 <14,000 字符（排版细则唯一来源 proposal-writing、扫描细则唯一来源 proposal-qa、澄清细则唯一来源 proposal-core；frontmatter 增挂 proposal-writing/proposal-qa）。
- **P1-6** 主笔 DRAFT/REVISED_DRAFT 按章分片协议（≤4000 字、DRAFT_part{i}/n、末尾短索引）。
- **P1-7** A 路线规模分级：project_scale 驱动 single_space 轻量档（澄清 1 轮、卡②③合并、evidence 降级）。
- **P1-8** lint 跨文件一致性断言（双 leak_scan.py 逐行一致、SECTION_OUTLINE 枚举完备）；prompts.md 扫描命令改绝对路径；新增 L10.9。

### P2（优化项）
- **P2-1** 双份 leak_scan.py DOCX_PART_RE 增 `docProps/(core|app).xml`，xml_visible_text 适配 docProps 元数据；test 补 docProps 用例。
- **P2-2** test_leak_scan.py 参数化跑双脚本；quality-reviewer 改引 skill 内词表。
- **P2-3** leak_terms.txt 加负向断言，消除"学校总方案/学校总体方案"误报，收紧回应模式尾组。
- **P2-4** clarify_waived 唯一落点 clarify_trace.clarify_waived；direction_options 已选定时卡①只做确认回显不重问。
- **P2-5** WORKFLOW_LOG 重写为 Step↔Phase 显式映射。
- **P2-6** TEST_PLAN/README 版本头清理，历史入附录/CHANGELOG。
- **P2-7** 产物落盘约定 `<工作区>/output/proposal/` + 命名规则 + 扫描交付同路径。
- **P2-8** check_env.py 改检测 + `--install` 授权安装，timeout 600→120；红线 #10 改"产出 docx 才强制"（C 路线纯文本豁免）。
- **P2-9** 路由 A 注明 evidence 必调理由；evidence-researcher 新增 `targeted_check` 定向核验模式。

### 回归守卫
- lint 新增守卫词：`首轮 pass，或 revise 后 closure pass`、`SECTION_OUTLINE`、`DRAFT_part`、`downstream_dispatch`、`depth_plan`、`direction_confirmed`、`门禁矩阵`、`路线裁剪`。
- test_leak_scan.py 新增 docProps 用例 + 负向断言误报用例。

## 0.6.3

对 0.6.2 终段顺序的**再次修正**：泄漏扫描应在卡④ 初稿确认**之前**执行，而非卡④ 与精排版之间。理由：交付给用户确认的初稿应当既有 QA 背书、又已确认无内部信息泄漏——扫描放在确认之后，用户确认的可能是带泄漏风险的稿子。

### 1. 终段顺序定稿
- 初稿 → 质量评审（full + closure）→ **泄漏扫描（0 hits）** → 卡④ 初稿确认（附 QA 结论摘要 + 扫描结果）→ 用户确认满意 → **精美 Word 精排版输出**（排后重扫不变）。
- 卡④ 标题改为"Writer 完成 DRAFT 并经完整 QA 全量 review + closure 与泄漏扫描之后"；内容新增泄漏扫描结果（0 hits）；交互改为确认后直接精排版、排后重扫。
- WORKFLOW_LOG 重排：第 11 行 Leak Scan、第 12 行确认卡④（QA 与泄漏扫描全过之后）、第 13 行精排。
- Phase 7 明确执行时机：QA closure 通过之后、卡④ 之前，0 hits 才交付确认。
- A 路线主流程、proposal-core 卡④、README 流程图同步更新。

### 2. 回归守卫
- `tests/cases/prompts.md` L10.8 终段顺序更新为"初稿 → 质量评审 → 泄漏扫描 → 卡④ 确认 → 确认后精排版"，倒置情形扩为"先确认再评审或扫描"。
- `TEST_PLAN.md` L10.8 判定点同步。
- lint 守卫沿用（卡④ 标题前缀不变，仍匹配）。

## 0.6.2

本版本是对 0.6.1 的两处流程精炼，来自一条流程反馈：① 课程专家与空间专家被当成"每个方案必跑"，但很多方案并不需要两者（纯空间建设如学生发展中心可能无课程，纯课程方案可能无空间）；② 终段顺序错了——当前是"先弹初稿确认卡、用户确认后再做质量评审"，应是"先完成质量评审，再交付初稿确认，确认后才出精排版 Word"。

### 1. 课程与空间专家改为按需调取（非必走）
- lead.md 主流程（A 路线）从 `(education-program-designer || space-planner)` 改为 `[课程/空间：按 DESIGN_BRIEF 决策，二者都做 / 只做其一 / 都不做，按需零~二调取]`。
- WORKFLOW_LOG 第 4 行（课程）、第 5 行（空间）标注"按需"，门禁列改为"按需"；表后注记明确：纯空间方案可不列第 4 行、纯课程方案可不列第 5 行，二者也可都不列，均不视为流程缺失。
- 新增提示：由 卡② 确认的 DESIGN_BRIEF 决定取哪些、取几个（可零、可一、可二）。纯空间建设方案（如学生发展中心空间建设）可不调 education-program-designer；纯课程方案可不调 space-planner。
- 卡② 门禁表述从"阻课程/空间/主笔"软化为"阻后续专业产出——课程/空间按需调取、主笔必走"。

### 2. 终段顺序修正：先评审、后确认、最后精排
- 原顺序：主笔 DRAFT → 卡④ 初稿确认 → 质量评审 → 精排。问题：用户先确认了才评审，等于确认没有评审背书。
- 新顺序：主笔 DRAFT → 质量评审（full + closure）→ **卡④ 初稿确认（QA 全过之后）** → 用户确认满意 → 泄漏扫描 → 精美 Word 精排版交付。
- 卡④ 定义改为"Writer 完成 DRAFT 并经完整 QA 全量 review + closure 之后"，明确"先完成质量评审，再交付初稿；不得把先确认再评审倒置"；内容新增 QA 结论摘要。
- WORKFLOW_LOG 重排：原 7.5 卡④ 移到 QA-Closure（第 10 行）之后为第 11 行，Leak Scan 为第 12 行，精排为第 13 行。
- SKILL.md 卡④ 与"四卡硬门禁"规则同步更新；README 流程图画为 QA 全过 → 卡④ → 精排。

### 3. 回归守卫
- `tests/lint.py`：lead.md 新增 `按需` 与 `卡④ 初稿确认卡（Writer 完成 DRAFT 并经完整 QA` 守卫；SKILL.md 新增 `按需` 守卫。
- `tests/cases/prompts.md` 新增 **L10.8**：纯空间建设方案不得强制调取 education-program-designer；且终段必须"先 QA 全量 review+closure，再弹卡④ 初稿确认，确认后才出精排版 Word"，不得倒置为"先确认再评审"。

## 0.6.1

本版本是对 0.6.0「需求澄清三段式」的**精炼修正**，回应一条关键反馈：之前把 M1-M7 当成"逐项必查的固定提问清单"，会导致需求分析专家机械地把"空间/课程/资料/参考"等维度逐条抛给用户，即便材料里已经说清也照问不误——这违背了"评估在前、提问在后"的本意。

### 1. M1-M7 从"必查清单"重定性为"候选评估维度"
- 删除"逐项必查，不得漏项"的硬性措辞；改为**评估清单**：intake 第一步对照 M1-M7 逐项判定 `satisfied / partial / missing`，并标注本单是否相关（`relevant`）。
- **只有 `missing` 且本单相关的维度才进入问题或 `material_request`；`satisfied` 的维度直接进 `can_confirm` 并注明依据，禁止再以任何形式追问。**
- 用户提到的"空间/课程/资料/参考"只是候选检查项，不是必问题目——已被材料充分回答的维度直接从问题清单消失。

### 2. 新增 `requirement_assessment` 评估字段（intake 输出合同，置于 `gap_analysis` 之前）
- 强制"先评估、再提问"：CLARIFY_PLAN 必须先给出 M1-M7 逐项评估结论，再从其中 `missing` 的项派生 `blocking` 问题与 `material_request`。
- 门禁新增：未对 M1-M7 全部维度给评估结论 → 未完成；某 `blocking` 问题指向的维度在评估里其实已 `satisfied` 却仍被提问 → 视为机械追问、违反"评估在前"，退回。

### 3. 需求分析专家双模式强化
- intake「目标」与「工作方法」新增硬步骤：在输出任何问题之前先逐维度评估；问题必须指向"这一单具体缺的那一点"，而不是泛泛问"请描述你的空间规划"。
- 资料清单输出改为"仅列 `missing`/`partial` 且本单相关项"，`satisfied` 项不进 `material_request`。
- MUST 新增：「不机械套用固定维度逐条追问」。

### 4. 总师 SOP / 共享铁律同步
- Phase 1.1 新增"评估在前"提示；CLARIFY_PLAN 门禁改为"含 `requirement_assessment`、且 `blocking` 必须对应评估里 `missing` 的维度、material_request 仅列真正缺失项"。
- Phase 1.2 清单先行 HTML 第④块改为"候选维度 M1-M7 逐项评估结论（已满足/部分/待补），仅待补项需提供资料"。
- proposal-core 新增"评估在前、提问在后"原则段落。

### 5. 回归守卫
- `tests/lint.py` V0.6.1 守卫：三份核心文件均须含 `requirement_assessment`（proposal-core 另须含"评估在前"）。
- `tests/cases/prompts.md` 新增 **L10.7 已提供充分资料时不得机械追问固定维度**（材料已含平面图+校本课程+办学规划+参考案例时，M1/M2/M3/M4 应判 satisfied，不得再逐条问"你的空间规划是什么/你的课程想法是什么"）。

## 0.6.0

本版本解决销售实测反馈的**核心跑偏问题**：确认卡①出现得太早——销售点了"确认"就继续跑，跑完才发现方向不是他想要的。根因不是销售不认真，而是卡①出现时连"空间是单室还是中心级""是校内建设还是上级申报""有没有平面图和参考方案"都还没问清，**卡上没有可判断方向的信息，用户的确认自然没有约束力**。

### 1. 需求澄清三段式（Phase 1，硬门禁）
把原来"读材料 → 出 PROJECT_BRIEF → 弹卡①"一步走完的流程，拆成四段：

| 段 | 执行者 | 产出 |
|---|---|---|
| 1.0 资料盘点 | 总师（扫描 `输入资料/` 与工作区，列清单请用户认领） | 已认领资料清单 |
| 1.1 intake | requirement-analyst（`mode=intake`） | `CLARIFY_PLAN` |
| 1.2 grill 澄清 | 总师（清单先行 HTML + `AskUserQuestion` 一次一问，上限 3 轮） | 澄清问答记录 |
| 1.3 final | requirement-analyst（`mode=final`） | `PROJECT_BRIEF` + `clarify_trace` |
| 1.5 卡① | 总师 | 需求与方向确认卡 |

### 2. 需求分析专家改为双模式
- `mode=intake`：**禁止**输出 PROJECT_BRIEF，只输出 `CLARIFY_PLAN`——含 `gap_analysis.blocking`（每项带可直接回答的问题 + 2-4 个候选答案）、`gap_analysis.non_blocking`（每项带假设 + 假设错了的后果）、`material_request`（M1-M7 标准资料清单，逐项三态）、`direction_options`（2-3 组方向候选）。
- `mode=final`：必须消化澄清记录并回填 `clarify_trace`（resolved / unresolved / direction_choices / materials_final_status / clarify_waived）；已澄清的不得重复追问，未关闭的 blocking 必须原样进 `must_confirm`。

### 3. 分级门禁（避免澄清变成卡流程）
- **blocking（方向性）**：学段、领域主线、空间范围、投入量级、目标读者、交付用途，申报/投标场景含评审口径 → 必须澄清；3 轮未收敛且用户未明确授权假设 → **停止推进**并列出后果。
- **non_blocking（细节性）**：平面图精确尺寸、设备型号、具体课时 → 记为假设 + 风险，进卡①风险区，不打扰用户。
- 用户明确"不用澄清直接跑" → 允许，记 `clarify_waived=true`，卡①顶部红色横幅逐条列出未确认方向并提示返工风险。
- 判定分界：**缺了会导致返工的是 blocking，缺了可后补的是 non_blocking**；不确定时按 blocking 处理。

### 4. 标准资料清单 M1-M7（逐项必查）
M1 平面图/CAD/实拍｜M2 现有课程资料｜M3 办学理念资料（章程/规划/校训解读/成果）｜M4 参考方案与心目中的样板｜M5 申报或招标文件（含评分表）｜M6 投入与建设边界｜M7 交付要求。每项标 `已提供 / 确实没有 / 待补`，说明支撑哪一段设计；用户说"确实没有"的不再反复索要。M1/M2/M3 缺失通常构成 blocking，M5 在申报/投标场景一律 blocking。

### 5. 资料投递双通道
- 约定入口目录 `<工作区>/输入资料/`（兼容 `输入材料/`、`01_输入资料/`、`materials/`）；
- 总师在 Phase 1.0 **主动扫描工作区**（深度 ≤3，识别 docx/pdf/xlsx/pptx/图片/dwg），列清单请用户认领，解决"放了但没说"；
- 新增红线 #12：**扫到的文件未经用户认领，不得作为设计依据**；
- `.dwg` 明确提示需转换或另附 PDF/图片，不假装能直接解析。

### 6. 卡① 升级为"需求与方向确认卡"
内容从"需求摘要回显"改为六块固定结构：状态横幅（未确认方向）→ 项目基本盘 → 分线核心需求 → **方向候选选题 2-3 组**（每个候选写清"选它意味着方案重心落在哪"）→ 资料清单三态表 → 假设与风险区。方向选题让销售在进入顶层设计前就能判断"是不是我想要的"，是本次修改的关键区块，不得省略。

### 7. 新增红线与门禁
- 红线 #11 **禁止跳过需求澄清**：未收到 CLARIFY_PLAN 就出卡①、收到后未做任何澄清交互就调 final、blocking 未关闭且未获授权就进调研 —— 均为违规；
- 红线 #12 **禁止把扫到的文件当已确认输入**；
- 交接门禁新增 `CLARIFY_PLAN` 校验项；`PROJECT_BRIEF` 门禁新增 `mode: final` + `clarify_trace` + unresolved 必须映射到 must_confirm；
- 交付前门禁新增"澄清三段式已完整执行"一条；
- WORKFLOW_LOG 新增 1.0/1.1/1.2/1.3 四行，**不得合并成一行"需求"**。

### 8. 路由与文档
- A/B 路线均前置澄清三段式；C 路线（单项任务）澄清可降级为总师 1 轮定向澄清，但设计类任务不可省略；
- proposal-core Skill 新增 MUST #0「先澄清，再定义需求；先定义需求，再出确认卡」与"卡片有效性原则"；
- `tests/lint.py` 新增 V0.6.0 回归守卫（CLARIFY_PLAN / clarify_trace / clarify_waived / 三段式等机制词不得丢失）。

## 0.5.0

本版本解决试用同事反馈的“流程不流畅”问题：未深度使用 WorkBuddy 的同事在跑方案时会在 Phase 7.5 才临时安装环境依赖，造成中途卡顿。新增「对话首步环境自检」，把依赖补齐前移到流程最前面。

### 1. 环境就绪自检（bin/check_env.py）
- 新增纯标准库、跨平台、幂等的 `bin/check_env.py`：检测运行解释器是否可 import `python-docx`，缺失则自动补齐（优先就地 `pip install`；Linux 系统 Python 的 externally-managed 场景改用隔离 venv；再失败降级 `--user`），并做最小 docx 功能回环验证。
- 输出机器可读的 `DOCX_PYTHON=<路径>` 与 `DOCX_READY=yes|no`，供总师解析；失败退出码 2 并给出人工处置方式，不静默放过。

### 2. 总师 SOP 前置预检（proposal-team-lead.md）
- 新增「🔧 预检 — 环境就绪自检」作为**每次对话首步、先于一切产出**的执行阶段；新增硬编码红线 #10「禁止跳过环境自检」。
- WORKFLOW_LOG 增加第 0 行（环境自检），交付前门禁增加“环境自检已通过、DOCX_PYTHON 已记录并用于 Phase 7.5”一条。

### 3. Phase 7.5 排版去临时安装（proposal-writing SKILL.md）
- 明排版所用解释器必须与预检回报的 `DOCX_PYTHON` 一致，**本步不再临时 `pip install`**；若预检未跑或 `DOCX_READY=no`，先回到总师执行预检。

### 4. 文档
- README 新增「安装后环境预检」小节与手动预检命令；版本升至 0.5.0。

## 0.4.0

本版本基于新环境完整实跑反馈，修复调研输出超限、确认卡提交失效、政策铺陈、扫描脚本缺失、详略失衡五类问题。

### 1. 调研输出体积控制（防 payload limit）
- evidence-researcher 与 research-evidence Skill 新增硬规则：单次写入/回传 ≤ 约 4000 字，超长按主题分片（`part: i/n`），最后单独回传短索引 + 完整 artifact_meta。
- Leader Phase 3 支持分片接收，派发时主动提醒成员遵守体积控制，不得要求一次性输出整份长文。

### 2. 确认卡收集机制修正（防“网页勾选了但没提交”）
- 明确 HTML 卡仅为审阅界面，网页内勾选/按钮不回传对话、一律无效。
- 确认动作改为：展示卡片后用 AskUserQuestion 在对话框内**逐题**弹出确认选项（一次一问，含「确认通过」「需要修改/补充」），逐题收齐后才记 approved。
- 卡面固定标注“本页仅用于审阅，请在对话框的问答选项中逐项确认”。

### 3. 成品规范：字体统一 + 政策筛选
- 精排版字体**全文统一微软雅黑**（标题加粗、正文常规，图题同字体），不再使用宋体/思源宋体。
- 政策筛选从“3-5 条”收紧为 **2-3 条最相关**；禁止把调研到的全部政策以“政策汇总表”铺陈进客户稿，未入选政策只留内部 Brief。
- proposal-qa P1 新增“政策汇总表全量铺陈”检查项。

### 4. 泄漏扫描脚本随 Skill 分发（防“脚本不存在”）
- `leak_scan.py` + `leak_terms.txt` 复制进 `skills/proposal-qa/scripts/`，脚本改为加载同目录词表，脱离对 `tests/` 的依赖。
- 所有引用（Leader Phase 7、proposal-qa §1、proposal-core MUST#12、quality-reviewer）统一改为：先解析专家目录绝对路径再调用，**禁止 CWD 相对路径 `tests/leak_scan.py`**。
- 新增硬规则：脚本缺失/损坏时报告阻塞，**禁止临时自写扫描脚本替代**。

### 5. 详略布局前置到大纲阶段
- top-design 五件套新增“详略主张”（哪些板块详写/简写）；DESIGN_BRIEF 门禁同步要求。
- proposal-writing：大纲必须为每章定 depth（detailed/standard/brief）+ 篇幅预算，核心差异化章详写、常规保障章简写，全篇均匀用力的大纲不通过；Section Card 增加 budget 字段并核对实际篇幅。
- 卡③ 必须展示各章详略等级与篇幅占比；QA P1 新增“详略严重失衡”。

## 0.3.0

本版本针对真实运行反馈，新增「四张用户确认卡（HTML 门禁）」「精美 Word 排版工序」，并修正 TeamCreate 工具误判问题。不与 0.2.1 的红线冲突。

### 1. TeamCreate 工具可用性修正
- 明确 TeamCreate 为**延迟工具（deferred tool）**，必须经 `ToolSearch` 取 schema 后用 `DeferExecuteTool` 调用，否则报 “not available”。
- Phase 0 协议重写为“ToolSearch → DeferExecuteTool”两步法，避免总师误以为该工具不存在而用任务清单替代团队。

### 2. 四张用户确认卡（HTML，强制门禁）
- 卡①需求分析卡（PROJECT_BRIEF）：列两线需求/基础/约束/待确认/可假设，用户可补充或确认，approved 前不进调研。
- 卡②顶层设计卡（DESIGN_BRIEF）：定位/双螺旋/成长·课程·空间逻辑/记忆点/客户表达边界，approved 前不进课程空间主笔。
- 卡③大纲卡（SECTION_OUTLINE）：一~三级标题结构与各章产出，approved 前不写正文。
- 卡④初稿卡（DRAFT）：预览+变更点+clientization 摘要，approved 后再走最终 QA 全量 review→closure→leak_scan→精排交付。
- 卡用自包含 HTML（内联 CSS、浅色、可打印），经 present_files 预览；内部 artifact_meta 不进卡；四卡为对应阶段的硬门禁。

### 3. 精美 Word 排版工序（Phase 7.5）
- leak_scan 通过后，内容稿须再经受控 python-docx 脚本产出**精排版** `.docx`，禁止裸草稿交付。
- 内置模板：客户交流版封面（无“内部资料/报价”字样）、微软雅黑标题+宋体正文（段首缩进 2 字符）、低饱和蓝绿配色+砖红/莫兰迪点缀、统一表格样式与斑马纹、图题样式、页眉页脚。
- 排版只改视觉不改文案，排后重跑 leak_scan 确认无新增泄漏；输出文件名带 `_精排版`。

### 4. 交付前门禁与 WORKFLOW_LOG
- 门禁新增“四张确认卡均 approved”“已产出精排版且重扫无泄漏”两条。
- WORKFLOW_LOG 模板增加 1.5/3.5/6.5/7.5/12 行，覆盖确认卡与精排阶段。

## 0.2.1

本版本基于真实 WorkBuddy 运行反馈，仅修复可审计协作、QA 闭环与内部信息泄漏三类问题，不扩展知识库或团队规模。

### 1. 可审计的专家调用
- 所有专业产物新增 `artifact_meta.producer / artifact / status`。
- Leader 必须校验 producer 与预期 Agent ID 一致；缺失/错配不得继续。
- Leader 每次真实派发后给用户 1 行 Agent ID 进度提示。
- WORKFLOW_LOG 增加 artifact 与 producer 校验信息。

### 2. QA Closure Review
- 首次 QA `result=revise` 后，必须由 proposal-writer 产出 `REVISED_DRAFT`。
- Writer 的“已修改”仅为自报，不具备放行资格。
- 必须再次调用 quality-reviewer 产出 `QA_CLOSURE_REPORT`。
- Closure 未通过则停止自动交付，默认不进入第三轮。

### 3. Clientization Guard
- requirement-analyst 新增 `clientization_guard.internal_only_terms`。
- 明确区分“信息真实”与“客户可见”。
- 对内部人名/称呼、会议来源、内部文件昵称、排期、分析标签统一标记 replace / omit / confirm。
- Writer 与 QA 必须接收该 guard；动态 raw term 任意泄漏均为 P0。

### 4. Leak Scanner
- `leak_scan.py` 新增 `--term` 动态 literal term 与 `--terms` 附加正则词表。
- DOCX 扫描范围扩展到正文、页眉、页脚、脚注、尾注、批注。
- 支持 stdin。
- 文件损坏/解析失败返回 exit 2 并 BLOCK DELIVERY，不再误判 clean。
- 通用词表新增“乔老师课程 / 方书记明确提出 / 按王总要求”等模式。
- 新增 `tests/test_leak_scan.py` 6 个自动回归用例。

### 5. 已验证
- `python3 tests/lint.py`：通过。
- `python3 tests/test_leak_scan.py`：6/6 通过。
- 旧版漏检样例 `乔老师课程 / 方书记明确提出 / 按王总要求`：现均可命中。
- DOCX 页眉 `内部资料`：现可命中 `word/header1.xml`。

仍需在用户本机 WorkBuddy 中验证真实子 Agent UI 调度与 Closure Review 是否按预期发生。
