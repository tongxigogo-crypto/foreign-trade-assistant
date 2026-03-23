#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_BIN="$(command -v python3 || true)"
if [ -z "$PYTHON_BIN" ]; then
  osascript -e 'display dialog "未检测到 python3，请先安装 Python 3.11+ 后再试。" buttons {"确定"} default button "确定"'
  exit 1
fi

"$PYTHON_BIN" -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m app.main init

osascript -e 'display dialog "依赖安装完成。下一步请双击：启动外贸助理桌面版_mac.command" buttons {"确定"} default button "确定"'
