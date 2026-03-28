param(
    [string]$RepoRoot = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Read-TextOrEmpty([string]$Path) {
    if (Test-Path $Path) {
        return Get-Content -Path $Path -Raw
    }
    return ""
}

Push-Location $RepoRoot
try {
    $harnessJson = Join-Path $RepoRoot 'docs\harness\session_state.json'
    $sessionMd = Join-Path $RepoRoot 'docs\harness\current_session.md'
    $guardrailJson = Join-Path $RepoRoot 'docs\harness\architecture_guardrails.json'
    $verdictJson = Join-Path $RepoRoot 'docs\harness\closed_loop_verdict.json'
    $latestReport = Get-ChildItem -Path (Join-Path $RepoRoot 'agent_system\output') -Filter 'run-report-*.json' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    $memoryMd = Join-Path $RepoRoot 'docs\memory\self_improving_agent.md'

    $state = $null
    if (Test-Path $harnessJson) {
        $state = Get-Content -Path $harnessJson -Raw | ConvertFrom-Json
    }

    $gitStatus = @(git status --short)

    Write-Host "HARNESS_RESTORE"
    if ($null -ne $state) {
        Write-Host ("active_task: {0}" -f $state.active_task)
        Write-Host ("current_goal: {0}" -f $state.current_goal)
        Write-Host ("updated_at: {0}" -f $state.updated_at)
        if ($state.next_actions) {
            Write-Host "next_actions:"
            $state.next_actions | ForEach-Object { Write-Host ("- {0}" -f $_) }
        }
        if ($state.blockers) {
            Write-Host "blockers:"
            $state.blockers | ForEach-Object { Write-Host ("- {0}" -f $_) }
        }
    } else {
        Write-Host "active_task: <missing harness state>"
    }

    Write-Host ""
    Write-Host "HARNESS_FILES"
    Write-Host $sessionMd
    Write-Host $guardrailJson
    Write-Host $verdictJson
    if ($null -ne $latestReport) {
        Write-Host $latestReport.FullName
    } else {
        Write-Host "<no run report yet>"
    }
    Write-Host $memoryMd
    Write-Host ""
    Write-Host "GIT_STATUS"
    if ($gitStatus.Count -eq 0) {
        Write-Host "clean"
    } else {
        $gitStatus | ForEach-Object { Write-Host $_ }
    }
}
finally {
    Pop-Location
}
