#!/usr/bin/env python3
"""运行校验→构建→渲染的交付流水线。"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run(cmd):
    print("$", " ".join(map(str, cmd)))
    subprocess.run(cmd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="运行远播方案交付流水线")
    parser.add_argument("project_dir")
    args = parser.parse_args()
    project = Path(args.project_dir).resolve()
    scripts = Path(__file__).resolve().parent
    run([sys.executable, scripts / "validate_project.py", project])
    run([sys.executable, scripts / "build_docx.py", project])
    manifest = json.loads((project / "qa/build_manifest.json").read_text(encoding="utf-8"))
    run([sys.executable, scripts / "render_review.py", manifest["output"], "--output-dir", project / "qa/render"])
    print("流水线完成。仍需人工逐页勾选视觉检查清单。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
