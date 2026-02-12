"""
Grafana dashboard configuration for GRID monitoring.

Provides comprehensive dashboard configurations for visualizing
GRID system metrics, performance data, and operational insights.
Includes dashboard definitions, panel configurations, and alert rules.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


class PanelType(Enum):
    """Grafana panel types."""
    GRAPH = "graph"
    STAT = "stat"
    TABLE = "table"
    HEATMAP = "heatmap"
    GAUGE = "gauge"
    SINGLE_STAT = "singlestat"
    BARGAUGE = "bargauge"
    PIE_CHART = "piechart"


class DataSourceType(Enum):
    """Data source types."""
    PROMETHEUS = "prometheus"
    INFLUXDB = "influxdb"
    ELASTICSEARCH = "elasticsearch"
    GRAPHITE = "graphite"


@dataclass
class PanelConfig:
    """Grafana panel configuration."""
    panel_id: int
    title: str
    panel_type: PanelType
    data_source: DataSourceType
    query: str
    description: str | None
    position: dict[str, int]  # x, y, w, h
    targets: list[dict[str, Any]]
    options: dict[str, Any]
    field_config: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to Grafana panel JSON."""
        return {
            "id": self.panel_id,
            "title": self.title,
            "type": self.panel_type.value,
            "datasource": self.data_source.value,
            "description": self.description,
            "gridPos": self.position,
            "targets": self.targets,
            "options": self.options,
            "fieldConfig": self.field_config,
        }


