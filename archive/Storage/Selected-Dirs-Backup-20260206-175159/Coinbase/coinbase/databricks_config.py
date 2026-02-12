"""Databricks configuration and client management."""

import os
from dataclasses import dataclass
from typing import Any


@dataclass
class DatabricksConfig:
    """Configuration for Databricks connection."""

    host: str | None = None
    token: str | None = None
    cluster_id: str | None = None
    warehouse_id: str | None = None
    account_id: str | None = None

    @classmethod
    def from_env(cls) -> "DatabricksConfig":
        """Load configuration from environment variables.

        Environment variables:
        - DATABRICKS_HOST: Databricks workspace URL
        - DATABRICKS_TOKEN: Personal access token
        - DATABRICKS_CLUSTER_ID: Cluster ID (optional)
        - DATABRICKS_WAREHOUSE_ID: SQL warehouse ID (optional)
        - DATABRICKS_ACCOUNT_ID: Account ID (optional)
        """
        return cls(
            host=os.getenv("DATABRICKS_HOST"),
            token=os.getenv("DATABRICKS_TOKEN"),
            cluster_id=os.getenv("DATABRICKS_CLUSTER_ID"),
            warehouse_id=os.getenv("DATABRICKS_WAREHOUSE_ID"),
            account_id=os.getenv("DATABRICKS_ACCOUNT_ID"),
        )

    def validate(self) -> bool:
        """Validate required configuration fields."""
        return bool(self.host and self.token)

    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "host": self.host,
            "token": "***REDACTED***" if self.token else None,
            "cluster_id": self.cluster_id,
            "warehouse_id": self.warehouse_id,
            "account_id": self.account_id,
        }


class DatabricksClient:
    """Wrapper for Databricks SDK client."""

    def __init__(self, config: DatabricksConfig | None = None):
        """Initialize Databricks client.

        Args:
            config: Databricks configuration. If None, loads from environment.
        """
        self.config = config or DatabricksConfig.from_env()
        self._client = None

        if not self.config.validate():
            raise ValueError(
                "Invalid Databricks configuration. "
                "Required: DATABRICKS_HOST and DATABRICKS_TOKEN environment variables."
            )

    @property
    def client(self) -> Any:
        """Get or create Databricks SDK client."""
        if self._client is None:
            try:
                from databricks.sdk import WorkspaceClient  # type: ignore[import-not-found]

                self._client = WorkspaceClient(
                    host=self.config.host,
                    token=self.config.token,
                )
            except ImportError:
                raise ImportError(
                    "databricks-sdk package not installed. "
                    "Install with: pip install databricks-sdk"
                )
        return self._client

    def test_connection(self) -> dict[str, Any]:
        """Test Databricks connection.

        Returns:
            Dictionary with connection status and workspace info.
        """
        try:
            workspace = self.client.get_workspace_id()
            clusters = self.client.clusters.list()

            return {
                "status": "connected",
                "workspace_id": workspace,
                "cluster_count": len(list(clusters)),
                "config": self.config.to_dict(),
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "config": self.config.to_dict(),
            }

    def list_clusters(self) -> list[Any]:
        """List available clusters."""
        result = self.client.clusters.list()
        return list(result)

    def list_warehouses(self) -> list[Any]:
        """List available SQL warehouses."""
        result = self.client.warehouses.list()
        return list(result)

    def run_sql_query(self, query: str, warehouse_id: str | None = None) -> dict[str, Any]:
        """Execute SQL query on Databricks.

        Args:
            query: SQL query string.
            warehouse_id: SQL warehouse ID. If None, uses config warehouse_id.

        Returns:
            Query results.
        """
        warehouse = warehouse_id or self.config.warehouse_id
        if not warehouse:
            raise ValueError("SQL warehouse ID required for query execution")

        result = self.client.statement_execution.execute_statement(
            statement=query,
            warehouse_id=warehouse,
        )
        return result  # type: ignore
