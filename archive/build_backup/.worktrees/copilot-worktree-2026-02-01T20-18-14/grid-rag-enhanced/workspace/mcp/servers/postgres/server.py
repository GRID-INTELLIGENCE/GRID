#!/usr/bin/env python3
"""
Production PostgreSQL MCP Server
Provides PostgreSQL database operations using real MCP library
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any

import asyncpg

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


class ProductionPostgresMCPServer:
    """Production PostgreSQL MCP Server using real MCP library"""

    def __init__(self):
        self.server = Server("postgres")
        self.connection_pool = None
        self._register_handlers()

    async def _initialize_connection_pool(self):
        """Initialize PostgreSQL connection pool"""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            logger.warning("DATABASE_URL not set - database features will be unavailable")
            return

        try:
            self.connection_pool = await asyncpg.create_pool(database_url, min_size=2, max_size=10, command_timeout=60)
            logger.info("PostgreSQL connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            # Continue without database connection for testing

    def _register_handlers(self):
        """Register MCP handlers"""

        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
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
                Tool(name="list_tables", description="List all tables in database"),
                Tool(
                    name="describe_table",
                    description="Get table schema",
                    inputSchema={
                        "type": "object",
                        "properties": {"table": {"type": "string", "description": "Table name"}},
                        "required": ["table"],
                    },
                ),
                Tool(name="get_connection_info", description="Get database connection information"),
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

        try:
            async with self.connection_pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
                )
                tables = [row["table_name"] for row in rows]

                result = {"tables": tables, "count": len(tables)}

                return CallToolResult(content=[TextContent(text=json.dumps(result, indent=2), type="text")])
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

                return CallToolResult(content=[TextContent(text=json.dumps(schema, indent=2), type="text")])
        except Exception as e:
            return CallToolResult(
                content=[TextContent(text=f"Error describing table: {str(e)}", type="text")], isError=True
            )

    async def _get_connection_info(self, arguments: dict[str, Any]) -> CallToolResult:
        """Get database connection information"""
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
            except Exception as e:
                info["connection_error"] = str(e)

        return CallToolResult(content=[TextContent(text=json.dumps(info, indent=2), type="text")])

    async def run(self, read_stream, write_stream, options):
        """Run the MCP server"""
        # Initialize connection pool
        await self._initialize_connection_pool()
        await self.server.run(read_stream, write_stream, options)


# Create global server instance for MCP CLI
server = ProductionPostgresMCPServer()


async def main():
    """Main server function"""
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="postgres", server_version="1.0.0", capabilities={"tools": {}, "resources": {}}
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
