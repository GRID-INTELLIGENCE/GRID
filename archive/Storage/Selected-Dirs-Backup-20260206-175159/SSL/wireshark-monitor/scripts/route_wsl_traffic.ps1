#Requires -Version 5.1
<#
.SYNOPSIS
    WSL Network Monitoring → E:\ Directory Routing
.DESCRIPTION
    Captures network traffic via tshark (sudo) in WSL, parses it, and routes
    output to E:\SSL, E:\grid, E:\coinbase, E:\wellness_studio.

    CLEANUP MODE: Debug-only feature.
    Scans ALL directories but ONLY removes corrupt/broken files:
    - 0-byte .pcapng captures (failed/incomplete)
    - Malformed .json files (invalid JSON)
    - Empty config files (0-byte .yaml/.yml)
    NEVER removes development files (.py, .ps1, .sh, .md, .yaml with content, etc.)
.NOTES
    Prerequisites: WSL with tshark installed (sudo access), Python 3 in WSL
#>

param(
    [string]$Interface = "eth0",
    [string]$CaptureFilter = "src net 172.27.240.0/20",
    [string]$CoinbaseFilter = "src host 10.0.0.5",
    [int]$CaptureDuration = 30,
    [int]$CleanupMaxAgeDays = 7,
    [switch]$SkipCapture,
    [switch]$SkipParse,
    [switch]$SkipCleanup,
    [switch]$DebugCleanup,
    [switch]$SkipFirewall,
    [switch]$ResetFirewall
)

$ErrorActionPreference = "Continue"
$DateStamp = Get-Date -Format "yyyyMMdd"
$TimestampFull = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# =============================================
# Directory Definitions
# =============================================
$Directories = @{
    SSL      = 'E:\SSL'
    Grid     = 'E:\grid'
    Coinbase = 'E:\coinbase'
    Wellness = 'E:\wellness_studio'
}

# Debug cleanup scans ALL directories but only removes corrupt files
# NEVER removes development files (.py, .ps1, .sh, .md, .yaml with content, etc.)
$ProtectedExtensions = @('.py', '.ps1', '.sh', '.bat', '.cmd', '.md', '.txt', '.csv',
                         '.html', '.css', '.js', '.ts', '.jsx', '.tsx', '.sql',
                         '.r', '.ipynb', '.toml', '.ini', '.cfg', '.env',
                         '.code-workspace', '.gitignore', '.gitattributes')
$CorruptScanExtensions = @('*.pcapng', '*.json', '*.yaml', '*.yml')

# =============================================
# Step 1: Ensure Directories Exist
# =============================================
Write-Host "[$TimestampFull] Step 1: Ensuring directories exist..." -ForegroundColor Cyan

foreach ($dir in $Directories.Values) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  Created: $dir" -ForegroundColor Green
    } else {
        Write-Host "  Exists:  $dir" -ForegroundColor DarkGray
    }
}

