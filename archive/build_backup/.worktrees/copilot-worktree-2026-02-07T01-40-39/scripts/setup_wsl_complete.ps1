#!/usr/bin/env powershell
<#
.SYNOPSIS
    Complete WSL + llama-cli Setup and Diagnostics
    Run with: powershell -ExecutionPolicy Bypass -File setup_wsl_complete.ps1
#>

param(
    [switch]$SkipDiagnostic,
    [switch]$FixOnly,
    [switch]$RunSetup
)

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        WSL + llama-cli Complete Setup & Diagnostic         ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# PART 1: DIAGNOSTICS
# ============================================================================

if (-not $SkipDiagnostic) {
    Write-Host "PART 1: DIAGNOSTICS" -ForegroundColor Yellow
    Write-Host "─" * 64 -ForegroundColor Gray
    Write-Host ""

    # Check WSL
    Write-Host "[1/6] WSL Installation:" -ForegroundColor White
    try {
        $wslVersion = & wsl --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ WSL 2 installed" -ForegroundColor Green
            foreach ($line in $wslVersion) {
                Write-Host "    $line" -ForegroundColor Gray
            }
        } else {
            Write-Host "  ⚠ WSL 1 detected (legacy)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ✗ WSL not installed" -ForegroundColor Red
    }
    Write-Host ""

    # List distros
    Write-Host "[2/6] WSL Distros:" -ForegroundColor White
    try {
        $distros = & wsl --list --quiet 2>$null
        if ($distros.Count -gt 0) {
            Write-Host "  ✓ Found distros:" -ForegroundColor Green
            $distros | ForEach-Object { 
                if ($_ -match '\S') {
                    Write-Host "    - $_" -ForegroundColor Gray
                }
            }
        } else {
            Write-Host "  ✗ No distros found" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ⚠ Could not list distros" -ForegroundColor Yellow
    }
    Write-Host ""

    # Test path translation
    Write-Host "[3/6] Path Translation (E:\\ in WSL):" -ForegroundColor White
    try {
        $wslPath = & wsl wslpath -a "E:\" 2>$null
        if ($LASTEXITCODE -eq 0 -and $wslPath) {
            Write-Host "  ✓ E:\ → $wslPath" -ForegroundColor Green
        } else {
            Write-Host "  ⚠ Path translation may not work" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ⚠ wslpath not available" -ForegroundColor Yellow
    }
    Write-Host ""

    # Check Windows drive
    Write-Host "[4/6] Windows E: Drive:" -ForegroundColor White
    if (Test-Path "E:\") {
        Write-Host "  ✓ E:\ exists on Windows" -ForegroundColor Green
        if (Test-Path "E:\EUFLE") {
            Write-Host "  ✓ E:\EUFLE directory found" -ForegroundColor Green
        } else {
            Write-Host "  ✗ E:\EUFLE not found" -ForegroundColor Red
        }
    } else {
        Write-Host "  ✗ E:\ drive not found" -ForegroundColor Red
    }
    Write-Host ""

    # Check WSL mount
    Write-Host "[5/6] WSL Mount Status:" -ForegroundColor White
    try {
        $mounted = & wsl test -d "/mnt/e" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ /mnt/e is mounted in WSL" -ForegroundColor Green
            
            $eufleExists = & wsl test -d "/mnt/e/EUFLE" 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✓ /mnt/e/EUFLE accessible from WSL" -ForegroundColor Green
            } else {
                Write-Host "  ✗ /mnt/e/EUFLE NOT accessible" -ForegroundColor Red
            }
        } else {
            Write-Host "  ✗ /mnt/e NOT mounted in WSL" -ForegroundColor Red
            Write-Host "    → This needs to be fixed before setup" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ⚠ Could not check mount status" -ForegroundColor Yellow
    }
    Write-Host ""

    # Check setup script
    Write-Host "[6/6] Setup Script:" -ForegroundColor White
    if (Test-Path "E:\EUFLE\scripts\setup_llamacpp.sh") {
        Write-Host "  ✓ setup_llamacpp.sh found" -ForegroundColor Green
    } else {
        Write-Host "  ✗ setup_llamacpp.sh not found" -ForegroundColor Red
    }
    Write-Host ""
}

# ============================================================================
# PART 2: FIX MOUNT ISSUES
# ============================================================================

Write-Host "PART 2: FIX WSL MOUNT ISSUES" -ForegroundColor Yellow
Write-Host "─" * 64 -ForegroundColor Gray
Write-Host ""

Write-Host "To enable Windows drive mounting in WSL:" -ForegroundColor White
Write-Host ""
Write-Host "  1. Open WSL terminal and run:" -ForegroundColor Gray
Write-Host "     sudo nano /etc/wsl.conf" -ForegroundColor Cyan
Write-Host ""
Write-Host "  2. Add these lines (or replace [automount] section):" -ForegroundColor Gray
Write-Host ""
Write-Host "     [automount]" -ForegroundColor Cyan
Write-Host "     enabled = true" -ForegroundColor Cyan
Write-Host "     options = \"metadata\"" -ForegroundColor Cyan
Write-Host ""
Write-Host "  3. Save the file:" -ForegroundColor Gray
Write-Host "     Press Ctrl+O (save) → Enter → Ctrl+X (exit)" -ForegroundColor Cyan
Write-Host ""
Write-Host "  4. Restart WSL:" -ForegroundColor Gray
Write-Host "     In PowerShell: wsl --shutdown" -ForegroundColor Cyan
Write-Host "     Then reopen WSL terminal" -ForegroundColor Cyan
Write-Host ""

# Offer to create wsl.conf content
Write-Host "OR - Auto-apply fix (if you have WSL open):" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Run this in WSL terminal:" -ForegroundColor Gray
Write-Host "  echo '[automount]' | sudo tee /etc/wsl.conf > /dev/null" -ForegroundColor Cyan
Write-Host "  echo 'enabled = true' | sudo tee -a /etc/wsl.conf > /dev/null" -ForegroundColor Cyan
Write-Host "  echo 'options = \"metadata\"' | sudo tee -a /etc/wsl.conf > /dev/null" -ForegroundColor Cyan
Write-Host ""

Write-Host "Then verify the fix:" -ForegroundColor White
Write-Host "  wsl ls -la /mnt/e/EUFLE/" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# PART 3: RUN SETUP
# ============================================================================

Write-Host "PART 3: RUN SETUP" -ForegroundColor Yellow
Write-Host "─" * 64 -ForegroundColor Gray
Write-Host ""

Write-Host "Once /mnt/e/EUFLE is accessible, run:" -ForegroundColor White
Write-Host ""
Write-Host "  wsl bash /mnt/e/EUFLE/scripts/setup_llamacpp.sh" -ForegroundColor Cyan
Write-Host ""

Write-Host "Or from the WSL terminal:" -ForegroundColor White
Write-Host ""
Write-Host "  cd /mnt/e/EUFLE" -ForegroundColor Cyan
Write-Host "  bash scripts/setup_llamacpp.sh" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# SUMMARY
# ============================================================================

Write-Host "SUMMARY" -ForegroundColor Yellow
Write-Host "─" * 64 -ForegroundColor Gray
Write-Host ""
Write-Host "Three Options Available:" -ForegroundColor White
Write-Host ""
Write-Host "  1. OLLAMA (Easiest)" -ForegroundColor Green
Write-Host "     Already configured, just run: python eufle.py --ask" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. WSL + llama-cli (Advanced)" -ForegroundColor Yellow
Write-Host "     Requires fixing /mnt mount above, then running setup" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Local HF Model (Already works)" -ForegroundColor Blue
Write-Host "     Automatic fallback, no setup needed" -ForegroundColor Gray
Write-Host ""

Write-Host "═" * 64 -ForegroundColor Cyan
Write-Host ""
