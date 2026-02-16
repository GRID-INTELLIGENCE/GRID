"""
Unit tests for security headers middleware.

Covers: header presence, CSRF token generation/validation,
CSRF exempt paths, CORS validation, get_security_headers utility.
"""

from __future__ import annotations

import time

from starlette.requests import Request
from starlette.responses import Response

from safety.api.security_headers import (
    SecurityHeadersMiddleware,
    generate_csrf_token,
    get_security_headers,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_request(
    method: str = "GET",
    path: str = "/",
    headers: dict[str, str] | None = None,
    cookies: dict[str, str] | None = None,
    scheme: str = "https",
) -> Request:
    """Build a minimal ASGI Request for testing."""
    raw_headers: list[tuple[bytes, bytes]] = []
    if headers:
        for k, v in headers.items():
            raw_headers.append((k.lower().encode(), v.encode()))
    if cookies:
        cookie_str = "; ".join(f"{k}={v}" for k, v in cookies.items())
        raw_headers.append((b"cookie", cookie_str.encode()))

    port = 443 if scheme == "https" else 80
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "scheme": scheme,
        "headers": raw_headers,
        "query_string": b"",
        "root_path": "",
        "server": ("localhost", port),
    }
    return Request(scope)


# ---------------------------------------------------------------------------
# Security headers presence
# ---------------------------------------------------------------------------


class TestSecurityHeaders:
    """Verify all expected security headers are set."""

    def test_all_headers_present(self):
        headers = get_security_headers()
        expected_keys = [
            "content-security-policy",
            "x-frame-options",
            "x-content-type-options",
            "x-xss-protection",
            "referrer-policy",
            "permissions-policy",
            "cross-origin-embedder-policy",
            "cross-origin-opener-policy",
            "cross-origin-resource-policy",
            "x-permitted-cross-domain-policies",
            "x-dns-prefetch-control",
        ]
        lower_keys = {k.lower() for k in headers}
        for key in expected_keys:
            assert key in lower_keys, f"Missing header: {key}"

    def test_hsts_present_on_https(self):
        """HSTS is only added when scheme is https."""
        middleware = SecurityHeadersMiddleware(None)
        response = Response()
        # Build a proper https request
        request = _make_request(scheme="https")
        middleware._add_security_headers(response, request)
        lower_headers = {k.lower(): v for k, v in response.headers.items()}
        assert "strict-transport-security" in lower_headers

    def test_hsts_absent_on_http(self):
        """HSTS should NOT be added for plain http."""
        middleware = SecurityHeadersMiddleware(None)
        response = Response()
        request = _make_request(scheme="http")
        middleware._add_security_headers(response, request)
        lower_headers = {k.lower(): v for k, v in response.headers.items()}
        assert "strict-transport-security" not in lower_headers

    def test_frame_options_deny(self):
        headers = get_security_headers()
        lower_headers = {k.lower(): v for k, v in headers.items()}
        assert lower_headers["x-frame-options"] == "DENY"

    def test_content_type_nosniff(self):
        headers = get_security_headers()
        lower_headers = {k.lower(): v for k, v in headers.items()}
        assert lower_headers["x-content-type-options"] == "nosniff"


# ---------------------------------------------------------------------------
# CSRF token generation + validation
# ---------------------------------------------------------------------------


class TestCSRFTokens:
    """Tests for CSRF token generation and validation."""

    def test_generate_and_validate(self):
        middleware = SecurityHeadersMiddleware(None, csrf_secret="test-secret")
        token = middleware.get_csrf_token("session-1")
        assert middleware._validate_csrf_token(token, "session-1") is True

    def test_invalid_session_fails(self):
        middleware = SecurityHeadersMiddleware(None, csrf_secret="test-secret")
        token = middleware.get_csrf_token("session-1")
        assert middleware._validate_csrf_token(token, "session-WRONG") is False

    def test_tampered_token_fails(self):
        middleware = SecurityHeadersMiddleware(None, csrf_secret="test-secret")
        token = middleware.get_csrf_token("session-1")
        tampered = token[:-4] + "XXXX"
        assert middleware._validate_csrf_token(tampered, "session-1") is False

    def test_expired_token_fails(self):
        middleware = SecurityHeadersMiddleware(None, csrf_secret="test-secret")
        # Manually create a token with old timestamp
        import hashlib
        import hmac

        old_ts = str(int(time.time()) - 600)  # 10 min ago, threshold is 5 min
        msg = f"session-1:{old_ts}"
        sig = hmac.new(b"test-secret", msg.encode(), hashlib.sha256).hexdigest()
        expired_token = f"{old_ts}:{sig}"
        assert middleware._validate_csrf_token(expired_token, "session-1") is False

    def test_malformed_token_fails(self):
        middleware = SecurityHeadersMiddleware(None, csrf_secret="test-secret")
        assert middleware._validate_csrf_token("not-a-valid-token", "s") is False
        assert middleware._validate_csrf_token("", "s") is False

    def test_standalone_generate_csrf_token(self):
        token = generate_csrf_token("my-session", secret="fixed-secret")
        assert ":" in token
        parts = token.split(":", 1)
        assert parts[0].isdigit()


# ---------------------------------------------------------------------------
# CSRF exempt paths
# ---------------------------------------------------------------------------


class TestCSRFExemptPaths:
    """Verify CSRF-exempt prefixes bypass validation."""

    def test_exempt_prefixes(self):
        middleware = SecurityHeadersMiddleware(None)
        exempt_paths = ["/infer", "/privacy/scan", "/health", "/metrics", "/observe/stream", "/review/123", "/v1/check"]
        for path in exempt_paths:
            assert any(path.startswith(p) for p in middleware._CSRF_EXEMPT_PREFIXES), (
                f"Path {path} should be CSRF exempt"
            )


# ---------------------------------------------------------------------------
# CORS check
# ---------------------------------------------------------------------------


class TestCORSCheck:
    """Tests for CORS origin validation."""

    def test_allowed_origin_passes(self):
        middleware = SecurityHeadersMiddleware(None, allowed_origins={"https://app.example.com"})
        request = _make_request(headers={"origin": "https://app.example.com"})
        assert middleware._check_cors(request) is True

    def test_disallowed_origin_fails(self):
        middleware = SecurityHeadersMiddleware(None, allowed_origins={"https://app.example.com"})
        request = _make_request(headers={"origin": "https://evil.com"})
        assert middleware._check_cors(request) is False

    def test_no_origin_header_passes(self):
        middleware = SecurityHeadersMiddleware(None)
        request = _make_request()
        assert middleware._check_cors(request) is True


# ---------------------------------------------------------------------------
# get_security_headers utility
# ---------------------------------------------------------------------------


class TestGetSecurityHeaders:
    """Tests for the get_security_headers() utility."""

    def test_returns_dict(self):
        headers = get_security_headers()
        assert isinstance(headers, dict)
        assert len(headers) > 5

    def test_referrer_policy_present(self):
        headers = get_security_headers()
        lower_headers = {k.lower(): v for k, v in headers.items()}
        assert "referrer-policy" in lower_headers
        assert lower_headers["referrer-policy"] == "strict-origin-when-cross-origin"
