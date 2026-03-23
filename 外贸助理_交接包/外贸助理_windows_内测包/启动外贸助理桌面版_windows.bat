@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [提示] 未检测到 .venv，请先双击运行：安装依赖_windows.bat
  pause
  exit /b 1
)

call ".venv\Scripts\activate.bat"
python -m app.main desktop
set "APP_EXIT=%errorlevel%"

if not "%APP_EXIT%"=="0" (
  echo [提示] 桌面版已退出，错误码：%APP_EXIT%
  pause
)

exit /b %APP_EXIT%
