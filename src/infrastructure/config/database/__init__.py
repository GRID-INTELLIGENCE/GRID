"""
Database Configuration Submodule.

Provides:
- Fallback chain for database backends
- URL normalization for async drivers
- Connection retry with exponential backoff
- Health check utilities

Extracted from Mothership's database engine patterns.
"""

from .fallback import DatabaseBackend, DatabaseFallbackChain
from .retry import ConnectionRetry, RetryConfig
from .url_normalizer import normalize_async_url, supports_async

__all__ = [
    # Fallback
    "DatabaseBackend",
    "DatabaseFallbackChain",
    # Retry
    "ConnectionRetry",
    "RetryConfig",
    # URL Normalization
    "normalize_async_url",
    "supports_async",
]
