<#
.SYNOPSIS
    Discover and track Git repositories under OneDrive folders.
.DESCRIPTION
    Recursively searches OneDrive roots for .git directories, collects remote info,
    latest commit (hash, date, subject), and flags GRID-related repos.
    Produces a formatted report file and console output.
.PARAMETER ReportPath
    Where to save the report. Default: E:\_projects\OneDrive_git_repos_report.txt
.PARAMETER Quiet
    Suppress console output (report file still written).
.NOTES
    Requires Git in PATH or at "C:\Program Files\Git\bin\git.exe".
    Part of: restore_project_grid plan -- OneDrive Git tracking.
    Created: 2026-02-07
#>
[CmdletBinding()]
param(
    [string]$ReportPath = "E:\_projects\OneDrive_git_repos_report.txt",
    [switch]$Quiet
)

$ErrorActionPreference = 'Continue'

# -- Resolve Git executable --
$gitExe = $null
if (Get-Command git -ErrorAction SilentlyContinue) { $gitExe = "git" }
elseif (Test-Path "C:\Program Files\Git\bin\git.exe") { $gitExe = "C:\Program Files\Git\bin\git.exe" }
else { Write-Error "Git not found in PATH or at C:\Program Files\Git\bin\git.exe"; exit 1 }

# -- Enumerate OneDrive roots --
$roots = @()
$candidate = Join-Path $env:UserProfile "OneDrive"
if (Test-Path $candidate) { $roots += $candidate }
Get-ChildItem -Path $env:UserProfile -Directory -Filter "OneDrive - *" -Force -ErrorAction SilentlyContinue |
    ForEach-Object { $roots += $_.FullName }

if ($roots.Count -eq 0) {
    Write-Warning "No OneDrive folders found under $env:UserProfile"
    exit 0
}
Write-Host "OneDrive roots to scan:" -ForegroundColor Cyan
$roots | ForEach-Object { Write-Host "  $_" }
Write-Host ""

# -- Ensure report directory exists --
$reportDir = Split-Path -Parent $ReportPath
if (-not (Test-Path $reportDir)) { New-Item -ItemType Directory -Path $reportDir -Force | Out-Null }

# -- Discover .git directories --
$results = @()
$seenRoots = @{}

foreach ($root in $roots) {
    if (-not (Test-Path $root)) { continue }
    Write-Host "Scanning: $root ..." -ForegroundColor Yellow
    Get-ChildItem -Path $root -Recurse -Directory -Filter ".git" -Force -ErrorAction SilentlyContinue | ForEach-Object {
        $repoRoot = $_.Parent.FullName
        if ($seenRoots[$repoRoot]) { return }
        $seenRoots[$repoRoot] = $true

        # --- Remotes ---
        $remotes = "(none)"
        try {
            $remoteRaw = & $gitExe -C $repoRoot remote -v 2>$null
            $fetchLines = $remoteRaw | Where-Object { $_ -match '\(fetch\)' }
            if ($fetchLines) { $remotes = ($fetchLines -join "; ").Trim() }
        } catch { $remotes = "(error)" }

        # --- Last commit (use | delimiter for safe parsing) ---
        $lastHash    = "(no commits)"
        $lastDate    = ""
        $lastSubject = ""
        try {
            $logLine = & $gitExe -C $repoRoot log -1 --format="%H|%ci|%s" 2>$null
            if ($logLine -match "^([0-9a-f]{40})\|(.+?)\|(.+)$") {
                $lastHash    = $Matches[1]
                $lastDate    = $Matches[2]
                $lastSubject = $Matches[3]
            }
        } catch { }

        # --- GRID flag ---
        $isGrid = $false
        $configPath = Join-Path $repoRoot ".git\config"
        if (Test-Path $configPath) {
            $configContent = Get-Content $configPath -Raw -ErrorAction SilentlyContinue
            if ($configContent -match "GRID-INTELLIGENCE|irfankabir02|GRID") { $isGrid = $true }
        }

        # --- Recent commits log (last 5 for version-history correlation) ---
        $recentLog = @()
        try {
            $logLines = & $gitExe -C $repoRoot log -5 --format="%h %ci %s" 2>$null
            if ($logLines) { $recentLog = @($logLines) }
        } catch { }

        $results += [PSCustomObject]@{
            RepoPath    = $repoRoot
            Remotes     = $remotes
            LastHash    = $lastHash
            LastDate    = $lastDate
            Subject     = $lastSubject
            GRIDRelated = $isGrid
            RecentLog   = $recentLog
        }
    }
}