@dataclass
class DashboardConfig:
    """Grafana dashboard configuration."""
    dashboard_id: str
    title: str
    description: str
    tags: set[str]
    panels: list[PanelConfig]
    variables: list[dict[str, Any]]
    time_settings: dict[str, Any]
    refresh_settings: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to Grafana dashboard JSON."""
        return {
            "id": None,
            "uid": self.dashboard_id,
            "title": self.title,
            "description": self.description,
            "tags": list(self.tags),
            "panels": [panel.to_dict() for panel in self.panels],
            "templating": {"list": self.variables},
            "time": self.time_settings,
            "refresh": self.refresh_settings,
            "schemaVersion": 38,
            "version": 1,
        }


class GrafanaDashboardManager:
    """
    Grafana dashboard manager for GRID.

    Features:
    - Dashboard configuration management
    - Panel configuration
    - Template variables
    - Alert rule definitions
    - Dashboard templates
    - Auto-refresh settings
    - Multi-datasource support
    """

    def __init__(self, storage_path: str | None = None):
        """
        Initialize dashboard manager.

        Args:
            storage_path: Path for dashboard storage
        """
        self.storage_path = storage_path or "./data/grafana_dashboards"
        self.dashboards: dict[str, DashboardConfig] = {}

        logger.info("GrafanaDashboardManager initialized")

    def create_system_overview_dashboard(self) -> DashboardConfig:
        """Create system overview dashboard."""
        dashboard_id = str(uuid4())

        panels = [
            # System status panel
            PanelConfig(
                panel_id=1,
                title="System Status",
                panel_type=PanelType.STAT,
                data_source=DataSourceType.PROMETHEUS,
                query="up{job='grid'}",
                description="Overall system status",
                position={"x": 0, "y": 0, "w": 12, "h": 8},
                targets=[
                    {
                        "expr": "up{job='grid'}",
                        "legendFormat": "{{instance}}",
                        "refId": "A",
                    }
                ],
                options={
                    "reduceOptions": {
                        "values": False,
                        "calcs": ["lastNotNull"],
                        "fields": "",
                    },
                    "colorMode": "value",
                    "graphMode": "area",
                    "justifyMode": "auto",
                    "orientation": "auto",
                },
                field_config={
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {"hideFrom": {"legend": False, "tooltip": False, "vis": False}},
                        "mappings": [],
                        "thresholds": {
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "red", "value": 0},
                            ]
                        },
                    },
                    "overrides": [],
                },
            ),

            # CPU usage panel
            PanelConfig(
                panel_id=2,
                title="CPU Usage",
                panel_type=PanelType.GRAPH,
                data_source=DataSourceType.PROMETHEUS,
                query="rate(process_cpu_seconds_total{job='grid'}[5m]) * 100",
                description="CPU usage percentage",
                position={"x": 12, "y": 0, "w": 12, "h": 8},
                targets=[
                    {
                        "expr": "rate(process_cpu_seconds_total{job='grid'}[5m]) * 100",
                        "legendFormat": "{{instance}}",
                        "refId": "A",
                    }
                ],
                options={
                    "tooltip": {"mode": "single", "sort": "none"},
                    "legend": {"displayMode": "list", "placement": "bottom"},
                },
                field_config={
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {"axisLabel": "", "axisPlacement": "auto"},
                        "mappings": [],
                        "thresholds": {
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "yellow", "value": 70},
                                {"color": "red", "value": 90},
                            ]
                        },
                        "unit": "percent",
                    },
                    "overrides": [],
                },
            ),

            # Memory usage panel
            PanelConfig(
                panel_id=3,
                title="Memory Usage",
                panel_type=PanelType.GRAPH,
                data_source=DataSourceType.PROMETHEUS,
                query="process_resident_memory_bytes{job='grid'}",
                description="Memory usage in bytes",
                position={"x": 0, "y": 8, "w": 12, "h": 8},
                targets=[
                    {
                        "expr": "process_resident_memory_bytes{job='grid'}",
                        "legendFormat": "{{instance}}",
                        "refId": "A",
                    }
                ],
                options={
                    "tooltip": {"mode": "single", "sort": "none"},
                    "legend": {"displayMode": "list", "placement": "bottom"},
                },
                field_config={
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {"axisLabel": "", "axisPlacement": "auto"},
                        "mappings": [],
                        "thresholds": {
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "yellow", "value": 1073741824},  # 1GB
                                {"color": "red", "value": 2147483648},    # 2GB
                            ]
                        },
                        "unit": "bytes",
                    },
                    "overrides": [],
                },
            ),

            # Event processing rate
            PanelConfig(
                panel_id=4,
                title="Event Processing Rate",
                panel_type=PanelType.GRAPH,
                data_source=DataSourceType.PROMETHEUS,
                query="rate(grid_events_total[5m])",
                description="Events processed per second",
                position={"x": 12, "y": 8, "w": 12, "h": 8},
                targets=[
                    {
                        "expr": "rate(grid_events_total[5m])",
                        "legendFormat": "{{event_type}}",
                        "refId": "A",
                    }
                ],
                options={
                    "tooltip": {"mode": "single", "sort": "none"},
                    "legend": {"displayMode": "list", "placement": "bottom"},
                },
                field_config={
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {"axisLabel": "", "axisPlacement": "auto"},
                        "mappings": [],
                        "unit": "reqps",
                    },
                    "overrides": [],
                },
            ),
        ]

        dashboard = DashboardConfig(
            dashboard_id=dashboard_id,
            title="GRID System Overview",
            description="Comprehensive overview of GRID system performance and health",
            tags={"grid", "system", "overview"},
            panels=panels,
            variables=[
                {
                    "name": "instance",
                    "type": "query",
                    "datasource": {"type": "prometheus", "uid": "prometheus"},
                    "query": "label_values(up{job='grid'}, instance)",
                    "multi": True,
                    "includeAll": True,
                    "allValue": ".*",
                    "refresh": 1,
                }
            ],
            time_settings={"from": "now-1h", "to": "now"},
            refresh_settings={"type": "interval", "interval": "30s"},
        )

        self.dashboards[dashboard_id] = dashboard
        return dashboard

    def create_skills_performance_dashboard(self) -> DashboardConfig:
        """Create skills performance dashboard."""
        dashboard_id = str(uuid4())

        panels = [
            # Skill execution rate
            PanelConfig(
                panel_id=1,
                title="Skill Execution Rate",
                panel_type=PanelType.GRAPH,
                data_source=DataSourceType.PROMETHEUS,
                query="rate(grid_skills_executed_total[5m])",
                description="Skills executed per second",
                position={"x": 0, "y": 0, "w": 12, "h": 8},
                targets=[
                    {
                        "expr": "rate(grid_skills_executed_total{status='success'}[5m])",
                        "legendFormat": "Success - {{skill_id}}",
                        "refId": "A",
                    },
                    {
                        "expr": "rate(grid_skills_executed_total{status='error'}[5m])",
                        "legendFormat": "Error - {{skill_id}}",
                        "refId": "B",
                    },
                ],
                options={
                    "tooltip": {"mode": "single", "sort": "none"},
                    "legend": {"displayMode": "list", "placement": "bottom"},
                },
                field_config={
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {"axisLabel": "", "axisPlacement": "auto"},
                        "unit": "reqps",
                    },
                    "overrides": [],
                },
            ),

            # Skill execution duration
            PanelConfig(
                panel_id=2,
                title="Skill Execution Duration",
                panel_type=PanelType.HEATMAP,
                data_source=DataSourceType.PROMETHEUS,
                query="rate(grid_skill_execution_duration_seconds_bucket[5m])",
                description="Distribution of skill execution times",
                position={"x": 12, "y": 0, "w": 12, "h": 8},
                targets=[
                    {
                        "expr": "rate(grid_skill_execution_duration_seconds_bucket[5m])",
                        "legendFormat": "{{skill_id}}",
                        "refId": "A",
                    }
                ],
                options={
                    "heatmap": {"mode": "heatmap"},
                    "calculation": {"yAxis": "heatmap"},
                    "color": {"mode": "palette-classic"},
                },
                field_config={
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {"axisLabel": "", "axisPlacement": "auto"},
                        "unit": "seconds",
                    },
                    "overrides": [],
                },
            ),

            # Skill memory usage
            PanelConfig(
                panel_id=3,
                title="Skill Memory Usage",
                panel_type=PanelType.GRAPH,
                data_source=DataSourceType.PROMETHEUS,
                query="grid_skill_memory_usage_bytes",
                description="Memory usage by skill",
                position={"x": 0, "y": 8, "w": 12, "h": 8},
                targets=[
                    {
                        "expr": "grid_skill_memory_usage_bytes",
                        "legendFormat": "{{skill_id}}",
                        "refId": "A",
                    }
                ],
                options={
                    "tooltip": {"mode": "single", "sort": "none"},
                    "legend": {"displayMode": "list", "placement": "bottom"},
                },
                field_config={
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {"axisLabel": "", "axisPlacement": "auto"},
                        "unit": "bytes",
                    },
                    "overrides": [],
                },
            ),

            # Skill error rate
            PanelConfig(
                panel_id=4,
                title="Skill Error Rate",
                panel_type=PanelType.SINGLE_STAT,
                data_source=DataSourceType.PROMETHEUS,
                query="rate(grid_skills_executed_total{status='error'}[5m]) / rate(grid_skills_executed_total[5m])",
                description="Overall skill error rate",
                position={"x": 12, "y": 8, "w": 12, "h": 8},
                targets=[
                    {
                        "expr": "rate(grid_skills_executed_total{status='error'}[5m]) / rate(grid_skills_executed_total[5m])",
                        "legendFormat": "Error Rate",
                        "refId": "A",
                    }
                ],
                options={
                    "reduceOptions": {
                        "values": False,
                        "calcs": ["lastNotNull"],
                        "fields": "",
                    },
                    "colorMode": "value",
                    "graphMode": "area",
                    "justifyMode": "auto",
                    "orientation": "auto",
                },
                field_config={
                    "defaults": {
                        "color": {"mode": "thresholds"},
                        "mappings": [],
                        "thresholds": {
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "yellow", "value": 0.05},
                                {"color": "red", "value": 0.1},
                            ]
                        },
                        "unit": "percentunit",
                    },
                    "overrides": [],
                },
            ),
        ]

        dashboard = DashboardConfig(
            dashboard_id=dashboard_id,
            title="GRID Skills Performance",
            description="Detailed performance metrics for GRID skills",
            tags={"grid", "skills", "performance"},
            panels=panels,
            variables=[
                {
                    "name": "skill_id",
                    "type": "query",
                    "datasource": {"type": "prometheus", "uid": "prometheus"},
                    "query": "label_values(grid_skills_executed_total, skill_id)",
                    "multi": True,
                    "includeAll": True,
                    "allValue": ".*",
                    "refresh": 1,
                }
            ],
            time_settings={"from": "now-1h", "to": "now"},
            refresh_settings={"type": "interval", "interval": "30s"},
        )

        self.dashboards[dashboard_id] = dashboard
        return dashboard

    def create_security_dashboard(self) -> DashboardConfig:
        """Create security monitoring dashboard."""
        dashboard_id = str(uuid4())

        panels = [
            # Security alerts
            PanelConfig(
                panel_id=1,
                title="Security Alerts",
                panel_type=PanelType.GRAPH,
                data_source=DataSourceType.PROMETHEUS,
                query="rate(grid_security_alerts_total[5m])",
                description="Security alerts by type and severity",
                position={"x": 0, "y": 0, "w": 12, "h": 8},
                targets=[
                    {
                        "expr": "rate(grid_security_alerts_total[5m])",
                        "legendFormat": "{{alert_type}} - {{severity}}",
                        "refId": "A",
                    }
                ],
                options={
                    "tooltip": {"mode": "single", "sort": "none"},
                    "legend": {"displayMode": "list", "placement": "bottom"},
                },
                field_config={
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {"axisLabel": "", "axisPlacement": "auto"},
                        "unit": "reqps",
                    },
                    "overrides": [],
                },
            ),

            # Vulnerabilities
            PanelConfig(
                panel_id=2,
                title="Security Vulnerabilities",
                panel_type=PanelType.TABLE,
                data_source=DataSourceType.PROMETHEUS,
                query="grid_security_vulnerabilities_total",
                description="Security vulnerabilities by category and severity",
                position={"x": 12, "y": 0, "w": 12, "h": 8},
                targets=[
                    {
                        "expr": "grid_security_vulnerabilities_total",
                        "legendFormat": "{{category}} - {{severity}}",
                        "refId": "A",
                    }
                ],
                options={
                    "showHeader": True,
                },
                field_config={
                    "defaults": {
                        "color": {"mode": "thresholds"},
                        "mappings": [],
                        "thresholds": {
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "yellow", "value": 1},
                                {"color": "red", "value": 5},
                            ]
                        },
                    },
                    "overrides": [],
                },
            ),

            # Threat detection
            PanelConfig(
                panel_id=3,
                title="Threat Detection Rate",
                panel_type=PanelType.GRAPH,
                data_source=DataSourceType.PROMETHEUS,
                query="rate(grid_security_alerts_total{alert_type='threat'}[5m])",
                description="Threat detection rate over time",
                position={"x": 0, "y": 8, "w": 24, "h": 8},
                targets=[
                    {
                        "expr": "rate(grid_security_alerts_total{alert_type='threat'}[5m])",
                        "legendFormat": "{{severity}}",
                        "refId": "A",
                    }
                ],
                options={
                    "tooltip": {"mode": "single", "sort": "none"},
                    "legend": {"displayMode": "list", "placement": "bottom"},
                },
                field_config={
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {"axisLabel": "", "axisPlacement": "auto"},
                        "unit": "reqps",
                    },
                    "overrides": [],
                },
            ),
        ]

        dashboard = DashboardConfig(
            dashboard_id=dashboard_id,
            title="GRID Security Monitoring",
            description="Security monitoring and threat detection dashboard",
            tags={"grid", "security", "monitoring"},
            panels=panels,
            variables=[
                {
                    "name": "severity",
                    "type": "query",
                    "datasource": {"type": "prometheus", "uid": "prometheus"},
                    "query": "label_values(grid_security_alerts_total, severity)",
                    "multi": True,
                    "includeAll": True,
                    "allValue": ".*",
                    "refresh": 1,
                }
            ],
            time_settings={"from": "now-24h", "to": "now"},
            refresh_settings={"type": "interval", "interval": "1m"},
        )

        self.dashboards[dashboard_id] = dashboard
        return dashboard

    def create_knowledge_graph_dashboard(self) -> DashboardConfig:
        """Create knowledge graph dashboard."""
        dashboard_id = str(uuid4())

        panels = [
            # Entity counts
            PanelConfig(
                panel_id=1,
                title="Knowledge Graph Entities",
                panel_type=PanelType.PIE_CHART,
                data_source=DataSourceType.PROMETHEUS,
                query="grid_knowledge_entities_total",
                description="Distribution of entity types",
                position={"x": 0, "y": 0, "w": 12, "h": 8},
                targets=[
                    {
                        "expr": "grid_knowledge_entities_total",
                        "legendFormat": "{{entity_type}}",
                        "refId": "A",
                    }
                ],
                options={
                    "pieType": "pie",
                    "tooltip": {"mode": "single", "sort": "none"},
                    "legend": {"displayMode": "list", "placement": "right"},
                },
                field_config={
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "mappings": [],
                    },
                    "overrides": [],
                },
            ),

            # Relationship counts
            PanelConfig(
                panel_id=2,
                title="Knowledge Graph Relationships",
                panel_type=PanelType.BARGAUGE,
                data_source=DataSourceType.PROMETHEUS,
                query="grid_knowledge_relationships_total",
                description="Relationship types distribution",
                position={"x": 12, "y": 0, "w": 12, "h": 8},
                targets=[
                    {
                        "expr": "grid_knowledge_relationships_total",
                        "legendFormat": "{{relationship_type}}",
                        "refId": "A",
                    }
                ],
                options={
                    "displayMode": "gradient",
                    "orientation": "horizontal",
                    "reduceOptions": {
                        "values": False,
                        "calcs": ["lastNotNull"],
                        "fields": "",
                    },
                },
                field_config={
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "mappings": [],
                    },
                    "overrides": [],
                },
            ),

            # Query performance
            PanelConfig(
                panel_id=3,
                title="Query Performance",
                panel_type=PanelType.GRAPH,
                data_source=DataSourceType.PROMETHEUS,
                query="rate(grid_knowledge_query_duration_seconds[5m])",
                description="Knowledge graph query performance",
                position={"x": 0, "y": 8, "w": 24, "h": 8},
                targets=[
                    {
                        "expr": "rate(grid_knowledge_query_duration_seconds_sum[5m]) / rate(grid_knowledge_query_duration_seconds_count[5m])",
                        "legendFormat": "Average - {{query_type}}",
                        "refId": "A",
                    },
                    {
                        "expr": "histogram_quantile(0.95, rate(grid_knowledge_query_duration_seconds_bucket[5m]))",
                        "legendFormat": "95th percentile - {{query_type}}",
                        "refId": "B",
                    },
                ],
                options={
                    "tooltip": {"mode": "single", "sort": "none"},
                    "legend": {"displayMode": "list", "placement": "bottom"},
                },
                field_config={
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {"axisLabel": "", "axisPlacement": "auto"},
                        "unit": "seconds",
                    },
                    "overrides": [],
                },
            ),
        ]

        dashboard = DashboardConfig(
            dashboard_id=dashboard_id,
            title="GRID Knowledge Graph",
            description="Knowledge graph metrics and performance",
            tags={"grid", "knowledge", "graph"},
            panels=panels,
            variables=[
                {
                    "name": "entity_type",
                    "type": "query",
                    "datasource": {"type": "prometheus", "uid": "prometheus"},
                    "query": "label_values(grid_knowledge_entities_total, entity_type)",
                    "multi": True,
                    "includeAll": True,
                    "allValue": ".*",
                    "refresh": 1,
                }
            ],
            time_settings={"from": "now-1h", "to": "now"},
            refresh_settings={"type": "interval", "interval": "30s"},
        )

        self.dashboards[dashboard_id] = dashboard
        return dashboard

    def save_dashboard(self, dashboard: DashboardConfig, filename: str | None = None) -> str:
        """
        Save dashboard configuration to file.

        Args:
            dashboard: Dashboard configuration
            filename: Optional filename

        Returns:
            File path
        """
        if not filename:
            filename = f"{dashboard.dashboard_id}.json"

        filepath = f"{self.storage_path}/{filename}"

        try:
            with open(filepath, 'w') as f:
                json.dump(dashboard.to_dict(), f, indent=2)

            logger.info(f"Dashboard saved to {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Failed to save dashboard: {e}")
            raise

    def load_dashboard(self, filepath: str) -> DashboardConfig | None:
        """
        Load dashboard configuration from file.

        Args:
            filepath: Dashboard file path

        Returns:
            Dashboard configuration or None if failed
        """
        try:
            with open(filepath) as f:
                json.load(f)

            # Convert back to DashboardConfig
            # This is a simplified version - in production, you'd need
            # proper deserialization logic

            logger.info(f"Dashboard loaded from {filepath}")
            return None  # Placeholder

        except Exception as e:
            logger.error(f"Failed to load dashboard: {e}")
            return None

    def get_dashboard(self, dashboard_id: str) -> DashboardConfig | None:
        """Get dashboard by ID."""
        return self.dashboards.get(dashboard_id)

    def list_dashboards(self) -> list[str]:
        """List all dashboard IDs."""
        return list(self.dashboards.keys())

    def delete_dashboard(self, dashboard_id: str) -> bool:
        """Delete a dashboard."""
        if dashboard_id in self.dashboards:
            del self.dashboards[dashboard_id]
            return True
        return False


# Global dashboard manager instance
_global_dashboard_manager: GrafanaDashboardManager | None = None


def get_grafana_dashboard_manager() -> GrafanaDashboardManager:
    """Get or create global Grafana dashboard manager."""
    global _global_dashboard_manager
    if _global_dashboard_manager is None:
        _global_dashboard_manager = GrafanaDashboardManager()
    return _global_dashboard_manager


def set_grafana_dashboard_manager(manager: GrafanaDashboardManager) -> None:
    """Set global Grafana dashboard manager."""
    global _global_dashboard_manager
    _global_dashboard_manager = manager
