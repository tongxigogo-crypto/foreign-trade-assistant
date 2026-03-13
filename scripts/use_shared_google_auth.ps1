$ErrorActionPreference = "Stop"

$sharedScript = "E:\CodexWorkspace\Playground\shared_google_auth\use_shared_token.ps1"

if (-not (Test-Path $sharedScript)) {
  throw "Shared auth script not found: $sharedScript"
}

. $sharedScript

Write-Host "foreign_trade_assistant is now using the shared Google authorization in this shell."
