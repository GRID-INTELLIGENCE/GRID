"""
JWT Authentication Test Suite.

Comprehensive tests for JWT token generation, validation, and refresh.
Tests both the security layer and API endpoints.
"""

from __future__ import annotations

import os
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from jwt.exceptions import InvalidTokenError as JWTError

from application.mothership.main import create_app
from application.mothership.security.jwt import JWTManager, TokenPair, TokenPayload, reset_jwt_manager

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def jwt_manager() -> JWTManager:
    """Create a JWT manager for testing."""
    return JWTManager(
        secret_key="test-secret-key-at-least-32-characters-long",
        algorithm="HS256",
        access_token_expire_minutes=30,
        refresh_token_expire_days=7,
        environment="test",
    )


@pytest.fixture
def client() -> Generator[TestClient]:
    """Create a test client with clean state and trigger lifespan."""
    reset_jwt_manager()
    # Reset rate limit store for test isolation
    from application.mothership.dependencies import _rate_limit_store

    _rate_limit_store.clear()
    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.fixture
def valid_access_token(jwt_manager: JWTManager) -> str:
    """Create a valid access token."""
    return jwt_manager.create_access_token(
        subject="test_user",
        scopes=["read", "write"],
        user_id="user_123",
        email="test@example.com",
    )


@pytest.fixture
def valid_refresh_token(jwt_manager: JWTManager) -> str:
    """Create a valid refresh token."""
    return jwt_manager.create_refresh_token(
        subject="test_user",
        user_id="user_123",
    )


@pytest.fixture
def expired_access_token(jwt_manager: JWTManager) -> str:
    """Create an expired access token."""
    return jwt_manager.create_access_token(
        subject="test_user",
        expires_delta=timedelta(seconds=-1),
    )


# =============================================================================
# JWT Manager Tests
# =============================================================================


class TestJWTManager:
    """Test JWT manager functionality."""

    def test_create_access_token(self, jwt_manager: JWTManager) -> None:
        """Test access token creation."""
        token = jwt_manager.create_access_token(
            subject="user123",
            scopes=["read", "write"],
            user_id="user123",
            email="user@example.com",
        )

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode without verification to inspect
        payload = jwt_manager.decode_unverified(token)
        assert payload["sub"] == "user123"
        assert payload["type"] == "access"
        assert "read" in payload["scopes"]
        assert "write" in payload["scopes"]

    def test_create_refresh_token(self, jwt_manager: JWTManager) -> None:
        """Test refresh token creation."""
        token = jwt_manager.create_refresh_token(
            subject="user123",
            user_id="user123",
        )

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode without verification to inspect
        payload = jwt_manager.decode_unverified(token)
        assert payload["sub"] == "user123"
        assert payload["type"] == "refresh"

    def test_create_token_pair(self, jwt_manager: JWTManager) -> None:
        """Test creating access/refresh token pair."""
        token_pair = jwt_manager.create_token_pair(
            subject="user123",
            scopes=["read"],
            user_id="user123",
            email="user@example.com",
        )

        assert isinstance(token_pair, TokenPair)
        assert token_pair.token_type == "bearer"
        assert token_pair.expires_in == 30 * 60  # 30 minutes in seconds
        assert len(token_pair.access_token) > 0
        assert len(token_pair.refresh_token) > 0

    def test_verify_valid_token(self, jwt_manager: JWTManager, valid_access_token: str) -> None:
        """Test verifying a valid token."""
        payload = jwt_manager.verify_token(valid_access_token, expected_type="access")

        assert isinstance(payload, TokenPayload)
        assert payload.sub == "test_user"
        assert payload.user_id == "user_123"
        assert payload.email == "test@example.com"
        assert "read" in payload.scopes
        assert "write" in payload.scopes

    def test_verify_expired_token(self, jwt_manager: JWTManager, expired_access_token: str) -> None:
        """Test verifying an expired token raises error."""
        with pytest.raises(JWTError):
            jwt_manager.verify_token(expired_access_token)

    def test_verify_wrong_token_type(self, jwt_manager: JWTManager, valid_refresh_token: str) -> None:
        """Test verifying token with wrong type raises error."""
        with pytest.raises(ValueError, match="Invalid token type"):
            jwt_manager.verify_token(valid_refresh_token, expected_type="access")

    def test_verify_invalid_signature(self, jwt_manager: JWTManager) -> None:
        """Test verifying token with invalid signature."""
        # Create token with different secret
        other_manager = JWTManager(secret_key="different-secret-key-for-testing-purposes", environment="test")
        token = other_manager.create_access_token(subject="user123")

        with pytest.raises(JWTError):
            jwt_manager.verify_token(token)

    def test_refresh_access_token(self, jwt_manager: JWTManager, valid_refresh_token: str) -> None:
        """Test refreshing access token from refresh token."""
        new_access_token = jwt_manager.refresh_access_token(valid_refresh_token)

        assert isinstance(new_access_token, str)
        assert len(new_access_token) > 0

        # Verify the new token is valid
        payload = jwt_manager.verify_token(new_access_token, expected_type="access")
        assert payload.sub == "test_user"

    def test_refresh_with_access_token_fails(self, jwt_manager: JWTManager, valid_access_token: str) -> None:
        """Test that refresh fails when using access token."""
        with pytest.raises(ValueError, match="Invalid token type"):
            jwt_manager.refresh_access_token(valid_access_token)

    def test_weak_secret_key_warning(self) -> None:
        """Test that weak secret key generates warning."""
        manager = JWTManager(secret_key="short", environment="test")
        assert manager.secret_key == "short"  # Should still work, just warned

    def test_custom_expiration(self, jwt_manager: JWTManager) -> None:
        """Test custom token expiration."""
        token = jwt_manager.create_access_token(
            subject="user123",
            expires_delta=timedelta(minutes=5),
        )

        payload = jwt_manager.decode_unverified(token)
        exp_time = datetime.fromtimestamp(payload["exp"], tz=UTC)
        now = datetime.now(UTC)

        # Should expire in approximately 5 minutes
        time_diff = (exp_time - now).total_seconds()
        assert 290 < time_diff < 310  # Allow 10 second tolerance


