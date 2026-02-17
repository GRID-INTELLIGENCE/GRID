<#
.SYNOPSIS
    Track most recently modified files across all (or selected) drives for trace-to-recover.
.DESCRIPTION
    Recursively scans drive roots, collects file path, LastWriteTime, and Length;
    sorts by mtime descending and writes a timestamped JSON report plus optional Markdown table.
    Exclusions skip system/code-noise paths (e.g. .git, node_modules, System Volume Information).
.PARAMETER ReportDir
    Directory for output reports. Default: E:\docs
.PARAMETER TopN
    Maximum number of most-recent files to include. Default: 500
.PARAMETER Drives
    Optional comma-separated drive letters (e.g. E,F) to scan. If not set, uses config or all FileSystem drives.
.PARAMETER ConfigPath
    Optional path to JSON config (driveRoots, exclusions, maxFiles). Default: E:\config\recent_files_trace.json
.PARAMETER NoMarkdown
    Do not write the .md summary file.
.NOTES
    Part of: track most recent files (trace to recover). Created: 2026-02-07
#>
[CmdletBinding()]
param(
    [string]$ReportDir = "E:\docs",
    [int]$TopN = 500,
    [string]$Drives = "",
    [string]$ConfigPath = "E:\config\recent_files_trace.json",
    [switch]$NoMarkdown
)

$ErrorActionPreference = 'Continue'

# Default exclusion set (directory names that skip recursion; path substrings that skip)
$script:ExcludeDirNames = @(
    '.git', 'node_modules', '__pycache__', '.venv', 'venv', '.venv_locked',
    'dist', 'build', '.pytest_cache', 'System Volume Information', '$Recycle.Bin', 'Recovery'
)
$script:ExcludePathContains = @(
    'WinSxS', 'System Volume Information', '\Program Files\', '\Program Files (x86)\'
)
$script:ExcludeFilePatterns = @('*.pyc', '*.egg-info')
$script:DriveRoots = @{}  # e.g. { "C:" = ["C:\Users\irfan"]; "E:" = ["E:\"] }
$script:MaxFiles = 500
$script:AllFileSystemDrives = $true  # if no config and no -Drives, use Get-PSDrive

# Load optional config
if (Test-Path $ConfigPath) {
    try {
        $cfg = Get-Content -Path $ConfigPath -Raw | ConvertFrom-Json
        if ($cfg.driveRoots) {
            $script:DriveRoots = @{}
            $cfg.driveRoots.PSObject.Properties | ForEach-Object {
                $drive = $_.Name
                $roots = @()
                $_.Value | ForEach-Object { $roots += $_ }
                $script:DriveRoots[$drive] = $roots
            }
            $script:AllFileSystemDrives = $false
        }
        if ($cfg.excludeDirNames) {
            $script:ExcludeDirNames = @($cfg.excludeDirNames)
        }
        if ($cfg.excludePathContains) {
            $script:ExcludePathContains = @($cfg.excludePathContains)
        }
        if ($null -ne $cfg.maxFiles) {
            $script:MaxFiles = [int]$cfg.maxFiles
        }
    } catch {
        Write-Warning "Could not load config $ConfigPath : $_"
    }
}

# -TopN / config maxFiles
$takeN = if ($TopN -gt 0) { $TopN } else { $script:MaxFiles }

# Resolve roots to scan
$rootsToScan = @()
if ($Drives -ne "") {
    foreach ($d in $Drives -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }) {
        $letter = $d.TrimEnd(':') + ':'
        if ($script:DriveRoots[$letter]) {
            $rootsToScan += $script:DriveRoots[$letter]
        } else {
            $r = $letter + '\'
            if (Test-Path $r) { $rootsToScan += $r }
        }
    }
} elseif ($script:DriveRoots.Count -gt 0) {
    foreach ($key in $script:DriveRoots.Keys) {
        foreach ($r in $script:DriveRoots[$key]) { $rootsToScan += $r }
    }
} else {
    Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Root } | ForEach-Object {
        $r = $_.Root
        if ($r -match '^[A-Z]:\\$' -and (Test-Path $r)) {
            # Limit C:\ to user profile to avoid scanning entire Windows
            if ($r -eq 'C:\') {
                $userRoot = Join-Path $r "Users\$env:USERNAME"
                if (Test-Path $userRoot) { $rootsToScan += $userRoot } else { $rootsToScan += $r }
            } else {
                $rootsToScan += $r
            }
        }
    }
}

if ($rootsToScan.Count -eq 0) {
    Write-Warning "No roots to scan. Check -Drives or config driveRoots."
    exit 0
}

Write-Host "Trace recent files (mtime) - report dir: $ReportDir , top: $takeN" -ForegroundColor Cyan
Write-Host "Roots to scan:" -ForegroundColor Yellow
$rootsToScan | ForEach-Object { Write-Host "  $_" }

