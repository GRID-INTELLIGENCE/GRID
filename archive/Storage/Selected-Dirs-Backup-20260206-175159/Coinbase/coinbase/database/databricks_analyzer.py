"""
Databricks Portfolio Analysis
==============================
Analyze portfolio data stored in Databricks.

Focus: Databricks as top priority for artifact creation
"""

import hashlib
import logging
from typing import Any

from ..infrastructure.databricks_connector import DatabricksConnector
from .databricks_persistence import DatabricksPortfolioPersistence

logger = logging.getLogger(__name__)


class DatabricksPortfolioAnalyzer:
    """
    Analyze portfolio data from Databricks.

    Provides analytics and insights from stored portfolio data.
    """

    def __init__(self, connector: DatabricksConnector | None = None):
        """
        Initialize analyzer.

        Args:
            connector: Databricks connector instance
        """
        self.connector = connector or DatabricksConnector()
        self.persistence = DatabricksPortfolioPersistence(self.connector)

    def analyze_portfolio(self, user_id: str) -> dict[str, Any]:
        """
        Analyze portfolio for user.

        Args:
            user_id: User ID (will be hashed)

        Returns:
            Portfolio analysis results
        """
        hashlib.sha256(user_id.encode()).hexdigest()

        # Get positions
        positions = self.persistence.get_positions(user_id)

        if not positions:
            return {
                "user_id": user_id,
                "total_positions": 0,
                "total_value": 0.0,
                "total_gain_loss": 0.0,
                "gain_loss_percentage": 0.0,
                "positions": [],
            }

        # Calculate metrics
        total_value = sum(p["current_value"] for p in positions)
        total_purchase_value = sum(p["purchase_value"] for p in positions)
        total_commission = sum(p["commission"] for p in positions)
        total_gain_loss = total_value - total_purchase_value - total_commission

        gain_loss_percentage = 0.0
        if total_purchase_value > 0:
            gain_loss_percentage = (total_gain_loss / total_purchase_value) * 100

        # Calculate position metrics
        for pos in positions:
            pos["gain_loss"] = pos["total_gain_loss"]
            pos["gain_loss_percentage"] = pos["gain_loss_percentage"]

        # Sort by performance
        sorted_positions = sorted(positions, key=lambda p: p["gain_loss_percentage"], reverse=True)

        return {
            "user_id": user_id,
            "total_positions": len(positions),
            "total_value": total_value,
            "total_purchase_value": total_purchase_value,
            "total_commission": total_commission,
            "total_gain_loss": total_gain_loss,
            "gain_loss_percentage": gain_loss_percentage,
            "positions": sorted_positions,
        }

    def get_top_performers(self, user_id: str, limit: int = 5) -> list[dict[str, Any]]:
        """
        Get top performing positions.

        Args:
            user_id: User ID
            limit: Number of positions to return

        Returns:
            List of top performing positions
        """
        analysis = self.analyze_portfolio(user_id)
        return analysis["positions"][:limit]  # type: ignore

    def get_worst_performers(self, user_id: str, limit: int = 5) -> list[dict[str, Any]]:
        """
        Get worst performing positions.

        Args:
            user_id: User ID
            limit: Number of positions to return

        Returns:
            List of worst performing positions
        """
        analysis = self.analyze_portfolio(user_id)
        return analysis["positions"][-limit:]  # type: ignore

    def get_sector_allocation(self, user_id: str) -> dict[str, float]:
        """
        Get portfolio sector allocation.

        Args:
            user_id: User ID

        Returns:
            Dictionary of sector -> percentage
        """
        analysis = self.analyze_portfolio(user_id)
        total_value = analysis["total_value"]

        if total_value == 0:
            return {}

        sector_allocation = {}

        for pos in analysis["positions"]:
            sector = pos.get("sector", "Unknown")
            sector_value = pos["current_value"]

            if sector not in sector_allocation:
                sector_allocation[sector] = 0.0

            sector_allocation[sector] += sector_value

        # Convert to percentages
        for sector in sector_allocation:
            sector_allocation[sector] = (sector_allocation[sector] / total_value) * 100

        return sector_allocation

    def get_concentration_risk(self, user_id: str) -> dict[str, Any]:
        """
        Calculate portfolio concentration risk.

        Args:
            user_id: User ID

        Returns:
            Concentration risk metrics
        """
        analysis = self.analyze_portfolio(user_id)
        positions = analysis["positions"]
        total_value = analysis["total_value"]

        if total_value == 0 or not positions:
            return {
                "risk_level": "UNKNOWN",
                "top_position_percentage": 0.0,
                "top_3_percentage": 0.0,
                "recommendation": "No data available",
            }

        # Calculate top position percentage
        top_position_value = positions[0]["current_value"]
        top_position_percentage = (top_position_value / total_value) * 100

        # Calculate top 3 positions percentage
        top_3_value = sum(p["current_value"] for p in positions[:3])
        top_3_percentage = (top_3_value / total_value) * 100

        # Determine risk level
        risk_level = "LOW"
        recommendation = "Well-diversified portfolio"

        if top_position_percentage > 50:
            risk_level = "HIGH"
            recommendation = "High concentration risk - diversify portfolio"
        elif top_position_percentage > 30:
            risk_level = "MEDIUM"
            recommendation = "Moderate concentration risk - consider diversification"

        return {
            "risk_level": risk_level,
            "top_position_percentage": top_position_percentage,
            "top_3_percentage": top_3_percentage,
            "recommendation": recommendation,
        }


# Example usage
def example_usage() -> None:
    """Example usage of DatabricksPortfolioAnalyzer."""
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

    # Initialize analyzer
    analyzer = DatabricksPortfolioAnalyzer()

    # Analyze portfolio
    analysis = analyzer.analyze_portfolio("user123")

    print("Portfolio Analysis")
    print("=" * 60)
    print(f"Total Positions: {analysis['total_positions']}")
    print(f"Total Value: ${analysis['total_value']:,.2f}")
    print(f"Total Gain/Loss: ${analysis['total_gain_loss']:,.2f}")
    print(f"Gain/Loss %: {analysis['gain_loss_percentage']:.2f}%")

    # Top performers
    print("\nTop Performers:")
    for pos in analyzer.get_top_performers("user123", 3):
        print(f"  {pos['symbol']}: {pos['gain_loss_percentage']:.2f}%")

    # Concentration risk
    risk = analyzer.get_concentration_risk("user123")
    print(f"\nRisk Level: {risk['risk_level']}")
    print(f"Recommendation: {risk['recommendation']}")


if __name__ == "__main__":
    example_usage()
