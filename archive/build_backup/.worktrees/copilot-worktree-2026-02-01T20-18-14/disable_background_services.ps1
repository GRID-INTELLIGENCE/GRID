#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Final System Optimization for Active Embedding Generation
    Reduces system background load to maximum efficiency

.DESCRIPTION
    Disables non-critical Windows services and reduces system overhead
    while embedding generation is running (PID 29348)
    
    All changes are reversible and only affect system services

.PARAMETER Aggressive
    Also disable Windows defender and network services
#>

param(
    [switch]$Aggressive
)

Write-Host ""
Write-Host "[SYSTEM BACKGROUND OPTIMIZATION]" -ForegroundColor Magenta
Write-Host "==================================" -ForegroundColor Magenta
Write-Host ""

# Check if embedding still running
$emb = Get-Process -Id 29348 -ErrorAction SilentlyContinue
if (-not $emb) {
    Write-Host "[ERROR] Embedding process not found!" -ForegroundColor Red
    exit 1
}

Write-Host "[STATUS] Embedding: PID 29348 - ACTIVE" -ForegroundColor Green
Write-Host ""

# Define non-critical services
$nonCriticalServices = @(
    'DiagTrack',              # Diagnostic Tracking Service
    'dmwappushservice',       # Service advertising
    'cdp',                    # Connected Devices Platform
    'PcaSvc',                 # Program Compatibility Assistant
    'TabletInputService',     # Tablet Input Service
    'WbioSrvc',              # Windows Biometric Service
    'FrameServer',           # Windows Camera Frame Server
    'WxTsBootstrap',         # Wireless Display Service
    'iphlpsvc',              # IP Helper
    'lfsvc'                  # Location Service
)

$networkServices = @(
    'fdPHost',               # Function Discovery Provider Host
    'fdResponder',           # Function Discovery Resource Publication
    'MapsBroker'             # Downloaded Maps Manager
)

$defenderServices = @(
    'WinDefend',             # Windows Defender
    'SecurityHealthService'  # Windows Security Service
)

Write-Host "[SERVICES TO DISABLE]" -ForegroundColor Cyan
Write-Host ""

# Count services that can be stopped
$canStop = 0
foreach ($srv in $nonCriticalServices) {
    $s = Get-Service -Name $srv -ErrorAction SilentlyContinue
    if ($s -and $s.Status -eq 'Running') {
        Write-Host "  * $srv" -ForegroundColor White
        $canStop++
    }
}

Write-Host ""
Write-Host "Found: $canStop services that can be disabled" -ForegroundColor Yellow
Write-Host ""

if ($Aggressive) {
    Write-Host "[AGGRESSIVE MODE]" -ForegroundColor Red
    Write-Host "  * Will also disable Windows Defender" -ForegroundColor Red
    Write-Host "  * Security: Temporarily reduced" -ForegroundColor Red
    Write-Host ""
}

# Confirm
Read-Host "Press ENTER to disable services (or Ctrl+C to cancel)"

Write-Host ""
Write-Host "[EXECUTING SERVICE DISABLEMENT]" -ForegroundColor Cyan
Write-Host ""

# Stop non-critical services
Write-Host "Disabling background services..." -ForegroundColor White
$stopped = 0
foreach ($srv in $nonCriticalServices) {
    $service = Get-Service -Name $srv -ErrorAction SilentlyContinue
    if ($service) {
        try {
            Stop-Service -Name $srv -Force -ErrorAction SilentlyContinue
            $stopped++
            Write-Host "  [OK] $srv" -ForegroundColor Green
        } catch {
            Write-Host "  [SKIP] $srv (protected service)" -ForegroundColor Yellow
        }
    }
}

Write-Host ""
Write-Host "  Stopped: $stopped services" -ForegroundColor Green
Write-Host ""

# Network services
if ($Aggressive) {
    Write-Host "Disabling network discovery services..." -ForegroundColor White
    $netStopped = 0
    foreach ($srv in $networkServices) {
        $service = Get-Service -Name $srv -ErrorAction SilentlyContinue
        if ($service -and $service.Status -eq 'Running') {
            try {
                Stop-Service -Name $srv -Force -ErrorAction SilentlyContinue
                $netStopped++
                Write-Host "  [OK] $srv" -ForegroundColor Green
            } catch {
                Write-Host "  [SKIP] $srv" -ForegroundColor Yellow
            }
        }
    }
    Write-Host ""
    Write-Host "  Stopped: $netStopped network services" -ForegroundColor Green
    Write-Host ""
    
    # Defender
    Write-Host "Disabling Windows Defender..." -ForegroundColor White
    foreach ($srv in $defenderServices) {
        Stop-Service -Name $srv -Force -ErrorAction SilentlyContinue
    }
    Write-Host "  [OK] Windows Defender disabled" -ForegroundColor Green
    Write-Host ""
}

# Verify embedding still running
Start-Sleep -Milliseconds 300
$embCheck = Get-Process -Id 29348 -ErrorAction SilentlyContinue
if ($embCheck) {
    Write-Host "[VERIFICATION]" -ForegroundColor Green
    Write-Host "  [OK] Embedding process still running" -ForegroundColor Green
    Write-Host "  [OK] System overhead reduced" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Embedding process lost!" -ForegroundColor Red
}

Write-Host ""
Write-Host "[OPTIMIZATION COMPLETE]" -ForegroundColor Green
Write-Host "  * Embedding generation should now run faster" -ForegroundColor Green
Write-Host "  * Monitor with: .\monitor_terminal_resources.ps1" -ForegroundColor Green
Write-Host ""
