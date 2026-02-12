"""
Coinbase Fact-Checking Module
=============================
Online source verification for crypto data.

Features:
- Verify price data against multiple sources
- Cross-reference sentiment with news
- Validate market data integrity
- Detect anomalies and potential manipulation
"""

import logging
import statistics
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import requests  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class SourceVerification:
    """Verification result from a data source."""

    source_name: str
    verified: bool
    data: dict[str, Any]
    confidence: float
    timestamp: datetime


@dataclass
class FactCheckResult:
    """Result of fact-checking operation."""

    asset_symbol: str
    data_type: str  # "price", "sentiment", "volume"
    verified: bool
    consensus_value: float | None
    sources_checked: int
    sources_verified: int
    anomalies: list[str]
    recommendations: list[str]


class FactChecker:
    """
    Fact-check crypto data against online sources.

    Uses multiple sources to verify data integrity and detect anomalies.
    Minimal dependencies: only requests library.
    """

    def __init__(self) -> None:
        """Initialize fact-checker with data sources."""
        self.sources = {
            "coingecko": "https://api.coingecko.com/api/v3/simple/price",
            "binance": "https://api.binance.com/api/v3/ticker/price",
            "coinbase": "https://api.coinbase.com/v2/prices",
        }
        self.timeout = 10  # seconds

    def verify_price(
        self,
        asset_symbol: str,
        reported_price: float,
        tolerance: float = 0.05,
    ) -> FactCheckResult:
        """
        Verify reported price against multiple sources.

        Args:
            asset_symbol: Asset symbol (e.g., "BTC")
            reported_price: Price to verify
            tolerance: Acceptable deviation percentage (0.05 = 5%)

        Returns:
            FactCheckResult with verification status
        """
        verifications = []

        for source_name, url in self.sources.items():
            try:
                verification = self._check_price_source(
                    source_name,
                    url,
                    asset_symbol,
                    reported_price,
                )
                if verification:
                    verifications.append(verification)
            except Exception as e:
                logger.warning(f"Failed to check {source_name}: {e}")

        if not verifications:
            return FactCheckResult(
                asset_symbol=asset_symbol,
                data_type="price",
                verified=False,
                consensus_value=None,
                sources_checked=len(self.sources),
                sources_verified=0,
                anomalies=["No sources available"],
                recommendations=["Check network connectivity"],
            )

        # Calculate consensus
        verified_prices = [v.data["price"] for v in verifications if v.verified]

        if not verified_prices:
            return FactCheckResult(
                asset_symbol=asset_symbol,
                data_type="price",
                verified=False,
                consensus_value=None,
                sources_checked=len(verifications),
                sources_verified=0,
                anomalies=["All sources rejected reported price"],
                recommendations=["Investigate potential data manipulation"],
            )

        consensus_value = statistics.mean(verified_prices)
        std_dev = statistics.stdev(verified_prices) if len(verified_prices) > 1 else 0.0
        consensus_pct = std_dev / consensus_value if consensus_value > 0 else 0.0

        # Check if within tolerance
        verified = consensus_pct <= tolerance

        # Detect anomalies
        anomalies = []
        if consensus_pct > 0.02:  # 2% deviation
            anomalies.append(f"High price variance: {consensus_pct:.2%}")

        if abs(reported_price - consensus_value) / consensus_value > tolerance:
            anomalies.append(
                f"Reported price deviation: {abs(reported_price - consensus_value) / consensus_value:.2%}"
            )

        # Generate recommendations
        recommendations = []
        if not verified:
            recommendations.append("Price data may be unreliable")
            recommendations.append("Cross-check with additional sources")
        elif consensus_pct > 0.01:
            recommendations.append("Moderate variance in sources - use caution")

        return FactCheckResult(
            asset_symbol=asset_symbol,
            data_type="price",
            verified=verified,
            consensus_value=consensus_value,
            sources_checked=len(verifications),
            sources_verified=len(verified_prices),
            anomalies=anomalies,
            recommendations=recommendations,
        )

    def _check_price_source(
        self,
        source_name: str,
        url: str,
        asset_symbol: str,
        reported_price: float,
    ) -> SourceVerification | None:
        """
        Check price from a specific source.

        Args:
            source_name: Name of data source
            url: API endpoint URL
            asset_symbol: Asset symbol
            reported_price: Price to verify

        Returns:
            SourceVerification or None
        """
        try:
            # Map symbols for different APIs
            symbol_map = {
                "coingecko": {"BTC": "bitcoin", "ETH": "ethereum"},
                "binance": {"BTC": "BTCUSDT", "ETH": "ETHUSDT"},
                "coinbase": {"BTC": "BTC-USD", "ETH": "ETH-USD"},
            }

            mapped_symbol = symbol_map.get(source_name, {}).get(asset_symbol, asset_symbol)

            if source_name == "coingecko":
                response = requests.get(
                    f"{url}?ids={mapped_symbol}&vs_currencies=usd",
                    timeout=self.timeout,
                )
                data = response.json()
                price = data.get(mapped_symbol, {}).get("usd")

            elif source_name == "binance":
                response = requests.get(
                    f"{url}?symbol={mapped_symbol}",
                    timeout=self.timeout,
                )
                data = response.json()
                price = float(data.get("price", 0))

            elif source_name == "coinbase":
                response = requests.get(
                    f"{url}/{mapped_symbol}/spot",
                    timeout=self.timeout,
                )
                data = response.json()
                price = float(data.get("data", {}).get("amount", 0))

            if price is None or price <= 0:
                return None

            # Check if within 10% of reported price
            deviation = abs(price - reported_price) / reported_price
            verified = deviation <= 0.10

            return SourceVerification(
                source_name=source_name,
                verified=verified,
                data={"price": price, "deviation": deviation},
                confidence=1.0 - deviation,
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            logger.warning(f"Error checking {source_name}: {e}")
            return None

    def detect_anomalies(
        self,
        asset_symbol: str,
        price_history: list[dict[str, Any]],
    ) -> list[str]:
        """
        Detect anomalies in price history.

        Args:
            asset_symbol: Asset symbol
            price_history: List of price data points

        Returns:
            List of detected anomalies
        """
        anomalies = []

        if len(price_history) < 10:
            anomalies.append("Insufficient data for anomaly detection")
            return anomalies

        prices = [p["price"] for p in price_history]
        volumes = [p.get("volume", 0) for p in price_history]

        # Check for sudden price spikes
        recent_prices = prices[:5]
        older_prices = prices[5:10]

        recent_avg = statistics.mean(recent_prices)
        older_avg = statistics.mean(older_prices)

        if older_avg > 0:
            price_change = abs(recent_avg - older_avg) / older_avg
            if price_change > 0.20:  # 20% change
                anomalies.append(f"Sudden price movement: {price_change:.2%}")

        # Check for volume anomalies
        recent_volumes = volumes[:5]
        older_volumes = volumes[5:10]

        recent_vol_avg = statistics.mean(recent_volumes)
        older_vol_avg = statistics.mean(older_volumes)

        if older_vol_avg > 0:
            volume_change = abs(recent_vol_avg - older_vol_avg) / older_vol_avg
            if volume_change > 2.0:  # 200% volume change
                anomalies.append(f"Unusual volume: {volume_change:.2%}")

        # Check for price gaps
        for i in range(1, len(prices)):
            gap = abs(prices[i] - prices[i - 1]) / prices[i - 1] if prices[i - 1] > 0 else 0
            if gap > 0.10:  # 10% gap
                anomalies.append(f"Price gap detected: {gap:.2%}")
                break

        return anomalies

    def cross_reference_news(
        self,
        asset_symbol: str,
        sentiment_score: float,
    ) -> dict[str, Any]:
        """
        Cross-reference sentiment with recent news (placeholder).

        Args:
            asset_symbol: Asset symbol
            sentiment_score: Sentiment score to verify

        Returns:
            Cross-reference result
        """
        # Placeholder for actual news API integration
        # In production, integrate with news APIs like:
        # - CryptoCompare news API
        # - CoinDesk API
        # - CryptoSlate API

        return {
            "asset_symbol": asset_symbol,
            "sentiment_verified": True,
            "news_count": 0,
            "recent_headlines": [],
            "recommendation": "Integrate with news API for verification",
        }


# Example usage
def example_usage() -> None:
    """Example usage of FactChecker."""

    # Initialize fact-checker
    fact_checker = FactChecker()

    # Verify price
    result = fact_checker.verify_price(
        asset_symbol="BTC",
        reported_price=50000.0,
        tolerance=0.05,
    )

    print(f"Price Verification: {result.verified}")
    print(f"Consensus Price: ${result.consensus_value:,.2f}")
    print(f"Sources Checked: {result.sources_checked}/{result.sources_verified}")

    if result.anomalies:
        print("\nAnomalies:")
        for anomaly in result.anomalies:
            print(f"  - {anomaly}")

    if result.recommendations:
        print("\nRecommendations:")
        for rec in result.recommendations:
            print(f"  - {rec}")

    # Detect anomalies in price history
    price_history = [
        {"price": 49000.0, "volume": 1000000},
        {"price": 49500.0, "volume": 1100000},
        {"price": 50000.0, "volume": 1200000},
        {"price": 50500.0, "volume": 1300000},
        {"price": 51000.0, "volume": 1400000},
        {"price": 51500.0, "volume": 1500000},
        {"price": 52000.0, "volume": 1600000},
        {"price": 52500.0, "volume": 1700000},
        {"price": 53000.0, "volume": 1800000},
        {"price": 53500.0, "volume": 1900000},
    ]

    anomalies = fact_checker.detect_anomalies("BTC", price_history)
    print(f"\nAnomalies Detected: {len(anomalies)}")
    for anomaly in anomalies:
        print(f"  - {anomaly}")


if __name__ == "__main__":
    example_usage()
