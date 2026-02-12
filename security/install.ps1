# ============================================================================
# Network Security System - Installation Script (Windows PowerShell)
# ============================================================================
# This script installs and configures the network security system
# for comprehensive network access control and monitoring.
#
# Usage:
#   .\security\install.ps1
#   .\security\install.ps1 -Quick    # Skip confirmation prompts
# ============================================================================

[CmdletBinding()]
param(
    [switch]$Quick
)

# Require Administrator privileges
#Requires -RunAsAdministrator

# Configuration
$ErrorActionPreference = "Stop"
$SecurityDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $SecurityDir

# ============================================================================
# Helper Functions
# ============================================================================

function Write-Header {
    param([string]$Message)
    Write-Host "============================================================================" -ForegroundColor Blue
    Write-Host $Message -ForegroundColor Blue
    Write-Host "============================================================================" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Cyan
}

function Confirm-Action {
    param([string]$Message)

    if ($Quick) {
        return $true
    }

    $response = Read-Host "$Message (y/n)"
    return $response -match '^[Yy]$'
}

# ============================================================================
# Installation Steps
# ============================================================================

Write-Header "🔒 NETWORK SECURITY SYSTEM INSTALLATION"
Write-Host ""
Write-Host "This script will install and configure comprehensive network security"
Write-Host "monitoring for your codebase. By default, ALL network access will be"
Write-Host "DENIED until explicitly whitelisted."
Write-Host ""
Write-Host "Installation directory: $SecurityDir"
Write-Host "Project root: $RootDir"
Write-Host ""

if (-not (Confirm-Action "Continue with installation?")) {
    Write-Host "Installation cancelled."
    exit 0
}

Write-Host ""

# ----------------------------------------------------------------------------
# Step 1: Check Python version
# ----------------------------------------------------------------------------

Write-Info "Step 1/8: Checking Python version..."

try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found"
    }
    Write-Success "Python found: $pythonVersion"
} catch {
    Write-Error-Custom "Python is not installed or not in PATH"
    Write-Host "Please install Python 3.8+ from https://www.python.org/"
    exit 1
}

Write-Host ""

# ----------------------------------------------------------------------------
# Step 2: Create logs directory
# ----------------------------------------------------------------------------

Write-Info "Step 2/8: Creating logs directory..."

$LogsDir = Join-Path $SecurityDir "logs"
if (-not (Test-Path $LogsDir)) {
    New-Item -ItemType Directory -Path $LogsDir -Force | Out-Null
}
Write-Success "Logs directory created: $LogsDir"
Write-Host ""

# ----------------------------------------------------------------------------
# Step 3: Install Python dependencies
# ----------------------------------------------------------------------------

Write-Info "Step 3/8: Installing Python dependencies..."

$RequirementsFile = Join-Path $SecurityDir "requirements.txt"
if (Test-Path $RequirementsFile) {
    Write-Host "   Installing from requirements.txt..."
    python -m pip install -r $RequirementsFile --quiet --disable-pip-version-check
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Dependencies installed"
    } else {
        Write-Warning-Custom "Some dependencies may have failed to install"
    }
} else {
    Write-Warning-Custom "requirements.txt not found, installing manually..."
    python -m pip install pyyaml rich --quiet --disable-pip-version-check
    Write-Success "Core dependencies installed"
}
Write-Host ""

# ----------------------------------------------------------------------------
# Step 4: Verify configuration file
# ----------------------------------------------------------------------------

Write-Info "Step 4/8: Verifying configuration file..."

$ConfigFile = Join-Path $SecurityDir "network_access_control.yaml"
if (Test-Path $ConfigFile) {
    Write-Success "Configuration file found: network_access_control.yaml"
} else {
    Write-Error-Custom "Configuration file not found!"
    Write-Host "Expected location: $ConfigFile"
    exit 1
}
Write-Host ""

# ----------------------------------------------------------------------------
# Step 5: Test security module
# ----------------------------------------------------------------------------

Write-Info "Step 5/8: Testing security module..."

Push-Location $RootDir
try {
    $testScript = @"
import sys
sys.path.insert(0, r'$RootDir')
try:
    import security
    print('Security module loaded successfully')
except Exception as e:
    print(f'Failed to load security module: {e}')
    sys.exit(1)
"@

    $result = python -c $testScript 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success $result
    } else {
        Write-Error-Custom "Failed to load security module"
        Write-Host $result
        exit 1
    }
} finally {
    Pop-Location
}

Write-Host ""

# ----------------------------------------------------------------------------
# Step 6: Scan codebase for network usage
# ----------------------------------------------------------------------------

Write-Info "Step 6/8: Scanning codebase for network usage..."
Write-Host "   This may take a few minutes for large projects..."
Write-Host ""

$IntegrationScript = Join-Path $SecurityDir "integrate_security.py"
if (Test-Path $IntegrationScript) {
    try {
        Push-Location $RootDir
        python $IntegrationScript --scan --root $RootDir
        Pop-Location
        Write-Host ""
    } catch {
        Write-Warning-Custom "Scan encountered some issues but continuing..."
        Write-Host ""
    }
} else {
    Write-Warning-Custom "Integration scanner not found, skipping scan"
    Write-Host ""
}

