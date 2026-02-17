"""
MCP Tool Registry - Manages tool discovery, registration, and invocation.

This module provides a centralized registry for MCP (Model Context Protocol) tools,
supporting async operations, health checks, and configuration-based server management.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timezone
from enum import Enum, StrEnum
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class ServerStatus(StrEnum):
    """Status of an MCP server."""

    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


@dataclass
class ToolDefinition:
    """Definition of an MCP tool."""

    name: str
    description: str
    parameters: dict[str, Any]
    server_name: str
    server_url: str
    tags: list[str] = field(default_factory=list)
    version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "server_name": self.server_name,
            "tags": self.tags,
            "version": self.version,
        }


@dataclass
class ServerConfig:
    """Configuration for an MCP server."""

    name: str
    url: str
    enabled: bool = True
    description: str = ""
    health_endpoint: str = "/health"
    health_check_interval: int = 30
    timeout: float = 30.0
    retry_attempts: int = 3
    retry_delay: float = 1.0


@dataclass
class ServerInfo:
    """Runtime information about an MCP server."""

    config: ServerConfig
    status: ServerStatus = ServerStatus.UNKNOWN
    last_health_check: datetime | None = None
    tools: list[ToolDefinition] = field(default_factory=list)
    error_message: str | None = None


@dataclass
class ToolCallResult:
    """Result of a tool invocation."""

    success: bool
    tool_name: str
    result: Any = None
    error: str | None = None
    execution_time_ms: int = 0
    server_name: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "success": self.success,
            "tool_name": self.tool_name,
            "result": self.result,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "server_name": self.server_name,
        }


class ToolRegistry:
    """
    Central registry for MCP tools.

    Manages tool discovery, registration, health monitoring, and invocation
    across multiple MCP servers.

    Example:
        ```python
        registry = ToolRegistry()
        await registry.load_config("mcp-setup/mcp_config.json")
        await registry.discover_all_tools()

        # List available tools
        for tool in registry.list_tools():
            print(f"{tool['name']}: {tool['description']}")

        # Call a tool
        result = await registry.call_tool("rag_query", {"query": "What is GRID?"})
        ```
    """

    def __init__(
        self,
        timeout: float = 30.0,
        max_connections: int = 10,
    ):
        """
        Initialize the tool registry.

        Args:
            timeout: Default timeout for HTTP requests in seconds.
            max_connections: Maximum number of concurrent connections per server.
        """
        self._tools: dict[str, ToolDefinition] = {}
        self._servers: dict[str, ServerInfo] = {}
        self._client: httpx.AsyncClient | None = None
        self._timeout = timeout
        self._max_connections = max_connections
        self._health_check_task: asyncio.Task | None = None
        self._callbacks: dict[str, list[Callable]] = {
            "tool_registered": [],
            "tool_called": [],
            "server_status_changed": [],
        }

    async def __aenter__(self) -> ToolRegistry:
        """Async context manager entry."""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure HTTP client is initialized."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout),
                limits=httpx.Limits(max_connections=self._max_connections),
            )
        return self._client

    async def close(self) -> None:
        """Close the registry and cleanup resources."""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        if self._client:
            await self._client.aclose()
            self._client = None

    def load_config_sync(self, config_path: str | Path) -> None:
        """
        Load server configuration from a JSON file (synchronous).

        Args:
            config_path: Path to the MCP configuration file.
        """
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path) as f:
            config_data = json.load(f)

        self._parse_config(config_data)

    async def load_config(self, config_path: str | Path) -> None:
        """
        Load server configuration from a JSON file.

        Args:
            config_path: Path to the MCP configuration file.
        """
        import aiofiles
        config_path = Path(config_path)
        if not await asyncio.to_thread(config_path.exists):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        async with aiofiles.open(config_path) as f:
            content = await f.read()
            config_data = json.loads(content)

        self._parse_config(config_data)

    def _parse_config(self, config_data: dict[str, Any]) -> None:
        """Parse configuration data and register servers."""
        defaults = config_data.get("defaults", {})
        default_timeout = defaults.get("timeout_seconds", 60.0)
        default_retry = defaults.get("retry_attempts", 3)
        default_retry_delay = defaults.get("retry_delay_seconds", 2.0)

        for server_data in config_data.get("servers", []):
            health_check = server_data.get("health_check", {})

            config = ServerConfig(
                name=server_data["name"],
                url=f"http://localhost:{server_data.get('port', 8000)}",
                enabled=server_data.get("enabled", True),
                description=server_data.get("description", ""),
                health_endpoint=health_check.get("endpoint", "/health"),
                health_check_interval=health_check.get("interval_seconds", 30),
                timeout=server_data.get("timeout", default_timeout),
                retry_attempts=server_data.get("retry_attempts", default_retry),
                retry_delay=server_data.get("retry_delay", default_retry_delay),
            )

            self.register_server(config)

    def register_server(self, config: ServerConfig) -> None:
        """
        Register an MCP server.

        Args:
            config: Server configuration.
        """
        self._servers[config.name] = ServerInfo(config=config)
        logger.info(f"Registered server: {config.name} at {config.url}")

    def add_server(self, name: str, url: str, **kwargs: Any) -> None:
        """
        Add a server with minimal configuration.

        Args:
            name: Server name.
            url: Server URL.
            **kwargs: Additional ServerConfig parameters.
        """
        config = ServerConfig(name=name, url=url, **kwargs)
        self.register_server(config)

    async def check_server_health(self, server_name: str) -> ServerStatus:
        """
        Check the health of a specific server.

        Args:
            server_name: Name of the server to check.

        Returns:
            Current server status.
        """
        if server_name not in self._servers:
            return ServerStatus.UNKNOWN

        server = self._servers[server_name]
        client = await self._ensure_client()

        try:
            url = f"{server.config.url}{server.config.health_endpoint}"
            response = await client.get(url, timeout=5.0)

            old_status = server.status
            if response.status_code == 200:
                server.status = ServerStatus.HEALTHY
                server.error_message = None
            else:
                server.status = ServerStatus.UNHEALTHY
                server.error_message = f"Health check returned {response.status_code}"

            server.last_health_check = datetime.now(UTC)

            if old_status != server.status:
                await self._emit("server_status_changed", server_name, server.status)

            return server.status

        except httpx.ConnectError:
            server.status = ServerStatus.OFFLINE
            server.error_message = "Connection refused"
            server.last_health_check = datetime.now(UTC)
            return ServerStatus.OFFLINE

        except Exception as e:
            server.status = ServerStatus.UNHEALTHY
            server.error_message = str(e)
            server.last_health_check = datetime.now(UTC)
            logger.warning(f"Health check failed for {server_name}: {e}")
            return ServerStatus.UNHEALTHY

    async def check_all_servers_health(self) -> dict[str, ServerStatus]:
        """
        Check health of all registered servers.

        Returns:
            Dictionary mapping server names to their status.
        """
        tasks = [self.check_server_health(name) for name, server in self._servers.items() if server.config.enabled]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            name: (results[i] if not isinstance(results[i], Exception) else ServerStatus.UNHEALTHY)
            for i, name in enumerate(n for n, s in self._servers.items() if s.config.enabled)
        }

    async def discover_tools(self, server_name: str) -> list[ToolDefinition]:
        """
        Discover tools from a specific server.

        Args:
            server_name: Name of the server.

        Returns:
            List of discovered tools.
        """
        if server_name not in self._servers:
            raise ValueError(f"Unknown server: {server_name}")

        server = self._servers[server_name]
        if not server.config.enabled:
            logger.info(f"Skipping disabled server: {server_name}")
            return []

        client = await self._ensure_client()
        discovered = []

        try:
            # Try MCP standard endpoint first
            response = await client.post(
                f"{server.config.url}/list_tools",
                timeout=server.config.timeout,
            )
            response.raise_for_status()

            tools_data = response.json()

            # Handle both list and dict responses
            if isinstance(tools_data, dict):
                tools_data = tools_data.get("tools", [])

            for tool_data in tools_data:
                tool = ToolDefinition(
                    name=tool_data["name"],
                    description=tool_data.get("description", ""),
                    parameters=tool_data.get("inputSchema", tool_data.get("parameters", {})),
                    server_name=server_name,
                    server_url=server.config.url,
                    tags=tool_data.get("tags", []),
                    version=tool_data.get("version", "1.0.0"),
                )
                discovered.append(tool)
                self._tools[tool.name] = tool
                await self._emit("tool_registered", tool)

            server.tools = discovered
            logger.info(f"Discovered {len(discovered)} tools from {server_name}")
            return discovered

        except httpx.ConnectError:
            logger.warning(f"Cannot connect to server {server_name} at {server.config.url}")
            return []

        except Exception as e:
            logger.error(f"Failed to discover tools from {server_name}: {e}")
            return []

    async def discover_all_tools(self) -> dict[str, list[ToolDefinition]]:
        """
        Discover tools from all registered servers.

        Returns:
            Dictionary mapping server names to their tools.
        """
        results = {}
        for server_name in self._servers:
            results[server_name] = await self.discover_tools(server_name)
        return results

    def get_tool(self, name: str) -> ToolDefinition | None:
        """
        Get a tool by name.

        Args:
            name: Tool name.

        Returns:
            Tool definition or None if not found.
        """
        return self._tools.get(name)

    def list_tools(
        self,
        server_name: str | None = None,
        tags: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        List all registered tools.

        Args:
            server_name: Optional filter by server name.
            tags: Optional filter by tags.

        Returns:
            List of tool definitions as dictionaries.
        """
        tools = list(self._tools.values())

        if server_name:
            tools = [t for t in tools if t.server_name == server_name]

        if tags:
            tools = [t for t in tools if any(tag in t.tags for tag in tags)]

        return [t.to_dict() for t in tools]

    def list_servers(self) -> list[dict[str, Any]]:
        """
        List all registered servers with their status.

        Returns:
            List of server information.
        """
        return [
            {
                "name": server.config.name,
                "url": server.config.url,
                "enabled": server.config.enabled,
                "status": server.status.value,
                "description": server.config.description,
                "tool_count": len(server.tools),
                "last_health_check": (server.last_health_check.isoformat() if server.last_health_check else None),
                "error": server.error_message,
            }
            for server in self._servers.values()
        ]

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> ToolCallResult:
        """
        Call a tool with the given arguments.

        Args:
            name: Tool name.
            arguments: Tool arguments.
            timeout: Optional timeout override.

        Returns:
            Tool call result.
        """
        start_time = asyncio.get_event_loop().time()

        if name not in self._tools:
            return ToolCallResult(
                success=False,
                tool_name=name,
                error=f"Tool not found: {name}",
            )

        tool = self._tools[name]
        server = self._servers.get(tool.server_name)

        if not server:
            return ToolCallResult(
                success=False,
                tool_name=name,
                error=f"Server not found: {tool.server_name}",
            )

        client = await self._ensure_client()
        request_timeout = timeout or server.config.timeout

        # Retry logic
        last_error: Exception | None = None
        for attempt in range(server.config.retry_attempts):
            try:
                response = await client.post(
                    f"{tool.server_url}/call_tool",
                    json={"name": name, "arguments": arguments or {}},
                    timeout=request_timeout,
                )
                response.raise_for_status()

                result_data = response.json()
                execution_time = int((asyncio.get_event_loop().time() - start_time) * 1000)

                result = ToolCallResult(
                    success=True,
                    tool_name=name,
                    result=result_data.get("content", result_data),
                    execution_time_ms=execution_time,
                    server_name=tool.server_name,
                )

                await self._emit("tool_called", result)
                return result

            except httpx.TimeoutException:
                last_error = TimeoutError(f"Tool call timed out after {request_timeout}s")

            except httpx.HTTPStatusError as e:
                last_error = e
                # Don't retry on 4xx errors
                if 400 <= e.response.status_code < 500:
                    break

            except Exception as e:
                last_error = e

            if attempt < server.config.retry_attempts - 1:
                await asyncio.sleep(server.config.retry_delay)

        execution_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
        return ToolCallResult(
            success=False,
            tool_name=name,
            error=str(last_error),
            execution_time_ms=execution_time,
            server_name=tool.server_name,
        )

    async def call_tool_on_server(
        self,
        server_name: str,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
    ) -> ToolCallResult:
        """
        Call a tool on a specific server.

        Useful when the same tool name exists on multiple servers.

        Args:
            server_name: Server to call.
            tool_name: Tool name.
            arguments: Tool arguments.

        Returns:
            Tool call result.
        """
        # Find tool with matching server
        for tool in self._tools.values():
            if tool.name == tool_name and tool.server_name == server_name:
                return await self.call_tool(tool_name, arguments)

        return ToolCallResult(
            success=False,
            tool_name=tool_name,
            error=f"Tool {tool_name} not found on server {server_name}",
            server_name=server_name,
        )

    def on(self, event: str, callback: Callable) -> None:
        """
        Register an event callback.

        Events:
            - tool_registered: (tool: ToolDefinition)
            - tool_called: (result: ToolCallResult)
            - server_status_changed: (server_name: str, status: ServerStatus)

        Args:
            event: Event name.
            callback: Callback function.
        """
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    async def _emit(self, event: str, *args: Any) -> None:
        """Emit an event to all registered callbacks."""
        for callback in self._callbacks.get(event, []):
            try:
                result = callback(*args)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Error in event callback for {event}: {e}")

    def start_health_monitoring(self, interval: int | None = None) -> None:
        """
        Start background health monitoring for all servers.

        Args:
            interval: Check interval in seconds (default: use server config).
        """
        if self._health_check_task and not self._health_check_task.done():
            return

        async def monitor() -> None:
            while True:
                await self.check_all_servers_health()
                await asyncio.sleep(interval or 30)

        self._health_check_task = asyncio.create_task(monitor())

    def stop_health_monitoring(self) -> None:
        """Stop background health monitoring."""
        if self._health_check_task:
            self._health_check_task.cancel()
            self._health_check_task = None


