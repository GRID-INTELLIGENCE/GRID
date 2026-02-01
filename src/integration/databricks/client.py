"""Databricks WorkspaceClient wrapper with authentication."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from databricks.sdk import WorkspaceClient  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    load_dotenv(env_path)
    logger.info(f"Loaded environment variables from {env_path}")
except ImportError:
    logger.warning("python-dotenv not installed, environment variables may not be loaded from .env file")


class DatabricksClient:
    """Wrapper around Databricks WorkspaceClient with GRID-specific configuration."""

    def __init__(
        self,
        host: str | None = None,
        token: str | None = None,
        profile: str | None = None,
    ):
        """Initialize Databricks client.

        Args:
            host: Databricks workspace host URL (e.g., https://dbc-xxx.cloud.databricks.com)
            token: Personal Access Token (PAT) or use environment variable DATABRICKS_TOKEN
            profile: Databricks CLI profile name (uses configured auth from databricks configure)

        Priority for authentication:
            1. Explicit 'token' parameter
            2. DATABRICKS_TOKEN environment variable
            3. 'databricks' environment variable (for API key storage)
            4. Explicit 'profile' parameter
            5. Default Databricks CLI profile
        """
        # Priority: explicit args > environment variables > CLI profile
        self.host = host or os.getenv("DATABRICKS_HOST", "").strip()
        # Token priority: explicit arg > DATABRICKS_TOKEN env var > 'databricks' env var
        self.token = token or os.getenv("DATABRICKS_TOKEN", "").strip() or os.getenv("databricks", "").strip()
        self.profile = profile

        # Validate authentication
        if not self.host and not self.profile:
            raise ValueError("Either 'host' parameter or DATABRICKS_HOST environment variable is required")

        if not self.token and not self.profile:
            raise ValueError(
                "Either 'token' parameter, DATABRICKS_TOKEN environment variable, "
                "'databricks' environment variable, or 'profile' parameter is required"
            )

        # Create WorkspaceClient
        if self.profile:
            logger.info(f"Using Databricks CLI profile: {self.profile}")
            self.client = WorkspaceClient(profile=self.profile)
        else:
            logger.info(f"Connecting to Databricks workspace: {self.host}")
            self.client = WorkspaceClient(host=self.host, token=self.token)

        # Verify connection
        self._verify_connection()

    def _verify_connection(self) -> None:
        """Verify the connection to Databricks workspace."""
        try:
            # Use workspace.get_status() to verify connection
            self.client.workspace.get_status("/")
            logger.info("Successfully connected to Databricks workspace")
        except Exception as e:
            logger.error(f"Failed to connect to Databricks workspace: {e}")
            raise

    @property
    def workspace(self) -> WorkspaceClient:
        """Get the underlying WorkspaceClient."""
        return self.client

    def list_clusters(self) -> list[dict[str, Any]]:
        """List all clusters in the workspace.

        Returns:
            List of cluster information dictionaries
        """
        clusters = []
        for cluster in self.client.clusters.list():
            clusters.append(
                {
                    "cluster_id": cluster.cluster_id,
                    "cluster_name": cluster.cluster_name,
                    "state": cluster.state,
                    "num_workers": cluster.num_workers,
                    "spark_version": cluster.spark_version,
                }
            )
        return clusters

    def get_cluster(self, cluster_id: str) -> dict[str, Any] | None:
        """Get cluster details.

        Args:
            cluster_id: Cluster ID

        Returns:
            Cluster information or None if not found
        """
        try:
            cluster = self.client.clusters.get(cluster_id=cluster_id)
            return {
                "cluster_id": cluster.cluster_id,
                "cluster_name": cluster.cluster_name,
                "state": cluster.state,
                "num_workers": cluster.num_workers,
                "spark_version": cluster.spark_version,
                "node_type_id": cluster.node_type_id,
                "driver_node_type_id": cluster.driver_node_type_id,
            }
        except Exception as e:
            logger.error(f"Failed to get cluster {cluster_id}: {e}")
            return None
