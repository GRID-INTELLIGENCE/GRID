"""Tests for security headers middleware.

Covers both implementations:
- application.mothership.middleware.security_headers.SecurityHeadersMiddleware
  (standalone module, scheme-based HSTS)
- application.mothership.middleware.SecurityHeadersMiddleware
  (from __init__, adds Cache-Control on auth/admin paths)
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Standalone security_headers module
# ---------------------------------------------------------------------------


def _make_standalone_app() -> FastAPI:
    from application.mothership.middleware.security_headers import (
        SecurityHeadersMiddleware as StandaloneHeaders,
    )

    app = FastAPI()

    @app.get("/api/test")
    def test_route():
        return {"ok": True}

    @app.get("/api/v1/auth/login")
    def login():
        return {"token": "abc"}

    app.add_middleware(StandaloneHeaders)
    return app


@pytest.mark.unit
class TestStandaloneSecurityHeaders:
    def test_x_content_type_options(self) -> None:
        client = TestClient(_make_standalone_app(), raise_server_exceptions=False)
        r = client.get("/api/test")
        assert r.headers.get("X-Content-Type-Options") == "nosniff"

    def test_x_frame_options(self) -> None:
        client = TestClient(_make_standalone_app(), raise_server_exceptions=False)
        r = client.get("/api/test")
        assert r.headers.get("X-Frame-Options") == "DENY"

    def test_x_xss_protection(self) -> None:
        client = TestClient(_make_standalone_app(), raise_server_exceptions=False)
        r = client.get("/api/test")
        assert r.headers.get("X-XSS-Protection") == "1; mode=block"

    def test_referrer_policy(self) -> None:
        client = TestClient(_make_standalone_app(), raise_server_exceptions=False)
        r = client.get("/api/test")
        assert r.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    def test_content_security_policy_present(self) -> None:
        client = TestClient(_make_standalone_app(), raise_server_exceptions=False)
        r = client.get("/api/test")
        csp = r.headers.get("Content-Security-Policy", "")
        assert "default-src" in csp
        assert "object-src 'none'" in csp

    def test_permissions_policy_present(self) -> None:
        client = TestClient(_make_standalone_app(), raise_server_exceptions=False)
        r = client.get("/api/test")
        pp = r.headers.get("Permissions-Policy", "")
        assert "camera=()" in pp
        assert "geolocation=()" in pp

    def test_hsts_absent_on_http(self) -> None:
        client = TestClient(_make_standalone_app(), raise_server_exceptions=False)
        r = client.get("/api/test")
        assert "Strict-Transport-Security" not in r.headers

    def test_hsts_present_on_https(self) -> None:
        """Simulate HTTPS by calling through an HTTPS URL via the test client."""
        from application.mothership.middleware.security_headers import (
            SecurityHeadersMiddleware as StandaloneHeaders,
        )

        app = FastAPI()

        @app.get("/api/test")
        def test_route():
            return {"ok": True}

        app.add_middleware(StandaloneHeaders)
        # TestClient uses http by default; we set base_url to https to simulate
        client = TestClient(app, base_url="https://testserver", raise_server_exceptions=False)
        r = client.get("/api/test")
        assert "Strict-Transport-Security" in r.headers
        assert "max-age=" in r.headers["Strict-Transport-Security"]


# ---------------------------------------------------------------------------
# __init__.py SecurityHeadersMiddleware (richer variant)
# ---------------------------------------------------------------------------


def _make_init_app(path: str = "/api/test") -> FastAPI:
    from application.mothership.middleware import SecurityHeadersMiddleware as InitHeaders

    app = FastAPI()

    @app.get("/api/test")
    def test_route():
        return {"ok": True}

    @app.get("/api/v1/auth/login")
    def login():
        return {"token": "abc"}

    @app.get("/api/v1/admin/users")
    def admin():
        return {"users": []}

    app.add_middleware(InitHeaders)
    return app


@pytest.mark.unit
class TestInitSecurityHeaders:
    def test_core_headers_present(self) -> None:
        client = TestClient(_make_init_app(), raise_server_exceptions=False)
        r = client.get("/api/test")
        assert r.headers.get("X-Content-Type-Options") == "nosniff"
        assert r.headers.get("X-Frame-Options") == "DENY"
        assert r.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    def test_cache_control_on_auth_path(self) -> None:
        client = TestClient(_make_init_app(), raise_server_exceptions=False)
        r = client.get("/api/v1/auth/login")
        cache = r.headers.get("Cache-Control", "")
        assert "no-store" in cache

    def test_cache_control_on_admin_path(self) -> None:
        client = TestClient(_make_init_app(), raise_server_exceptions=False)
        r = client.get("/api/v1/admin/users")
        cache = r.headers.get("Cache-Control", "")
        assert "no-store" in cache

    def test_no_cache_control_on_regular_path(self) -> None:
        client = TestClient(_make_init_app(), raise_server_exceptions=False)
        r = client.get("/api/test")
        # Regular API paths should not carry Cache-Control from this middleware
        assert "no-store" not in r.headers.get("Cache-Control", "")

    def test_custom_headers_forwarded(self) -> None:
        from application.mothership.middleware import SecurityHeadersMiddleware as InitHeaders

        app = FastAPI()

        @app.get("/api/test")
        def test_route():
            return {"ok": True}

        app.add_middleware(InitHeaders, custom_headers={"X-Powered-By": "GRID"})
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/test")
        assert r.headers.get("X-Powered-By") == "GRID"

    def test_csp_overridable(self) -> None:
        from application.mothership.middleware import SecurityHeadersMiddleware as InitHeaders

        app = FastAPI()

        @app.get("/api/test")
        def test_route():
            return {"ok": True}

        custom_csp = "default-src 'none'"
        app.add_middleware(InitHeaders, content_security_policy=custom_csp)
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/test")
        assert r.headers.get("Content-Security-Policy") == custom_csp
