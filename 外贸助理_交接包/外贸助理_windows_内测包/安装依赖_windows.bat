@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
  where python >nul 2>nul
  if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.11+（勾选 Add Python to PATH）。
    pause
    exit /b 1
  )
  set "PY_CMD=python"
) else (
  set "PY_CMD=py -3"
)

echo [1/5] 创建虚拟环境 .venv ...
%PY_CMD% -m venv .venv
if errorlevel 1 (
  echo [错误] 创建虚拟环境失败。
  pause
  exit /b 1
)

call ".venv\Scripts\activate.bat"

echo [2/5] 升级 pip ...
python -m pip install --upgrade pip
if errorlevel 1 (
  echo [错误] pip 升级失败。
  pause
  exit /b 1
)

echo [3/5] 安装依赖 requirements.txt ...
pip install -r requirements.txt
if errorlevel 1 (
  echo [错误] 依赖安装失败。
  pause
  exit /b 1
)

echo [4/5] 初始化本地数据目录 ...
python -m app.main init
if errorlevel 1 (
  echo [错误] 初始化失败。
  pause
  exit /b 1
)

echo [5/5] 完成。下一步请双击：启动外贸助理桌面版_windows.bat
pause