# =============================================
# Step 2: Capture Traffic via WSL/tshark
# =============================================
if (-not $SkipCapture) {
    Write-Host "`n[$TimestampFull] Step 2: Capturing traffic..." -ForegroundColor Cyan

    $CaptureJobs = @(
        @{
            Name   = "SSL"
            Filter = $CaptureFilter
            Output = "$($Directories.SSL)\network_traffic_$DateStamp.pcapng"
        },
        @{
            Name   = "Grid"
            Filter = "tcp port 22 or tcp port 3306 or tcp port 5432 or tcp port 6379 or tcp port 27017 or tcp port 2376 or tcp port 6443 or tcp port 8080 or tcp port 8443"
            Output = "$($Directories.Grid)\traffic_$DateStamp.pcapng"
        },
        @{
            Name   = "Coinbase"
            Filter = "tcp port 443 or tcp port 8443 or tcp port 8333 or tcp port 30303 or tcp port 8545 or tcp port 8546 or tcp portrange 3000-3010"
            Output = "$($Directories.Coinbase)\monitoring_$DateStamp.pcapng"
        },
        @{
            Name   = "Wellness"
            Filter = "tcp port 80 or tcp port 443 or tcp port 8080"
            Output = "$($Directories.Wellness)\activity_$DateStamp.pcapng"
        },
        @{
            Name   = "DNS"
            Filter = "port 53"
            Output = "$($Directories.SSL)\dns_queries_$DateStamp.pcapng"
        }
    )

    # Launch traffic generation in a SEPARATE WSL process first
    # This runs independently so packets are flowing while tshark captures
    Write-Host "`n  Launching traffic generator (separate process)..." -ForegroundColor Gray
    $trafficGenCmd = "for i in 1 2 3; do sleep 2; nslookup example.com >/dev/null 2>&1; nslookup coinbase.com >/dev/null 2>&1; curl -s http://example.com >/dev/null 2>&1; curl -s https://example.com >/dev/null 2>&1; curl -s https://api.coinbase.com >/dev/null 2>&1; ping -c 3 8.8.8.8 >/dev/null 2>&1; done"
    Start-Job -Name "TrafficGen" -ScriptBlock {
        param($cmd)
        wsl bash -c $cmd 2>&1
    } -ArgumentList $trafficGenCmd | Out-Null

    # Build a single WSL bash script that runs all captures in parallel
    $bashCmds = @()
    $wslOutputs = @()
    foreach ($job in $CaptureJobs) {
        $wslOutput = ($job.Output -replace '\\', '/' -replace 'E:', '/mnt/e')
        $wslOutputs += $wslOutput
        $bashCmds += "sudo tshark -i $Interface -f '$($job.Filter)' -w '$wslOutput' -a duration:$CaptureDuration -q &"
        Write-Host "  [$($job.Name)] Queued capture -> $($job.Output)" -ForegroundColor Yellow
    }
    $bashCmds += "wait"

    $fullBashCmd = $bashCmds -join "`n"
    $escapedCmd = $fullBashCmd -replace '"', '\"'

    Write-Host "`n  Running all captures in parallel ($CaptureDuration seconds)..." -ForegroundColor Gray
    try {
        wsl bash -c "$escapedCmd" 2>&1 | ForEach-Object { Write-Host "  [WSL] $_" -ForegroundColor DarkGray }
    } catch {
        Write-Warning "  Capture execution error: $_"
    }

    # Clean up traffic generator job
    Get-Job -Name "TrafficGen" -ErrorAction SilentlyContinue | Stop-Job -PassThru | Remove-Job -Force -ErrorAction SilentlyContinue

    # Verify which files were created
    foreach ($job in $CaptureJobs) {
        if (Test-Path $job.Output) {
            $size = (Get-Item $job.Output).Length
            Write-Host "  [$($job.Name)] Capture complete ($size bytes) -> $($job.Output)" -ForegroundColor Green
        } else {
            Write-Host "  [$($job.Name)] No capture file created" -ForegroundColor DarkYellow
        }
    }
} else {
    Write-Host "`n[$TimestampFull] Step 2: Skipped (--SkipCapture)" -ForegroundColor DarkGray
}

