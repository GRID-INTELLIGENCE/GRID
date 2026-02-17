#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Integrate MCP Enforcement into System Startup
    
.DESCRIPTION
    Sets up enforcement hooks to run:
    - At Windows startup (via Scheduled Task)
    - At user logon
    - Before VS Code launches (via profile integration)
    
.PARAMETER Install
    Install all startup integrations
    
.PARAMETER Remove
    Remove all startup integrations
    
.PARAMETER Status
    Show current integration status
#>

param(
    [switch]$Install = $false,
    [switch]$Remove = $false,
    [switch]$Status = $false
)

$ErrorActionPreference = "Stop"

$EnforcementHook = "E:\scripts\mcp_enforcement_hook.ps1"
$SpawnMonitorTask = "E:\scripts\setup_spawn_monitor_task.ps1"
$ProfileIntegration = @"

# MCP Total-Deny Enforcement Hook (AI Safety)
if (Test-Path "E:\scripts\mcp_enforcement_hook.ps1") {
    & "E:\scripts\mcp_enforcement_hook.ps1" -Silent -LogOnly
}
"@

function Show-IntegrationStatus {
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host "MCP ENFORCEMENT INTEGRATION STATUS" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
    
    # Check enforcement hook
    Write-Host ""
    Write-Host "1. Enforcement Hook Script" -ForegroundColor Cyan
    if (Test-Path $EnforcementHook) {
        Write-Host "   [OK] $EnforcementHook" -ForegroundColor Green
    } else {
        Write-Host "   [X] Not found: $EnforcementHook" -ForegroundColor Red
    }
    
    # Check spawn monitor task
    Write-Host ""
    Write-Host "2. Spawn Monitor Scheduled Task" -ForegroundColor Cyan
    $task = Get-ScheduledTask -TaskName "MCP_SpawnMonitor_TotalDeny" -ErrorAction SilentlyContinue
    if ($task) {
        Write-Host "   [OK] Task registered, State: $($task.State)" -ForegroundColor Green
    } else {
        Write-Host "   [X] Task not registered" -ForegroundColor Yellow
    }
    
    # Check PowerShell profile integration
    Write-Host ""
    Write-Host "3. PowerShell Profile Integration" -ForegroundColor Cyan
    $profilePath = $PROFILE.CurrentUserAllHosts
    if (Test-Path $profilePath) {
        $profileContent = Get-Content $profilePath -Raw
        if ($profileContent -match "mcp_enforcement_hook") {
            Write-Host "   [OK] Profile integration active" -ForegroundColor Green
        } else {
            Write-Host "   [X] Profile integration not found" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   [X] Profile does not exist: $profilePath" -ForegroundColor Yellow
    }
    
    # Check recent logs
    Write-Host ""
    Write-Host "4. Recent Activity" -ForegroundColor Cyan
    $enforcementLog = "E:\wellness_studio\ai_safety\logs\enforcement_hook.log"
    $monitorLog = "E:\wellness_studio\ai_safety\logs\spawn_monitor.log"
    
    if (Test-Path $enforcementLog) {
        $lastEntry = Get-Content $enforcementLog -Tail 1
        Write-Host "   Enforcement: $lastEntry" -ForegroundColor Gray
    }
    
    if (Test-Path $monitorLog) {
        $lastEntry = Get-Content $monitorLog -Tail 1
        Write-Host "   Monitor: $lastEntry" -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Cyan
}

function Install-Integrations {
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host "INSTALLING MCP ENFORCEMENT INTEGRATIONS" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
    
    # 1. Setup spawn monitor scheduled task
    Write-Host ""
    Write-Host "[1/3] Setting up Spawn Monitor Scheduled Task..." -ForegroundColor Cyan
    if (Test-Path $SpawnMonitorTask) {
        & $SpawnMonitorTask
    } else {
        Write-Host "   [!] Spawn monitor setup script not found" -ForegroundColor Yellow
    }
    
    # 2. Add to PowerShell profile
    Write-Host ""
    Write-Host "[2/3] Adding to PowerShell Profile..." -ForegroundColor Cyan
    $profilePath = $PROFILE.CurrentUserAllHosts
    $profileDir = Split-Path $profilePath -Parent
    
    if (-not (Test-Path $profileDir)) {
        New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
    }
    
    if (Test-Path $profilePath) {
        $profileContent = Get-Content $profilePath -Raw
        if ($profileContent -match "mcp_enforcement_hook") {
            Write-Host "   [OK] Already integrated" -ForegroundColor Green
        } else {
            Add-Content -Path $profilePath -Value $ProfileIntegration
            Write-Host "   [OK] Added enforcement hook to profile" -ForegroundColor Green
        }
    } else {
        Set-Content -Path $profilePath -Value $ProfileIntegration
        Write-Host "   [OK] Created profile with enforcement hook" -ForegroundColor Green
    }
    
    # 3. Run initial validation
    Write-Host ""
    Write-Host "[3/3] Running initial validation..." -ForegroundColor Cyan
    if (Test-Path $EnforcementHook) {
        & $EnforcementHook -LogOnly
    }
    
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host "INTEGRATION COMPLETE" -ForegroundColor Green
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Active Protections:" -ForegroundColor Cyan
    Write-Host "  [PERSISTENT]  Spawn monitor runs continuously"
    Write-Host "  [REACTIVE]    File watching detects config changes"
    Write-Host "  [CAUTIOUS]    Read-only validation, no mutations"
    Write-Host "  [ALWAYS ON]   Integrated into startup and profile"
    Write-Host ""
}

function Remove-Integrations {
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host "REMOVING MCP ENFORCEMENT INTEGRATIONS" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
    
    # 1. Remove scheduled task
    Write-Host ""
    Write-Host "[1/2] Removing Scheduled Task..." -ForegroundColor Cyan
    if (Test-Path $SpawnMonitorTask) {
        & $SpawnMonitorTask -Remove
    }
    
    # 2. Remove from PowerShell profile
    Write-Host ""
    Write-Host "[2/2] Removing from PowerShell Profile..." -ForegroundColor Cyan
    $profilePath = $PROFILE.CurrentUserAllHosts
    if (Test-Path $profilePath) {
        $content = Get-Content $profilePath -Raw
        $newContent = $content -replace '(?s)# MCP Total-Deny Enforcement Hook.*?mcp_enforcement_hook\.ps1.*?-LogOnly\s*\}', ''
        Set-Content -Path $profilePath -Value $newContent.Trim()
        Write-Host "   [OK] Removed from profile" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host "INTEGRATIONS REMOVED" -ForegroundColor Green
    Write-Host "=" * 60 -ForegroundColor Cyan
}

# Main execution
if ($Status) {
    Show-IntegrationStatus
} elseif ($Remove) {
    Remove-Integrations
} elseif ($Install) {
    Install-Integrations
} else {
    Write-Host "Usage: .\integrate_enforcement.ps1 [-Install|-Remove|-Status]"
    Write-Host ""
    Write-Host "  -Install  Install all startup integrations"
    Write-Host "  -Remove   Remove all startup integrations"
    Write-Host "  -Status   Show current integration status"
}
