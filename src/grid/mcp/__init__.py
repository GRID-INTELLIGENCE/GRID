"""
GRID MCP (Model Context Protocol) Module

Provides tool registry, server management, and integration utilities
for MCP-based tool discovery and invocation.

Example:
    ```python
    from grid.mcp import ToolRegistry, get_registry, quick_setup

    # Quick setup with config file
    registry = await quick_setup("mcp-setup/mcp_config.json")

    # List available tools
    tools = registry.list_tools()

    # Call a tool
    result = await registry.call_tool("rag_query", {"query": "What is GRID?"})
    ```
"""

from .tool_registry import (
    ServerConfig,
    ServerInfo,
    ServerStatus,
    ToolCallResult,
    ToolDefinition,
    ToolRegistry,
    get_registry,
    quick_setup,
    set_registry,
)

__all__ = [
    # Core classes
    "ToolRegistry",
    "ToolDefinition",
    "ToolCallResult",
    "ServerConfig",
    "ServerInfo",
    "ServerStatus",
    # Global registry functions
    "get_registry",
    "set_registry",
    "quick_setup",
]

__version__ = "1.0.0"
