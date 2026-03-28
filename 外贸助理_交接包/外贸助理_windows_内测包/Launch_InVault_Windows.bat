@echo off
setlocal
cd /d "%~dp0"

if exist "%~dp0InVault.exe" (
  start "" "%~dp0InVault.exe"
  exit /b 0
)

if exist "%~dp0dist\\InVault.exe" (
  start "" "%~dp0dist\\InVault.exe"
  exit /b 0
)

if exist "%~dp0.venv\\Scripts\\pythonw.exe" (
  powershell -NoProfile -WindowStyle Hidden -Command "Start-Process -FilePath '.\\.venv\\Scripts\\pythonw.exe' -ArgumentList '-m','app.main','desktop' -WorkingDirectory '%CD%' -WindowStyle Hidden"
  exit /b 0
)

powershell -NoProfile -Command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('Runtime not found. Please run install script first.','Trade Assistant') | Out-Null"
exit /b 1
