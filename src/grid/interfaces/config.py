"""Configuration for interfaces metrics dashboard."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import timedelta


def _parse_bool(value: str | None) -> bool:
    """Parse boolean value from environment variable.

    Args:
        value: String value to parse

    Returns:
        Boolean value (default: False)
    """
    if not value:
        return False
    return value.lower() in ("true", "1", "yes", "on")


@dataclass
class DashboardConfig:
    """Configuration for interfaces metrics dashboard."""

    # Collection settings
    default_time_window_days: int = 7
    trace_limit: int = 1000
    batch_size: int = 100

    # Databricks settings
    use_databricks: bool = False
    databricks_schema: str = "default"
    bridge_metrics_table: str = "interfaces_bridge_metrics"
    sensory_metrics_table: str = "interfaces_sensory_metrics"
    metrics_summary_table: str = "interfaces_metrics_summary"

    # Local prototype settings
    prototype_mode: bool = False
    prototype_db_path: str = "data/interfaces_metrics.db"
    prototype_port: int = 8080
    prototype_host: str = "localhost"

    # Dashboard settings
    refresh_interval_seconds: int = 30
    default_chart_hours: int = 24

    # JSON collection settings
    enable_json_collection: bool = True
    json_scan_days: int = 7
    json_scan_paths: list[str] = field(
        default_factory=lambda: ["data", "grid/logs/traces", "**/benchmark*.json", "**/stress*.json"]
    )

    @classmethod
    def from_env(cls) -> DashboardConfig:
        """Load configuration from environment variables.

        Returns:
            DashboardConfig instance
        """
        env = os.environ

        return cls(
            default_time_window_days=int(env.get("INTERFACES_METRICS_TIME_WINDOW_DAYS", "7")),
            trace_limit=int(env.get("INTERFACES_METRICS_TRACE_LIMIT", "1000")),
            batch_size=int(env.get("INTERFACES_METRICS_BATCH_SIZE", "100")),
            use_databricks=_parse_bool(env.get("USE_DATABRICKS")) or _parse_bool(env.get("INTERFACES_USE_DATABRICKS")),
            databricks_schema=env.get("INTERFACES_DATABRICKS_SCHEMA", "default"),
            bridge_metrics_table=env.get("INTERFACES_BRIDGE_TABLE", "interfaces_bridge_metrics"),
            sensory_metrics_table=env.get("INTERFACES_SENSORY_TABLE", "interfaces_sensory_metrics"),
            metrics_summary_table=env.get("INTERFACES_SUMMARY_TABLE", "interfaces_metrics_summary"),
            prototype_mode=_parse_bool(env.get("INTERFACES_PROTOTYPE_MODE", "true")),
            prototype_db_path=env.get("INTERFACES_PROTOTYPE_DB_PATH", "data/interfaces_metrics.db"),
            prototype_port=int(env.get("INTERFACES_PROTOTYPE_PORT", "8080")),
            prototype_host=env.get("INTERFACES_PROTOTYPE_HOST", "localhost"),
            refresh_interval_seconds=int(env.get("INTERFACES_DASHBOARD_REFRESH_SECONDS", "30")),
            default_chart_hours=int(env.get("INTERFACES_DASHBOARD_CHART_HOURS", "24")),
            enable_json_collection=_parse_bool(env.get("INTERFACES_ENABLE_JSON_COLLECTION", "true")),
            json_scan_days=int(env.get("INTERFACES_JSON_SCAN_DAYS", "7")),
            json_scan_paths=(
                env.get("INTERFACES_JSON_SCAN_PATHS", "").split(",")
                if env.get("INTERFACES_JSON_SCAN_PATHS")
                else ["data", "grid/logs/traces", "**/benchmark*.json", "**/stress*.json"]
            ),
        )

    def get_time_window_delta(self) -> timedelta:
        """Get time window as timedelta.

        Returns:
            Time window timedelta
        """
        return timedelta(days=self.default_time_window_days)

    def get_bridge_table_name(self) -> str:
        """Get full table name for bridge metrics.

        Returns:
            Full table name (with schema if Databricks)
        """
        if self.use_databricks and self.databricks_schema != "default":
            return f"{self.databricks_schema}.{self.bridge_metrics_table}"
        return self.bridge_metrics_table

    def get_sensory_table_name(self) -> str:
        """Get full table name for sensory metrics.

        Returns:
            Full table name (with schema if Databricks)
        """
        if self.use_databricks and self.databricks_schema != "default":
            return f"{self.databricks_schema}.{self.sensory_metrics_table}"
        return self.sensory_metrics_table

    def get_summary_table_name(self) -> str:
        """Get full table name for metrics summary.

        Returns:
            Full table name (with schema if Databricks)
        """
        if self.use_databricks and self.databricks_schema != "default":
            return f"{self.databricks_schema}.{self.metrics_summary_table}"
        return self.metrics_summary_table


# Global config instance
_config: DashboardConfig | None = None


def get_config() -> DashboardConfig:
    """Get global dashboard configuration.

    Returns:
        DashboardConfig instance
    """
    global _config
    if _config is None:
        _config = DashboardConfig.from_env()
    return _config


def set_config(config: DashboardConfig) -> None:
    """Set global dashboard configuration.

    Args:
        config: DashboardConfig instance
    """
    global _config
    _config = config