function ShouldSkipPath {
    param([string]$path)
    foreach ($sub in $script:ExcludePathContains) {
        if ($path -like "*$sub*") { return $true }
    }
    return $false
}

function ShouldSkipDirName {
    param([string]$name)
    foreach ($ex in $script:ExcludeDirNames) {
        if ($name -eq $ex) { return $true }
    }
    return $false
}

function ShouldSkipFileName {
    param([string]$name)
    if ($name -match '\.pyc$') { return $true }
    if ($name -match '\.egg-info$') { return $true }
    return $false
}

function Get-RecentFilesRecurse {
    param([string]$currentPath, [System.Collections.Generic.List[object]]$collector)
    $dirs = $null
    try {
        $dirs = Get-ChildItem -LiteralPath $currentPath -Directory -Force -ErrorAction SilentlyContinue
    } catch { return }
    $files = $null
    try {
        $files = Get-ChildItem -LiteralPath $currentPath -File -Force -ErrorAction SilentlyContinue
    } catch { return }

    foreach ($f in $files) {
        if (ShouldSkipFileName $f.Name) { continue }
        try {
            $collector.Add([PSCustomObject]@{
                path             = $f.FullName
                lastWriteTimeUtc = $f.LastWriteTimeUtc.ToString('o')
                lastWriteTimeLocal = $f.LastWriteTime.ToString('o')
                length           = $f.Length
            })
        } catch { }
    }

    foreach ($d in $dirs) {
        if (ShouldSkipDirName $d.Name) { continue }
        if (ShouldSkipPath $d.FullName) { continue }
        Get-RecentFilesRecurse -currentPath $d.FullName -collector $collector
    }
}

$collector = [System.Collections.Generic.List[object]]::new()
foreach ($root in $rootsToScan) {
    if (-not (Test-Path $root)) { continue }
    Write-Host "Scanning: $root ..." -ForegroundColor Gray
    Get-RecentFilesRecurse -currentPath $root -collector $collector
}

Write-Host "Collected $($collector.Count) files. Sorting by mtime descending..." -ForegroundColor Cyan
$sorted = $collector | Sort-Object { [DateTime]::Parse($_.lastWriteTimeUtc) } -Descending | Select-Object -First $takeN
$drivesScanned = $rootsToScan | ForEach-Object { (Split-Path $_ -Qualifier) } | Sort-Object -Unique

$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$baseName = "recent_files_trace_$timestamp"
if (-not (Test-Path $ReportDir)) { New-Item -ItemType Directory -Path $ReportDir -Force | Out-Null }

$reportJsonPath = Join-Path $ReportDir "$baseName.json"
$payload = @{
    generatedUtc   = (Get-Date).ToUniversalTime().ToString('o')
    drivesScanned = @($drivesScanned)
    rootsScanned  = @($rootsToScan)
    totalFilesCollected = $collector.Count
    topN          = $takeN
    topFiles      = @($sorted | ForEach-Object {
        @{ path = $_.path; lastWriteTimeUtc = $_.lastWriteTimeUtc; lastWriteTimeLocal = $_.lastWriteTimeLocal; length = $_.length }
    })
}
$payload | ConvertTo-Json -Depth 4 | Set-Content -Path $reportJsonPath -Encoding UTF8
Write-Host "Wrote: $reportJsonPath" -ForegroundColor Green

if (-not $NoMarkdown) {
    $reportMdPath = Join-Path $ReportDir "$baseName.md"
    $sb = [System.Text.StringBuilder]::new()
    [void]$sb.AppendLine("# Recent Files Trace (mtime)")
    [void]$sb.AppendLine("")
    [void]$sb.AppendLine("**Generated (UTC):** $($payload.generatedUtc)")
    [void]$sb.AppendLine("**Drives scanned:** $($drivesScanned -join ', ')")
    [void]$sb.AppendLine("**Total collected:** $($payload.totalFilesCollected) | **Top N:** $($payload.topN)")
    [void]$sb.AppendLine("")
    [void]$sb.AppendLine("| Path | Last modified (local) | Size |")
    [void]$sb.AppendLine("|------|------------------------|------|")
    foreach ($e in $sorted) {
        $path = $e.path -replace '\|', '\|'
        $size = if ($e.length -ge 1MB) { "{0:N2} MB" -f ($e.length / 1MB) } elseif ($e.length -ge 1KB) { "{0:N2} KB" -f ($e.length / 1KB) } else { "$($e.length) B" }
        [void]$sb.AppendLine("| $path | $($e.lastWriteTimeLocal) | $size |")
    }
    $sb.ToString() | Set-Content -Path $reportMdPath -Encoding UTF8
    Write-Host "Wrote: $reportMdPath" -ForegroundColor Green
}

Write-Host "Done. Top file: $($sorted[0].path)" -ForegroundColor Cyan
