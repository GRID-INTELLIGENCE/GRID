"""
Database Fallback Chain.

Implements automatic fallback between database backends:
1. Try primary backend (e.g., Databricks)
2. Validate connection health
3. Fall back to secondary if primary fails
4. Continue down the chain until one works

Extracted from Mothership's Databricks → SQLite fallback pattern.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


class DatabaseBackend(Protocol):
    """
    Protocol for database backend implementations.

    Any database connector that implements this protocol
    can be used in a fallback chain.
    """

    @property
    def name(self) -> str:
        """Backend name for logging/debugging."""
        ...

    @property
    def url(self) -> str:
        """Connection URL (masked for secrets)."""
        ...

    def is_healthy(self) -> bool:
        """Check if backend is accessible."""
        ...

    def connect(self) -> Any:
        """Create and return a connection/engine."""
        ...


@dataclass(frozen=True, slots=True)
class BackendStatus:
    """Immutable status record for a backend."""

    name: str
    is_healthy: bool
    error_message: str | None = None
    latency_ms: float | None = None


class DatabaseFallbackChain:
    """
    Automatic fallback chain for database backends.

    Tries backends in order, falling back automatically
    when one fails health checks.

    Usage:
        chain = DatabaseFallbackChain([
            DatabricksBackend(...),
            PostgreSQLBackend(...),
            SQLiteBackend(...),
        ])

        # Get working backend (raises if all fail)
        backend = chain.get_connection()

        # Check all backends
        status = chain.health_check_all()
    """

    def __init__(
        self,
        backends: list[DatabaseBackend],
        *,
        on_fallback: Callable[[str, str], None] | None = None,
    ):
        """
        Initialize fallback chain.

        Args:
            backends: List of backends in priority order
            on_fallback: Optional callback(backend_name, reason) on fallback
        """
        self._backends = backends
        self._on_fallback = on_fallback
        self._active_backend: DatabaseBackend | None = None
        self._status_cache: dict[str, BackendStatus] = {}

    @property
    def backends(self) -> list[DatabaseBackend]:
        """Get list of backends."""
        return self._backends

    @property
    def active_backend(self) -> DatabaseBackend | None:
        """Get currently active backend."""
        return self._active_backend

    def get_connection(self) -> Any:
        """
        Get connection from first healthy backend.

        Returns:
            Connection/engine from healthy backend

        Raises:
            ConnectionError: If all backends are unavailable
        """
        errors: list[str] = []

        for backend in self._backends:
            name = backend.name

            try:
                if backend.is_healthy():
                    self._active_backend = backend
                    logger.info(f"Using database backend: {name}")
                    return backend.connect()

            except Exception as e:
                error_msg = str(e)
                errors.append(f"{name}: {error_msg}")
                self._status_cache[name] = BackendStatus(
                    name=name,
                    is_healthy=False,
                    error_message=error_msg,
                )

                # Log fallback
                logger.warning(f"Backend {name} unavailable: {error_msg}")

                # Call fallback callback
                if self._on_fallback:
                    self._on_fallback(name, error_msg)

        # All backends failed
        error_summary = "; ".join(errors)
        raise ConnectionError(f"All database backends unavailable: {error_summary}")

    def health_check_all(self) -> dict[str, BackendStatus]:
        """
        Check health of all backends.

        Returns:
            Dict mapping backend names to status
        """
        results: dict[str, BackendStatus] = {}

        for backend in self._backends:
            name = backend.name

            try:
                import time

                start = time.perf_counter()
                is_healthy = backend.is_healthy()
                latency = (time.perf_counter() - start) * 1000

                results[name] = BackendStatus(
                    name=name,
                    is_healthy=is_healthy,
                    latency_ms=latency,
                )

            except Exception as e:
                results[name] = BackendStatus(
                    name=name,
                    is_healthy=False,
                    error_message=str(e),
                )

        self._status_cache.update(results)
        return results

    def reset(self) -> None:
        """Reset active backend and cache."""
        self._active_backend = None
        self._status_cache.clear()


class SimpleBackend(DatabaseBackend):
    """
    Simple backend implementation for testing/quick use.

    Usage:
        backend = SimpleBackend(
            name="sqlite",
            url="sqlite:///./app.db",
            connect_fn=lambda: create_engine("sqlite:///./app.db"),
            health_fn=lambda: True,
        )
    """

    def __init__(
        self,
        name: str,
        url: str,
        connect_fn: Callable[[], Any],
        health_fn: Callable[[], bool] | None = None,
        mask_url: bool = True,
    ):
        """
        Initialize simple backend.

        Args:
            name: Backend name
            url: Connection URL
            connect_fn: Function to create connection/engine
            health_fn: Optional health check function (default: always True)
            mask_url: Whether to mask secrets in URL
        """
        self._name = name
        self._url = url
        self._connect_fn = connect_fn
        self._health_fn = health_fn or (lambda: True)
        self._mask_url = mask_url

    @property
    def name(self) -> str:
        return self._name

    @property
    def url(self) -> str:
        if self._mask_url:
            return self._mask_secrets(self._url)
        return self._url

    def _mask_secrets(self, url: str) -> str:
        """Mask secrets in URL for logging."""
        import re

        # Mask password in URL
        pattern = r"(://[^:]+:)([^@]+)(@)"
        return re.sub(pattern, r"\1***\3", url)

    def is_healthy(self) -> bool:
        return self._health_fn()

    def connect(self) -> Any:
        return self._connect_fn()


def create_sqlite_fallback(
    path: str = "./fallback.db",
    async_driver: bool = True,
) -> SimpleBackend:
    """
    Create a SQLite fallback backend.

    Args:
        path: Path to SQLite file
        async_driver: If True, use aiosqlite driver

    Returns:
        SimpleBackend configured for SQLite
    """
    from .url_normalizer import normalize_async_url

    url = f"sqlite:///{path}"
    if async_driver:
        url = normalize_async_url(url)

    def connect():
        try:
            from sqlalchemy.ext.asyncio import create_async_engine

            return create_async_engine(url)
        except ImportError:
            from sqlalchemy import create_engine

            return create_engine(url.replace("+aiosqlite", ""))

    def health_check() -> bool:
        # SQLite is always "healthy" if file/dir is writable
        from pathlib import Path

        parent = Path(path).parent
        return parent.exists() or parent == Path(".")

    return SimpleBackend(
        name="sqlite_fallback",
        url=url,
        connect_fn=connect,
        health_fn=health_check,
    )
