#!/usr/bin/env python3
"""
Production PostgreSQL MCP Server
Provides PostgreSQL database operations using real MCP library
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Any

import asyncpg

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
    """Lightweight TTL cache for read-heavy database operations."""

    def __init__(self, ttl_seconds: int = 30, max_entries: int = 256):
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


class ProductionPostgresMCPServer:
    """Production PostgreSQL MCP Server using real MCP library"""

    def __init__(self):
        self.server = Server("postgres")
        self.connection_pool = None
        self.cache = SimpleCache(
            ttl_seconds=int(os.getenv("POSTGRES_CACHE_TTL", "30")),
            max_entries=int(os.getenv("POSTGRES_CACHE_MAX", "256")),
        )
        self._register_handlers()

    def _pool_settings(self) -> dict[str, Any]:
        """Read pool settings from environment with safe defaults."""
        return {
            "min_size": int(os.getenv("POSTGRES_POOL_MIN", "2")),
            "max_size": int(os.getenv("POSTGRES_POOL_MAX", "10")),
            "command_timeout": float(os.getenv("POSTGRES_POOL_COMMAND_TIMEOUT", "60")),
            "max_inactive_connection_lifetime": float(os.getenv("POSTGRES_POOL_MAX_IDLE", "300")),
        }

    async def _initialize_connection_pool(self):
        """Initialize PostgreSQL connection pool with retries."""
        database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/grid")
        settings = self._pool_settings()
        retries = int(os.getenv("POSTGRES_POOL_RETRIES", "3"))
        backoff = float(os.getenv("POSTGRES_POOL_BACKOFF", "2"))

        last_error: Exception | None = None
        for attempt in range(1, retries + 1):
            try:
                self.connection_pool = await asyncpg.create_pool(
                    database_url,
                    **settings,
                )
                logger.info(
                    "PostgreSQL pool ready (min=%s max=%s timeout=%ss)",
                    settings["min_size"],
                    settings["max_size"],
                    settings["command_timeout"],
                )
                return
            except Exception as e:
                last_error = e
                logger.warning("Pool init attempt %s/%s failed: %s", attempt, retries, e)
                if attempt < retries:
                    await asyncio.sleep(backoff**attempt)

        logger.error("Failed to create connection pool after %s attempts: %s", retries, last_error)
        self.connection_pool = None

    def _register_handlers(self):
        """Register MCP handlers"""

        @self.server.list_tools()
        async def list_tools(request: ListToolsRequest) -> ListToolsResult:
            """List available PostgreSQL tools"""
            tools = [
                Tool(
                    name="query",
                    description="Execute SQL query",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "sql": {"type": "string", "description": "SQL query to execute"},
                            "params": {"type": "array", "description": "Query parameters", "default": []},
                        },
                        "required": ["sql"],
                    },
                ),
                Tool(
                    name="list_tables",
                    description="List all tables in database",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="describe_table",
                    description="Get table schema",
                    inputSchema={
                        "type": "object",
                        "properties": {"table": {"type": "string", "description": "Table name"}},
                        "required": ["table"],
                    },
                ),
                Tool(
                    name="get_connection_info",
                    description="Get database connection information",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
            ]
            return ListToolsResult(tools=tools)

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
            """Handle tool calls"""
            try:
                if name == "query":
                    return await self._execute_query(arguments)
                elif name == "list_tables":
                    return await self._list_tables(arguments)
                elif name == "describe_table":
                    return await self._describe_table(arguments)
                elif name == "get_connection_info":
                    return await self._get_connection_info(arguments)
                else:
                    return CallToolResult(
                        content=[TextContent(text=f"Unknown tool: {name}", type="text")], isError=True
                    )
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return CallToolResult(content=[TextContent(text=f"Error: {str(e)}", type="text")], isError=True)

    async def _execute_query(self, arguments: dict[str, Any]) -> CallToolResult:
        """Execute SQL query"""
        sql = arguments.get("sql")
        params = arguments.get("params", [])

        if not sql:
            return CallToolResult(content=[TextContent(text="Error: SQL query is required", type="text")], isError=True)

        if not self.connection_pool:
            return CallToolResult(
                content=[
                    TextContent(text="Database connection not available. Please check DATABASE_URL.", type="text")
                ],
                isError=True,
            )

        try:
            async with self.connection_pool.acquire() as conn:
                # Check if it's a SELECT query
                sql_upper = sql.strip().upper()
                if sql_upper.startswith("SELECT") or sql_upper.startswith("WITH"):
                    # SELECT query - return results
                    rows = await conn.fetch(sql, *params)
                    columns = list(rows[0].keys()) if rows else []

                    result = {"columns": columns, "rows": [dict(row) for row in rows], "count": len(rows)}

                    return CallToolResult(
                        content=[TextContent(text=json.dumps(result, indent=2, default=str), type="text")]
                    )
                else:
                    # INSERT, UPDATE, DELETE - return affected rows
                    result = await conn.execute(sql, *params)

                    return CallToolResult(
                        content=[TextContent(text=f"Query executed successfully. Result: {result}", type="text")]
                    )

        except Exception as e:
            return CallToolResult(
                content=[TextContent(text=f"Query execution error: {str(e)}", type="text")], isError=True
            )

    async def _list_tables(self, arguments: dict[str, Any]) -> CallToolResult:
        """List all tables in database"""
        if not self.connection_pool:
            return CallToolResult(
                content=[TextContent(text="Database connection not available", type="text")], isError=True
            )

        cache_key = ("list_tables",)
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            async with self.connection_pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
                )
                tables = [row["table_name"] for row in rows]

                result = {"tables": tables, "count": len(tables)}

                response = CallToolResult(content=[TextContent(text=json.dumps(result, indent=2), type="text")])
                self.cache.set(cache_key, response)
                return response
        except Exception as e:
            return CallToolResult(
                content=[TextContent(text=f"Error listing tables: {str(e)}", type="text")], isError=True
            )

    async def _describe_table(self, arguments: dict[str, Any]) -> CallToolResult:
        """Get table schema"""
        table = arguments.get("table")

        if not table:
            return CallToolResult(
                content=[TextContent(text="Error: table name is required", type="text")], isError=True
            )

        if not self.connection_pool:
            return CallToolResult(
                content=[TextContent(text="Database connection not available", type="text")], isError=True
            )

        cache_key = ("describe_table", table)
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            async with self.connection_pool.acquire() as conn:
                # Get column information
                columns = await conn.fetch(
                    """
                    SELECT
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        character_maximum_length
                    FROM information_schema.columns
                    WHERE table_name = $1 AND table_schema = 'public'
                    ORDER BY ordinal_position
                """,
                    table,
                )

                # Get primary key information
                pks = await conn.fetch(
                    """
                    SELECT column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.table_name = $1
                        AND tc.constraint_type = 'PRIMARY KEY'
                        AND tc.table_schema = 'public'
                """,
                    table,
                )

                primary_keys = [pk["column_name"] for pk in pks]

                schema = []
                for col in columns:
                    schema.append(
                        {
                            "name": col["column_name"],
                            "type": col["data_type"],
                            "nullable": col["is_nullable"] == "YES",
                            "default": col["column_default"],
                            "max_length": col["character_maximum_length"],
                            "primary_key": col["column_name"] in primary_keys,
                        }
                    )

                response = CallToolResult(content=[TextContent(text=json.dumps(schema, indent=2), type="text")])
                self.cache.set(cache_key, response)
                return response
        except Exception as e:
            return CallToolResult(
                content=[TextContent(text=f"Error describing table: {str(e)}", type="text")], isError=True
            )

    async def _get_connection_info(self, arguments: dict[str, Any]) -> CallToolResult:
        """Get database connection information"""
        cache_key = ("connection_info",)
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        info = {
            "database_url": os.getenv("DATABASE_URL", "Not configured"),
            "connection_pool_active": self.connection_pool is not None,
            "server_version": "Unknown",
            "timestamp": datetime.now().isoformat(),
        }

        if self.connection_pool:
            try:
                async with self.connection_pool.acquire() as conn:
                    version = await conn.fetchval("SELECT version()")
                    info["server_version"] = version
                    info["pool_size"] = self.connection_pool.get_size()
                    info["pool_idle"] = self.connection_pool.get_idle_size()
                    info["pool_min"] = self.connection_pool._minsize
                    info["pool_max"] = self.connection_pool._maxsize
            except Exception as e:
                info["connection_error"] = str(e)

        response = CallToolResult(content=[TextContent(text=json.dumps(info, indent=2), type="text")])
        self.cache.set(cache_key, response)
        return response

    async def run(self, read_stream, write_stream, options):
        """Run the MCP server"""
        # Initialize connection pool
        await self._initialize_connection_pool()
        await self.server.run(read_stream, write_stream, options)


# Create global server instance for MCP CLI
server = ProductionPostgresMCPServer()


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
