#!/usr/bin/env powershell
<#
.SYNOPSIS
    WSL Configuration Diagnostic & Fix Script
    
.DESCRIPTION
    Diagnoses WSL setup issues and provides fixes for:
    - WSL not installed
    - Drives not mounted
    - Path resolution issues
#>


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

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "WSL Configuration Diagnostic" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check WSL installation
Write-Host "[1/6] Checking WSL installation..." -ForegroundColor Yellow
try {
    $wslVersion = & wsl --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "WSL 2 installed:" -ForegroundColor Green
        Write-Host "  $wslVersion"
        $wslInstalled = $true
    } else {
        Write-Host "WSL 1 detected (legacy)" -ForegroundColor Yellow
        $wslInstalled = $true
    }
} catch {
    Write-Host "WSL not installed" -ForegroundColor Red
    Write-Host "  Install with: wsl --install" -ForegroundColor Yellow
    $wslInstalled = $false
}
Write-Host ""

# Step 2: List distros
Write-Host "[2/6] Available WSL distros..." -ForegroundColor Yellow
try {
    $distros = & wsl --list --quiet 2>$null
    if ($distros) {
        Write-Host "Found distros:" -ForegroundColor Green
        $distros | ForEach-Object { Write-Host "  - $_" }
    } else {
        Write-Host "No distros found" -ForegroundColor Red
    }
} catch {
    Write-Host "Could not list distros" -ForegroundColor Yellow
}
Write-Host ""

# Step 3: Test WSL path translation
Write-Host "[3/6] Testing WSL path translation..." -ForegroundColor Yellow
try {
    $wslPath = & wsl wslpath -a "E:\" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "E:\ translates to: $wslPath" -ForegroundColor Green
    } else {
        Write-Host "Could not translate path" -ForegroundColor Yellow
    }
} catch {
    Write-Host "wslpath command failed" -ForegroundColor Yellow
}
Write-Host ""

# Step 4: Check if EUFLE directory is accessible from WSL
Write-Host "[4/6] Checking EUFLE directory accessibility..." -ForegroundColor Yellow
try {
    $eufleTest = & wsl test -d "/mnt/e/EUFLE" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "/mnt/e/EUFLE is accessible from WSL" -ForegroundColor Green
    } else {
        Write-Host "/mnt/e/EUFLE NOT accessible from WSL" -ForegroundColor Red
        Write-Host "  Trying alternative paths..." -ForegroundColor Yellow
        
        # Try uppercase
        $eufleTest = & wsl test -d "/mnt/E/EUFLE" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Found at /mnt/E/EUFLE (uppercase)" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "Could not test path" -ForegroundColor Yellow
}
Write-Host ""

# Step 5: Check E: drive exists on Windows
Write-Host "[5/6] Checking E: drive on Windows..." -ForegroundColor Yellow
if (Test-Path "E:\") {
    Write-Host "E:\ exists on Windows" -ForegroundColor Green
    $eufleTest = Test-Path "E:\EUFLE"
    if ($eufleTest) {
        Write-Host "E:\EUFLE directory exists" -ForegroundColor Green
    } else {
        Write-Host "E:\EUFLE directory NOT found" -ForegroundColor Red
    }
} else {
    Write-Host "E:\ drive NOT found on Windows" -ForegroundColor Red
}
Write-Host ""

# Step 6: Fix recommendations
Write-Host "[6/6] Recommended Fixes..." -ForegroundColor Yellow
Write-Host ""

Write-Host "If /mnt/e is not mounted in WSL:" -ForegroundColor White
Write-Host "  1. Create/edit WSL config file:" -ForegroundColor Gray
Write-Host "     wsl --distribution Ubuntu" -ForegroundColor Gray
Write-Host "     sudo nano /etc/wsl.conf" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Add these lines:" -ForegroundColor Gray
Write-Host "     [automount]" -ForegroundColor Gray
Write-Host "     enabled = true" -ForegroundColor Gray
Write-Host "     options = \"metadata\"" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Save (Ctrl+O, Enter, Ctrl+X)" -ForegroundColor Gray
Write-Host ""
Write-Host "  4. Shutdown and restart WSL:" -ForegroundColor Gray
Write-Host "     wsl --shutdown" -ForegroundColor Gray
Write-Host "     Then open WSL terminal again" -ForegroundColor Gray
Write-Host ""

Write-Host "If you want to verify the fix:" -ForegroundColor White
Write-Host "  wsl ls -la /mnt/e/EUFLE/scripts/" -ForegroundColor Gray
Write-Host ""

Write-Host "To run setup after fix:" -ForegroundColor White
Write-Host "  wsl bash /mnt/e/EUFLE/scripts/setup_llamacpp.sh" -ForegroundColor Gray
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Diagnostic Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
