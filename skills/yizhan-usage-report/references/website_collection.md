# 网站登录与取数

网页登录采用 WorkBuddy/Codex 优先稳定 API 登录检查、失败后用户协助的受控流程。目标是避开网页登录页验证码的不稳定点，同时避免反复开关浏览器或陷入登录循环。

## 登录策略

Task 3 必须按以下顺序执行：

1. 如果 `output/website_data.json` 已存在，先跳过登录，进入 Task 4 校验。
2. 如果没有可用的 `website_data.json`，先运行稳定登录检查：
   ```bash
   npm install
   npm run login:check -- --credentials "../登录信息.txt" --target-school "学校名" --out "output/login_check.json"
   ```
3. 登录检查只允许执行一次：
   - 默认使用 `/api/login_platform`，不走网页登录页验证码表单。
   - 如有登录信息文件，只在当前运行中读取真实账号和密码，不保存凭证。
   - 只提交一次凭证，不循环重试。
   - 输出的 `login_check.json` 不包含账号、密码、cookie、token 或 authorization header。
4. 自动登录后必须确认 `backend_school` 与目标学校一致。
5. 若自动登录失败、验证码/MFA 阻塞、账号密码不清楚、页面异常、或无法确认后台学校名，立即停止自动登录并请求用户协助。
6. 用户协助时使用固定提示语：

```text
自动登录没有完成。请在打开的浏览器中手动完成生涯翼站后台登录。登录完成并进入学校后台后，请回复：
我已完成生涯翼站后台登录，可以继续取数。
```

7. 用户回复确认前，不得进入 Task 4，不得生成 `website_data.json`，不得生成登记表或报告。
8. 用户确认后，agent 使用当前已登录会话确认后台学校名并采集聚合数据。

如果用户协助后 agent 仍无法连接已登录会话，或仍无法确认后台学校名，必须停止并请求用户处理浏览器状态，或提供已采集的 `website_data.json`。不要重新开始自动登录。

## WorkBuddy 稳定复现命令

推荐把登录作为 Task 3 的固定第一步：

```bash
npm install
npm run login:check -- --credentials "../登录信息.txt" --target-school "深圳实验学校高中部" --out "output/login_check.json"
```

成功条件：

- 命令退出码为 `0`。
- `output/login_check.json` 中 `status` 为 `ok`。
- `backend_school` 与 Excel 目标学校一致，或用户明确确认差异。

如后续取数必须使用浏览器上下文，可在同一次运行中追加：

```bash
npm run login:check -- --credentials "../登录信息.txt" --target-school "深圳实验学校高中部" --out "output/login_check_browser.json" --open-browser
```

不要把 `--profile-dir` 指向长期留存目录。若临时使用了 profile 目录，交付前删除；不要把浏览器 profile、storageState、cookie、token 或 authorization header 作为产物交付。

## 登录检查

- 登录站点通常为 `https://saas.yishengya.cn/`；稳定检查接口为 `https://apiv2.yishengya.cn/api/login_platform`。
- 不保存账号、密码、cookie、token、authorization header。
- 登录后先确认后台身份学校名，与 Excel 目标学校一致或由用户确认差异。
- 保存登录检查证据时只记录：是否成功、后台学校名、目标学校名、时间、使用方式。
- 登录未成功时，必须停止在 Task 3。

## 推荐采集字段

最终 `website_data.json` 至少应包含：

```json
{
  "schema_version": "phase1-task5-website-data-v1",
  "source_site": "https://saas.yishengya.cn/",
  "backend_school": "学校名",
  "collection_policy": "Only aggregate website metrics were persisted. Student-level rows were not saved.",
  "login_check": {
    "status": "ok",
    "method": "api_login_platform_or_user_assisted_visible_browser"
  },
  "manual_dom_aggregates": {
    "student_management_total_accounts": 0,
    "ai_career": {"total_users": 0, "total_uses": 0, "current_month_uses": 0, "table_total_rows": 0},
    "ai_partner_history": {"total_users": 0, "total_uses": 0, "current_month_uses": 0, "table_total_rows": 0},
    "ai_partner_profile": {"table_total_rows": 0},
    "message_bottle": {"published_count": 0, "reply_count": 0, "current_month_bottle_count": 0, "table_total_rows": 0},
    "ai_interview": {"total_users": 0, "total_records": 0, "current_month_records": 0, "report_table_total_rows": 0}
  },
  "api_aggregates": {
    "planner_content_stats": {},
    "partner_content_stats": [],
    "message_bottle_stats": {},
    "message_bottle_tag_stats": [],
    "ai_interview_info": {},
    "ai_interview_reports_meta": {}
  },
  "completeness_audit": {
    "website_full_list_monthly_record_trend": {
      "rows": []
    }
  }
}
```

保存后必须运行：

```bash
python scripts/validate_website_data.py --website "output/website_data.json" --excel-metrics "output/excel_metrics.json"
```

只有校验返回 `status: ok` 才能进入数据登记表生成。任何失败都视为网站取数未完成，必须回到登录/取数步骤或请求用户提供可用的 `website_data.json`。

## 页面和接口线索

- 学生账号总数：系统管理 / 学校信息管理 / 学生管理，读取分页总数。
- AI 生涯规划记录：`/yizhan/aiChat/history/index`，列表接口类似 `/api/ai/planner/dialog_records?page_size=1&page_index=1`。
- AI 生涯规划内容统计：`/yizhan/aiChat/history/statistic`，接口 `/api/ai/planner/content_stats`。
- AI 心语伙伴历史分析：`/yizhan/heart_partner_history/analyse/index`，接口类似 `/api/ai/partner/analysis_records?page_size=1&page=1`。
- AI 心语伙伴内容统计：`/yizhan/heart_partner_history/analyse/statistic`，接口 `/api/ai/partner/content_stats`。
- AI 心语伙伴画像：`/yizhan/heart_partner_ai/report`，接口类似 `/api/ai/partner_profile/list?limit=1&page=1`。
- 漂流瓶记录：`/yizhan/drift_bottle/list/index/`，接口类似 `/api/ai/message_bottle?page_size=1&page=1`。
- 漂流瓶统计：`/yizhan/drift_bottle/list/index/statistic`，接口 `/api/ai/message_bottle/tag_stats`。
- AI 模拟面试：`/yizhan/aiInterview/history/index`，接口类似 `/api/ai/interview_stats/reports?page_size=1&page=1`。
- AI 模拟面试汇总：接口通常包含 `/api/ai/interview_stats/info`。

## 趋势口径

趋势必须来自网站后台记录，不从 Excel 月度统计表替代。优先做全量分页匿名聚合，只保存每月计数和去重总数，不保存列表行。

推荐趋势字段：

```json
{
  "month": "2026-01",
  "ai_career_dialog_records": 0,
  "ai_partner_analysis_records": 0,
  "message_bottle_posts": 0,
  "ai_interview_reports": 0,
  "total_backend_records": 0
}
```

报告措辞必须写“后台记录数趋势”或“网站后台记录趋势”，不要写成“使用次数趋势”。
