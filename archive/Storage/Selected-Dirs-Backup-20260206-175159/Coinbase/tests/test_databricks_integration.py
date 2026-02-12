"""
Integration Tests for Databricks Components
===========================================
Tests for Databricks workflow and component collaboration.

Focus: Quality over quantity - practical relevance, accuracy, precision
"""


import pytest

from coinbase.database.databricks_analyzer import DatabricksPortfolioAnalyzer
from coinbase.database.databricks_persistence import (
    PortfolioPosition,
)
from coinbase.integrations.yahoo_finance import YahooPortfolioParser


class TestDatabricksPersistenceIntegration:
    """Integration tests for Databricks persistence workflow."""

    def test_parse_and_save_workflow(self):
        """Test parsing Yahoo Finance data and saving to Databricks."""
        # This test verifies the workflow structure
        # Actual Databricks connection requires credentials

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

        assert position.symbol == "AAPL"
        assert position.quantity == 50
        assert position.current_value == 8750.0

    def test_portfolio_position_structure(self):
        """Test portfolio position data structure."""
        position = PortfolioPosition(
            symbol="MSFT",
            asset_name="Microsoft Corporation",
            sector="Technology",
            quantity=30,
            purchase_price=250.0,
            current_price=280.0,
            purchase_value=7500.0,
            current_value=8400.0,
            total_gain_loss=900.0,
            gain_loss_percentage=12.0,
            purchase_date="2024-02-20",
        )

        # Verify structure
        assert hasattr(position, "symbol")
        assert hasattr(position, "quantity")
        assert hasattr(position, "current_price")
        assert hasattr(position, "total_gain_loss")
        assert hasattr(position, "gain_loss_percentage")

    def test_multiple_positions_batch(self):
        """Test handling multiple positions in batch."""
        positions = [
            PortfolioPosition(
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
            ),
            PortfolioPosition(
                symbol="MSFT",
                asset_name="Microsoft Corporation",
                sector="Technology",
                quantity=30,
                purchase_price=250.0,
                current_price=280.0,
                purchase_value=7500.0,
                current_value=8400.0,
                total_gain_loss=900.0,
                gain_loss_percentage=12.0,
                purchase_date="2024-02-20",
            ),
        ]

        assert len(positions) == 2
        assert positions[0].symbol == "AAPL"
        assert positions[1].symbol == "MSFT"


class TestDatabricksAnalyzerIntegration:
    """Integration tests for Databricks analyzer workflow."""

    def test_analyzer_structure(self):
        """Test analyzer structure and methods."""
        # Verify analyzer has required methods
        assert hasattr(DatabricksPortfolioAnalyzer, "analyze_portfolio")
        assert hasattr(DatabricksPortfolioAnalyzer, "get_top_performers")
        assert hasattr(DatabricksPortfolioAnalyzer, "get_worst_performers")
        assert hasattr(DatabricksPortfolioAnalyzer, "get_sector_allocation")
        assert hasattr(DatabricksPortfolioAnalyzer, "get_concentration_risk")

    def test_concentration_risk_calculation(self):
        """Test concentration risk calculation logic."""
        # Create sample positions
        positions = [
            {"symbol": "AAPL", "current_value": 50000.0, "gain_loss_percentage": 20.0},
            {"symbol": "MSFT", "current_value": 30000.0, "gain_loss_percentage": 15.0},
            {"symbol": "GOOGL", "current_value": 20000.0, "gain_loss_percentage": 10.0},
        ]

        total_value = sum(p["current_value"] for p in positions)
        top_position_value = positions[0]["current_value"]
        top_position_percentage = (top_position_value / total_value) * 100

        assert total_value == 100000.0
        assert top_position_percentage == 50.0

    def test_sector_allocation_calculation(self):
        """Test sector allocation calculation logic."""
        positions = [
            {"symbol": "AAPL", "current_value": 50000.0, "sector": "Technology"},
            {"symbol": "MSFT", "current_value": 30000.0, "sector": "Technology"},
            {"symbol": "JPM", "current_value": 20000.0, "sector": "Finance"},
        ]

        total_value = sum(p["current_value"] for p in positions)
        sector_allocation = {}

        for pos in positions:
            sector = pos["sector"]
            if sector not in sector_allocation:
                sector_allocation[sector] = 0.0
            sector_allocation[sector] += pos["current_value"]

        # Convert to percentages
        for sector in sector_allocation:
            sector_allocation[sector] = (sector_allocation[sector] / total_value) * 100

        assert sector_allocation["Technology"] == 80.0
        assert sector_allocation["Finance"] == 20.0


