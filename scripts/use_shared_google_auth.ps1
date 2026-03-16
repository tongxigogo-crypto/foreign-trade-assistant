$ErrorActionPreference = "Stop"
$token = gcloud auth application-default print-access-token
$env:GOOGLE_WORKSPACE_CLI_TOKEN = $token
Write-Host "GOOGLE_WORKSPACE_CLI_TOKEN loaded for current shell."
