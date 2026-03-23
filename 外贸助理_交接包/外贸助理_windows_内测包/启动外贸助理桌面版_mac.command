#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d ".venv" ]; then
  osascript -e 'display dialog "未检测到 .venv 环境，请先双击运行：安装依赖_mac.command" buttons {"确定"} default button "确定"'
  exit 1
fi

source .venv/bin/activate
python -m app.main desktop
