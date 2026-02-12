<#
.SYNOPSIS
    List OneDrive file version history and correlate with Git commits.
.DESCRIPTION
    Uses Microsoft Graph REST API to list version history for a file or folder
    path in OneDrive, then optionally compares version timestamps to git log
    output from a local repo to suggest which OneDrive version corresponds to
    which Git commit.

    Requires:
      - Microsoft Graph permission: Files.Read (delegated)
      - An access token (device-code flow, or paste from Graph Explorer)
      - Git in PATH (for commit correlation)

.PARAMETER OneDrivePath
    The relative path inside OneDrive (e.g. "Documents/GitHub/Python/README.md").
    Use forward slashes. This is the path as it appears under your OneDrive root.

.PARAMETER RepoRoot
    Optional. Local path to the Git repo root to correlate version dates with
    git log. If omitted, only OneDrive versions are listed.

.PARAMETER AccessToken
    A valid Microsoft Graph access token with Files.Read scope.
    If not provided, the script will attempt device-code flow using
    a well-known client ID (requires interactive sign-in).

.PARAMETER UseDeviceCode
    If set and no AccessToken provided, initiates device-code flow.

.EXAMPLE
    # List versions of a file (token from Graph Explorer):
    .\onedrive_version_history.ps1 -OneDrivePath "Documents/GitHub/Python/README.md" `
        -AccessToken "eyJ0eX..."

    # List versions and correlate with local git repo:
    .\onedrive_version_history.ps1 -OneDrivePath "Documents/GitHub/Python/README.md" `
        -RepoRoot "C:\Users\irfan\OneDrive\Documents\GitHub\Python" `
        -AccessToken "eyJ0eX..."

.NOTES
    Part of: restore_project_grid plan -- OneDrive version history correlation.
    Created: 2026-02-07
    Graph API reference: https://learn.microsoft.com/en-us/graph/api/driveitem-list-versions
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$OneDrivePath,

    [string]$RepoRoot,

    [string]$AccessToken,

    [switch]$UseDeviceCode
)

$ErrorActionPreference = 'Stop'

# -- Helper: Graph API call --
function Invoke-GraphAPI {
    param([string]$Uri, [string]$Token)
    $headers = @{ Authorization = "Bearer $Token"; "Content-Type" = "application/json" }
    Invoke-RestMethod -Uri $Uri -Headers $headers -Method Get
}

# -- Obtain access token via device-code flow if needed --
if (-not $AccessToken) {
    if ($UseDeviceCode) {
        # Use the well-known "Microsoft Graph Command Line Tools" client ID
        # This is a public client that supports device-code flow
        $clientId = "14d82eec-204b-4c2f-b7e8-296a70dab67e"
        $tenantId = "common"
        $scope    = "Files.Read"

        Write-Host "Starting device-code flow..." -ForegroundColor Cyan
        $deviceCodeUrl = "https://login.microsoftonline.com/$tenantId/oauth2/v2.0/devicecode"
        $body = @{ client_id = $clientId; scope = "$scope offline_access" }
        $deviceResp = Invoke-RestMethod -Uri $deviceCodeUrl -Method Post -Body $body

        Write-Host ""
        Write-Host $deviceResp.message -ForegroundColor Yellow
        Write-Host ""

        # Poll for token
        $tokenUrl = "https://login.microsoftonline.com/$tenantId/oauth2/v2.0/token"
        $pollBody = @{
            client_id   = $clientId
            grant_type  = "urn:ietf:params:oauth:grant-type:device_code"
            device_code = $deviceResp.device_code
        }
        $timeout = [DateTime]::Now.AddSeconds($deviceResp.expires_in)
        $token = $null
        while ([DateTime]::Now -lt $timeout) {
            Start-Sleep -Seconds $deviceResp.interval
            try {
                $tokenResp = Invoke-RestMethod -Uri $tokenUrl -Method Post -Body $pollBody
                $token = $tokenResp.access_token
                break
            } catch {
                $errBody = $_.ErrorDetails.Message | ConvertFrom-Json -ErrorAction SilentlyContinue
                if ($errBody.error -eq "authorization_pending") { continue }
                elseif ($errBody.error -eq "slow_down") { Start-Sleep -Seconds 5; continue }
                else { throw $_ }
            }
        }
        if (-not $token) { Write-Error "Device-code flow timed out."; exit 1 }
        $AccessToken = $token
        Write-Host "Authenticated successfully." -ForegroundColor Green
    } else {
        Write-Host @"

No access token provided. Options:
  1. Get a token from https://developer.microsoft.com/en-us/graph/graph-explorer
     (sign in, consent to Files.Read, copy the access token)
  2. Re-run with -UseDeviceCode to authenticate interactively
  3. Set `$env:GRAPH_TOKEN and re-run

