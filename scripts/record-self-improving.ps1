param(
    [string]$WorkspaceRoot = "",
    [string]$Category = "general",
    [string]$Status = "success",
    [string]$Summary = "",
    [switch]$AutoCommit
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($WorkspaceRoot)) {
    $WorkspaceRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

$memoryDir = Join-Path $WorkspaceRoot "docs\memory"
$memoryPath = Join-Path $memoryDir "self_improving_agent.md"
New-Item -ItemType Directory -Force -Path $memoryDir | Out-Null

if (-not (Test-Path $memoryPath)) {
    Set-Content -Path $memoryPath -Encoding UTF8 -Value "# Self Improving Agent Memory`n"
}

$timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
$entry = @"

## [$timestamp] $Category

- status: $Status
- summary: $Summary
"@
Add-Content -Path $memoryPath -Value $entry -Encoding UTF8

if ($AutoCommit) {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Warning "AUTO_COMMIT_SKIPPED: git not found."
        return
    }

    try {
        & git -C $WorkspaceRoot rev-parse --is-inside-work-tree *> $null
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "AUTO_COMMIT_SKIPPED: not a git repository."
            return
        }

        & git -C $WorkspaceRoot add -A
        & git -C $WorkspaceRoot diff --cached --quiet
        if ($LASTEXITCODE -eq 1) {
            $msg = "chore(self-improving): $Status $Category $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
            & git -C $WorkspaceRoot commit -m $msg *> $null
            if ($LASTEXITCODE -eq 0) {
                Write-Output "AUTO_COMMIT_OK: $msg"
            } else {
                Write-Warning "AUTO_COMMIT_FAILED: git commit returned exit code $LASTEXITCODE."
            }
        } else {
            Write-Output "AUTO_COMMIT_SKIPPED: no staged changes."
        }
    } catch {
        Write-Warning "AUTO_COMMIT_FAILED: $($_.Exception.Message)"
    }
}

