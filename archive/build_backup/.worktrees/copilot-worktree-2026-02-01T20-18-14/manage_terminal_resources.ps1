#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Resource allocation and priority management for Antigravity terminal (PID 29348)

.DESCRIPTION
    Sets high priority, CPU affinity, and memory management for optimal performance
    of the terminal process used for grid operations.

.PARAMETER Priority
    Process priority level: Low, BelowNormal, Normal, AboveNormal, High, RealTime
    Default: High

.PARAMETER Cores
    Number of CPU cores to allocate. Options: 1, 2, 4, 8, 16
    Default: 4

.PARAMETER StartCore
    First core index to start affinity allocation (0-15)
    Default: 4

.EXAMPLE
    .\manage_terminal_resources.ps1 -Priority High -Cores 8 -StartCore 0

.NOTES
    Requires administrator privileges
    Process ID: 29348 (Antigravity PowerShell)
#>

param(
    [ValidateSet('Low', 'BelowNormal', 'Normal', 'AboveNormal', 'High', 'RealTime')]
    [string]$Priority = 'High',
    
    [ValidateSet(1, 2, 4, 8, 16)]
    [int]$Cores = 4,
    
    [ValidateRange(0, 15)]
    [int]$StartCore = 4
)

function ConvertTo-AffinityMask {
    param(
        [int]$CoreCount,
        [int]$StartCore
    )
    
    $mask = 0
    for ($i = 0; $i -lt $CoreCount; $i++) {
        $mask = $mask -bor (1 -shl ($StartCore + $i))
    }
    return $mask
}

function Show-ProcessInfo {
    param([System.Diagnostics.Process]$Process)
    
    $cpuTime = $Process.TotalProcessorTime.ToString()
    $memory = [math]::Round($Process.WorkingSet / 1MB, 2)
    $handles = $Process.Handles
    
    Write-Host ""
    Write-Host "TERMINAL PROCESS RESOURCE ALLOCATION" -ForegroundColor Cyan
    Write-Host "====================================" -ForegroundColor Cyan
    Write-Host "Process Name:     $($Process.ProcessName)" -ForegroundColor White
    Write-Host "PID:              $($Process.Id)" -ForegroundColor White
    Write-Host "Priority:         $($Process.PriorityClass)" -ForegroundColor Green
    Write-Host "Memory Usage:     $memory MB" -ForegroundColor Yellow
    Write-Host "CPU Time:         $cpuTime" -ForegroundColor Yellow
    Write-Host "Handles:          $($handles)" -ForegroundColor White
    Write-Host "====================================" -ForegroundColor Cyan
}

function Show-CoreAllocation {
    param(
        [int]$AffinityMask,
        [int]$StartCore,
        [int]$CoreCount
    )
    
    Write-Host ""
    Write-Host "[CPU CORE ALLOCATION]" -ForegroundColor Cyan
    Write-Host "  Allocated cores: $StartCore-$($StartCore + $CoreCount - 1)" -ForegroundColor Green
    Write-Host "  Number of cores: $CoreCount" -ForegroundColor Green
    Write-Host "  Affinity mask (hex): 0x$($AffinityMask.ToString('X'))" -ForegroundColor Cyan
    Write-Host "  Affinity mask (decimal): $AffinityMask" -ForegroundColor Cyan
    
    Write-Host ""
    Write-Host "  Core utilization map (Ryzen 7700):" -ForegroundColor Gray
    $coreMap = ""
    for ($i = 0; $i -lt 16; $i++) {
        if ($i -ge $StartCore -and $i -lt ($StartCore + $CoreCount)) {
            $coreMap += "="
        } else {
            $coreMap += "-"
        }
        if (($i + 1) % 8 -eq 0 -and $i -gt 0) { $coreMap += " " }
    }
    Write-Host "  $coreMap" -ForegroundColor Green
    Write-Host "  ======== Allocated  -------- System/Other" -ForegroundColor Gray
}

# Main execution
Write-Host ""
Write-Host "[ANTIGRAVITY TERMINAL RESOURCE MANAGER]" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[WARNING] Not running as administrator. Some operations may fail." -ForegroundColor Yellow
    Write-Host "   To enable all features, run this script as administrator" -ForegroundColor Yellow
    Write-Host ""
}

# Get process
$processId = 29348
$process = Get-Process -Id $processId -ErrorAction SilentlyContinue

if (-not $process) {
    Write-Host "[ERROR] Process with PID $processId not found!" -ForegroundColor Red
    Write-Host "   Is the Antigravity terminal open?" -ForegroundColor Yellow
    exit 1
}

# Apply priority
try {
    $process.PriorityClass = $Priority
    Write-Host "[OK] Priority set to: $Priority" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to set priority: $_" -ForegroundColor Red
}

# Apply affinity
try {
    $affinityMask = ConvertTo-AffinityMask -CoreCount $Cores -StartCore $StartCore
    $process.ProcessorAffinity = [IntPtr]$affinityMask
    Write-Host "[OK] Processor affinity applied" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "[WARNING] Could not set processor affinity (may require admin): $_" -ForegroundColor Yellow
}

# Display info
Show-ProcessInfo -Process $process
Show-CoreAllocation -AffinityMask $affinityMask -StartCore $StartCore -CoreCount $Cores

# Performance recommendations
Write-Host ""
Write-Host "[OPTIMIZATION TIPS]" -ForegroundColor Cyan
Write-Host "  * Process is now prioritized by Windows scheduler" -ForegroundColor White
Write-Host "  * Dedicated cores reduce context-switching overhead" -ForegroundColor White
Write-Host "  * Monitor task manager to verify allocation" -ForegroundColor White
Write-Host "  * If CPU usage is low, try reducing -Cores parameter" -ForegroundColor White

Write-Host ""
Write-Host "[NEXT STEPS]" -ForegroundColor Cyan
Write-Host "   .\manage_terminal_resources.ps1" -ForegroundColor Gray

Write-Host ""
