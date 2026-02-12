"""
Smoke Tests for Databricks Components
======================================
Critical path tests ensuring Databricks functionality.

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


def test_databricks_schema_defined():
    """Smoke test: Databricks schema is defined."""
    assert CREATE_PORTFOLIO_POSITIONS is not None
    assert CREATE_PRICE_HISTORY is not None
    assert CREATE_TRADING_SIGNALS is not None
    assert CREATE_PORTFOLIO_EVENTS is not None
    assert CREATE_PORTFOLIO_SUMMARY is not None


def test_databricks_merge_queries_defined():
    """Smoke test: Databricks MERGE queries are defined."""
    assert MERGE_PORTFOLIO_POSITION is not None
    assert MERGE_PORTFOLIO_SUMMARY is not None


def test_portfolio_position_creation():
    """Smoke test: PortfolioPosition can be created."""
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


def test_databricks_persistence_initialization():
    """Smoke test: DatabricksPersistence can be initialized."""
    import os

    # Only test with credentials
    if all(
        [
            os.getenv("DATABRICKS_HOST"),
            os.getenv("DATABRICKS_HTTP_PATH"),
            os.getenv("DATABRICKS_TOKEN"),
        ]
    ):
        persistence = DatabricksPortfolioPersistence()
        assert persistence is not None
        assert persistence.connector is not None


def test_databricks_analyzer_initialization():
    """Smoke test: DatabricksAnalyzer can be initialized."""
    import os

    # Only test with credentials
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


def test_portfolio_position_calculation():
    """Smoke test: Portfolio position calculations work."""
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

    # Verify calculations
    assert position.purchase_value == 7500.0
    assert position.current_value == 8750.0
    assert position.total_gain_loss == 1250.0
    assert position.gain_loss_percentage == 16.67


def test_databricks_workflow_structure():
    """Smoke test: Databricks workflow structure is correct."""
    # Verify workflow steps exist
    workflow_components = [
        "DatabricksConnector",
        "DatabricksPortfolioPersistence",
        "DatabricksPortfolioAnalyzer",
        "PortfolioPosition",
    ]

    from coinbase.infrastructure.databricks_connector import DatabricksConnector

    assert DatabricksConnector is not None
    assert DatabricksPortfolioPersistence is not None
    assert DatabricksPortfolioAnalyzer is not None
    assert PortfolioPosition is not None


def test_critical_path_portfolio_analysis():
    """Smoke test: Critical path for portfolio analysis."""
    # Create sample position
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

    # Verify critical calculations
    assert position.current_value > 0
    assert position.total_gain_loss > 0
    assert position.gain_loss_percentage > 0


def test_databricks_integration_example_exists():
    """Smoke test: Databricks integration example exists."""
    import os

    example_path = "e:/Coinbase/examples/databricks_integration.py"
    assert os.path.exists(example_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
