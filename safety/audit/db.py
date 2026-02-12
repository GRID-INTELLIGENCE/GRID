"""
Async database engine and session management for the audit store.

Uses SQLAlchemy 2.0 async with asyncpg.
Fail-closed: if the DB is unreachable, callers must refuse requests.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from safety.audit.models import Base
from safety.observability.logging_setup import get_logger
from safety.observability.metrics import AUDIT_DB_HEALTHY

logger = get_logger("audit.db")

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _get_database_url() -> str:
    url = os.getenv("DATABASE_URL", "")
    if not url:
        raise RuntimeError(
            "DATABASE_URL environment variable is required for audit store"
        )
    # Ensure async driver
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


async def init_db() -> None:
    """Initialize the async engine and create tables if needed."""
    global _engine, _session_factory
    url = _get_database_url()
    _engine = create_async_engine(
        url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=os.getenv("SAFETY_DB_ECHO", "").lower() == "true",
    )
    _session_factory = async_sessionmaker(
        _engine, class_=AsyncSession, expire_on_commit=False
    )
    # Create tables (in production use Alembic migrations instead)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    AUDIT_DB_HEALTHY.set(1)
    logger.info("audit_db_initialized", url=url.split("@")[-1])


async def close_db() -> None:
    """Dispose of the engine pool."""
    global _engine, _session_factory
    if _engine:
        await _engine.dispose()
        _engine = None
        _session_factory = None
    AUDIT_DB_HEALTHY.set(0)
    logger.info("audit_db_closed")


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession]:
    """
    Provide a transactional async session.

    Raises RuntimeError if the DB is not initialized (fail-closed).
    """
    if _session_factory is None:
        AUDIT_DB_HEALTHY.set(0)
        raise RuntimeError("Audit database not initialized — fail closed")
    session = _session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        AUDIT_DB_HEALTHY.set(0)
        raise
    finally:
        await session.close()


async def check_health() -> bool:
    """Return True if the audit DB is reachable."""
    try:
        if _engine is None:
            AUDIT_DB_HEALTHY.set(0)
            return False
        async with _engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        AUDIT_DB_HEALTHY.set(1)
        return True
    except Exception as exc:
        logger.error("audit_db_health_check_failed", error=str(exc))
        AUDIT_DB_HEALTHY.set(0)
        return False
