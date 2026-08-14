# YB配置清单 skill（可迁移版）

面向学校 / 教育机构**生涯、心理、科创及通用设备与软件**建设项目的**配置清单生成 skill**。
解析项目需求文件，按**业务线大类**（生涯 / 科创）从 **ERP §6 产品接口**运行期切片拉取产品，
以 **tags / 小类名 / 分组名多信号语义匹配**生成**可追溯、可确认、可审计**的设备 / 软件配置清单（含预算）。

> 本目录为**可迁移安装包**：不绑定任何机器路径，不携带真实 token，不含运行期快照。
> 直接整体复制到目标 agent 的 skills 目录即可使用。

---

## 1. 与"本地产品库"旧版的核心区别

旧版把一份 `standard-products.json`（1664 条产品 + 本地图片）随技能打包，
维护成本高、易过期。本版改为：

| 项 | 旧版 | 本可迁移版 |
|---|---|---|
| 产品内容来源 | 随包的固定 `standard-products.json` | 运行期从 ERP §6 **按需切片拉取** |
| 切片入口 | 无（全量本地库） | **业务线大类**（`--line 生涯/科创`）+ 空间/显式分类/关键词 |
| 语义匹配锚点 | 人工维护的空间大字典 | **多信号分层**：小类名/分组名（受控词表）+ ERP `tags` 派生 function_tags + 产品名 + product_intro；空间词仅参考 |
| 图片 | 下载到本地 `product-images/` 并做 SHA-256 核验 | **引用 ERP `image_url` 远程链接，不下载、不本地核验** |
| 固定资源 | 整个产品库 | 仅 `product-mapping.json`（规则）+ overlay（人工知识）+ 每次运行的快照（数据） |

溯源仍 100% 成立：每条产品行经 `product_key(=ERP product_no)` 可追溯至运行期快照与 ERP 原记录。

### 三层数据架构（什么存本地、什么运行期拿）

| 层 | 内容 | 位置 |
|---|---|---|
| 产品数据层 | 名称/编号/品牌/型号/价格/**tags**/小类/分组/图片 URL | **运行期 ERP**（`assets/erp-runs/<run_id>/snapshot.json`，不进包） |
| 派生缓存层 | 品牌词典、空间词表、空 tags 语义兜底、空间查询入口 | `product-mapping.json`，`build_product_mapping.py` 从 ERP 全量统计自动派生，可重跑刷新 |
| 人工规则层 | `query_routing.business_lines`（业务线→ERP 大类）、`keyword_aliases`（需求词→ERP 关键词） | `product-mapping.overlay.json` 人工维护，build 时深合并，重跑不丢失 |

ERP 里不存在同义词与业务线知识，故必须人工维护；映射层与快照分别 SHA-256 指纹化，
规则版本与数据版本都可审计、可复现。

---

## 2. 目录结构

```
YB配置清单/
├── SKILL.md                          # skill 主入口（frontmatter + 强约束）
├── agents/
│   └── openai.yaml                   # OpenAI 风格 agent 消费方式示例（可选）
├── assets/
│   ├── product-mapping.json         # ★ 薄映射层（build 自动派生 + overlay 合并产物）
│   ├── product-mapping.overlay.json # ★ 人工覆盖层（业务线路由/同义词/条目修正，重跑不丢）
│   ├── default-configuration-list.xlsx  # 配置清单 Excel 模板（中立空壳，标题按项目动态填写）
│   ├── project-intake-template.yaml # 项目需求采集模板
│   └── erp_apikey.example.txt       # token 占位/示例（重命名为 erp_apikey.txt 填入真实 token）
├── references/
│   ├── universal-rules.md           # 来源、版本、多信号匹配、图片约束、强约束
│   ├── project-schema.md            # 配置清单字段契约（含 business_lines）
│   ├── validation-checklist.md      # 校验清单（硬错误级）
│   └── workflow-and-gates.md        # 阶段 A–H 流程与 4 道门
├── scripts/
│   ├── build_product_mapping.py      # 一次性：由 ERP 生成 product-mapping.json（合并 overlay）
│   ├── fetch_erp_catalog.py          # 按需：业务线/空间/关键词切片拉取 → 运行期快照
│   └── insert_product_images.py      # 把远程图片引用写入配置清单（依赖 openpyxl）
└── tests/
    ├── test_insert_product_images.py # 图片插入与模板结构测试
    └── test_fetch_erp_catalog.py     # 查询路由/关键词收窄逻辑测试
```

