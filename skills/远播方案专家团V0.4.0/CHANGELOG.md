# Changelog

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
