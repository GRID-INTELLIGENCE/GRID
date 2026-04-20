#!/usr/bin/env python3
"""
Production Database MCP Server
Provides SQLite database operations using real MCP library
"""

import asyncio
import json
import logging
import re
import sqlite3
import time
from typing import Any

# Real MCP imports
from mcp.server import Server
from mcp.types import CallToolResult, ListToolsResult, TextContent, Tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SQLInjectionValidator:
    """Validates SQL queries and inputs against injection attacks."""

    # Dangerous statement starters — anything that isn't a plain SELECT
    _DANGEROUS_STARTERS = (
        "DROP ",
        "DELETE ",
        "INSERT ",
        "UPDATE ",
        "ALTER ",
        "CREATE ",
        "TRUNCATE ",
        "EXEC ",
        "EXECUTE ",
        "UNION ",
    )

    # SQL injection patterns in raw input strings
    _INPUT_INJECTION_PATTERNS = [
        r"'[^']*;",  # single-quote then semicolon (classic injection)
        r"--\s*(?:\n|$)",  # line comment at end of input
        r";\s*(?:DROP|DELETE|INSERT|UPDATE|ALTER|EXEC)\b",  # compound dangerous stmt
        r"'\s*;",  # quote-then-semicolon shorthand
    ]

    def validate_query(self, sql: str) -> bool:
        """Return True only for safe SELECT-only queries with no compound statements."""
        sql_stripped = sql.strip()
        sql_upper = sql_stripped.upper()

        # Must be a plain SELECT
        if not sql_upper.startswith("SELECT ") and sql_upper != "SELECT":
            return False

        # No compound statements
        if ";" in sql_stripped:
            return False

        # No UNION-based injection (covers SELECT … UNION SELECT …)
        if re.search(r"\bUNION\b", sql_upper):
            return False

        return True

    def sanitize_input(self, input_str: str) -> str:
        """Return input unchanged if safe; raise ValueError if injection pattern detected."""
        for pattern in self._INPUT_INJECTION_PATTERNS:
            if re.search(pattern, input_str, re.IGNORECASE):
                raise ValueError("Potentially malicious SQL input detected: injection pattern matched")
        return input_str

    def validate_table_name(self, name: str) -> bool:
        """Return True for identifiers that contain only alphanumerics, underscores, and dots."""
        if not name:
            return False
        return bool(re.match(r"^[a-zA-Z0-9_.]+$", name))


class ConnectionManager:
    """Manages SQLite connections with a per-manager limit and idle timeout."""

    def __init__(self, max_connections: int = 10, connection_timeout: int = 300):
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        # Each entry: {"conn": <connection>, "db_path": str, "created_at": float}
        self.connections: dict = {}

    def add_connection(self, name: str, conn, db_path: str) -> bool:
        """Register a connection under *name*. Returns False when the pool is full."""
        if len(self.connections) >= self.max_connections:
            return False
        self.connections[name] = {
            "conn": conn,
            "db_path": db_path,
            "created_at": time.time(),
        }
        return True

    def get_connection(self, name: str):
        """Return the connection or None if it is unknown or has exceeded the timeout."""
        if name not in self.connections:
            return None
        entry = self.connections[name]
        if time.time() - entry["created_at"] > self.connection_timeout:
            del self.connections[name]
            return None
        return entry["conn"]

    def remove_connection(self, name: str) -> bool:
        """Remove and return True if the connection existed, False otherwise."""
        if name in self.connections:
            del self.connections[name]
            return True
        return False


class ProductionDatabaseMCPServer:
    """Production Database MCP Server using real MCP library"""

    def __init__(self):
        self.server = Server("database")
        self.connections = {}
        self._validator = SQLInjectionValidator()
        self._allowed_query_patterns = [
            "^SELECT\\s+",  # Only SELECT queries allowed for read operations
            "^INSERT\\s+INTO\\s+[a-zA-Z_][a-zA-Z0-9_]*\\s+VALUES\\s*\\(",
            "^UPDATE\\s+[a-zA-Z_][a-zA-Z0-9_]*\\s+SET\\s+[a-zA-Z_][a-zA-Z0-9_]*\\s*=\\s*\\?",
            "^DELETE\\s+FROM\\s+[a-zA-Z_][a-zA-Z0-9_]*\\s+WHERE\\s+[a-zA-Z_][a-zA-Z0-9_]*\\s*=\\s*\\?",
        ]
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
        """Execute SQL query with security validation"""
        connection = arguments.get("connection")
        sql = arguments.get("sql")
        params = arguments.get("params", [])

        if connection not in self.connections:
            return CallToolResult(
                content=[TextContent(text=f"Connection {connection} not found", type="text")], isError=True
            )

        # Security: Validate SQL query pattern
        if not self._is_query_safe(sql):
            return CallToolResult(
                content=[
                    TextContent(
                        text="Query rejected: SQL pattern not allowed. Only SELECT queries with proper validation are permitted.",
                        type="text",
                    )
                ],
                isError=True,
            )

        try:
            conn = self.connections[connection]
            cursor = conn.cursor()

            # Security: Use parameterized queries
            if params:
                cursor.execute(sql, params)
            else:
                # For SELECT queries without parameters, ensure it's a safe read-only query
                if not sql.strip().upper().startswith("SELECT"):
                    return CallToolResult(
                        content=[
                            TextContent(
                                text="Query rejected: Only SELECT queries are allowed without parameters.", type="text"
                            )
                        ],
                        isError=True,
                    )
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
            logger.error(f"Query execution error: {e}")
            return CallToolResult(
                content=[TextContent(text=f"Error executing query: {str(e)}", type="text")], isError=True
            )

    def _is_query_safe(self, sql: str) -> bool:
        """Validate SQL query against injection patterns using SQLInjectionValidator."""
        return self._validator.validate_query(sql)

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
    # MCP stdio transport requires interactive mode
    await run_health_server()


if __name__ == "__main__":
    asyncio.run(main())
