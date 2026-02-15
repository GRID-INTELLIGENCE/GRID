# Network Security Audit Script
# Run this script periodically to audit network connections and firewall rules
# Recommended: Schedule weekly via Windows Task Scheduler

param(
    [string]$OutputPath = ".\network_audit_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt",
    [switch]$CheckFirewall = $true,
    [switch]$Verbose = $false
)

Write-Host "Network Security Audit - $(Get-Date)" -ForegroundColor Cyan
Write-Host "=" * 60

$report = @()
$report += "Network Security Audit Report"
$report += "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$report += "=" * 60
$report += ""

# 1. Active Network Connections
Write-Host "`n[1/3] Checking active network connections..." -ForegroundColor Yellow
$report += "ACTIVE NETWORK CONNECTIONS"
$report += "-" * 60

try {
    $connections = netstat -an | Select-String -Pattern "ESTABLISHED|LISTENING"
    $report += $connections | Out-String
    
    # Flag suspicious connections
    $suspiciousPatterns = @(
        "\.onion",           # Tor
        "192\.168\.",        # Local network (usually OK, but flag for review)
        "10\.0\.",           # Private network
        "172\.(1[6-9]|2[0-9]|3[0-1])\.",  # Private network
        ":443",              # HTTPS (usually OK)
        ":80",               # HTTP (usually OK)
        ":22",               # SSH
        ":3389",             # RDP
        ":5432",             # PostgreSQL
        ":3306",             # MySQL
        ":6379"              # Redis
    )
    
    $suspicious = $connections | Where-Object {
        $line = $_.Line
        foreach ($pattern in $suspiciousPatterns) {
            if ($line -match $pattern) {
                return $true
            }
        }
        return $false
    }
    
    if ($suspicious) {
        Write-Host "  ⚠ Found potentially suspicious connections" -ForegroundColor Red
        $report += "`nSUSPICIOUS CONNECTIONS (Review Required):"
        $report += $suspicious | Out-String
    } else {
        Write-Host "  ✓ No obviously suspicious connections detected" -ForegroundColor Green
        $report += "`nNo obviously suspicious connections detected."
    }
} catch {
    Write-Host "  ✗ Failed to check connections: $_" -ForegroundColor Red
    $report += "ERROR: Failed to check connections - $_"
}

$report += ""

# 2. Firewall Rules Status
if ($CheckFirewall) {
    Write-Host "`n[2/3] Checking firewall rules..." -ForegroundColor Yellow
    $report += "FIREWALL RULES STATUS"
    $report += "-" * 60
    
    try {
        $firewallStatus = Get-NetFirewallProfile | Select-Object Name, Enabled
        $report += $firewallStatus | Format-Table -AutoSize | Out-String
        
        $disabledProfiles = $firewallStatus | Where-Object { -not $_.Enabled }
        if ($disabledProfiles) {
            Write-Host "  ⚠ Some firewall profiles are disabled!" -ForegroundColor Red
            $report += "`nWARNING: Disabled firewall profiles:"
            $report += $disabledProfiles | Format-Table -AutoSize | Out-String
        } else {
            Write-Host "  ✓ All firewall profiles are enabled" -ForegroundColor Green
            $report += "`nAll firewall profiles are enabled."
        }
        
        # Check for block rules
        $blockRules = Get-NetFirewallRule | Where-Object { $_.Action -eq "Block" } | Select-Object -First 10
        if ($blockRules) {
            $report += "`nSample Block Rules (first 10):"
            $report += $blockRules | Format-Table Name, DisplayName, Enabled, Direction | Out-String
        }
    } catch {
        Write-Host "  ✗ Failed to check firewall: $_" -ForegroundColor Red
        $report += "ERROR: Failed to check firewall - $_"
    }
    
    $report += ""
}

# 3. Network Adapters
Write-Host "`n[3/3] Checking network adapters..." -ForegroundColor Yellow
$report += "NETWORK ADAPTERS"
$report += "-" * 60

try {
    $adapters = Get-NetAdapter | Where-Object { $_.Status -eq "Up" } | Select-Object Name, InterfaceDescription, Status, LinkSpeed
    $report += $adapters | Format-Table -AutoSize | Out-String
    Write-Host "  ✓ Network adapters checked" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed to check adapters: $_" -ForegroundColor Red
    $report += "ERROR: Failed to check adapters - $_"
}

# Summary
$report += ""
$report += "=" * 60
$report += "AUDIT SUMMARY"
$report += "=" * 60
$report += "Review the connections and firewall status above."
$report += "If suspicious connections are found, investigate immediately."
$report += "Ensure firewall rules remain active and block rules are in place."
$report += ""
$report += "Next Steps:"
$report += "1. Review suspicious connections (if any)"
$report += "2. Verify firewall rules are active"
$report += "3. Update blocklist if needed"
$report += "4. Schedule next audit (recommended: weekly)"

# Write report
$report | Out-File -FilePath $OutputPath -Encoding UTF8
Write-Host "`n✓ Audit report saved to: $OutputPath" -ForegroundColor Green

if ($Verbose) {
    Write-Host "`nFull Report:" -ForegroundColor Cyan
    $report | Write-Host
}

Write-Host "`nAudit complete!" -ForegroundColor Cyan
