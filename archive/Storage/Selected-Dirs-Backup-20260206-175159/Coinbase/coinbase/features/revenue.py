"""
Coinbase Revenue Features
==========================
Revenue-generating crypto/investment features built on crypto_db.

Features:
- Portfolio analysis and optimization
- Price tracking and alerts
- Sentiment-based trading signals
- Risk assessment and management
- Revenue calculation and reporting
"""

import logging
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from ..database.crypto_db import CryptoDatabase

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk levels for investments."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class TradingSignal(Enum):
    """Trading signals."""

    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


@dataclass
class PortfolioAnalysis:
    """Portfolio analysis results."""

    total_value: float
    total_cost: float
    total_pnl: float
    pnl_percentage: float
    best_performer: dict[str, Any]
    worst_performer: dict[str, Any]
    risk_level: RiskLevel
    diversification_score: float
    recommendations: list[str]


@dataclass
class PriceAlert:
    """Price alert configuration."""

    asset_symbol: str
    target_price: float
    alert_type: str  # "above", "below"
    triggered: bool = False
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TradingRecommendation:
    """Trading recommendation."""

    asset_symbol: str
    signal: TradingSignal
    confidence: float
    reasoning: str
    target_price: float | None = None
    stop_loss: float | None = None


class RevenueFeatures:
    """
    Revenue-generating features for crypto investments.

    Built on crypto_db with minimal dependencies.
    Focused on actionable insights for revenue generation.
    """

    def __init__(self, db: CryptoDatabase):
        """
        Initialize revenue features.

        Args:
            db: CryptoDatabase instance
        """
        self.db = db

    def analyze_portfolio(
        self,
        user_id_hash: str,
    ) -> PortfolioAnalysis:
        """
        Analyze portfolio performance and provide recommendations.

        Args:
            user_id_hash: Hashed user ID

        Returns:
            PortfolioAnalysis with insights
        """
        # Get all positions for user
        with self.db.session() as cursor:
            cursor.execute(
                """
                SELECT asset_symbol, quantity, average_cost, current_value, unrealized_pnl
                FROM portfolio_positions
                WHERE user_id_hash = ?
                """,
                (user_id_hash,),
            )
            positions = cursor.fetchall()

        if not positions:
            return PortfolioAnalysis(
                total_value=0.0,
                total_cost=0.0,
                total_pnl=0.0,
                pnl_percentage=0.0,
                best_performer={},
                worst_performer={},
                risk_level=RiskLevel.LOW,
                diversification_score=0.0,
                recommendations=["No positions found"],
            )

        # Calculate portfolio metrics
        total_value = sum(pos[3] for pos in positions)
        total_cost = sum(pos[1] * pos[2] for pos in positions)
        total_pnl = sum(pos[4] for pos in positions)
        pnl_percentage = (total_pnl / total_cost * 100) if total_cost > 0 else 0.0

        # Find best and worst performers
        performers = [
            {
                "symbol": pos[0],
                "pnl": pos[4],
                "pnl_pct": (pos[4] / (pos[1] * pos[2]) * 100) if (pos[1] * pos[2]) > 0 else 0.0,
            }
            for pos in positions
        ]
        best_performer = max(performers, key=lambda x: x["pnl_pct"])
        worst_performer = min(performers, key=lambda x: x["pnl_pct"])

        # Calculate risk level
        volatility = (
            statistics.stdev([p["pnl_pct"] for p in performers]) if len(performers) > 1 else 0.0
        )
        if volatility < 5.0:
            risk_level = RiskLevel.LOW
        elif volatility < 15.0:
            risk_level = RiskLevel.MEDIUM
        elif volatility < 30.0:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.EXTREME

        # Calculate diversification score
        unique_symbols = len(set(pos[0] for pos in positions))
        diversification_score = min(unique_symbols / 10.0 * 100, 100.0)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            total_value,
            pnl_percentage,
            risk_level,
            diversification_score,
            best_performer,
            worst_performer,
        )

        return PortfolioAnalysis(
            total_value=total_value,
            total_cost=total_cost,
            total_pnl=total_pnl,
            pnl_percentage=pnl_percentage,
            best_performer=best_performer,
            worst_performer=worst_performer,
            risk_level=risk_level,
            diversification_score=diversification_score,
            recommendations=recommendations,
        )

    def _generate_recommendations(
        self,
        total_value: float,
        pnl_percentage: float,
        risk_level: RiskLevel,
        diversification_score: float,
        best_performer: dict[str, Any],
        worst_performer: dict[str, Any],
    ) -> list[str]:
        """Generate portfolio recommendations."""
        recommendations = []

        if pnl_percentage > 20.0:
            recommendations.append(
                "Strong performance: Consider taking profits on high-gain positions"
            )
        elif pnl_percentage < -10.0:
            recommendations.append(
                "Underperformance: Review portfolio allocation and consider rebalancing"
            )

        if risk_level == RiskLevel.EXTREME:
            recommendations.append("High risk: Consider reducing exposure to volatile assets")
        elif risk_level == RiskLevel.LOW and diversification_score < 50.0:
            recommendations.append(
                "Low risk but low diversification: Consider adding more asset types"
            )

        if diversification_score < 30.0:
            recommendations.append("Poor diversification: Add 3-5 different assets to reduce risk")

        if best_performer["pnl_pct"] > 50.0:
            recommendations.append(
                f"Strong performer: {best_performer['symbol']} - Consider taking partial profits"
            )

        if worst_performer["pnl_pct"] < -20.0:
            recommendations.append(
                f"Underperformer: {worst_performer['symbol']} - Consider reducing exposure"
            )

        return recommendations

    def create_price_alert(
        self,
        asset_symbol: str,
        target_price: float,
        alert_type: str = "above",
    ) -> PriceAlert:
        """
        Create price alert for revenue opportunities.

        Args:
            asset_symbol: Asset symbol
            target_price: Target price
            alert_type: "above" or "below"

        Returns:
            PriceAlert configuration
        """
        return PriceAlert(
            asset_symbol=asset_symbol,
            target_price=target_price,
            alert_type=alert_type,
            created_at=datetime.utcnow(),
        )

    def check_price_alerts(
        self,
        alerts: list[PriceAlert],
    ) -> list[PriceAlert]:
        """
        Check which price alerts have been triggered.

        Args:
            alerts: List of price alerts

        Returns:
            List of triggered alerts
        """
        triggered = []

        for alert in alerts:
            current_price = self.db.get_asset_price(alert.asset_symbol)
            if current_price is None:
                continue

            if alert.alert_type == "above" and current_price >= alert.target_price:
                alert.triggered = True
                triggered.append(alert)
            elif alert.alert_type == "below" and current_price <= alert.target_price:
                alert.triggered = True
                triggered.append(alert)

        return triggered

    def generate_trading_signal(
        self,
        asset_symbol: str,
    ) -> TradingRecommendation:
        """
        Generate trading signal based on sentiment and price data.

        Args:
            asset_symbol: Asset symbol

        Returns:
            TradingRecommendation with signal and reasoning
        """
        # Get sentiment history
        sentiment_history = self.db.get_sentiment_history(asset_symbol, limit=10)

        if not sentiment_history:
            return TradingRecommendation(
                asset_symbol=asset_symbol,
                signal=TradingSignal.HOLD,
                confidence=0.5,
                reasoning="Insufficient data for signal generation",
            )

        # Calculate average sentiment
        avg_sentiment = statistics.mean([s["sentiment_score"] for s in sentiment_history])

        # Get price history
        price_history = self.db.get_price_history(asset_symbol, limit=20)

        if len(price_history) < 5:
            return TradingRecommendation(
                asset_symbol=asset_symbol,
                signal=TradingSignal.HOLD,
                confidence=0.5,
                reasoning="Insufficient price history",
            )

        # Calculate price trend
        recent_prices = [p["price"] for p in price_history[:5]]
        older_prices = [p["price"] for p in price_history[5:10]]

        avg_recent = statistics.mean(recent_prices)
        avg_older = statistics.mean(older_prices)

        price_change_pct = ((avg_recent - avg_older) / avg_older * 100) if avg_older > 0 else 0.0

        # Generate signal
        signal, confidence, reasoning = self._calculate_signal(
            avg_sentiment,
            price_change_pct,
        )

        # Get current price for targets
        current_price = self.db.get_asset_price(asset_symbol)

        return TradingRecommendation(
            asset_symbol=asset_symbol,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
            target_price=(
                current_price * 1.05  # type: ignore
                if signal in [TradingSignal.BUY, TradingSignal.STRONG_BUY]
                else None
            ),
            stop_loss=(
                current_price * 0.95  # type: ignore
                if signal in [TradingSignal.BUY, TradingSignal.STRONG_BUY]
                else None
            ),
        )

    def _calculate_signal(
        self,
        sentiment_score: float,
        price_change_pct: float,
    ) -> tuple[TradingSignal, float, str]:
        """Calculate trading signal from sentiment and price data."""
        # Strong buy: High positive sentiment + price increase
        if sentiment_score > 0.5 and price_change_pct > 2.0:
            return (
                TradingSignal.STRONG_BUY,
                0.8,
                f"Strong positive sentiment ({sentiment_score:.2f}) and price momentum ({price_change_pct:.2f}%)",
            )

        # Buy: Positive sentiment + moderate price increase
        if sentiment_score > 0.3 and price_change_pct > 0.0:
            return (
                TradingSignal.BUY,
                0.7,
                f"Positive sentiment ({sentiment_score:.2f}) and upward trend ({price_change_pct:.2f}%)",
            )

        # Strong sell: High negative sentiment + price decrease
        if sentiment_score < -0.5 and price_change_pct < -2.0:
            return (
                TradingSignal.STRONG_SELL,
                0.8,
                f"Strong negative sentiment ({sentiment_score:.2f}) and price decline ({price_change_pct:.2f}%)",
            )

        # Sell: Negative sentiment + price decrease
        if sentiment_score < -0.3 and price_change_pct < 0.0:
            return (
                TradingSignal.SELL,
                0.7,
                f"Negative sentiment ({sentiment_score:.2f}) and downward trend ({price_change_pct:.2f}%)",
            )

        # Hold: Mixed signals
        return (
            TradingSignal.HOLD,
            0.5,
            f"Mixed signals: sentiment={sentiment_score:.2f}, price_change={price_change_pct:.2f}%",
        )

    def calculate_revenue(
        self,
        user_id_hash: str,
        days: int = 30,
    ) -> dict[str, Any]:
        """
        Calculate revenue from portfolio over time period.

        Args:
            user_id_hash: Hashed user ID
            days: Number of days to analyze

        Returns:
            Revenue statistics
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        with self.db.session() as cursor:
            # Get transactions in period
            cursor.execute(
                """
                SELECT asset_symbol, transaction_type, quantity, price, fee, timestamp
                FROM transactions
                WHERE user_id_hash = ? AND timestamp >= ?
                ORDER BY timestamp ASC
                """,
                (user_id_hash, start_date),
            )
            transactions = cursor.fetchall()

        if not transactions:
            return {
                "period_days": days,
                "total_transactions": 0,
                "total_fees": 0.0,
                "revenue": 0.0,
                "revenue_rate": 0.0,
            }

        # Calculate revenue
        total_fees = sum(tx[4] for tx in transactions)

        # Get current portfolio value
        current_value = self.db.get_portfolio_value(user_id_hash)

        # Calculate revenue rate (daily)
        revenue_rate = current_value / days if days > 0 else 0.0

        return {
            "period_days": days,
            "total_transactions": len(transactions),
            "total_fees": total_fees,
            "revenue": current_value,
            "revenue_rate": revenue_rate,
        }


# Example usage
def example_usage() -> None:
    """Example usage of RevenueFeatures."""
    import os

    # Initialize database
    db = CryptoDatabase(
        databricks_config={
            "host": os.getenv("DATABRICKS_HOST") or "",
            "http_path": os.getenv("DATABRICKS_HTTP_PATH") or "",
            "token": os.getenv("DATABRICKS_TOKEN") or "",
        }
    )

    # Initialize revenue features
    features = RevenueFeatures(db)

    # Hash user ID
    user_id_hash = db.hash_user_id("user123")

    # Analyze portfolio
    analysis = features.analyze_portfolio(user_id_hash)
    print(f"Portfolio Value: ${analysis.total_value:,.2f}")
    print(f"PnL: {analysis.pnl_percentage:.2f}%")
    print(f"Risk Level: {analysis.risk_level.value}")
    print(f"Diversification: {analysis.diversification_score:.1f}%")
    print("\nRecommendations:")
    for rec in analysis.recommendations:
        print(f"  - {rec}")

    # Create price alert
    alert = features.create_price_alert("BTC", target_price=52000.0, alert_type="above")
    triggered = features.check_price_alerts([alert])
    print(f"\nPrice Alerts Triggered: {len(triggered)}")

    # Generate trading signal
    signal = features.generate_trading_signal("BTC")
    print(f"\nTrading Signal: {signal.signal.value}")
    print(f"Confidence: {signal.confidence:.2f}")
    print(f"Reasoning: {signal.reasoning}")
    if signal.target_price:
        print(f"Target Price: ${signal.target_price:,.2f}")
    if signal.stop_loss:
        print(f"Stop Loss: ${signal.stop_loss:,.2f}")

    # Calculate revenue
    revenue = features.calculate_revenue(user_id_hash, days=30)
    print(f"\nRevenue (30 days): ${revenue['revenue']:,.2f}")
    print(f"Daily Rate: ${revenue['revenue_rate']:,.2f}/day")


if __name__ == "__main__":
    example_usage()
