import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path


REQUIRED_PY_MODULES = ["openpyxl", "docx"]


def module_available(name):
    return importlib.util.find_spec(name) is not None


def find_browser():
    candidates = [
        Path.home() / "AppData/Local/Google/Chrome/Application/chrome.exe",
        Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
        Path("C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"),
        Path("C:/Program Files/Microsoft/Edge/Application/msedge.exe"),
        Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
    ]
    for path in candidates:
        if path.exists():
            return str(path)
    for exe in ("google-chrome", "chrome", "chromium", "chromium-browser", "msedge"):
        found = shutil.which(exe)
        if found:
            return found
    return None


def find_executable(name):
    return shutil.which(name)


def maybe_install(missing):
    pip_names = {"docx": "python-docx", "openpyxl": "openpyxl"}
    packages = [pip_names[m] for m in missing if m in pip_names]
    if not packages:
        return
    subprocess.run([sys.executable, "-m", "pip", "install", *packages], check=True)


def main():
    parser = argparse.ArgumentParser(description="Preflight check for yizhan-usage-report workflow.")
    parser.add_argument("--input-dir", default="input", help="Run input directory.")
    parser.add_argument("--output-dir", default="output", help="Run output directory.")
    parser.add_argument("--xlsx", default=None, help="Optional explicit monthly statistics Excel path.")
    parser.add_argument("--website-data", default=None, help="Optional pre-collected website_data.json path.")
    parser.add_argument("--install", action="store_true", help="Install missing Python packages with pip when possible.")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    issues = []
    warnings = []

    if not input_dir.exists():
        issues.append(f"input directory does not exist: {input_dir}")

    if args.xlsx:
        xlsx_files = [Path(args.xlsx)]
    elif input_dir.exists():
        xlsx_files = sorted(input_dir.glob("*.xlsx"))
        preferred = [p for p in xlsx_files if "统计查询按月" in p.name]
        if preferred:
            xlsx_files = preferred
    else:
        xlsx_files = []

    if not xlsx_files:
        issues.append("monthly statistics Excel not found; expected an .xlsx file, preferably containing 统计查询按月 in the filename")
        selected_xlsx = None
    elif len(xlsx_files) > 1 and not args.xlsx:
        issues.append("multiple candidate Excel files found; pass --xlsx explicitly")
        selected_xlsx = None
    else:
        selected_xlsx = xlsx_files[0]
        if not selected_xlsx.exists():
            issues.append(f"Excel file does not exist: {selected_xlsx}")

    missing_modules = [m for m in REQUIRED_PY_MODULES if not module_available(m)]
    if missing_modules and args.install:
        maybe_install(missing_modules)
        missing_modules = [m for m in REQUIRED_PY_MODULES if not module_available(m)]
    if missing_modules:
        issues.append(f"missing Python modules: {', '.join(missing_modules)}; install with: python -m pip install openpyxl python-docx")

    browser = find_browser()
    if not browser:
        warnings.append("Chrome/Edge browser not found. Task 3 can still run the API login helper, but cannot open an authenticated browser session; ask the user to log in manually if browser-only collection is required.")

    node = find_executable("node")
    npm = find_executable("npm")
    if not node or not npm:
        warnings.append("Node.js/npm not found. Task 3 stable API login helper cannot run; ask the user to log in manually or provide website_data.json.")

    website_data = Path(args.website_data) if args.website_data else output_dir / "website_data.json"
    website_data_status = "provided" if website_data.exists() else "missing"

    result = {
        "status": "fail" if issues else "ok",
        "issues": issues,
        "warnings": warnings,
        "input_dir": str(input_dir.resolve()) if input_dir.exists() else str(input_dir),
        "output_dir": str(output_dir.resolve()),
        "selected_xlsx": str(selected_xlsx.resolve()) if selected_xlsx else None,
        "website_data": str(website_data.resolve()) if website_data.exists() else str(website_data),
        "website_data_status": website_data_status,
        "browser": browser,
        "node": node,
        "npm": npm,
        "python": sys.version.split()[0],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