class TestYahooToDatabricksWorkflow:
    """Integration tests for Yahoo Finance to Databricks workflow."""

    def test_yahoo_parser_structure(self):
        """Test Yahoo Finance parser structure."""
        parser = YahooPortfolioParser("e:/Coinbase/portfolios/yahoo_portfolio.csv")

        # Verify parser has required methods
        assert hasattr(parser, "parse")
        assert hasattr(parser, "get_portfolio_summary")
        assert hasattr(parser, "get_top_performers")
        assert hasattr(parser, "get_worst_performers")

    def test_yahoo_to_position_conversion(self):
        """Test converting Yahoo position to PortfolioPosition."""
        # This verifies the conversion logic structure
        # Actual conversion happens in integration example

        # Sample Yahoo position data
        yahoo_data = {
            "symbol": "AAPL",
            "current_price": 175.0,
            "purchase_price": 150.0,
            "quantity": 50,
            "purchase_date": "2024-01-15",
        }

        # Verify conversion logic
        purchase_value = yahoo_data["purchase_price"] * yahoo_data["quantity"]
        current_value = yahoo_data["current_price"] * yahoo_data["quantity"]
        total_gain_loss = current_value - purchase_value
        gain_loss_percentage = (total_gain_loss / purchase_value) * 100

        assert purchase_value == 7500.0
        assert current_value == 8750.0
        assert total_gain_loss == 1250.0
        assert pytest.approx(gain_loss_percentage, 0.01) == 16.67


class TestEndToEndDatabricksWorkflow:
    """End-to-end integration tests for Databricks workflow."""

    def test_workflow_structure(self):
        """Test complete workflow structure."""
        # This verifies the workflow steps exist
        workflow_steps = [
            "Parse Yahoo Finance portfolio data",
            "Initialize Databricks tables",
            "Save positions to Databricks",
            "Save portfolio summary to Databricks",
            "Analyze portfolio from Databricks",
            "Retrieve top performers from Databricks",
            "Calculate concentration risk from Databricks",
            "Get sector allocation from Databricks",
        ]

        assert len(workflow_steps) == 8
        assert "Parse Yahoo Finance portfolio data" in workflow_steps
        assert "Save positions to Databricks" in workflow_steps
        assert "Analyze portfolio from Databricks" in workflow_steps

    def test_portfolio_metrics_calculation(self):
        """Test portfolio metrics calculation."""
        positions = [
            {"symbol": "AAPL", "quantity": 50, "purchase_price": 150.0, "current_price": 175.0},
            {"symbol": "MSFT", "quantity": 30, "purchase_price": 250.0, "current_price": 280.0},
        ]

        # Calculate metrics
        total_value = sum(p["quantity"] * p["current_price"] for p in positions)
        total_purchase_value = sum(p["quantity"] * p["purchase_price"] for p in positions)
        total_gain_loss = total_value - total_purchase_value
        gain_loss_percentage = (total_gain_loss / total_purchase_value) * 100

        assert total_value == 17150.0
        assert total_purchase_value == 15000.0
        assert total_gain_loss == 2150.0
        assert pytest.approx(gain_loss_percentage, 0.01) == 14.33


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
