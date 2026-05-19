#!/usr/bin/env node

const fs = require("fs");
const path = require("path");

const DEFAULT_SITE = "https://saas.yishengya.cn/";
const DEFAULT_API_BASE = "https://apiv2.yishengya.cn";

function parseArgs(argv) {
  const args = {
    site: DEFAULT_SITE,
    apiBase: DEFAULT_API_BASE,
    credentials: process.env.YIZHAN_CREDENTIALS || null,
    username: process.env.YIZHAN_USERNAME || null,
    password: process.env.YIZHAN_PASSWORD || null,
    targetSchool: process.env.YIZHAN_TARGET_SCHOOL || null,
    out: "output/website_data.json",
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = () => {
      if (i + 1 >= argv.length) throw new Error(`Missing value for ${arg}`);
      i += 1;
      return argv[i];
    };
    if (arg === "--site") args.site = next();
    else if (arg === "--api-base") args.apiBase = next();
    else if (arg === "--credentials") args.credentials = next();
    else if (arg === "--username") args.username = next();
    else if (arg === "--password") args.password = next();
    else if (arg === "--target-school") args.targetSchool = next();
    else if (arg === "--out") args.out = next();
    else if (arg === "--help" || arg === "-h") {
      printHelp();
      process.exit(0);
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  return args;
}

function printHelp() {
  console.log(`Usage:
  npm run website:collect -- --credentials "../登录信息.txt" --target-school "深圳实验学校高中部" --out "output/website_data.json"

The output keeps only aggregate website metrics. It never persists credentials,
cookies, tokens, authorization headers, or student-level rows.
`);
}

function resolveCredentialPath(explicitPath) {
  if (explicitPath) return path.resolve(explicitPath);
  const candidates = [
    path.resolve(process.cwd(), "登录信息.txt"),
    path.resolve(process.cwd(), "..", "登录信息.txt"),
    path.resolve(process.cwd(), "..", "..", "登录信息.txt"),
  ];
  return candidates.find((candidate) => fs.existsSync(candidate)) || null;
}

function readCredentials(args) {
  let username = args.username;
  let password = args.password;
  const credentialPath = resolveCredentialPath(args.credentials);
  if ((!username || !password) && credentialPath && fs.existsSync(credentialPath)) {
    const content = fs.readFileSync(credentialPath, "utf8");
    const usernameMatch = content.match(/账号\s*[：:]\s*([^\s\r\n]+)/u);
    const passwordMatch = content.match(/密码\s*[：:]\s*([^\s\r\n]+)/u);
    username = username || (usernameMatch ? usernameMatch[1].trim() : null);
    password = password || (passwordMatch ? passwordMatch[1].trim() : null);
  }
  return { username, password, credentialSource: credentialPath ? path.basename(credentialPath) : "env_or_args" };
}

function backendSchoolFromUser(user) {
  return user?.organization?.model?.name || user?.organization?.org_name || user?.school_name || null;
}

async function apiJson(apiBase, endpoint, token = null, options = {}) {
  const url = endpoint.startsWith("http") ? endpoint : `${apiBase.replace(/\/$/, "")}${endpoint}`;
  const headers = { accept: "application/json", ...(options.headers || {}) };
  if (token) headers.authorization = token;
  const response = await fetch(url, { ...options, headers });
  const text = await response.text();
  let payload;
  try {
    payload = JSON.parse(text);
  } catch {
    throw new Error(`Non-JSON response from ${endpoint}: ${response.status}`);
  }
  if (payload.code && payload.code !== 200) {
    throw new Error(`API failed ${endpoint}: ${payload.code} ${payload.message || ""}`.trim());
  }
  return payload;
}

async function login(args, credentials) {
  if (!credentials.username || !credentials.password) throw new Error("credentials_missing");
  const payload = await apiJson(args.apiBase, "/api/login_platform", null, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ username: credentials.username, password: credentials.password }),
  });
  if (!payload.data?.token || !payload.data?.user) throw new Error("api_login_platform_missing_token_or_user");
  return {
    token: payload.data.token,
    user: payload.data.user,
    backendSchool: backendSchoolFromUser(payload.data.user),
  };
}

function toMonth(value) {
  if (!value || typeof value !== "string") return null;
  const match = value.match(/(\d{4})[-/](\d{1,2})/);
  if (!match) return null;
  return `${match[1]}-${String(Number(match[2])).padStart(2, "0")}`;
}

function number(value, fallback = 0) {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string") {
    const cleaned = value.replace(/,/g, "").replace(/%/g, "").trim();
    const parsed = Number(cleaned);
    if (Number.isFinite(parsed)) return parsed;
  }
  return fallback;
}

