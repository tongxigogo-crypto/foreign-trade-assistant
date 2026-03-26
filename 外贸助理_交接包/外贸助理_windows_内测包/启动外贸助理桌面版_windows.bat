@echo off
setlocal

cd /d "%~dp0"

if exist "InVault.exe" (
  start "" "InVault.exe"
  exit /b 0
)

if not exist ".venv\Scripts\pythonw.exe" (
  powershell -NoProfile -Command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('Python environment (.venv) not found. Please run dependency installer first.','Trade Assistant') | Out-Null"
  exit /b 1
)

if not exist "local_data\logs" mkdir "local_data\logs" >nul 2>nul

rem Hidden launch to avoid persistent black cmd window.
powershell -NoProfile -WindowStyle Hidden -Command "Start-Process -FilePath '.\.venv\Scripts\pythonw.exe' -ArgumentList '-m','app.main','desktop' -WorkingDirectory '%CD%' -WindowStyle Hidden"
exit /b 0
