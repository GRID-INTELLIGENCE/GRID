$gridMcpPath = "E:\grid\mcp-setup\mcp_config.json"

# Read and parse the Grid MCP config
$json = Get-Content -Path $gridMcpPath -Raw | ConvertFrom-Json

Write-Host "Updating Grid MCP config" -ForegroundColor Cyan
Write-Host "Current servers:"
foreach ($server in $json.servers) {
    $status = if ($server.enabled) { "ENABLED" } else { "DISABLED" }
    Write-Host "  - $($server.name): $status"
}

# Find and disable portfolio-safety-lens
$portfolioServer = $json.servers | Where-Object { $_.name -eq "portfolio-safety-lens" }
if ($portfolioServer) {
    $portfolioServer.enabled = $false
    $portfolioServer._denylist_reason = "total-deny-scope"
    $portfolioServer._denylist_applied = $true
    
    Write-Host "" -ForegroundColor Cyan
    Write-Host "Disabling portfolio-safety-lens..." -ForegroundColor Green
}

# Save the updated config
$json | ConvertTo-Json -Depth 10 | Set-Content -Path $gridMcpPath

Write-Host "Grid MCP config updated successfully" -ForegroundColor Green
Write-Host "Portfolio-safety-lens is now DISABLED" -ForegroundColor Yellow
