"""Tests for rate limiting middleware.

Covers two implementations:
- RateLimitMiddleware (in-memory, from middleware/__init__.py) — used in
  the main request pipeline when Redis is not configured.
- CognitiveRedisRateLimitMiddleware (from rate_limit_redis.py) — Redis-backed
  with cognitive-load adjustment; tested here via its in-memory fallback path.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI  # noqa: I001
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# In-memory RateLimitMiddleware (from __init__.py)
# ---------------------------------------------------------------------------


def _make_memory_app(requests_per_minute: int = 60, burst_size: int = 20) -> FastAPI:
    from application.mothership.middleware import RateLimitMiddleware

    app = FastAPI()

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.get("/api/data")
    def data():
        return {"data": True}

    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=requests_per_minute,
        burst_size=burst_size,
        exclude_paths=["/health", "/ping"],
    )
    return app


@pytest.mark.unit
class TestInMemoryRateLimitMiddleware:
    def test_excluded_path_bypasses_rate_limit(self) -> None:
        client = TestClient(_make_memory_app(), raise_server_exceptions=False)
        r = client.get("/health")
        assert r.status_code == 200
        assert "X-RateLimit-Limit" not in r.headers

    def test_within_burst_passes_with_headers(self) -> None:
        client = TestClient(_make_memory_app(burst_size=10), raise_server_exceptions=False)
        r = client.get("/api/data")
        assert r.status_code == 200
        assert "X-RateLimit-Limit" in r.headers
        assert "X-RateLimit-Remaining" in r.headers

    def test_burst_limit_triggers_429(self) -> None:
        # burst_size=2 means the 3rd request gets rejected
        client = TestClient(_make_memory_app(requests_per_minute=100, burst_size=2), raise_server_exceptions=False)
        client.get("/api/data")
        client.get("/api/data")
        r = client.get("/api/data")
        assert r.status_code == 429
        body = r.json()
        assert body["error"]["code"] == "RATE_LIMIT_EXCEEDED"
        assert "Retry-After" in r.headers

    def test_rate_limit_headers_reflect_remaining(self) -> None:
        client = TestClient(
            _make_memory_app(requests_per_minute=10, burst_size=10),
            raise_server_exceptions=False,
        )
        r1 = client.get("/api/data")
        r2 = client.get("/api/data")
        remaining1 = int(r1.headers["X-RateLimit-Remaining"])
        remaining2 = int(r2.headers["X-RateLimit-Remaining"])
        assert remaining2 < remaining1

    def test_api_key_gets_separate_bucket_from_ip(self) -> None:
        client = TestClient(
            _make_memory_app(requests_per_minute=100, burst_size=2),
            raise_server_exceptions=False,
        )
        # Exhaust the IP bucket
        client.get("/api/data")
        client.get("/api/data")
        assert client.get("/api/data").status_code == 429
        # API key gets its own bucket
        r_key = client.get("/api/data", headers={"X-API-Key": "my-key-12345678"})
        assert r_key.status_code == 200

    def test_reset_store_clears_limits(self) -> None:
        from application.mothership.middleware import RateLimitMiddleware

        mw = RateLimitMiddleware.__new__(RateLimitMiddleware)
        mw._store = {"ip:1.2.3.4": [1.0, 2.0, 3.0]}
        mw.reset_store()
        assert mw._store == {}

    def test_cleanup_removes_expired_entries(self) -> None:
        import time

        from application.mothership.middleware import RateLimitMiddleware

        mw = RateLimitMiddleware.__new__(RateLimitMiddleware)
        mw._store = {"ip:1.2.3.4": [time.time() - 120.0]}  # expired
        mw._request_count = 0
        mw.cleanup_interval = 1  # trigger on next call
        mw._cleanup_old_entries()
        assert mw._store["ip:1.2.3.4"] == []


# ---------------------------------------------------------------------------
# CognitiveRedisRateLimitMiddleware — in-memory fallback path
# (no Redis configured, falls back to _is_rate_limited_memory)
# ---------------------------------------------------------------------------


def _make_cognitive_app(requests_per_minute: int = 60) -> FastAPI:
    from application.mothership.middleware.rate_limit_redis import CognitiveRedisRateLimitMiddleware

    app = FastAPI()

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.get("/api/data")
    def data():
        return {"data": True}

    app.add_middleware(
        CognitiveRedisRateLimitMiddleware,
        requests_per_minute=requests_per_minute,
        redis_url=None,  # no Redis → in-memory fallback
        exclude_paths=["/health"],
    )
    return app


@pytest.mark.unit
class TestCognitiveRateLimitMiddleware:
    def test_excluded_path_bypasses(self) -> None:
        client = TestClient(_make_cognitive_app(), raise_server_exceptions=False)
        r = client.get("/health")
        assert r.status_code == 200
        assert "X-RateLimit-Limit" not in r.headers

    def test_within_limit_passes(self) -> None:
        client = TestClient(_make_cognitive_app(requests_per_minute=10), raise_server_exceptions=False)
        r = client.get("/api/data")
        assert r.status_code == 200
        assert "X-RateLimit-Remaining" in r.headers

    def test_limit_exceeded_returns_429(self) -> None:
        client = TestClient(_make_cognitive_app(requests_per_minute=2), raise_server_exceptions=False)
        client.get("/api/data")
        client.get("/api/data")
        r = client.get("/api/data")
        assert r.status_code == 429
        body = r.json()
        assert body["error"]["code"] == "COGNITIVE_RATE_LIMIT_EXCEEDED"

    def test_cognitive_adjustment_header_present(self) -> None:
        client = TestClient(_make_cognitive_app(requests_per_minute=10), raise_server_exceptions=False)
        r = client.get("/api/data")
        assert r.status_code == 200
        assert "X-Cognitive-Load-Adjustment" in r.headers
        # With no cognitive engine, adjustment factor = 1.0
        assert r.headers["X-Cognitive-Load-Adjustment"] == "1.00"

    def test_memory_rate_check_allows_within_limit(self) -> None:
        from application.mothership.middleware.rate_limit_redis import CognitiveRedisRateLimitMiddleware

        mw = CognitiveRedisRateLimitMiddleware.__new__(CognitiveRedisRateLimitMiddleware)
        mw.cognitive_engine = None
        mw.base_requests_per_minute = 5
        mw.cognitive_thresholds = {"low": 0.3, "medium": 0.6, "high": 0.8}
        mw._fallback_store = {}

        limited, remaining, effective = mw._is_rate_limited_memory("key", 5)
        assert limited is False
        assert remaining == 4

    def test_memory_rate_check_blocks_over_limit(self) -> None:
        from application.mothership.middleware.rate_limit_redis import CognitiveRedisRateLimitMiddleware

        mw = CognitiveRedisRateLimitMiddleware.__new__(CognitiveRedisRateLimitMiddleware)
        mw.cognitive_engine = None
        mw.base_requests_per_minute = 2
        mw.cognitive_thresholds = {"low": 0.3, "medium": 0.6, "high": 0.8}
        mw._fallback_store = {}

        mw._is_rate_limited_memory("key", 2)  # request 1
        mw._is_rate_limited_memory("key", 2)  # request 2
        limited, remaining, effective = mw._is_rate_limited_memory("key", 2)
        assert limited is True
        assert remaining == 0

    def test_cognitive_adjustment_factor_no_engine(self) -> None:
        from application.mothership.middleware.rate_limit_redis import CognitiveRedisRateLimitMiddleware

        mw = CognitiveRedisRateLimitMiddleware.__new__(CognitiveRedisRateLimitMiddleware)
        mw.cognitive_engine = None
        mw.cognitive_thresholds = {"low": 0.3, "medium": 0.6, "high": 0.8}
        assert mw._get_cognitive_adjustment_factor("any-key") == 1.0
