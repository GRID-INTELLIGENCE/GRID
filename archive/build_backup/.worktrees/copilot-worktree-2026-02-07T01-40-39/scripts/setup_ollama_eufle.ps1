#!/usr/bin/env powershell
<#
.SYNOPSIS
    Setup EUFLE with Ollama as the default language model provider
    
.DESCRIPTION
    This script:
    1. Checks if Ollama is installed
    2. Sets EUFLE_DEFAULT_PROVIDER environment variable to "ollama"
    3. Optionally starts Ollama server
    4. Verifies the setup
#>

param(
    [switch]$StartOllama,
    [switch]$Permanent
)

Write-Host "================================" -ForegroundColor Cyan
Write-Host "EUFLE + Ollama Setup Script" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Ollama installation
Write-Host "[1/4] Checking Ollama installation..." -ForegroundColor Yellow

try {
    $ollamaVersion = & ollama --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Ollama found: $ollamaVersion" -ForegroundColor Green
        $ollamaInstalled = $true
    } else {
        throw "Ollama not found"
    }
} catch {
    Write-Host "✗ Ollama not installed or not in PATH" -ForegroundColor Red
    Write-Host ""
    Write-Host "To install Ollama:" -ForegroundColor Yellow
    Write-Host "  1. Download from https://ollama.ai" -ForegroundColor White
    Write-Host "  2. Install and restart PowerShell" -ForegroundColor White
    Write-Host "  3. Run: ollama pull mistral (or another model)" -ForegroundColor White
    Write-Host "  4. Then re-run this script" -ForegroundColor White
    exit 1
}

# Step 2: Set environment variable (temporary)
Write-Host ""
Write-Host "[2/4] Setting EUFLE_DEFAULT_PROVIDER=ollama (temporary)..." -ForegroundColor Yellow
$env:EUFLE_DEFAULT_PROVIDER = "ollama"
Write-Host "✓ Environment variable set for this session" -ForegroundColor Green

# Step 3: Set environment variable (permanent if requested)
if ($Permanent) {
    Write-Host ""
    Write-Host "[3/4] Setting permanent environment variable..." -ForegroundColor Yellow
    try {
        [Environment]::SetEnvironmentVariable("EUFLE_DEFAULT_PROVIDER", "ollama", "User")
        Write-Host "✓ Permanent environment variable set (User scope)" -ForegroundColor Green
    } catch {
        Write-Host "⚠ Could not set permanent variable (requires different approach)" -ForegroundColor Yellow
        Write-Host "  Fallback: Run in Admin PowerShell:" -ForegroundColor White
        Write-Host "  [Environment]::SetEnvironmentVariable('EUFLE_DEFAULT_PROVIDER', 'ollama', 'User')" -ForegroundColor Gray
    }
} else {
    Write-Host ""
    Write-Host "[3/4] Skipping permanent setup (use -Permanent flag to enable)" -ForegroundColor Gray
}

# Step 4: Start Ollama if requested
Write-Host ""
Write-Host "[4/4] Ollama server status..." -ForegroundColor Yellow

$ollamaRunning = $false
try {
    $null = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($?) {
        Write-Host "✓ Ollama server is already running on localhost:11434" -ForegroundColor Green
        $ollamaRunning = $true
    }
} catch {
    Write-Host "⚠ Ollama server not detected on localhost:11434" -ForegroundColor Yellow
}

if (-not $ollamaRunning -and $StartOllama) {
    Write-Host "Starting Ollama server..." -ForegroundColor Yellow
    Start-Process ollama -ArgumentList "serve" -NoNewWindow
    Start-Sleep -Seconds 3
    
    try {
        $null = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction SilentlyContinue
        Write-Host "✓ Ollama server started successfully" -ForegroundColor Green
    } catch {
        Write-Host "⚠ Could not verify Ollama server is running. Start manually: ollama serve" -ForegroundColor Yellow
    }
}

if (-not $ollamaRunning -and -not $StartOllama) {
    Write-Host "To start Ollama server, run: ollama serve" -ForegroundColor White
}

# Verification
Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Ensure Ollama server is running: ollama serve" -ForegroundColor White
Write-Host "  2. Pull a model (if needed): ollama pull mistral" -ForegroundColor White
Write-Host "  3. Test EUFLE: python eufle.py --ask" -ForegroundColor White
Write-Host ""
Write-Host "Environment variables:" -ForegroundColor White
Write-Host "  EUFLE_DEFAULT_PROVIDER = $env:EUFLE_DEFAULT_PROVIDER" -ForegroundColor Gray
Write-Host ""
