#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Real-time resource monitoring for Antigravity terminal (PID 29348)

.DESCRIPTION
    Displays CPU, memory, thread count, and other metrics updating every 2 seconds
    Useful for verifying the resource allocation is working properly

.PARAMETER RefreshInterval
    Update frequency in seconds (default: 2)

.PARAMETER Duration
    How long to monitor in seconds (0 = infinite, default: 0)

.EXAMPLE
    .\monitor_terminal_resources.ps1 -RefreshInterval 1 -Duration 60
#>

param(
    [int]$RefreshInterval = 2,
    [int]$Duration = 0
)

$processId = 29348
$startTime = Get-Date
$refreshCount = 0
$clearScreen = $true

function Clear-TerminalDisplay {
    Clear-Host
}

function Get-MemoryString {
    param([long]$Bytes)
    if ($Bytes -lt 1MB) { return "$([math]::Round($Bytes / 1KB, 1)) KB" }
    if ($Bytes -lt 1GB) { return "$([math]::Round($Bytes / 1MB, 1)) MB" }
    return "$([math]::Round($Bytes / 1GB, 1)) GB"
}

function Get-CPUUsage {
    param([System.Diagnostics.Process]$Process)
    
    # Get system uptime for CPU calculation
    $uptime = (Get-Date) - $Process.StartTime
    if ($uptime.TotalSeconds -eq 0) { return 0 }
    
    $cpuUsed = $Process.TotalProcessorTime.TotalSeconds / [Environment]::ProcessorCount
    $cpuPercent = ($cpuUsed / $uptime.TotalSeconds) * 100
    return [math]::Min($cpuPercent, 100)
}

function Show-ProcessMetrics {
    param([System.Diagnostics.Process]$Process)
    
    $refreshCount++
    $elapsed = (Get-Date) - $startTime
    
    # Get metrics
    $memory = $Process.WorkingSet
    $memoryString = Get-MemoryString -Bytes $memory
    
    $peakMemory = $Process.PeakWorkingSet
    $peakMemoryString = Get-MemoryString -Bytes $peakMemory
    
    $threads = $Process.Threads.Count
    $handles = $Process.Handles
    $cpuTime = $Process.TotalProcessorTime.ToString("hh\:mm\:ss")
    $priority = $Process.PriorityClass
    
    # Affinity might not be accessible, so wrap in try-catch
    $affinityStr = "N/A"
    try {
        if ($Process.ProcessorAffinity) {
            $affinity = [int]$Process.ProcessorAffinity
            $cores = [System.BitOperations]::PopCount($affinity)
            $affinityStr = "Cores: $cores"
        }
    } catch { }
    
    # Color coding
    $memoryPercent = ($memory / (32GB)) * 100
    if ($memoryPercent -lt 25) { $memColor = 'Green' }
    elseif ($memoryPercent -lt 50) { $memColor = 'Yellow' }
    else { $memColor = 'Red' }
    
    # Display header
    Write-Host "╔════════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║  ANTIGRAVITY TERMINAL - RESOURCE MONITORING                                   ║" -ForegroundColor Cyan
    Write-Host "╠════════════════════════════════════════════════════════════════════════════════╣" -ForegroundColor Cyan
    
    # Time info
    Write-Host "║ Monitoring time: $(("{0:dd} days, {0:hh}:{0:mm}:{0:ss}" -f $elapsed).PadRight(65)) ║" -ForegroundColor White
    Write-Host "║ Samples: $($refreshCount.ToString().PadRight(74)) ║" -ForegroundColor White
    
    Write-Host "╠════════════════════════════════════════════════════════════════════════════════╣" -ForegroundColor Cyan
    
    # Process info
    Write-Host "║ Process ID:      $($processId.ToString().PadRight(70)) ║" -ForegroundColor White
    Write-Host "║ Process Name:    $($Process.ProcessName.PadRight(70)) ║" -ForegroundColor White
    Write-Host "║ Priority:        $($priority.ToString().PadRight(70)) ║" -ForegroundColor Green
    
    Write-Host "╠════════════════════════════════════════════════════════════════════════════════╣" -ForegroundColor Cyan
    
    # Memory
    Write-Host "║ Memory (bytes):  $($memory.ToString().PadRight(70)) ║" -ForegroundColor $memColor
    Write-Host "║ Memory (human):  $($memoryString.PadRight(70)) ║" -ForegroundColor $memColor
    Write-Host "║ Peak Memory:     $($peakMemoryString.PadRight(70)) ║" -ForegroundColor Yellow
    Write-Host "║ Memory %:        $(([math]::Round($memoryPercent, 1)).ToString().PadRight(70)) ║" -ForegroundColor $memColor
    
    Write-Host "╠════════════════════════════════════════════════════════════════════════════════╣" -ForegroundColor Cyan
    
    # CPU and threading
    Write-Host "║ CPU Time:        $($cpuTime.PadRight(70)) ║" -ForegroundColor Cyan
    Write-Host "║ Active Threads:  $($threads.ToString().PadRight(70)) ║" -ForegroundColor Cyan
    Write-Host "║ Open Handles:    $($handles.ToString().PadRight(70)) ║" -ForegroundColor Cyan
    Write-Host "║ Processor Aff.:  $($affinityStr.PadRight(70)) ║" -ForegroundColor Green
    
    Write-Host "╚════════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    
    # Visual memory bar
    $barLength = 50
    $filledLength = [int](($memoryPercent / 100) * $barLength)
    $bar = "█" * $filledLength + "░" * ($barLength - $filledLength)
    Write-Host "  Memory: [$bar] $($memoryPercent.ToString('F1'))%" -ForegroundColor $memColor
    
    Write-Host ""
}

# Main loop
Clear-TerminalDisplay
Write-Host "🚀 Starting resource monitor for PID $processId..." -ForegroundColor Magenta
Start-Sleep -Seconds 1

$endTime = if ($Duration -eq 0) { [DateTime]::MaxValue } else { $startTime.AddSeconds($Duration) }

while ((Get-Date) -lt $endTime) {
    $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
    
    if (-not $process) {
        Write-Host "`n❌ Process $processId no longer exists!" -ForegroundColor Red
        Write-Host "   Terminal may have been closed." -ForegroundColor Yellow
        break
    }
    
    if ($clearScreen) {
        Clear-TerminalDisplay
    }
    
    Show-ProcessMetrics -Process $process
    
    Write-Host "  Updating in $RefreshInterval seconds... (Press Ctrl+C to stop)" -ForegroundColor DarkGray
    
    Start-Sleep -Seconds $RefreshInterval
}

Write-Host "`n✅ Monitoring complete." -ForegroundColor Green
