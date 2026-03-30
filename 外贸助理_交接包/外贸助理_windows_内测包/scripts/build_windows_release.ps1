param(
    [string]$Version = (Get-Date -Format "yyyyMMdd"),
    [switch]$SkipTests
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$workspaceRoot = (Resolve-Path (Join-Path $root "..\..")).Path

function Resolve-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return "py -3"
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return "python"
    }
    throw "Python 3.11+ not found."
}

function Invoke-Checked([scriptblock]$Action) {
    & $Action
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE"
    }
}

function Run-Step([string]$Title, [scriptblock]$Action) {
    Write-Host "==> $Title" -ForegroundColor Cyan
    & $Action
}

$pyCmd = Resolve-PythonCommand
$buildVenv = Join-Path $root ".venv-build"
$releaseRoot = Join-Path $root "release"
$stageDir = Join-Path $releaseRoot ("TA_Beta_{0}_windows" -f $Version)
$zipPath = Join-Path $releaseRoot ("TA_Beta_{0}_windows.zip" -f $Version)

Run-Step "Runtime audit gate (auto)" {
    Push-Location $workspaceRoot
    try {
        Invoke-Expression "$pyCmd -m agent_system.runtime --root `"$workspaceRoot`" --run-id `"build-gate-win-$Version`" --mode preview --audit-level auto" | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "Runtime audit gate failed."
        }
    }
    finally {
        Pop-Location
    }
}

Run-Step "Create build virtualenv" {
    if (Test-Path $buildVenv) {
        Remove-Item -Recurse -Force $buildVenv
    }
    Invoke-Expression "$pyCmd -m venv `"$buildVenv`""
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create build venv."
    }
}

$python = Join-Path $buildVenv "Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Build python executable missing: $python"
}

Run-Step "Install build dependencies" {
    Invoke-Checked { & $python -m pip install --upgrade pip }
    Invoke-Checked { & $python -m pip install -r requirements.txt pyinstaller pystray pillow }
}

if (-not $SkipTests) {
    Run-Step "Run tests" {
        Invoke-Checked { & $python -m pytest -q }
    }
}

Run-Step "Build InVault executable (PyInstaller spec)" {
    Invoke-Checked {
        & $python -m PyInstaller --noconfirm --clean "build\InVault.spec"
    }
}

Run-Step "Assemble beta package" {
    if (Test-Path $stageDir) {
        Remove-Item -Recurse -Force $stageDir
    }
    New-Item -ItemType Directory -Path $stageDir | Out-Null
    if (-not (Test-Path "dist\InVault.exe")) {
        throw "Missing build output: dist\\InVault.exe"
    }
    Copy-Item -Force "dist\InVault.exe" (Join-Path $stageDir "InVault.exe")
    Copy-Item -Recurse -Force "extension" (Join-Path $stageDir "extension")
    Copy-Item -Force "GUIDE_WINDOWS_FIRST_USE.txt" (Join-Path $stageDir "GUIDE_WINDOWS_FIRST_USE.txt")
    Copy-Item -Force "README.md" (Join-Path $stageDir "README.md")
    @'
@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist "InVault.exe" (
  echo [ERROR] InVault.exe not found.
  pause
  exit /b 1
)
start "" "InVault.exe" cli desktop
'@ | Set-Content -Encoding UTF8 (Join-Path $stageDir "Launch_InVault_Windows.bat")
    @'
@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist "InVault.exe" (
  echo [ERROR] InVault.exe not found.
  pause
  exit /b 1
)
start "" "InVault.exe"
'@ | Set-Content -Encoding UTF8 (Join-Path $stageDir "Launch_InVault_Tray.bat")
}

Run-Step "Create zip" {
    if (Test-Path $zipPath) {
        Remove-Item -Force $zipPath
    }
    Compress-Archive -Path "$stageDir\*" -DestinationPath $zipPath -Force
}

Write-Host ""
Write-Host "Build completed." -ForegroundColor Green
Write-Host "Stage dir: $stageDir"
Write-Host "Zip file : $zipPath"