# =============================================
# Step 3: Parse Traffic with Python
# =============================================
if (-not $SkipParse) {
    Write-Host "`n[$TimestampFull] Step 3: Parsing traffic..." -ForegroundColor Cyan
    Write-Host "  Note: This parses captures currently in progress or existing files." -ForegroundColor Gray

    $ParseJobs = @(
        @{
            Name     = "SSL"
            Input    = "$($Directories.SSL)\network_traffic_$DateStamp.pcapng"
            Output   = "$($Directories.SSL)\parsed_ssl_$DateStamp.json"
            Protocol = "SSL"
        },
        @{
            Name     = "Grid"
            Input    = "$($Directories.Grid)\traffic_$DateStamp.pcapng"
            Output   = "$($Directories.Grid)\parsed_grid_$DateStamp.json"
            Protocol = "Grid"
        },
        @{
            Name     = "Coinbase"
            Input    = "$($Directories.Coinbase)\monitoring_$DateStamp.pcapng"
            Output   = "$($Directories.Coinbase)\parsed_coinbase_$DateStamp.json"
            Protocol = "Coinbase"
        },
        @{
            Name     = "Wellness"
            Input    = "$($Directories.Wellness)\activity_$DateStamp.pcapng"
            Output   = "$($Directories.Wellness)\parsed_wellness_$DateStamp.json"
            Protocol = "Wellness"
        },
        @{
            Name     = "DNS"
            Input    = "$($Directories.SSL)\dns_queries_$DateStamp.pcapng"
            Output   = "$($Directories.SSL)\parsed_dns_$DateStamp.json"
            Protocol = "DNS"
        }
    )

    $ScriptPath = Join-Path $PSScriptRoot "parse_traffic.py"

    foreach ($job in $ParseJobs) {
        if (Test-Path $job.Input) {
            $wslInput = ($job.Input -replace '\\', '/' -replace 'E:', '/mnt/e')
            $wslOutput = ($job.Output -replace '\\', '/' -replace 'E:', '/mnt/e')
            $wslScript = ($ScriptPath -replace '\\', '/' -replace 'E:', '/mnt/e')

            Write-Host "  [$($job.Name)] Parsing: $($job.Input)" -ForegroundColor Yellow
            try {
                wsl python3 "$wslScript" "$wslInput" --output "$wslOutput" --protocol "$($job.Protocol)"
                Write-Host "  [$($job.Name)] Parsed -> $($job.Output)" -ForegroundColor Green
            } catch {
                Write-Warning "  [$($job.Name)] Parse failed: $_"
            }
        } else {
            # Check if it was just started
            if (-not $SkipCapture) {
                Write-Host "  [$($job.Name)] Waiting for capture file to be created..." -ForegroundColor Yellow
                $retryCount = 0
                while (-not (Test-Path $job.Input) -and $retryCount -lt 10) {
                    Start-Sleep -Seconds 1
                    $retryCount++
                }
            }
            
            if (Test-Path $job.Input) {
                # Re-run parse logic
                $wslInput = ($job.Input -replace '\\', '/' -replace 'E:', '/mnt/e')
                $wslOutput = ($job.Output -replace '\\', '/' -replace 'E:', '/mnt/e')
                $wslScript = ($ScriptPath -replace '\\', '/' -replace 'E:', '/mnt/e')
                try {
                    wsl python3 "$wslScript" "$wslInput" --output "$wslOutput" --protocol "$($job.Protocol)"
                    Write-Host "  [$($job.Name)] Parsed -> $($job.Output)" -ForegroundColor Green
                } catch {
                    Write-Warning "  [$($job.Name)] Parse failed: $_"
                }
            } else {
                Write-Host "  [$($job.Name)] No capture file found: $($job.Input)" -ForegroundColor DarkGray
            }
        }
    }
} else {
    Write-Host "`n[$TimestampFull] Step 3: Skipped (--SkipParse)" -ForegroundColor DarkGray
}

# =============================================
# Step 4: Generate Report
# =============================================
Write-Host "`n[$TimestampFull] Step 4: Generating report..." -ForegroundColor Cyan

$ReportPath = "$($Directories.SSL)\network_report_$DateStamp.md"
$ReportContent = @"
# Network Activity Report
**Generated:** $TimestampFull

---

## Capture Summary
| Directory | Capture File | Status |
|-----------|-------------|--------|
"@

