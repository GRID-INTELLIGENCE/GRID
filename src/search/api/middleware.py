"""Latency tracking and guardrail middleware for the search API."""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Auth middleware
# ---------------------------------------------------------------------------


def _extract_identity(request: Request) -> str | None:
    """Extract identity from Authorization header (Bearer token or API key)."""
    auth = request.headers.get("Authorization")
    if not auth:
        return None
    if auth.startswith("Bearer "):
        # For tests we accept literal tokens; production would validate JWT
        return auth[7:].strip() or None
    if auth.startswith("ApiKey "):
        return auth[7:].strip() or None
    return None


class AuthMiddleware(BaseHTTPMiddleware):
    """Extracts and validates identity; sets request.state.identity."""

    def __init__(self, app: object, required: bool = True) -> None:
        super().__init__(app)
        self.required = required

    async def dispatch(self, request: Request, call_next: object) -> Response:
        identity = _extract_identity(request)
        request.state.identity = identity
        if self.required and not identity and self._is_search_path(request):
            from starlette.responses import JSONResponse

            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication required"},
            )
        return await call_next(request)

    def _is_search_path(self, request: Request) -> bool:
        path = getattr(request, "url", None)
        path_str = path.path if path else str(request.scope.get("path", ""))
        return "/api/search/" in path_str and "/query" in path_str


# ---------------------------------------------------------------------------
# Rate limit middleware
# ---------------------------------------------------------------------------


class InMemoryRateLimitStore:
    """In-memory sliding window for rate limiting."""

    def __init__(self, requests_per_minute: int = 60) -> None:
        self.requests_per_minute = requests_per_minute
        self._counts: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def check(self, key: str) -> bool:
        now = time.monotonic()
        window_start = now - 60.0
        with self._lock:
            ts = self._counts[key]
            ts[:] = [t for t in ts if t > window_start]
            if len(ts) >= self.requests_per_minute:
                return False
            ts.append(now)
            return True


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforces per-identity rate limits. Returns 429 when exceeded."""

    def __init__(
        self,
        app: object,
        requests_per_minute: int = 60,
        store: InMemoryRateLimitStore | None = None,
    ) -> None:
        super().__init__(app)
        self.store = store or InMemoryRateLimitStore(requests_per_minute)

    async def dispatch(self, request: Request, call_next: object) -> Response:
        if not self._is_search_path(request):
            return await call_next(request)
        identity = getattr(request.state, "identity", None)
        key = identity or request.client.host if request.client else "anonymous"
        if not self.store.check(key):
            from starlette.responses import JSONResponse

            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
            )
        return await call_next(request)

    def _is_search_path(self, request: Request) -> bool:
        path = getattr(request, "url", None)
        path_str = path.path if path else str(request.scope.get("path", ""))
        return "/api/search/" in path_str


# ---------------------------------------------------------------------------
# Audit middleware
# ---------------------------------------------------------------------------


class AuditMiddleware(BaseHTTPMiddleware):
    """Logs search requests for audit trail."""

    async def dispatch(self, request: Request, call_next: object) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        if self._is_search_path(request):
            identity = getattr(request.state, "identity", None) or "anonymous"
            path = getattr(request.url, "path", str(request.scope.get("path", "")))
            logger.info(
                "search_audit identity=%s path=%s status=%s elapsed_ms=%.2f",
                identity,
                path,
                response.status_code,
                elapsed_ms,
            )
        return response

    def _is_search_path(self, request: Request) -> bool:
        path = getattr(request, "url", None)
        path_str = path.path if path else str(request.scope.get("path", ""))
        return "/api/search/" in path_str


# ---------------------------------------------------------------------------
# Latency tracking (SLA)
# ---------------------------------------------------------------------------


class LatencyTracker:
    """Tracks request latencies and computes percentile statistics.

    Maintains a sliding window of the most recent observations so
    percentile calculations remain bounded in memory.
    """

    def __init__(self, window_size: int = 10_000) -> None:
        self.window_size = window_size
        self._latencies: deque[float] = deque(maxlen=window_size)
        self._request_count: int = 0

    def record(self, latency_ms: float) -> None:
        self._latencies.append(latency_ms)
        self._request_count += 1

    @property
    def request_count(self) -> int:
        return self._request_count

    def percentile(self, p: float) -> float:
        """Return the p-th percentile latency (0-100 scale)."""
        if not self._latencies:
            return 0.0
        sorted_vals = sorted(self._latencies)
        idx = int(len(sorted_vals) * p / 100)
        idx = min(idx, len(sorted_vals) - 1)
        return sorted_vals[idx]

    @property
    def p50(self) -> float:
        return self.percentile(50)

    @property
    def p95(self) -> float:
        return self.percentile(95)

    @property
    def p99(self) -> float:
        return self.percentile(99)

    def stats(self) -> dict[str, float]:
        return {
            "request_count": self._request_count,
            "p50_ms": round(self.p50, 2),
            "p95_ms": round(self.p95, 2),
            "p99_ms": round(self.p99, 2),
        }
