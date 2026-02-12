#!/usr/bin/env python3
"""
Production Database MCP Server
Provides SQLite database operations using real MCP library
"""

import asyncio
import json
import logging
import sqlite3
from typing import Any

# Real MCP imports
from mcp.server import Server
from mcp.types import CallToolResult, ListToolsResult, TextContent, Tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProductionDatabaseMCPServer:
    """Production Database MCP Server using real MCP library"""

    def __init__(self):
        self.server = Server("database")
        self.connections = {}
        self._register_handlers()

    def _register_handlers(self):
        """Register MCP handlers"""

        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """List available database tools"""
            tools = [
                Tool(
                    name="connect",
                    description="Connect to a SQLite database",
                    inputSchema={
                        "type": "object",
                        "properties": {"database": {"type": "string", "description": "Path to SQLite database file"}},
                        "required": ["database"],
                    },
                ),
                Tool(
                    name="query",
                    description="Execute SQL query",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "connection": {"type": "string", "description": "Connection name"},
                            "sql": {"type": "string", "description": "SQL query to execute"},
                        },
                        "required": ["connection", "sql"],
                    },
                ),
                Tool(
                    name="list_tables",
                    description="List all tables in database",
                    inputSchema={
                        "type": "object",
                        "properties": {"connection": {"type": "string", "description": "Connection name"}},
                        "required": ["connection"],
                    },
                ),
                Tool(
                    name="describe_table",
                    description="Get table schema",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "connection": {"type": "string", "description": "Connection name"},
                            "table": {"type": "string", "description": "Table name"},
                        },
                        "required": ["connection", "table"],
                    },
                ),
            ]
            return ListToolsResult(tools=tools)

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
            """Handle tool calls"""
            try:
                if name == "connect":
                    return await self._connect(arguments)
                elif name == "query":
                    return await self._query(arguments)
                elif name == "list_tables":
                    return await self._list_tables(arguments)
                elif name == "describe_table":
                    return await self._describe_table(arguments)
                else:
                    return CallToolResult(
                        content=[TextContent(text=f"Unknown tool: {name}", type="text")], isError=True
                    )
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return CallToolResult(content=[TextContent(text=f"Error: {str(e)}", type="text")], isError=True)

    async def _connect(self, arguments: dict[str, Any]) -> CallToolResult:
        """Connect to SQLite database"""
        database = arguments.get("database")
        connection_name = f"conn_{len(self.connections)}"

        try:
            conn = sqlite3.connect(database)
            self.connections[connection_name] = conn

            return CallToolResult(
                content=[TextContent(text=f"Connected to {database} as {connection_name}", type="text")]
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(text=f"Error connecting to database: {str(e)}", type="text")], isError=True
            )

    async def _query(self, arguments: dict[str, Any]) -> CallToolResult:
        """Execute SQL query"""
        connection = arguments.get("connection")
        sql = arguments.get("sql")

        if connection not in self.connections:
            return CallToolResult(
                content=[TextContent(text=f"Connection {connection} not found", type="text")], isError=True
            )

        try:
            conn = self.connections[connection]
            cursor = conn.cursor()
            cursor.execute(sql)

            # Check if it's a SELECT query
            if sql.strip().upper().startswith("SELECT"):
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]

                result = {"columns": columns, "rows": rows, "count": len(rows)}

                return CallToolResult(content=[TextContent(text=json.dumps(result, indent=2), type="text")])
            else:
                # For INSERT, UPDATE, DELETE
                conn.commit()
                affected = cursor.rowcount

                return CallToolResult(
                    content=[TextContent(text=f"Query executed successfully. {affected} rows affected.", type="text")]
                )

        except Exception as e:
            return CallToolResult(
                content=[TextContent(text=f"Error executing query: {str(e)}", type="text")], isError=True
            )

    async def _list_tables(self, arguments: dict[str, Any]) -> CallToolResult:
        """List all tables in database"""
        connection = arguments.get("connection")

        if connection not in self.connections:
            return CallToolResult(
                content=[TextContent(text=f"Connection {connection} not found", type="text")], isError=True
            )

        try:
            conn = self.connections[connection]
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            return CallToolResult(content=[TextContent(text=json.dumps(tables, indent=2), type="text")])
        except Exception as e:
            return CallToolResult(
                content=[TextContent(text=f"Error listing tables: {str(e)}", type="text")], isError=True
            )

    async def _describe_table(self, arguments: dict[str, Any]) -> CallToolResult:
        """Get table schema"""
        connection = arguments.get("connection")
        table = arguments.get("table")

        if connection not in self.connections:
            return CallToolResult(
                content=[TextContent(text=f"Connection {connection} not found", type="text")], isError=True
            )

        # Security: Validate table name to prevent SQL injection
        # Table names must be alphanumeric with underscores only
        if not table or not all(c.isalnum() or c == "_" for c in table):
            return CallToolResult(
                content=[
                    TextContent(
                        text=f"Invalid table name: {table}. Only alphanumeric characters and underscores allowed.",
                        type="text",
                    )
                ],
                isError=True,
            )

        try:
            conn = self.connections[connection]
            cursor = conn.cursor()
            # Use parameterized identifier by validating above and quoting
            cursor.execute(f'PRAGMA table_info("{table}")')
            columns = cursor.fetchall()

            schema = []
            for col in columns:
                schema.append(
                    {
                        "name": col[1],
                        "type": col[2],
                        "not_null": bool(col[3]),
                        "primary_key": bool(col[5]),
                        "default_value": col[4],
                    }
                )

            return CallToolResult(content=[TextContent(text=json.dumps(schema, indent=2), type="text")])
        except Exception as e:
            return CallToolResult(
                content=[TextContent(text=f"Error describing table: {str(e)}", type="text")], isError=True
            )

    async def run(self, read_stream, write_stream, options):
        """Run the MCP server"""
        await self.server.run(read_stream, write_stream, options)


# Create global server instance for MCP CLI
server = ProductionDatabaseMCPServer()


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
    # In Docker daemon mode, run only the health server
    # MCP stdio transport requires interactive mode
    await run_health_server()


if __name__ == "__main__":
    asyncio.run(main())
