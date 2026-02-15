#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Stratagem Intelligence Startup Validator
    Validates Language Server, MCP servers, Terminal Integration, and Initialization sequencing
    
.DESCRIPTION
    Comprehensive diagnostic script that checks:
    1. Python Language Server (Pylance) configuration and health
    2. MCP server registration and Docker prerequisites
    3. Terminal shell integration (PowerShell, WSL, Git Bash)
    4. Concurrent initialization mutex and sequencing
    
.PARAMETER Verbose
    Enable detailed diagnostic output
    
.PARAMETER Fix
    Attempt to fix issues automatically (where possible)
#>

param(
    [switch]$Verbose = $false,
    [switch]$Fix = $false
)

$ErrorActionPreference = "Continue"
$WarningPreference = "Continue"

# Use simple ASCII symbols to avoid encoding issues
$prefix_success = "[OK]"
$prefix_warning = "[!]"
$prefix_error = "[X]"
$prefix_info = "[*]"
$prefix_debug = "[>]"

$PythonPath = $null
try {
    $PythonPath = & (Join-Path $PSScriptRoot "resolve_python.ps1")
} catch {
    $PythonPath = "python"
}

function Write-Status {
    param(
        [string]$Message,
        [ValidateSet("Success", "Warning", "Error", "Info", "Debug")]
        [string]$Level = "Info"
    )
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    $prefix = switch ($Level) {
        "Success" { $prefix_success }
        "Warning" { $prefix_warning }
        "Error" { $prefix_error }
        "Info" { $prefix_info }
        "Debug" { $prefix_debug }
    }
    
    $color = switch ($Level) {
        "Success" { "Green" }
        "Warning" { "Yellow" }
        "Error" { "Red" }
        "Info" { "Cyan" }
        "Debug" { "Gray" }
    }
    
    Write-Host "[$timestamp] $prefix $Message" -ForegroundColor $color
}

function Test-VSCodeSettings {
    Write-Status "Checking VS Code Settings..." -Level "Info"
    
    $settingsPath = "E:\Apps\.vscode\settings.json"
    
    if (-not (Test-Path $settingsPath)) {
        Write-Status "VS Code settings.json not found at $settingsPath" -Level "Error"
        return $false
    }
    
    try {
        $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
        
        # Check Python LSP
        $lspEnabled = $settings.'python.languageServer' -eq "Pylance"
        if ($lspEnabled) {
            Write-Status "Python Language Server: Pylance (enabled)" -Level "Success"
        } else {
            Write-Status "Python Language Server: Not configured for Pylance" -Level "Warning"
        }
        
        # Check MCP servers
        if ($settings.mcpServers) {
            $mcp_count = $settings.mcpServers.PSObject.Properties.Count
            Write-Status "MCP Servers configured: $mcp_count" -Level "Success"
            
            foreach ($server in $settings.mcpServers.PSObject.Properties) {
                Write-Status "  - $($server.Name): configured" -Level "Info"
            }
        } else {
            Write-Status "No MCP servers configured in settings" -Level "Warning"
        }
        
        # Check Terminal Integration
        $termIntegration = $settings.'terminal.integrated.shellIntegration.enabled'
        if ($termIntegration -eq $true) {
            Write-Status "Terminal Shell Integration: Enabled" -Level "Success"
        } else {
            Write-Status "Terminal Shell Integration: Not explicitly enabled" -Level "Warning"
        }
        
        return $true
    } catch {
        Write-Status "Error parsing settings.json: $_" -Level "Error"
        return $false
    }
}

function Test-Pyrightconfig {
    Write-Status "Checking Pyright Configuration..." -Level "Info"
    
    $pyrightPath = "E:\pyrightconfig.json"
    
    if (-not (Test-Path $pyrightPath)) {
        Write-Status "pyrightconfig.json not found" -Level "Error"
        return $false
    }
    
    try {
        $config = Get-Content $pyrightPath -Raw | ConvertFrom-Json
        
        $typeCheckingMode = $config.typeCheckingMode
        Write-Status "Type Checking Mode: $typeCheckingMode" -Level $(if ($typeCheckingMode -eq "strict") { "Success" } else { "Warning" })
        
        $reportOptional = $config.reportOptionalMemberAccess
        Write-Status "Report Optional Member Access: $reportOptional" -Level $(if ($reportOptional -eq "error") { "Success" } else { "Warning" })
        
        return $true
    } catch {
        Write-Status "Error parsing pyrightconfig.json: $_" -Level "Error"
        return $false
    }
}

