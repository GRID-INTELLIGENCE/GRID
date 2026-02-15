#!/usr/bin/env pwsh
<#
.SYNOPSIS
    OFF-Switch for MCP Servers and Background Tasks

.DESCRIPTION
    Single-command script to disable all MCP servers, kill stray processes,
    and stop background monitoring tasks.
    
    Actions performed:
    1. Kill Python processes running MCP servers
    2. Stop and disable MCP_SpawnMonitor_TotalDeny scheduled task
    3. Disable all MCP servers in config files
    4. Clean spawn monitor state files

.PARAMETER Status
    Show current state without making changes

.PARAMETER Restore
    Re-enable systems (reverse the OFF-switch)

.EXAMPLE
    .\off_switch.ps1           # Disable everything
    .\off_switch.ps1 -Status   # Show current state
    .\off_switch.ps1 -Restore  # Re-enable everything
#>

param(
    [switch]$Status = $false,
    [switch]$Restore = $false
)

$ErrorActionPreference = "Continue"

# Configuration
$TaskName = "MCP_SpawnMonitor_TotalDeny"
$MCPConfigs = @(
    "E:\work\GRID\mcp-setup\mcp_config.json",
    "C:\Users\irfan\.cursor\mcp.json"
)
$MonitorStateFile = "E:\work\wellness_studio\ai_safety\monitoring\.monitor_state.json"
$DenylistConfig = "E:\config\server_denylist.json"

function Write-Header($text) {
    Write-Host ""
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host $text -ForegroundColor Cyan
    Write-Host ("=" * 60) -ForegroundColor Cyan
}

function Write-Action($action, $status, $color = "Green") {
    Write-Host "  [$status] " -ForegroundColor $color -NoNewline
    Write-Host $action
}

function Get-MCPProcesses {
    $processes = @()
    try {
        $pythonProcs = Get-Process -Name python, python3, py -ErrorAction SilentlyContinue
        foreach ($proc in $pythonProcs) {
            try {
                $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)" -ErrorAction SilentlyContinue).CommandLine
                if ($cmdLine -match "mcp|spawn_monitor") {
                    $processes += @{
                        Process = $proc
                        CommandLine = $cmdLine
                    }
                }
            } catch {}
        }
    } catch {}
    return $processes
}

function Show-Status {
    Write-Header "OFF-SWITCH STATUS"
    
    # Check scheduled task
    Write-Host "`nScheduled Task:" -ForegroundColor Yellow
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($task) {
        $stateColor = if ($task.State -eq "Running") { "Red" } elseif ($task.State -eq "Disabled") { "Green" } else { "Yellow" }
        Write-Action "Task '$TaskName'" $task.State $stateColor
    } else {
        Write-Action "Task '$TaskName'" "NOT FOUND" "Gray"
    }
    
    # Check MCP processes
    Write-Host "`nMCP Processes:" -ForegroundColor Yellow
    $mcpProcs = Get-MCPProcesses
    if ($mcpProcs.Count -eq 0) {
        Write-Action "No MCP processes running" "OK" "Green"
    } else {
        foreach ($p in $mcpProcs) {
            Write-Action "PID $($p.Process.Id): $($p.CommandLine.Substring(0, [Math]::Min(60, $p.CommandLine.Length)))..." "RUNNING" "Red"
        }
    }
    
    # Check MCP configs
    Write-Host "`nMCP Configs:" -ForegroundColor Yellow
    foreach ($configPath in $MCPConfigs) {
        if (Test-Path $configPath) {
            try {
                $config = Get-Content $configPath -Raw | ConvertFrom-Json
                $servers = @()
                
                # Handle different config formats
                if ($config.servers) {
                    $servers = $config.servers
                } elseif ($config.mcpServers) {
                    $servers = $config.mcpServers.PSObject.Properties | ForEach-Object { $_.Value }
                }
                
                $enabled = ($servers | Where-Object { -not $_.disabled }).Count
                $total = $servers.Count
                
                if ($enabled -eq 0) {
                    Write-Action "$(Split-Path $configPath -Leaf): $total servers (all disabled)" "OFF" "Green"
                } else {
                    Write-Action "$(Split-Path $configPath -Leaf): $enabled/$total servers enabled" "ON" "Red"
                }
            } catch {
                Write-Action "$(Split-Path $configPath -Leaf): Parse error" "ERROR" "Red"
            }
        } else {
            Write-Action "$(Split-Path $configPath -Leaf): Not found" "N/A" "Gray"
        }
    }
    
    # Check monitor state file
    Write-Host "`nMonitor State:" -ForegroundColor Yellow
    if (Test-Path $MonitorStateFile) {
        Write-Action "State file exists" "ACTIVE" "Yellow"
    } else {
        Write-Action "No state file" "CLEAN" "Green"
    }
    
    Write-Host ""
}

