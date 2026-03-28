param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path,
    [string]$RunId = "agent-architecture-run",
    [string]$Query = "agent architecture guardrails harness recovery",
    [ValidateSet("preview", "confirm_write")]
    [string]$Mode = "preview"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Push-Location $RepoRoot
try {
    python -m agent_system.runtime --root $RepoRoot --run-id $RunId --query $Query --mode $Mode --pretty
}
finally {
    Pop-Location
}
