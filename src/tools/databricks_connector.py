"""
Databricks Connector Implementation

Implementation of Databricks connection using the generalized GRID connector patterns.
"""

import os
import time
from typing import Any

from databricks.sdk import WorkspaceClient

from .data_connectors import (
    BaseConnectorConfig,
    BaseDataClient,
    ConfigurationError,
    ConnectionError,
    QueryExecutionError,
    QueryInterface,
    QueryResult,
)


class DatabricksConfig(BaseConnectorConfig):
    """Configuration for Databricks connector."""

    def __init__(
        self,
        host: str,
        token: str,
        cluster_id: str | None = None,
        warehouse_id: str | None = None,
        account_id: str | None = None,
    ):
        super().__init__(
            host=host, token=token, cluster_id=cluster_id, warehouse_id=warehouse_id, account_id=account_id
        )

    @classmethod
    def from_env(cls, prefix: str = "DATABRICKS") -> "DatabricksConfig":
        """Load configuration from environment variables."""
        return cls(
            host=os.getenv(f"{prefix}_HOST"),
            token=os.getenv(f"{prefix}_TOKEN"),
            cluster_id=os.getenv(f"{prefix}_CLUSTER_ID"),
            warehouse_id=os.getenv(f"{prefix}_WAREHOUSE_ID"),
            account_id=os.getenv(f"{prefix}_ACCOUNT_ID"),
        )

    def validate(self) -> bool:
        """Validate required configuration fields."""
        return all([self.get("host"), self.get("token")])


class DatabricksClient(BaseDataClient):
    """Databricks client implementation using GRID patterns."""

    def _establish_connection(self) -> None:
        """Establish Databricks connection."""
        try:
            self._client = WorkspaceClient(host=self.config.get("host"), token=self.config.get("token"))
        except Exception as e:
            raise ConnectionError(f"Databricks connection failed: {e}") from e

    def _close_connection(self) -> None:
        """Close Databricks connection."""
        self._client = None

    def _perform_health_check(self) -> dict[str, Any]:
        """Perform Databricks health check."""
        try:
            # Test by listing clusters
            clusters = list(self._client.clusters.list())
            warehouses = list(self._client.warehouses.list())

            return {"clusters": len(clusters), "warehouses": len(warehouses), "workspace": self.config.get("host")}
        except Exception as e:
            raise ConnectionError(f"Health check failed: {e}") from e

    def list_clusters(self) -> list[dict[str, Any]]:
        """List available clusters."""
        if self._status.value != "connected":
            raise ConnectionError("Not connected to Databricks")

        try:
            clusters = list(self._client.clusters.list())
            return [
                {
                    "id": cluster.cluster_id,
                    "name": cluster.cluster_name,
                    "state": cluster.state,
                    "driver_type": cluster.driver_node_type_id,
                }
                for cluster in clusters
            ]
        except Exception as e:
            raise QueryExecutionError(f"Failed to list clusters: {e}") from e

    def list_warehouses(self) -> list[dict[str, Any]]:
        """List available SQL warehouses."""
        if self._status.value != "connected":
            raise ConnectionError("Not connected to Databricks")

        try:
            warehouses = list(self._client.warehouses.list())
            return [
                {
                    "id": warehouse.id,
                    "name": warehouse.name,
                    "type": warehouse.warehouse_type,
                    "state": warehouse.state,
                    "size": warehouse.cluster_size,
                }
                for warehouse in warehouses
            ]
        except Exception as e:
            raise QueryExecutionError(f"Failed to list warehouses: {e}") from e


class DatabricksQuery(QueryInterface):
    """Databricks query implementation using GRID patterns."""

    def _execute_with_client(self, query: str, parameters: dict[str, Any]) -> QueryResult:
        """Execute SQL query on Databricks."""
        if self.client._status.value != "connected":
            raise ConnectionError("Not connected to Databricks")

        start_time = time.time()

        try:
            # Format query with parameters if provided
            formatted_query = self._format_query(query, parameters)

            # Execute query using SQL warehouse
            warehouse_id = self.client.config.get("warehouse_id")
            if not warehouse_id:
                raise ConfigurationError("No warehouse ID configured")

            result = self.client._client.sql.execute(statement=formatted_query, warehouse_id=warehouse_id)

            execution_time = time.time() - start_time

            # Convert result to standardized format
            data = result.result.as_dict() if result.result else []

            return QueryResult(
                status="success",
                data=data,
                rows_affected=len(data),
                execution_time=execution_time,
                metadata={"warehouse_id": warehouse_id, "statement_id": result.statement_id},
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return QueryResult(
                status="error", data=[], rows_affected=0, execution_time=execution_time, error_message=str(e)
            )

    def _format_query(self, query: str, parameters: dict[str, Any]) -> str:
        """Format query with parameters (simple implementation)."""
        if not parameters:
            return query

        # Simple parameter substitution
        formatted = query
        for key, value in parameters.items():
            if isinstance(value, str):
                formatted = formatted.replace(f":{key}", f"'{value}'")
            else:
                formatted = formatted.replace(f":{key}", str(value))

        return formatted


def create_databricks_connector(prefix: str = "DATABRICKS") -> tuple[DatabricksClient, DatabricksQuery]:
    """Factory function to create Databricks connector and query interface."""
    config = DatabricksConfig.from_env(prefix)
    client = DatabricksClient(config)
    query_interface = DatabricksQuery(client)

    return client, query_interface


# Convenience functions for common operations
def test_databricks_connection(prefix: str = "DATABRICKS") -> dict[str, Any]:
    """Test Databricks connection using environment variables."""
    try:
        client, _ = create_databricks_connector(prefix)
        return client.test_connection()
    except Exception as e:
        return {"status": "error", "message": str(e)}


def execute_databricks_query(
    query: str, parameters: dict[str, Any] | None = None, prefix: str = "DATABRICKS"
) -> QueryResult:
    """Execute query on Databricks using environment variables."""
    client, query_interface = create_databricks_connector(prefix)

    try:
        client.connect()
        return query_interface.execute_query(query, **(parameters or {}))
    finally:
        client.disconnect()
