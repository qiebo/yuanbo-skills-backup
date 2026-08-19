# 标书审查（Bid / Tender Response Review）v2.3.0

中文招投标响应文件合规审查 skill。一份招标文件（+补遗）+ 若干响应文件 → 废标风险矩阵、
分级问题清单、评分估算、内容一致性/矛盾机检、HTML 报告。

跨平台（Windows / Linux / macOS）可复用，且不绑定特定 agent 平台：本质是
`SKILL.md 指令 + Python 脚本` 的组合，任何能加载 skill frontmatter、可编排子代理、
装有 Python 3 的宿主（TRAE、Claude、其他 agent 框架、或纯命令行）都能用。

## 目录结构
```text
标书审查V2.0/
├── SKILL.md                    # 主流程（6 步工作流 + 子代理提示词 + 铁律/硬性规则）
├── requirements.txt            # 运行依赖（python-docx / olefile / pdfplumber）
├── CHANGELOG.md
├── scripts/                    # 所有机检/抽取/渲染脚本（纯标准库 + 上述 3 依赖）
├── references/                 # 审查基准/报告/清单/经验教训模板
├── assets/                     # HTML 报告模板（自包含，无外部资源）
└── config/
    └── consistency_dicts.json  # 内容一致性机检的领域词典（换行业改这里即可）
```

## 安装（任意设备，3 步）
```bash
cd 标书审查V2.0
python -m venv .venv                       # 建议虚拟环境，隔离依赖
# Windows
.venv\Scripts\activate && pip install -r requirements.txt
# Linux / macOS
source .venv/bin/activate && pip install -r requirements.txt
```
> `python-docx/olefile/pdfplumber` 均为纯轮子，不直接依赖系统库；解析 `.doc`（老格式）需 `olefile`，`.docx`/`.pdf` 由其余两项支持。

## 快速用法
1. 把招标文件、补遗、响应文件放进项目 `output/`（或任意目录），用对应脚本抽取为 markdown：
   - `.docx` → `python scripts/extract_docx.py 招标文件.docx output/招标文件.md --extract-images`
   - `.pdf`  → `python scripts/extract_pdf.py 招标文件.pdf output/招标文件.md --extract-images`
   - `.doc`  → `python scripts/extract_doc_text.py 招标文件.doc output/招标文件.md`
   - 依次存入 `output/招标文件.md`、`output/补遗1.md`…；响应文件存 `output/响应文件_XX.md`
2. 按 `SKILL.md` 走 6 步工作流（提取基准 → 并行子代理 → 机械核查 → 终审 → HTML）。
3. 机检命令（全部相对路径、跨平台，`output/` 为工作目录下的文本抽取目录）：
   ```bash
   python scripts/verify_prices.py --baseline output/审查基准.md --doc output/响应文件.md
   python scripts/consistency_check.py output/*.md
   python scripts/crossref_check.py output/响应文件_*.md    # → output/机检_内容一致性.md
   python scripts/score_estimate.py --baseline output/审查基准.md --docs output/响应文件_*.md
   python scripts/render_report.py --template assets/report-template.html --data output/report_data.json --out output/终审汇总报告.html
   ```

## 领域适配（换行业/品目时唯一要动的点）
内容一致性机检的词典集中在 `config/consistency_dicts.json`：
- `common_cities`：产地/城市清单（制造商地名 × 产地 一致性校验）
- `suffix_words`：制造商字号清洗时剔除的组织/行政后缀
- `noise_words`：投标主体声明提取时要过滤的噪声词
- `model_prefix_min_len / max_len`：型号前缀字母长度范围（错位校验）
改完即可，无需动脚本。也可用环境变量 `CROSSREF_DICT` 指定自定义词典路径。
其余规则框架（错位链、产地地名冲突、型号前缀对应、跨位置敏感字段冲突）对任何语种/品目通用。

## 迁移到其他设备 / 仓库
- 本目录即完整包：**删除 `.venv/`、`scripts/__pycache__/`** 后再分发（它们含本机绝对路径与平台二进制）。
- 目标机按上方「安装」重建虚拟环境即可，脚本零改动。

## 局限
- 不含图片 OCR / 视觉鉴伪；废标与评分以评标小组对盖章正本及原件/图片的认定为准。
- 电子标有效性以平台 / CA 机构认定为准。
- 评分估算为保守辅助，非评标结论。本包为合规审查辅助意见，不构成法律意见。