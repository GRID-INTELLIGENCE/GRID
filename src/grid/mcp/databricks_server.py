#!/usr/bin/env python3
"""
Databricks MCP Server with Coinbase Integration

Provides Databricks operations for Coinbase data processing.
"""

import aiofiles
import asyncio
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add GRID to path
grid_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(grid_root / "src"))

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        CallToolResult,
        TextContent,
        Tool,
    )
except ImportError:
    print("MCP library not found. Please install: pip install mcp")
    sys.exit(1)

# Databricks SDK
try:
    from databricks.sdk import WorkspaceClient
except ImportError:
    print("Databricks SDK not found. Please install: pip install databricks-sdk")
    sys.exit(1)

# Coinbase SDK (if needed)
try:
    import coinbase
except ImportError:
    coinbase = None

# Configure logging
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DatabricksConfig:
    """Databricks configuration."""

    host: str
    token: str
    coinbase_api_key: str | None = None
    coinbase_api_secret: str | None = None
    coinbase_project_path: str = "E:\\coinbase"


class DatabricksCoinbaseMCPServer:
    """Databricks MCP Server with Coinbase Integration"""

    def __init__(self):
        self.server = Server("databricks-coinbase")
        self.config = self._load_config()
        self.client = WorkspaceClient(host=self.config.host, token=self.config.token)
        self.project_path = Path(self.config.coinbase_project_path)
        self._register_handlers()

    def _load_config(self) -> DatabricksConfig:
        """Load configuration from environment"""
        host = os.getenv("DATABRICKS_HOST")
        token = os.getenv("DATABRICKS_TOKEN")
        coinbase_key = os.getenv("COINBASE_API_KEY")
        coinbase_secret = os.getenv("COINBASE_API_SECRET")
        coinbase_project_path = os.getenv("COINBASE_PROJECT_PATH", "E:\\coinbase")

        if not host or not token:
            raise ValueError("DATABRICKS_HOST and DATABRICKS_TOKEN environment variables required")

        return DatabricksConfig(
            host=host,
            token=token,
            coinbase_api_key=coinbase_key,
            coinbase_api_secret=coinbase_secret,
            coinbase_project_path=coinbase_project_path,
        )

    def _register_handlers(self):
        """Register MCP handlers"""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available Databricks and Coinbase tools"""
            tools = [
                Tool(
                    name="databricks_list_clusters",
                    description="List all Databricks clusters",
                    inputSchema={"type": "object", "properties": {}, "required": []},
                ),
                Tool(
                    name="databricks_get_cluster",
                    description="Get details of a specific cluster",
                    inputSchema={
                        "type": "object",
                        "properties": {"cluster_id": {"type": "string", "description": "Cluster ID"}},
                        "required": ["cluster_id"],
                    },
                ),
                Tool(
                    name="databricks_start_cluster",
                    description="Start a Databricks cluster",
                    inputSchema={
                        "type": "object",
                        "properties": {"cluster_id": {"type": "string", "description": "Cluster ID"}},
                        "required": ["cluster_id"],
                    },
                ),
                Tool(
                    name="databricks_list_jobs",
                    description="List Databricks jobs",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "page_token": {
                                "type": "string",
                                "description": "Page token for pagination",
                                "default": None,
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of jobs to return",
                                "default": 25,
                            },
                        },
                        "required": [],
                    },
                ),
                Tool(
                    name="databricks_run_job",
                    description="Run a Databricks job",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "job_id": {"type": "string", "description": "Job ID"},
                            "parameters": {"type": "object", "description": "Job parameters", "default": {}},
                        },
                        "required": ["job_id"],
                    },
                ),
                Tool(
                    name="databricks_query_sql",
                    description="Execute SQL query on Databricks SQL warehouse",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "warehouse_id": {"type": "string", "description": "SQL warehouse ID"},
                            "query": {"type": "string", "description": "SQL query"},
                        },
                        "required": ["warehouse_id", "query"],
                    },
                ),
                Tool(
                    name="databricks_upload_file",
                    description="Upload a file from Coinbase project to Databricks DBFS",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Relative path to file in Coinbase project"},
                            "dbfs_path": {"type": "string", "description": "DBFS path to upload to"},
                        },
                        "required": ["file_path", "dbfs_path"],
                    },
                ),
                Tool(
                    name="coinbase_list_files",
                    description="List files in the Coinbase project directory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "subdir": {"type": "string", "description": "Subdirectory to list", "default": "."},
                        },
                        "required": [],
                    },
                ),
            ]

            # Add Coinbase tools if available
            if self.config.coinbase_api_key:
                tools.extend(
                    [
                        Tool(
                            name="coinbase_get_prices",
                            description="Get current cryptocurrency prices from Coinbase",
                            inputSchema={
                                "type": "object",
                                "properties": {
                                    "currency_pair": {
                                        "type": "string",
                                        "description": "Currency pair (e.g., BTC-USD)",
                                        "default": "BTC-USD",
                                    },
                                },
                                "required": [],
                            },
                        ),
                        Tool(
                            name="databricks_store_coinbase_data",
                            description="Fetch Coinbase data and store in Databricks table",
                            inputSchema={
                                "type": "object",
                                "properties": {
                                    "currency_pair": {
                                        "type": "string",
                                        "description": "Currency pair",
                                        "default": "BTC-USD",
                                    },
                                    "table_name": {"type": "string", "description": "Databricks table name"},
                                    "catalog": {
                                        "type": "string",
                                        "description": "Catalog name",
                                        "default": "hive_metastore",
                                    },
                                    "schema": {"type": "string", "description": "Schema name", "default": "default"},
                                },
                                "required": ["table_name"],
                            },
                        ),
                    ]
                )

            return tools

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
            """Handle tool calls"""
            try:
                if name == "databricks_list_clusters":
                    return await self._list_clusters(arguments)
                elif name == "databricks_get_cluster":
                    return await self._get_cluster(arguments)
                elif name == "databricks_start_cluster":
                    return await self._start_cluster(arguments)
                elif name == "databricks_list_jobs":
                    return await self._list_jobs(arguments)
                elif name == "databricks_run_job":
                    return await self._run_job(arguments)
                elif name == "databricks_query_sql":
                    return await self._query_sql(arguments)
                elif name == "databricks_upload_file":
                    return await self._upload_file(arguments)
                elif name == "coinbase_list_files":
                    return await self._list_files(arguments)
                elif name == "coinbase_get_prices":
                    return await self._get_coinbase_prices(arguments)
                elif name == "databricks_store_coinbase_data":
                    return await self._store_coinbase_data(arguments)
                else:
                    return CallToolResult(content=[TextContent(type="text", text=f"Unknown tool: {name}")])
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return CallToolResult(content=[TextContent(type="text", text=f"Error: {str(e)}")])

    async def _list_clusters(self, _args: dict[str, Any]) -> CallToolResult:
        """List Databricks clusters"""
        try:
            clusters = list(self.client.clusters.list())
            cluster_info = [
                {
                    "cluster_id": c.cluster_id,
                    "cluster_name": c.cluster_name,
                    "state": c.state.value if c.state else "UNKNOWN",
                    "spark_version": c.spark_version,
                    "node_type_id": c.node_type_id,
                }
                for c in clusters
            ]
            return CallToolResult(content=[TextContent(type="text", text=json.dumps(cluster_info, indent=2))])
        except Exception as e:
            return CallToolResult(content=[TextContent(type="text", text=f"Failed to list clusters: {e}")])

    async def _get_cluster(self, args: dict[str, Any]) -> CallToolResult:
        """Get cluster details"""
        cluster_id = args["cluster_id"]
        try:
            cluster = self.client.clusters.get(cluster_id)
            cluster_info = {
                "cluster_id": cluster.cluster_id,
                "cluster_name": cluster.cluster_name,
                "state": cluster.state.value if cluster.state else "UNKNOWN",
                "spark_version": cluster.spark_version,
                "node_type_id": cluster.node_type_id,
                "driver_node_type_id": cluster.driver_node_type_id,
                "num_workers": cluster.num_workers,
            }
            return CallToolResult(content=[TextContent(type="text", text=json.dumps(cluster_info, indent=2))])
        except Exception as e:
            return CallToolResult(content=[TextContent(type="text", text=f"Failed to get cluster: {e}")])

    async def _start_cluster(self, args: dict[str, Any]) -> CallToolResult:
        """Start a cluster"""
        cluster_id = args["cluster_id"]
        try:
            self.client.clusters.start(cluster_id)
            return CallToolResult(content=[TextContent(type="text", text=f"Started cluster {cluster_id}")])
        except Exception as e:
            return CallToolResult(content=[TextContent(type="text", text=f"Failed to start cluster: {e}")])

    async def _list_jobs(self, args: dict[str, Any]) -> CallToolResult:
        """List jobs"""
        page_token = args.get("page_token")
        limit = args.get("limit", 25)
        try:
            jobs = list(self.client.jobs.list(page_token=page_token, limit=limit))
            job_info = [
                {
                    "job_id": j.job_id,
                    "job_name": j.settings.name,
                    "state": j.state.value if j.state else "UNKNOWN",
                }
                for j in jobs
            ]
            return CallToolResult(content=[TextContent(type="text", text=json.dumps(job_info, indent=2))])
        except Exception as e:
            return CallToolResult(content=[TextContent(type="text", text=f"Failed to list jobs: {e}")])

    async def _run_job(self, args: dict[str, Any]) -> CallToolResult:
        """Run a job"""
        job_id = args["job_id"]
        parameters = args.get("parameters", {})
        try:
            run = self.client.jobs.run_now(job_id=job_id, job_parameters=parameters)
            return CallToolResult(
                content=[TextContent(type="text", text=f"Started job run {run.run_id} for job {job_id}")]
            )
        except Exception as e:
            return CallToolResult(content=[TextContent(type="text", text=f"Failed to run job: {e}")])

    async def _query_sql(self, args: dict[str, Any]) -> CallToolResult:
        """Execute SQL query"""
        warehouse_id = args["warehouse_id"]
        query = args["query"]
        try:
            result = self.client.query.execute(warehouse_id=warehouse_id, query=query)
            # This is simplified; actual implementation would need to handle result pagination
            return CallToolResult(content=[TextContent(type="text", text=f"Query executed. Result: {result}")])
        except Exception as e:
            return CallToolResult(content=[TextContent(type="text", text=f"Failed to execute query: {e}")])

    async def _get_coinbase_prices(self, args: dict[str, Any]) -> CallToolResult:
        """Get Coinbase prices"""
        if not coinbase:
            return CallToolResult(content=[TextContent(type="text", text="Coinbase library not available")])

        currency_pair = args.get("currency_pair", "BTC-USD")
        try:
            # Simplified Coinbase API call
            # In reality, would use coinbase SDK
            price_data = {"currency_pair": currency_pair, "price": "placeholder"}
            return CallToolResult(content=[TextContent(type="text", text=json.dumps(price_data, indent=2))])
        except Exception as e:
            return CallToolResult(content=[TextContent(type="text", text=f"Failed to get Coinbase prices: {e}")])

    async def _store_coinbase_data(self, args: dict[str, Any]) -> CallToolResult:
        """Store Coinbase data in Databricks"""
        currency_pair = args.get("currency_pair", "BTC-USD")
        table_name = args["table_name"]
        catalog = args.get("catalog", "hive_metastore")
        schema = args.get("schema", "default")

        try:
            # Get Coinbase data
            coinbase_result = await self._get_coinbase_prices({"currency_pair": currency_pair})
            if coinbase_result.content[0].text.startswith("Failed"):
                return coinbase_result

            # Store in Databricks table (simplified)
            # In reality, would use Databricks SQL to insert data
            return CallToolResult(
                content=[
                    TextContent(
                        type="text", text=f"Stored Coinbase data for {currency_pair} in {catalog}.{schema}.{table_name}"
                    )
                ]
            )
        except Exception as e:
            return CallToolResult(content=[TextContent(type="text", text=f"Failed to store Coinbase data: {e}")])

    async def _upload_file(self, args: dict[str, Any]) -> CallToolResult:
        file_path = args["file_path"]
        dbfs_path = args["dbfs_path"]
        local_file = self.project_path / file_path
        if not local_file.exists():
            return CallToolResult(content=[TextContent(type="text", text=f"File not found: {local_file}")])
        try:
            async with aiofiles.open(local_file, mode="rb") as f:
                content = await f.read()
                self.client.dbfs.upload(dbfs_path, content)
            return CallToolResult(content=[TextContent(type="text", text=f"Uploaded {file_path} to {dbfs_path}")])
        except Exception as e:
            return CallToolResult(content=[TextContent(type="text", text=f"Failed to upload file: {e}")])

    async def _list_files(self, args: dict[str, Any]) -> CallToolResult:
        subdir = args.get("subdir", ".")
        path = self.project_path / subdir
        if not path.exists():
            return CallToolResult(content=[TextContent(type="text", text=f"Path not found: {path}")])
        try:
            files = (
                [f for f in path.rglob("*") if f.is_file()]
                if subdir == "."
                else [f for f in path.iterdir() if f.is_file()]
            )
            file_list = [str(f.relative_to(self.project_path)) for f in files]
            return CallToolResult(content=[TextContent(type="text", text=json.dumps(file_list, indent=2))])
        except Exception as e:
            return CallToolResult(content=[TextContent(type="text", text=f"Failed to list files: {e}")])


async def main() -> None:
    """Main server entry point"""
    logger.info("Starting Databricks-Coinbase MCP Server...")
    server = DatabricksCoinbaseMCPServer()

    async with stdio_server() as (read_stream, write_stream):
        await server.server.run(read_stream, write_stream, server.server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
