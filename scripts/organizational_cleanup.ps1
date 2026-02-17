#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Organizational Cleanup & Placement Validation
    
.DESCRIPTION
    Validates and cleans up enforcement system organization:
    - Identifies duplicate scripts and processes
    - Validates config paths consistency
    - Cleans up orphaned/duplicate processes
    - Archives legacy scripts
    
.PARAMETER Audit
    Run audit only, don't make changes
    
.PARAMETER Fix
    Apply fixes automatically
    
.PARAMETER Verbose
    Show detailed output
#>

param(
    [switch]$Audit = $true,
    [switch]$Fix = $false,
    [switch]$Verbose = $false
)

$ErrorActionPreference = "Continue"

# ============================================================================
# CONFIGURATION - Central paths for enforcement system
# ============================================================================
$Config = @{
    # Core config location
    DenylistConfig = "E:\config\server_denylist.json"
    DenylistSchema = "E:\config\server_denylist_schema.json"
    
    # AI Safety monitoring location
    MonitorDir = "E:\wellness_studio\ai_safety\monitoring"
    LogDir = "E:\wellness_studio\ai_safety\logs"
    SafetyConfig = "E:\wellness_studio\ai_safety\config"
    
    # Scripts location  
    ScriptsDir = "E:\scripts"
    
    # MCP configs to validate
    MCPConfigs = @(
        "E:\grid\mcp-setup\mcp_config.json",
        "C:\Users\irfan\.cursor\mcp.json"
    )
    
    # Archive location for legacy scripts
    ArchiveDir = "E:\scripts\_archive"
}

function Write-Audit {
    param(
        [string]$Category,
        [string]$Item,
        [ValidateSet("OK", "WARN", "ERROR", "INFO", "FIX")]
        [string]$Status,
        [string]$Message
    )
    
    $color = switch ($Status) {
        "OK" { "Green" }
        "WARN" { "Yellow" }
        "ERROR" { "Red" }
        "INFO" { "Cyan" }
        "FIX" { "Magenta" }
    }
    
    $prefix = switch ($Status) {
        "OK" { "[✓]" }
        "WARN" { "[!]" }
        "ERROR" { "[✗]" }
        "INFO" { "[·]" }
        "FIX" { "[→]" }
    }
    
    Write-Host "  $prefix " -ForegroundColor $color -NoNewline
    Write-Host "$Category | $Item" -NoNewline
    if ($Message) { Write-Host " - $Message" -ForegroundColor Gray }
    else { Write-Host "" }
}

# ============================================================================
# AUDIT FUNCTIONS
# ============================================================================

function Test-DuplicateProcesses {
    Write-Host "`n=== PROCESS AUDIT ===" -ForegroundColor Cyan
    
    $pythonProcesses = Get-Process python -ErrorAction SilentlyContinue
    $issues = @()
    
    # Get process info including parent PID
    $processInfo = Get-CimInstance -ClassName Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue
    $parentPids = $processInfo | ForEach-Object { $_.ProcessId }
    
    # Filter out child processes (where ParentProcessId is another python process)
    $rootProcesses = $processInfo | Where-Object { $_.ParentProcessId -notin $parentPids }
    
    # Group by script (only root processes)
    $grouped = $rootProcesses | Group-Object { ($_.CommandLine -split ' ')[1] }
    
    foreach ($group in $grouped) {
        $scriptName = Split-Path $group.Name -Leaf
        if ($group.Count -gt 1) {
            Write-Audit -Category "Process" -Item $scriptName -Status "WARN" -Message "DUPLICATE: $($group.Count) root instances (PIDs: $($group.Group.ProcessId -join ', '))"
            $issues += @{
                Type = "duplicate_process"
                Script = $group.Name
                PIDs = $group.Group.ProcessId
            }
        } else {
            if ($Verbose) {
                Write-Audit -Category "Process" -Item $scriptName -Status "OK" -Message "Single root (PID: $($group.Group[0].ProcessId))"
            }
        }
    }
    
    # Check if spawn monitor is running (use original for this check)
    $spawnMonitor = $pythonProcesses | Where-Object { $_.CommandLine -like "*spawn_monitor*" }
    if ($spawnMonitor.Count -eq 0) {
        Write-Audit -Category "Process" -Item "spawn_monitor.py" -Status "ERROR" -Message "NOT RUNNING"
        $issues += @{ Type = "missing_process"; Script = "spawn_monitor.py" }
    } elseif ($spawnMonitor.Count -eq 1) {
        Write-Audit -Category "Process" -Item "spawn_monitor.py" -Status "OK" -Message "Running (PID: $($spawnMonitor.Id))"
    }
    
    return $issues
}

