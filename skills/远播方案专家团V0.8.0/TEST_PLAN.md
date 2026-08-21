# 远播学校建设方案专家团 · 测试计划（当前版本 0.8.0）

> 演进史（0.2.1 起的历次修复目标）见文末附录；本计划主体随版本持续更新。

## 1. 本轮修复目标
V0.8.0 将 0.7.1 的提示词执行层收敛成果正式定版：共享规则单一事实源、总师/成员提示词预算、A 三种规模与 C 两种 TeamCreate 形态、single_space 合并卡双 approval、Windows UTF-8 输出，并规范化打包根目录名。0.7.0 的门禁、Artifact 合同、DRAFT 分片、docProps 扫描和授权安装必须继续通过。详见 CHANGELOG 0.8.0。

## 2. L0 工程检查
```bash
python3 tests/lint.py
python3 tests/test_leak_scan.py
```
然后在实际 WorkBuddy 环境运行官方 validator。L0 不能替代真实 runtime 测试。

## 3. L1-L8 原有行为测试
继续使用 `tests/cases/prompts.md`：动态路由、需求、调研、顶层、课程空间、正文完整度、QA 故障注入、端到端多模型稳定性。

## 4. L9 V0.2.1 强制门禁
### L9.1 真实 Agent 调用
完整新方案的 WorkBuddy UI/执行记录应真实出现所需 Agent ID。WORKFLOW_LOG 只是审计摘要，不可替代平台调用证据。

### L9.2 Artifact Producer Gate
每个专业产物必须有：
```yaml
artifact_meta:
  producer: <expected Agent ID>
  artifact: <expected artifact>
  status: complete
```
缺失/错配必须退回成员，不得由 Leader 补写。

### L9.3 Clientization Guard
材料含“回应书记诉求 / 乔老师课程 / 按王总要求”等内部表达时，PROJECT_BRIEF 必须提取到 `clientization_guard.internal_only_terms`；Writer 与 QA 必须收到该字段；最终稿 raw 原词 0 出现。

### L9.4 QA Closure
故意让首次 QA 返回 revise。必须看到：
`quality-reviewer(full) → proposal-writer(REVISED_DRAFT) → quality-reviewer(closure)`。
只有 Closure result=pass 才可交付。Closure 再失败时应停止并报告阻塞项，不无限循环。

### L9.5 Leak Scanner
必须通过：
- 通用词：`乔老师课程` 可命中；
- 动态词：`--term "火种计划"` 可命中；
- DOCX 页眉 `内部资料` 可命中；
- 损坏 DOCX 返回错误并 BLOCK DELIVERY；
- 干净文本返回 0。

自动回归：
```bash
python3 tests/test_leak_scan.py
```

## 4.5 L10 V0.6.0 需求澄清三段式门禁

用例明细见 `tests/cases/prompts.md` § L10。核心判定点：

| # | 场景 | 必过条件 |
|---|---|---|
| L10.1 | 仅一句话需求 | 执行顺序为 资料盘点 → intake(CLARIFY_PLAN) → grill → final → 卡①；**不得**直接出 PROJECT_BRIEF 或直接弹卡① |
| L10.2 | 材料齐但交付用途不明 | 交付用途判 blocking 并追问；细节缺口判 non_blocking 给假设+风险 |
| L10.3 | 用户要求跳过澄清 | 允许，但 `clarify_waived=true` 且卡①顶部醒目横幅列出未确认方向 |
| L10.4 | 三轮仍未收敛 | 停止推进并列出后果，不得自行假设进调研 |
| L10.5 | 资料放 `输入资料/` 未告知 | 主动扫描并列清单请用户认领；未认领不得作为依据（红线 #12） |
| L10.6 | 澄清结果回填 | `clarify_trace.resolved` 逐条记录；已答项不得重复进 must_confirm；unresolved 必须映射到 must_confirm |
| L10.7 | 已提供充分资料时不得机械追问固定维度 | M1-M4 在 `requirement_assessment` 中判 satisfied、进 can_confirm，不得再逐条问"空间规划/课程想法/参考方案" |
| L10.8 | 课程/空间按需 + 终段顺序 | 纯空间方案不强制调课程专家、纯课程方案不强制调空间专家；终段须 初稿→QA 闭环（首轮 pass 或 revise 后 closure pass）→泄漏扫描→卡④确认→确认后精排版 Word，不得“先确认再评审/扫描” |
| L10.9 | 规模分级（single_space 轻量档） | project_scale=single_space 时澄清 1 轮、卡②③合并、evidence 降为按需/targeted_check；不得走 center_level 全流程 |
| L10.10 | 提示词执行预算与路线矩阵 | 总师提示词 ≤8000 字符、需求分析提示词 ≤7000 字符；`A-single_space/A-multi_space/A-center_level/C-single/C-multi` 定义完整；合并卡同时记录 `design_approved` 与 `outline_approved` |

结构回归（机检）：`python3 tests/lint.py` 必须通过 V0.6.0 机制词守卫（CLARIFY_PLAN / mode: intake / mode: final / clarify_trace / clarify_waived / 需求澄清三段式）。

## 5. 首批真实回归顺序
0. **仅一句话需求（L10.1）**：验证澄清三段式不被跳过 —— 这是 0.6.0 的核心回归项，优先跑；
1. 已有成熟方案优化：验证 requirement → writer → QA full → 必要 closure；
2. 单主题科创完整链路；
3. 多空间实验室集群；
4. 学生发展中心；
5. 同一输入至少在 2-3 个模型/环境重复。

## 6. 通过标准
- WorkBuddy UI 能看到真实成员调用，而非 Leader 独写；
- 必需 artifact producer 100% 正确；
- 首次 QA 若 revise，Closure Review 执行率 100%；
- P0/P1 未关闭时交付率 0；
- clientization_guard 动态内部词泄漏 = 0；
- DOCX 正文/页眉/页脚等通用泄漏 = 0；
- 高风险虚构事实 = 0；
- 强制需求遗漏 = 0；
- **澄清三段式跳过率 = 0**（未收到 CLARIFY_PLAN 就出卡① / 未做澄清交互就调 final / blocking 未关闭且未授权就进调研，任一发生即失败）；
- **卡① 方向候选选题缺失率 = 0**；
- 大纲化失败率目标 < 5%（积累足够样本后统计）。
- 提示词预算超限率 = 0；共享规则变化先改 `proposal-core`，不在多个 Agent MD 复制新版本。

## 7. 回归原则
- 优先修稳定复现的问题；
- 修复放在最相关专家/Skill，不复制到所有成员；
- 默认维持 1+7；
- 本轮门禁稳定前不扩展知识库。

## 附录：历史版本修复目标
- **V0.2.1**：① 专家调用可审计（producer 证明）；② QA revise 后独立 Closure Review，Writer 不自我放行；③ 内部信息从固定黑名单升级为动态 clientization_guard + 通用/动态机器扫描，并补 DOCX 页眉页脚等扫描区域。
- **V0.6.0**：需求澄清三段式（intake→grill→final）硬门禁，卡①改为方向锁定。
- **V0.6.1**：评估在前、提问在后（M1-M7 候选评估维度，非必问题目）。
- **V0.6.2**：课程/空间按需调取；终段顺序改为评审前置（先 QA 后确认再精排）。
- **V0.6.3**：泄漏扫描前置到卡④之前。