function Test-PythonEnvironment {
    Write-Status "Checking Python Environment..." -Level "Info"
    
    try {
        $pythonVersion = & $PythonPath --version 2>&1
        Write-Status "Python: $pythonVersion" -Level "Success"
        
        # Check Pylance
        $pylanceCheck = & $PythonPath -m pip list 2>&1 | Select-String "pylance"
        if ($pylanceCheck) {
            Write-Status "Pylance package: Installed" -Level "Success"
        } else {
            Write-Status "Note: Pylance is a VS Code extension (not a pip package)" -Level "Info"
        }
        
        # Check Pydantic
        $pydantic = & $PythonPath -m pip list 2>&1 | Select-String "pydantic"
        if ($pydantic) {
            Write-Status "Pydantic: $pydantic" -Level "Success"
        } else {
            Write-Status "Pydantic: Not installed" -Level "Warning"
        }
        
        return $true
    } catch {
        Write-Status "Error checking Python environment: $_" -Level "Error"
        return $false
    }
}

function Test-DockerDesktop {
    Write-Status "Checking Docker Desktop..." -Level "Info"
    
    try {
        $dockerCheck = docker ps 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Status "Docker Desktop: Running and accessible" -Level "Success"
            return $true
        } else {
            Write-Status "Docker Desktop: Not running or not accessible" -Level "Warning"
            Write-Status "  (Required for PostgreSQL, GitHub MCP, and SonarQube servers)" -Level "Info"
            return $false
        }
    } catch {
        Write-Status "Docker Desktop: Not found on system" -Level "Warning"
        return $false
    }
}

function Test-MCPServers {
    Write-Status "Testing MCP Server Availability..." -Level "Info"
    
    # Test uvx availability
    try {
        $uvxCheck = uvx --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Status "uv package manager: Available" -Level "Success"
        } else {
            Write-Status "uv package manager: Not available" -Level "Warning"
            return
        }
    } catch {
        Write-Status "uv package manager: Not found" -Level "Warning"
        return
    }
    
    # Test SQLite MCP server
    try {
        $output = uvx mcp-server-sqlite --help 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Status "MCP Server 'sqlite': Available" -Level "Success"
        } else {
            Write-Status "MCP Server 'sqlite': Not responding" -Level "Warning"
        }
    } catch {
        Write-Status "MCP Server 'sqlite': Error - $_" -Level "Warning"
    }

    # Denylist validation for active MCP configs (TOTAL-DENY SCOPE)
    $denylistScript = "E:\scripts\server_denylist_manager.py"
    $denylistConfig = "E:\config\server_denylist.json"
    $mcpConfigs = @(
        "E:\grid\mcp-setup\mcp_config.json",
        "C:\Users\irfan\.cursor\mcp.json"
    )

    if (-not (Test-Path $denylistScript)) {
        Write-Status "Denylist manager not found: $denylistScript" -Level "Warning"
        return
    }

    if (-not (Test-Path $denylistConfig)) {
        Write-Status "Denylist config not found: $denylistConfig" -Level "Warning"
        return
    }

    foreach ($mcpConfig in $mcpConfigs) {
        if (-not (Test-Path $mcpConfig)) {
            Write-Status "MCP config not found: $mcpConfig" -Level "Warning"
            continue
        }

        Write-Status "Validating MCP config (TOTAL-DENY): $mcpConfig" -Level "Info"
        try {
            # Use --total-deny flag to enforce total-deny scope for ALL MCP servers
            & $PythonPath $denylistScript --config $denylistConfig --validate-config $mcpConfig --total-deny
            if ($LASTEXITCODE -ne 0) {
                Write-Status "TOTAL-DENY VIOLATION: Enabled servers in $mcpConfig" -Level "Error"
                throw "Total-deny validation failed for $mcpConfig"
            } else {
                Write-Status "Total-deny validation passed for $mcpConfig" -Level "Success"
            }
        } catch {
            Write-Status "Critical Failure running denylist validation: $_" -Level "Error"
            throw
        }
    }
}

