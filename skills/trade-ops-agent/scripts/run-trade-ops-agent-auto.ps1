param(
    [string]$WorkspaceRoot = "",
    [string]$RunDate = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
if ([string]::IsNullOrWhiteSpace($WorkspaceRoot)) {
    $WorkspaceRoot = Join-Path $projectRoot "trade_ops"
}

$runner = Join-Path $PSScriptRoot "run-trade-ops-agent.ps1"
$selfImprove = Join-Path $projectRoot "scripts\auto_self_improve.ps1"

$status = "success"
$notes = @()

try {
    & $runner -WorkspaceRoot $WorkspaceRoot -RunDate $RunDate
} catch {
    $status = "failure"
    $notes += $_.Exception.Message
    throw
} finally {
    if (Test-Path $selfImprove) {
        $category = if ($status -eq "success") { "success" } else { "failure" }
        & $selfImprove -Category $category -Trigger "trade_ops_pipeline" -Status $status -Notes $notes -Scope "foreign_trade_assistant"
    }
}