function Invoke-OffSwitch {
    Write-Header "OFF-SWITCH: DISABLING ALL MCP SYSTEMS"
    
    $actions = 0
    
    # 1. Kill MCP processes
    Write-Host "`n[1/4] Killing MCP Processes..." -ForegroundColor Yellow
    $mcpProcs = Get-MCPProcesses
    if ($mcpProcs.Count -eq 0) {
        Write-Action "No MCP processes found" "SKIP" "Gray"
    } else {
        foreach ($p in $mcpProcs) {
            try {
                Stop-Process -Id $p.Process.Id -Force -ErrorAction Stop
                Write-Action "Killed PID $($p.Process.Id)" "DONE" "Green"
                $actions++
            } catch {
                Write-Action "Failed to kill PID $($p.Process.Id)" "FAIL" "Red"
            }
        }
    }
    
    # 2. Stop and disable scheduled task
    Write-Host "`n[2/4] Disabling Scheduled Task..." -ForegroundColor Yellow
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($task) {
        if ($task.State -eq "Running") {
            Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
            Write-Action "Stopped task" "DONE" "Green"
            $actions++
        }
        if ($task.State -ne "Disabled") {
            Disable-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue | Out-Null
            Write-Action "Disabled task" "DONE" "Green"
            $actions++
        } else {
            Write-Action "Task already disabled" "SKIP" "Gray"
        }
    } else {
        Write-Action "Task not found" "SKIP" "Gray"
    }
    
    # 3. Disable all MCP servers in configs
    Write-Host "`n[3/4] Disabling MCP Servers in Configs..." -ForegroundColor Yellow
    foreach ($configPath in $MCPConfigs) {
        if (Test-Path $configPath) {
            try {
                $config = Get-Content $configPath -Raw | ConvertFrom-Json
                $modified = $false
                
                # Handle array format (servers)
                if ($config.servers) {
                    foreach ($server in $config.servers) {
                        if (-not $server.disabled) {
                            $server | Add-Member -NotePropertyName "disabled" -NotePropertyValue $true -Force
                            $modified = $true
                        }
                    }
                }
                
                # Handle object format (mcpServers)
                if ($config.mcpServers) {
                    foreach ($prop in $config.mcpServers.PSObject.Properties) {
                        if (-not $prop.Value.disabled) {
                            $prop.Value | Add-Member -NotePropertyName "disabled" -NotePropertyValue $true -Force
                            $modified = $true
                        }
                    }
                }
                
                if ($modified) {
                    $config | ConvertTo-Json -Depth 10 | Set-Content $configPath
                    Write-Action "Updated $(Split-Path $configPath -Leaf)" "DONE" "Green"
                    $actions++
                } else {
                    Write-Action "$(Split-Path $configPath -Leaf) already disabled" "SKIP" "Gray"
                }
            } catch {
                Write-Action "Failed to update $(Split-Path $configPath -Leaf): $_" "FAIL" "Red"
            }
        } else {
            Write-Action "$(Split-Path $configPath -Leaf) not found" "SKIP" "Gray"
        }
    }
    
    # 4. Clean state files
    Write-Host "`n[4/4] Cleaning State Files..." -ForegroundColor Yellow
    if (Test-Path $MonitorStateFile) {
        Remove-Item $MonitorStateFile -Force -ErrorAction SilentlyContinue
        Write-Action "Removed monitor state file" "DONE" "Green"
        $actions++
    } else {
        Write-Action "No state file to clean" "SKIP" "Gray"
    }
    
    Write-Header "OFF-SWITCH COMPLETE"
    Write-Host "`nActions taken: $actions" -ForegroundColor $(if ($actions -gt 0) { "Green" } else { "Yellow" })
    Write-Host "All MCP systems are now OFF.`n" -ForegroundColor Green
}

function Invoke-Restore {
    Write-Header "RESTORE: RE-ENABLING MCP SYSTEMS"
    
    $actions = 0
    
    # 1. Re-enable scheduled task
    Write-Host "`n[1/2] Re-enabling Scheduled Task..." -ForegroundColor Yellow
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($task) {
        if ($task.State -eq "Disabled") {
            Enable-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue | Out-Null
            Write-Action "Enabled task" "DONE" "Green"
            $actions++
        }
        if ($task.State -ne "Running") {
            Start-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
            Write-Action "Started task" "DONE" "Green"
            $actions++
        }
    } else {
        Write-Action "Task not found - run setup_spawn_monitor_task.ps1 to create" "WARN" "Yellow"
    }
    
    # 2. Note about MCP servers
    Write-Host "`n[2/2] MCP Server Configs..." -ForegroundColor Yellow
    Write-Action "MCP configs left disabled (manual enable recommended)" "INFO" "Yellow"
    Write-Host "    To re-enable specific servers, edit the config files and set 'disabled: false'" -ForegroundColor Gray
    
    Write-Header "RESTORE COMPLETE"
    Write-Host "`nActions taken: $actions" -ForegroundColor $(if ($actions -gt 0) { "Green" } else { "Yellow" })
    Write-Host "Spawn monitor task restored. MCP servers require manual config edit.`n" -ForegroundColor Green
}

# Main execution
if ($Status) {
    Show-Status
} elseif ($Restore) {
    Invoke-Restore
} else {
    Invoke-OffSwitch
}
