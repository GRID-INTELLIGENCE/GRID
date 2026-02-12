#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Setup Windows Scheduled Task for Persistent Spawn Monitor
    
.DESCRIPTION
    Creates a scheduled task that:
    - Runs at system startup (ALWAYS ACTIVE)
    - Auto-restarts on failure (PERSISTENT)
    - Runs with total-deny enforcement (CAUTIOUS)
    
.PARAMETER Remove
    Remove the scheduled task instead of creating it
    
.PARAMETER Status
    Show current task status
#>

param(
    [switch]$Remove = $false,
    [switch]$Status = $false
)

$ErrorActionPreference = "Stop"

$TaskName = "MCP_SpawnMonitor_TotalDeny"
$TaskDescription = "Persistent MCP spawn monitor with total-deny enforcement (AI Safety)"
$PythonPath = & (Join-Path $PSScriptRoot "resolve_python.ps1")
$MonitorScript = "E:\wellness_studio\ai_safety\monitoring\spawn_monitor.py"
$WorkingDir = "E:\"

# Task arguments
$TaskArguments = @(
    $MonitorScript,
    "--total-deny",
    "--daemon",
    "--interval", "30"
) -join " "

function Show-TaskStatus {
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host "SPAWN MONITOR SCHEDULED TASK STATUS" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
    
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($task) {
        Write-Host "Task Name:    $TaskName" -ForegroundColor Green
        Write-Host "State:        $($task.State)" -ForegroundColor $(if ($task.State -eq "Running") { "Green" } else { "Yellow" })
        Write-Host "Description:  $($task.Description)"
        
        $taskInfo = Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($taskInfo) {
            Write-Host "Last Run:     $($taskInfo.LastRunTime)"
            Write-Host "Last Result:  $($taskInfo.LastTaskResult)"
            Write-Host "Next Run:     $($taskInfo.NextRunTime)"
        }
        
        # Check monitor state file
        $stateFile = "E:\wellness_studio\ai_safety\monitoring\.monitor_state.json"
        if (Test-Path $stateFile) {
            Write-Host ""
            Write-Host "Monitor State File:" -ForegroundColor Cyan
            $state = Get-Content $stateFile -Raw | ConvertFrom-Json
            Write-Host "  Started:     $($state.started_at)"
            Write-Host "  Heartbeat:   $($state.last_heartbeat)"
            Write-Host "  Checks:      $($state.total_checks)"
            Write-Host "  Violations:  $($state.total_violations)"
        }
    } else {
        Write-Host "Task '$TaskName' not found" -ForegroundColor Yellow
        Write-Host "Run this script without parameters to create it"
    }
    Write-Host "=" * 60 -ForegroundColor Cyan
}

function Remove-MonitorTask {
    Write-Host "Removing scheduled task: $TaskName" -ForegroundColor Yellow
    
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($task) {
        if ($task.State -eq "Running") {
            Stop-ScheduledTask -TaskName $TaskName
            Write-Host "  Stopped running task" -ForegroundColor Yellow
        }
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "  Task removed successfully" -ForegroundColor Green
    } else {
        Write-Host "  Task not found" -ForegroundColor Yellow
    }
}

function Create-MonitorTask {
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host "CREATING PERSISTENT SPAWN MONITOR TASK" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
    
    # Verify prerequisites
    if (-not (Test-Path $PythonPath)) {
        Write-Host "[X] Python not found at: $PythonPath" -ForegroundColor Red
        exit 1
    }
    
    if (-not (Test-Path $MonitorScript)) {
        Write-Host "[X] Monitor script not found at: $MonitorScript" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "[OK] Python: $PythonPath" -ForegroundColor Green
    Write-Host "[OK] Script: $MonitorScript" -ForegroundColor Green
    
    # Remove existing task if present
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Host "[*] Removing existing task..." -ForegroundColor Yellow
        if ($existingTask.State -eq "Running") {
            Stop-ScheduledTask -TaskName $TaskName
        }
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    
    # Create action
    $action = New-ScheduledTaskAction `
        -Execute $PythonPath `
        -Argument $TaskArguments `
        -WorkingDirectory $WorkingDir
    
    # Create triggers
    $triggers = @(
        # Run at system startup
        (New-ScheduledTaskTrigger -AtStartup),
        # Also run at logon as backup
        (New-ScheduledTaskTrigger -AtLogOn)
    )
    
    # Create settings for PERSISTENCE
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RestartInterval (New-TimeSpan -Minutes 1) `
        -RestartCount 999 `
        -ExecutionTimeLimit (New-TimeSpan -Days 365) `
        -MultipleInstances IgnoreNew `
        -Priority 4
    
    # Create principal (run whether logged in or not requires admin)
    $principal = New-ScheduledTaskPrincipal `
        -UserId $env:USERNAME `
        -LogonType Interactive `
        -RunLevel Limited
    
    # Register the task
    Write-Host "[*] Registering scheduled task..." -ForegroundColor Cyan
    
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Description $TaskDescription `
        -Action $action `
        -Trigger $triggers `
        -Settings $settings `
        -Principal $principal `
        -Force
    
    Write-Host "[OK] Task registered: $TaskName" -ForegroundColor Green
    
    # Start the task immediately
    Write-Host "[*] Starting task..." -ForegroundColor Cyan
    Start-ScheduledTask -TaskName $TaskName
    
    Start-Sleep -Seconds 2
    
    $task = Get-ScheduledTask -TaskName $TaskName
    if ($task.State -eq "Running") {
        Write-Host "[OK] Task is now RUNNING" -ForegroundColor Green
    } else {
        Write-Host "[!] Task state: $($task.State)" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host "SPAWN MONITOR TASK CREATED SUCCESSFULLY" -ForegroundColor Green
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Features:" -ForegroundColor Cyan
    Write-Host "  [PERSISTENT]  Auto-restart on failure (999 retries)"
    Write-Host "  [REACTIVE]    File watching for immediate response"
    Write-Host "  [CAUTIOUS]    Read-only validation, extensive logging"
    Write-Host "  [ALWAYS ON]   Runs at startup, no execution time limit"
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor Cyan
    Write-Host "  Check status:  .\setup_spawn_monitor_task.ps1 -Status"
    Write-Host "  Remove task:   .\setup_spawn_monitor_task.ps1 -Remove"
    Write-Host "  View logs:     Get-Content E:\wellness_studio\ai_safety\logs\spawn_monitor.log -Tail 50"
    Write-Host ""
}

# Main execution
if ($Status) {
    Show-TaskStatus
} elseif ($Remove) {
    Remove-MonitorTask
} else {
    Create-MonitorTask
}
