$denylistPath = "E:\config\server_denylist.json"
$json = Get-Content -Path $denylistPath -Raw | ConvertFrom-Json
Write-Host "Current rules: $($json.denylistRules.Count)"

$new1 = [PSCustomObject]@{ name = "deny-grid-rag"; reason = "mcp-server-denial"; scope = "global"; enabled = $true; targetServer = "grid-rag"; notes = "Total deny for grid-rag" }
$new2 = [PSCustomObject]@{ name = "deny-grid-agentic"; reason = "mcp-server-denial"; scope = "global"; enabled = $true; targetServer = "grid-agentic"; notes = "Total deny for grid-agentic" }
$new3 = [PSCustomObject]@{ name = "deny-grid-dev-tools"; reason = "mcp-server-denial"; scope = "global"; enabled = $true; targetServer = "grid-dev-tools"; notes = "Total deny for grid-dev-tools" }
$new4 = [PSCustomObject]@{ name = "deny-portfolio-servers"; reason = "mcp-server-denial"; scope = "global"; enabled = $true; pattern = "portfolio-.*"; notes = "Total deny for portfolio servers" }
$new5 = [PSCustomObject]@{ name = "deny-python-mcp-spawns"; reason = "spawn-prevention"; scope = "global"; enabled = $true; notes = "Prevent Python MCP spawning" }

$json.denylistRules += $new1
$json.denylistRules += $new2
$json.denylistRules += $new3
$json.denylistRules += $new4
$json.denylistRules += $new5

$json | ConvertTo-Json -Depth 10 | Set-Content -Path $denylistPath
Write-Host "Updated to: $($json.denylistRules.Count) rules" -ForegroundColor Green
Write-Host "ADDED: deny-grid-rag" -ForegroundColor Green
Write-Host "ADDED: deny-grid-agentic" -ForegroundColor Green
Write-Host "ADDED: deny-grid-dev-tools" -ForegroundColor Green
Write-Host "ADDED: deny-portfolio-servers" -ForegroundColor Green
Write-Host "ADDED: deny-python-mcp-spawns" -ForegroundColor Green