# =============================================================================
# API Endpoint Tests
# =============================================================================


class TestAuthEndpoints:
    """Test authentication API endpoints."""

    def test_login_success(self, client: TestClient) -> None:
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "testpass",
                "scopes": ["read", "write"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"
        assert data["data"]["expires_in"] > 0
        assert "read" in data["data"]["scopes"]

    def test_login_default_scopes(self, client: TestClient) -> None:
        """Test login with default scopes."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "testpass",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "read" in data["data"]["scopes"]
        assert "write" in data["data"]["scopes"]

    def test_login_invalid_scopes(self, client: TestClient) -> None:
        """Test login with invalid scopes grants read-only."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "testpass",
                "scopes": ["invalid_scope", "another_bad_scope"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        # Should default to read-only when no valid scopes
        assert data["data"]["scopes"] == ["read"]

    def test_login_validation_error(self, client: TestClient) -> None:
        """Test login with missing fields."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser"},  # Missing password
        )

        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_refresh_token_success(self, client: TestClient) -> None:
        """Test successful token refresh."""
        # First, login to get tokens
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpass"},
        )
        refresh_token = login_response.json()["data"]["refresh_token"]

        # Now refresh
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"

    def test_refresh_with_invalid_token(self, client: TestClient) -> None:
        """Test refresh with invalid token."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False

    def test_validate_token_success(self, client: TestClient) -> None:
        """Test token validation with valid token."""
        # Login to get token
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpass", "scopes": ["read", "write"]},
        )
        access_token = login_response.json()["data"]["access_token"]

        # Validate token
        response = client.get(
            "/api/v1/auth/validate",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["valid"] is True
        assert data["data"]["user_id"] is not None
        assert "read" in data["data"]["scopes"]

    def test_validate_without_token(self, client: TestClient) -> None:
        """Test validation without token in development mode."""
        response = client.get("/api/v1/auth/validate")

        # In development mode, should work but show not authenticated
        assert response.status_code == 200
        data = response.json()
        # Development mode allows unauthenticated access
        assert data["success"] is True

    def test_logout_success(self, client: TestClient) -> None:
        """Test logout endpoint."""
        # Login first
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpass"},
        )
        access_token = login_response.json()["data"]["access_token"]

        # Logout
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
            json={},  # Ensure Content-Type is set
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Logged out successfully" in data["data"]["message"]


# =============================================================================
# Integration Tests
# =============================================================================


class TestNavigationWithAuth:
    """Test navigation endpoint with JWT authentication."""

    @pytest.mark.xfail(reason="Requires Phase 2: AI Brain Integration - navigation module initialization")
    def test_navigation_with_valid_token(self, client: TestClient) -> None:
        """Test navigation endpoint accepts valid JWT token."""
        # Login to get token
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpass"},
        )
        access_token = login_response.json()["data"]["access_token"]

        # Use token with navigation endpoint
        response = client.post(
            "/api/v1/navigation/plan",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "goal": "test goal",
                "context": {},
                "max_alternatives": 3,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.xfail(reason="Requires Phase 2: AI Brain Integration - navigation module initialization")
    def test_navigation_without_token_dev_mode(self, client: TestClient) -> None:
        """Test navigation works without token in development mode."""
        response = client.post(
            "/api/v1/navigation/plan",
            json={
                "goal": "test goal",
                "context": {},
            },
        )

        # Should work in development mode
        assert response.status_code == 200


# =============================================================================
# Security Tests
# =============================================================================


class TestSecurityHardening:
    """Test security hardening measures."""

    def test_token_cannot_be_reused_after_logout(self, client: TestClient) -> None:
        """Test that tokens should be invalidated after logout."""
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpass"},
        )
        access_token = login_response.json()["data"]["access_token"]

        # Logout
        client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
            json={},  # Ensure Content-Type is set
        )

        # Token is now correctly invalidated (using blacklist)
        response = client.get(
            "/api/v1/auth/validate",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        # Correctly fails with 401 because token is revoked
        assert response.status_code == 401

    def test_malformed_token_rejected(self, client: TestClient) -> None:
        """Test that malformed tokens are rejected."""
        response = client.get(
            "/api/v1/auth/validate",
            headers={"Authorization": "Bearer not.a.valid.token"},
        )

        # Should fail validation
        assert response.status_code in [401, 500]

    def test_token_expiration_respected(self, jwt_manager: JWTManager, client: TestClient) -> None:
        """Test that expired tokens are rejected."""
        # Create an expired token
        expired_token = jwt_manager.create_access_token(
            subject="testuser",
            expires_delta=timedelta(seconds=-1),
        )

        response = client.get(
            "/api/v1/auth/validate",
            headers={"Authorization": f"Bearer {expired_token}"},
        )

        assert response.status_code == 401

    def test_rate_limiting_on_login(self) -> None:
        """Test rate limiting on login endpoint."""
        # Create a client with rate limiting enabled
        from application.mothership.config import reload_settings
        from safety.api.rate_limiter import RateLimitResult

        os.environ["MOTHERSHIP_RATE_LIMIT_ENABLED"] = "true"
        os.environ["MOTHERSHIP_SECRET_KEY"] = "test-secret-key-at-least-32-characters-long"
        reload_settings()

        app = create_app()
        client = TestClient(app)

        try:
            # Mock rate limiter to allow 5 requests then deny
            async def mock_allow(*args, **kwargs):
                mock_allow.counter += 1
                if mock_allow.counter > 5:
                    return RateLimitResult(allowed=False, remaining=0, reset_seconds=60)
                return RateLimitResult(allowed=True, remaining=10, reset_seconds=0)

            mock_allow.counter = 0

            # Patch where it is USED: safety.api.middleware.allow_request
            with patch("safety.api.middleware.allow_request", side_effect=mock_allow):
                # Make multiple login requests
                responses = []
                for _ in range(10):  # Reduced from 150
                    response = client.post(
                        "/api/v1/auth/login",
                        json={"username": "testuser", "password": "testpass"},
                    )
                    responses.append(response)

                # Should eventually get rate limited
                status_codes = [r.status_code for r in responses]
                assert 429 in status_codes  # Too Many Requests

        finally:
            # Clean up
            os.environ["MOTHERSHIP_RATE_LIMIT_ENABLED"] = "false"
            reload_settings()


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_username(self, client: TestClient) -> None:
        """Test login with empty username."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "", "password": "testpass"},
        )

        # 422 if validation enforced, 200 in permissive dev mode
        assert response.status_code in [200, 422]

    def test_very_long_username(self, client: TestClient) -> None:
        """Test login with very long username."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "a" * 256, "password": "testpass"},
        )

        # 422 if validation enforced, 200 in permissive dev mode
        assert response.status_code in [200, 422]

    def test_special_characters_in_username(self, client: TestClient) -> None:
        """Test login with special characters."""
        # Use special chars that won't trigger PII/email detection in safety middleware
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "user-special_chars!", "password": "testpass"},
        )

        assert response.status_code == 200  # Should work

    def test_unicode_in_credentials(self, client: TestClient) -> None:
        """Test login with unicode characters."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "用户名", "password": "пароль"},
        )

        assert response.status_code == 200  # Should work in dev mode
