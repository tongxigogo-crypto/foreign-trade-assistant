param(
    [string]$SourceDir = "E:\CodexWorkspace\Playground\foreign_trade_assistant",
    [string]$BackupRoot = "E:\CodexWorkspace\Backups\foreign_trade_assistant",
    [int]$KeepLatest = 16
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $SourceDir)) {
    throw "Source directory not found: $SourceDir"
}

New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$zipPath = Join-Path $BackupRoot "foreign_trade_assistant_$timestamp.zip"
$logPath = Join-Path $BackupRoot "backup.log"

function Write-BackupLog {
    param([string]$Message)
    $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Add-Content -LiteralPath $logPath -Value $line
}

try {
    Write-BackupLog "START backup -> $zipPath"
    Compress-Archive -Path (Join-Path $SourceDir "*") -DestinationPath $zipPath -CompressionLevel Optimal -Force
    $zipInfo = Get-Item -LiteralPath $zipPath
    Write-BackupLog ("DONE backup size={0} bytes" -f $zipInfo.Length)

    $archives = Get-ChildItem -LiteralPath $BackupRoot -Filter "foreign_trade_assistant_*.zip" | Sort-Object LastWriteTime -Descending
    if ($archives.Count -gt $KeepLatest) {
        $toDelete = $archives | Select-Object -Skip $KeepLatest
        foreach ($file in $toDelete) {
            Remove-Item -LiteralPath $file.FullName -Force
            Write-BackupLog "PRUNE old backup -> $($file.Name)"
        }
    }
}
catch {
    Write-BackupLog "ERROR $($_.Exception.Message)"
    throw
}
