<#
.SYNOPSIS
    GRID Repository Restructure Script (Safe & Staged)

.DESCRIPTION
    Implements a non-destructive "Copy + Shim" reorganization.
    Follows the version 2026-01-01 strategy for safe repository evolution.

.PARAMETER DryRun
    Show what would happen without making changes.

.PARAMETER Phase
    "structure": Create directories and __init__.py files.
    "pilot": Copy shared/utils and shared/types with shims.
    "expand": Copy domain, features, and infra with shims.
    "all": Run structure, pilot, and expand phases.
#>

param(
    [switch]$DryRun = $false,
    [ValidateSet("structure", "pilot", "expand", "all")]
    [string]$Phase = "structure"
)

$basePath = "E:\grid"
$ErrorActionPreference = "Stop"

# --- UI Helpers ---
function Write-Header { param($Message) Write-Host "`n═══ $Message ═══" -ForegroundColor Cyan }
function Write-Step { param($Message) Write-Host "  → $Message" -ForegroundColor Green }
function Write-DryRun { param($Message) Write-Host "  [DRY RUN] $Message" -ForegroundColor Yellow }
function Write-Warning-Custom { param($Message) Write-Host "  ⚠ $Message" -ForegroundColor Yellow }
function Write-Success { param($Message) Write-Host "  ✓ $Message" -ForegroundColor Green }

# --- Hazard Guard ---
function Is-HazardPath {
    param([string]$Path)
    # Check for Windows device names (NUL, CON, PRN, etc.)
    return $Path -match "\\(nul|con|prn|aux|com[1-9]|lpt[1-9])($|\\)"
}

# --- Shim Generator ---
function Create-PythonShim {
    param([string]$OldPath, [string]$NewModulePath)

    if ($DryRun) {
        Write-DryRun "Would create shim: $OldPath -> re-exports $NewModulePath"
        return
    }

    $content = @"
# Compatibility Shim for GRID Restructure
# This file re-exports the module from its new semantic location.
# Source: $OldPath
# Target: $NewModulePath

from $NewModulePath import *

import warnings
warnings.warn(
    "Importing from '$OldPath' is deprecated. "
    "Please use '$NewModulePath' instead.",
    DeprecationWarning,
    stacklevel=2
)
"@
    Set-Content -Path $OldPath -Value $content
    Write-Step "Created shim at $OldPath"
}

# --- Core Functions ---

function Create-DirectoryStructure {
    Write-Header "Phase: Structure"
    $directories = @(
        "src\domain\models", "src\domain\services\cognitive", "src\domain\services\quantum",
        "src\domain\services\processing", "src\domain\services\senses", "src\domain\entities\awareness",
        "src\domain\entities\essence", "src\domain\entities\evolution", "src\features\cli\commands",
        "src\features\api\routes", "src\features\api\middleware", "src\features\applications\mothership",
        "src\features\applications\resonance", "src\features\skills", "src\infrastructure\database",
        "src\infrastructure\rag\embeddings", "src\infrastructure\cloud", "src\infrastructure\monitoring",
        "src\shared\utils", "src\shared\config", "src\shared\types", "lang\python", "lang\rust",
        "tests\unit\domain", "tests\unit\features", "tests\unit\infrastructure", "docs\architecture",
    )

    foreach ($dir in $directories) {
        $fullPath = Join-Path $basePath $dir
        if (-not (Test-Path $fullPath)) {
            if ($DryRun) { Write-DryRun "Would create dir: $dir" }
            else { New-Item -ItemType Directory -Force -Path $fullPath | Out-Null; Write-Step "Created $dir" }
        }
    }

    # Create __init__.py files
    foreach ($dir in $directories) {
        $fullPath = Join-Path $basePath $dir
        if ($dir.StartsWith("src") -or $dir.StartsWith("lang\python")) {
            $initFile = Join-Path $fullPath "__init__.py"
            if (-not (Test-Path $initFile)) {
                if ($DryRun) { Write-DryRun "Would create __init__.py in $dir" }
                else { Set-Content -Path $initFile -Value '"""Auto-generated package init."""'; Write-Step "Initted $dir" }
            }
        }
    }
}

function Invoke-StagedMigration {
    param([array]$Mappings)

    foreach ($map in $Mappings) {
        $src = Join-Path $basePath $map.Source
        $dst = Join-Path $basePath $map.Dest

        if (Is-HazardPath $src) { Write-Warning-Custom "Skipping hazard: $($map.Source)"; continue }
        if (-not (Test-Path $src)) { Write-Warning-Custom "Not found: $($map.Source)"; continue }

        if ($DryRun) {
            Write-DryRun "Would copy: $($map.Source) -> $($map.Dest)"
            if ($map.Shim -eq $true) { Write-DryRun "Would create shim for $($map.Source)" }
            continue
        }

        # Ensure destination parent exists
        $destParent = Split-Path $dst -Parent
        if (-not (Test-Path $destParent)) { New-Item -ItemType Directory -Force -Path $destParent | Out-Null }

        # Execute Copy
        if ($map.Type -eq "dir") {
            Copy-Item -Path $src -Destination $dst -Recurse -Force
            Write-Step "Copied dir: $($map.Source)"
        } else {
            Copy-Item -Path $src -Destination $dst -Force
            Write-Step "Copied file: $($map.Source)"

            # Create Shim if requested and file is Python
            if ($map.Shim -eq $true -and $src.EndsWith(".py")) {
                # Convert destination path to module path (e.g., src\shared\utils\log.py -> src.shared.utils.log)
                $relNew = $map.Dest -replace "\.py$", "" -replace "\\", "."
                Create-PythonShim -OldPath $src -NewModulePath $relNew
            }
        }
    }
}

# --- Phase Definitions ---

$PilotMappings = @(
    @{Source="python\logging_utils.py"; Dest="src\shared\utils\logging_utils.py"; Type="file"; Shim=$true},
    @{Source="python\schema_validator.py"; Dest="src\shared\types\schema_validator.py"; Type="file"; Shim=$true},
    @{Source="python\type_validator.py"; Dest="src\shared\types\type_validator.py"; Type="file"; Shim=$true}
)

$ExpandMappings = @(
    @{Source="models\faceless.py"; Dest="src\domain\models\faceless.py"; Type="file"; Shim=$true},
    @{Source="core\products.py"; Dest="src\domain\models\products.py"; Type="file"; Shim=$true},
    @{Source="grid\quantum"; Dest="src\domain\services\quantum"; Type="dir"},
    @{Source="grid\processing"; Dest="src\domain\services\processing"; Type="dir"},
    @{Source="tools\rag"; Dest="src\infrastructure\rag"; Type="dir"},
)

# --- Main ---
Write-Header "GRID SAFE RESTRUCTURE START"
if ($DryRun) { Write-Warning-Custom "DRY RUN MODE ENABLED" }

switch ($Phase) {
    "structure" { Create-DirectoryStructure }
    "pilot"     { Create-DirectoryStructure; Invoke-StagedMigration $PilotMappings }
    "expand"    { Invoke-StagedMigration $ExpandMappings }
    "all"       { Create-DirectoryStructure; Invoke-StagedMigration $PilotMappings; Invoke-StagedMigration $ExpandMappings }
}

Write-Header "COMPLETED"
