#!/usr/bin/env python
"""
GRID Memory MCP Server
Provides local memory storage and retrieval for agents
"""

import asyncio
import json
import logging
from typing import Any, Dict, List
from pathlib import Path
from mcp.server.stdio import stdio_server
from mcp.server import Server
from mcp.types import Tool, TextContent

logger = logging.getLogger(__name__)

server = Server("grid-memory")
MEMORY_DIR = Path.home() / ".grid" / "memory"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="store_memory",
            description="Store data in local memory",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Memory key"},
                    "value": {"type": "string", "description": "Value to store"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Optional tags"},
                },
                "required": ["key", "value"],
            },
        ),
        Tool(
            name="retrieve_memory",
            description="Retrieve data from local memory",
            inputSchema={
                "type": "object",
                "properties": {"key": {"type": "string", "description": "Memory key"}},
                "required": ["key"],
            },
        ),
        Tool(name="list_memory", description="List all stored memories", inputSchema={}),
        Tool(name="clear_memory", description="Clear all stored memories", inputSchema={}),
    ]


def get_memory_path(key: str) -> Path:
    return MEMORY_DIR / f"{key}.json"


@server.call_tool()
async def call_tool(name: str, args: dict[str, Any]) -> list[TextContent]:
    if name == "store_memory":
        key = args.get("key")
        value = args.get("value")
        tags = args.get("tags", [])

        memory_data = {"key": key, "value": value, "tags": tags, "created_at": asyncio.get_event_loop().time()}

        memory_path = get_memory_path(key)
        memory_path.write_text(json.dumps(memory_data, indent=2))

        logger.info(f"Stored memory: {key}")
        return [TextContent(f"Stored memory: {key}")]

    elif name == "retrieve_memory":
        key = args.get("key")
        memory_path = get_memory_path(key)

        if memory_path.exists():
            data = json.loads(memory_path.read_text())
            return [TextContent(json.dumps(data, indent=2))]
        else:
            return [TextContent("Memory not found")]

    elif name == "list_memory":
        memories: List[Dict] = []
        for memory_file in MEMORY_DIR.glob("*.json"):
            data = json.loads(memory_file.read_text())
            memories.append({"key": data["key"], "tags": data.get("tags", [])})

        return [TextContent(json.dumps({"memories": memories}, indent=2))]

    elif name == "clear_memory":
        for memory_file in MEMORY_DIR.glob("*.json"):
            memory_file.unlink()

        logger.info("Cleared all memories")
        return [TextContent("Memory cleared")]

    return [TextContent("Unknown tool")]


async def main():
    logging.basicConfig(level=logging.INFO)
    logger.info("GRID Memory MCP Server starting...")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, Server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
