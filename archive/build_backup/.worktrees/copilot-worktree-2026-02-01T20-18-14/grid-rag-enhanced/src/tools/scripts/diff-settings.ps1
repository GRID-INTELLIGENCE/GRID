<#
.SYNOPSIS
  Diff user settings.json vs workspace settings in .code-workspace and export overrides.
#>
[CmdletBinding()]
param(
    [string]$UserSettingsPath = "$env:APPDATA\Code\User\settings.json",
    [string]$WorkspaceFile = "E:\grid\.code-workspace",
    [string]$ReportDir = "$env:USERPROFILE\Documents\vscode-audit-exports"
)

if (-not (Test-Path -Path $ReportDir)) { New-Item -ItemType Directory -Path $ReportDir -Force | Out-Null }

if (-not (Test-Path -Path $UserSettingsPath)) { Write-Error "User settings not found: $UserSettingsPath"; exit 2 }
if (-not (Test-Path -Path $WorkspaceFile)) { Write-Error "Workspace file not found: $WorkspaceFile"; exit 2 }

$user = Get-Content -Raw -Path $UserSettingsPath | ConvertFrom-Json
$workspace = Get-Content -Raw -Path $WorkspaceFile | ConvertFrom-Json
$wsSettings = $workspace.settings

# Compute shallow diff of top-level keys
$overrides = @()
foreach ($k in $wsSettings.PSObject.Properties.Name) {
    $uVal = $user.$k -as [object]
    if ($null -eq $uVal) { $overrides += [PSCustomObject]@{ key = $k; user = '<not set>'; workspace = $wsSettings.$k } }
    else { if (($user.$k).ToString() -ne ($wsSettings.$k).ToString()) { $overrides += [PSCustomObject]@{ key = $k; user = $user.$k; workspace = $wsSettings.$k } } }
}

$outJson = Join-Path $ReportDir ("settings-overrides-{0:yyyyMMdd-HHmmss}.json" -f (Get-Date))
$outCsv = Join-Path $ReportDir ("settings-overrides-{0:yyyyMMdd-HHmmss}.csv" -f (Get-Date))
$overrides | ConvertTo-Json -Depth 5 | Out-File -FilePath $outJson -Encoding utf8
$overrides | Export-Csv -Path $outCsv -NoTypeInformation

Write-Output "Settings overrides report written: $outJson"
Write-Output "CSV: $outCsv"
