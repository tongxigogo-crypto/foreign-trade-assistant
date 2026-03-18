param(
    [string]$RunDate = (Get-Date -Format "yyyy-MM-dd"),
    [switch]$ConfirmWrites
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$orchestrator = Join-Path $root "trade_ops\orchestrator.py"

$args = @(
    "`"$orchestrator`"",
    "--root", "`"$root`"",
    "--date", $RunDate,
    "--pretty"
)

if ($ConfirmWrites) {
    $args += "--confirm-writes"
}

python @args