if ($results.Count -eq 0) {
    Write-Host "`nNo .git directories found under OneDrive." -ForegroundColor Green
    "No .git directories found under OneDrive roots: $($roots -join ', ')" |
        Out-File $ReportPath -Encoding utf8
    Write-Host "Report written to $ReportPath"
    exit 0
}

Write-Host "`nFound $($results.Count) repo(s).`n" -ForegroundColor Cyan

# -- Build report --
$sep = "-" * 80
$lines = @()
$lines += "================================================================================"
$lines += "  OneDrive Git Repos Report"
$lines += "================================================================================"
$lines += "Generated : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$lines += "Roots     : $($roots -join ', ')"
$lines += "Repos     : $($results.Count)"
$lines += ""

foreach ($r in $results) {
    $lines += $sep
    $lines += "Repo Path    : $($r.RepoPath)"
    $lines += "Remotes      : $($r.Remotes)"
    $lines += "Last Commit  : $($r.LastHash)"
    $lines += "Commit Date  : $($r.LastDate)"
    $lines += "Subject      : $($r.Subject)"
    $lines += "GRID-related : $(if ($r.GRIDRelated) { 'YES' } else { 'no' })"
    if ($r.RecentLog.Count -gt 0) {
        $lines += "Recent commits (last 5):"
        foreach ($entry in $r.RecentLog) {
            $lines += "  $entry"
        }
    }
}
$lines += $sep
$lines += ""

# -- Summary table --
$lines += "=== Summary Table ==="
$lines += ""
$header = "{0,-60} {1,-8} {2,-28} {3}" -f "Repo Path", "GRID?", "Commit Date", "Subject"
$lines += $header
$lines += ("-" * 120)
foreach ($r in $results) {
    $short = if ($r.RepoPath.Length -gt 58) { "..." + $r.RepoPath.Substring($r.RepoPath.Length - 55) } else { $r.RepoPath }
    $gf    = if ($r.GRIDRelated) { "YES" } else { "" }
    $row   = "{0,-60} {1,-8} {2,-28} {3}" -f $short, $gf, $r.LastDate, $r.Subject
    $lines += $row
}
$lines += ""

# -- Version-history correlation notes --
$lines += "=== OneDrive Version History Correlation ==="
$lines += ""
$lines += "To correlate OneDrive file versions with Git commits:"
$lines += "  1. Right-click a file in the repo folder -> Version history"
$lines += "  2. Match OneDrive version dates against 'Commit Date' above"
$lines += "  3. Or use the Graph API helper: E:\scripts\onedrive_version_history.ps1"
$lines += ""
$lines += "OneDrive Recycle Bin:"
$lines += "  - Check https://onedrive.live.com -> Recycle bin for deleted .git folders"
$lines += "  - In Explorer: OneDrive icon -> View online -> Recycle bin"
$lines += ""

# -- Write report file --
$reportText = $lines -join "`r`n"
$reportText | Set-Content -Path $ReportPath -Encoding UTF8

Write-Host "Report saved to: $ReportPath" -ForegroundColor Green

if (-not $Quiet) {
    Write-Host ""
    $lines | ForEach-Object { Write-Host $_ }
}

# -- Return objects for pipeline use --
$results

