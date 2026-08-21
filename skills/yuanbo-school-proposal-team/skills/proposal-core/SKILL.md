---
name: proposal-core
description: "Core rules shared by the Yuanbo K12 School Proposal Expert Team. Keeps proposals factual, school-specific, complete, client-facing, auditable and lightweight."
---

# Proposal Core · 核心铁律

本 Skill 只服务 **K12 学校特色育人空间/项目建设方案**，重点初高中。首期业务域为科创/科学教育与生涯/心理/学生发展。

## MUST
1. **先理解项目，再设计。** 不从通用模板直接扩写，不默认固定章节、三级课程或统一空间模型。
2. **关键事实不得虚构。** 学校基础、政策、合作、赛事、设备型号/参数/价格、比较性结论等必须有依据；无法核实时标记为待确认、建议或目标。
3. **语言强度不得超过证据。** 事实、判断、建议、建设目标、预期成效必须使用匹配语气。
4. **政策必须解释。** 进入方案的政策应回答“政策信号 → 对学校意味着什么 → 对本项目设计意味着什么”，不得只罗列文件。
5. **顶层设计必须有学校专属性并能落地。** 概念、结构、主线应映射课程、服务、空间或运行机制。
6. **事实可信 ≠ 客户可见。** 用户提供的信息可以是真实的，但人名、内部称呼、会议来源、内部文件名、排期、销售/领导指令等仍可能不适合出现在客户稿；必须通过 clientization_guard 单独判断。
7. **内部信息零容忍。** internal_only_terms 的 raw 原词、内部分析标签、内部沟通来源、内部昵称、内部排期等不得进入客户交付物。
8. **内容形式服从信息关系。** 横向比较优先表格；原因、判断、理念优先自然段；步骤/任务/规则优先列表。
9. **正式方案必须完整。** 不允许大量“标题 + 一句话 + 三个 bullet”的大纲式输出代替正文。
10. **必须 Senior Editing。** 删除空话、重复、机械排比/对仗、无信息增量升华和明显 AI 模式，但保留有价值的高级表达。
11. **必须独立 QA。** 作者不得自我放行；QA 提出 P0/P1 后，修订稿必须由 QA closure review 独立确认关闭。
12. **交付前必须双重泄漏检查。** 语义检查 clientization_guard + 机器扫描 `skills/proposal-qa/scripts/leak_scan.py`（专家包内绝对路径调用，禁止 CWD 相对路径，禁止自写脚本替代）；任一失败均不得交付。

## 标准 Artifact 元数据
专业成员的内部交接产物统一包含：
```yaml
artifact_meta:
  producer: <Agent ID>
  artifact: <PROJECT_BRIEF|EVIDENCE_BRIEF|DESIGN_BRIEF|PROGRAM_PLAN|SPACE_PLAN|DRAFT|REVISED_DRAFT|QA_REPORT|QA_CLOSURE_REPORT>
  status: complete
```
Leader 只采信 producer 与预期成员一致的产物；不得自行补写 producer 冒充成员调用。

## 用户确认卡（HTML 门禁）
专业产物→下一阶段之间，Leader 必须产出 HTML 确认卡并等用户 `approved`：
- **卡①需求分析卡**（PROJECT_BRIEF）：学校/学段/对象、两线需求、基础、约束、must_confirm、can_assume；用户可补充/修正/确认。
- **卡②顶层设计卡**（DESIGN_BRIEF）：定位、双螺旋结构、成长/课程/空间逻辑、记忆点、client 边界。
- **卡③大纲卡**（SECTION_OUTLINE）：一~三级标题、各章主题与产出、篇幅。
- **卡④初稿卡**（DRAFT）：预览+变更点+clientization 摘要。

规则：卡用自包含 HTML（内联 CSS、浅色主题、可打印），经 `present_files` 预览；内部 artifact_meta **不得写入卡**；四卡分别为 调研/课程空间主笔/正文撰写/最终交付 的硬门禁。未 approved 不得放行。

**确认收集（硬规则）**：HTML 卡仅作审阅界面，网页内勾选/按钮不会回传对话，一律无效。展示卡片后必须用 AskUserQuestion 在对话框内**逐题**弹出确认选项（一次一问，选项含「确认通过」「需要修改/补充」），逐题收齐「确认通过」后才记 `user_status=approved`。卡面须固定标注：“本页仅用于审阅，网页内勾选不会提交；请在对话框的问答选项中逐项确认。”

## Clientization Guard
PROJECT_BRIEF 应包含：
```yaml
clientization_guard:
  internal_only_terms:
    - raw:
      type:
      action: replace | omit | confirm
      client_safe_name:
      reason:
  client_visible_names: []
```
规则：
- `replace`：只有 client_safe_name 有明确来源时才能替换；
- `omit`：删除内部来源痕迹，只保留背后的建设诉求；
- `confirm`：用户未确认前禁止外显；
- 所有 `raw` 项必须进入最终动态泄漏检查。

## 事实语气速记
- 已核实事实：可直接陈述，并保留来源线索。
- 用户提供未独立核实：必要时写“据学校提供资料”。
- 分析判断：使用“据此判断、主要体现在、可理解为”等有边界表达。
- 方案动作：使用“拟、建议、计划”。
- 目标：写明建设方向/范围，不把未来写成既成事实。
- 预期成效：使用“预期、预计、有望”，不承诺不可控结果。

## 商务分寸
对成熟学校，默认立场是“基于已有基础进一步深化、形成协同、补齐载体、扩大覆盖”，而不是暗示学校“现在不够好”。
