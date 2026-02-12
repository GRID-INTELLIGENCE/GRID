# PowerShell wrapper script for collecting interfaces metrics
# Usage: .\scripts\collect_interfaces_metrics.ps1 [--days N] [--prototype] [--databricks]

param(
    [int]$Days = 7,
    [switch]$Prototype,
    [switch]$Databricks
)

$ErrorActionPreference = "Stop"

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$CollectScript = Join-Path $ProjectRoot "tools" "collect_interfaces_metrics.py"

# Build arguments
$Arguments = @()

if ($Days) {
    $Arguments += "--days", $Days
}

if ($Prototype) {
    $Arguments += "--prototype"
}

if ($Databricks) {
    $Arguments += "--databricks"
}

# Run collection script
Write-Host "Collecting interfaces metrics..." -ForegroundColor Cyan
Write-Host "Script: $CollectScript" -ForegroundColor Gray
Write-Host "Arguments: $($Arguments -join ' ')" -ForegroundColor Gray
Write-Host ""

try {
    python $CollectScript @Arguments
    $ExitCode = $LASTEXITCODE

    if ($ExitCode -eq 0) {
        Write-Host "`nCollection completed successfully!" -ForegroundColor Green
    } else {
        Write-Host "`nCollection failed with exit code $ExitCode" -ForegroundColor Red
        exit $ExitCode
    }
} catch {
    Write-Host "`nError running collection script: $_" -ForegroundColor Red
    exit 1
}
