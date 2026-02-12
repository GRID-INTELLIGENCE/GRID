"""
Databricks Portfolio Persistence
================================
Store and retrieve portfolio data in Databricks.

Focus: Databricks as top priority for artifact creation
"""

import hashlib
import logging
from dataclasses import dataclass
from typing import Any

from ..infrastructure.databricks_connector import DatabricksConnector
from .databricks_schema import ALL_SCHEMAS, MERGE_PORTFOLIO_POSITION, MERGE_PORTFOLIO_SUMMARY

logger = logging.getLogger(__name__)


@dataclass
class PortfolioPosition:
    """Portfolio position data."""

    symbol: str
    asset_name: str
    sector: str
    quantity: float
    purchase_price: float
    current_price: float
    purchase_value: float
    current_value: float
    total_gain_loss: float
    gain_loss_percentage: float
    purchase_date: str
    commission: float = 0.0
    high_limit: float | None = None
    low_limit: float | None = None
    comment: str | None = None
    transaction_type: str | None = None


class DatabricksPortfolioPersistence:
    """
    Portfolio persistence layer for Databricks.

    Stores and retrieves portfolio data with privacy-first design.
    """

    def __init__(self, connector: DatabricksConnector | None = None):
        """
        Initialize persistence layer.

        Args:
            connector: Databricks connector instance
        """
        self.connector = connector or DatabricksConnector()
        self._initialize_tables()

    def _initialize_tables(self) -> None:
        """Initialize Databricks tables."""
        try:
            with self.connector.connect() as conn:
                cursor = conn.cursor()

                # Create all tables
                for schema_ddl in ALL_SCHEMAS:
                    cursor.execute(schema_ddl)

                conn.commit()
                logger.info("Databricks tables initialized")

        except Exception as e:
            logger.error(f"Failed to initialize tables: {e}")
            raise

    def save_position(self, user_id: str, position: PortfolioPosition) -> None:
        """
        Save or update portfolio position.

        Args:
            user_id: User ID (will be hashed)
            position: Portfolio position data
        """
        user_id_hash = hashlib.sha256(user_id.encode()).hexdigest()

        try:
            with self.connector.connect() as conn:
                cursor = conn.cursor()

                # Use MERGE for upsert
                cursor.execute(
                    MERGE_PORTFOLIO_POSITION,
                    (
                        user_id_hash,
                        position.symbol,
                        position.asset_name,
                        position.sector,
                        position.quantity,
                        position.purchase_price,
                        position.current_price,
                        position.purchase_value,
                        position.current_value,
                        position.total_gain_loss,
                        position.gain_loss_percentage,
                        position.purchase_date,
                        position.commission,
                        position.high_limit,
                        position.low_limit,
                        position.comment,
                        position.transaction_type,
                    ),
                )

                conn.commit()
                logger.info(f"Saved position: {position.symbol}")

        except Exception as e:
            logger.error(f"Failed to save position: {e}")
            raise

    def save_positions_batch(self, user_id: str, positions: list[PortfolioPosition]) -> None:
        """
        Save multiple positions in batch.

        Args:
            user_id: User ID (will be hashed)
            positions: List of portfolio positions
        """
        for position in positions:
            self.save_position(user_id, position)

    def save_portfolio_summary(self, user_id: str, summary: dict[str, Any]) -> None:
        """
        Save portfolio summary.

        Args:
            user_id: User ID (will be hashed)
            summary: Portfolio summary data
        """
        user_id_hash = hashlib.sha256(user_id.encode()).hexdigest()

        try:
            with self.connector.connect() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    MERGE_PORTFOLIO_SUMMARY,
                    (
                        user_id_hash,
                        summary.get("total_positions", 0),
                        summary.get("total_value", 0.0),
                        summary.get("total_purchase_value", 0.0),
                        summary.get("total_commission", 0.0),
                        summary.get("total_gain_loss", 0.0),
                        summary.get("gain_loss_percentage", 0.0),
                    ),
                )

                conn.commit()
                logger.info("Saved portfolio summary for user")

        except Exception as e:
            logger.error(f"Failed to save summary: {e}")
            raise

    def get_positions(self, user_id: str) -> list[dict[str, Any]]:
        """
        Get all positions for user.

        Args:
            user_id: User ID

        Returns:
            List of position dictionaries
        """
        user_id_hash = hashlib.sha256(user_id.encode()).hexdigest()

        query = """
            SELECT symbol, asset_name, sector, quantity, purchase_price,
                   current_price, purchase_value, current_value, total_gain_loss,
                   gain_loss_percentage, purchase_date, commission, high_limit,
                   low_limit, comment, transaction_type
            FROM portfolio_positions
            WHERE user_id_hash = ?
            ORDER BY symbol
        """

        try:
            with self.connector.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (user_id_hash,))

                results = cursor.fetchall()

                positions = []
                for row in results:
                    positions.append(
                        {
                            "symbol": row[0],
                            "asset_name": row[1],
                            "sector": row[2],
                            "quantity": row[3],
                            "purchase_price": row[4],
                            "current_price": row[5],
                            "purchase_value": row[6],
                            "current_value": row[7],
                            "total_gain_loss": row[8],
                            "gain_loss_percentage": row[9],
                            "purchase_date": row[10],
                            "commission": row[11],
                            "high_limit": row[12],
                            "low_limit": row[13],
                            "comment": row[14],
                            "transaction_type": row[15],
                        }
                    )

                return positions

        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise

    def get_portfolio_summary(self, user_id: str) -> dict[str, Any] | None:
        """
        Get portfolio summary for user.

        Args:
            user_id: User ID

        Returns:
            Portfolio summary dictionary or None
        """
        user_id_hash = hashlib.sha256(user_id.encode()).hexdigest()

        query = """
            SELECT total_positions, total_value, total_purchase_value,
                   total_commission, total_gain_loss, gain_loss_percentage
            FROM portfolio_summary
            WHERE user_id_hash = ?
        """

        try:
            with self.connector.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (user_id_hash,))

                result = cursor.fetchone()

                if result:
                    return {
                        "total_positions": result[0],
                        "total_value": result[1],
                        "total_purchase_value": result[2],
                        "total_commission": result[3],
                        "total_gain_loss": result[4],
                        "gain_loss_percentage": result[5],
                    }

                return None

        except Exception as e:
            logger.error(f"Failed to get summary: {e}")
            raise


# Example usage
def example_usage() -> None:
    """Example usage of DatabricksPortfolioPersistence."""
    import os

    # Check for credentials
    if not all(
        [
            os.getenv("DATABRICKS_HOST"),
            os.getenv("DATABRICKS_HTTP_PATH"),
            os.getenv("DATABRICKS_TOKEN"),
        ]
    ):
        print("⚠ Databricks credentials not found")
        print("Set DATABRICKS_HOST, DATABRICKS_HTTP_PATH, DATABRICKS_TOKEN")
        return

    # Initialize persistence
    persistence = DatabricksPortfolioPersistence()

    # Create position
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

    # Save position
    persistence.save_position("user123", position)
    print("✓ Position saved")

    # Get positions
    positions = persistence.get_positions("user123")
    print(f"✓ Retrieved {len(positions)} positions")


if __name__ == "__main__":
    example_usage()
