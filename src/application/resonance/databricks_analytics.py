"""
Databricks Analytics Integration - Phase 3 Implementation.

Provides:
- SQL statement execution via Databricks SDK
- Cost tracking via system.billing.usage table
- Query history monitoring
- DBU consumption tracking
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


# Environment variable check for network operations
ALLOW_DATABRICKS_SYNC = os.getenv("ALLOW_DATABRICKS_SYNC", "false").lower() == "true"


@dataclass
class SQLExecutionResult:
    """Result from a SQL statement execution."""

    statement_id: str
    status: str  # "PENDING", "RUNNING", "SUCCEEDED", "FAILED", "CANCELED"
    execution_time_ms: float
    rows_affected: int
    result_data: list[list[Any]] = field(default_factory=list)
    column_names: list[str] = field(default_factory=list)
    error_message: Optional[str] = None
    dbu_consumed: float = 0.0


@dataclass
class DBUUsageRecord:
    """DBU usage record from Databricks billing."""

    usage_date: datetime
    sku_name: str
    usage_quantity: float
    usage_unit: str
    billing_origin_product: str


@dataclass
class QueryMetrics:
    """Metrics from query execution."""

    query_id: str
    query_text: str
    warehouse_id: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_ms: float
    rows_produced: int
    bytes_scanned: int
    estimated_dbu: float


class DatabricksAnalytics:
    """
    Databricks Analytics Integration.

    Uses the Databricks SDK for Python to:
    - Execute SQL statements against SQL Warehouses
    - Query the billing.usage system table
    - Track query performance and costs

    Authentication:
        - DATABRICKS_HOST: Workspace URL
        - DATABRICKS_TOKEN: Personal access token
        - Or use DATABRICKS_CONFIG_PROFILE for profile-based auth
    """

    # Default warehouse ID (can be overridden)
    DEFAULT_WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID", "")

    # Cost estimation constants
    DBU_PER_SECOND_SERVERLESS = 0.0028  # Approximate DBU/second for serverless
    DBU_PER_SECOND_CLASSIC = 0.0012  # Approximate DBU/second for classic

    def __init__(
        self,
        host: Optional[str] = None,
        token: Optional[str] = None,
        warehouse_id: Optional[str] = None,
    ):
        """
        Initialize Databricks Analytics.

        Args:
            host: Databricks workspace URL (or use DATABRICKS_HOST env var)
            token: Personal access token (or use DATABRICKS_TOKEN env var)
            warehouse_id: SQL Warehouse ID (or use DATABRICKS_WAREHOUSE_ID env var)
        """
        self._host = host or os.getenv("DATABRICKS_HOST", "")
        self._token = token or os.getenv("DATABRICKS_TOKEN", "")
        self._warehouse_id = warehouse_id or self.DEFAULT_WAREHOUSE_ID

        # Client state
        self._client: Any = None
        self._is_connected = False

        # Tracking
        self._query_history: list[QueryMetrics] = []
        self._usage_cache: list[DBUUsageRecord] = []
        self._cache_updated: Optional[datetime] = None

        logger.info(f"DatabricksAnalytics initialized (sync enabled: {ALLOW_DATABRICKS_SYNC})")

    def _get_client(self) -> Any:
        """
        Get or create Databricks WorkspaceClient.

        Returns:
            WorkspaceClient instance (lazy initialization)
        """
        if self._client is not None:
            return self._client

        if not ALLOW_DATABRICKS_SYNC:
            logger.warning("Databricks sync disabled (ALLOW_DATABRICKS_SYNC=false)")
            return None

        try:
            from databricks.sdk import WorkspaceClient

            if self._host and self._token:
                self._client = WorkspaceClient(
                    host=self._host,
                    token=self._token,
                )
            else:
                # Use default authentication (config profiles or env vars)
                self._client = WorkspaceClient()

            self._is_connected = True
            logger.info("Databricks client connected")
            return self._client
        except ImportError:
            logger.error("databricks-sdk not installed. Run: pip install databricks-sdk")
            return None
        except Exception as e:
            logger.error(f"Failed to create Databricks client: {e}")
            return None

    async def execute_sql(
        self,
        statement: str,
        warehouse_id: Optional[str] = None,
        timeout_seconds: int = 300,
    ) -> SQLExecutionResult:
        """
        Execute a SQL statement on Databricks SQL Warehouse.

        Uses the Statement Execution API for async SQL execution.

        Args:
            statement: SQL statement to execute
            warehouse_id: SQL Warehouse ID (uses default if not provided)
            timeout_seconds: Maximum wait time for completion

        Returns:
            SQLExecutionResult with data and metrics
        """
        statement_id = f"stmt_{uuid4().hex[:12]}"
        start_time = datetime.now(UTC)

        client = self._get_client()
        if client is None:
            # Return mock result when not connected
            return SQLExecutionResult(
                statement_id=statement_id,
                status="FAILED",
                execution_time_ms=0,
                rows_affected=0,
                error_message="Databricks client not available",
            )

        try:
            wh_id = warehouse_id or self._warehouse_id
            if not wh_id:
                return SQLExecutionResult(
                    statement_id=statement_id,
                    status="FAILED",
                    execution_time_ms=0,
                    rows_affected=0,
                    error_message="No warehouse ID configured",
                )

            # Execute statement via SDK
            response = client.statement_execution.execute_statement(
                warehouse_id=wh_id,
                statement=statement,
                wait_timeout=f"{timeout_seconds}s",
            )

            end_time = datetime.now(UTC)
            execution_time_ms = (end_time - start_time).total_seconds() * 1000

            # Extract results
            status = response.status.state.value if response.status else "UNKNOWN"
            result_data = []
            column_names = []
            rows_affected = 0

            if response.manifest and response.manifest.schema:
                column_names = [col.name for col in response.manifest.schema.columns]

            if response.result and response.result.data_array:
                result_data = response.result.data_array
                rows_affected = len(result_data)

            # Estimate DBU consumed
            estimated_dbu = execution_time_ms / 1000 * self.DBU_PER_SECOND_SERVERLESS

            # Record metrics
            metrics = QueryMetrics(
                query_id=statement_id,
                query_text=statement[:500],  # Truncate
                warehouse_id=wh_id,
                start_time=start_time,
                end_time=end_time,
                duration_ms=execution_time_ms,
                rows_produced=rows_affected,
                bytes_scanned=0,  # Not available from this API
                estimated_dbu=estimated_dbu,
            )
            self._query_history.append(metrics)

            return SQLExecutionResult(
                statement_id=statement_id,
                status=status,
                execution_time_ms=execution_time_ms,
                rows_affected=rows_affected,
                result_data=result_data,
                column_names=column_names,
                dbu_consumed=estimated_dbu,
            )

        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            return SQLExecutionResult(
                statement_id=statement_id,
                status="FAILED",
                execution_time_ms=(datetime.now(UTC) - start_time).total_seconds() * 1000,
                rows_affected=0,
                error_message=str(e),
            )

    async def query_billing_usage(
        self,
        days_back: int = 7,
    ) -> list[DBUUsageRecord]:
        """
        Query the system.billing.usage table for cost data.

        Args:
            days_back: Number of days to look back

        Returns:
            List of DBU usage records
        """
        query = f"""
        SELECT
            usage_date,
            sku_name,
            SUM(usage_quantity) as total_usage,
            usage_unit,
            billing_origin_product
        FROM system.billing.usage
        WHERE usage_date >= current_date() - INTERVAL {days_back} DAYS
        GROUP BY usage_date, sku_name, usage_unit, billing_origin_product
        ORDER BY usage_date DESC
        """

        result = await self.execute_sql(query)

        records: list[DBUUsageRecord] = []
        if result.status == "SUCCEEDED":
            for row in result.result_data:
                try:
                    records.append(
                        DBUUsageRecord(
                            usage_date=datetime.fromisoformat(str(row[0])) if row[0] else datetime.now(UTC),
                            sku_name=str(row[1]) if row[1] else "",
                            usage_quantity=float(row[2]) if row[2] else 0.0,
                            usage_unit=str(row[3]) if row[3] else "DBU",
                            billing_origin_product=str(row[4]) if row[4] else "",
                        )
                    )
                except (IndexError, ValueError) as e:
                    logger.warning(f"Failed to parse usage record: {e}")

        self._usage_cache = records
        self._cache_updated = datetime.now(UTC)

        return records

    async def get_total_dbu_consumed(self, days_back: int = 7) -> float:
        """Get total DBUs consumed in the specified period."""
        # Use cache if fresh
        if self._cache_updated and datetime.now(UTC) - self._cache_updated < timedelta(hours=1):
            return sum(r.usage_quantity for r in self._usage_cache)

        records = await self.query_billing_usage(days_back)
        return sum(r.usage_quantity for r in records)

    # ─────────────────────────────────────────────────────────────────────────
    # Resonance-Specific Queries
    # ─────────────────────────────────────────────────────────────────────────

    async def query_impact_distribution(
        self,
        table_name: str = "resonance_events",
    ) -> SQLExecutionResult:
        """
        Execute impact distribution query on Resonance events.

        Returns mean impact and count per event type.
        """
        query = f"""
        SELECT
            event_type,
            COUNT(*) as event_count,
            AVG(impact) as mean_impact,
            MAX(impact) as max_impact,
            MIN(impact) as min_impact
        FROM {table_name}
        WHERE timestamp >= current_timestamp() - INTERVAL 24 HOURS
        GROUP BY event_type
        ORDER BY mean_impact DESC
        """
        return await self.execute_sql(query)

    async def query_hot_activities(
        self,
        table_name: str = "resonance_events",
        threshold: int = 50,
    ) -> SQLExecutionResult:
        """
        Query for activities exceeding event density threshold.

        Args:
            table_name: Table containing events
            threshold: Minimum events per activity to be "hot"
        """
        query = f"""
        SELECT
            activity_id,
            COUNT(*) as event_count,
            AVG(impact) as avg_impact,
            MAX(impact) as peak_impact,
            MIN(timestamp) as first_event,
            MAX(timestamp) as last_event
        FROM {table_name}
        WHERE timestamp >= current_timestamp() - INTERVAL 1 HOUR
        GROUP BY activity_id
        HAVING COUNT(*) >= {threshold}
        ORDER BY event_count DESC
        LIMIT 20
        """
        return await self.execute_sql(query)

    async def query_temporal_flow(
        self,
        table_name: str = "resonance_events",
        window_minutes: int = 5,
    ) -> SQLExecutionResult:
        """
        Query events with rolling impact calculation.

        Args:
            table_name: Table containing events
            window_minutes: Rolling window size in minutes
        """
        query = f"""
        SELECT
            date_trunc('minute', timestamp) as time_bucket,
            COUNT(*) as event_count,
            AVG(impact) as avg_impact,
            SUM(CASE WHEN impact >= 0.9 THEN 1 ELSE 0 END) as spike_count,
            AVG(AVG(impact)) OVER (
                ORDER BY date_trunc('minute', timestamp)
                ROWS BETWEEN {window_minutes - 1} PRECEDING AND CURRENT ROW
            ) as rolling_avg_impact
        FROM {table_name}
        WHERE timestamp >= current_timestamp() - INTERVAL 2 HOURS
        GROUP BY date_trunc('minute', timestamp)
        ORDER BY time_bucket DESC
        LIMIT 120
        """
        return await self.execute_sql(query)

    async def query_cost_efficiency(
        self,
        events_table: str = "resonance_events",
    ) -> SQLExecutionResult:
        """
        Calculate cost efficiency metrics.

        Returns cost per meaningful event and efficiency ratio.
        """
        query = f"""
        WITH event_stats AS (
            SELECT
                COUNT(*) as total_events,
                SUM(CASE WHEN impact >= 0.5 THEN 1 ELSE 0 END) as meaningful_events,
                SUM(CASE WHEN impact >= 0.9 THEN 1 ELSE 0 END) as high_impact_events
            FROM {events_table}
            WHERE timestamp >= current_timestamp() - INTERVAL 1 HOUR
        ),
        cost_stats AS (
            SELECT
                SUM(usage_quantity) as total_dbu
            FROM system.billing.usage
            WHERE usage_date = current_date()
        )
        SELECT
            e.total_events,
            e.meaningful_events,
            e.high_impact_events,
            c.total_dbu,
            CASE WHEN e.total_events > 0
                 THEN c.total_dbu / e.total_events
                 ELSE 0
            END as dbu_per_event,
            CASE WHEN e.meaningful_events > 0
                 THEN c.total_dbu / e.meaningful_events
                 ELSE 0
            END as dbu_per_meaningful_event,
            CASE WHEN e.total_events > 0
                 THEN CAST(e.meaningful_events AS FLOAT) / e.total_events
                 ELSE 0
            END as efficiency_ratio
        FROM event_stats e
        CROSS JOIN cost_stats c
        """
        return await self.execute_sql(query)

    # ─────────────────────────────────────────────────────────────────────────
    # Query History & Metrics
    # ─────────────────────────────────────────────────────────────────────────

    def get_query_history(self, limit: int = 50) -> list[QueryMetrics]:
        """Get recent query history."""
        return self._query_history[-limit:]

    def get_total_estimated_dbu(self) -> float:
        """Get total estimated DBU from query history."""
        return sum(q.estimated_dbu for q in self._query_history)

    def get_query_performance_stats(self) -> dict[str, Any]:
        """Get query performance statistics."""
        if not self._query_history:
            return {
                "total_queries": 0,
                "avg_duration_ms": 0,
                "total_rows_produced": 0,
                "estimated_dbu": 0,
            }

        durations = [q.duration_ms for q in self._query_history]
        return {
            "total_queries": len(self._query_history),
            "avg_duration_ms": sum(durations) / len(durations),
            "min_duration_ms": min(durations),
            "max_duration_ms": max(durations),
            "total_rows_produced": sum(q.rows_produced for q in self._query_history),
            "estimated_dbu": self.get_total_estimated_dbu(),
        }

    @property
    def is_connected(self) -> bool:
        """Check if connected to Databricks."""
        return self._is_connected
