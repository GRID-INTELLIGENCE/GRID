"""
Coinbase Crypto Database
========================
Minimal, secure, cost-effective database for cryptocurrency/investment tracking.
Based on GRID patterns but focused on revenue-generating features.

Principles:
- Privacy-first: No PII, encrypted identifiers
- Security-first: Parameterized queries, no SQL injection
- Cost-effective: Minimal dependencies, only revenue features
- Business-aligned: Crypto/investment/stocks revenue generation
"""

import hashlib
import json
import logging
import secrets
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Iterator

# Reuse GRID's Databricks connector (no new dependencies)
try:
    from databricks import sql
except ImportError:
    # Fallback import for different databricks package versions
    import databricks.sql as sql  # type: ignore[import-not-found]

logger = logging.getLogger(__name__)


class CryptoAssetType(Enum):
    """Cryptocurrency asset types."""

    BITCOIN = "bitcoin"
    ETHEREUM = "ethereum"
    STABLECOIN = "stablecoin"
    ALTCOIN = "altcoin"
    DEFI = "defi"
    NFT = "nft"


class TransactionType(Enum):
    """Transaction types."""

    BUY = "buy"
    SELL = "sell"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    STAKING_REWARD = "staking_reward"


@dataclass
class CryptoAsset:
    """Cryptocurrency asset data."""

    symbol: str
    name: str
    asset_type: CryptoAssetType
    current_price: float
    market_cap: float | None = None
    volume_24h: float | None = None
    last_updated: datetime | None = None


@dataclass
class PortfolioPosition:
    """Portfolio position data."""

    user_id_hash: str  # Hashed user ID (privacy-first)
    asset_symbol: str
    quantity: float
    average_cost: float
    current_value: float
    unrealized_pnl: float
    last_updated: datetime


@dataclass
class Transaction:
    """Transaction data."""

    id: str
    user_id_hash: str
    asset_symbol: str
    transaction_type: TransactionType
    quantity: float
    price: float
    fee: float
    timestamp: datetime
    metadata: dict[str, Any] | None = None