> 已**剔除**：`import_product_images.py`（旧版本地图片导入，已废弃并硬拦截）、
> `__pycache__`、运行期 `assets/erp-runs/` 快照（每次运行自动生成）。

---

## 3. 安装（给另一个 agent）

把整个 `YB配置清单/` 目录复制到目标 agent 的 skills 目录即可，例如：

- WorkBuddy：`~/.workbuddy/skills/YB配置清单/`
- 其他 agent：按其 skills 目录约定放置

整个目录复制到目标 agent 的 skills 目录即可。依赖说明：

- `build_product_mapping.py` / `fetch_erp_catalog.py` **仅依赖 Python 标准库**（请求用 `urllib`）；
- `insert_product_images.py` 依赖 **openpyxl**（`pip install openpyxl`），仅在写 Excel 图片引用时需要。

---

## 4. 配置 ERP token（必做，三选一，优先级从高到低）

1. **运行时传参**（推荐，最安全）：
   ```bash
   python scripts/fetch_erp_catalog.py --token-file /path/to/erp_apikey.txt --space 自我认知室
   ```
2. **环境变量**：
   ```bash
   export ERP_API_TOKEN=你的token        # Windows: set ERP_API_TOKEN=你的token
   python scripts/fetch_erp_catalog.py --space 自我认知室
   ```
3. **文件兜底**：把 `assets/erp_apikey.example.txt` 重命名为 `assets/erp_apikey.txt`
   并填入真实 token（纯文本一行，带不带 `Bearer ` 前缀都行）。

> 真实接口地址 `https://erpapi.yishengya.cn/api` 可用环境变量 `ERP_API_BASE` 覆盖。
> **本包不携带任何真实 token**，请自行从 ERP 后台获取。

---

## 5. 运行流程

### 步骤 A — 生成薄映射层（仅首次 / ERP 类目或标签体系大改时）

```bash
python scripts/build_product_mapping.py --token-file assets/erp_apikey.txt
# 产物：assets/product-mapping.json（自动派生层 + product-mapping.overlay.json 人工层深合并）
```

该脚本从 ERP 拉取类目树（含大类与小类）+ 全部在售产品，自动派生：
- `space_to_query`：空间名 → 应查的 ERP 分类 / 关键词（空间词条目来自 ERP `tags` 中带空间后缀的词条，另含父级大类直达入口）
- `tag_routing`：把 ERP `tags` 分流为 `source_spaces` / `function_tags` / 品牌型号噪声
- `category_fallback`：空 tags 产品的低置信语义兜底（`confidence=low`，不作主锚点）
- `price_policy` / `image_policy` / `role_map` / `key_map`

人工知识（ERP 中不存在，脚本算不出来）维护在 `assets/product-mapping.overlay.json`：
- `query_routing.business_lines`：**业务线 → ERP 启用大类**（`生涯`→[112,44,45]、`科创`→[111]），Stage E 的 `--line` 切片入口；ERP 新增大类时在此加一行
- `keyword_aliases`：**需求词 → ERP tags/小类/分组关键词** 同义词表，约 30 条播种，随用随补
- 空间条目修正等。overlay 在 build 时深合并进 mapping.json，并记录 `overlay_ref` 指纹以便审计。

### 步骤 B — 按需切片拉取（每次生成配置清单时，Stage E 调用）

