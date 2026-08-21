# 远播方案专家团

**版本：0.8.0（提示词执行层收敛 + 打包规范化）**

面向 K12 学校、重点服务初中和高中场景的 WorkBuddy Team 型专家团。当前只处理一种主文类：**学校特色育人空间/项目建设方案**，首期覆盖科创/科学教育/工程实践，以及生涯/心理/学生发展。

## 0.8.0 提示词执行层

本版本不改变 0.7.0 的核心门禁和产物合同，只收敛执行表达：

- `proposal-core/SKILL.md` 是路线、规模、卡片、交接和交付规则的单一事实源；Agent 提示词只保留“何时做、收到什么、返回什么、何时停止”。
- 总师提示词采用短状态机；成员提示词采用“边界 → 输入 → 工作顺序 → 输出合同 → 放行检查”，减少长篇解释和重复规则。
- `single_space` 仍执行 QA、扫描和卡④；只压缩澄清、证据和卡②/③界面。合并卡必须分别取得 `design_approved`、`outline_approved`。
- `C-single` 不创建团队，`C-multi` 才创建团队；客户可见文本和 DOCX 无论路线都必须做客户化与扫描。

## 演进史（历史版本细节见 CHANGELOG）

早期 V0.2.1 修了三个真实问题：① 专家调用不可验证 → `artifact_meta.producer` 审计；② QA 返修缺独立复审 → 强制 closure review；③ 内部称呼泄漏 → 动态 `clientization_guard` + `leak_scan.py`（正文/页眉/页脚/脚注/尾注/批注）。

## 团队
| Agent | 角色 | 核心产出 |
|---|---|---|
| proposal-team-lead | 方案总师 | 路由、调度、门禁、最终汇总 |
| requirement-analyst | 需求分析专家 | CLARIFY_PLAN（intake）→ PROJECT_BRIEF + clientization_guard（final） |
| evidence-researcher | 信息研究专家 | EVIDENCE_BRIEF |
| top-design-architect | 顶层设计专家 | DESIGN_BRIEF |
| education-program-designer | 课程与育人体系专家 | PROGRAM_PLAN（按需调取） |
| space-planner | 空间规划专家 | SPACE_PLAN（按需调取） |
| proposal-writer | 资深方案主笔 | DRAFT / REVISED_DRAFT |
| quality-reviewer | 方案质量评审专家 | QA_REPORT / QA_CLOSURE_REPORT |

## V0.6.0 需求澄清三段式（本轮重点）

**问题**：销售反馈"弹出需求确认卡后点了确认就继续跑，跑完发现很多不是我想要的"。
**根因**：卡①出现得太早。那时连"空间是单室还是中心级""是校内建设还是上级申报""有没有平面图和参考方案"都还没问清——**卡上没有可判断方向的信息，确认自然没有约束力**。

**新流程**：
```text
1.0 资料盘点     总师扫描 输入资料/ 与工作区 → 列清单请用户认领
     ↓
1.1 intake       requirement-analyst(mode=intake) → CLARIFY_PLAN
                 · blocking 缺口（带可直接回答的问题 + 候选答案）
                 · non_blocking 缺口（带假设 + 假设错了的后果）
                 · M1-M7 资料清单（逐项三态）
                 · 2-3 组方向候选选题
     ↓
1.2 grill 澄清   总师：先出「信息与资料清单」HTML（可批量回复）
                 再用 AskUserQuestion 一次一问追问 blocking，上限 3 轮
     ↓
1.3 final        requirement-analyst(mode=final) → PROJECT_BRIEF + clarify_trace
     ↓
1.5 卡①         需求与方向确认卡（六块：状态横幅/基本盘/分线需求/方向选题/资料三态/假设风险）
```

**分级门禁**：方向性缺口（学段、领域主线、空间范围、投入量级、目标读者、交付用途）必须澄清，3 轮未收敛且用户未授权假设 → 停止推进；细节性缺口记为假设 + 风险继续跑。用户可明确要求跳过澄清（记 `clarify_waived=true`），但卡①顶部会红色横幅列出全部未确认方向与返工风险。

**资料投递两种方式**：对话框直接上传/粘贴，或放进 `<工作区>/输入资料/` 后告知一声（总师也会主动扫描工作区并请你认领，防止"放了但没说"）。

