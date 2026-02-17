"""Data collector for dashboard queries."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from grid.interfaces.config import DashboardConfig, get_config

from . import queries


class DashboardCollector:
    """Collects data from SQLite/Databricks for dashboard display."""

    def __init__(self, config: DashboardConfig | None = None):
        """Initialize dashboard collector.

        Args:
            config: Dashboard configuration (default: from environment)
        """
        self.config = config or get_config()
        self._conn: sqlite3.Connection | None = None

    def _get_connection(self) -> sqlite3.Connection:
        """Get SQLite connection.

        Returns:
            SQLite connection
        """
        if self._conn is not None:
            return self._conn

        db_path = self.config.prototype_db_path
        db_file = Path(db_path)
        if not db_file.exists():
            raise FileNotFoundError(f"Database file not found: {db_path}")

        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        return self._conn

    def _execute_query(self, query: str) -> list[dict[str, Any]]:
        """Execute query and return results as list of dictionaries.

        Args:
            query: SQL query string

        Returns:
            List of result dictionaries
        """
        conn = self._get_connection()
        cursor = conn.execute(query)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_recent_bridge_metrics(self, hours: int = 24) -> list[dict[str, Any]]:
        """Get recent bridge metrics.

        Args:
            hours: Number of hours to look back (default: 24)

        Returns:
            List of bridge metric dictionaries
        """
        query = queries.get_recent_bridge_metrics(hours)
        return self._execute_query(query)

    def get_recent_sensory_metrics(self, hours: int = 24) -> list[dict[str, Any]]:
        """Get recent sensory metrics.

        Args:
            hours: Number of hours to look back (default: 24)

        Returns:
            List of sensory metric dictionaries
        """
        query = queries.get_recent_sensory_metrics(hours)
        return self._execute_query(query)

    def get_latency_percentiles(self, hours: int = 24, interface_type: str = "bridge") -> dict[str, float]:
        """Get latency percentiles.

        Args:
            hours: Number of hours to look back (default: 24)
            interface_type: Interface type ('bridge' or 'sensory')

        Returns:
            Dictionary with p50, p95, p99 percentiles
        """
        query = queries.get_latency_percentiles(hours, interface_type)
        latencies = [row["latency_ms"] for row in self._execute_query(query)]

        if not latencies:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0}

        latencies.sort()
        n = len(latencies)

        def percentile(p: float) -> float:
            idx = int(p * n)
            if idx >= n:
                idx = n - 1
            return latencies[idx]

        return {
            "p50": percentile(0.50),
            "p95": percentile(0.95),
            "p99": percentile(0.99),
            "min": latencies[0] if latencies else 0.0,
            "max": latencies[-1] if latencies else 0.0,
            "count": n,
        }

    def get_throughput_metrics(self, hours: int = 24) -> list[dict[str, Any]]:
        """Get throughput metrics.

        Args:
            hours: Number of hours to look back (default: 24)

        Returns:
            List of throughput metric dictionaries
        """
        query = queries.get_throughput_metrics(hours)
        return self._execute_query(query)

    def get_coherence_trends(self, hours: int = 24) -> list[dict[str, Any]]:
        """Get coherence trends.

        Args:
            hours: Number of hours to look back (default: 24)

        Returns:
            List of coherence trend dictionaries
        """
        query = queries.get_coherence_trends(hours)
        return self._execute_query(query)

    def get_modality_distribution(self, hours: int = 24) -> list[dict[str, Any]]:
        """Get modality distribution.

        Args:
            hours: Number of hours to look back (default: 24)

        Returns:
            List of modality distribution dictionaries
        """
        query = queries.get_modality_distribution(hours)
        return self._execute_query(query)

    def get_error_rates(self, hours: int = 24) -> list[dict[str, Any]]:
        """Get error rates.

        Args:
            hours: Number of hours to look back (default: 24)

        Returns:
            List of error rate dictionaries
        """
        query = queries.get_error_rates(hours)
        return self._execute_query(query)

    def get_compression_metrics(self, hours: int = 24) -> list[dict[str, Any]]:
        """Get compression metrics.

        Args:
            hours: Number of hours to look back (default: 24)

        Returns:
            List of compression metric dictionaries
        """
        query = queries.get_compression_metrics(hours)
        return self._execute_query(query)

    def get_summary_stats(self, hours: int = 24) -> list[dict[str, Any]]:
        """Get summary statistics.

        Args:
            hours: Number of hours to look back (default: 24)

        Returns:
            List of summary statistic dictionaries
        """
        query = queries.get_summary_stats(hours)
        return self._execute_query(query)

    def get_all_metrics(self, hours: int = 24) -> dict[str, Any]:
        """Get all metrics for dashboard.

        Args:
            hours: Number of hours to look back (default: 24)

        Returns:
            Dictionary with all metrics
        """
        return {
            "bridge_metrics": self.get_recent_bridge_metrics(hours),
            "sensory_metrics": self.get_recent_sensory_metrics(hours),
            "bridge_latency_percentiles": self.get_latency_percentiles(hours, "bridge"),
            "sensory_latency_percentiles": self.get_latency_percentiles(hours, "sensory"),
            "throughput_metrics": self.get_throughput_metrics(hours),
            "coherence_trends": self.get_coherence_trends(hours),
            "modality_distribution": self.get_modality_distribution(hours),
            "error_rates": self.get_error_rates(hours),
            "compression_metrics": self.get_compression_metrics(hours),
            "summary_stats": self.get_summary_stats(hours),
            "hours": hours,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
