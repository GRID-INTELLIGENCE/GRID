"""
Coinbase Main Application
===========================
Main entry point for Coinbase crypto investment platform.

Features:
- Portfolio management
- Trading signals
- Fact-checking
- Revenue tracking
- Risk assessment
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .database.crypto_db import CryptoAsset, CryptoDatabase, PortfolioPosition, Transaction
from .features.fact_check import FactChecker
from .features.revenue import RevenueFeatures, TradingRecommendation

logger = logging.getLogger(__name__)


@dataclass
class CoinbaseConfig:
    """Coinbase configuration."""

    databricks_host: str
    databricks_http_path: str
    databricks_token: str


class CoinbaseApp:
    """
    Main Coinbase application for crypto investments.

    Privacy-first, security-first, revenue-focused.
    Minimal dependencies, maximum value.
    """

    def __init__(self, config: CoinbaseConfig):
        """
        Initialize Coinbase application.

        Args:
            config: CoinbaseConfig with Databricks credentials
        """
        self.config = config

        # Initialize database
        self.db = CryptoDatabase(
            databricks_config={
                "host": config.databricks_host,
                "http_path": config.databricks_http_path,
                "token": config.databricks_token,
            }
        )

        # Initialize revenue features
        self.revenue_features = RevenueFeatures(self.db)

        # Initialize fact-checker
        self.fact_checker = FactChecker()

        logger.info("Coinbase application initialized")

    def add_crypto_asset(
        self,
        symbol: str,
        name: str,
        asset_type: str,
        current_price: float,
        market_cap: float | None = None,
        volume_24h: float | None = None,
    ) -> None:
        """
        Add cryptocurrency asset.

        Args:
            symbol: Asset symbol (e.g., "BTC")
            name: Asset name (e.g., "Bitcoin")
            asset_type: Asset type (bitcoin, ethereum, stablecoin, etc.)
            current_price: Current price
            market_cap: Market capitalization
            volume_24h: 24-hour trading volume
        """
        from .database.crypto_db import CryptoAssetType

        # Map asset type string to enum
        type_map = {
            "bitcoin": CryptoAssetType.BITCOIN,
            "ethereum": CryptoAssetType.ETHEREUM,
            "stablecoin": CryptoAssetType.STABLECOIN,
            "altcoin": CryptoAssetType.ALTCOIN,
            "defi": CryptoAssetType.DEFI,
            "nft": CryptoAssetType.NFT,
        }

        asset = CryptoAsset(
            symbol=symbol,
            name=name,
            asset_type=type_map.get(asset_type, CryptoAssetType.ALTCOIN),
            current_price=current_price,
            market_cap=market_cap,
            volume_24h=volume_24h,
            last_updated=datetime.utcnow(),
        )

        self.db.upsert_crypto_asset(asset)
        logger.info(f"Asset added: {symbol}")

    def add_portfolio_position(
        self,
        user_id: str,
        asset_symbol: str,
        quantity: float,
        average_cost: float,
    ) -> None:
        """
        Add portfolio position.

        Args:
            user_id: User ID (will be hashed for privacy)
            asset_symbol: Asset symbol
            quantity: Quantity held
            average_cost: Average cost basis
        """
        user_id_hash = self.db.hash_user_id(user_id)
        current_price = self.db.get_asset_price(asset_symbol) or average_cost

        position = PortfolioPosition(
            user_id_hash=user_id_hash,
            asset_symbol=asset_symbol,
            quantity=quantity,
            average_cost=average_cost,
            current_value=quantity * current_price,
            unrealized_pnl=(current_price - average_cost) * quantity,
            last_updated=datetime.utcnow(),
        )

        self.db.upsert_portfolio_position(position)
        logger.info(f"Position added: {asset_symbol}")

    def analyze_portfolio(
        self,
        user_id: str,
    ) -> dict[str, Any]:
        """
        Analyze portfolio and provide recommendations.

        Args:
            user_id: User ID

        Returns:
            Portfolio analysis results
        """
        user_id_hash = self.db.hash_user_id(user_id)
        analysis = self.revenue_features.analyze_portfolio(user_id_hash)

        return {
            "total_value": analysis.total_value,
            "total_cost": analysis.total_cost,
            "total_pnl": analysis.total_pnl,
            "pnl_percentage": analysis.pnl_percentage,
            "best_performer": analysis.best_performer,
            "worst_performer": analysis.worst_performer,
            "risk_level": analysis.risk_level.value,
            "diversification_score": analysis.diversification_score,
            "recommendations": analysis.recommendations,
        }

    def get_trading_signal(
        self,
        asset_symbol: str,
    ) -> TradingRecommendation:
        """
        Get trading signal for an asset.

        Args:
            asset_symbol: Asset symbol

        Returns:
            Trading recommendation
        """
        return self.revenue_features.generate_trading_signal(asset_symbol)

    def verify_price(
        self,
        asset_symbol: str,
        reported_price: float,
        tolerance: float = 0.05,
    ) -> dict[str, Any]:
        """
        Verify price against multiple sources.

        Args:
            asset_symbol: Asset symbol
            reported_price: Price to verify
            tolerance: Acceptable deviation

        Returns:
            Verification result
        """
        result = self.fact_checker.verify_price(
            asset_symbol=asset_symbol,
            reported_price=reported_price,
            tolerance=tolerance,
        )

        return {
            "verified": result.verified,
            "consensus_price": result.consensus_value,
            "sources_checked": result.sources_checked,
            "sources_verified": result.sources_verified,
            "anomalies": result.anomalies,
            "recommendations": result.recommendations,
        }

    def calculate_revenue(
        self,
        user_id: str,
        days: int = 30,
    ) -> dict[str, Any]:
        """
        Calculate revenue over time period.

        Args:
            user_id: User ID
            days: Number of days

        Returns:
            Revenue statistics
        """
        user_id_hash = self.db.hash_user_id(user_id)
        return self.revenue_features.calculate_revenue(user_id_hash, days)

    def get_portfolio_value(
        self,
        user_id: str,
    ) -> float:
        """
        Get total portfolio value.

        Args:
            user_id: User ID

        Returns:
            Total portfolio value
        """
        user_id_hash = self.db.hash_user_id(user_id)
        return self.db.get_portfolio_value(user_id_hash)

    def add_transaction(
        self,
        user_id: str,
        asset_symbol: str,
        transaction_type: str,
        quantity: float,
        price: float,
        fee: float,
    ) -> None:
        """
        Add transaction record.

        Args:
            user_id: User ID
            asset_symbol: Asset symbol
            transaction_type: buy, sell, transfer_in, transfer_out
            quantity: Quantity
            price: Price
            fee: Transaction fee
        """
        import secrets

        from .database.crypto_db import TransactionType

        # Map transaction type
        type_map = {
            "buy": TransactionType.BUY,
            "sell": TransactionType.SELL,
            "transfer_in": TransactionType.TRANSFER_IN,
            "transfer_out": TransactionType.TRANSFER_OUT,
            "staking_reward": TransactionType.STAKING_REWARD,
        }

        transaction = Transaction(
            id=str(secrets.token_urlsafe(16)),
            user_id_hash=self.db.hash_user_id(user_id),
            asset_symbol=asset_symbol,
            transaction_type=type_map.get(transaction_type, TransactionType.BUY),
            quantity=quantity,
            price=price,
            fee=fee,
            timestamp=datetime.utcnow(),
        )

        self.db.add_transaction(transaction)
        logger.info(f"Transaction added: {transaction.id}")


def create_app() -> CoinbaseApp | None:
    """
    Create Coinbase application from environment variables.

    Returns:
        Initialized CoinbaseApp or None if credentials missing
    """
    config = CoinbaseConfig(
        databricks_host=os.getenv("DATABRICKS_HOST", ""),
        databricks_http_path=os.getenv("DATABRICKS_HTTP_PATH", ""),
        databricks_token=os.getenv("DATABRICKS_TOKEN", ""),
    )

    return CoinbaseApp(config)


# Example usage
def example_usage() -> None:
    """Example usage of Coinbase application."""

    # Create app from environment
    app = create_app()
    if app is None:
        print("Could not create app - missing Databricks credentials")
        return

    # Add crypto asset
    app.add_crypto_asset(
        symbol="BTC",
        name="Bitcoin",
        asset_type="bitcoin",
        current_price=50000.0,
        market_cap=1000000000000.0,
        volume_24h=30000000000.0,
    )

    # Add portfolio position
    app.add_portfolio_position(
        user_id="user123",
        asset_symbol="BTC",
        quantity=0.5,
        average_cost=45000.0,
    )

    # Analyze portfolio
    analysis = app.analyze_portfolio("user123")
    print(f"Portfolio Value: ${analysis['total_value']:,.2f}")
    print(f"PnL: {analysis['pnl_percentage']:.2f}%")
    print(f"Risk Level: {analysis['risk_level']}")
    print("\nRecommendations:")
    for rec in analysis["recommendations"]:
        print(f"  - {rec}")

    # Get trading signal
    signal = app.get_trading_signal("BTC")
    print(f"\nTrading Signal: {signal.signal.value}")
    print(f"Reasoning: {signal.reasoning}")

    # Verify price
    verification = app.verify_price("BTC", 50000.0)
    print(f"\nPrice Verified: {verification['verified']}")

    # Calculate revenue
    revenue = app.calculate_revenue("user123", days=30)
    print(f"\nRevenue (30 days): ${revenue['revenue']:,.2f}")


if __name__ == "__main__":
    example_usage()
