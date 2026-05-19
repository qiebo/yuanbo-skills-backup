# 使用说明

用户每次运行前准备：

- `统计查询按月.xlsx`：包含学校名、月份、各功能数据条数/使用人数、总使用人数、总登录人次、平均登录次数和 `总计` 行。
- 生涯翼站后台登录条件：账号密码或已经登录好的浏览器环境。agent 会先运行一次稳定 API 登录检查，失败后再请用户协助。
- 可选：已采集好的 `website_data.json`。如果有这个文件，可跳过重新登录网站。

推荐运行目录：

```text
run-folder/
├─ input/
│  └─ 学校-统计查询按月.xlsx
├─ output/
└─ logs/
```

推荐用户提示词：

```text
请使用 yizhan-usage-report skill，基于 input 文件夹里的统计查询按月 Excel，先尝试自动登录生涯翼站后台采集网站聚合数据；如果登录失败，再请求我手动协助登录。只输出 Word 报告和数据登记表，并完成 QA。
```

如果已有网站聚合数据：

```text
请使用 yizhan-usage-report skill，基于 input/学校-统计查询按月.xlsx 和 output/website_data.json 生成报告，不需要重新登录网站。
```

默认输出：

- `excel_metrics.json`
- `{学校名}-生涯翼站报告数据汇总.json`
- `{学校名}-生涯翼站报告数据汇总.xlsx`
- `{学校名}-生涯翼站使用情况学期分析报告.docx`

登录方式：

- Task 3 默认先尝试一次稳定 API 登录检查，推荐命令：
  ```bash
  npm install
  npm run login:check -- --credentials "../登录信息.txt" --target-school "学校名" --out "output/login_check.json"
  ```
- 自动登录使用当前运行中提供的账号密码调用后台登录检查接口，不走网页登录页验证码表单。
- 如果后续取数必须使用浏览器上下文，可追加 `--open-browser` 打开同一次运行的临时已登录浏览器。
- 如果自动登录失败、验证码/MFA 阻塞、凭证不清楚或后台学校名无法确认，agent 必须停止并请求用户协助。
- 用户在浏览器中完成登录并进入学校后台后，回复：`我已完成生涯翼站后台登录，可以继续取数。`
- 自动登录成功或用户确认前，agent 不会进入 Task 4，也不会生成报告。

需要人工进一步确认的情况：

- 自动登录失败、验证码/MFA 阻塞或凭证不清楚。
- 用户完成手动登录后，agent 仍无法确认后台学校名。
- 后台学校名与 Excel 学校名不一致。
- 网站数据缺失或与 Excel 明显冲突。

稳定执行要求：

- agent 必须先展示 Task 1 到 Task 8 的执行清单。
- 每个 task 完成后才能进入下一个 task。
- Task 3 允许一次受控自动登录尝试；失败后必须请求用户协助。
- 不得反复打开/关闭浏览器，不得循环提交凭证，不得在登录成功或用户确认前进入 Task 4。
- `output/login_check.json` 只能保存登录检查结果和学校身份，不得保存账号、密码、cookie、token 或 authorization header。
- 登录或网站数据校验失败时，agent 必须停止并请求用户协助，不能生成空报告。

固定交付原则：

- Word 是默认正式报告。
- Excel/JSON 数据登记表用于追溯和复盘。
- 不保存账号、密码、cookie、token、authorization header、学生个人明细或后台列表行。
