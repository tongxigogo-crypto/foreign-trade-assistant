param(
    [ValidateSet("success", "correction", "failure")]
    [string]$Category = "success",
    [string]$Trigger = "manual",
    [string]$Status = "success",
    [string[]]$Notes = @(),
    [string]$Scope = "foreign_trade_assistant"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$memoryDir = Join-Path $projectRoot "docs\memory"
$memoryPath = Join-Path $memoryDir "self_improving_agent.md"

New-Item -ItemType Directory -Force -Path $memoryDir | Out-Null
if (-not (Test-Path $memoryPath)) {
    Set-Content -Path $memoryPath -Value "# Self Improving Agent Memory`n" -Encoding UTF8
}

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
if (-not $Notes -or $Notes.Count -eq 0) {
    $Notes = @("none")
}
$noteLines = ($Notes | ForEach-Object { "- note: $($_)" }) -join "`n"

$entry = @"
## $timestamp - $Trigger
- Category: $Category
- Trigger: automatic self-improving hook.
- status=$Status
- Scope: $Scope
$noteLines
"@

Add-Content -Path $memoryPath -Value ("`n" + $entry + "`n") -Encoding UTF8
Write-Output "self-improving entry appended: $timestamp"
