# PowerShell wrapper script for running interfaces metrics dashboard prototype
# Usage: .\scripts\run_dashboard_prototype.ps1 [--host HOST] [--port PORT] [--db-path PATH]

param(
    [string]$Host = "localhost",
    [int]$Port = 8080,
    [string]$DbPath = ""
)

$ErrorActionPreference = "Stop"

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$DashboardScript = Join-Path $ProjectRoot "tools" "interfaces_dashboard" "dashboard.py"

# Build arguments
$Arguments = @()

if ($Host) {
    $Arguments += "--host", $Host
}

if ($Port) {
    $Arguments += "--port", $Port
}

if ($DbPath) {
    $Arguments += "--db-path", $DbPath
}

# Run dashboard script
Write-Host "Starting interfaces metrics dashboard..." -ForegroundColor Cyan
Write-Host "Script: $DashboardScript" -ForegroundColor Gray
Write-Host "URL: http://${Host}:${Port}" -ForegroundColor Gray
Write-Host "Arguments: $($Arguments -join ' ')" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Ctrl+C to stop the dashboard" -ForegroundColor Yellow
Write-Host ""

try {
    python $DashboardScript @Arguments
    $ExitCode = $LASTEXITCODE

    if ($ExitCode -ne 0) {
        Write-Host "`nDashboard exited with code $ExitCode" -ForegroundColor Red
        exit $ExitCode
    }
} catch {
    Write-Host "`nError running dashboard: $_" -ForegroundColor Red
    exit 1
}
