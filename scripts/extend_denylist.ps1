# PowerShell script to extend server_denylist.json with 5 new MCP server deny rules

param()

$ErrorActionPreference = "Stop"

$denylistPath = "E:\config\server_denylist.json"

try {
    # Read and parse existing JSON
    Write-Host "`n=== Extending server_denylist.json ===" -ForegroundColor Cyan
    Write-Host "Reading from: $denylistPath"
    
    $jsonContent = Get-Content -Path $denylistPath -Raw
    $json = $jsonContent | ConvertFrom-Json
    
    Write-Host "Current rules count: $($json.denylistRules.Count)"
    
    # Define new deny rules as array of PSCustomObject
    $newRules = @(
        [PSCustomObject]@{
            name = "deny-grid-rag"
            reason = "mcp-server-denial"
            scope = "global"
            enabled = $true
            targetServer = "grid-rag"
            matchAttributes = [PSCustomObject]@{ name = "grid-rag" }
            deniedScopes = @("filesystem", "network", "database", "memory", "system")
            notes = "Total deny scope for grid-rag MCP server across all editors"
        },
        [PSCustomObject]@{
            name = "deny-grid-agentic"
            reason = "mcp-server-denial"
            scope = "global"
            enabled = $true
            targetServer = "grid-agentic"
            matchAttributes = [PSCustomObject]@{ name = "grid-agentic" }
            deniedScopes = @("filesystem", "network", "database", "memory", "system")
            notes = "Total deny scope for grid-agentic MCP server"
        },
        [PSCustomObject]@{
            name = "deny-grid-dev-tools"
            reason = "mcp-server-denial"
            scope = "global"
            enabled = $true
            targetServer = "grid-dev-tools"
            matchAttributes = [PSCustomObject]@{ name = "grid-dev-tools" }
            deniedScopes = @("filesystem", "network", "database", "memory", "system")
            notes = "Total deny scope for grid-dev-tools MCP server"
        },
        [PSCustomObject]@{
            name = "deny-portfolio-servers"
            reason = "mcp-server-denial"
            scope = "global"
            enabled = $true
            pattern = "portfolio-.*"
            matchAttributes = [PSCustomObject]@{ category = "portfolio" }
            deniedScopes = @("filesystem", "network", "database", "memory", "system")
            notes = "Total deny scope for all portfolio-* MCP servers"
        },
        [PSCustomObject]@{
            name = "deny-python-mcp-spawns"
            reason = "spawn-prevention"
            scope = "global"
            enabled = $true
            matchAttributes = [PSCustomObject]@{ commandPattern = "^python.*mcp" }
            deniedScopes = @("subprocess", "spawn", "execution")
            notes = "Prevent Python-based MCP server spawning"
        }
    )
    
    # Add new rules to denylistRules array
    foreach ($rule in $newRules) {
        $json.denylistRules += $rule
    }
    
    # Save with proper JSON formatting
    $updatedJson = $json | ConvertTo-Json -Depth 10
    $updatedJson | Set-Content -Path $denylistPath
    
    Write-Host "Updated rules count: $($json.denylistRules.Count)" -ForegroundColor Green
    Write-Host "`n✓ Successfully added 5 new deny rules:" -ForegroundColor Green
    foreach ($rule in $newRules) {
        Write-Host "  ✓ $($rule.name)" -ForegroundColor Green
    }
    Write-Host "`nFile saved: $denylistPath`n" -ForegroundColor Cyan
    
    exit 0
}
catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
    exit 1
}
