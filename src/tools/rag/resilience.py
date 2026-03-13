"""RAG resilience layer using apiguard primitives.

Provides pre-configured circuit breakers, retry handlers, and rate-limit
buckets for RAG service integrations.  Uses apiguard directly — no dependency
on ``application.mothership``.

LIMITATIONS:
    Keyword/threshold-based resilience is not a substitute for full
    observability.  Circuit breaker thresholds should be tuned per
    deployment environment.

Each service type shares a single circuit breaker instance so that all
callers converge on the same health signal (e.g. if Ollama is down, every
OllamaReranker *and* OllamaLocalLLM see the open circuit immediately).
"""

from __future__ import annotations

import contextlib
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy apiguard import with graceful no-op fallback
# ---------------------------------------------------------------------------

try:
    from apiguard import CircuitBreaker, RetryHandler, TokenBucket
    from apiguard.adapters.httpx import AsyncRateLimitedClient
    from apiguard.exceptions import CircuitOpenError

    _APIGUARD_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover
    _APIGUARD_AVAILABLE = False
    CircuitOpenError = RuntimeError  # type: ignore[assignment,misc]
    logger.debug("apiguard not installed — RAG resilience layer disabled (no-op)")


# ---------------------------------------------------------------------------
# No-op shims used when apiguard is absent
# ---------------------------------------------------------------------------


class _NoOpBreaker:
    """Transparent context-manager that never trips."""

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return None

    # Satisfy the subset of CircuitBreaker API used by providers
    def is_open(self) -> bool:
        return False

    def is_closed(self) -> bool:
        return True

    def reset(self) -> None:
        pass


_NOOP_BREAKER = _NoOpBreaker()

# ---------------------------------------------------------------------------
# Service-level singleton registries
# ---------------------------------------------------------------------------

_circuit_breakers: dict[str, Any] = {}
_token_buckets: dict[str, Any] = {}

# Pre-tuned defaults per service type.
# Keys: service name → (failure_threshold, recovery_timeout, success_threshold)
_CIRCUIT_DEFAULTS: dict[str, tuple[int, float, int]] = {
    "ollama": (3, 30.0, 1),
    "openai": (5, 60.0, 1),
    "openai_compatible": (4, 45.0, 1),
    "anthropic": (5, 60.0, 1),
    "gemini": (5, 60.0, 1),
}

# Keys: service name → (capacity, refill_rate)
_BUCKET_DEFAULTS: dict[str, tuple[int, float]] = {
    "ollama": (30, 5.0),
    "openai": (60, 10.0),
    "openai_compatible": (40, 5.0),
    "anthropic": (40, 5.0),
    "gemini": (40, 5.0),
}

# Retry defaults: (max_retries, base_delay, max_delay)
_RETRY_DEFAULTS: dict[str, tuple[int, float, float]] = {
    "ollama": (2, 0.5, 10.0),
    "openai": (3, 1.0, 30.0),
    "openai_compatible": (3, 1.0, 30.0),
    "anthropic": (3, 1.0, 30.0),
    "gemini": (3, 1.0, 30.0),
}


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------


def get_circuit_breaker(service: str) -> Any:
    """Return the shared :class:`CircuitBreaker` for *service*.

    Creates one on first call; subsequent calls return the same instance.
    Returns a transparent no-op when apiguard is not installed.
    """
    if not _APIGUARD_AVAILABLE:
        return _NOOP_BREAKER
    if service not in _circuit_breakers:
        ft, rt, st = _CIRCUIT_DEFAULTS.get(service, (5, 60.0, 1))
        _circuit_breakers[service] = CircuitBreaker(
            failure_threshold=ft,
            recovery_timeout=rt,
            success_threshold=st,
        )
    return _circuit_breakers[service]


def get_token_bucket(service: str) -> Any:
    """Return the shared :class:`TokenBucket` for *service*.

    Returns ``None`` when apiguard is not installed (caller must handle).
    """
    if not _APIGUARD_AVAILABLE:
        return None
    if service not in _token_buckets:
        cap, rate = _BUCKET_DEFAULTS.get(service, (60, 10.0))
        _token_buckets[service] = TokenBucket(capacity=cap, refill_rate=rate)
    return _token_buckets[service]


def get_retry_handler(service: str) -> Any:
    """Create a new :class:`RetryHandler` for *service*.

    Retry handlers are stateless per-request, so a fresh instance is fine.
    Returns ``None`` when apiguard is not installed.
    """
    if not _APIGUARD_AVAILABLE:
        return None
    mr, bd, md = _RETRY_DEFAULTS.get(service, (3, 1.0, 30.0))
    return RetryHandler(max_retries=mr, base_delay=bd, max_delay=md)


# ---------------------------------------------------------------------------
# Convenience: pre-wired async client
# ---------------------------------------------------------------------------


def create_async_resilient_client(
    service: str,
    base_url: str | None = None,
    timeout: float = 30.0,
    headers: dict[str, str] | None = None,
) -> Any:
    """Build an :class:`AsyncRateLimitedClient` pre-configured for *service*.

    The returned client must be used as an ``async with`` context manager.
    Falls back to a plain ``httpx.AsyncClient`` when apiguard is absent.
    """
    if not _APIGUARD_AVAILABLE:
        import httpx

        return httpx.AsyncClient(
            base_url=base_url or "",
            timeout=timeout,
            headers=headers or {},
        )
    return AsyncRateLimitedClient(
        bucket=get_token_bucket(service),
        retry=get_retry_handler(service),
        breaker=get_circuit_breaker(service),
        base_url=base_url,
        timeout=timeout,
        headers=headers,
    )


# ---------------------------------------------------------------------------
# Convenience: sync circuit-breaker guard
# ---------------------------------------------------------------------------


def guarded_call(service: str, fn: Any, *args: Any, **kwargs: Any) -> Any:
    """Execute *fn* inside the circuit breaker for *service* (sync).

    Raises :class:`CircuitOpenError` if the circuit is open.
    """
    breaker = get_circuit_breaker(service)
    with breaker:
        return fn(*args, **kwargs)


async def async_guarded_call(service: str, fn: Any, *args: Any, **kwargs: Any) -> Any:
    """Execute an awaitable *fn* inside the circuit breaker for *service*.

    Raises :class:`CircuitOpenError` if the circuit is open.
    """
    breaker = get_circuit_breaker(service)
    with breaker:
        return await fn(*args, **kwargs)


# Re-export for convenience
__all__ = [
    "CircuitOpenError",
    "async_guarded_call",
    "create_async_resilient_client",
    "get_circuit_breaker",
    "get_retry_handler",
    "get_token_bucket",
    "guarded_call",
]
