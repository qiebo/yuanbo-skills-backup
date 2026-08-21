---
name: proposal-qa
description: "Quality gate for K12 school construction proposals. Supports full review and closure review; detects dynamic clientization leaks, facts, requirements, top-design consistency, outline-like output, content-form issues and AI-style behavior."
---

# Proposal QA · 质量门禁

QA 的目标是判断“能不能交付、为什么不能”，不是把整份方案重新写一遍。

## 0. Clientization / 内部信息泄漏（P0，零容忍）
这是第一关。检查两类词：

### A. 项目动态词（优先级最高）
来自 `PROJECT_BRIEF.clientization_guard.internal_only_terms[].raw`。**任何一个 raw 原词出现在客户稿中 = P0。**
固定词表没有命中，也不能放行。

### B. 通用内部模式
- 内部人名/代号：X老师课程、X总方案、书记/领导沟通指向等；
- 内部会议/沟通：回应书记诉求、按X总要求、销售反馈、客户说要等；
- 内部排期/试点/商务动作；
- 内部分析标签：校训转译、痛点分析、销售抓手、客户需求分析；
- 内部资料、内部口径、旧版/初稿等不应出现在正式稿的来源标记。

### 客户化修法
- 内部昵称 → 正式名称（有依据时）或功能性中性名称；
- 内部沟通来源 → 删除“谁提出”，直接表达建设目标/设计理由；
- 内部排期 → 若确需写实施计划，改为经确认的项目建设时间，而非公司内部动作；
- 内部分析标签 → 仅保留结论，不展示分析工具名。

## 1. 机器复核

### 脚本位置（硬规则，防"脚本不存在"）
扫描脚本随本 Skill 分发，固定位于**专家包内**：
`<专家目录>/skills/proposal-qa/scripts/leak_scan.py`（默认词表 `leak_terms.txt` 在同目录，脚本自动加载）。

- 运行前必须先解析专家安装目录的**绝对路径**（通常为 `~/.workbuddy/plugins/marketplaces/my-experts/plugins/yuanbo-school-proposal-team`，以实际安装位置为准），拼接出脚本绝对路径后调用；
- **禁止**使用 CWD 相对路径 `tests/leak_scan.py`——在用户工作区运行时该相对路径不存在；
- **禁止临时自写扫描脚本替代**：若脚本确实缺失/损坏，必须向 Leader 报告阻塞（按交付失败处理），不得自己写一个简化脚本冒充完成扫描。

### 用法
默认词表：
```bash
python3 "<专家目录>/skills/proposal-qa/scripts/leak_scan.py" final.docx
```
加入项目动态词：
```bash
python3 "<专家目录>/skills/proposal-qa/scripts/leak_scan.py" \
  --term "乔老师课程" \
  --term "方书记明确提出" \
  final.docx
```
或附加正则词表：
```bash
python3 "<专家目录>/skills/proposal-qa/scripts/leak_scan.py" --terms project_leak_terms.txt final.docx
```

扫描器应覆盖 DOCX 正文、页眉、页脚、脚注、尾注、批注；解析失败/文件不可读必须视为失败，而不是 clean。纯文本可用 `-` 从 stdin 扫描。

## 2. Full Review 顺序
1. 动态 clientization guard；
2. 通用泄漏模式；
3. 需求覆盖；
4. 事实/证据风险；
5. 顶层设计与后文映射；
6. 课程/服务与空间一致性；
7. 正文完整度；
8. 政策融合；
9. 表格/段落形式；
10. 客户表达与商务分寸；
11. AI 模式；
12. 实施/运行/验收匹配度。

## 3. 问题等级
### P0
- 高风险事实错误/虚构；
- 用户硬性需求遗漏；
- 结构失效、不可交付；
- 关键口径冲突；
- 任意内部信息泄漏，包括动态 internal_only raw term。

### P1
- OUTLINE_LIKE_OUTPUT；
- 顶层与后文断裂；
- 政策明显罗列（含把调研到的政策做成“政策汇总表”全量铺陈进正文；正文应只保留 2-3 条最相关政策并写成论证）；
- 课程空间冲突；
- 对学校基础表达失当；
- 详略严重失衡（核心差异化章节与常规保障章节平均用力、全篇均匀铺陈）；
- 严重 AI 模式影响阅读。

### P2
局部措辞、标题、节奏、表格列名、轻度重复等。

## 4. Closure Review（返修后强制）
QA Round 1 如果 result=revise：
1. Writer 按 required_revision 返修；
2. **必须再次调用 quality-reviewer**；
3. QA 逐条检查上轮 revision id 是否真的关闭；
4. 重新检查动态内部词；
5. 检查是否引入新 P0/P1；
6. remaining 非空时 result 必须 revise。

Writer 的“已修改”声明不能替代 Closure Review。

## 5. OUTLINE_LIKE_OUTPUT
重点看：
- 多个核心标题下只有 1-2 句；
- 课程/空间/服务没有实际任务、场景、运行解释；
- bullet/表格替代全部论证；
- 回答不了“为什么、怎么做、怎么用”。

## 6. 顶层设计
- 概念来自什么真实学校信息？
- 能否映射课程/空间/服务？
- 是帮助理解还是包装？
- 是否把内部方法/领导要求直接展示？
- 是否无依据使用首创/领先？

## 7. 形式
- 横向比较是否用表格；
- 解释原因是否被塞进表格；
- 表格后是否重复；
- 列表是否拆句注水。

## 8. AI 模式
- 无信息增量升华；
- 人为对仗/连续排比；
- 强迫三段式；
- 高频“从A到B”“不是A而是B”；
- 同义信息重复；
- 抽象名词密集；
- 所有章节节奏相同。

## 9. Full QA_REPORT
```yaml
artifact_meta:
  producer: quality-reviewer
  artifact: QA_REPORT
  status: complete
review_mode: full
review_id:
result: pass | revise
p0: []
p1: []
p2: []
required_revision:
  - id:
    location:
    issue:
    action:
optional_revision: []
clientization_check:
  dynamic_terms_checked: true
  leaks_found: []
```

## 10. QA_CLOSURE_REPORT
```yaml
artifact_meta:
  producer: quality-reviewer
  artifact: QA_CLOSURE_REPORT
  status: complete
review_mode: closure
source_review_id:
result: pass | revise
closed_revision_ids: []
remaining_revision_ids: []
new_blockers: []
clientization_check:
  dynamic_terms_checked: true
  leaks_found: []
```

默认最多两轮 QA：full + closure。Closure 仍失败，停止自动交付，由 Leader 报告阻塞项。
