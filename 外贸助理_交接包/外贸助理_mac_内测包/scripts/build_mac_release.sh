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
BUILD_VENV="$ROOT_DIR/.venv-build"

echo "==> Create build virtualenv"
rm -rf "$BUILD_VENV"
python3 -m venv "$BUILD_VENV"
source "$BUILD_VENV/bin/activate"

echo "==> Install build dependencies"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller pystray pillow

if [[ "$SKIP_TESTS" != "1" ]]; then
  echo "==> Run tests"
  python -m pytest -q
fi

echo "==> Build InVault executable (PyInstaller spec)"
python -m PyInstaller \
  --noconfirm \
  --clean \
  build/InVault.spec

echo "==> Assemble beta package"
mkdir -p "$RELEASE_ROOT"
rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR"
cp "dist/InVault" "$STAGE_DIR/InVault"
chmod +x "$STAGE_DIR/InVault"
cp -R "extension" "$STAGE_DIR/extension"
cp "README.md" "$STAGE_DIR/README.md"
cp "GUIDE_MAC_FIRST_USE.txt" "$STAGE_DIR/GUIDE_MAC_FIRST_USE.txt"
cat > "$STAGE_DIR/Launch_InVault_Mac.command" <<'EOF'
#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
if [ ! -x "./InVault" ]; then
  osascript -e 'display dialog "未找到 InVault 可执行文件，请重新解压内测包。" buttons {"确定"} default button "确定"'
  exit 1
fi
exec ./InVault
EOF
cat > "$STAGE_DIR/启动外贸助理桌面版_mac.command" <<'EOF'
#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
exec ./Launch_InVault_Mac.command
EOF
chmod +x "$STAGE_DIR/Launch_InVault_Mac.command" "$STAGE_DIR/启动外贸助理桌面版_mac.command"

echo "==> Create zip"
rm -f "$ZIP_PATH"
if command -v zip >/dev/null 2>&1; then
  (cd "$RELEASE_ROOT" && zip -r "$(basename "$ZIP_PATH")" "$(basename "$STAGE_DIR")")
else
  python - "$RELEASE_ROOT" "$(basename "$STAGE_DIR")" "$ZIP_PATH" <<'PY'
import os
import pathlib
import sys
import zipfile

release_root = pathlib.Path(sys.argv[1])
stage_name = sys.argv[2]
zip_path = pathlib.Path(sys.argv[3])
stage_dir = release_root / stage_name

with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for root, _, files in os.walk(stage_dir):
        for f in files:
            p = pathlib.Path(root) / f
            zf.write(p, p.relative_to(release_root))
PY
fi

echo "==> Skip dmg in beta zip mode"

echo
echo "Build completed."
echo "Stage dir: $STAGE_DIR"
echo "Zip file : $ZIP_PATH"
