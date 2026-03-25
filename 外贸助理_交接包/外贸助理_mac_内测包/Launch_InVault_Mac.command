#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "[InVault] preparing mac launch..."

# Remove Gatekeeper quarantine flag for this folder (best effort).
if command -v xattr >/dev/null 2>&1; then
  xattr -dr com.apple.quarantine "$SCRIPT_DIR" 2>/dev/null || true
fi

# Ensure all command launchers are executable.
chmod +x "$SCRIPT_DIR"/*.command 2>/dev/null || true

# If packaged binary exists, prefer it.
if [ -x "$SCRIPT_DIR/InVault" ]; then
  exec "$SCRIPT_DIR/InVault"
fi

INSTALL_SCRIPT=""
if [ -f "$SCRIPT_DIR/安装依赖_mac.command" ]; then
  INSTALL_SCRIPT="$SCRIPT_DIR/安装依赖_mac.command"
elif [ -f "$SCRIPT_DIR/install_mac.command" ]; then
  INSTALL_SCRIPT="$SCRIPT_DIR/install_mac.command"
fi

READY_FLAG="$SCRIPT_DIR/.venv/.invault_ready_v1"
if [ ! -f "$READY_FLAG" ]; then
  if [ -n "$INSTALL_SCRIPT" ]; then
    echo "[InVault] first run, installing dependencies..."
    bash "$INSTALL_SCRIPT"
  fi
fi

if [ -x "$SCRIPT_DIR/.venv/bin/python" ]; then
  exec "$SCRIPT_DIR/.venv/bin/python" -m app.main desktop
fi

if command -v python3 >/dev/null 2>&1; then
  exec python3 -m app.main desktop
fi

echo "[ERROR] Python runtime not found."
echo "Please run: 安装依赖_mac.command"
exit 1
