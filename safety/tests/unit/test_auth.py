"""
Unit tests for authentication and trust-tier resolution.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock

from jose import jwt

from safety.api.auth import (
    TrustTier,
    get_user_from_token,
)


def _make_request(
    *, bearer: str = "", api_key: str = "", client_ip: str = "127.0.0.1"
) -> MagicMock:
    """Create a mock FastAPI Request object."""
    request = MagicMock()
    headers = {}
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    if api_key:
        headers["X-API-Key"] = api_key
    request.headers = headers
    request.client = MagicMock()
    request.client.host = client_ip
    return request


class TestJWTAuth:
    def test_valid_jwt_returns_user(self):
        secret = os.environ["SAFETY_JWT_SECRET"]
        token = jwt.encode(
            {"sub": "user-123", "role": "verified"},
            secret,
            algorithm="HS256",
        )
        request = _make_request(bearer=token)
        user = get_user_from_token(request)
        assert user.id == "user-123"
        assert user.trust_tier == TrustTier.VERIFIED

    def test_invalid_jwt_falls_to_anon(self):
        request = _make_request(bearer="invalid.token.here")
        user = get_user_from_token(request)
        assert user.trust_tier == TrustTier.ANON
        assert "anon" in user.id

    def test_jwt_with_admin_role(self):
        secret = os.environ["SAFETY_JWT_SECRET"]
        token = jwt.encode(
            {"sub": "admin-1", "role": "admin"},
            secret,
            algorithm="HS256",
        )
        request = _make_request(bearer=token)
        user = get_user_from_token(request)
        assert user.trust_tier == TrustTier.PRIVILEGED


class TestAPIKeyAuth:
    def test_valid_api_key(self):
        request = _make_request(api_key="test-key-1")
        user = get_user_from_token(request)
        assert user.trust_tier == TrustTier.VERIFIED

    def test_invalid_api_key(self):
        request = _make_request(api_key="nonexistent-key")
        user = get_user_from_token(request)
        assert user.trust_tier == TrustTier.ANON


class TestAnonymous:
    def test_no_credentials(self):
        request = _make_request()
        user = get_user_from_token(request)
        assert user.trust_tier == TrustTier.ANON
        assert "127.0.0.1" in user.id
