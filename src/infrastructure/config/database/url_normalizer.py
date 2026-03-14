"""
Database URL Normalization.

Normalizes database URLs for async drivers:
- sqlite:/// → sqlite+aiosqlite:///
- postgresql:// → postgresql+asyncpg://
- postgres:// → postgresql+asyncpg://

Extracted from Mothership's _normalize_async_db_url pattern.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


# Mapping of sync drivers to async drivers
ASYNC_DRIVER_MAP = {
    "sqlite": "aiosqlite",
    "postgresql": "asyncpg",
    "postgres": "asyncpg",
    "mysql": "aiomysql",
    "mariadb": "aiomysql",
}

# Databases that have async driver support
ASYNC_SUPPORTED = frozenset(ASYNC_DRIVER_MAP.keys())

# Databases that are sync-only (no async driver)
SYNC_ONLY = frozenset(["databricks", "oracle", "mssql"])


@dataclass(frozen=True, slots=True)
class ParsedURL:
    """Immutable parsed database URL."""

    scheme: str
    driver: str | None
    username: str | None
    password: str | None
    host: str | None
    port: int | None
    database: str | None
    query: dict[str, str]

    @property
    def has_async_driver(self) -> bool:
        """Check if URL uses async driver."""
        if self.driver:
            return any(
                async_driver in self.driver
                for async_driver in ["aiosqlite", "asyncpg", "aiomysql"]
            )
        return False

    @property
    def is_sync_only(self) -> bool:
        """Check if database type has no async support."""
        return self.scheme in SYNC_ONLY


def normalize_async_url(url: str, *, force: bool = False) -> str:
    """
    Normalize database URL for async driver.

    Adds async driver suffix if not present:
    - sqlite:///path → sqlite+aiosqlite:///path
    - postgresql://host/db → postgresql+asyncpg://host/db

    Args:
        url: Database connection URL
        force: If True, normalize even if already has driver

    Returns:
        Normalized URL with async driver

    Examples:
        >>> normalize_async_url("sqlite:///./app.db")
        'sqlite+aiosqlite:///./app.db'
        >>> normalize_async_url("postgresql://localhost/mydb")
        'postgresql+asyncpg://localhost/mydb'
        >>> normalize_async_url("databricks://...")
        'databricks://...'  # No async support
    """
    url = (url or "").strip()

    if not url:
        return url

    # Parse URL
    parsed = parse_database_url(url)

    # Skip sync-only databases
    if parsed.is_sync_only:
        return url

    # Check if already has async driver
    if parsed.has_async_driver and not force:
        return url

    # Get async driver for scheme
    async_driver = ASYNC_DRIVER_MAP.get(parsed.scheme)
    if not async_driver:
        # Unknown scheme, return as-is
        return url

    # Build normalized URL
    return _build_async_url(url, parsed.scheme, async_driver)


def _build_async_url(original_url: str, scheme: str, async_driver: str) -> str:
    """Build async URL from original URL."""
    # Handle special case: SQLite relative paths
    if scheme == "sqlite":
        # sqlite:///path → sqlite+aiosqlite:///path
        if original_url.startswith("sqlite:///"):
            return original_url.replace("sqlite:///", f"sqlite+{async_driver}:///", 1)
        # sqlite:///:memory: → sqlite+aiosqlite:///:memory:
        elif original_url.startswith("sqlite://"):
            return original_url.replace("sqlite://", f"sqlite+{async_driver}://", 1)

    # Handle postgresql:// and postgres://
    if scheme in ("postgresql", "postgres"):
        # Check if already has driver
        if "+" in original_url.split("://")[0]:
            # Already has driver, replace it
            pattern = rf"^{re.escape(scheme)}\+[a-z]+://"
            return re.sub(pattern, f"{scheme}+{async_driver}://", original_url)
        else:
            # No driver, add async driver
            return original_url.replace(f"{scheme}://", f"{scheme}+{async_driver}://", 1)

    # Handle mysql://
    if scheme == "mysql":
        if "+" in original_url.split("://")[0]:
            pattern = r"^mysql\+[a-z]+://"
            return re.sub(pattern, f"mysql+{async_driver}://", original_url)
        else:
            return original_url.replace("mysql://", f"mysql+{async_driver}://", 1)

    # Fallback: generic replacement
    return original_url.replace(f"{scheme}://", f"{scheme}+{async_driver}://", 1)


def parse_database_url(url: str) -> ParsedURL:
    """
    Parse database URL into components.

    Args:
        url: Database connection URL

    Returns:
        ParsedURL with components
    """
    url = (url or "").strip()

    # Handle SQLite special case
    if url.startswith("sqlite:///"):
        return ParsedURL(
            scheme="sqlite",
            driver=None,
            username=None,
            password=None,
            host=None,
            port=None,
            database=url.replace("sqlite:///", ""),
            query={},
        )

    # Handle sqlite:///:memory:
    if url.startswith("sqlite://"):
        return ParsedURL(
            scheme="sqlite",
            driver=None,
            username=None,
            password=None,
            host=None,
            port=None,
            database=url.replace("sqlite://", ""),
            query={},
        )

    # Parse standard URL
    try:
        parsed = urlparse(url)

        # Extract scheme and driver
        scheme = parsed.scheme
        driver = None
        if "+" in scheme:
            scheme, driver = scheme.split("+", 1)

        # Extract credentials
        username = parsed.username
        password = parsed.password

        # Extract host and port
        host = parsed.hostname
        port = parsed.port

        # Extract database
        database = parsed.path.lstrip("/") if parsed.path else None

        # Extract query params
        query = {}
        if parsed.query:
            from urllib.parse import parse_qs

            for key, values in parse_qs(parsed.query).items():
                query[key] = values[0] if values else ""

        return ParsedURL(
            scheme=scheme,
            driver=driver,
            username=username,
            password=password,
            host=host,
            port=port,
            database=database,
            query=query,
        )

    except Exception:
        # Fallback for malformed URLs
        return ParsedURL(
            scheme="unknown",
            driver=None,
            username=None,
            password=None,
            host=None,
            port=None,
            database=None,
            query={},
        )


def supports_async(url: str) -> bool:
    """
    Check if database URL supports async operations.

    Args:
        url: Database connection URL

    Returns:
        True if async is supported
    """
    parsed = parse_database_url(url)

    # Already has async driver
    if parsed.has_async_driver:
        return True

    # Sync-only databases
    if parsed.is_sync_only:
        return False

    # Check if scheme has async driver available
    return parsed.scheme in ASYNC_SUPPORTED


def mask_url_secrets(url: str, mask: str = "***") -> str:
    """
    Mask secrets in database URL for logging.

    Args:
        url: Database connection URL
        mask: Mask string to use

    Returns:
        URL with secrets masked

    Examples:
        >>> mask_url_secrets("postgresql://user:secret@localhost/db")
        'postgresql://user:***@localhost/db'
        >>> mask_url_secrets("databricks://token:dapi123@host")
        'databricks://token:***@host'
    """
    url = (url or "").strip()

    if not url:
        return url

    # Mask password in standard URL format
    pattern = r"(://[^:]+:)([^@]+)(@)"
    masked = re.sub(pattern, rf"\1{mask}\3", url)

    # Mask token in databricks URL
    if "databricks://token:" in masked:
        pattern = r"(databricks://token:)([^@]+)(@)"
        masked = re.sub(pattern, rf"\1{mask}\3", masked)

    return masked


def build_url(
    scheme: str,
    *,
    host: str | None = None,
    port: int | None = None,
    database: str | None = None,
    username: str | None = None,
    password: str | None = None,
    driver: str | None = None,
    query: dict[str, str] | None = None,
) -> str:
    """
    Build database URL from components.

    Args:
        scheme: Database scheme (sqlite, postgresql, etc.)
        host: Hostname
        port: Port number
        database: Database name/path
        username: Username
        password: Password
        driver: Driver name (aiosqlite, asyncpg, etc.)
        query: Query parameters

    Returns:
        Constructed URL
    """
    # Build scheme with driver
    full_scheme = f"{scheme}+{driver}" if driver else scheme

    # Handle SQLite special case
    if scheme == "sqlite":
        return f"{full_scheme}:///{database or ':memory:'}"

    # Build standard URL
    netloc = ""
    if username:
        if password:
            netloc = f"{username}:{password}@{host or 'localhost'}"
        else:
            netloc = f"{username}@{host or 'localhost'}"
    else:
        netloc = host or "localhost"

    if port:
        netloc = f"{netloc}:{port}"

    path = f"/{database}" if database else ""

    query_str = ""
    if query:
        from urllib.parse import urlencode

        query_str = f"?{urlencode(query)}"

    return f"{full_scheme}://{netloc}{path}{query_str}"
