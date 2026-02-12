#!/usr/bin/env pwsh
<#
.SYNOPSIS
    MCP Enforcement Hook - Persistent Pre-Launch Validation
    
.DESCRIPTION
    Validates MCP configurations against denylist before any startup.
    This script is designed to be:
    - PERSISTENT: Integrated into system startup and VS Code launch
    - REACTIVE: Validates immediately when called
    - CAUTIOUS: Read-only, never modifies configs, detailed logging
    
.PARAMETER Block
    If violations found, return exit code 1 to block startup
    
.PARAMETER Silent
    Suppress console output (for background/scheduled runs)
    
.PARAMETER LogOnly
    Log violations but don't block (monitoring mode)
#>

param(
    [switch]$Block = $true,
    [switch]$Silent = $false,
    [switch]$LogOnly = $false
)

$ErrorActionPreference = "Continue"

# Configuration
$DenylistConfig = "E:\config\server_denylist.json"
$DenylistManager = "E:\scripts\server_denylist_manager.py"
$PythonPath = & (Join-Path $PSScriptRoot "resolve_python.ps1")
$LogDir = "E:\wellness_studio\ai_safety\logs"
$LogFile = "$LogDir\enforcement_hook.log"

$MCPConfigs = @(
    "E:\grid\mcp-setup\mcp_config.json",
    "C:\Users\irfan\.cursor\mcp.json"
)

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    # Ensure log directory exists
    if (-not (Test-Path $LogDir)) {
        New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    }
    
    # Append to log file
    Add-Content -Path $LogFile -Value $logEntry
    
    # Console output unless silent
    if (-not $Silent) {
        $color = switch ($Level) {
            "ERROR" { "Red" }
            "WARN" { "Yellow" }
            "OK" { "Green" }
            default { "Cyan" }
        }
        Write-Host $logEntry -ForegroundColor $color
    }
}

function Test-Prerequisites {
    $missing = @()
    
    if (-not (Test-Path $PythonPath)) {
        $missing += "Python: $PythonPath"
    }
    
    if (-not (Test-Path $DenylistManager)) {
        $missing += "DenylistManager: $DenylistManager"
    }
    
    if (-not (Test-Path $DenylistConfig)) {
        $missing += "DenylistConfig: $DenylistConfig"
    }
    
    if ($missing.Count -gt 0) {
        Write-Log "Missing prerequisites: $($missing -join ', ')" -Level "ERROR"
        return $false
    }
    
    return $true
}

function Invoke-TotalDenyValidation {
    param([string]$ConfigPath)
    
    if (-not (Test-Path $ConfigPath)) {
        Write-Log "Config not found: $ConfigPath" -Level "WARN"
        return @{ Passed = $true; Violations = @() }
    }
    
    try {
        # Run validation with --total-deny flag (CAUTIOUS: read-only)
        $output = & $PythonPath $DenylistManager `
            --config $DenylistConfig `
            --validate-config $ConfigPath `
            --total-deny 2>&1
        
        $exitCode = $LASTEXITCODE
        
        if ($exitCode -eq 0) {
            return @{ Passed = $true; Violations = @() }
        } else {
            # Parse violations from output
            $violations = @()
            foreach ($line in $output) {
                if ($line -match "^\s+-\s+(\S+)\s+\(Reason:\s+([^)]+)\)") {
                    $violations += @{
                        Server = $Matches[1]
                        Reason = $Matches[2]
                        Config = $ConfigPath
                    }
                }
            }
            return @{ Passed = $false; Violations = $violations }
        }
    } catch {
        Write-Log "Validation error for $ConfigPath : $_" -Level "ERROR"
        return @{ Passed = $false; Violations = @(@{ Server = "VALIDATION_ERROR"; Reason = $_.ToString(); Config = $ConfigPath }) }
    }
}

function Write-ViolationReport {
    param([array]$AllViolations)
    
    Write-Log "=" * 60
    Write-Log "TOTAL-DENY ENFORCEMENT REPORT" -Level "ERROR"
    Write-Log "=" * 60
    
    $grouped = $AllViolations | Group-Object -Property Config
    
    foreach ($group in $grouped) {
        Write-Log "Config: $($group.Name)" -Level "WARN"
        foreach ($v in $group.Group) {
            Write-Log "  - $($v.Server) (Reason: $($v.Reason))" -Level "ERROR"
        }
    }
    
    Write-Log "=" * 60
    Write-Log "Total violations: $($AllViolations.Count)" -Level "ERROR"
    Write-Log "Action: $(if ($LogOnly) { 'LOGGED (monitoring mode)' } else { 'BLOCKED' })" -Level $(if ($LogOnly) { "WARN" } else { "ERROR" })
}

# Main execution
Write-Log "=" * 60
Write-Log "MCP ENFORCEMENT HOOK - TOTAL-DENY VALIDATION"
Write-Log "=" * 60

if (-not (Test-Prerequisites)) {
    Write-Log "Prerequisites check failed" -Level "ERROR"
    if ($Block -and -not $LogOnly) { exit 1 }
    exit 0
}

Write-Log "Validating MCP configs (TOTAL-DENY mode)..."

$allViolations = @()
$allPassed = $true

foreach ($config in $MCPConfigs) {
    Write-Log "Checking: $config"
    
    $result = Invoke-TotalDenyValidation -ConfigPath $config
    
    if ($result.Passed) {
        Write-Log "  [OK] No violations" -Level "OK"
    } else {
        $allPassed = $false
        $allViolations += $result.Violations
        Write-Log "  [X] $($result.Violations.Count) violation(s)" -Level "ERROR"
    }
}

if ($allViolations.Count -gt 0) {
    Write-ViolationReport -AllViolations $allViolations
    
    if ($Block -and -not $LogOnly) {
        Write-Log "STARTUP BLOCKED: Enabled MCP servers detected" -Level "ERROR"
        Write-Log "Disable all servers in MCP configs to proceed" -Level "WARN"
        exit 1
    }
} else {
    Write-Log "All MCP configs validated successfully" -Level "OK"
    Write-Log "Total-deny enforcement: PASSED" -Level "OK"
}

Write-Log "=" * 60
exit 0
