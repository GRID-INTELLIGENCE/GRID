[CmdletBinding()]
param(
  [string]$Date = (Get-Date).ToString('yyyy-MM-dd'),
  [switch]$Reset,
  [switch]$Open
)

$root = Split-Path -Parent $PSCommandPath
$configPath = Join-Path $root 'config.json'
$dailyDir = Join-Path $root 'daily'
$dailyPath = Join-Path $dailyDir ("$Date.md")
$todayPath = Join-Path $root 'TODAY.md'

if (-not (Test-Path $dailyDir)) {
  New-Item -ItemType Directory -Path $dailyDir -Force | Out-Null
}

$config = $null
if (Test-Path $configPath) {
  $config = Get-Content $configPath -Raw | ConvertFrom-Json
}

function Render-FocusAreas {
  param($cfg)
  if (-not $cfg -or -not $cfg.focusAreas) { return "- (no focus areas configured)" }

  $areas = $cfg.focusAreas | Sort-Object { $_.priority }
  $lines = @()
  foreach ($a in $areas) {
    $lines += "- **$($a.priority). $($a.name)**"
    foreach ($p in ($a.paths | ForEach-Object { $_ })) {
      $lines += "  - ``$($p)``"
    }
  }
  return ($lines -join "`n")
}

function Render-Metrics {
  param($cfg)
  if (-not $cfg -or -not $cfg.metrics) { return "- (no metrics configured)" }

  $lines = @()
  foreach ($m in $cfg.metrics) {
    $lines += "- **$($m.name):** $($m.goal)"
  }
  return ($lines -join "`n")
}

function Render-Tools {
  param($cfg)
  if (-not $cfg -or -not $cfg.tools) { return "- (no tools configured)" }

  $lines = @()
  foreach ($t in $cfg.tools) {
    $lines += "- **$($t.name)**"
    $lines += "  - ``$($t.command)``"
  }
  return ($lines -join "`n")
}

if ($Reset -or -not (Test-Path $dailyPath)) {
  $content = @()
  $content += "# GRID Daily Workflow - $Date"
  $content += ""
  $content += "## Focus Areas (ordered)"
  $content += ""
  $content += (Render-FocusAreas -cfg $config)
  $content += ""
  $content += "## Tasks (today)"
  $content += ""
  $content += "- [ ] Editor toolbar reps (60s): Undo/Redo, Save All, Toggle Panel, Toggle Side Bar"
  $content += "- [ ] "
  $content += ""
  $content += "## Metrics"
  $content += ""
  $content += (Render-Metrics -cfg $config)
  $content += ""
  $content += "## Tools / Commands"
  $content += ""
  $content += (Render-Tools -cfg $config)
  $content += ""
  $content += "## Notes / Decisions"
  $content += ""
  $content += "- "

  $content -join "`n" | Set-Content -Path $dailyPath -Encoding UTF8
}

if (Test-Path $todayPath) {
  try {
    $todayHash = (Get-FileHash -Path $todayPath -Algorithm SHA256).Hash
    $dailyHash = (Get-FileHash -Path $dailyPath -Algorithm SHA256).Hash
    if ($todayHash -ne $dailyHash) {
      Copy-Item -Path $todayPath -Destination $dailyPath -Force
    }
  } catch {
  }
}

try {
  if (Test-Path $todayPath) {
    Remove-Item -Path $todayPath -Force
  }
  New-Item -ItemType HardLink -Path $todayPath -Target $dailyPath | Out-Null
} catch {
  Copy-Item -Path $dailyPath -Destination $todayPath -Force
}

Write-Host ("Updated: " + $dailyPath)
Write-Host ("Linked:  " + $todayPath)

if ($Open) {
  Invoke-Item $todayPath
}
