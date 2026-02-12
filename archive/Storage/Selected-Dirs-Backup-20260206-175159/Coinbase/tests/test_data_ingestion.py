"""
Data Ingestion Tests
====================
Complete test coverage for data ingestion module.
"""

from unittest.mock import patch

import pandas as pd
import pytest

from coinbase.ingestion.data_ingestion import (
    IngestionResult,
    PortfolioDataIngestion,
    ingest_portfolio_csv,
)


class TestPortfolioDataIngestion:
    """Tests for PortfolioDataIngestion class."""

    def test_initialization(self):
        """Test initialization."""
        ingestion = PortfolioDataIngestion()

        assert ingestion.persistence is not None
        assert ingestion.security is not None
        assert ingestion.audit_logger is not None

    def test_create_position_from_row(self):
        """Test creating position from CSV row."""
        ingestion = PortfolioDataIngestion()

        row = pd.Series(
            {
                "Symbol": "AAPL",
                "Current Price": 175.0,
                "Purchase Price": 150.0,
                "Quantity": 100.0,
                "Commission": 0.0,
                "Trade Date": "20240115",
                "High Limit": 200.0,
                "Low Limit": 100.0,
                "Comment": "Test comment",
                "Transaction Type": "BUY",
            }
        )

        position = ingestion._create_position_from_row(row, "hashed_user")

        assert position.symbol == "AAPL"
        assert position.quantity == 100.0
        assert position.purchase_price == 150.0
        assert position.current_price == 175.0
        assert position.purchase_value == 15000.0
        assert position.current_value == 17500.0
        assert position.total_gain_loss == 2500.0
        assert position.high_limit == 200.0
        assert position.low_limit == 100.0
        assert position.comment == "Test comment"
        assert position.transaction_type == "BUY"

    def test_parse_date_yyyymmdd(self):
        """Test parsing YYYYMMDD date format."""
        ingestion = PortfolioDataIngestion()

        result = ingestion._parse_date("20240115")
        assert result == "2024-01-15"

    def test_parse_date_standard(self):
        """Test parsing standard date format."""
        ingestion = PortfolioDataIngestion()

        result = ingestion._parse_date("2024-01-15")
        assert result == "2024-01-15"

    def test_parse_date_invalid(self):
        """Test parsing invalid date."""
        ingestion = PortfolioDataIngestion()

        result = ingestion._parse_date("invalid")
        # Should return today's date
        assert len(result) == 10

    def test_validate_position_success(self):
        """Test validation of valid position."""
        ingestion = PortfolioDataIngestion()

        from coinbase.database.databricks_persistence import PortfolioPosition

        position = PortfolioPosition(
            symbol="AAPL",
            asset_name="Apple Inc.",
            sector="Technology",
            quantity=100.0,
            purchase_price=150.0,
            current_price=175.0,
            purchase_value=15000.0,
            current_value=17500.0,
            total_gain_loss=2500.0,
            gain_loss_percentage=16.67,
            purchase_date="2024-01-15",
        )

        # Should not raise exception
        ingestion._validate_position(position)

    def test_validate_position_negative_quantity(self):
        """Test validation fails with negative quantity."""
        ingestion = PortfolioDataIngestion()

        from coinbase.database.databricks_persistence import PortfolioPosition

        position = PortfolioPosition(
            symbol="AAPL",
            asset_name="Apple Inc.",
            sector="Technology",
            quantity=-100.0,
            purchase_price=150.0,
            current_price=175.0,
            purchase_value=-15000.0,
            current_value=-17500.0,
            total_gain_loss=-2500.0,
            gain_loss_percentage=16.67,
            purchase_date="2024-01-15",
        )

        with pytest.raises(ValueError, match="Quantity cannot be negative"):
            ingestion._validate_position(position)

    def test_validate_position_value_inconsistency(self):
        """Test validation fails with value inconsistency."""
        ingestion = PortfolioDataIngestion()

        from coinbase.database.databricks_persistence import PortfolioPosition

        position = PortfolioPosition(
            symbol="AAPL",
            asset_name="Apple Inc.",
            sector="Technology",
            quantity=100.0,
            purchase_price=150.0,
            current_price=175.0,
            purchase_value=20000.0,  # Wrong value
            current_value=17500.0,
            total_gain_loss=2500.0,
            gain_loss_percentage=16.67,
            purchase_date="2024-01-15",
        )

        with pytest.raises(ValueError, match="Purchase value inconsistency"):
            ingestion._validate_position(position)