## 完整新方案流程
```text
TeamCreate
  ↓
资料盘点 → requirement-analyst(intake) → grill澄清 → requirement-analyst(final)
  ↓                                                    ↓
  └────────────── 卡① 需求与方向确认 ←─────────────────┘
  ↓
evidence-researcher
  ↓
top-design-architect → 卡② 顶层设计确认
  ↓
课程专家（按需） ─┐
                  ├→（零 / 一 / 二者均可，按 DESIGN_BRIEF 决策）
空间专家（按需） ─┘
  ↓
proposal-writer → 卡③ 大纲确认
  ↓
DRAFT → quality-reviewer(full)
                 │
            pass │
                 ↓
          quality-reviewer(closure)
                 │
            pass │
                 ↓
          leak_scan（0 hits）
                 ↓
          卡④ 初稿确认（QA 与泄漏扫描全过后再交付确认）
                 ↓（用户确认满意）
          精美 Word 精排版输出
```

> **三点精炼（v0.6.2~v0.7.0）**
> 1. **课程与空间按需调取**：不是每个方案都跑这两个专家。纯空间建设（如学生发展中心空间）可能无课程，可不调课程专家；纯课程方案可能无空间建设，可不调空间专家。取哪些、取几个由 卡② 确认的 DESIGN_BRIEF 的 `downstream_dispatch` 决定（可零、可一、可二）。
> 2. **终段顺序（v0.6.3 定稿）**：初稿完成后**先完成 QA 闭环（首轮 pass，或 revise 后 closure pass）与泄漏扫描（0 hits）**，再交付初稿确认（卡④，附 QA 结论与扫描结果）；用户确认满意后，直接输出**精美 Word 精排版**（排后重扫）。不再"先确认再评审"。
> 3. **v0.7.0 一致性收敛**：交付前门禁改为按路线裁剪的门禁矩阵（A 全量 / B 卡①+QA闭环+扫描+精排版 / C 最小集）；A 路线规模分级（`single_space` 轻量档）；主笔 DRAFT 按章分片（≤4000 字）；泄漏扫描新增 docProps 文档属性；环境预检改为检测 + 授权安装。

## Clientization Guard
“信息真实”与“适合客户看到”分开判断。比如：
- `回应书记诉求`：保留“加强生涯与学科融合”的建设要求，删除内部沟通来源；
- `乔老师课程`：有正式名用正式名，无正式名用中性功能名称并待确认；
- `按王总要求新增展示区`：正文写展示区的项目价值，不写来源是谁。

这些 raw 原词会进入最终动态泄漏扫描。

## 本地自检
```bash
python3 tests/lint.py
python3 tests/test_leak_scan.py
```

动态扫描示例（正式运行时使用 `skills/` 下的脚本）：
```bash
python3 skills/proposal-qa/scripts/leak_scan.py \
  --term "乔老师课程" \
  --term "方书记明确提出" \
  final.docx
```

`tests/` 下另有同名脚本与测试用例，供回归测试使用；交付门禁固定调用 `skills/proposal-qa/scripts/leak_scan.py`。

## 安装后环境预检（消除流程中途装包卡顿）

首次把专家团交给未深度使用 WorkBuddy 的同事时，最易在 Phase 7.5「精美 Word 精排版」才临时安装 `python-docx` 而卡顿。本版本在**对话首步由总师预检环境**（见 `agents/proposal-team-lead.md` 的「🔧 预检 — 环境就绪自检」）。

如需安装后手动先跑一遍（推荐），执行：

```bash
EXPERT_DIR="$HOME/.workbuddy/plugins/marketplaces/my-experts/plugins/yuanbo-school-proposal-team"
python3 "$EXPERT_DIR/bin/check_env.py"            # 只检测、不安装
python3 "$EXPERT_DIR/bin/check_env.py" --install  # 征得用户同意后授权安装
```

期望输出含 `DOCX_READY=yes`。脚本纯标准库、跨平台、幂等；默认只检测缺失、不擅自安装（受限网络/企业 IT 环境友好），加 `--install` 才自动补齐（优先就地安装，Linux externally-managed 场景装入隔离 venv），失败打印人工处置方式并阻断，不会静默放过。

