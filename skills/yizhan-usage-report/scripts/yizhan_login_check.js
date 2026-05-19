#!/usr/bin/env node

const fs = require("fs");
const os = require("os");
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
    out: null,
    openBrowser: false,
    profileDir: null,
    browserExecutable: null,
    headless: false,
    keepOpenMs: 0,
    timeoutMs: 45000,
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
    else if (arg === "--open-browser") args.openBrowser = true;
    else if (arg === "--profile-dir") args.profileDir = next();
    else if (arg === "--browser-executable") args.browserExecutable = next();
    else if (arg === "--headless") args.headless = true;
    else if (arg === "--headed") args.headless = false;
    else if (arg === "--keep-open-ms") args.keepOpenMs = Number(next());
    else if (arg === "--timeout-ms") args.timeoutMs = Number(next());
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
  npm run login:check -- --credentials "../登录信息.txt" --target-school "深圳实验学校高中部" --out "output/login_check.json"

Stable WorkBuddy flow:
  1. Run the command above.
  2. Continue only when output/login_check.json has "status": "ok".

Options:
  --site URL                 SaaS site. Default: ${DEFAULT_SITE}
  --api-base URL             API base. Default: ${DEFAULT_API_BASE}
  --credentials PATH          UTF-8 text file containing lines like 账号：name and 密码：secret.
  --username VALUE            Username. Prefer env YIZHAN_USERNAME over putting this in command history.
  --password VALUE            Password. Prefer env YIZHAN_PASSWORD over putting this in command history.
  --target-school VALUE       Expected backend school name used for identity confirmation.
  --out PATH                  JSON result path. The result never includes credentials, cookies, or tokens.
  --open-browser              After API login, open a temporary authenticated browser for same-run manual checks.
  --profile-dir PATH          Optional browser profile dir for --open-browser. Avoid persisting it after the run.
  --browser-executable PATH   Optional Chrome/Edge executable path.
  --headless                  Run browser without a visible window when --open-browser is used.
  --headed                    Run visible browser. Default.
  --keep-open-ms NUMBER       Keep the browser open after injection, useful for manual fallback.
