"""
Yahoo Finance Integration
==========================
Parse and analyze Yahoo Finance portfolio data.

Quality Focus: Practical relevance, accuracy, precision with real data
"""

import csv
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class YahooPosition:
    """Yahoo Finance position data."""

    symbol: str
    current_price: float
    purchase_price: float
    quantity: float
    purchase_date: str
    commission: float = 0.0
    high_limit: float | None = None
    low_limit: float | None = None
    comment: str | None = None
    transaction_type: str | None = None

    @property
    def current_value(self) -> float:
        """Calculate current value."""
        return self.current_price * self.quantity

    @property
    def purchase_value(self) -> float:
        """Calculate purchase value."""
        return self.purchase_price * self.quantity

    @property
    def total_gain_loss(self) -> float:
        """Calculate total gain/loss."""
        return self.current_value - self.purchase_value - self.commission

    @property
    def gain_loss_percentage(self) -> float:
        """Calculate gain/loss percentage."""
        if self.purchase_value == 0:
            return 0.0
        return (self.total_gain_loss / self.purchase_value) * 100


class YahooPortfolioParser:
    """Parse Yahoo Finance portfolio CSV data."""

    def __init__(self, csv_path: str):
        """
        Initialize parser.

        Args:
            csv_path: Path to Yahoo Finance CSV file
        """
        self.csv_path = csv_path
        self.positions: list[YahooPosition] = []

    def parse(self) -> list[YahooPosition]:
        """
        Parse Yahoo Finance CSV file.

        Returns:
            List of YahooPosition objects
        """
        positions = []

        try:
            with open(self.csv_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row in reader:
                    # Skip empty rows
                    if not row.get("Symbol"):
                        continue

                    # Parse numeric values
                    current_price = self._parse_float(row.get("Current Price", "0"))
                    purchase_price = self._parse_float(row.get("Purchase Price", "0"))
                    quantity = self._parse_float(row.get("Quantity", "0"))
                    commission = self._parse_float(row.get("Commission", "0"))
                    high_limit = self._parse_float(row.get("High Limit", ""))
                    low_limit = self._parse_float(row.get("Low Limit", ""))

                    # Create position
                    position = YahooPosition(
                        symbol=row["Symbol"],
                        current_price=current_price,
                        purchase_price=purchase_price,
                        quantity=quantity,
                        purchase_date=row.get("Trade Date", ""),
                        commission=commission,
                        high_limit=high_limit if high_limit else None,
                        low_limit=low_limit if low_limit else None,
                        comment=row.get("Comment", ""),
                        transaction_type=row.get("Transaction Type", ""),
                    )

                    # Only include positions with quantity > 0
                    if position.quantity > 0:
                        positions.append(position)

            self.positions = positions
            logger.info(f"Parsed {len(positions)} positions from {self.csv_path}")

            return positions

        except Exception as e:
            logger.error(f"Error parsing CSV: {e}")
            raise

    def _parse_float(self, value: str) -> float:
        """
        Parse float from string.

        Args:
            value: String value

        Returns:
            Float value
        """
        try:
            return float(value) if value else 0.0
        except (ValueError, TypeError):
            return 0.0

    def get_portfolio_summary(self) -> dict[str, Any]:
        """
        Get portfolio summary.

        Returns:
            Portfolio summary dictionary
        """
        if not self.positions:
            return {
                "total_positions": 0,
                "total_value": 0.0,
                "total_purchase_value": 0.0,
                "total_gain_loss": 0.0,
                "gain_loss_percentage": 0.0,
            }

        total_value = sum(p.current_value for p in self.positions)
        total_purchase_value = sum(p.purchase_value for p in self.positions)
        total_commission = sum(p.commission for p in self.positions)
        total_gain_loss = total_value - total_purchase_value - total_commission

        gain_loss_percentage = 0.0
        if total_purchase_value > 0:
            gain_loss_percentage = (total_gain_loss / total_purchase_value) * 100

        return {
            "total_positions": len(self.positions),
            "total_value": total_value,
            "total_purchase_value": total_purchase_value,
            "total_commission": total_commission,
            "total_gain_loss": total_gain_loss,
            "gain_loss_percentage": gain_loss_percentage,
        }

    def get_top_performers(self, limit: int = 5) -> list[YahooPosition]:
        """
        Get top performing positions.

        Args:
            limit: Number of positions to return

        Returns:
            List of top performing positions
        """
        sorted_positions = sorted(
            self.positions, key=lambda p: p.gain_loss_percentage, reverse=True
        )
        return sorted_positions[:limit]

    def get_worst_performers(self, limit: int = 5) -> list[YahooPosition]:
        """
        Get worst performing positions.

        Args:
            limit: Number of positions to return

        Returns:
            List of worst performing positions
        """
        sorted_positions = sorted(self.positions, key=lambda p: p.gain_loss_percentage)
        return sorted_positions[:limit]


# Example usage
def example_usage() -> None:
    """Example usage of YahooPortfolioParser."""
    import os
    from pathlib import Path

    # Get portfolio path from environment or use default relative to project
    portfolio_path = os.environ.get("COINBASE_PORTFOLIO_PATH")
    if not portfolio_path:
        # Auto-detect project root
        project_root = os.environ.get("COINBASE_PROJECT_ROOT")
        if project_root:
            portfolio_path = str(Path(project_root) / "portfolios" / "yahoo_portfolio.csv")
        else:
            # Fallback to relative path from current working directory
            portfolio_path = str(Path.cwd() / "portfolios" / "yahoo_portfolio.csv")

    parser = YahooPortfolioParser(str(portfolio_path))

    # Parse portfolio
    parser.parse()

    # Get summary
    summary = parser.get_portfolio_summary()

    print("Portfolio Summary")
    print("=" * 60)
    print(f"Total Positions: {summary['total_positions']}")
    print(f"Total Value: ${summary['total_value']:,.2f}")
    print(f"Total Purchase Value: ${summary['total_purchase_value']:,.2f}")
    print(f"Total Gain/Loss: ${summary['total_gain_loss']:,.2f}")
    print(f"Gain/Loss %: {summary['gain_loss_percentage']:.2f}%")
    print()

    # Top performers
    print("Top Performers")
    print("-" * 60)
    for pos in parser.get_top_performers(3):
        print(f"{pos.symbol}: {pos.gain_loss_percentage:.2f}% | ${pos.total_gain_loss:,.2f}")

    print()

    # Worst performers
    print("Worst Performers")
    print("-" * 60)
    for pos in parser.get_worst_performers(3):
        print(f"{pos.symbol}: {pos.gain_loss_percentage:.2f}% | ${pos.total_gain_loss:,.2f}")


if __name__ == "__main__":
    example_usage()
