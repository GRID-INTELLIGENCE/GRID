"""
Unit Tests for Databricks Components
=====================================
Comprehensive unit tests for Databricks integration.

Focus: Quality over quantity - practical relevance, accuracy, precision
"""


import pytest

from coinbase.database.databricks_analyzer import DatabricksPortfolioAnalyzer
from coinbase.database.databricks_persistence import (
    DatabricksPortfolioPersistence,
    PortfolioPosition,
)
from coinbase.database.databricks_schema import (
    CREATE_PORTFOLIO_EVENTS,
    CREATE_PORTFOLIO_POSITIONS,
    CREATE_PORTFOLIO_SUMMARY,
    CREATE_PRICE_HISTORY,
    CREATE_TRADING_SIGNALS,
    MERGE_PORTFOLIO_POSITION,
    MERGE_PORTFOLIO_SUMMARY,
)


class TestDatabricksSchema:
    """Unit tests for Databricks schema definitions."""

    def test_schema_ddl_exists(self):
        """Test that all schema DDLs are defined."""
        assert CREATE_PORTFOLIO_POSITIONS is not None
        assert CREATE_PRICE_HISTORY is not None
        assert CREATE_TRADING_SIGNALS is not None
        assert CREATE_PORTFOLIO_EVENTS is not None
        assert CREATE_PORTFOLIO_SUMMARY is not None

    def test_merge_queries_exist(self):
        """Test that MERGE queries are defined."""
        assert MERGE_PORTFOLIO_POSITION is not None
        assert MERGE_PORTFOLIO_SUMMARY is not None

    def test_portfolio_position_ddl_structure(self):
        """Test portfolio positions table structure."""
        assert "CREATE TABLE IF NOT EXISTS portfolio_positions" in CREATE_PORTFOLIO_POSITIONS
        assert "user_id_hash" in CREATE_PORTFOLIO_POSITIONS
        assert "symbol" in CREATE_PORTFOLIO_POSITIONS
        assert "quantity" in CREATE_PORTFOLIO_POSITIONS
        assert "current_price" in CREATE_PORTFOLIO_POSITIONS


class TestPortfolioPosition:
    """Unit tests for PortfolioPosition dataclass."""

    def test_portfolio_position_creation(self):
        """Test creating portfolio position."""
        position = PortfolioPosition(
            symbol="AAPL",
            asset_name="Apple Inc.",
            sector="Technology",
            quantity=50,
            purchase_price=150.0,
            current_price=175.0,
            purchase_value=7500.0,
            current_value=8750.0,
            total_gain_loss=1250.0,
            gain_loss_percentage=16.67,
            purchase_date="2024-01-15",
        )

        assert position.symbol == "AAPL"
        assert position.quantity == 50
        assert position.current_value == 8750.0
        assert position.total_gain_loss == 1250.0

    def test_portfolio_position_defaults(self):
        """Test portfolio position with optional fields."""
        position = PortfolioPosition(
            symbol="AAPL",
            asset_name="Apple Inc.",
            sector="Technology",
            quantity=50,
            purchase_price=150.0,
            current_price=175.0,
            purchase_value=7500.0,
            current_value=8750.0,
            total_gain_loss=1250.0,
            gain_loss_percentage=16.67,
            purchase_date="2024-01-15",
            commission=0.0,
        )

        assert position.high_limit is None
        assert position.low_limit is None
        assert position.comment is None
        assert position.transaction_type is None


class TestDatabricksPersistence:
    """Unit tests for DatabricksPortfolioPersistence."""

    def test_initialization_without_credentials(self):
        """Test initialization fails gracefully without credentials."""
        import os

        # Save original env vars
        original_host = os.environ.get("DATABRICKS_HOST")
        original_path = os.environ.get("DATABRICKS_HTTP_PATH")
        original_token = os.environ.get("DATABRICKS_TOKEN")
        original_offline = os.environ.get("DATABRICKS_OFFLINE")

        # Clear credentials and disable offline mode
        os.environ.pop("DATABRICKS_HOST", None)
        os.environ.pop("DATABRICKS_HTTP_PATH", None)
        os.environ.pop("DATABRICKS_TOKEN", None)
        os.environ.pop("DATABRICKS_OFFLINE", None)

        # Should raise ValueError
        with pytest.raises(ValueError):
            DatabricksPortfolioPersistence()

        # Restore env vars
        if original_host:
            os.environ["DATABRICKS_HOST"] = original_host
        if original_path:
            os.environ["DATABRICKS_HTTP_PATH"] = original_path
        if original_token:
            os.environ["DATABRICKS_TOKEN"] = original_token
        if original_offline:
            os.environ["DATABRICKS_OFFLINE"] = original_offline


class TestDatabricksAnalyzer:
    """Unit tests for DatabricksPortfolioAnalyzer."""

    def test_initialization(self):
        """Test analyzer initialization."""
        import os

        # Only test if credentials available
        if all(
            [
                os.getenv("DATABRICKS_HOST"),
                os.getenv("DATABRICKS_HTTP_PATH"),
                os.getenv("DATABRICKS_TOKEN"),
            ]
        ):
            analyzer = DatabricksPortfolioAnalyzer()
            assert analyzer is not None
            assert analyzer.persistence is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
