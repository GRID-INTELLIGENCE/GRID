from __future__ import annotations

import asyncio
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from ..config import get_settings

try:
    # Import centralized metrics to avoid duplicates
    from infrastructure.metrics import db_active_connections as _db_connections

    METRICS_ENABLED = True
except ImportError:
    METRICS_ENABLED = False

logger = logging.getLogger(__name__)

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None
_databricks_sync_engine = None  # For Databricks synchronous operations
_disposed: bool = False  # Disposal flag to prevent double-disposal
_engine_lock = asyncio.Lock()  # Lock for thread-safe engine operations

# Safe defaults for connection pooling
POOL_SIZE_DEFAULT = 20
MAX_OVERFLOW_DEFAULT = 10
POOL_TIMEOUT_DEFAULT = 30


def get_database_url() -> str:
    """Return the configured database URL from application settings."""
    settings = get_settings()
    return settings.database.url


def _normalize_async_db_url(url: str) -> str:
    url = (url or "").strip()
    if url.startswith("sqlite:///") and "+aiosqlite" not in url:
        return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://") and "+asyncpg" not in url:
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    # Databricks uses synchronous connector (no async support in databricks-sql-connector)
    # We'll handle this separately
    if url.startswith("databricks://"):
        return url
    return url


def _should_auto_init_sqlite(url: str) -> bool:
    """Return True if we should auto-create tables for a SQLite URL."""
    u = (url or "").strip()
    return u.startswith("sqlite://") or u.startswith("sqlite+aiosqlite://")


async def _init_sqlite_schema(engine: AsyncEngine) -> None:
    """Initialize SQLite schema (create tables) for local-first fallback."""
    try:
        # Importing models ensures Base.metadata is populated
        from .models import Base  # noqa: F401
        from .models_base import Base as BaseModel

        async with engine.begin() as conn:
            await conn.run_sync(BaseModel.metadata.create_all)

        logger.info("SQLite schema initialized (create_all).")
    except Exception as e:
        logger.warning(f"SQLite schema init failed (continuing): {e}", exc_info=True)


def get_async_engine() -> AsyncEngine:
    global _engine
    if _engine is not None:
        return _engine

    settings = get_settings()

    # Handle Databricks (synchronous connector - needs special handling)
    if settings.database.use_databricks:
        from .databricks_connector import create_databricks_engine, validate_databricks_connection

        # Validate Databricks config/connection early; fall back automatically if not healthy.
        try:
            is_ok = validate_databricks_connection()
        except Exception as e:
            logger.warning(f"Databricks validation threw error; falling back: {e}", exc_info=True)
            is_ok = False

        if not is_ok:
            fallback_url = _normalize_async_db_url(settings.database.fallback_url)
            logger.warning(f"Databricks unavailable; using fallback DB: {fallback_url}")
            _engine = create_async_engine(
                fallback_url,
                echo=settings.database.echo,
                poolclass=NullPool if _should_auto_init_sqlite(fallback_url) else None,
            )
            if _should_auto_init_sqlite(fallback_url):
                try:
                    asyncio.get_event_loop().create_task(_init_sqlite_schema(_engine))
                except Exception:  # noqa: S110 intentional silent handling
                    # If we're not in an event loop context, schema can be initialized lazily elsewhere.
                    pass
            return _engine

        # Databricks connector is synchronous. For async app compatibility we:
        # - keep a sync engine for actual Databricks operations
        # - return a lightweight async engine so dependency wiring remains consistent
        sync_engine = create_databricks_engine()

        from sqlalchemy.pool import StaticPool

        _engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )

        # Store sync engine for Databricks
        import application.mothership.db.engine as engine_module

        engine_module._databricks_sync_engine = sync_engine  # type: ignore[assignment]

        logger.warning("Databricks is synchronous - async operations will use sync engine via asyncio.to_thread")

        return _engine

    url = _normalize_async_db_url(settings.database.url)
    is_sqlite = url.startswith("sqlite+") or url.startswith("sqlite://")

    kwargs: dict[str, Any] = {
        "echo": settings.database.echo,
    }

    if is_sqlite:
        kwargs["poolclass"] = NullPool
    else:
        kwargs.update(
            {
                "pool_size": settings.database.pool_size,
                "max_overflow": settings.database.max_overflow,
                "pool_timeout": settings.database.pool_timeout,
                "pool_recycle": getattr(settings.database, "pool_recycle", 3600),
                "pool_pre_ping": getattr(settings.database, "pool_pre_ping", True),
            }
        )

    _engine = create_async_engine(url, **kwargs)

    if METRICS_ENABLED and _engine.pool and hasattr(_engine.pool, "size"):
        _db_connections.set(_engine.pool.size())

    if _should_auto_init_sqlite(url):
        try:
            asyncio.get_event_loop().create_task(_init_sqlite_schema(_engine))
        except Exception:  # noqa: S110 intentional silent handling
            pass
    return _engine


def get_async_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is not None:
        return _sessionmaker

    engine = get_async_engine()
    _sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    return _sessionmaker


async def dispose_async_engine() -> None:
    """
    Dispose of the async engine and close all connections.

    FIXED: Properly closes connection pool on application shutdown.
    Should be called during FastAPI lifespan shutdown or application exit.
    Idempotent - safe to call multiple times.
    """
    global _engine, _sessionmaker, _databricks_sync_engine, _disposed

    async with _engine_lock:
        # Check if already disposed
        if _disposed:
            logger.debug("Database engine already disposed, skipping")
            return

        _disposed = True

        if _sessionmaker is not None:
            _sessionmaker = None
            logger.info("Session maker cleared")

        if _engine is not None:
            await _engine.dispose()
            pool_size = _engine.pool.size() if _engine.pool else 0
            _engine = None
            if METRICS_ENABLED:
                _db_connections.set(0)
            logger.info(f"Async engine disposed (pool size was {pool_size})")

        # Dispose Databricks sync engine if it exists
        if _databricks_sync_engine is not None:
            _databricks_sync_engine.dispose()
            _databricks_sync_engine = None
            logger.info("Databricks sync engine disposed")


def init_db_lifespan(app):
    """
    Initialize database with FastAPI lifespan hooks.

    Usage:
        app = FastAPI(lifespan=init_db_lifespan)

    Or with @asynccontextmanager:
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            await startup_db()
            yield
            await shutdown_db()
    """
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def lifespan(app):
        # Startup
        get_async_engine()  # Force engine creation
        logger.info("Database engine initialized")

        yield

        # Shutdown
        await dispose_async_engine()
        logger.info("Database engine disposed")

    return lifespan


# Backwards compatibility alias
shutdown_db = dispose_async_engine
