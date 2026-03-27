#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

show_info() {
  /usr/bin/osascript -e "display dialog \"$1\" buttons {\"OK\"} default button \"OK\"" >/dev/null 2>&1 || true
}

show_error() {
  /usr/bin/osascript -e "display dialog \"$1\" buttons {\"OK\"} default button \"OK\" with icon stop" >/dev/null 2>&1 || true
}

echo "[TradeAssistant] preparing launch..."

# Best effort: clear quarantine flag for this folder.
if command -v xattr >/dev/null 2>&1; then
  xattr -dr com.apple.quarantine "$SCRIPT_DIR" 2>/dev/null || true
fi

chmod +x "$SCRIPT_DIR"/*.command 2>/dev/null || true

# Future-proof: if signed binary exists, prefer it.
if [ -x "$SCRIPT_DIR/InVault" ]; then
  exec "$SCRIPT_DIR/InVault"
fi

PYTHON_BIN="$(command -v python3 || true)"
if [ -z "$PYTHON_BIN" ]; then
  show_error "Python3 not found. Please install Python 3.11+ first, then retry."
  echo "[ERROR] python3 not found."
  exit 1
fi

if [ ! -d "$SCRIPT_DIR/.venv" ]; then
  echo "[TradeAssistant] first run: creating virtual environment..."
  "$PYTHON_BIN" -m venv "$SCRIPT_DIR/.venv" || {
    show_error "Failed to create .venv. Please check folder permissions and retry."
    exit 1
  }
fi

echo "[TradeAssistant] installing/updating dependencies..."
"$SCRIPT_DIR/.venv/bin/python" -m pip install --upgrade pip >/dev/null
"$SCRIPT_DIR/.venv/bin/python" -m pip install -r "$SCRIPT_DIR/requirements.txt" || {
  show_error "Dependency install failed. Please check network and retry."
  exit 1
}

"$SCRIPT_DIR/.venv/bin/python" -m app.main init >/dev/null 2>&1 || true

show_info "Launching Trade Assistant Desktop. First launch can take about 30-60 seconds."
exec "$SCRIPT_DIR/.venv/bin/python" -m app.main desktop
