#!/usr/bin/env python3
"""
Production Memory MCP Server
Provides in-memory data storage and retrieval using real MCP library
"""

import asyncio
import json
import logging
import os
import time
from collections import defaultdict
from datetime import datetime
from typing import Any

# Real MCP imports
from mcp.server import Server
from mcp.types import (
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    TextContent,
    Tool,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleCache:
    """Lightweight TTL cache for read-heavy operations"""

    def __init__(self, ttl_seconds: int = 15, max_entries: int = 512):
        self.ttl = ttl_seconds
        self.max_entries = max_entries
        self._store: dict[tuple[Any, ...], tuple[Any, float]] = {}

    def get(self, key: tuple[Any, ...]) -> Any | None:
        entry = self._store.get(key)
        if not entry:
            return None
        value, timestamp = entry
        if time.time() - timestamp > self.ttl:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: tuple[Any, ...], value: Any) -> None:
        if len(self._store) >= self.max_entries:
            oldest_key = min(self._store.items(), key=lambda item: item[1][1])[0]
            self._store.pop(oldest_key, None)
        self._store[key] = (value, time.time())

    def clear(self) -> None:
        self._store.clear()


class ProductionMemoryMCPServer:
    """Production Memory MCP Server using real MCP library"""

    def __init__(self):
        self.server = Server("memory")
        self.data_store = defaultdict(dict)
        self.metadata = defaultdict(dict)
        self.cache = SimpleCache(ttl_seconds=int(os.getenv("MEMORY_CACHE_TTL", "15")))
        self._register_handlers()

    def _register_handlers(self):
        """Register MCP handlers"""

        @self.server.list_tools()
        async def list_tools(request: ListToolsRequest) -> ListToolsResult:
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
                Tool(
                    name="get_stats",
                    description="Get memory usage statistics",
                    inputSchema={"type": "object", "properties": {}},
                ),
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
        self.cache.clear()

        return CallToolResult(content=[TextContent(text=f"Stored '{key}' in namespace '{namespace}'", type="text")])

    async def _get_value(self, arguments: dict[str, Any]) -> CallToolResult:
        """Retrieve a value from memory"""
        key = arguments.get("key")
        namespace = arguments.get("namespace", "default")

        if not key:
            return CallToolResult(content=[TextContent(text="Error: key is required", type="text")], isError=True)

        cache_key = ("get", namespace, key)
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        if key not in self.data_store[namespace]:
            return CallToolResult(
                content=[TextContent(text=f"Key '{key}' not found in namespace '{namespace}'", type="text")],
                isError=True,
            )

        value = self.data_store[namespace][key]
        metadata = self.metadata[namespace][key]

        result = {"key": key, "namespace": namespace, "value": value, "metadata": metadata}

        response = CallToolResult(content=[TextContent(text=json.dumps(result, indent=2), type="text")])
        self.cache.set(cache_key, response)
        return response

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
        self.cache.clear()

        return CallToolResult(content=[TextContent(text=f"Deleted '{key}' from namespace '{namespace}'", type="text")])

    async def _list_keys(self, arguments: dict[str, Any]) -> CallToolResult:
        """List all keys in a namespace"""
        namespace = arguments.get("namespace", "default")

        cache_key = ("list_keys", namespace)
        cached = self.cache.get(cache_key)
        if cached:
            return cached

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
        self.cache.clear()

        return CallToolResult(
            content=[TextContent(text=f"Cleared {count} items from namespace '{namespace}'", type="text")]
        )

    async def _get_stats(self, arguments: dict[str, Any]) -> CallToolResult:
        """Get memory usage statistics"""
        cache_key = ("get_stats",)
        cached = self.cache.get(cache_key)
        if cached:
            return cached

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

        response = CallToolResult(content=[TextContent(text=json.dumps(stats, indent=2), type="text")])
        self.cache.set(cache_key, response)
        return response

    async def run(self, read_stream, write_stream, options):
        """Run the MCP server"""
        await self.server.run(read_stream, write_stream, options)


# Create global server instance for MCP CLI
server = ProductionMemoryMCPServer()


async def run_health_server(host: str = "0.0.0.0", port: int = 8080):
    """Run a minimal HTTP health server in background."""
    from aiohttp import web

    async def health_handler(request):
        return web.Response(text="healthy\n", content_type="text/plain")

    app = web.Application()
    app.router.add_get("/health", health_handler)
    app.router.add_get("/", health_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logger.info(f"Health server started on {host}:{port}")

    # Keep running forever
    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        await runner.cleanup()


async def main():
    """Main server function with health endpoint."""
    # MCP stdio transport requires interactive mode
    await run_health_server()


if __name__ == "__main__":
    asyncio.run(main())
