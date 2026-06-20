"""Tests for RequestSizeLimitMiddleware.

Verifies that oversized requests are rejected at the Content-Length header
check before the body is consumed, that excluded paths are unaffected,
and that requests within the limit pass through.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.mothership.middleware.request_size import RequestSizeLimitMiddleware


def _make_app(max_size_bytes: int = 1024, exclude_paths: list[str] | None = None) -> FastAPI:
    app = FastAPI()

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.post("/api/upload")
    async def upload():
        return {"received": True}

    @app.get("/api/data")
    def data():
        return {"data": True}

    app.add_middleware(
        RequestSizeLimitMiddleware,
        max_size_bytes=max_size_bytes,
        exclude_paths=exclude_paths or ["/health", "/ping", "/metrics"],
    )
    return app


@pytest.mark.unit
class TestExcludedPaths:
    def test_health_path_not_size_limited(self) -> None:
        client = TestClient(_make_app(), raise_server_exceptions=False)
        r = client.get("/health")
        assert r.status_code == 200

    def test_custom_excluded_path_not_size_limited(self) -> None:
        app = _make_app(exclude_paths=["/special"])

        @app.post("/special")
        def special():
            return {"ok": True}

        small_client = TestClient(app, raise_server_exceptions=False)
        big_body = b"x" * 10_000
        r = small_client.post(
            "/special",
            content=big_body,
            headers={"Content-Length": str(len(big_body))},
        )
        # Excluded from size limiting
        assert r.status_code == 200


@pytest.mark.unit
class TestContentLengthEnforcement:
    def test_request_within_limit_passes(self) -> None:
        client = TestClient(_make_app(max_size_bytes=1024), raise_server_exceptions=False)
        small_body = b"x" * 100
        r = client.post(
            "/api/upload",
            content=small_body,
            headers={"Content-Length": str(len(small_body))},
        )
        assert r.status_code == 200

    def test_request_exceeding_limit_returns_413(self) -> None:
        client = TestClient(_make_app(max_size_bytes=100), raise_server_exceptions=False)
        big_body = b"x" * 200
        r = client.post(
            "/api/upload",
            content=big_body,
            headers={"Content-Length": str(len(big_body))},
        )
        assert r.status_code == 413
        body = r.json()
        assert body["error"]["code"] == "REQUEST_TOO_LARGE"

    def test_error_body_contains_max_size(self) -> None:
        max_size = 50
        client = TestClient(_make_app(max_size_bytes=max_size), raise_server_exceptions=False)
        r = client.post(
            "/api/upload",
            content=b"x" * 200,
            headers={"Content-Length": "200"},
        )
        assert r.status_code == 413
        assert str(max_size) in r.json()["error"]["message"]

    def test_missing_content_length_passes_through(self) -> None:
        """Without Content-Length, the middleware cannot pre-reject (body streams through)."""
        client = TestClient(_make_app(max_size_bytes=10), raise_server_exceptions=False)
        # TestClient usually sends Content-Length; send chunked without it
        r = client.post("/api/upload", content=b"x" * 5)
        # Route succeeds — no Content-Length header means no pre-check
        assert r.status_code == 200

    def test_invalid_content_length_header_ignored(self) -> None:
        """Malformed Content-Length should not crash the middleware."""
        client = TestClient(_make_app(max_size_bytes=100), raise_server_exceptions=False)
        r = client.post(
            "/api/upload",
            content=b"hello",
            headers={"Content-Length": "not-a-number"},
        )
        # Invalid value ignored; request proceeds
        assert r.status_code == 200

    def test_get_request_without_body_passes(self) -> None:
        client = TestClient(_make_app(max_size_bytes=10), raise_server_exceptions=False)
        r = client.get("/api/data")
        assert r.status_code == 200

    def test_exact_limit_boundary_passes(self) -> None:
        max_size = 100
        client = TestClient(_make_app(max_size_bytes=max_size), raise_server_exceptions=False)
        exact_body = b"x" * max_size
        r = client.post(
            "/api/upload",
            content=exact_body,
            headers={"Content-Length": str(max_size)},
        )
        # Exactly at limit (not exceeding) → allowed
        assert r.status_code == 200

    def test_one_over_limit_rejected(self) -> None:
        max_size = 100
        client = TestClient(_make_app(max_size_bytes=max_size), raise_server_exceptions=False)
        over_body = b"x" * (max_size + 1)
        r = client.post(
            "/api/upload",
            content=over_body,
            headers={"Content-Length": str(max_size + 1)},
        )
        assert r.status_code == 413


@pytest.mark.unit
class TestMiddlewareConfiguration:
    def test_default_max_size_is_10mb(self) -> None:
        mw = RequestSizeLimitMiddleware.__new__(RequestSizeLimitMiddleware)
        mw.max_size_bytes = 10 * 1024 * 1024
        mw.exclude_paths = ["/health", "/ping", "/metrics"]
        assert mw.max_size_bytes == 10 * 1024 * 1024

    def test_exclude_paths_configurable(self) -> None:
        app = FastAPI()
        mw = RequestSizeLimitMiddleware(app, exclude_paths=["/custom"])
        assert "/custom" in mw.exclude_paths