# ----------------------------------------------------------------------------
# Step 7: Create backup of configuration
# ----------------------------------------------------------------------------

Write-Info "Step 7/8: Creating configuration backup..."

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupFile = "$ConfigFile.backup.$timestamp"
Copy-Item $ConfigFile $BackupFile
Write-Success "Backup created: $(Split-Path -Leaf $BackupFile)"
Write-Host ""

# ----------------------------------------------------------------------------
# Step 8: Initialize security system
# ----------------------------------------------------------------------------

Write-Info "Step 8/8: Initializing security system..."

Push-Location $RootDir
try {
    $initScript = @"
import sys
sys.path.insert(0, r'$RootDir')
import os
os.environ['DISABLE_NETWORK_SECURITY'] = 'false'
import security
status = security.get_status()
print(f"Status: {status['status']}")
print(f"Mode: {status['mode']}")
print(f"Default Policy: {status['default_policy']}")
"@

    $result = python -c $initScript 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host $result
        Write-Success "Security system initialized"
    } else {
        Write-Error-Custom "Failed to initialize security system"
        Write-Host $result
        exit 1
    }
} finally {
    Pop-Location
}

Write-Host ""

# ============================================================================
# Post-Installation
# ============================================================================

Write-Header "✅ INSTALLATION COMPLETE"
Write-Host ""
Write-Host "Network security system has been installed and configured."
Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Green
Write-Host ""
Write-Host "1. Review the configuration:"
Write-Host "   Get-Content security\network_access_control.yaml"
Write-Host ""
Write-Host "2. Start monitoring (in a separate terminal):"
Write-Host "   python security\monitor_network.py dashboard"
Write-Host ""
Write-Host "3. Run your application and observe blocked requests:"
Write-Host "   python your_main_application.py"
Write-Host ""
Write-Host "4. Check what was blocked:"
Write-Host "   python security\monitor_network.py blocked"
Write-Host ""
Write-Host "5. Whitelist trusted domains:"
Write-Host "   python security\monitor_network.py add api.example.com"
Write-Host ""
Write-Host "6. Enable network access (after whitelisting):"
Write-Host "   python security\monitor_network.py enable"
Write-Host ""
Write-Host "⚠️  IMPORTANT:" -ForegroundColor Yellow
Write-Host "   - ALL network access is DENIED by default"
Write-Host "   - Review blocked requests carefully before whitelisting"
Write-Host "   - Monitor for data leaks: python security\monitor_network.py leaks"
Write-Host "   - Read documentation: security\README.md"
Write-Host ""
Write-Host "📁 Files and Directories:" -ForegroundColor Cyan
Write-Host "   Config:  $ConfigFile"
Write-Host "   Logs:    $LogsDir"
Write-Host "   Monitor: python security\monitor_network.py dashboard"
Write-Host ""
Write-Host "🔒 Security Status:" -ForegroundColor Green

Push-Location $RootDir
try {
    $statusScript = @"
import sys
sys.path.insert(0, r'$RootDir')
import security
security.print_status()
"@
    python -c $statusScript 2>$null
} catch {
    Write-Host "   Run: python -c 'import security; security.print_status()'"
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Blue
Write-Host ""

# ============================================================================
# Create quick start scripts
# ============================================================================

# Create monitor script
$MonitorScript = @"
@echo off
cd /d "%~dp0.."
python security\monitor_network.py dashboard
pause
"@
Set-Content -Path (Join-Path $SecurityDir "monitor.bat") -Value $MonitorScript
Write-Success "Created quick start script: security\monitor.bat"

# Create enable network script
$EnableScript = @"
@echo off
cd /d "%~dp0.."
python security\monitor_network.py enable
pause
"@
Set-Content -Path (Join-Path $SecurityDir "enable_network.bat") -Value $EnableScript
Write-Success "Created quick start script: security\enable_network.bat"

# Create disable network script
$DisableScript = @"
@echo off
cd /d "%~dp0.."
python security\monitor_network.py disable
pause
"@
Set-Content -Path (Join-Path $SecurityDir "disable_network.bat") -Value $DisableScript
Write-Success "Created quick start script: security\disable_network.bat"

# Create PowerShell monitor script
$MonitorPS = @"
# Network Security Monitor
Set-Location (Split-Path -Parent `$PSScriptRoot)
python security\monitor_network.py dashboard
"@
Set-Content -Path (Join-Path $SecurityDir "monitor.ps1") -Value $MonitorPS
Write-Success "Created PowerShell script: security\monitor.ps1"

Write-Host ""
Write-Header "🎉 Installation successful!"
Write-Host ""
Write-Host "Quick Start Commands:" -ForegroundColor Cyan
Write-Host "  .\security\monitor.bat         - Launch dashboard (Windows)"
Write-Host "  .\security\monitor.ps1         - Launch dashboard (PowerShell)"
Write-Host "  .\security\enable_network.bat  - Enable network access"
Write-Host "  .\security\disable_network.bat - Disable network access"
Write-Host ""

exit 0