function Test-DuplicateScripts {
    Write-Host "`n=== SCRIPT AUDIT ===" -ForegroundColor Cyan
    
    $duplicatePatterns = @(
        @{ Pattern = "extend_denylist*.ps1"; Keep = "extend_denylist.ps1" },
        @{ Pattern = "create_cursor_mcp*.ps1"; Keep = "create_cursor_mcp.ps1" },
        @{ Pattern = "disable_grid_servers*.ps1"; Keep = "disable_grid_servers.ps1" }
    )
    
    $issues = @()
    
    foreach ($dp in $duplicatePatterns) {
        $files = Get-ChildItem (Join-Path $Config.ScriptsDir $dp.Pattern) -ErrorAction SilentlyContinue
        if ($files.Count -gt 1) {
            $toArchive = $files | Where-Object { $_.Name -ne $dp.Keep }
            Write-Audit -Category "Script" -Item $dp.Pattern -Status "WARN" -Message "DUPLICATES: $($toArchive.Name -join ', ')"
            foreach ($f in $toArchive) {
                $issues += @{
                    Type = "duplicate_script"
                    Path = $f.FullName
                    Archive = $true
                }
            }
        } elseif ($files.Count -eq 1) {
            if ($Verbose) {
                Write-Audit -Category "Script" -Item $files[0].Name -Status "OK"
            }
        }
    }
    
    return $issues
}

function Test-ConfigConsistency {
    Write-Host "`n=== CONFIG AUDIT ===" -ForegroundColor Cyan
    
    $issues = @()
    
    # Check core config files exist
    $requiredConfigs = @(
        $Config.DenylistConfig,
        $Config.DenylistSchema,
        (Join-Path $Config.MonitorDir "spawn_monitor.py"),
        (Join-Path $Config.MonitorDir ".monitor_state.json")
    )
    
    foreach ($cfg in $requiredConfigs) {
        if (Test-Path $cfg) {
            $size = (Get-Item $cfg).Length
            Write-Audit -Category "Config" -Item (Split-Path $cfg -Leaf) -Status "OK" -Message "$size bytes"
        } else {
            Write-Audit -Category "Config" -Item (Split-Path $cfg -Leaf) -Status "ERROR" -Message "MISSING: $cfg"
            $issues += @{ Type = "missing_config"; Path = $cfg }
        }
    }
    
    # Check MCP configs
    foreach ($mcpCfg in $Config.MCPConfigs) {
        if (Test-Path $mcpCfg) {
            try {
                $content = Get-Content $mcpCfg -Raw | ConvertFrom-Json
                $serverCount = 0
                $disabledCount = 0
                
                # Handle different JSON structures
                if ($content.servers) {
                    $serverCount = $content.servers.Count
                    $disabledCount = ($content.servers | Where-Object { $_.enabled -eq $false }).Count
                } elseif ($content.mcpServers) {
                    $serverCount = ($content.mcpServers.PSObject.Properties).Count
                    $disabledCount = ($content.mcpServers.PSObject.Properties | Where-Object { $_.Value.disabled -eq $true }).Count
                }
                
                if ($serverCount -eq $disabledCount) {
                    Write-Audit -Category "MCP" -Item (Split-Path $mcpCfg -Leaf) -Status "OK" -Message "All $serverCount servers disabled"
                } else {
                    Write-Audit -Category "MCP" -Item (Split-Path $mcpCfg -Leaf) -Status "WARN" -Message "$disabledCount/$serverCount disabled"
                    $issues += @{ Type = "servers_enabled"; Path = $mcpCfg }
                }
            } catch {
                Write-Audit -Category "MCP" -Item (Split-Path $mcpCfg -Leaf) -Status "ERROR" -Message "Parse error"
            }
        } else {
            Write-Audit -Category "MCP" -Item (Split-Path $mcpCfg -Leaf) -Status "INFO" -Message "Not present"
        }
    }
    
    return $issues
}

