#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-$(date +%Y%m%d)}"
SKIP_TESTS="${SKIP_TESTS:-0}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python3 not found." >&2
  exit 1
fi

RELEASE_ROOT="$ROOT_DIR/release"
STAGE_DIR="$RELEASE_ROOT/TA_Beta_${VERSION}_mac"
ZIP_PATH="$RELEASE_ROOT/TA_Beta_${VERSION}_mac.zip"
DMG_PATH="$RELEASE_ROOT/TA_Beta_${VERSION}_mac.dmg"
BUILD_VENV="$ROOT_DIR/.venv-build"
APP_NAME="TradeAssistant"
APP_BUNDLE="$ROOT_DIR/dist/${APP_NAME}.app"

echo "==> Prepare build virtualenv"
rm -rf "$BUILD_VENV"
python3 -m venv "$BUILD_VENV"
source "$BUILD_VENV/bin/activate"
python -m pip install --upgrade pip
PIP_REQ_ARGS=(-r requirements.txt)
if [[ -f requirements-dev.txt ]]; then
  PIP_REQ_ARGS+=(-r requirements-dev.txt)
else
  echo "[WARN] requirements-dev.txt missing; continuing without dev dependencies."
fi
python -m pip install "${PIP_REQ_ARGS[@]}" pyinstaller pystray pillow

if [[ "$SKIP_TESTS" != "1" ]]; then
  echo "==> Run tests"
  python -m pytest -q
fi

echo "==> Build .app with PyInstaller"
rm -rf "$ROOT_DIR/build" "$ROOT_DIR/dist"
python -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name "$APP_NAME" \
  --add-data "app/dashboard_ui.html:app" \
  --add-data "app/dashboard_layout_v2.json:app" \
  "app/desktop_entry.py"

if [[ ! -d "$APP_BUNDLE" ]]; then
  echo "Build failed: app bundle not found: $APP_BUNDLE" >&2
  exit 1
fi

echo "==> Assemble release folder"
mkdir -p "$RELEASE_ROOT"
rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR"

cp -R "$APP_BUNDLE" "$STAGE_DIR/${APP_NAME}.app"
cp -R "extension" "$STAGE_DIR/extension"
if [[ -d "config" ]]; then
  cp -R "config" "$STAGE_DIR/config"
else
  mkdir -p "$STAGE_DIR/config"
  cat > "$STAGE_DIR/config/partner-policy.json" <<'JSON'
{
  "data_dir": "local_data",
  "knowledge_file": "knowledge_base.json",
  "output_dir": "artifacts",
  "state_board_file": "state_board.json",
  "user_settings_file": "user_settings.json"
}
JSON
fi

cat > "$STAGE_DIR/FIRST_USE.txt" <<'TXT'
Trade Assistant for macOS - First Use

1) Open the downloaded DMG.
2) Drag TradeAssistant.app to Applications.
3) Open TradeAssistant.app.
4) If blocked by Gatekeeper:
   - Go to System Settings -> Privacy & Security
   - Click "Open Anyway" for TradeAssistant
   - Open again

Inside app:
1) Click "One-click Start"
2) Click "Open Web Workbench"
TXT

echo "==> Build zip package"
rm -f "$ZIP_PATH"
(cd "$RELEASE_ROOT" && zip -qr "$(basename "$ZIP_PATH")" "$(basename "$STAGE_DIR")")

echo "==> Build dmg package"
rm -f "$DMG_PATH"
hdiutil create -volname "${APP_NAME}" -srcfolder "$STAGE_DIR" -ov -format UDZO "$DMG_PATH" >/dev/null

echo
echo "Build completed."
echo "Stage dir: $STAGE_DIR"
echo "Zip file : $ZIP_PATH"
echo "DMG file : $DMG_PATH"