class TestIngestionResult:
    """Tests for IngestionResult dataclass."""

    def test_result_creation(self):
        """Test result creation."""
        result = IngestionResult(
            success=True,
            total_rows=10,
            processed_rows=10,
            failed_rows=0,
            duration_ms=100.0,
            errors=[],
            warnings=[],
        )

        assert result.success is True
        assert result.total_rows == 10
        assert result.processed_rows == 10
        assert result.failed_rows == 0
        assert result.duration_ms == 100.0


class TestIngestionIntegration:
    """Integration tests for data ingestion."""

    @pytest.fixture
    def sample_csv(self, tmp_path):
        """Create sample CSV file."""
        csv_path = tmp_path / "test_portfolio.csv"

        data = pd.DataFrame(
            {
                "Symbol": ["AAPL", "GOOG"],
                "Current Price": [175.0, 328.44],
                "Purchase Price": [150.0, 314.55],
                "Quantity": [100.0, 1.0],
                "Commission": [0.0, 0.0],
                "Trade Date": ["20240115", "20260107"],
                "High Limit": [200.0, None],
                "Low Limit": [100.0, None],
                "Comment": [None, "4ever"],
                "Transaction Type": [None, "BUY"],
            }
        )

        data.to_csv(csv_path, index=False)
        return csv_path

    def test_ingest_csv_success(self, sample_csv):
        """Test successful CSV ingestion."""
        ingestion = PortfolioDataIngestion()

        with patch.object(ingestion.persistence, "save_position"):
            result = ingestion.ingest_csv(
                csv_path=str(sample_csv), user_id="user123", skip_validation=False
            )

        assert result.success is True
        assert result.total_rows == 2
        assert result.processed_rows == 2
        assert result.failed_rows == 0
        assert result.duration_ms > 0

    def test_ingest_csv_with_validation_errors(self, sample_csv):
        """Test CSV ingestion with validation errors."""
        # Create CSV with invalid data
        data = pd.DataFrame(
            {
                "Symbol": ["AAPL"],
                "Current Price": [175.0],
                "Purchase Price": [150.0],
                "Quantity": [-100.0],  # Invalid
                "Commission": [0.0],
                "Trade Date": ["20240115"],
                "High Limit": [None],
                "Low Limit": [None],
                "Comment": [None],
                "Transaction Type": [None],
            }
        )

        import tempfile

        csv_path = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
        data.to_csv(csv_path.name, index=False)
        csv_path.close()

        ingestion = PortfolioDataIngestion()

        result = ingestion.ingest_csv(
            csv_path=csv_path.name, user_id="user123", skip_validation=False
        )

        assert result.success is False
        assert result.failed_rows == 1
        assert len(result.errors) > 0


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_ingest_portfolio_csv(self):
        """Test convenience function."""
        import os
        import tempfile

        # Create sample CSV
        data = pd.DataFrame(
            {
                "Symbol": ["AAPL"],
                "Current Price": [175.0],
                "Purchase Price": [150.0],
                "Quantity": [100.0],
                "Commission": [0.0],
                "Trade Date": ["20240115"],
                "High Limit": [None],
                "Low Limit": [None],
                "Comment": [None],
                "Transaction Type": [None],
            }
        )

        csv_path = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
        data.to_csv(csv_path.name, index=False)
        csv_path.close()

        with patch("coinbase.ingestion.data_ingestion.PortfolioDataIngestion") as mock_ingestion:
            mock_result = IngestionResult(
                success=True,
                total_rows=1,
                processed_rows=1,
                failed_rows=0,
                duration_ms=100.0,
                errors=[],
                warnings=[],
            )
            mock_ingestion.return_value.ingest_csv.return_value = mock_result

            result = ingest_portfolio_csv(
                csv_path=csv_path.name, user_id="user123", skip_validation=False
            )

        assert result.success is True

        # Cleanup
        os.unlink(csv_path.name)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
