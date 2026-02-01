"""
GRID PostgreSQL Adapter - User Database Integration
===================================================
Provides async PostgreSQL access for user queries via asyncpg.
Integrates with DomainGateway persistence patterns.
"""

from __future__ import annotations

import logging
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class UserRow(Protocol):
    """Protocol for user database row."""

    user_id: str
    username: str
    email: str | None
    password_hash: str
    status: str
    org_id: str | None
    metadata: dict[str, Any]


class GridPostgresAdapter:
    """Async PostgreSQL adapter for user database queries.

    Uses asyncpg for high-performance async access.
    Gracefully degrades to None if database unavailable.
    """

    def __init__(self, connection_string: str | None = None):
        self._pool = None
        self._connection_string = connection_string

    async def _ensure_pool(self) -> bool:
        """Ensure connection pool is initialized."""
        if self._pool is not None:
            return True

        try:
            import asyncpg  # type: ignore[import-untyped]

            from grid.security.secrets_loader import get_secret

            dsn = self._connection_string or get_secret(
                "DATABASE_URL", required=False, default="postgresql://localhost:5432/grid"
            )

            self._pool = await asyncpg.create_pool(dsn, min_size=2, max_size=10, command_timeout=30)
            logger.info("PostgreSQL connection pool established")
            return True

        except ImportError:
            logger.warning("asyncpg not installed - PostgreSQL unavailable")
            return False
        except Exception as e:
            logger.warning(f"PostgreSQL connection failed: {e}")
            return False

    async def query_user_by_username(self, username: str) -> dict[str, Any] | None:
        """Query user by username (case-insensitive).

        Returns:
            User dict or None if not found
        """
        if not await self._ensure_pool():
            return None

        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT user_id, username, email, password_hash, status, org_id, metadata
                    FROM users
                    WHERE LOWER(username) = LOWER($1)
                    """,
                    username,
                )
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"User query failed: {e}")
            return None

    async def query_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        """Query user by ID."""
        if not await self._ensure_pool():
            return None

        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"User query by ID failed: {e}")
            return None

    async def update_last_login(self, user_id: str) -> bool:
        """Update user's last login timestamp."""
        if not await self._ensure_pool():
            return False

        try:
            async with self._pool.acquire() as conn:
                await conn.execute("UPDATE users SET last_login = NOW() WHERE user_id = $1", user_id)
                return True
        except Exception as e:
            logger.error(f"Update last login failed: {e}")
            return False

    async def close(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None


# Singleton instance
_postgres_adapter: GridPostgresAdapter | None = None


def get_postgres_adapter() -> GridPostgresAdapter:
    """Get singleton PostgreSQL adapter."""
    global _postgres_adapter
    if _postgres_adapter is None:
        _postgres_adapter = GridPostgresAdapter()
    return _postgres_adapter