# Global registry instance
_global_registry: ToolRegistry | None = None


def get_registry() -> ToolRegistry:
    """Get or create the global tool registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def set_registry(registry: ToolRegistry) -> None:
    """Set the global tool registry instance."""
    global _global_registry
    _global_registry = registry


async def quick_setup(config_path: str | Path | None = None) -> ToolRegistry:
    """
    Quick setup for the tool registry.

    Loads configuration and discovers all tools.

    Args:
        config_path: Path to MCP config file. If None, uses default location.

    Returns:
        Configured registry with discovered tools.
    """
    registry = get_registry()

    if config_path is None:
        # Try common locations
        for path in [
            Path("mcp-setup/mcp_config.json"),
            Path("config/mcp_config.json"),
            Path.home() / ".codeium/windsurf/mcp/mcp_config.json",
        ]:
            if await asyncio.to_thread(path.exists):
                config_path = path
                break

    if config_path:
        await registry.load_config(config_path)

    await registry.discover_all_tools()
    return registry


# Example usage and testing
if __name__ == "__main__":

    async def main() -> None:
        """Example usage of the tool registry."""
        registry = ToolRegistry()

        # Add servers manually
        registry.add_server("grid-rag", "http://localhost:8000")
        registry.add_server("grid-tools", "http://localhost:8001")

        # Or load from config
        # await registry.load_config("mcp-setup/mcp_config.json")

        # Check health
        health = await registry.check_all_servers_health()
        print("Server health:")
        for name, status in health.items():
            print(f"  {name}: {status.value}")

        # Discover tools
        await registry.discover_all_tools()

        # List tools
        print("\nAvailable tools:")
        for tool in registry.list_tools():
            print(f"  - {tool['name']}: {tool['description']}")

        # Example tool call (uncomment if servers are running)
        # result = await registry.call_tool("rag_query", {"query": "What is GRID?"})
        # print(f"\nTool result: {result.to_dict()}")

        await registry.close()

    asyncio.run(main())
