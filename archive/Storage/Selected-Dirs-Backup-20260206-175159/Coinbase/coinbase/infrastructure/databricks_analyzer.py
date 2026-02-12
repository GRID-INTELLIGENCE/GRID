"""
Databricks Analyzer
===================
Powerful data analysis infrastructure.

Reference: Compass - Points to data insights
"""

import hashlib
import logging
from typing import Any

from ..infrastructure.databricks_connector import DatabricksConnector

logger = logging.getLogger(__name__)


class DatabricksAnalyzer:
    """
    Powerful data analysis infrastructure.

    Uses Databricks connector for analytics.
    Like a Compass pointing to data insights.
    """

    def __init__(self, connector: DatabricksConnector | None = None):
        """
        Initialize analyzer.

        Args:
            connector: Databricks connector instance
        """
        self.connector = connector or DatabricksConnector()

    def analyze_portfolio(self, user_id: str) -> dict[str, Any]:
        """
        Analyze portfolio with Databricks.

        Args:
            user_id: User ID (will be hashed)

        Returns:
            Portfolio analysis results
        """
        user_id_hash = hashlib.sha256(user_id.encode()).hexdigest()

        try:
            # Query portfolio data
            query = """
                SELECT asset_symbol, quantity, average_cost
                FROM portfolio_positions
                WHERE user_id_hash = ?
                ORDER BY asset_symbol
            """

            results = self.connector.execute_query(query, (user_id_hash,))

            if not results:
                return {
                    "user_id": user_id,
                    "total_value": 0.0,
                    "total_cost": 0.0,
                    "pnl": 0.0,
                    "pnl_percentage": 0.0,
                    "position_count": 0,
                    "positions": [],
                }

            # Calculate metrics
            total_value = 0.0
            total_cost = 0.0
            positions = []

            for row in results:
                asset_symbol, quantity, average_cost = row
                current_price = 50000.0  # Placeholder - should fetch from market data

                position_value = quantity * current_price
                position_cost = quantity * average_cost
                position_pnl = position_value - position_cost

                total_value += position_value
                total_cost += position_cost

                positions.append(
                    {
                        "asset_symbol": asset_symbol,
                        "quantity": quantity,
                        "average_cost": average_cost,
                        "current_price": current_price,
                        "position_value": position_value,
                        "position_pnl": position_pnl,
                    }
                )

            pnl = total_value - total_cost
            pnl_percentage = (pnl / total_cost * 100) if total_cost > 0 else 0.0

            return {
                "user_id": user_id,
                "total_value": total_value,
                "total_cost": total_cost,
                "pnl": pnl,
                "pnl_percentage": pnl_percentage,
                "position_count": len(positions),
                "positions": positions,
            }

        except Exception as e:
            logger.error(f"Portfolio analysis failed: {e}")
            raise

    def get_price_history(self, asset_symbol: str, limit: int = 100) -> list[dict[str, Any]]:
        """
        Get price history for asset.

        Args:
            asset_symbol: Asset symbol
            limit: Max results

        Returns:
            Price history data
        """
        query = """
            SELECT symbol, price, volume, timestamp
            FROM price_history
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """

        results = self.connector.execute_query(query, (asset_symbol, limit))

        return [
            {"symbol": row[0], "price": row[1], "volume": row[2], "timestamp": row[3]}
            for row in results
            ] if results else []

    def calculate_moving_average(self, asset_symbol: str, window: int = 20) -> float | None:
        """
        Calculate moving average.

        Args:
            asset_symbol: Asset symbol
            window: Window size

        Returns:
            Moving average value
        """
        history = self.get_price_history(asset_symbol, limit=window)

        if len(history) < window:
            return None

        prices = [float(h["price"]) for h in history[:window]]
        return sum(prices) / len(prices)

    def detect_anomalies(self, asset_symbol: str, threshold: float = 0.10) -> list[dict[str, Any]]:
        """
        Detect price anomalies.

        Args:
            asset_symbol: Asset symbol
            threshold: Anomaly threshold

        Returns:
            List of detected anomalies
        """
        history = self.get_price_history(asset_symbol, limit=50)

        if len(history) < 10:
            return []

        anomalies = []
        prices = [h["price"] for h in history]

        for i in range(1, len(prices)):
            change = abs(prices[i] - prices[i - 1]) / prices[i - 1]

            if change >= threshold:
                anomalies.append(
                    {
                        "asset_symbol": asset_symbol,
                        "timestamp": history[i]["timestamp"],
                        "price": prices[i],
                        "previous_price": prices[i - 1],
                        "change": change,
                        "type": "spike" if prices[i] > prices[i - 1] else "drop",
                    }
                )

        return anomalies


# Example usage
def example_usage() -> None:
    """Example usage of DatabricksAnalyzer."""
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
        return

    # Initialize analyzer
    analyzer = DatabricksAnalyzer()

    # Analyze portfolio
    analysis = analyzer.analyze_portfolio("user123")
    print(f"Portfolio Value: ${analysis['total_value']:,.2f}")
    print(f"PnL: {analysis['pnl_percentage']:.2f}%")
    print(f"Positions: {analysis['position_count']}")


if __name__ == "__main__":
    example_usage()
