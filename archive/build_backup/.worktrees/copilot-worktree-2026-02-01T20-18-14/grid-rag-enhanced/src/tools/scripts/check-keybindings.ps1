<#
.SYNOPSIS
  Check VS Code user keybindings for duplicates and conflicts with installed extensions.
#>
[CmdletBinding()]
param(
    [string]$KeybindingsPath = "$env:APPDATA\Code\User\keybindings.json",
    [string]$ExtensionsDir = "$env:USERPROFILE\.vscode\extensions",
    [string]$ReportDir = "$env:USERPROFILE\Documents\vscode-audit-exports"
)

# Ensure output dir
if (-not (Test-Path -Path $ReportDir)) { New-Item -ItemType Directory -Path $ReportDir -Force | Out-Null }

# Load keybindings
if (-not (Test-Path -Path $KeybindingsPath)) {
    Write-Error "Keybindings file not found: $KeybindingsPath"
    exit 2
}

$kbJson = Get-Content -Raw -Path $KeybindingsPath | ConvertFrom-Json

# Normalize keys and find duplicates
$kbNormalized = $kbJson | ForEach-Object {
    [PSCustomObject]@{
        key = ($_.'key' -replace '\\s+', ' ').Trim().ToLower();
        command = $_.command;
        when = $_.when
    }
}

$dupKeys = $kbNormalized | Group-Object key | Where-Object { $_.Count -gt 1 } | Select-Object Name, Count, @{n='Commands';e={$_.Group | ForEach-Object {$_.command} -join ';'}}

# Scan extensions for contributed keybindings
$extConflicts = @()
if (Test-Path -Path $ExtensionsDir) {
    Get-ChildItem -Path $ExtensionsDir -Directory | ForEach-Object {
        $pkg = Join-Path $_.FullName 'package.json'
        if (Test-Path $pkg) {
            try {
                $p = Get-Content -Raw -Path $pkg | ConvertFrom-Json
                if ($p.contributes -and $p.contributes.keybindings) {
                    foreach ($kb in $p.contributes.keybindings) {
                        $k = ($kb.key -replace '\\s+', ' ').Trim().ToLower()
                        $extConflicts += [PSCustomObject]@{ extension = $_.Name; key = $k; command = $kb.command }
                    }
                }
            } catch {
                # ignore invalid package.json
            }
        }
    }
}

# Compare user keys with extensions
$userKeys = $kbNormalized | Select-Object key, command
$matches = @()
foreach ($e in $extConflicts) {
    $m = $userKeys | Where-Object { $_.key -eq $e.key }
    if ($m) {
        $matches += [PSCustomObject]@{ key = $e.key; userCommands = ($m | ForEach-Object {$_.command}) -join ';'; extension = $e.extension; extCommand = $e.command }
    }
}

# Write reports
$report = [PSCustomObject]@{
    timestamp = (Get-Date).ToString('o')
    keybindingsPath = $KeybindingsPath
    duplicates = $dupKeys
    extensionMatches = $matches
}

$reportJson = Join-Path $ReportDir ("keybindings-report-{0:yyyyMMdd-HHmmss}.json" -f (Get-Date))
$reportCsv = Join-Path $ReportDir ("keybindings-duplicates-{0:yyyyMMdd-HHmmss}.csv" -f (Get-Date))

$report | ConvertTo-Json -Depth 5 | Out-File -FilePath $reportJson -Encoding utf8

if ($dupKeys) { $dupKeys | Export-Csv -Path $reportCsv -NoTypeInformation }

# Summary
Write-Output "Report written: $reportJson"
if ($dupKeys) { Write-Output "Duplicate keys report: $reportCsv" } else { Write-Output "No duplicate user key combos found." }
if ($matches) { Write-Output "Found $($matches.Count) user key(s) that also appear in installed extensions (possible conflicts)." } else { Write-Output "No extension conflicts found for user key combos." }
