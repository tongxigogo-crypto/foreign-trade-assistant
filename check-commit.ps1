param(
    [string]$RepoRoot = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Push-Location $RepoRoot
try {
    $statusLines = @(git status --short)

    if ($statusLines.Count -eq 0) {
        Write-Host "git status --short: clean"
        Write-Host "Decision: no commit needed."
        exit 0
    }

    $noisePatterns = @(
        '(^|\\|/)__pycache__(\\|/|$)',
        '(^|\\|/)\\.venv(\\|/|$)',
        '(^|\\|/)\\.venv-build(\\|/|$)',
        '(^|\\|/)(build|dist|release)(\\|/|$)',
        '(^|\\|/)local_data(\\|/|$)',
        '(^|\\|/)website[\\/]+assets[\\/]+downloads(\\|/|$)',
        '\\.pyc$',
        '\\.pyo$',
        '\\.log$',
        '\\.zip$'
    )

    $noiseLines = New-Object System.Collections.Generic.List[string]
    $candidateLines = New-Object System.Collections.Generic.List[string]

    foreach ($line in $statusLines) {
        if ($line -match '^\s*[MARCDU\?\!]{1,2}\s+') {
            $path = $line.Substring(3).Trim()
        } else {
            $path = $line.Trim()
        }

        $isNoise = $false
        foreach ($pattern in $noisePatterns) {
            if ($path -match $pattern) {
                $isNoise = $true
                break
            }
        }

        if ($isNoise) {
            $noiseLines.Add($line)
        } else {
            $candidateLines.Add($line)
        }
    }

    Write-Host "git status --short:"
    $statusLines | ForEach-Object { Write-Host $_ }
    Write-Host ""

    if ($candidateLines.Count -gt 0 -and $noiseLines.Count -eq 0) {
        Write-Host "Decision: commit checkpoint candidate."
        Write-Host "Reason: changes are not just noise."
        exit 0
    }

    if ($candidateLines.Count -gt 0 -and $noiseLines.Count -gt 0) {
        Write-Host "Decision: mixed status."
        Write-Host "Action: separate stable feature changes from noise before committing."
        exit 0
    }

    Write-Host "Decision: cleanup only."
    Write-Host "Reason: status is mostly noise or generated files."
}
finally {
    Pop-Location
}
