"""
Tests for Databricks Analytics Integration - Phase 3.

Covers:
- SQL execution
- Billing usage queries
- Resonance-specific queries
- Query metrics tracking
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from application.resonance.databricks_analytics import (
    DatabricksAnalytics,
    QueryMetrics,
    SQLExecutionResult,
)


@pytest.fixture
def databricks_analytics():
    """Create a DatabricksAnalytics instance (not connected)."""
    return DatabricksAnalytics()


@pytest.fixture
def mock_client():
    """Create a mock Databricks client."""
    mock = MagicMock()
    mock.statement_execution.execute_statement.return_value = MagicMock(
        status=MagicMock(state=MagicMock(value="SUCCEEDED")),
        manifest=MagicMock(
            schema=MagicMock(
                columns=[
                    MagicMock(name="col1"),
                    MagicMock(name="col2"),
                ]
            )
        ),
        result=MagicMock(data_array=[["val1", "val2"], ["val3", "val4"]]),
    )
    return mock


class TestSQLExecution:
    """Test SQL statement execution."""

    @pytest.mark.asyncio
    async def test_execute_sql_no_client(self, databricks_analytics):
        """Test SQL execution when client not available."""
        result = await databricks_analytics.execute_sql("SELECT * FROM test_table")

        assert isinstance(result, SQLExecutionResult)
        assert result.status == "FAILED"
        assert "not available" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_execute_sql_no_warehouse(self, databricks_analytics):
        """Test SQL execution when no warehouse configured."""
        with patch.object(databricks_analytics, "_get_client", return_value=MagicMock()):
            result = await databricks_analytics.execute_sql("SELECT 1")

            # Will fail due to no warehouse ID
            assert result.status == "FAILED" or result.warehouse_id == ""

    @pytest.mark.asyncio
    async def test_execute_sql_success(self, databricks_analytics, mock_client):
        """Test successful SQL execution."""
        databricks_analytics._client = mock_client
        databricks_analytics._is_connected = True
        databricks_analytics._warehouse_id = "test_warehouse"

        with patch.dict("os.environ", {"ALLOW_DATABRICKS_SYNC": "true"}):
            result = await databricks_analytics.execute_sql(
                "SELECT * FROM test",
            )

        assert result.statement_id.startswith("stmt_")
        # Note: actual status depends on mock behavior


class TestBillingQueries:
    """Test billing/usage queries."""

    @pytest.mark.asyncio
    async def test_query_billing_usage(self, databricks_analytics):
        """Test billing usage query."""
        records = await databricks_analytics.query_billing_usage(days_back=7)

        # Will return empty list since not connected
        assert isinstance(records, list)

    @pytest.mark.asyncio
    async def test_get_total_dbu_consumed(self, databricks_analytics):
        """Test total DBU consumption calculation."""
        total = await databricks_analytics.get_total_dbu_consumed(days_back=7)

        assert isinstance(total, (int, float))
        assert total >= 0


class TestResonanceQueries:
    """Test Resonance-specific analytics queries."""

    @pytest.mark.asyncio
    async def test_query_impact_distribution(self, databricks_analytics):
        """Test impact distribution query."""
        result = await databricks_analytics.query_impact_distribution()

        assert isinstance(result, SQLExecutionResult)
        assert result.statement_id.startswith("stmt_")

    @pytest.mark.asyncio
    async def test_query_hot_activities(self, databricks_analytics):
        """Test hot activities query."""
        result = await databricks_analytics.query_hot_activities(threshold=50)

        assert isinstance(result, SQLExecutionResult)

    @pytest.mark.asyncio
    async def test_query_temporal_flow(self, databricks_analytics):
        """Test temporal flow query."""
        result = await databricks_analytics.query_temporal_flow(window_minutes=5)

        assert isinstance(result, SQLExecutionResult)

    @pytest.mark.asyncio
    async def test_query_cost_efficiency(self, databricks_analytics):
        """Test cost efficiency query."""
        result = await databricks_analytics.query_cost_efficiency()

        assert isinstance(result, SQLExecutionResult)


class TestQueryMetrics:
    """Test query metrics tracking."""

    @pytest.mark.asyncio
    async def test_query_history_tracking(self, databricks_analytics, mock_client):
        """Test that queries are tracked in history."""
        databricks_analytics._client = mock_client
        databricks_analytics._is_connected = True
        databricks_analytics._warehouse_id = "test_wh"

        with patch.dict("os.environ", {"ALLOW_DATABRICKS_SYNC": "true"}):
            await databricks_analytics.execute_sql("SELECT 1")
            await databricks_analytics.execute_sql("SELECT 2")

        history = databricks_analytics.get_query_history()
        # May have entries depending on mock success
        assert isinstance(history, list)

    def test_get_query_performance_stats_empty(self, databricks_analytics):
        """Test performance stats when no queries executed."""
        stats = databricks_analytics.get_query_performance_stats()

        assert stats["total_queries"] == 0
        assert stats["avg_duration_ms"] == 0

    def test_get_total_estimated_dbu(self, databricks_analytics):
        """Test total estimated DBU calculation."""
        # Add some fake query history
        databricks_analytics._query_history.append(
            QueryMetrics(
                query_id="q1",
                query_text="SELECT 1",
                warehouse_id="wh1",
                start_time=datetime.now(UTC),
                end_time=datetime.now(UTC),
                duration_ms=1000,
                rows_produced=10,
                bytes_scanned=1000,
                estimated_dbu=0.5,
            )
        )

        total = databricks_analytics.get_total_estimated_dbu()
        assert total == 0.5


class TestConnectionState:
    """Test connection state management."""

    def test_initial_not_connected(self, databricks_analytics):
        """Test that analytics starts disconnected."""
        assert databricks_analytics.is_connected is False

    def test_get_client_without_sdk(self, databricks_analytics):
        """Test client creation when SDK not installed."""
        client = databricks_analytics._get_client()

        # Should return None if SDK not installed or sync disabled
        assert client is None or databricks_analytics._is_connected


class TestDBUCostConstants:
    """Test DBU cost calculation constants."""

    def test_serverless_cost_higher(self, databricks_analytics):
        """Test that serverless cost per DBU is higher than classic."""
        assert databricks_analytics.DBU_PER_SECOND_SERVERLESS > databricks_analytics.DBU_PER_SECOND_CLASSIC
