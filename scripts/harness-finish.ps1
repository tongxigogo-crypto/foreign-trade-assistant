param(
    [string]$RepoRoot = (Get-Location).Path,
    [string]$ActiveTask = "",
    [string]$CurrentGoal = "",
    [string[]]$Progress = @(),
    [string[]]$Blockers = @(),
    [string[]]$NextActions = @(),
    [string]$Summary = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Format-ListSection {
    param([string[]]$Items)
    if ($null -eq $Items -or $Items.Count -eq 0) {
        return "- None"
    }
    return (($Items | ForEach-Object { "- $_" }) -join "`n")
}

Push-Location $RepoRoot
try {
    $harnessDir = Join-Path $RepoRoot 'docs\harness'
    $memoryDir = Join-Path $RepoRoot 'docs\memory'
    $sessionJson = Join-Path $harnessDir 'session_state.json'
    $sessionMd = Join-Path $harnessDir 'current_session.md'
    $memoryMd = Join-Path $memoryDir 'self_improving_agent.md'

    New-Item -ItemType Directory -Force -Path $harnessDir | Out-Null
    New-Item -ItemType Directory -Force -Path $memoryDir | Out-Null

    $timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:sszzz")
    $state = [ordered]@{
        updated_at = $timestamp
        active_task = $ActiveTask
        current_goal = $CurrentGoal
        progress = @($Progress)
        blockers = @($Blockers)
        next_actions = @($NextActions)
        last_git_status = (@(git status --short) -join "`n")
    }

    ($state | ConvertTo-Json -Depth 8) | Set-Content -Path $sessionJson -Encoding UTF8

    $activeTaskLine = if ([string]::IsNullOrWhiteSpace($ActiveTask)) { "None" } else { $ActiveTask }
    $currentGoalLine = if ([string]::IsNullOrWhiteSpace($CurrentGoal)) { "None" } else { $CurrentGoal }

    $md = @"
# Current Session

## Active Task
- $activeTaskLine

## Current Goal
- $currentGoalLine

## Progress
$(Format-ListSection -Items $Progress)

## Blockers
$(Format-ListSection -Items $Blockers)

## Next Actions
$(Format-ListSection -Items $NextActions)

## Updated At
- $timestamp
"@
    $md | Set-Content -Path $sessionMd -Encoding UTF8

    if (-not [string]::IsNullOrWhiteSpace($Summary)) {
        if (-not (Test-Path $memoryMd)) {
            Set-Content -Path $memoryMd -Encoding UTF8 -Value "# Self Improving Agent Memory`n"
        }
        $entry = @"

## [$timestamp] checkpoint

- status: checkpoint
- summary: $Summary
"@
        Add-Content -Path $memoryMd -Value $entry -Encoding UTF8
    }

    Write-Host "HARNESS_CHECKPOINT_OK"
    Write-Host $sessionJson
    Write-Host $sessionMd
}
finally {
    Pop-Location
}
