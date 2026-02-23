"""Databricks Clusters management."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class DatabricksClustersManager:
    """Manage Databricks clusters."""

    def __init__(self, client):
        """Initialize clusters manager.

        Args:
            client: DatabricksClient instance
        """
        self.client = client

    def start_cluster(self, cluster_id: str) -> bool:
        """Start a cluster.

        Args:
            cluster_id: Cluster ID to start

        Returns:
            True if successful
        """
        try:
            self.client.workspace.clusters.start(cluster_id=cluster_id)
            logger.info(f"Started cluster {cluster_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to start cluster {cluster_id}: {e}")
            return False

    def stop_cluster(self, cluster_id: str) -> bool:
        """Stop a cluster.

        Args:
            cluster_id: Cluster ID to stop

        Returns:
            True if successful
        """
        try:
            self.client.workspace.clusters.stop(cluster_id=cluster_id)
            logger.info(f"Stopped cluster {cluster_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to stop cluster {cluster_id}: {e}")
            return False

    def get_cluster_status(self, cluster_id: str) -> dict[str, Any] | None:
        """Get cluster status.

        Args:
            cluster_id: Cluster ID

        Returns:
            Cluster status information or None
        """
        try:
            cluster = self.client.workspace.clusters.get(cluster_id=cluster_id)
            return {
                "cluster_id": cluster.cluster_id,
                "cluster_name": cluster.cluster_name,
                "state": cluster.state,
                "num_workers": cluster.num_workers,
                "driver": cluster.driver,
                "spark_version": cluster.spark_version,
                "node_type_id": cluster.node_type_id,
            }
        except Exception as e:
            logger.error(f"Failed to get cluster status for {cluster_id}: {e}")
            return None

    def list_clusters(self) -> list[dict[str, Any]]:
        """List all clusters.

        Returns:
            List of cluster information
        """
        clusters = [
            {
                "cluster_id": cluster.cluster_id,
                "cluster_name": cluster.cluster_name,
                "state": cluster.state,
                "num_workers": cluster.num_workers,
                "spark_version": cluster.spark_version,
            }
            for cluster in self.client.workspace.clusters.list()
        ]
        return clusters

    def resize_cluster(self, cluster_id: str, num_workers: int) -> bool:
        """Resize a cluster.

        Args:
            cluster_id: Cluster ID
            num_workers: Number of workers

        Returns:
            True if successful
        """
        try:
            self.client.workspace.clusters.resize(cluster_id=cluster_id, num_workers=num_workers)
            logger.info(f"Resized cluster {cluster_id} to {num_workers} workers")
            return True
        except Exception as e:
            logger.error(f"Failed to resize cluster {cluster_id}: {e}")
            return False