function bumpMonth(rowsByMonth, month, key) {
  if (!month) return;
  if (!rowsByMonth.has(month)) {
    rowsByMonth.set(month, {
      month,
      ai_career_dialog_records: 0,
      ai_partner_analysis_records: 0,
      message_bottle_posts: 0,
      ai_interview_reports: 0,
      total_backend_records: 0,
    });
  }
  const row = rowsByMonth.get(month);
  row[key] += 1;
  row.total_backend_records += 1;
}

async function collectPagedList(apiBase, token, makeEndpoint, listGetter, totalGetter, pageCountGetter, pageParamName, pageSizeParamName, pageSize = 200) {
  const first = await apiJson(apiBase, makeEndpoint(1, pageSize), token);
  const firstData = first.data || {};
  const firstList = listGetter(firstData) || [];
  const total = number(totalGetter(firstData), firstList.length);
  const pageCountValue = number(pageCountGetter(firstData), 0);
  const expectedPages = Math.max(
    1,
    Math.ceil((total || pageCountValue || firstList.length) / pageSize),
    pageCountValue > pageSize ? Math.ceil(pageCountValue / pageSize) : pageCountValue
  );
  const rows = [...firstList];

  for (let page = 2; page <= expectedPages; page += 1) {
    const payload = await apiJson(apiBase, makeEndpoint(page, pageSize), token);
    const list = listGetter(payload.data || []) || [];
    rows.push(...list);
    if (!list.length) break;
  }

  return { rows, total: total || rows.length };
}

function endpointWithParams(base, params) {
  const url = new URL(base, "https://placeholder.local");
  Object.entries(params).forEach(([key, value]) => url.searchParams.set(key, String(value)));
  return `${url.pathname}${url.search}`;
}

