#!/usr/bin/env python3
"""
Production Memory MCP Server
Provides in-memory data storage and retrieval using real MCP library
"""

import asyncio
import json
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any

# Real MCP imports
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    ListToolsResult,
    TextContent,
    Tool,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProductionMemoryMCPServer:
    """Production Memory MCP Server using real MCP library"""

    def __init__(self):
        self.server = Server("memory")
        self.data_store = defaultdict(dict)
        self.metadata = defaultdict(dict)
        self._register_handlers()

    def _register_handlers(self):
        """Register MCP handlers"""

        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """List available memory tools"""
            tools = [
                Tool(
                    name="set",
                    description="Store a value in memory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "key": {"type": "string", "description": "Key to store the value under"},
                            "value": {"type": "string", "description": "Value to store"},
                            "namespace": {
                                "type": "string",
                                "description": "Namespace for organizing data",
                                "default": "default",
                            },
                        },
                        "required": ["key", "value"],
                    },
                ),
                Tool(
                    name="get",
                    description="Retrieve a value from memory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "key": {"type": "string", "description": "Key to retrieve"},
                            "namespace": {
                                "type": "string",
                                "description": "Namespace to search in",
                                "default": "default",
                            },
                        },
                        "required": ["key"],
                    },
                ),
                Tool(
                    name="delete",
                    description="Delete a value from memory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "key": {"type": "string", "description": "Key to delete"},
                            "namespace": {
                                "type": "string",
                                "description": "Namespace to delete from",
                                "default": "default",
                            },
                        },
                        "required": ["key"],
                    },
                ),
                Tool(
                    name="list_keys",
                    description="List all keys in a namespace",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "namespace": {
                                "type": "string",
                                "description": "Namespace to list keys from",
                                "default": "default",
                            }
                        },
                    },
                ),
                Tool(
                    name="clear_namespace",
                    description="Clear all data in a namespace",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "namespace": {"type": "string", "description": "Namespace to clear", "default": "default"}
                        },
                    },
                ),
                Tool(name="get_stats", description="Get memory usage statistics"),
            ]
            return ListToolsResult(tools=tools)

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
            """Handle tool calls"""
            try:
                if name == "set":
                    return await self._set_value(arguments)
                elif name == "get":
                    return await self._get_value(arguments)
                elif name == "delete":
                    return await self._delete_value(arguments)
                elif name == "list_keys":
                    return await self._list_keys(arguments)
                elif name == "clear_namespace":
                    return await self._clear_namespace(arguments)
                elif name == "get_stats":
                    return await self._get_stats(arguments)
                else:
                    return CallToolResult(
                        content=[TextContent(text=f"Unknown tool: {name}", type="text")], isError=True
                    )
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return CallToolResult(content=[TextContent(text=f"Error: {str(e)}", type="text")], isError=True)

    async def _set_value(self, arguments: dict[str, Any]) -> CallToolResult:
        """Store a value in memory"""
        key = arguments.get("key")
        value = arguments.get("value")
        namespace = arguments.get("namespace", "default")

        if not key or value is None:
            return CallToolResult(
                content=[TextContent(text="Error: key and value are required", type="text")], isError=True
            )

        # Store the value
        self.data_store[namespace][key] = value
        self.metadata[namespace][key] = {
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "size": len(str(value)),
        }

        return CallToolResult(content=[TextContent(text=f"Stored '{key}' in namespace '{namespace}'", type="text")])

    async def _get_value(self, arguments: dict[str, Any]) -> CallToolResult:
        """Retrieve a value from memory"""
        key = arguments.get("key")
        namespace = arguments.get("namespace", "default")

        if not key:
            return CallToolResult(content=[TextContent(text="Error: key is required", type="text")], isError=True)

        if key not in self.data_store[namespace]:
            return CallToolResult(
                content=[TextContent(text=f"Key '{key}' not found in namespace '{namespace}'", type="text")],
                isError=True,
            )

        value = self.data_store[namespace][key]
        metadata = self.metadata[namespace][key]

        result = {"key": key, "namespace": namespace, "value": value, "metadata": metadata}

        return CallToolResult(content=[TextContent(text=json.dumps(result, indent=2), type="text")])

    async def _delete_value(self, arguments: dict[str, Any]) -> CallToolResult:
        """Delete a value from memory"""
        key = arguments.get("key")
        namespace = arguments.get("namespace", "default")

        if not key:
            return CallToolResult(content=[TextContent(text="Error: key is required", type="text")], isError=True)

        if key not in self.data_store[namespace]:
            return CallToolResult(
                content=[TextContent(text=f"Key '{key}' not found in namespace '{namespace}'", type="text")],
                isError=True,
            )

        # Delete the value and metadata
        del self.data_store[namespace][key]
        del self.metadata[namespace][key]

        return CallToolResult(content=[TextContent(text=f"Deleted '{key}' from namespace '{namespace}'", type="text")])

    async def _list_keys(self, arguments: dict[str, Any]) -> CallToolResult:
        """List all keys in a namespace"""
        namespace = arguments.get("namespace", "default")

        keys = list(self.data_store[namespace].keys())

        result = {"namespace": namespace, "keys": keys, "count": len(keys)}

        return CallToolResult(content=[TextContent(text=json.dumps(result, indent=2), type="text")])

    async def _clear_namespace(self, arguments: dict[str, Any]) -> CallToolResult:
        """Clear all data in a namespace"""
        namespace = arguments.get("namespace", "default")

        count = len(self.data_store[namespace])

        # Clear all data and metadata
        self.data_store[namespace].clear()
        self.metadata[namespace].clear()

        return CallToolResult(
            content=[TextContent(text=f"Cleared {count} items from namespace '{namespace}'", type="text")]
        )

    async def _get_stats(self, arguments: dict[str, Any]) -> CallToolResult:
        """Get memory usage statistics"""
        stats = {"namespaces": {}, "total_keys": 0, "total_size_bytes": 0}

        for namespace, data in self.data_store.items():
            namespace_stats = {
                "key_count": len(data),
                "size_bytes": sum(len(str(v)) for v in data.values()),
                "last_updated": datetime.now().isoformat(),
            }
            stats["namespaces"][namespace] = namespace_stats
            stats["total_keys"] += namespace_stats["key_count"]
            stats["total_size_bytes"] += namespace_stats["size_bytes"]

        return CallToolResult(content=[TextContent(text=json.dumps(stats, indent=2), type="text")])

    async def run(self, read_stream, write_stream, options):
        """Run the MCP server"""
        await self.server.run(read_stream, write_stream, options)


# Create global server instance for MCP CLI
server = ProductionMemoryMCPServer()


async def main():
    """Main server function"""
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="memory", server_version="1.0.0", capabilities={"tools": {}, "resources": {}}
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
