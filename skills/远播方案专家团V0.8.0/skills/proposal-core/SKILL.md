---
name: proposal-core
description: "Shared execution contract for the Yuanbo K12 Proposal Team: routing, artifacts, confirmation gates, clientization, factuality and delivery rules."
---

# Proposal Core · 共享执行合同

本 Skill 是全团的单一事实源。Agent MD 只补充角色职责，不重复改写本文件的门禁。

## 执行优先级

1. 用户明确要求与任务边界；
2. 本文件的路线矩阵、Artifact 合同和安全门禁；
3. 角色 Agent 的工作方法；
4. 示例与历史说明。

出现冲突时：保留安全门禁，停止推进，向 Leader 报告冲突位置；不得自行猜测。

## 全团不变量

- 不虚构学校、政策、合作、设备参数、价格、赛事或成效；语气必须匹配证据。
- 方案必须学校专属、能落到课程/服务、空间或运行机制；不从模板直接扩写。
- `事实可信 ≠ 客户可见`：内部人名、昵称、会议来源、排期、销售/领导指令和分析标签必须经过 `clientization_guard`。
- 正式方案必须是完整正文，不得用标题、表格或 bullet 堆成大纲。
- Writer 不自我放行；QA 首轮 `pass` 直接放行，首轮 `revise` 必须 Writer 返修后再做 QA `closure`。
- 客户可见产物必须通过语义 clientization 检查和专家包内 `leak_scan.py`，任一失败都阻断交付。

## Artifact 合同

所有专业成员返回：

```yaml
artifact_meta:
  producer: <Agent ID>
  artifact: <CLARIFY_PLAN|PROJECT_BRIEF|EVIDENCE_BRIEF|DESIGN_BRIEF|PROGRAM_PLAN|SPACE_PLAN|SECTION_OUTLINE|DRAFT|REVISED_DRAFT|QA_REPORT|QA_CLOSURE_REPORT>
  status: complete
```

Leader 只采信 producer、artifact、status 均匹配的产物；缺失、错配或超出职责即退回。Leader 不补写元数据冒充成员调用。

## 路线与规模矩阵

门禁按路线裁剪；规模只改变允许的轻量化步骤，不得删除事实、客户化、QA 或扫描安全门禁。

| 路线 | 适用 | 必要门禁/产出 |
|---|---|---|
| A-single_space | 单室级小方案 | 澄清最多 1 轮；证据可不调或用 `targeted_check`；卡②+卡③合并为一张“设计+大纲卡”，但必须分别记录 `design_approved` 与 `outline_approved`；卡④、QA、扫描仍执行，交付 DOCX 才精排 |
| A-multi_space | 多空间/集群方案 | A 标准流程；卡①②③④、producer 校验、QA、扫描、精排（如交付 DOCX） |
| A-center_level | 中心级/综合建设 | A 全量流程；证据 `full`，四卡完整执行 |
| B | 优化已有成熟方案 | 卡①；Writer→QA full→必要 closure→扫描→精排；卡②③④不适用 |
| C-single | 单项、单 Agent 可完成 | 不建团队；1 轮定向澄清；只取该任务最小 Artifact；客户可见内容仍须 clientization/扫描 |
| C-multi | 单项但需多个 Agent | 先 TeamCreate，再按最小集派发；其余同 C-single |

`project_scale` 只能取 `single_space | multi_space | center_level`。未明确规模时按 `multi_space` 处理并记录假设，不得临场选择最省流程的档位。

## 需求澄清三段式与确认卡

A/B 必须执行：

`资料盘点 → intake(CLARIFY_PLAN) → grill → final(PROJECT_BRIEF) → 卡①`

- `M1-M7` 是评估维度，不是固定问题清单；先判 `satisfied/partial/missing`，只追问相关且真正缺失项。
- 评估在前、提问在后：已满足维度直接进入 `can_confirm`，不得机械追问。
- `blocking` 未关闭且未获用户授权假设，不得调研或出设计；最多 3 轮，single_space 最多 1 轮。
- 卡①至少展示方向候选、资料三态、假设风险；用户选择必须落入 `clarify_trace.direction_choices` 或 WORKFLOW_LOG 的 `direction_confirmed: Dx`。
- 卡用自包含 HTML（内联 CSS、可打印），经 `present_files` 预览；用户确认前只展示卡，不把 HTML 勾选当提交；必须用 `AskUserQuestion` 逐题收集，全部通过才记 `approved`。
- `clarify_waived` 唯一落点是 `clarify_trace.clarify_waived`。

卡②来源为 `DESIGN_BRIEF`，必须包含 `downstream_dispatch`、`depth_plan`；卡③来源为 `SECTION_OUTLINE`，必须含章节 `depth`、`budget_ratio`、`draft_part_plan`。single_space 合并卡仍须同时满足两份合同并分别记录两项 approval。

## 调度与交接

- 成员不互相直连；Leader 只转发下游需要的 Brief。
- 派发 evidence/top-design 时附卡①已确认的 `direction_confirmed: Dx` 及要点。
- `downstream_dispatch` 决定课程/空间取零、一或二；缺字段退回，不靠 Leader 猜测。
- 课程/空间按需调取，非每个方案必走。
- 长产物按主题/章节分片，每片 ≤4000 字；末尾短索引才放完整 `artifact_meta`。

## 客户化与交付

`PROJECT_BRIEF.clientization_guard.internal_only_terms[].raw` 必须进入最终动态扫描。`replace` 只有正式名称有来源才可用；`omit` 只保留建设诉求；`confirm` 未确认前不得外显。

交付 DOCX：先由 `bin/check_env.py` 检查并记录 `DOCX_PYTHON`，产物固定放 `<工作区>/output/proposal/`；内容稿 QA+扫描通过后才出卡④，用户确认后用该解释器精排，精排后再次扫描。扫描固定调用：

`<专家目录>/skills/proposal-qa/scripts/leak_scan.py`

禁止使用 CWD 下的 `tests/leak_scan.py` 或临时自写脚本替代。

## WORKFLOW_LOG 最小字段

记录：`route`、`project_scale`、`step/phase`、实际 Agent ID、artifact、producer/status、门禁结果、用户 approval、扫描路径与结果。只列实际执行步骤；未执行的按路线记 `N/A`，不伪造调用。
