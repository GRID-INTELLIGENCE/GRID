$cursorMcpPath = "C:\Users\irfan\.cursor\mcp.json"

$cursorConfig = @{
    "`$schema" = "https://json-schema.org/draft/2020-12/schema"
    version = "1.0.0"
    description = "Cursor MCP Server Configuration (Total Deny Scope)"
    servers = @(
        @{
            name = "grid-rag"
            description = "RAG-powered knowledge base and document search"
            enabled = $false
            command = "python"
            args = @("mcp-setup/server/grid_rag_mcp_server.py")
            cwd = "e:\\grid"
            env = @{
                PYTHONPATH = "e:\\grid\\src;e:\\grid"
                RAG_LLM_MODE = "ollama"
            }
            port = 8000
            "_denylist_reason" = "total-deny-scope"
            "_denylist_applied" = $true
        },
        @{
            name = "enhanced-tools"
            description = "Enhanced development tools (profiling, security, docs, quality)"
            enabled = $false
            command = "python"
            args = @("mcp-setup/server/enhanced_tools_mcp_server.py")
            cwd = "e:\\grid"
            "_denylist_reason" = "total-deny-scope"
            "_denylist_applied" = $true
        },
        @{
            name = "portfolio-safety"
            description = "Portfolio Safety - Context-aware secure portfolio analytics"
            enabled = $false
            command = "python"
            args = @("mcp-setup/server/portfolio_safety_mcp_server.py")
            cwd = "e:\\Coinbase"
            "_denylist_reason" = "total-deny-scope"
            "_denylist_applied" = $true
        },
        @{
            name = "local-filesystem"
            description = "Safe local filesystem operations"
            enabled = $true
            command = "npx"
            args = @("@modelcontextprotocol/server-filesystem", ".")
            "_note" = "Approved for Cursor"
        }
    )
    defaults = @{
        timeout_seconds = 60
        retry_attempts = 3
        retry_delay_seconds = 2
    }
    logging = @{
        level = "INFO"
        format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        file = "logs/mcp_servers.log"
    }
}

# Convert and save as JSON
$cursorConfig | ConvertTo-Json -Depth 10 | Set-Content -Path $cursorMcpPath

Write-Host "Created Cursor MCP config at: $cursorMcpPath" -ForegroundColor Green
Write-Host "Disabled servers:" -ForegroundColor Cyan
Write-Host "  - grid-rag" -ForegroundColor Yellow
Write-Host "  - enhanced-tools" -ForegroundColor Yellow
Write-Host "  - portfolio-safety" -ForegroundColor Yellow
Write-Host ""