"@ -ForegroundColor Yellow

        if ($env:GRAPH_TOKEN) {
            $AccessToken = $env:GRAPH_TOKEN
            Write-Host "Using token from `$env:GRAPH_TOKEN" -ForegroundColor Cyan
        } else {
            exit 1
        }
    }
}

# -- Get item by path --
# Encode the path for the Graph API URL
$encodedPath = $OneDrivePath -replace '\\', '/'
$graphBase = "https://graph.microsoft.com/v1.0"
$itemUrl = "$graphBase/me/drive/root:/$encodedPath"

Write-Host "Resolving OneDrive item: $encodedPath ..." -ForegroundColor Cyan
try {
    $item = Invoke-GraphAPI -Uri $itemUrl -Token $AccessToken
} catch {
    Write-Error "Could not resolve path '$OneDrivePath': $_"
    exit 1
}

Write-Host "  Item: $($item.name)  (id: $($item.id))" -ForegroundColor Green
Write-Host "  Last modified: $($item.lastModifiedDateTime)" -ForegroundColor Green
Write-Host ""

# -- List versions --
$versionsUrl = "$graphBase/me/drive/items/$($item.id)/versions"
Write-Host "Fetching version history..." -ForegroundColor Cyan
try {
    $versionsResp = Invoke-GraphAPI -Uri $versionsUrl -Token $AccessToken
} catch {
    Write-Warning "Could not list versions (may not be supported for folders): $_"
    $versionsResp = @{ value = @() }
}

$versions = $versionsResp.value
Write-Host "  Versions found: $($versions.Count)" -ForegroundColor Green
Write-Host ""

# -- Display versions --
$versionData = @()
foreach ($v in $versions) {
    $versionData += [PSCustomObject]@{
        VersionId    = $v.id
        LastModified = $v.lastModifiedDateTime
        Size         = $v.size
    }
}

if ($versionData.Count -gt 0) {
    Write-Host "=== OneDrive Version History ===" -ForegroundColor Cyan
    $versionData | Format-Table -AutoSize
} else {
    Write-Host "No version history available for this item." -ForegroundColor Yellow
}

# -- Correlate with Git log (if RepoRoot provided) --
if ($RepoRoot -and (Test-Path $RepoRoot)) {
    $gitExe = $null
    if (Get-Command git -ErrorAction SilentlyContinue) { $gitExe = "git" }
    elseif (Test-Path "C:\Program Files\Git\bin\git.exe") { $gitExe = "C:\Program Files\Git\bin\git.exe" }

    if ($gitExe) {
        Write-Host "=== Git Log (for correlation) ===" -ForegroundColor Cyan
        $gitLog = & $gitExe -C $RepoRoot log -20 --format="%h|%ci|%s" 2>$null
        $commits = @()
        foreach ($line in $gitLog) {
            if ($line -match "^([0-9a-f]+)\|(.+?)\|(.+)$") {
                $commits += [PSCustomObject]@{
                    Hash       = $Matches[1]
                    CommitDate = $Matches[2]
                    Subject    = $Matches[3]
                }
            }
        }
        $commits | Format-Table -AutoSize

        # -- Attempt matching --
        if ($versionData.Count -gt 0 -and $commits.Count -gt 0) {
            Write-Host "=== Correlation (nearest commit per OneDrive version) ===" -ForegroundColor Cyan
            foreach ($v in $versionData) {
                $vDate = [DateTime]::Parse($v.LastModified)
                $best = $null
                $bestDiff = [TimeSpan]::MaxValue
                foreach ($c in $commits) {
                    try {
                        # Parse git date format: "2025-11-14 20:15:17 -0500"
                        $cDate = [DateTimeOffset]::Parse($c.CommitDate).UtcDateTime
                        $diff = [Math]::Abs(($vDate - $cDate).TotalSeconds)
                        if ($diff -lt $bestDiff.TotalSeconds) {
                            $bestDiff = [TimeSpan]::FromSeconds($diff)
                            $best = $c
                        }
                    } catch { }
                }
                if ($best) {
                    $diffStr = if ($bestDiff.TotalHours -lt 1) { "{0:N0} min" -f $bestDiff.TotalMinutes }
                               elseif ($bestDiff.TotalDays -lt 1) { "{0:N1} hrs" -f $bestDiff.TotalHours }
                               else { "{0:N1} days" -f $bestDiff.TotalDays }
                    Write-Host ("  Version {0} ({1})  ~  commit {2} ({3}) [{4}]  delta={5}" -f
                        $v.VersionId, $v.LastModified, $best.Hash, $best.CommitDate, $best.Subject, $diffStr)
                }
            }
            Write-Host ""
        }
    }
}

Write-Host "Done." -ForegroundColor Green
