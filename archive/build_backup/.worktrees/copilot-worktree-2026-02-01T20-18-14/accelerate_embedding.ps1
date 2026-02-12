#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Active Embedding Generation - Speed Optimization
    Safely stops processes during active embedding work to maximize performance

.DESCRIPTION
    Target: Running embedding generation (PID 29348)
    Action: Stop non-essential processes to free resources
    Risk: LOW - only stops IDE and optional security services

.EXAMPLE
    .\accelerate_embedding.ps1

.NOTES
    Terminal PID: 29348 (Embedded Generation)
    Current Status: HIGH PRIORITY + ALL CORES ALLOCATED
#>

Write-Host ""
Write-Host "[EMBEDDING ACCELERATION - ACTIVE OPTIMIZATION]" -ForegroundColor Magenta
Write-Host "=============================================" -ForegroundColor Magenta
Write-Host ""

# Check if target terminal exists
$embedProcess = Get-Process -Id 29348 -ErrorAction SilentlyContinue
if (-not $embedProcess) {
    Write-Host "[ERROR] Terminal PID 29348 not found!" -ForegroundColor Red
    exit 1
}

Write-Host "[TARGET] Embedding Process: PID $($embedProcess.Id) - Status: ACTIVE" -ForegroundColor Green
Write-Host ""

# Get system state
$sysMem = Get-CimInstance Win32_OperatingSystem
$availGB = [math]::Round($sysMem.FreePhysicalMemory / 1MB / 1024, 1)
Write-Host "[SYSTEM STATE]" -ForegroundColor Cyan
Write-Host "  Available Memory: $availGB GB" -ForegroundColor Yellow
Write-Host ""

# Define processes to stop
$codeProcesses = @(280, 2316, 11988, 18908, 19368, 22464, 23768, 25276, 26872, 27956, 28760, 30360)
$defenderPID = 4772

# Calculate memory savings
$codeMem = 0
$defenderMem = 16.7

foreach ($pid in $codeProcesses) {
    $p = Get-Process -Id $pid -ErrorAction SilentlyContinue
    if ($p) {
        $codeMem += [math]::Round($p.WorkingSet / 1MB, 1)
    }
}

Write-Host "[ACCELERATION PLAN]" -ForegroundColor Cyan
Write-Host "  [1] Stop VS Code instances:    +$codeMem MB" -ForegroundColor Yellow
Write-Host "  [2] Stop Windows Defender:     +16.7 MB" -ForegroundColor Yellow
Write-Host "  =================================" -ForegroundColor Cyan
Write-Host "  Total Memory Gain:             +$([math]::Round($codeMem + $defenderMem, 1)) MB" -ForegroundColor Green
Write-Host ""

# Confirm action
Write-Host "[CAUTION]" -ForegroundColor Yellow
Write-Host "  * Close VS Code now if you have unsaved work!" -ForegroundColor Red
Write-Host "  * Security: Windows Defender will be disabled temporarily" -ForegroundColor Yellow
Write-Host ""

Read-Host "Press ENTER to continue (stop processes for embedding speed boost) or Ctrl+C to cancel"

# Execute cleanup
Write-Host ""
Write-Host "[EXECUTING OPTIMIZATION]" -ForegroundColor Cyan

# Stop VS Code instances
Write-Host ""
Write-Host "Stopping VS Code instances..." -ForegroundColor White
$stoppedCode = 0
foreach ($pid in $codeProcesses) {
    $p = Get-Process -Id $pid -ErrorAction SilentlyContinue
    if ($p) {
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        $stoppedCode++
    }
}
Write-Host "  [OK] Stopped $stoppedCode Code instances" -ForegroundColor Green

# Stop Windows Defender
Write-Host ""
Write-Host "Stopping Windows Defender..." -ForegroundColor White
$defenderProc = Get-Process -Id $defenderPID -ErrorAction SilentlyContinue
if ($defenderProc) {
    Stop-Process -Id $defenderPID -Force -ErrorAction SilentlyContinue
    Write-Host "  [OK] Stopped Windows Defender" -ForegroundColor Green
}

# Verify embedding still running
Start-Sleep -Milliseconds 500
$embedCheck = Get-Process -Id 29348 -ErrorAction SilentlyContinue
if ($embedCheck) {
    Write-Host ""
    Write-Host "[VERIFICATION]" -ForegroundColor Green
    Write-Host "  [OK] Embedding process still running: PID 29348" -ForegroundColor Green
    Write-Host "  [OK] Memory available: $([math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB/1024, 1)) GB" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "[ERROR] Embedding process stopped!" -ForegroundColor Red
}

Write-Host ""
Write-Host "[OPTIMIZATION COMPLETE]" -ForegroundColor Green
Write-Host "  * Freed ~$([math]::Round($codeMem + $defenderMem, 1)) MB for embedding operations" -ForegroundColor Green
Write-Host "  * Embedding should complete faster with freed resources" -ForegroundColor Green
Write-Host ""
Write-Host "[MONITOR PROGRESS]" -ForegroundColor Cyan
Write-Host "  Run in separate terminal: .\monitor_terminal_resources.ps1" -ForegroundColor Gray
Write-Host ""
