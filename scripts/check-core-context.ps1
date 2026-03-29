Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$statusFile = Join-Path $root "status.md"
$harnessDir = Join-Path $root "docs\harness"
$sessionFile = Join-Path $harnessDir "session_state.json"
$currentFile = Join-Path $harnessDir "current_session.md"

if (-not (Test-Path $harnessDir)) {
    New-Item -ItemType Directory -Path $harnessDir -Force | Out-Null
}

if (-not (Test-Path $statusFile)) {
    @"
# 项目状态快照（Status）

更新时间：$(Get-Date -Format "yyyy-MM-dd")
说明：status.md 缺失后由 check-core-context.ps1 自动重建，请在下一轮更新完整进度。
"@ | Set-Content -Path $statusFile -Encoding UTF8
}

if (-not (Test-Path $sessionFile)) {
    $payload = [ordered]@{
        updated_at      = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        active_task     = "ready_for_next_task"
        current_goal    = "resume from status.md and wait for user instruction"
        progress        = @("baseline restored by check-core-context.ps1")
        open_questions  = @()
        blockers        = @()
        next_actions    = @("read AGENTS.md", "read status.md", "wait for task")
        last_git_status = "(pending refresh)"
    }
    $payload | ConvertTo-Json -Depth 6 | Set-Content -Path $sessionFile -Encoding UTF8
}

if (-not (Test-Path $currentFile)) {
    @"
# Current Session

## Active Task
- ready_for_next_task

## Current Goal
- resume from status.md and wait for user instruction

## Progress
- baseline restored by check-core-context.ps1

## Blockers
- None

## Next Actions
- read AGENTS.md
- read status.md
- wait for task
"@ | Set-Content -Path $currentFile -Encoding UTF8
}

Write-Output "core_context_status=ok"
Write-Output "status_path=$statusFile"
Write-Output "session_path=$sessionFile"
Write-Output "current_path=$currentFile"
