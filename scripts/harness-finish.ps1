param(
    [string]$WorkspaceRoot = "",
    [string]$RunId = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($WorkspaceRoot)) {
    $WorkspaceRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

if ([string]::IsNullOrWhiteSpace($RunId)) {
    $RunId = "finish-" + (Get-Date -Format "yyyyMMdd-HHmmss")
}

$checkScript = Join-Path $WorkspaceRoot "scripts\check-core-context.ps1"
if (Test-Path $checkScript) {
    & powershell -ExecutionPolicy Bypass -File $checkScript | Out-Null
}

Write-Host "==> harness quick checkpoint: $RunId" -ForegroundColor Cyan
$runtimePy = Join-Path $WorkspaceRoot "agent_system\runtime.py"
$summary = "harness finish checkpoint completed"
$status = "success"

if (Test-Path $runtimePy) {
    Push-Location $WorkspaceRoot
    try {
        & python -m agent_system.runtime --root $WorkspaceRoot --run-id $RunId --mode preview --audit-level quick | Out-Null
        $code = $LASTEXITCODE
        if ($code -ne 0 -and (Get-Command py -ErrorAction SilentlyContinue)) {
            & py -3 -m agent_system.runtime --root $WorkspaceRoot --run-id $RunId --mode preview --audit-level quick | Out-Null
            $code = $LASTEXITCODE
        }
        if ($code -ne 0) {
            $status = "failed"
            $summary = "runtime checkpoint failed; fallback to memory-only writeback"
        }
        else {
            $reportPath = Join-Path $WorkspaceRoot ("agent_system\output\run-report-{0}.json" -f $RunId)
            if (Test-Path $reportPath) {
                $report = Get-Content $reportPath -Raw -Encoding UTF8 | ConvertFrom-Json
                $inc = ($report.incremental_summary -join " | ")
                if (-not [string]::IsNullOrWhiteSpace($inc)) {
                    $summary = $inc
                }
            }
        }
    }
    finally {
        Pop-Location
    }
}
else {
    $status = "degraded"
    $summary = "agent_system/runtime.py missing; memory-only writeback applied"
}

$recordScript = Join-Path $WorkspaceRoot "scripts\record-self-improving.ps1"
if (Test-Path $recordScript) {
    & powershell -ExecutionPolicy Bypass -File $recordScript -WorkspaceRoot $WorkspaceRoot -Category "harness-finish" -Status $status -Summary $summary | Out-Null
}

Write-Output "harness_finish=ok"
Write-Output ("run_id=" + $RunId)
