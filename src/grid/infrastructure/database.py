import logging

import aiosqlite

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages SQLite database connection and operations using aiosqlite.
    Follows the Local-First architecture.
    """

    def __init__(self, db_path: str = "grid.db"):
        self.db_path = db_path
        self._connection: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        """Establish connection to the SQLite database."""
        if not self._connection:
            self._connection = await aiosqlite.connect(self.db_path)
            self._connection.row_factory = aiosqlite.Row
            logger.info(f"Connected to SQLite database at {self.db_path}")

    async def close(self) -> None:
        """Close the database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None
            logger.info("Closed SQLite connection")

    async def execute(self, query: str, parameters: tuple = ()) -> aiosqlite.Cursor:
        """Execute a SQL query."""
        if not self._connection:
            await self.connect()
        # Mypy might complain about _connection being None here despite check,
        # but aiosqlite.connect returns a connection.
        assert self._connection is not None
        return await self._connection.execute(query, parameters)

    async def execute_many(self, query: str, parameters: list[tuple]) -> aiosqlite.Cursor:
        """Execute multiple SQL queries (bulk insert)."""
        if not self._connection:
            await self.connect()
        assert self._connection is not None
        return await self._connection.executemany(query, parameters)

    async def fetch_all(self, query: str, parameters: tuple = ()) -> list[dict]:
        """Execute query and verify return all rows as dicts."""
        if not self._connection:
            await self.connect()
        assert self._connection is not None
        async with self._connection.execute(query, parameters) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def fetch_one(self, query: str, parameters: tuple = ()) -> dict | None:
        """Execute query and return one row as dict."""
        if not self._connection:
            await self.connect()
        assert self._connection is not None
        async with self._connection.execute(query, parameters) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def commit(self) -> None:
        """Commit current transaction."""
        if self._connection:
            await self._connection.commit()

    async def initialize_schema(self) -> None:
        """Create initial tables if they don't exist."""
        # Basic schema for auth and usage tracking
        schema = """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE,
            password_hash TEXT,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS tokens (
            token_id TEXT PRIMARY KEY,
            user_id TEXT,
            revoked BOOLEAN DEFAULT 0,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            event_type TEXT,
            quantity INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS usage_aggregation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            period TEXT,  -- 'YYYY-MM' for monthly, 'YYYY-MM-DD' for daily
            period_type TEXT DEFAULT 'monthly',  -- 'daily' or 'monthly'
            event_type TEXT,
            total_quantity INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, period, period_type, event_type),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS subscriptions (
            id TEXT PRIMARY KEY,
            user_id TEXT UNIQUE,
            tier TEXT DEFAULT 'free',  -- 'free', 'starter', 'pro', 'enterprise'
            stripe_customer_id TEXT,
            stripe_subscription_id TEXT,
            current_period_start TIMESTAMP,
            current_period_end TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """
        if not self._connection:
            await self.connect()
        assert self._connection is not None
        await self._connection.executescript(schema)
        await self._connection.commit()
        logger.info("Database schema initialized.")
