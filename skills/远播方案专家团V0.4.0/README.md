# 远播方案专家团

**版本：0.4.0（可审计协作 + Clientization Guard + QA Closure + 四张确认卡 + 精排交付）**

面向 K12 学校、重点服务初中和高中场景的 WorkBuddy Team 型专家团。当前只处理一种主文类：**学校特色育人空间/项目建设方案**，首期覆盖科创/科学教育/工程实践，以及生涯/心理/学生发展。

## V0.2.1 本轮只修三个真实问题
1. **专家调用不可验证** → 所有专业产物增加 `artifact_meta.producer`，Leader 必须验证 producer 与预期 Agent ID 一致；每次真实派发给用户 1 行进度提示，WORKFLOW_LOG 记录实际调用。
2. **QA 返修缺少独立复审** → 首次 QA revise 后强制 `proposal-writer(REVISED_DRAFT) → quality-reviewer(closure)`；Writer 不能自我关闭问题；Closure 仍失败则停止自动交付。
3. **内部资料/人名/内部称呼泄漏** → requirement-analyst 在 PROJECT_BRIEF 生成动态 `clientization_guard.internal_only_terms`；Writer/QA 必须逐项处理；`leak_scan.py` 支持 `--term` 动态 literal term，并扫描 DOCX 正文、页眉、页脚、脚注、尾注、批注，解析失败直接阻断。

## 团队
| Agent | 角色 | 核心产出 |
|---|---|---|
| proposal-team-lead | 方案总师 | 路由、调度、门禁、最终汇总 |
| requirement-analyst | 需求分析专家 | PROJECT_BRIEF + clientization_guard |
| evidence-researcher | 信息研究专家 | EVIDENCE_BRIEF |
| top-design-architect | 顶层设计专家 | DESIGN_BRIEF |
| education-program-designer | 课程与育人体系专家 | PROGRAM_PLAN |
| space-planner | 空间规划专家 | SPACE_PLAN |
| proposal-writer | 资深方案主笔 | DRAFT / REVISED_DRAFT |
| quality-reviewer | 方案质量评审专家 | QA_REPORT / QA_CLOSURE_REPORT |

## 完整新方案流程
```text
TeamCreate
  ↓
requirement-analyst → PROJECT_BRIEF + clientization_guard
  ↓
evidence-researcher
  ↓
top-design-architect
  ↓
课程专家 ─┐
          ├→ proposal-writer → quality-reviewer(full)
空间专家 ─┘                         │
                          pass ─────┤→ leak_scan → delivery
                          revise    │
                              proposal-writer(REVISED_DRAFT)
                                      ↓
                              quality-reviewer(closure)
                                      ↓
                                pass / STOP
```

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
- **0.4.0：固化完整交付流水线——四张确认卡门禁、QA 最多两轮闭环、通用词表 + 动态 internal_only 词泄漏扫描、精美 Word 精排版（Phase 7.5）与排后重扫；分发包去除本机个人路径，改为跨平台通用写法。**