foreach ($dir in $Directories.GetEnumerator()) {
    $pcapFiles = Get-ChildItem -Path $dir.Value -Filter "*$DateStamp.pcapng" -ErrorAction SilentlyContinue
    $status = if ($pcapFiles) { "Captured ($($pcapFiles.Count) file(s))" } else { "No capture" }
    $fileName = if ($pcapFiles) { $pcapFiles[0].Name } else { "N/A" }
    $ReportContent += "| $($dir.Key) | $fileName | $status |`n"
}

$ReportContent += "`n---`n`n## Parsed Results`n"

foreach ($dir in $Directories.GetEnumerator()) {
    $jsonFiles = Get-ChildItem -Path $dir.Value -Filter "*parsed*$DateStamp.json" -ErrorAction SilentlyContinue
    if ($jsonFiles) {
        foreach ($jf in $jsonFiles) {
            $ReportContent += "`n### $($dir.Key): $($jf.Name)`n"
            try {
                $preview = Get-Content $jf.FullName -Raw -ErrorAction SilentlyContinue
                if ($preview) {
                    $fence = '```'
                    $ReportContent += "${fence}json`n${preview}`n${fence}`n"
                }
            } catch {
                $ReportContent += "*Could not read file.*`n"
            }
        }
    }
}

$ReportContent += "`n---`n`n## Debug Cleanup Policy`n"
$ReportContent += "Cleanup is a **debugging feature** that scans all directories.`n"
$ReportContent += "It ONLY removes corrupt/broken files:`n"
$ReportContent += "- 0-byte .pcapng files (failed captures)`n"
$ReportContent += "- Malformed .json files (invalid JSON)`n"
$ReportContent += "- 0-byte .yaml/.yml files (empty configs)`n`n"
$ReportContent += "**NEVER removed:** .py, .ps1, .sh, .md, .txt, and all other dev files.`n"
$ReportContent += "Run with ``-DebugCleanup`` to activate. Requires ``-SkipCleanup`` to be OFF.`n"

$ReportContent | Out-File -FilePath $ReportPath -Encoding UTF8 -Force
Write-Host "  Report saved -> $ReportPath" -ForegroundColor Green

# =============================================
# Step 4.5: Enforce Firewall Rules via WSL/iptables
# =============================================
# Applied AFTER capture/parse so traffic generation isn't blocked.
# This hardens the network for the period between monitoring runs.
# =============================================
$FirewallScript = Join-Path $PSScriptRoot "firewall_rules.sh"
$wslFirewall = ($FirewallScript -replace '\\', '/' -replace 'E:', '/mnt/e')

if ($ResetFirewall) {
    Write-Host "`n[$TimestampFull] Step 4.5: Resetting firewall to permissive defaults..." -ForegroundColor Yellow
    wsl -u root bash "$wslFirewall" reset 2>&1 | ForEach-Object { Write-Host "  [FW] $_" -ForegroundColor DarkGray }
} elseif (-not $SkipFirewall) {
    Write-Host "`n[$TimestampFull] Step 4.5: Enforcing firewall rules..." -ForegroundColor Cyan
    try {
        wsl -u root bash "$wslFirewall" apply 2>&1 | ForEach-Object { Write-Host "  [FW] $_" -ForegroundColor DarkGray }
        Write-Host "  Firewall hardening applied (whitelist mode active until next run)" -ForegroundColor Green
    } catch {
        Write-Warning "  Firewall enforcement failed: $_"
        Write-Host "  Network remains in permissive mode (use -SkipFirewall to suppress)" -ForegroundColor Yellow
    }
} else {
    Write-Host "`n[$TimestampFull] Step 4.5: Firewall skipped (-SkipFirewall)" -ForegroundColor DarkGray
}