`);
}

function findBrowserExecutable() {
  const candidates = [
    path.join(os.homedir(), "AppData", "Local", "Google", "Chrome", "Application", "chrome.exe"),
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
  ];
  return candidates.find((candidate) => fs.existsSync(candidate)) || null;
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

  return {
    username,
    password,
    credentialSource: credentialPath ? path.basename(credentialPath) : "env_or_args",
  };
}

function backendSchoolFromUser(user) {
  return (
    user?.organization?.model?.name ||
    user?.organization?.org_name ||
    user?.school_name ||
    null
  );
}

async function apiLogin(args, credentials) {
  if (!credentials.username || !credentials.password) {
    return { ok: false, reason: "credentials_missing" };
  }

  const response = await fetch(`${args.apiBase.replace(/\/$/, "")}/api/login_platform`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      accept: "application/json",
    },
    body: JSON.stringify({
      username: credentials.username,
      password: credentials.password,
    }),
  });

  const text = await response.text();
  let payload;
  try {
    payload = JSON.parse(text);
  } catch {
    return { ok: false, reason: `api_non_json_response_${response.status}` };
  }

  if (payload.code !== 200 || !payload.data?.token || !payload.data?.user) {
    return {
      ok: false,
      reason: `api_login_failed_${payload.code || response.status}`,
      message: payload.message || null,
    };
  }

  return {
    ok: true,
    token: payload.data.token,
    user: payload.data.user,
    backendSchool: backendSchoolFromUser(payload.data.user),
    expiresIn: payload.data.expires_in || null,
  };
}

function buildPersistedUserState(user, token) {
  const userInfo = { ...user, token };
  return {
    user: {
      userInfo,
      userReadingHistory: { isTip: 0, id: 0 },
    },
  };
}

async function openAuthenticatedBrowser(args, login) {
  const { chromium } = require("playwright");
  const tempProfile = !args.profileDir;
  const profileDir = args.profileDir
    ? path.resolve(args.profileDir)
    : fs.mkdtempSync(path.join(os.tmpdir(), "yizhan-login-profile-"));
  const executablePath = args.browserExecutable || findBrowserExecutable();

  let context;
  try {
    context = await chromium.launchPersistentContext(profileDir, {
      headless: args.headless,
      executablePath: executablePath || undefined,
      viewport: { width: 1365, height: 900 },
      ignoreHTTPSErrors: true,
      acceptDownloads: false,
      locale: "zh-CN",
    });

    const page = context.pages()[0] || await context.newPage();
    page.setDefaultTimeout(args.timeoutMs);
    await page.goto(args.site, { waitUntil: "domcontentloaded", timeout: args.timeoutMs });
    const browserOriginUrl = page.url();
    await page.evaluate((state) => {
      window.localStorage.setItem("YSY_USEYSYUSERSTORE", JSON.stringify(state));
    }, buildPersistedUserState(login.user, login.token));
    await page.goto(new URL("/home/", browserOriginUrl).toString(), {
      waitUntil: "domcontentloaded",
      timeout: args.timeoutMs,
    });
    await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});

    const hasPasswordInput = await page.locator("input[type='password']").first().isVisible().catch(() => false);
    const text = await page.locator("body").innerText({ timeout: 5000 }).catch(() => "");
    const schoolVisible = login.backendSchool ? text.includes(login.backendSchool) : false;

    if (args.keepOpenMs > 0) await page.waitForTimeout(args.keepOpenMs);

    return {
      ok: !hasPasswordInput,
      currentUrl: page.url(),
      schoolVisible,
      profileDir: tempProfile ? null : profileDir,
    };
  } finally {
    if (context) await context.close().catch(() => {});
    if (tempProfile) fs.rmSync(profileDir, { recursive: true, force: true });
  }
}

async function run() {
  const args = parseArgs(process.argv.slice(2));
  const credentials = readCredentials(args);
  const startedAt = new Date().toISOString();
  const result = {
    status: "fail",
    site: args.site,
    api_base: args.apiBase,
    method: "api_login_platform",
    credential_source: credentials.credentialSource,
    target_school: args.targetSchool || null,
    backend_school: null,
    authenticated: false,
    browser_opened: false,
    browser_current_url: null,
    browser_school_visible: null,
    reason: null,
    started_at: startedAt,
    finished_at: null,
  };

  try {
    const login = await apiLogin(args, credentials);
    if (!login.ok) {
      result.reason = login.reason;
      if (login.message) result.message = login.message;
    } else {
      result.backend_school = login.backendSchool;
      result.authenticated = true;

      if (!login.backendSchool) {
        result.reason = "authenticated_but_school_not_confirmed";
      } else if (args.targetSchool && login.backendSchool !== args.targetSchool) {
        result.reason = "backend_school_mismatch";
      } else {
        result.status = "ok";
      }

      if (args.openBrowser && result.status === "ok") {
        const browser = await openAuthenticatedBrowser(args, login);
        result.browser_opened = true;
        result.browser_current_url = browser.currentUrl;
        result.browser_school_visible = browser.schoolVisible;
        if (!browser.ok) {
          result.status = "fail";
          result.reason = "browser_session_injection_failed";
        }
      }
    }
  } catch (error) {
    result.reason = error && error.message ? error.message : String(error);
  } finally {
    result.finished_at = new Date().toISOString();
  }

  if (args.out) {
    const outPath = path.resolve(args.out);
    fs.mkdirSync(path.dirname(outPath), { recursive: true });
    fs.writeFileSync(outPath, `${JSON.stringify(result, null, 2)}\n`, "utf8");
  }

  console.log(JSON.stringify(result, null, 2));
  process.exitCode = result.status === "ok" ? 0 : 2;
}

run().catch((error) => {
  console.error(error && error.stack ? error.stack : error);
  process.exit(1);
});
