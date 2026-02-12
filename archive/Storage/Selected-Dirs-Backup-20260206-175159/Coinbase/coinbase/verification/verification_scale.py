"""
Verification Scale
==================
Multi-source verification - Scale pattern.

Reference: Scale - Weigh and verify data sources
"""

import logging
from dataclasses import dataclass
from enum import Enum

import requests  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


class SourceType(Enum):
    """Data source types."""

    COINGECKO = "coingecko"
    BINANCE = "binance"
    COINBASE = "coinbase"


@dataclass
class SourceData:
    """Data from a source."""

    source: SourceType
    price: float | None
    timestamp: str | None
    error: str | None = None


@dataclass
class VerificationResult:
    """Verification result."""

    verified: bool
    consensus: float | None
    variance: float
    sources_checked: int
    sources_verified: int
    anomalies: list[str]
    recommendations: list[str]


class VerificationScale:
    """
    Verify data across sources like a Scale.

    Weigh sources and calculate consensus.
    """

    def __init__(self) -> None:
        """Initialize verification scale."""
        self.sources = {
            SourceType.COINGECKO: "https://api.coingecko.com/api/v3/simple/price",
            SourceType.BINANCE: "https://api.binance.com/api/v3/ticker/price",
            SourceType.COINBASE: "https://api.coinbase.com/v2/prices",
        }
        self.weights = {source: 1.0 for source in SourceType}
        self.timeout = 10

    def weigh_sources(
        self, asset_symbol: str, reported_price: float, tolerance: float = 0.05
    ) -> VerificationResult:
        """
        Weigh sources like a Scale.

        Args:
            asset_symbol: Asset symbol (e.g., "BTC")
            reported_price: Price to verify
            tolerance: Acceptable deviation

        Returns:
            VerificationResult
        """
        # Fetch data from all sources
        source_data = self._fetch_all_sources(asset_symbol)

        # Filter valid prices
        valid_prices = {
            source: data.price for source, data in source_data.items() if data.price is not None
        }

        if not valid_prices:
            return VerificationResult(
                verified=False,
                consensus=None,
                variance=0.0,
                sources_checked=len(source_data),
                sources_verified=0,
                anomalies=["No sources available"],
                recommendations=["Check network connectivity"],
            )

        # Calculate weighted consensus
        total_weight = sum(self.weights[s] for s in valid_prices.keys())
        consensus = (
            sum(price * self.weights[source] for source, price in valid_prices.items())
            / total_weight
        )

        # Calculate variance
        prices_list = list(valid_prices.values())
        variance = sum((p - consensus) ** 2 for p in prices_list) / len(prices_list)

        # Check if within tolerance
        deviation = abs(reported_price - consensus) / consensus if consensus > 0 else 0
        verified = deviation <= tolerance

        # Detect anomalies
        anomalies = []
        if variance > 1000.0:
            anomalies.append(f"High price variance: {variance:.2f}")

        if deviation > 0.02:
            anomalies.append(f"Reported price deviation: {deviation:.2%}")

        # Generate recommendations
        recommendations = []
        if not verified:
            recommendations.append("Price data may be unreliable")
            recommendations.append("Cross-check with additional sources")
        elif variance > 500.0:
            recommendations.append("Moderate variance - use caution")

        logger.info(
            f"Verification: {verified} | "
            f"Consensus: ${consensus:,.2f} | "
            f"Sources: {len(valid_prices)}/{len(source_data)}"
        )

        return VerificationResult(
            verified=verified,
            consensus=consensus,
            variance=variance,
            sources_checked=len(source_data),
            sources_verified=len(valid_prices),
            anomalies=anomalies,
            recommendations=recommendations,
        )

    def _fetch_all_sources(self, asset_symbol: str) -> dict[SourceType, SourceData]:
        """
        Fetch data from all sources.

        Args:
            asset_symbol: Asset symbol

        Returns:
            Dictionary of source data
        """
        results = {}

        for source_type, url in self.sources.items():
            try:
                data = self._fetch_source(source_type, url, asset_symbol)
                results[source_type] = data
            except Exception as e:
                logger.warning(f"Failed to fetch from {source_type.value}: {e}")
                results[source_type] = SourceData(
                    source=source_type, price=None, timestamp=None, error=str(e)
                )

        return results

    def _fetch_source(self, source_type: SourceType, url: str, asset_symbol: str) -> SourceData:
        """
        Fetch data from specific source.

        Args:
            source_type: Source type
            url: API URL
            asset_symbol: Asset symbol

        Returns:
            SourceData
        """
        # Map symbols for different APIs
        symbol_map = {
            SourceType.COINGECKO: {"BTC": "bitcoin", "ETH": "ethereum"},
            SourceType.BINANCE: {"BTC": "BTCUSDT", "ETH": "ETHUSDT"},
            SourceType.COINBASE: {"BTC": "BTC-USD", "ETH": "ETH-USD"},
        }

        mapped_symbol = symbol_map.get(source_type, {}).get(asset_symbol, asset_symbol)

        if source_type == SourceType.COINGECKO:
            response = requests.get(
                f"{url}?ids={mapped_symbol}&vs_currencies=usd", timeout=self.timeout
            )
            data = response.json()
            price = data.get(mapped_symbol, {}).get("usd")

        elif source_type == SourceType.BINANCE:
            response = requests.get(f"{url}?symbol={mapped_symbol}", timeout=self.timeout)
            data = response.json()
            price = float(data.get("price", 0)) if data else 0

        elif source_type == SourceType.COINBASE:
            response = requests.get(f"{url}/{mapped_symbol}/spot", timeout=self.timeout)
            data = response.json()
            price = float(data.get("data", {}).get("amount", 0)) if data else 0

        return SourceData(
            source=source_type, price=price if price and price > 0 else None, timestamp=None
        )


# Example usage
def example_usage() -> None:
    """Example usage of VerificationScale."""
    scale = VerificationScale()

    # Verify price
    result = scale.weigh_sources(asset_symbol="BTC", reported_price=50000.0)

    print(f"Verified: {result.verified}")
    print(f"Consensus: ${result.consensus:,.2f}")
    print(f"Sources: {result.sources_checked}/{result.sources_verified}")

    if result.anomalies:
        print("\nAnomalies:")
        for anomaly in result.anomalies:
            print(f"  - {anomaly}")


if __name__ == "__main__":
    example_usage()
