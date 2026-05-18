# 网站登录与取数

默认使用可用的浏览器自动化能力完成登录与取数。优先级：

1. `browser-use` 或同类智能浏览器代理。
2. Playwright / Chrome DevTools / 当前浏览器标签页。
3. 人工协助登录后，由 agent 继续读取页面和接口。

若连续 3 次登录失败、验证码无法识别、账号密码格式不清楚，停止重试并请求用户协助完成登录。不要把账号、密码、cookie、token、学生明细保存到产物中。

## 登录

- 登录站点通常为 `https://saas.yishengya.cn/`。
- 只输入真实账号和密码，不要把“账号”“密码”等提示文字一起输入。
- 登录后先确认后台身份学校名，与 Excel 目标学校一致或可解释。
- 保存登录检查证据时只记录：是否成功、后台学校名、目标学校名、时间、使用方式。不要保存凭证。

## 推荐采集字段

最终 `website_data.json` 至少应包含：

```json
{
  "schema_version": "phase1-task5-website-data-v1",
  "source_site": "https://saas.yishengya.cn/",
  "backend_school": "学校名",
  "collection_policy": "Only aggregate website metrics were persisted. Student-level rows were not saved.",
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
