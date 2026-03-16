param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$GwsArgs
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $GwsArgs -or $GwsArgs.Count -eq 0) {
    throw "Usage: .\scripts\gws-readonly.ps1 <gws args...>"
}

$blockedPatterns = @(
    "gmail send",
    "gmail draft create",
    "gmail modify",
    "gmail delete",
    "drive upload",
    "drive create",
    "drive move",
    "drive delete",
    "drive trash",
    "drive permission",
    "drive share",
    "drive rename",
    "sheets write",
    "sheets append",
    "docs write",
    "docs append",
    "tasks add",
    "tasks create",
    "tasks update",
    "tasks delete"
)

$cmdLine = ($GwsArgs -join " ").ToLowerInvariant()
foreach ($pattern in $blockedPatterns) {
    if ($cmdLine.Contains($pattern)) {
        throw "Blocked by read-only policy: '$pattern'. Allowed scope is Gmail/Drive read operations only."
    }
}

$env:FTA_GWS_READONLY = "1"
& gws @GwsArgs

