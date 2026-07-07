# 远播方案助手 V1.0（通用技能包）

本技能是 `education-proposal-design` 的**代理无关（agent-agnostic）通用打包**，供任意支持 `SKILL.md`
（含 `name` / `description` frontmatter）的 AI Agent 加载使用，例如 Claude、WorkBuddy 及其他 Agent 框架。

## 能力

从需求理解到 Word 交付的完整教育项目方案设计工作流：

- 教育政策与学校背景调研
- 方案顶层设计与章节大纲（概念词＋结构隐喻＋学校基因融合，见 `references/top_design_playbook.md`）
- 去 AI 化专业撰写（正例库见 `references/writing_guide.md` 第九节）
- 三方评审门控（课程 / 商业 / 政策）
- 格式化 Word 文档生成
- 老师 / 客户反馈驱动的迭代修改

## 目录结构

| 路径 | 说明 |
|------|------|
| `SKILL.md` | 技能主文件（标准 frontmatter：`name` / `version` / `description`） |
| `references/top_design_playbook.md` | 顶层设计方法库（金标准提炼） |
| `references/writing_guide.md` | 去 AI 化写作规范与金标准正例库 |
| `references/material_organization.md` | 资料组织与溯源方法 |
| `scripts/generate_proposal.js` | Word 生成脚本（Node.js + `docx`） |

## 环境要求

- 文件读写能力（Agent 在的工作目录创建/编辑 Markdown 与 `.docx`）。
- 文档生成（任选其一）：Node.js + `docx`（用附带的 `generate_proposal.js`）；或 `python-docx` / `pandoc` 由 `3_方案终稿.md` 生成等效 Word。
- 三方评审：具备子代理能力的 Agent 可并行派发；否则分三轮独立评审。

## 使用方式

Agent 读取 `SKILL.md` 后，按"阶段一需求确认 → 阶段二调研 → 阶段三大纲与顶层设计 → 阶段四撰写
→ 阶段五三方评审 → 阶段六 Word 生成 → 阶段七交付迭代"执行即可。所有方法论细节见 `references/`。