## WorkBuddy 安装/校验
沿用你当前已能运行的 V0.2 安装方式。本补丁没有更改 Expert Team 的 1+7 架构和插件目录结构，避免引入与当前本机 WorkBuddy 的兼容性变量。安装后仍应运行本机 `validate_expert.py`，并以实际 UI 的子 Agent 调用记录验证“专家团真的工作了”。

## 本轮不做
- 历史方案知识库 / RAG；
- 新增专家；
- 复杂预算/Word/PDF流水线；
- 无限 QA 循环。

## 版本
- 0.1.0：1+7 静态专家团候选版。
- 0.2.0：增加 TeamCreate、WORKFLOW_LOG、QA 和固定泄漏词门禁。
- 0.2.1：增加 Artifact Producer Gate、动态 Clientization Guard、QA Closure Review、DOCX 全区域/动态词泄漏扫描和回归测试。
- 0.3.x：增加四张用户确认卡（需求/顶层/大纲/初稿）作为硬门禁，HTML 卡 + 对话内逐项确认。
- 0.4.0：固化完整交付流水线——四张确认卡门禁、QA 最多两轮闭环、通用词表 + 动态 internal_only 词泄漏扫描、精美 Word 精排版（Phase 7.5）与排后重扫；分发包去除本机个人路径，改为跨平台通用写法。
- 0.5.0：对话首步环境自检（`bin/check_env.py`），消除 Phase 7.5 临时装包卡顿。
- **0.6.0：需求澄清三段式硬门禁——资料盘点 → intake(CLARIFY_PLAN) → grill 澄清（一次一问，上限 3 轮）→ final(PROJECT_BRIEF + clarify_trace) → 卡①；M1-M7 标准资料清单三态管理；卡① 升级为"需求与方向确认卡"含方向候选选题；新增红线 #11 禁止跳过澄清、#12 禁止把扫到的文件当已确认输入。**
- **0.6.1：澄清门禁精炼——M1-M7 从"逐项必查固定清单"重定为"候选评估维度"，新增 `requirement_assessment` 评估字段（先评估、再提问）；仅 `missing` 且本单相关的维度才进入问题与资料请求，材料已说清的维度（satisfied）不再追问，杜绝机械套问固定维度。**
- **0.6.2：流程精炼——① 课程与空间专家改为按需调取（纯空间建设方案可不调课程专家、纯课程方案可不调空间专家，取哪些/几个由 DESIGN_BRIEF 决定）；② 终段顺序修正为「初稿 → 质量评审 full+closure → 交付初稿确认卡④ → 用户确认满意 → 泄漏扫描 → 精美 Word 精排版」，不再"先确认再评审"。**
- **0.6.3：终段顺序再修正——泄漏扫描移到卡④ 初稿确认之前（QA closure 通过后执行、0 hits 才交付确认）；用户确认满意后直接输出精排版 Word（排后重扫不变）。终段定稿：初稿 → 质量评审 → 泄漏扫描 → 卡④ 确认 → 精排版 Word。**
- **0.7.0：一致性债收敛——交付前门禁改为按路线裁剪的门禁矩阵（P0-1）；合同字段补齐（SECTION_OUTLINE 输出合同、DESIGN_BRIEF 增 downstream_dispatch/depth_plan、卡① direction_confirmed 回落）；closure 表述统一；总师 MD 瘦身 <14k；主笔 DRAFT 按章分片协议；A 路线规模分级（single_space 轻量档）；lint 跨文件一致性断言；leak_scan 覆盖 docProps 文档属性；check_env 改检测+授权安装；TEST_PLAN/README 版本头清理。**
- **0.7.1：提示词执行层收敛——共享规则集中到 proposal-core；总师/需求/调研/顶层/主笔/QA 提示词精简；明确 A 三种规模与 C 两种 TeamCreate 形态；single_space 合并卡保留双 approval；lint 增加提示词预算；扫描与环境预检增加 Windows UTF-8 输出适配。**
- **0.8.0：0.7.1 提示词执行层收敛成果正式定版为大版本；打包根目录名规范化为 name（不带版本后缀），确保覆盖安装时目录名与 name 一致。**
