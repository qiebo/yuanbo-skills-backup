# 远播学校建设方案专家团 · V0.2.1 测试计划

## 1. 本轮修复目标
V0.2.1 只修三类已在真实 WorkBuddy 测试中暴露的结构问题：
1. 专家调用必须可审计，成员产物需带 producer 证明；
2. QA revise 后必须独立 Closure Review，Writer 不能自我放行；
3. 内部信息从固定黑名单升级为“PROJECT_BRIEF 动态 clientization_guard + 通用/动态机器扫描”，并补 DOCX 页眉页脚等扫描区域。

暂不增加历史方案知识库/RAG、新专家或复杂 Word 流水线。

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

## 5. 首批真实回归顺序
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
- 大纲化失败率目标 < 5%（积累足够样本后统计）。

## 7. 回归原则
- 优先修稳定复现的问题；
- 修复放在最相关专家/Skill，不复制到所有成员；
- 默认维持 1+7；
- 本轮门禁稳定前不扩展知识库。