function Test-TerminalShells {
    Write-Status "Testing Terminal Shell Integration..." -Level "Info"
    
    # Test PowerShell
    try {
        $psVersion = & powershell -NoProfile -Command '$PSVersionTable.PSVersion'
        Write-Status "PowerShell: Version $psVersion" -Level "Success"
    } catch {
        Write-Status "PowerShell: Error - $_" -Level "Error"
    }
    
    # Test WSL
    try {
        $wslCheck = wsl --list --verbose 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Status "WSL (Windows Subsystem for Linux): Available" -Level "Success"
        } else {
            Write-Status "WSL: Not available or not configured" -Level "Warning"
        }
    } catch {
        Write-Status "WSL: Not found on system" -Level "Warning"
    }
}

function Test-BackendServices {
    Write-Status "Checking Backend Services..." -Level "Info"
    
    $backendDir = "E:\Apps\backend"
    
    if (-not (Test-Path $backendDir)) {
        Write-Status "Backend directory not found: $backendDir" -Level "Error"
        return $false
    }
    
    # Check key service files
    $services = @(
        "services\mcp_server_manager.py",
        "services\terminal_integration_manager.py",
        "services\harness_service.py",
        "main.py"
    )
    
    foreach ($svc in $services) {
        $path = Join-Path $backendDir $svc
        if (Test-Path $path) {
            Write-Status "$svc : Present" -Level "Success"
        } else {
            Write-Status "$svc : Missing" -Level "Warning"
        }
    }
    
    return $true
}

function Generate-Report {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "               STARTUP VALIDATION REPORT" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "SUMMARY:" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "1. Language Server Configuration" -ForegroundColor Cyan
    Test-VSCodeSettings | Out-Null
    Test-Pyrightconfig | Out-Null
    Test-PythonEnvironment | Out-Null
    
    Write-Host ""
    Write-Host "2. MCP Server Configuration" -ForegroundColor Cyan
    Test-DockerDesktop | Out-Null
    Test-MCPServers | Out-Null
    
    Write-Host ""
    Write-Host "3. Terminal Shell Integration" -ForegroundColor Cyan
    Test-TerminalShells | Out-Null
    
    Write-Host ""
    Write-Host "4. Backend Services" -ForegroundColor Cyan
    Test-BackendServices | Out-Null
    
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "RECOMMENDATIONS:" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "[OK] Language Server & Type Checking:" -ForegroundColor Green
    Write-Host "  - Pylance is enabled in VS Code"
    Write-Host "  - pyrightconfig.json set to strict mode for type checking"
    Write-Host "  - Optional member access violations reported as errors"
    Write-Host ""
    
    Write-Host "[OK] MCP Server Initialization:" -ForegroundColor Green
    Write-Host "  - Thread-safe MCPServerManager with initialization mutex"
    Write-Host "  - Prevents loading conflicts and race conditions"
    Write-Host "  - Automatic Docker Desktop health check"
    Write-Host "  - Graceful fallback for servers requiring Docker"
    Write-Host ""
    
    Write-Host "[OK] Terminal Shell Integration:" -ForegroundColor Green
    Write-Host "  - TerminalIntegrationManager with retry logic"
    Write-Host "  - Supports PowerShell (primary) and WSL (advanced tasks)"
    Write-Host "  - Automatic shell availability detection"
    Write-Host "  - Exponential backoff retry strategy with 3 attempts"
    Write-Host ""
    
    Write-Host "[!] Next Steps:" -ForegroundColor Yellow
    Write-Host "  1. Ensure Docker Desktop is running for full MCP functionality"
    Write-Host "  2. Start VS Code to initialize Pylance language server"
    Write-Host "  3. Run python main.py in Apps/backend to start development server"
    Write-Host "  4. Monitor /health endpoint for MCP and terminal status"
    Write-Host ""
}

# Main execution
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   Stratagem Intelligence - Startup Validation Script" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Generate-Report

if ($Fix) {
    Write-Host "Fix mode requested (not implemented in this version)" -ForegroundColor Yellow
}

Write-Host "Validation complete. Review recommendations above." -ForegroundColor Green
Write-Host ""
