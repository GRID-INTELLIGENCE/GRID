#!/usr/bin/env python3
"""
Production Filesystem MCP Server
Uses real MCP library implementation
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any

# Real MCP imports
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    ServerCapabilities,
    TextContent,
    Tool,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProductionFilesystemMCPServer:
    """Production Filesystem MCP Server using real MCP library"""

    def __init__(self):
        self.server = Server("filesystem")
        self.allowed_roots = self._get_allowed_roots()
        self._register_handlers()

    def _get_allowed_roots(self) -> list[str]:
        """Get allowed root directories for security"""
        roots = [
            os.path.expanduser("~"),  # C:/Users/irfan
            os.getcwd(),  # Current workspace
        ]

        # Add common drive roots if they exist
        for drive in ["C:", "E:", "D:"]:
            if os.path.exists(drive):
                roots.append(drive)

        logger.info(f"Allowed roots: {roots}")
        return roots

    def _is_path_allowed(self, path: str) -> bool:
        """Check if path is within allowed roots"""
        abs_path = os.path.abspath(path)
        return any(abs_path.startswith(os.path.abspath(root)) for root in self.allowed_roots)

    def _register_handlers(self):
        """Register MCP handlers"""

        @self.server.list_tools()
        async def list_tools(request: ListToolsRequest) -> ListToolsResult:
            """List available filesystem tools"""
            tools = [
                Tool(
                    name="read_file",
                    description="Read the contents of a file",
                    inputSchema={
                        "type": "object",
                        "properties": {"path": {"type": "string", "description": "Path to the file to read"}},
                        "required": ["path"],
                    },
                ),
                Tool(
                    name="list_directory",
                    description="List contents of a directory",
                    inputSchema={
                        "type": "object",
                        "properties": {"path": {"type": "string", "description": "Path to the directory to list"}},
                        "required": ["path"],
                    },
                ),
                Tool(
                    name="get_file_info",
                    description="Get information about a file or directory",
                    inputSchema={
                        "type": "object",
                        "properties": {"path": {"type": "string", "description": "Path to the file or directory"}},
                        "required": ["path"],
                    },
                ),
                Tool(
                    name="create_directory",
                    description="Create a new directory",
                    inputSchema={
                        "type": "object",
                        "properties": {"path": {"type": "string", "description": "Path to the directory to create"}},
                        "required": ["path"],
                    },
                ),
                Tool(
                    name="write_file",
                    description="Write content to a file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Path to the file to write"},
                            "content": {"type": "string", "description": "Content to write to the file"},
                        },
                        "required": ["path", "content"],
                    },
                ),
            ]
            return ListToolsResult(tools=tools)

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
            """Handle tool calls"""
            try:
                if name == "read_file":
                    return await self._read_file(arguments)
                elif name == "list_directory":
                    return await self._list_directory(arguments)
                elif name == "get_file_info":
                    return await self._get_file_info(arguments)
                elif name == "create_directory":
                    return await self._create_directory(arguments)
                elif name == "write_file":
                    return await self._write_file(arguments)
                else:
                    return CallToolResult(
                        content=[TextContent(text=f"Unknown tool: {name}", type="text")], isError=True
                    )
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return CallToolResult(content=[TextContent(text=f"Error: {str(e)}", type="text")], isError=True)

    async def _read_file(self, arguments: dict[str, Any]) -> CallToolResult:
        """Read file contents"""
        path = arguments.get("path")

        if not path or not self._is_path_allowed(path):
            return CallToolResult(
                content=[TextContent(text="Access denied: path not allowed", type="text")], isError=True
            )

        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()

            return CallToolResult(content=[TextContent(text=content, type="text")])
        except Exception as e:
            return CallToolResult(
                content=[TextContent(text=f"Error reading file: {str(e)}", type="text")], isError=True
            )

    async def _list_directory(self, arguments: dict[str, Any]) -> CallToolResult:
        """List directory contents"""
        path = arguments.get("path")

        if not path or not self._is_path_allowed(path):
            return CallToolResult(
                content=[TextContent(text="Access denied: path not allowed", type="text")], isError=True
            )

        try:
            items = []
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                item_type = "directory" if os.path.isdir(item_path) else "file"
                items.append(f"{item_type}: {item}")

            content = "\n".join(items)
            return CallToolResult(content=[TextContent(text=content, type="text")])
        except Exception as e:
            return CallToolResult(
                content=[TextContent(text=f"Error listing directory: {str(e)}", type="text")], isError=True
            )

    async def _get_file_info(self, arguments: dict[str, Any]) -> CallToolResult:
        """Get file/directory information"""
        path = arguments.get("path")

        if not path or not self._is_path_allowed(path):
            return CallToolResult(
                content=[TextContent(text="Access denied: path not allowed", type="text")], isError=True
            )

        try:
            stat = os.stat(path)
            info = {
                "path": path,
                "type": "directory" if os.path.isdir(path) else "file",
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "permissions": oct(stat.st_mode)[-3:],
            }

            return CallToolResult(content=[TextContent(text=json.dumps(info, indent=2), type="text")])
        except Exception as e:
            return CallToolResult(
                content=[TextContent(text=f"Error getting file info: {str(e)}", type="text")], isError=True
            )

    async def _create_directory(self, arguments: dict[str, Any]) -> CallToolResult:
        """Create directory"""
        path = arguments.get("path")

        if not path or not self._is_path_allowed(path):
            return CallToolResult(
                content=[TextContent(text="Access denied: path not allowed", type="text")], isError=True
            )

        try:
            os.makedirs(path, exist_ok=True)
            return CallToolResult(content=[TextContent(text=f"Directory created: {path}", type="text")])
        except Exception as e:
            return CallToolResult(
                content=[TextContent(text=f"Error creating directory: {str(e)}", type="text")], isError=True
            )

    async def _write_file(self, arguments: dict[str, Any]) -> CallToolResult:
        """Write file content"""
        path = arguments.get("path")
        content = arguments.get("content", "")

        if not path or not self._is_path_allowed(path):
            return CallToolResult(
                content=[TextContent(text="Access denied: path not allowed", type="text")], isError=True
            )

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            return CallToolResult(content=[TextContent(text=f"File written: {path}", type="text")])
        except Exception as e:
            return CallToolResult(
                content=[TextContent(text=f"Error writing file: {str(e)}", type="text")], isError=True
            )

    async def run(self, read_stream, write_stream, options):
        """Run the MCP server"""
        await self.server.run(read_stream, write_stream, options)


# Create global server instance for MCP CLI
server = ProductionFilesystemMCPServer()


async def main():
    """Main server function"""
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="filesystem",
                server_version="1.0.0",
                capabilities=ServerCapabilities(tools={}, resources={}),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
