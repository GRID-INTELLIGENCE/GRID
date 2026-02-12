# GRID MCP (Model Context Protocol) Integration

This directory contains the MCP server implementations and configuration for GRID's tool integration system. MCP enables AI assistants to interact with GRID's RAG system, development tools, and other services.

## Overview

GRID provides two MCP servers:

| Server | Port | Description |
|--------|------|-------------|
| `grid-rag` | 8000 | RAG-powered knowledge base, document search, and semantic querying |
| `grid-enhanced-tools` | 8001 | Development tools: profiling, security auditing, documentation, quality gates |

## Quick Start

### 1. Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or with pip
pip install httpx pydantic mcp
```

### 2. Start the MCP Servers

```powershell
# From project root
.\scripts\start_mcp_servers.ps1

# Or start a specific server
.\scripts\start_mcp_servers.ps1 -ServerName "grid-rag"

# With verbose output
.\scripts\start_mcp_servers.ps1 -Verbose
```

### 3. Verify the Setup

```bash
python scripts/test_mcp_integration.py
```

## Configuration

The MCP configuration is stored in `mcp-setup/mcp_config.json`:

```json
{
  "servers": [
    {
      "name": "grid-rag",
      "enabled": true,
      "command": "python",
      "args": ["mcp-setup/server/grid_rag_mcp_server.py"],
      "port": 8000,
      "env": {
        "RAG_EMBEDDING_MODEL": "BAAI/bge-small-en-v1.5",
        "RAG_LLM_MODE": "ollama",
        "RAG_VECTOR_STORE_PATH": ".rag_db"
      }
    }
  ]
}
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RAG_EMBEDDING_PROVIDER` | `huggingface` | Embedding provider (huggingface, ollama) |
| `RAG_EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | Embedding model name |
| `RAG_LLM_MODE` | `ollama` | LLM mode (ollama, openai) |
| `RAG_LLM_MODEL_OLLAMA` | `qwen3-coder:480b-cloud` | Ollama model name |
| `RAG_VECTOR_STORE_PATH` | `.rag_db` | ChromaDB storage path |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API URL |

## Available Tools

### RAG Server (`grid-rag`)

| Tool | Description |
|------|-------------|
| `rag_query` | Query the knowledge base with semantic search |
| `rag_index` | Index documents into the knowledge base |
| `rag_add_document` | Add a single document to the index |
| `rag_search` | Perform direct vector similarity search |
| `rag_stats` | Get statistics about the indexed documents |
| `rag_on_demand` | Index and query in a single operation |

### Enhanced Tools Server (`grid-enhanced-tools`)

| Tool | Description |
|------|-------------|
| `performance_profiler` | Profile code performance and identify bottlenecks |
| `security_auditor` | Audit code for security vulnerabilities |
| `test_coverage_analyzer` | Analyze test coverage and suggest improvements |
| `documentation_generator` | Generate API documentation |
| `dependency_health_monitor` | Check dependency health and updates |
| `code_quality_gate` | Run quality checks (linting, typing, tests) |
| `workflow_orchestrator` | Orchestrate multi-step development workflows |

## Usage Examples

### Using the Tool Registry (Python)

```python
import asyncio
from grid.mcp.tool_registry import ToolRegistry

async def main():
    async with ToolRegistry() as registry:
        # Load configuration
        await registry.load_config("mcp-setup/mcp_config.json")
        
        # Discover all tools
        await registry.discover_all_tools()
        
        # List available tools
        for tool in registry.list_tools():
            print(f"{tool['name']}: {tool['description']}")
        
        # Call a tool
        result = await registry.call_tool(
            "rag_query",
            {"query": "What is GRID's architecture?"}
        )
        print(result.result)

asyncio.run(main())
```

### Direct HTTP Calls

```bash
# List tools
curl -X POST http://localhost:8000/list_tools

# Call a tool
curl -X POST http://localhost:8000/call_tool \
  -H "Content-Type: application/json" \
  -d '{"name": "rag_query", "arguments": {"query": "GRID architecture"}}'

# Health check
curl http://localhost:8000/health
```

### Using with Windsurf/Cursor

Add to your IDE's MCP configuration:

```json
{
  "mcp.servers": [
    {
      "name": "grid-rag",
      "url": "http://localhost:8000",
      "enabled": true
    },
    {
      "name": "grid-tools",
      "url": "http://localhost:8001",
      "enabled": true
    }
  ]
}
```

## Directory Structure

```
mcp-setup/
├── README.md                 # This file
├── mcp_config.json          # Server configuration
├── server/
│   ├── grid_rag_mcp_server.py       # RAG server implementation
│   ├── enhanced_tools_mcp_server.py # Tools server implementation
│   └── rag-server-config.json       # RAG-specific configuration
└── client/                   # Client utilities (if needed)
```

## Adding New Tools

1. **Add the tool handler** in the appropriate server file:

```python
async def handle_my_new_tool(arguments: dict) -> dict:
    """Handle the my_new_tool tool call."""
    # Your implementation here
    return {"result": "success", "data": ...}
```

2. **Register the tool** in `list_tools()`:

```python
{
    "name": "my_new_tool",
    "description": "What this tool does",
    "inputSchema": {
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "First parameter"},
        },
        "required": ["param1"]
    }
}
```

3. **Add the handler mapping** in `call_tool()`:

```python
if name == "my_new_tool":
    return await handle_my_new_tool(arguments)
```

4. **Restart the server** and test:

```bash
python scripts/test_mcp_integration.py --verbose
```

## Troubleshooting

### Server won't start

1. Check if the port is already in use:
   ```powershell
   netstat -ano | findstr :8000
   ```

2. Verify Python path and dependencies:
   ```bash
   python -c "import mcp; print(mcp.__version__)"
   ```

3. Check logs in `logs/mcp_*.log`

### Tools not discovered

1. Verify server is healthy:
   ```bash
   curl http://localhost:8000/health
   ```

2. Check server logs for errors

3. Run the test script with verbose flag:
   ```bash
   python scripts/test_mcp_integration.py --verbose
   ```

### Connection refused

1. Ensure Ollama is running (for RAG server):
   ```bash
   ollama serve
   ```

2. Check firewall settings

3. Verify the server URL in configuration matches the actual server

### Slow responses

1. First queries may be slow due to model loading
2. Check Ollama resource usage
3. Consider using a smaller embedding model

## Development

### Running Tests

```bash
# Test MCP integration
python scripts/test_mcp_integration.py

# Run unit tests for MCP module
pytest tests/mcp/ -v
```

### Debugging

Enable verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or set environment variable:

```bash
export LOG_LEVEL=DEBUG
```

## Related Documentation

- [GRID Architecture](../docs/architecture.md)
- [RAG System](../docs/RAG_FEATURES.md)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Tool Registry API](../src/grid/mcp/tool_registry.py)

## Contributing

When adding new tools or servers:

1. Follow the existing patterns in server implementations
2. Add comprehensive input validation
3. Include proper error handling
4. Document the tool in this README
5. Add tests for new functionality