async function collect(args, loginResult) {
  const token = loginResult.token;
  const apiBase = args.apiBase;

  const [
    students,
    careerRecords,
    careerStats,
    partnerRecords,
    partnerStats,
    partnerProfiles,
    bottleRecords,
    bottleStats,
    bottleTagStats,
    interviewReports,
    interviewInfo,
  ] = await Promise.all([
    apiJson(apiBase, "/api/school/system/student?page=1&limit=1", token),
    apiJson(apiBase, "/api/ai/planner/dialog_records?page_size=1&page_index=1", token),
    apiJson(apiBase, "/api/ai/planner/content_stats", token),
    apiJson(apiBase, "/api/ai/partner/analysis_records?page_size=1&page=1", token),
    apiJson(apiBase, "/api/ai/partner/content_stats", token),
    apiJson(apiBase, "/api/ai/partner_profile/list?limit=1&page=1", token),
    apiJson(apiBase, "/api/ai/message_bottle?page_size=1&page=1", token),
    apiJson(apiBase, "/api/ai/message_bottle/stats", token),
    apiJson(apiBase, "/api/ai/message_bottle/tag_stats", token),
    apiJson(apiBase, "/api/ai/interview_stats/reports?page_size=1&page=1", token),
    apiJson(apiBase, "/api/ai/interview_stats/info", token),
  ]);

  const rowsByMonth = new Map();
  const bottleSenderIds = new Set();

  const careerFull = await collectPagedList(
    apiBase,
    token,
    (page, size) => endpointWithParams("/api/ai/planner/dialog_records", { page_index: page, page_size: size }),
    (data) => data.list,
    (data) => data.page_count,
    (data) => data.page_count,
    "page_index",
    "page_size"
  );
  for (const row of careerFull.rows) bumpMonth(rowsByMonth, toMonth(row.interaction_time), "ai_career_dialog_records");

  const partnerFull = await collectPagedList(
    apiBase,
    token,
    (page, size) => endpointWithParams("/api/ai/partner/analysis_records", { page, page_size: size }),
    (data) => data.records,
    (data) => data.pagination?.page_count,
    (data) => data.pagination?.page_count,
    "page",
    "page_size"
  );
  for (const row of partnerFull.rows) bumpMonth(rowsByMonth, toMonth(row.interaction_time || row.created_at), "ai_partner_analysis_records");

  const bottleFull = await collectPagedList(
    apiBase,
    token,
    (page, size) => endpointWithParams("/api/ai/message_bottle", { page, page_size: size }),
    (data) => data.list,
    (data) => data.page_count,
    (data) => data.page_count,
    "page",
    "page_size"
  );
  for (const row of bottleFull.rows) {
    bumpMonth(rowsByMonth, toMonth(row.created_at), "message_bottle_posts");
    if (row.sender_id !== undefined && row.sender_id !== null) bottleSenderIds.add(String(row.sender_id));
  }

  const interviewFull = await collectPagedList(
    apiBase,
    token,
    (page, size) => endpointWithParams("/api/ai/interview_stats/reports", { page, page_size: size }),
    (data) => data.reports,
    (data) => data.pagination?.total,
    (data) => data.pagination?.last_page,
    "page",
    "page_size"
  );
  for (const row of interviewFull.rows) bumpMonth(rowsByMonth, toMonth(row.created_at), "ai_interview_reports");

  const careerUsage = careerRecords.data?.usage_stats || {};
  const partnerData = partnerRecords.data || {};
  const bottleData = bottleStats.data || {};
  const interviewData = interviewInfo.data || {};
  const reportsTotal = number(interviewReports.data?.pagination?.total, interviewFull.total);

  const trendRows = [...rowsByMonth.values()].sort((a, b) => a.month.localeCompare(b.month));
  const now = new Date();

  return {
    schema_version: "phase1-task5-website-data-v1",
    source_site: args.site,
    backend_school: loginResult.backendSchool,
    collected_at: now.toISOString(),
    collection_policy: "Only aggregate website metrics were persisted. Student-level rows were not saved.",
    login_check: {
      status: "ok",
      method: "api_login_platform",
      credential_source: "runtime_only",
    },
    manual_dom_aggregates: {
      student_management_total_accounts: number(students.data?.cnt),
      ai_career: {
        total_users: number(careerUsage.total_users),
        total_uses: number(careerUsage.total_interactions),
        current_month_uses: number(careerUsage.monthly_sessions),
        table_total_rows: number(careerRecords.data?.page_count, careerFull.total),
      },
      ai_partner_history: {
        total_users: number(partnerData.total_users),
        total_uses: number(partnerData.total_records),
        current_month_uses: number(partnerData.current_month_records),
        table_total_rows: number(partnerData.pagination?.page_count, partnerFull.total),
      },
      ai_partner_profile: {
        table_total_rows: number(partnerProfiles.data?.page_count, partnerProfiles.data?.total_pages),
      },
      message_bottle: {
        published_count: number(bottleData.bottle_count),
        reply_count: number(bottleData.reply_count),
        current_month_bottle_count: number(bottleData.month_bottle_count),
        table_total_rows: number(bottleRecords.data?.page_count, bottleFull.total),
      },
      ai_interview: {
        total_users: number(interviewData.total_users),
        total_records: number(interviewData.total_records),
        current_month_records: number(interviewData.current_month_records),
        report_table_total_rows: reportsTotal,
      },
    },
    api_aggregates: {
      planner_content_stats: careerStats.data || {},
      partner_content_stats: partnerStats.data || [],
      message_bottle_stats: bottleData,
      message_bottle_tag_stats: bottleTagStats.data || [],
      ai_interview_info: interviewData,
      ai_interview_reports_meta: {
        numeric_total_like_fields: {
          "data.pagination.total": reportsTotal,
          "data.pagination.last_page": number(interviewReports.data?.pagination?.last_page),
        },
      },
    },
    completeness_audit: {
      website_full_list_monthly_record_trend: {
        rows: trendRows,
        module_totals: {
          ai_career_dialog_records: { total_records: careerFull.rows.length },
          ai_partner_analysis_records: { total_records: partnerFull.rows.length },
          message_bottle: {
            total_records: bottleFull.rows.length,
            unique_sender_count: bottleSenderIds.size,
          },
          ai_interview_reports: { total_records: interviewFull.rows.length },
        },
      },
      table_completeness: [
        {
          table_no: "T-Student",
          purpose: "学生账号总数",
          task5_status: "ok",
          recommended_fields: ["manual_dom_aggregates.student_management_total_accounts"],
          source: "/api/school/system/student",
          notes: "Only pagination total cnt was persisted.",
        },
        {
          table_no: "T-Trend",
          purpose: "网站后台记录趋势",
          task5_status: "ok",
          recommended_fields: ["completeness_audit.website_full_list_monthly_record_trend.rows"],
          source: "Anonymized month aggregation from backend list APIs.",
          notes: "Student-level rows were discarded after aggregation.",
        },
      ],
    },
  };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const credentials = readCredentials(args);
  const loginResult = await login(args, credentials);
  if (!loginResult.backendSchool) throw new Error("backend_school_missing");
  if (args.targetSchool && loginResult.backendSchool !== args.targetSchool) {
    throw new Error(`backend_school_mismatch: backend=${loginResult.backendSchool}, target=${args.targetSchool}`);
  }

  const websiteData = await collect(args, loginResult);
  const outPath = path.resolve(args.out);
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, `${JSON.stringify(websiteData, null, 2)}\n`, "utf8");
  console.log(JSON.stringify({
    status: "ok",
    out: outPath,
    backend_school: websiteData.backend_school,
    student_accounts: websiteData.manual_dom_aggregates.student_management_total_accounts,
    trend_rows: websiteData.completeness_audit.website_full_list_monthly_record_trend.rows.length,
  }, null, 2));
}

main().catch((error) => {
  console.error(error && error.stack ? error.stack : error);
  process.exitCode = 1;
});
