# PowerShell script to set up Databricks environment variables
# Run this script to configure Databricks for GRID

Write-Host "GRID Databricks Environment Setup" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host ""

# Check if environment variables are already set
$serverHost = $env:DATABRICKS_SERVER_HOSTNAME
$httpPath = $env:DATABRICKS_HTTP_PATH
$accessToken = $env:DATABRICKS_ACCESS_TOKEN

if ($serverHost -and $httpPath -and $accessToken) {
    Write-Host "Environment variables already set:" -ForegroundColor Yellow
    Write-Host "  DATABRICKS_SERVER_HOSTNAME: $serverHost" -ForegroundColor Cyan
    Write-Host "  DATABRICKS_HTTP_PATH: $httpPath" -ForegroundColor Cyan
    Write-Host "  DATABRICKS_ACCESS_TOKEN: $($accessToken.Substring(0,8))***" -ForegroundColor Cyan
    Write-Host ""

    $useExisting = Read-Host "Use existing values? (yes/no)"
    if ($useExisting -eq "yes" -or $useExisting -eq "y") {
        Write-Host "Using existing environment variables" -ForegroundColor Green
        exit 0
    }
}

# Get values from user
Write-Host "Enter Databricks configuration:" -ForegroundColor Yellow
Write-Host ""

if (-not $serverHost) {
    $serverHost = Read-Host "DATABRICKS_SERVER_HOSTNAME"
}
if (-not $httpPath) {
    $httpPath = Read-Host "DATABRICKS_HTTP_PATH"
}
if (-not $accessToken) {
    $accessToken = Read-Host "DATABRICKS_ACCESS_TOKEN" -AsSecureString
    $accessToken = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($accessToken)
    )
}

# Set environment variables for current session
$env:DATABRICKS_SERVER_HOSTNAME = $serverHost
$env:DATABRICKS_HTTP_PATH = $httpPath
$env:DATABRICKS_ACCESS_TOKEN = $accessToken
$env:USE_DATABRICKS = "true"

Write-Host ""
Write-Host "Environment variables set for current session" -ForegroundColor Green
Write-Host ""

# Ask if user wants to set permanently
$setPermanent = Read-Host "Set permanently in User Environment Variables? (yes/no)"
if ($setPermanent -eq "yes" -or $setPermanent -eq "y") {
    [System.Environment]::SetEnvironmentVariable("DATABRICKS_SERVER_HOSTNAME", $serverHost, "User")
    [System.Environment]::SetEnvironmentVariable("DATABRICKS_HTTP_PATH", $httpPath, "User")
    [System.Environment]::SetEnvironmentVariable("DATABRICKS_ACCESS_TOKEN", $accessToken, "User")
    [System.Environment]::SetEnvironmentVariable("USE_DATABRICKS", "true", "User")

    Write-Host "Environment variables set permanently" -ForegroundColor Green
    Write-Host "Note: You may need to restart your terminal for changes to take effect" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Test connection: python -c 'from application.mothership.db.databricks_connector import validate_databricks_connection; print(\"SUCCESS\" if validate_databricks_connection() else \"FAILED\")'"
Write-Host "2. Run migration: python scripts/migrate_databricks_simple.py"
Write-Host "3. Cleanup old database: python scripts/cleanup_old_database.py"
