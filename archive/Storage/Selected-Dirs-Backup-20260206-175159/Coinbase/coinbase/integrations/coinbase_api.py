"""
Coinbase API Integration
========================
Real-time market data and transaction integration with Coinbase API.

Usage:
    from coinbase.integrations.coinbase_api import CoinbaseAPIClient

    client = CoinbaseAPIClient()

    # Get market data
    btc_price = client.get_spot_price('BTC-USD')

    # Get historical data
    historical = client.get_historical_data('BTC-USD', days=30)
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class Granularity(Enum):
    """Time granularity for historical data."""

    ONE_MINUTE = 60
    FIVE_MINUTES = 300
    FIFTEEN_MINUTES = 900
    ONE_HOUR = 3600
    SIX_HOURS = 21600
    ONE_DAY = 86400


@dataclass
class MarketData:
    """Market data for a cryptocurrency."""

    symbol: str
    price: float
    volume_24h: float
    high_24h: float
    low_24h: float
    price_change_24h: float
    price_change_percent_24h: float
    last_updated: datetime


@dataclass
class HistoricalDataPoint:
    """Single historical data point."""

    timestamp: datetime
    low: float
    high: float
    open: float
    close: float
    volume: float


class CoinbaseAPIClient:
    """
    Coinbase API client for real-time data integration.

    Features:
    - Real-time price data
    - Historical price data
    - Market statistics
    - Rate limiting compliance
    """

    BASE_URL = "https://api.exchange.coinbase.com"

    def __init__(self, api_key: str | None = None, api_secret: str | None = None):
        """
        Initialize Coinbase API client.

        Args:
            api_key: Optional API key for authenticated requests
            api_secret: Optional API secret for authenticated requests
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = None
        self._rate_limit_remaining = 100
        self._last_request_time = 0

        # Initialize rate limiter
        from coinbase.config import get_rate_limiter

        self.rate_limiter = get_rate_limiter()

    def _get_session(self) -> Any:
        """Get or create HTTP session."""
        if self.session is None:
            import requests  # type: ignore

            self.session = requests.Session()
            if self.session is not None:
                self.session.headers.update(
                    {"Content-Type": "application/json", "User-Agent": "CoinbasePlatform/1.0"}
                )
        return self.session

    def _make_request(self, endpoint: str, params: dict | None = None) -> dict[str, Any]:
        """
        Make API request with rate limiting.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            JSON response
        """
        # Check rate limit
        if not self.rate_limiter.allow_request("coinbase").allowed:
            logger.warning("Rate limit exceeded for Coinbase API")
            raise Exception("Rate limit exceeded")

        url = f"{self.BASE_URL}{endpoint}"

        try:
            session = self._get_session()
            response = session.get(url, params=params, timeout=30)

            # Update rate limit tracking
            self._rate_limit_remaining = int(response.headers.get("CB-After", 100))

            if response.status_code == 200:
                return response.json()  # type: ignore
            elif response.status_code == 429:
                logger.error("Coinbase API rate limit exceeded")
                raise Exception("Rate limit exceeded")
            else:
                logger.error(f"Coinbase API error: {response.status_code}")
                raise Exception(f"API error: {response.status_code}")

        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise

    def get_spot_price(self, currency_pair: str) -> float | None:
        """
        Get current spot price for a currency pair.

        Args:
            currency_pair: e.g., 'BTC-USD', 'ETH-USD'

        Returns:
            Current price or None
        """
        try:
            data = self._make_request(f"/products/{currency_pair}/ticker")
            price = float(data.get("price", 0))
            logger.info(f"Got spot price for {currency_pair}: {price}")
            return price
        except Exception as e:
            logger.error(f"Failed to get spot price: {e}")
            return None

    def get_market_data(self, currency_pair: str) -> MarketData | None:
        """
        Get comprehensive market data for a currency pair.

        Args:
            currency_pair: e.g., 'BTC-USD'

        Returns:
            MarketData object or None
        """
        try:
            # Get ticker data
            ticker = self._make_request(f"/products/{currency_pair}/ticker")

            # Get 24h stats
            stats = self._make_request(f"/products/{currency_pair}/stats")

            return MarketData(
                symbol=currency_pair,
                price=float(ticker.get("price", 0)),
                volume_24h=float(stats.get("volume", 0)),
                high_24h=float(stats.get("high", 0)),
                low_24h=float(stats.get("low", 0)),
                price_change_24h=float(stats.get("change", 0)),
                price_change_percent_24h=float(stats.get("change_percent", 0)),
                last_updated=datetime.now(),
            )
        except Exception as e:
            logger.error(f"Failed to get market data: {e}")
            return None

    def get_historical_data(
        self, currency_pair: str, granularity: Granularity = Granularity.ONE_DAY, days: int = 30
    ) -> list[HistoricalDataPoint]:
        """
        Get historical OHLCV data.

        Args:
            currency_pair: e.g., 'BTC-USD'
            granularity: Time granularity
            days: Number of days of history

        Returns:
            List of historical data points
        """
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)

            params = {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "granularity": granularity.value,
            }

            data = self._make_request(f"/products/{currency_pair}/candles", params)

            # Parse candle data [timestamp, low, high, open, close, volume]
            historical_data = []
            for candle in data:
                if len(candle) >= 6:
                    historical_data.append(
                        HistoricalDataPoint(
                            timestamp=datetime.fromtimestamp(int(candle[0])),
                            low=float(candle[1]),
                            high=float(candle[2]),
                            open=float(candle[3]),
                            close=float(candle[4]),
                            volume=float(candle[5]),
                        )
                    )

            logger.info(f"Got {len(historical_data)} historical data points for {currency_pair}")
            return sorted(historical_data, key=lambda x: x.timestamp)

        except Exception as e:
            logger.error(f"Failed to get historical data: {e}")
            return []

    def get_supported_currencies(self) -> list[str]:
        """
        Get list of supported currency pairs.

        Returns:
            List of currency pair symbols
        """
        try:
            products = self._make_request("/products")
            currencies = [p.get("id") for p in products.values() if isinstance(p, dict) and p.get("id")]
            return sorted([c for c in currencies if isinstance(c, str)])
        except Exception as e:
            logger.error(f"Failed to get currencies: {e}")
            return []

    def get_order_book(self, currency_pair: str, level: int = 1) -> dict[str, Any]:
        """
        Get order book for a currency pair.

        Args:
            currency_pair: e.g., 'BTC-USD'
            level: Detail level (1, 2, or 3)

        Returns:
            Order book data
        """
        try:
            return self._make_request(f"/products/{currency_pair}/book", {"level": level})
        except Exception as e:
            logger.error(f"Failed to get order book: {e}")
            return {}

    def get_recent_trades(self, currency_pair: str, limit: int = 100) -> list[dict[str, Any]]:
        """
        Get recent trades for a currency pair.

        Args:
            currency_pair: e.g., 'BTC-USD'
            limit: Number of trades to retrieve

        Returns:
            List of recent trades
        """
        try:
            return self._make_request(f"/products/{currency_pair}/trades", {"limit": limit})  # type: ignore
        except Exception as e:
            logger.error(f"Failed to get recent trades: {e}")
            return []


