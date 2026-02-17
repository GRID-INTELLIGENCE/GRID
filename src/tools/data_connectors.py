"""
GRID Data Connectors - Generalized Connection Abstractions

This module provides generalized connection patterns extracted from Coinbase's
Databricks integration, making them available for all GRID workspaces.
"""

import hashlib
import json
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class ConnectorStatus(StrEnum):
    """Connection status enumeration."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class QueryResult:
    """Standardized query result format."""

    status: str
    data: list[dict[str, Any]]
    rows_affected: int
    execution_time: float
    error_message: str | None = None
    metadata: dict[str, Any] | None = None


class ConnectorError(Exception):
    """Base exception for all connector errors."""

    def __init__(self, message: str, connector_type: str | None = None, error_code: str | None = None):
        self.message = message
        self.connector_type = connector_type
        self.error_code = error_code
        super().__init__(message)


class ConfigurationError(ConnectorError):
    def __init__(self, message: str, connector_type: str | None = None):
        super().__init__(message, connector_type, "CONFIG_ERROR")


class ConnectionError(ConnectorError):
    def __init__(self, message: str, connector_type: str | None = None):
        super().__init__(message, connector_type, "CONNECTION_ERROR")


class QueryExecutionError(ConnectorError):
    def __init__(self, message: str, connector_type: str | None = None, query: str | None = None):
        super().__init__(message, connector_type, "QUERY_ERROR")
        self.query = query


class BaseConnectorConfig(ABC):
    """Generic configuration pattern for all data connectors."""

    def __init__(self, **config_fields):
        self._fields = config_fields

    @classmethod
    @abstractmethod
    def from_env(cls, prefix: str) -> "BaseConnectorConfig":
        """Load configuration from environment variables with prefix."""
        pass

    @abstractmethod
    def validate(self) -> bool:
        """Validate all required fields are present."""
        pass

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._fields.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self._fields[key] = value


class BaseDataClient(ABC):
    """Generic client pattern for all data connectors."""

    def __init__(self, config: BaseConnectorConfig):
        self.config = config
        self._client = None
        self._status = ConnectorStatus.DISCONNECTED
        self._connection_pool = None

    def connect(self) -> None:
        """Establish connection to data source."""
        if not self.config.validate():
            raise ConfigurationError("Invalid configuration")

        self._status = ConnectorStatus.CONNECTING
        try:
            self._establish_connection()
            self._status = ConnectorStatus.CONNECTED
            logger.info(f"Connected to {self.__class__.__name__}")
        except Exception as e:
            self._status = ConnectorStatus.ERROR
            raise ConnectionError(f"Connection failed: {e}") from e

    def disconnect(self) -> None:
        """Close connection to data source."""
        if self._client:
            self._close_connection()
            self._client = None
            self._status = ConnectorStatus.DISCONNECTED
            logger.info(f"Disconnected from {self.__class__.__name__}")

    def test_connection(self) -> dict[str, Any]:
        """Test connection health and return status."""
        try:
            if self._status != ConnectorStatus.CONNECTED:
                self.connect()

            result = self._perform_health_check()
            return {"status": "connected", **result}
        except Exception as e:
            self._status = ConnectorStatus.ERROR
            return {"status": "error", "message": str(e)}

    @property
    def status(self) -> ConnectorStatus:
        """Get current connection status."""
        return self._status

    @abstractmethod
    def _establish_connection(self) -> None:
        """Override in subclasses to implement specific connection logic."""
        pass

    @abstractmethod
    def _close_connection(self) -> None:
        """Override in subclasses to implement specific cleanup logic."""
        pass

    @abstractmethod
    def _perform_health_check(self) -> dict[str, Any]:
        """Override in subclasses to implement specific health check."""
        pass


class QueryInterface:
    """Generic query interface for all data connectors."""

    def __init__(self, client: BaseDataClient, cache_size: int = 100):
        self.client = client
        self._query_cache: dict[str, QueryResult] = {}
        self._cache_size = cache_size
        self._query_stats: defaultdict[str, int] = defaultdict(int)

    def execute_query(self, query: str, **parameters) -> QueryResult:
        """Execute query with parameters and return structured result."""
        query_hash = self._hash_query(query, parameters)

        # Check cache
        if query_hash in self._query_cache:
            self._query_stats["cache_hits"] += 1
            return self._query_cache[query_hash]

        # Execute query
        try:
            result = self._execute_with_client(query, parameters)
            self._query_stats["executions"] += 1

            # Cache result if appropriate
            if self._should_cache(query):
                self._add_to_cache(query_hash, result)

            return result
        except Exception as e:
            self._query_stats["errors"] += 1
            raise QueryExecutionError(f"Query failed: {e}", query=query) from e

    def get_stats(self) -> dict[str, int]:
        """Get query execution statistics."""
        return dict(self._query_stats)

    def clear_cache(self) -> None:
        """Clear query cache."""
        self._query_cache.clear()
        logger.info("Query cache cleared")

    def _hash_query(self, query: str, parameters: dict) -> str:
        """Create hash for query caching."""
        query_str = f"{query}:{json.dumps(parameters, sort_keys=True)}"
        return hashlib.md5(query_str.encode()).hexdigest()

    def _should_cache(self, query: str) -> bool:
        """Determine if query result should be cached."""
        return query.strip().upper().startswith("SELECT")

    def _add_to_cache(self, query_hash: str, result: QueryResult) -> None:
        """Add result to cache with size limit."""
        if len(self._query_cache) >= self._cache_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self._query_cache))
            del self._query_cache[oldest_key]

        self._query_cache[query_hash] = result

    @abstractmethod
    def _execute_with_client(self, query: str, parameters: dict) -> QueryResult:
        """Override in subclasses for specific query execution."""
        pass


class ConnectorRegistry:
    """Registry for managing data connectors."""

    def __init__(self):
        self._connectors: dict[str, BaseDataClient] = {}
        self._configs: dict[str, BaseConnectorConfig] = {}

    def register_connector(self, name: str, client: BaseDataClient) -> None:
        """Register a data connector."""
        self._connectors[name] = client
        self._configs[name] = client.config
        logger.info(f"Registered connector: {name}")

    def get_connector(self, name: str) -> BaseDataClient | None:
        """Get a registered connector."""
        return self._connectors.get(name)

    def list_connectors(self) -> list[str]:
        """List all registered connectors."""
        return list(self._connectors.keys())

    def connect_all(self) -> dict[str, bool]:
        """Connect all registered connectors."""
        results = {}
        for name, client in self._connectors.items():
            try:
                client.connect()
                results[name] = True
            except Exception as e:
                logger.error(f"Failed to connect {name}: {e}")
                results[name] = False
        return results

    def test_all(self) -> dict[str, dict[str, Any]]:
        """Test all registered connectors."""
        results = {}
        for name, client in self._connectors.items():
            results[name] = client.test_connection()
        return results

    def disconnect_all(self) -> None:
        """Disconnect all registered connectors."""
        for name, client in self._connectors.items():
            try:
                client.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting {name}: {e}")


class ConnectorHandler:
    """Generic handler for integrating connectors with AgenticSystem."""

    def __init__(self, connector: BaseDataClient, query_interface: QueryInterface):
        self.connector = connector
        self.query_interface = query_interface

    def create_query_handler(self, query_template: str) -> Callable:
        """Create a handler function for AgenticSystem."""

        def handler(case_id: str, reference: dict[str, Any], agent_role: str) -> dict[str, Any]:
            try:
                # Extract parameters from reference
                parameters = self._extract_parameters(reference)

                # Format query with parameters
                query = self._format_query_template(query_template, parameters)

                # Execute query
                result = self.query_interface.execute_query(query, **parameters)

                return {
                    "case_id": case_id,
                    "agent_role": agent_role,
                    "status": "success",
                    "result": {
                        "status": result.status,
                        "data": result.data,
                        "rows_affected": result.rows_affected,
                        "execution_time": result.execution_time,
                        "metadata": result.metadata,
                    },
                }
            except Exception as e:
                logger.error(f"Handler error for case {case_id}: {e}")
                return {"case_id": case_id, "agent_role": agent_role, "status": "error", "message": str(e)}

        return handler

    def _extract_parameters(self, reference: dict[str, Any]) -> dict[str, Any]:
        """Extract parameters from reference data."""
        return reference.get("parameters", {})

    def _format_query_template(self, template: str, parameters: dict[str, Any]) -> str:
        """Format query template with parameters."""
        try:
            return template.format(**parameters)
        except KeyError as e:
            raise QueryExecutionError(f"Missing parameter: {e}") from e


# Global connector registry
connector_registry = ConnectorRegistry()


def get_connector(name: str) -> BaseDataClient | None:
    """Get connector from global registry."""
    return connector_registry.get_connector(name)


def register_connector(name: str, client: BaseDataClient) -> None:
    """Register connector in global registry."""
    connector_registry.register_connector(name, client)
