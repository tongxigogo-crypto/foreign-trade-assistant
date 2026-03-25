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

# Beta default: do not package unsigned InVault binary to avoid Gatekeeper hard block.
USE_PYINSTALLER="${USE_PYINSTALLER:-0}"

echo "==> Create build virtualenv"
rm -rf "$BUILD_VENV"
python3 -m venv "$BUILD_VENV"
source "$BUILD_VENV/bin/activate"

echo "==> Install build dependencies"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pystray pillow
if [[ "$USE_PYINSTALLER" == "1" ]]; then
  python -m pip install pyinstaller
fi

if [[ "$SKIP_TESTS" != "1" ]]; then
  echo "==> Run tests"
  python -m pytest -q
fi

echo "==> Assemble beta package"
mkdir -p "$RELEASE_ROOT"
rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR"

cp -R "app" "$STAGE_DIR/app"
cp -R "extension" "$STAGE_DIR/extension"
[[ -d "config" ]] && cp -R "config" "$STAGE_DIR/config"
[[ -d "docs" ]] && cp -R "docs" "$STAGE_DIR/docs"
cp "README.md" "$STAGE_DIR/README.md"
cp "requirements.txt" "$STAGE_DIR/requirements.txt"

if [[ -f "Launch_InVault_Mac.command" ]]; then
  cp "Launch_InVault_Mac.command" "$STAGE_DIR/Launch_InVault_Mac.command"
fi
if [[ -f "安装依赖_mac.command" ]]; then
  cp "安装依赖_mac.command" "$STAGE_DIR/安装依赖_mac.command"
fi
if [[ -f "启动外贸助理桌面版_mac.command" ]]; then
  cp "启动外贸助理桌面版_mac.command" "$STAGE_DIR/启动外贸助理桌面版_mac.command"
fi
if [[ -f "新手必读_首次安装与使用.txt" ]]; then
  cp "新手必读_首次安装与使用.txt" "$STAGE_DIR/新手必读_首次安装与使用.txt"
elif [[ -f "GUIDE_MAC_FIRST_USE.txt" ]]; then
  cp "GUIDE_MAC_FIRST_USE.txt" "$STAGE_DIR/GUIDE_MAC_FIRST_USE.txt"
fi

chmod +x "$STAGE_DIR"/*.command 2>/dev/null || true

if [[ "$USE_PYINSTALLER" == "1" ]]; then
  echo "==> Build InVault executable (optional)"
  python -m PyInstaller --noconfirm --clean build/InVault.spec
  if [[ -f "dist/InVault" ]]; then
    cp "dist/InVault" "$STAGE_DIR/InVault"
    chmod +x "$STAGE_DIR/InVault"
  fi
fi

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

echo
echo "Build completed."
echo "Stage dir: $STAGE_DIR"
echo "Zip file : $ZIP_PATH"
echo "USE_PYINSTALLER=$USE_PYINSTALLER"