class CoinbaseDataFeed:
    """
    Real-time data feed from Coinbase API.

    Provides streaming price updates and market data.
    """

    def __init__(self, client: CoinbaseAPIClient | None = None):
        """
        Initialize data feed.

        Args:
            client: Optional Coinbase API client
        """
        self.client = client or CoinbaseAPIClient()
        self.subscribers: dict[str, list[Callable[[str, float], None]]] = {}
        self._running = False
        self._update_interval = 60  # seconds

    def subscribe(self, currency_pair: str, callback: Callable[[str, float], None]) -> None:
        """
        Subscribe to price updates for a currency pair.

        Args:
            currency_pair: e.g., 'BTC-USD'
            callback: Function to call with price updates
        """
        if currency_pair not in self.subscribers:
            self.subscribers[currency_pair] = []
        self.subscribers[currency_pair].append(callback)
        logger.info(f"Subscribed to {currency_pair} updates")

    def unsubscribe(self, currency_pair: str, callback: Callable[[str, float], None]) -> None:
        """
        Unsubscribe from price updates.

        Args:
            currency_pair: e.g., 'BTC-USD'
            callback: Function to remove
        """
        if currency_pair in self.subscribers:
            self.subscribers[currency_pair].remove(callback)

    def start(self) -> None:
        """Start the data feed."""
        self._running = True
        import threading

        self._thread = threading.Thread(target=self._update_loop, daemon=True)
        self._thread.start()
        logger.info("Coinbase data feed started")

    def stop(self) -> None:
        """Stop the data feed."""
        self._running = False
        logger.info("Coinbase data feed stopped")

    def _update_loop(self) -> None:
        """Main update loop."""
        while self._running:
            try:
                for currency_pair in self.subscribers:
                    # Get latest price
                    price = self.client.get_spot_price(currency_pair)

                    if price:
                        # Notify subscribers
                        for callback in self.subscribers[currency_pair]:
                            try:
                                callback(currency_pair, price)
                            except Exception as e:
                                logger.error(f"Callback error: {e}")

                time.sleep(self._update_interval)

            except Exception as e:
                logger.error(f"Update loop error: {e}")
                time.sleep(5)


# Global client instance
_global_client: CoinbaseAPIClient | None = None
_global_feed: CoinbaseDataFeed | None = None


def get_coinbase_client() -> CoinbaseAPIClient:
    """Get global Coinbase API client instance."""
    global _global_client
    if _global_client is None:
        _global_client = CoinbaseAPIClient()
    return _global_client


def get_coinbase_feed() -> CoinbaseDataFeed:
    """Get global Coinbase data feed instance."""
    global _global_feed
    if _global_feed is None:
        _global_feed = CoinbaseDataFeed()
    return _global_feed


# Convenience functions
def get_current_price(currency_pair: str) -> float | None:
    """Quick function to get current price."""
    client = get_coinbase_client()
    return client.get_spot_price(currency_pair)


def get_historical_prices(currency_pair: str, days: int = 30) -> list[HistoricalDataPoint]:
    """Quick function to get historical prices."""
    client = get_coinbase_client()
    return client.get_historical_data(currency_pair, days=days)
