param(
    [string]$RunId = "",
    [switch]$ConfirmWrites
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$orchestrator = Join-Path $root "site_ops\orchestrator.py"

$args = @(
    "`"$orchestrator`"",
    "--root", "`"$root`"",
    "--pretty"
)

if ($RunId) {
    $args += @("--run-id", $RunId)
}

if ($ConfirmWrites) {
    $args += "--confirm-writes"
}

python @args
