#!/usr/bin/env pwsh
<#
.SYNOPSIS
Mount E: drive and all folders to WSL

.DESCRIPTION
Configures WSL to mount the E: drive with full access to all folders
#>

<#
IMPORTANT: This script is intended for one-time setup or repair only.
Do NOT add it to your shell profile (e.g., .bashrc, .zshrc, PowerShell profile).
Running this script on every terminal launch can cause duplication errors and is not supported.
#>

# Prevent running from a shell profile or multiple times
if ($env:RUNNING_FROM_PROFILE -eq '1') {
    Write-Host "❌ This script should NOT be run from a shell profile or autorun. Please run manually only when needed." -ForegroundColor Red
    exit 1
}

# Check if WSL is installed
Write-Host "Checking WSL installation..." -ForegroundColor Cyan
$wslCheck = wsl --list --verbose 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ WSL not found or not installed" -ForegroundColor Red
    exit 1
}

Write-Host "✅ WSL detected" -ForegroundColor Green
Write-Host $wslCheck

# Create WSL mount configuration
Write-Host "`nConfiguring WSL mount for E: drive..." -ForegroundColor Cyan

# Check if .wslconfig exists in user home
$homeDir = $env:USERPROFILE
$wslConfigPath = "$homeDir\.wslconfig"

# Backup existing config if it exists
if (Test-Path $wslConfigPath) {
    $backupPath = "$wslConfigPath.backup"
    Copy-Item $wslConfigPath $backupPath
    Write-Host "Backed up existing .wslconfig to $backupPath" -ForegroundColor Yellow
}

# Create or update .wslconfig
$wslConfig = @"
[interop]
appendWindowsPath = true

[automount]
enabled = true
root = /mnt
options = "metadata,umask=22,fmask=11"

[wsl2]
memory = 4GB
processors = 4
swap = 2GB
localhostForwarding = true
"@

Set-Content -Path $wslConfigPath -Value $wslConfig -Encoding UTF8
Write-Host "Created .wslconfig at $wslConfigPath" -ForegroundColor Green
Write-Host "`n📄 Config content:" -ForegroundColor Cyan
Get-Content $wslConfigPath

# Verify mount will work by checking if E: exists
Write-Host "`nVerifying E: drive exists..." -ForegroundColor Cyan
if (Test-Path "E:\") {
    Write-Host "E: drive found" -ForegroundColor Green
    Get-Item E:\ | Select-Object Name, FullName
} else {
    Write-Host "E: drive not found" -ForegroundColor Yellow
}

# Restart WSL to apply changes
Write-Host "`nRestarting WSL..." -ForegroundColor Cyan
wsl --shutdown
Start-Sleep -Seconds 2

# Verify mount is accessible
Write-Host "`nVerifying mount in WSL..." -ForegroundColor Cyan
$mounted = wsl ls -la /mnt/e/ 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "E: drive successfully mounted at /mnt/e/" -ForegroundColor Green
    Write-Host "`nDirectory listing:" -ForegroundColor Cyan
    wsl ls -lh /mnt/e/ | Select-Object -First 20
} else {
    Write-Host "Mount verification failed:" -ForegroundColor Yellow
    Write-Host $mounted
}

Write-Host "`nSummary:" -ForegroundColor Cyan
Write-Host "  - E: drive mounted at /mnt/e/ in WSL"
Write-Host "  - Auto-mount enabled for all drives"
Write-Host "  - WSL restarted to apply changes"
Write-Host "`nSetup complete!" -ForegroundColor Green