```bash
# 按业务线切片（推荐主入口；生涯=生涯中心+翼生涯系统+生涯工具，科创=科创中心）
python scripts/fetch_erp_catalog.py --line 科创 --run-id run-20260813

# 业务线切片 + 客户端关键词收窄（按 产品名+tags+小类名+分组名 任一命中保留）
python scripts/fetch_erp_catalog.py --line 科创 --keywords 机器人,竞赛 --run-id run-20260813

# 通用物资（桌椅/触控屏等无独立大类）：关键词全库搜索，或先用 ERP category/list 实时发现分组再显式切片
python scripts/fetch_erp_catalog.py --keywords 桌子,椅子 --run-id run-20260813

# 空间/显式查询（向后兼容）
python scripts/fetch_erp_catalog.py --space 自我认知室
python scripts/fetch_erp_catalog.py --category-id 112 --classification-id 9 --name 测评
# 产物：assets/erp-runs/<run-id>/snapshot.json + snapshot.sha256 + manifest.json
```

- 自带分页循环；`--line`/`--space` 按映射层路由展开为 `category_id`（父类）/`classification_id`（叶子分组）/`name` 关键词组合查询（**不拉全量 1664 条**）。
- `--keywords` 是客户端收窄：ERP 服务端 `name` 参数只搜 name+tags，小类/分组名锚点由客户端补足；命中关键词记录在产品 `matched_keywords` 与 `manifest.json`。
- `snapshot.json` 即本次运行的"标准产品库"等价物，带 SHA-256；`manifest.json` 同时记录**映射层 SHA-256**（含 overlay 指纹引用）。
- 每条产品已归一化为 skill 字段契约：`source_spaces`（参考证据）/ `function_tags` / `category`（小类名）/ `product_group`（分组名）/ `product_role` / 三价（市场/渠道/成本）/ `image_refs`（远程链接，`locally_verified=false`）。
- 映射层生成超过 30 天时脚本会打印刷新提醒（ERP 标签体系演变后重跑步骤 A 即可）。

### 步骤 C — 写入配置清单

由 `scripts/insert_product_images.py` 把 `snapshot.json` 中的远程图片引用
（`erp-image-url-v1` / `locally_verified=false`）插入到配置清单 Excel 的产品行，
**不覆盖用户原始输入文件**，仅产出新文件。具体调用方式见 `SKILL.md` 与 `workflow-and-gates.md`。

---

## 6. 双层指纹（溯源 / 审计核心）

| 指纹 | 哈希对象 | 含义 |
|---|---|---|
| 快照 SHA-256 | `snapshot.json` | 本次从 ERP 拉到的**数据切片** |
| 映射层 SHA-256 | `product-mapping.json` | 把原始数据**翻译**成清单语言的**规则** |

任一变化都意味着输出语义改变；旧快照保留旧映射层 SHA，二者永不混，满足"可复现、可审计"。

---

## 7. 迁移注意点

- **不含真实 token**：使用前按第 4 节配置，切勿把真实 token 提交进版本库。
- **不含运行期快照**：`assets/erp-runs/` 不在包内，首次运行自动生成，可安全加入 `.gitignore`。
- **图片为远程引用**：不下载、不本地核验；交付物中图片以 ERP `image_url` 超链接呈现，离线环境需另行处理。
- **映射层 = 自动派生 + 人工 overlay**：迁移到新 ERP 实例后，先按实例修订 `product-mapping.overlay.json` 的 `business_lines`（大类 id）与 `keyword_aliases`，再重跑 `build_product_mapping.py` 重新派生。
- **Excel 图片插入依赖 openpyxl**：目标环境如无，执行 `pip install openpyxl`（其余脚本纯标准库）。

---

## 8. 测试

```bash
python -m unittest discover tests -v
# 预期：全部 ok（模板结构 / 远程图片插入 / 查询路由 / 关键词收窄）
```

---

## 9. 依赖与运行环境

- Python 3.10+；`build`/`fetch` 仅用标准库（`argparse` `json` `hashlib` `urllib` `re` `os` 等）
- `insert_product_images.py` 与模板相关测试依赖 `openpyxl`
- 网络可达 ERP 接口 `https://erpapi.yishengya.cn/api`