class CryptoDatabase:
    """
    Minimal cryptocurrency database for revenue-generating features.

    Privacy-first: Uses hashed user IDs, no PII stored
    Security-first: Parameterized queries, SQL injection prevention
    Cost-effective: Minimal schema, only revenue features
    """

    def __init__(self, databricks_config: dict[str, str]):
        """
        Initialize crypto database.

        Args:
            databricks_config: Databricks connection config (host, http_path, token)
        """
        self.connection_params = {
            "server_hostname": databricks_config["host"],
            "http_path": databricks_config["http_path"],
            "access_token": databricks_config["token"],
        }
        self._create_tables()

    @contextmanager
    def session(self) -> Iterator[sql.Cursor]:
        """Yield a fresh cursor with auto-commit."""
        conn = sql.connect(**self.connection_params)
        cursor = conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()
            conn.close()

    def _create_tables(self) -> None:
        """Create minimal revenue-generating tables."""
        with self.session() as cursor:
            # Crypto assets table (market data)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS crypto_assets (
                    symbol STRING PRIMARY KEY,
                    name STRING,
                    asset_type STRING,
                    current_price DOUBLE,
                    market_cap DOUBLE,
                    volume_24h DOUBLE,
                    last_updated TIMESTAMP
                )
                """)

            # Price history table (for analysis)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS price_history (
                    id STRING,
                    symbol STRING,
                    price DOUBLE,
                    volume DOUBLE,
                    timestamp TIMESTAMP,
                    PRIMARY KEY (id, symbol)
                )
                """)

            # Portfolio positions table (user data - hashed IDs)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_positions (
                    user_id_hash STRING,
                    asset_symbol STRING,
                    quantity DOUBLE,
                    average_cost DOUBLE,
                    current_value DOUBLE,
                    unrealized_pnl DOUBLE,
                    last_updated TIMESTAMP,
                    PRIMARY KEY (user_id_hash, asset_symbol)
                )
                """)

            # Transactions table (audit trail)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id STRING PRIMARY KEY,
                    user_id_hash STRING,
                    asset_symbol STRING,
                    transaction_type STRING,
                    quantity DOUBLE,
                    price DOUBLE,
                    fee DOUBLE,
                    timestamp TIMESTAMP,
                    metadata STRING
                )
                """)

            # Sentiment analysis table (revenue feature)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sentiment_analysis (
                    id STRING PRIMARY KEY,
                    asset_symbol STRING,
                    sentiment_score DOUBLE,
                    source STRING,
                    timestamp TIMESTAMP
                )
                """)

        logger.info("Crypto database tables created")

    def hash_user_id(self, user_id: str) -> str:
        """
        Hash user ID for privacy-first storage.

        Args:
            user_id: Original user ID

        Returns:
            Hashed user ID (SHA-256)
        """
        return hashlib.sha256(user_id.encode()).hexdigest()

    def upsert_crypto_asset(self, asset: CryptoAsset) -> None:
        """
        Add or update crypto asset data.

        Args:
            asset: CryptoAsset data
        """
        with self.session() as cursor:
            cursor.execute(
                """
                MERGE INTO crypto_assets t
                USING (SELECT ? AS symbol) s
                ON t.symbol = s.symbol
                WHEN MATCHED THEN UPDATE SET
                    name = ?, asset_type = ?, current_price = ?,
                    market_cap = ?, volume_24h = ?, last_updated = ?
                WHEN NOT MATCHED THEN INSERT
                    (symbol, name, asset_type, current_price, market_cap, volume_24h, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    asset.symbol,
                    asset.name,
                    asset.asset_type.value,
                    asset.current_price,
                    asset.market_cap,
                    asset.volume_24h,
                    asset.last_updated or datetime.utcnow(),
                    asset.symbol,
                    asset.name,
                    asset.asset_type.value,
                    asset.current_price,
                    asset.market_cap,
                    asset.volume_24h,
                    asset.last_updated or datetime.utcnow(),
                ),
            )
        logger.info(f"Asset upserted: {asset.symbol}")

    def add_price_point(
        self,
        symbol: str,
        price: float,
        volume: float,
        timestamp: datetime | None = None,
    ) -> None:
        """
        Add price history point for analysis.

        Args:
            symbol: Asset symbol
            price: Current price
            volume: Trading volume
            timestamp: Price timestamp
        """
        import uuid

        with self.session() as cursor:
            cursor.execute(
                """
                INSERT INTO price_history (id, symbol, price, volume, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    symbol,
                    price,
                    volume,
                    timestamp or datetime.utcnow(),
                ),
            )

    def upsert_portfolio_position(self, position: PortfolioPosition) -> None:
        """
        Add or update portfolio position.

        Args:
            position: PortfolioPosition data (user_id_hash required)
        """
        with self.session() as cursor:
            cursor.execute(
                """
                MERGE INTO portfolio_positions t
                USING (SELECT ? AS user_id_hash, ? AS asset_symbol) s
                ON t.user_id_hash = s.user_id_hash AND t.asset_symbol = s.asset_symbol
                WHEN MATCHED THEN UPDATE SET
                    quantity = ?, average_cost = ?, current_value = ?,
                    unrealized_pnl = ?, last_updated = ?
                WHEN NOT MATCHED THEN INSERT
                    (user_id_hash, asset_symbol, quantity, average_cost, current_value, unrealized_pnl, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    position.user_id_hash,
                    position.asset_symbol,
                    position.quantity,
                    position.average_cost,
                    position.current_value,
                    position.unrealized_pnl,
                    position.last_updated,
                    position.user_id_hash,
                    position.asset_symbol,
                    position.quantity,
                    position.average_cost,
                    position.current_value,
                    position.unrealized_pnl,
                    position.last_updated,
                ),
            )
        logger.info(f"Position upserted: {position.asset_symbol}")

    def add_transaction(self, transaction: Transaction) -> None:
        """
        Add transaction record (audit trail).

        Args:
            transaction: Transaction data
        """
        with self.session() as cursor:
            cursor.execute(
                """
                INSERT INTO transactions
                (id, user_id_hash, asset_symbol, transaction_type, quantity, price, fee, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transaction.id,
                    transaction.user_id_hash,
                    transaction.asset_symbol,
                    transaction.transaction_type.value,
                    transaction.quantity,
                    transaction.price,
                    transaction.fee,
                    transaction.timestamp,
                    json.dumps(transaction.metadata or {}),
                ),
            )
        logger.info(f"Transaction added: {transaction.id}")

    def get_portfolio_value(self, user_id_hash: str) -> float:
        """
        Calculate total portfolio value.

        Args:
            user_id_hash: Hashed user ID

        Returns:
            Total portfolio value
        """
        with self.session() as cursor:
            cursor.execute(
                """
                SELECT SUM(current_value) FROM portfolio_positions
                WHERE user_id_hash = ?
                """,
                (user_id_hash,),
            )
            result = cursor.fetchone()
            return result[0] if result and result[0] else 0.0

    def get_asset_price(self, symbol: str) -> float | None:
        """
        Get current asset price.

        Args:
            symbol: Asset symbol

        Returns:
            Current price or None
        """
        with self.session() as cursor:
            cursor.execute(
                """
                SELECT current_price FROM crypto_assets
                WHERE symbol = ?
                """,
                (symbol,),
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def get_price_history(
        self,
        symbol: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Get price history for analysis.

        Args:
            symbol: Asset symbol
            start_date: Start date filter
            end_date: End date filter
            limit: Max results

        Returns:
            List of price history points
        """
        with self.session() as cursor:
            query = """
                SELECT symbol, price, volume, timestamp
                FROM price_history
                WHERE symbol = ?
            """
            params = [symbol]

            if start_date:
                query += " AND timestamp >= ?"
                params.append(str(start_date.isoformat()) if hasattr(start_date, 'isoformat') else str(start_date))

            if end_date:
                query += " AND timestamp <= ?"
                params.append(str(end_date.isoformat()) if hasattr(end_date, 'isoformat') else str(end_date))

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(str(limit))

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

            return [
                {
                    "symbol": row[0],
                    "price": row[1],
                    "volume": row[2],
                    "timestamp": row[3],
                }
                for row in rows
            ]

    def add_sentiment_analysis(
        self,
        asset_symbol: str,
        sentiment_score: float,
        source: str,
    ) -> None:
        """
        Add sentiment analysis data (revenue feature).

        Args:
            asset_symbol: Asset symbol
            sentiment_score: Sentiment score (-1.0 to 1.0)
            source: Data source
        """
        import uuid

        with self.session() as cursor:
            cursor.execute(
                """
                INSERT INTO sentiment_analysis (id, asset_symbol, sentiment_score, source, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    asset_symbol,
                    sentiment_score,
                    source,
                    datetime.utcnow(),
                ),
            )

    def get_sentiment_history(
        self,
        asset_symbol: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Get sentiment history for analysis.

        Args:
            asset_symbol: Asset symbol
            limit: Max results

        Returns:
            List of sentiment data points
        """
        with self.session() as cursor:
            cursor.execute(
                """
                SELECT asset_symbol, sentiment_score, source, timestamp
                FROM sentiment_analysis
                WHERE asset_symbol = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (asset_symbol, limit),
            )
            rows = cursor.fetchall()

            return [
                {
                    "asset_symbol": row[0],
                    "sentiment_score": row[1],
                    "source": row[2],
                    "timestamp": row[3],
                }
                for row in rows
            ]


# Example usage functions
def example_usage() -> None:
    """Example usage of CryptoDatabase."""
    import os

    # Initialize database with Databricks config
    db = CryptoDatabase(
        databricks_config={
            "host": os.getenv("DATABRICKS_HOST") or "",
            "http_path": os.getenv("DATABRICKS_HTTP_PATH") or "",
            "token": os.getenv("DATABRICKS_TOKEN") or "",
        }
    )

    # Hash user ID for privacy
    user_id_hash = db.hash_user_id("user123")

    # Add crypto asset
    bitcoin = CryptoAsset(
        symbol="BTC",
        name="Bitcoin",
        asset_type=CryptoAssetType.BITCOIN,
        current_price=50000.0,
        market_cap=1000000000000.0,
        volume_24h=30000000000.0,
    )
    db.upsert_crypto_asset(bitcoin)

    # Add price history
    db.add_price_point(symbol="BTC", price=50100.0, volume=31000000000.0)

    # Add portfolio position
    position = PortfolioPosition(
        user_id_hash=user_id_hash,
        asset_symbol="BTC",
        quantity=0.5,
        average_cost=45000.0,
        current_value=25000.0,
        unrealized_pnl=2500.0,
        last_updated=datetime.utcnow(),
    )
    db.upsert_portfolio_position(position)

    # Add transaction
    transaction = Transaction(
        id=str(secrets.token_urlsafe(16)),
        user_id_hash=user_id_hash,
        asset_symbol="BTC",
        transaction_type=TransactionType.BUY,
        quantity=0.5,
        price=50000.0,
        fee=50.0,
        timestamp=datetime.utcnow(),
    )
    db.add_transaction(transaction)

    # Get portfolio value
    portfolio_value = db.get_portfolio_value(user_id_hash)
    print(f"Portfolio value: ${portfolio_value:,.2f}")

    # Get price history
    history = db.get_price_history(symbol="BTC", limit=10)
    print(f"Price history points: {len(history)}")

    # Get sentiment
    db.add_sentiment_analysis(asset_symbol="BTC", sentiment_score=0.75, source="twitter")
    sentiment = db.get_sentiment_history(asset_symbol="BTC", limit=5)
    print(f"Sentiment data points: {len(sentiment)}")


if __name__ == "__main__":
    example_usage()