# =============================================
# Step 5: Debug Cleanup (corrupt files only)
# =============================================
# This is a DEBUGGING FEATURE. It scans ALL directories
# but ONLY removes corrupt/broken files:
#   - 0-byte .pcapng (failed captures)
#   - Malformed .json (invalid JSON content)
#   - 0-byte .yaml/.yml (empty configs)
# NEVER removes development files (.py, .ps1, .sh, .md, etc.)
# Activated with: -DebugCleanup (must also not use -SkipCleanup)
# =============================================
if (-not $SkipCleanup) {
    if ($DebugCleanup) {
        Write-Host "`n[$TimestampFull] Step 5: Debug Cleanup (corrupt files only)..." -ForegroundColor Cyan
        Write-Host "  [MODE] Scanning all directories for corrupt/broken files" -ForegroundColor Yellow
        Write-Host "  [SAFE] Development files are NEVER removed" -ForegroundColor Green

        $totalRemoved = 0
        $totalCorrupt = 0
        $scanDirs = @($Directories.Values)

        foreach ($scanDir in $scanDirs) {
            if (-not (Test-Path $scanDir)) { continue }
            Write-Host "`n  Scanning: $scanDir" -ForegroundColor Cyan
            $dirRemoved = 0

            # Get all candidate files (non-recursive to avoid deep dev trees)
            $candidates = Get-ChildItem -Path $scanDir -File -ErrorAction SilentlyContinue

            foreach ($file in $candidates) {
                $ext = $file.Extension.ToLower()

                # SAFETY: Skip all protected development file types
                if ($ProtectedExtensions -contains $ext) {
                    continue
                }

                $isCorrupt = $false
                $reason = ''

                # Check 1: 0-byte .pcapng files (failed/incomplete captures)
                if ($ext -eq '.pcapng' -and $file.Length -eq 0) {
                    $isCorrupt = $true
                    $reason = '0-byte capture (failed/incomplete)'
                }

                # Check 2: Malformed .json files
                if ($ext -eq '.json') {
                    if ($file.Length -eq 0) {
                        $isCorrupt = $true
                        $reason = '0-byte JSON (empty)'
                    } else {
                        try {
                            $content = Get-Content $file.FullName -Raw -ErrorAction Stop
                            $null = $content | ConvertFrom-Json -ErrorAction Stop
                        } catch {
                            $isCorrupt = $true
                            $reason = 'Malformed JSON (parse error)'
                        }
                    }
                }

                # Check 3: 0-byte .yaml/.yml files (empty configs)
                if (($ext -eq '.yaml' -or $ext -eq '.yml') -and $file.Length -eq 0) {
                    $isCorrupt = $true
                    $reason = '0-byte config (empty)'
                }

                if ($isCorrupt) {
                    $totalCorrupt++
                    try {
                        Remove-Item -Path $file.FullName -Force -ErrorAction Stop
                        Write-Host "    REMOVED: $($file.Name) [$reason]" -ForegroundColor DarkYellow
                        $dirRemoved++
                        $totalRemoved++
                    } catch {
                        Write-Warning "    FAILED:  $($file.Name) - $_"
                    }
                }
            }

            if ($dirRemoved -eq 0) {
                Write-Host "    No corrupt files found" -ForegroundColor DarkGray
            }
        }

        Write-Host "`n  [SUMMARY] Scanned $($scanDirs.Count) directories" -ForegroundColor Cyan
        Write-Host "  [SUMMARY] Found $totalCorrupt corrupt file(s), removed $totalRemoved" -ForegroundColor Cyan
        Write-Host "  [SAFE] All development files preserved" -ForegroundColor Green

    } else {
        Write-Host "`n[$TimestampFull] Step 5: Cleanup skipped (use -DebugCleanup to enable)" -ForegroundColor DarkGray
        Write-Host "  Debug cleanup scans for corrupt files only (0-byte captures, bad JSON, empty configs)" -ForegroundColor DarkGray
        Write-Host "  Development files (.py, .ps1, .sh, .md, etc.) are NEVER removed" -ForegroundColor DarkGray
    }
} else {
    Write-Host "`n[$TimestampFull] Step 5: Skipped (-SkipCleanup)" -ForegroundColor DarkGray
}

Write-Host "`n[$TimestampFull] Done." -ForegroundColor Green