function Test-LogDirectories {
    Write-Host "`n=== LOG STRUCTURE AUDIT ===" -ForegroundColor Cyan
    
    $requiredDirs = @(
        $Config.LogDir,
        (Join-Path $Config.LogDir "audit"),
        (Join-Path $Config.LogDir "enforcement"),
        (Join-Path $Config.LogDir "violation")
    )
    
    foreach ($dir in $requiredDirs) {
        if (Test-Path $dir) {
            $fileCount = (Get-ChildItem $dir -File -ErrorAction SilentlyContinue).Count
            Write-Audit -Category "LogDir" -Item (Split-Path $dir -Leaf) -Status "OK" -Message "$fileCount files"
        } else {
            Write-Audit -Category "LogDir" -Item (Split-Path $dir -Leaf) -Status "WARN" -Message "MISSING"
            if ($Fix) {
                New-Item -ItemType Directory -Path $dir -Force | Out-Null
                Write-Audit -Category "LogDir" -Item (Split-Path $dir -Leaf) -Status "FIX" -Message "Created"
            }
        }
    }
}

# ============================================================================
# FIX FUNCTIONS
# ============================================================================

function Invoke-FixDuplicateProcesses {
    param([array]$Issues)
    
    Write-Host "`n=== FIXING DUPLICATE PROCESSES ===" -ForegroundColor Magenta
    
    foreach ($issue in ($Issues | Where-Object { $_.Type -eq "duplicate_process" })) {
        $processIds = $issue.PIDs | Sort-Object
        $keepId = $processIds[0]  # Keep oldest
        $killIds = $processIds[1..($processIds.Count-1)]
        
        foreach ($procId in $killIds) {
            Write-Audit -Category "Fix" -Item "PID $procId" -Status "FIX" -Message "Stopping duplicate"
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        }
    }
}

function Invoke-ArchiveDuplicateScripts {
    param([array]$Issues)
    
    Write-Host "`n=== ARCHIVING DUPLICATE SCRIPTS ===" -ForegroundColor Magenta
    
    # Ensure archive dir exists
    if (-not (Test-Path $Config.ArchiveDir)) {
        New-Item -ItemType Directory -Path $Config.ArchiveDir -Force | Out-Null
    }
    
    foreach ($issue in ($Issues | Where-Object { $_.Type -eq "duplicate_script" })) {
        $filename = Split-Path $issue.Path -Leaf
        $archivePath = Join-Path $Config.ArchiveDir $filename
        
        Write-Audit -Category "Archive" -Item $filename -Status "FIX" -Message "Moving to _archive"
        Move-Item $issue.Path $archivePath -Force
    }
}

# ============================================================================
# MAIN
# ============================================================================

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     ORGANIZATIONAL CLEANUP & PLACEMENT VALIDATION          ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "Mode: $(if ($Fix) { 'FIX' } else { 'AUDIT ONLY' })" -ForegroundColor $(if ($Fix) { 'Magenta' } else { 'Cyan' })

$allIssues = @()

# Run audits
$allIssues += Test-DuplicateProcesses
$allIssues += Test-DuplicateScripts
$allIssues += Test-ConfigConsistency
Test-LogDirectories

# Summary
Write-Host "`n=== SUMMARY ===" -ForegroundColor Cyan
$issueCount = $allIssues.Count
if ($issueCount -eq 0) {
    Write-Host "  [✓] No issues found - organization is clean!" -ForegroundColor Green
} else {
    Write-Host "  [!] Found $issueCount issue(s)" -ForegroundColor Yellow
    
    if ($Fix) {
        Invoke-FixDuplicateProcesses -Issues $allIssues
        Invoke-ArchiveDuplicateScripts -Issues $allIssues
        Write-Host ""
        Write-Host "  [✓] Fixes applied" -ForegroundColor Green
    } else {
        Write-Host "  [*] Run with -Fix to apply corrections" -ForegroundColor Cyan
    }
}

Write-Host ""
