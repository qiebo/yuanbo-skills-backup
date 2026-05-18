import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HTML = ROOT / "output" / "report.html"
DEFAULT_PDF = ROOT / "output" / "report.pdf"


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
            return path
    return None


def export_pdf(html_path, pdf_path, browser_path=None):
    html_path = Path(html_path).resolve()
    pdf_path = Path(pdf_path).resolve()
    if not html_path.exists():
        raise FileNotFoundError(html_path)
    browser = Path(browser_path) if browser_path else find_browser()
    if not browser or not browser.exists():
        raise RuntimeError("Chrome/Edge executable not found. Install Chrome/Edge or pass --browser.")
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    url = html_path.as_uri()
    cmd = [
        str(browser),
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        "--print-to-pdf=" + str(pdf_path),
        url,
    ]
    subprocess.run(cmd, check=True)
    if not pdf_path.exists() or pdf_path.stat().st_size == 0:
        raise RuntimeError(f"PDF export failed: {pdf_path}")
    return pdf_path


def main():
    parser = argparse.ArgumentParser(description="Export the Yizhan HTML report to PDF.")
    parser.add_argument("--html", default=str(DEFAULT_HTML), help="Input HTML path.")
    parser.add_argument("--pdf", default=str(DEFAULT_PDF), help="Output PDF path.")
    parser.add_argument("--browser", default=None, help="Optional Chrome/Edge executable path.")
    args = parser.parse_args()
    out = export_pdf(args.html, args.pdf, args.browser)
    print(out)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
