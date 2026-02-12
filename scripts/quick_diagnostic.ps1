#!/usr/bin/env powershell

<#
IMPORTANT: This script is intended for one-time diagnostics or repair only.
Do NOT add it to your shell profile (e.g., .bashrc, .zshrc, PowerShell profile).
Running this script on every terminal launch can cause duplication errors and is not supported.
#>

# Prevent running from a shell profile or multiple times
if ($env:RUNNING_FROM_PROFILE -eq '1') {
    Write-Host "This script should NOT be run from a shell profile or autorun. Please run manually only when needed." -ForegroundColor Red
    exit 1
}

# Run diagnostics directly - no directory changes needed

$env:EUFLE_PATH = "E:\EUFLE"
$wslEuflePath = "/mnt/e/EUFLE"

Write-Host ""
Write-Host "════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   WSL Mount & Setup Quick Diagnostic              " -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Test 1: WSL Available
Write-Host "[TEST 1] Is WSL installed?" -ForegroundColor Yellow
try {
    $version = & wsl --version 2>&1
    Write-Host "YES - WSL is installed" -ForegroundColor Green
    Write-Host "  $($version[0])" -ForegroundColor Gray
} catch {
    Write-Host "NO - WSL not installed" -ForegroundColor Red
    Write-Host "  Install: wsl --install" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Test 2: Distros
Write-Host "[TEST 2] Available distros?" -ForegroundColor Yellow
$distros = @(& wsl --list --quiet 2>&1)
$distros = $distros | Where-Object { $_ -match '\S' }
if ($distros.Count -gt 0) {
    Write-Host "YES - Found distros:" -ForegroundColor Green
    $distros | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }
} else {
    Write-Host "NO distros found" -ForegroundColor Red
}
Write-Host ""

# Test 3: Windows E: drive
Write-Host "[TEST 3] Windows E: drive exists?" -ForegroundColor Yellow
if (Test-Path "E:\") {
    Write-Host "YES - E:\ drive found" -ForegroundColor Green
    if (Test-Path "E:\EUFLE") {
        Write-Host "YES - E:\EUFLE directory found" -ForegroundColor Green
    } else {
        Write-Host "NO - E:\EUFLE not found" -ForegroundColor Red
    }
} else {
    Write-Host "NO - E:\ drive not found" -ForegroundColor Red
}
Write-Host ""

# Test 4: WSL can see the mount
Write-Host "[TEST 4] Can WSL access /mnt/e/EUFLE?" -ForegroundColor Yellow
try {
    $test = & wsl test -d "/mnt/e/EUFLE" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "YES - /mnt/e/EUFLE is accessible!" -ForegroundColor Green
        Write-Host "  Ready to run setup!" -ForegroundColor Green
    } else {
        Write-Host "NO - Path not accessible" -ForegroundColor Red
        Write-Host "  This needs fixing first" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Cannot determine status" -ForegroundColor Yellow
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Gray
}
Write-Host ""

# Test 5: Setup script exists
Write-Host "[TEST 5] Setup script present?" -ForegroundColor Yellow
if (Test-Path "E:\EUFLE\scripts\setup_llamacpp.sh") {
    Write-Host "YES - setup_llamacpp.sh found at E:\EUFLE\scripts\" -ForegroundColor Green
} else {
    Write-Host "NO - Script not found" -ForegroundColor Red
}
Write-Host ""

# Recommendations
Write-Host "════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "NEXT STEPS" -ForegroundColor Yellow
Write-Host "════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Write-Host "If TEST 4 shows YES:" -ForegroundColor Green
Write-Host "  Ready! Run setup:" -ForegroundColor White
Write-Host "  wsl bash /mnt/e/EUFLE/scripts/setup_llamacpp.sh" -ForegroundColor Cyan
Write-Host ""

Write-Host "If TEST 4 shows NO:" -ForegroundColor Red
Write-Host "  Fix WSL mount:" -ForegroundColor White
Write-Host "  1. wsl" -ForegroundColor Cyan
Write-Host "  2. sudo nano /etc/wsl.conf" -ForegroundColor Cyan
Write-Host "  3. Add: [automount]" -ForegroundColor Cyan
Write-Host "         enabled = true" -ForegroundColor Cyan
Write-Host "  4. Save (Ctrl+O, Enter, Ctrl+X)" -ForegroundColor Cyan
Write-Host "  5. Exit WSL (Ctrl+D or exit)" -ForegroundColor Cyan
Write-Host "  6. wsl --shutdown" -ForegroundColor Cyan
Write-Host "  7. Re-run this diagnostic" -ForegroundColor Cyan
Write-Host ""

Write-Host "════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
