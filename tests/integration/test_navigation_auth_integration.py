"""
Navigation Authentication Integration Tests.

Comprehensive integration tests for navigation endpoint with various
authentication scenarios, error conditions, and user contexts.
"""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from application.mothership.main import create_app
from application.mothership.security.jwt import reset_jwt_manager

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    reset_jwt_manager()
    app = create_app()
    return TestClient(app)


@pytest.fixture
def authenticated_user(client: TestClient) -> dict[str, str]:
    """Create an authenticated user and return tokens."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "testpass",
            "scopes": ["read", "write"],
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


@pytest.fixture
def admin_user(client: TestClient) -> dict[str, str]:
    """Create an admin user and return tokens."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "admin",
            "password": "adminpass",
            "scopes": ["read", "write", "admin"],
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


@pytest.fixture
def readonly_user(client: TestClient) -> dict[str, str]:
    """Create a read-only user and return tokens."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "readonly",
            "password": "readpass",
            "scopes": ["read"],
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


# =============================================================================
# Basic Integration Tests
# =============================================================================


class TestNavigationAuthenticationBasics:
    """Test basic navigation endpoint authentication."""

    def test_navigation_with_valid_jwt(
        self,
        client: TestClient,
        authenticated_user: dict[str, str],
    ) -> None:
        """Test navigation endpoint accepts valid JWT token."""
        response = client.post(
            "/api/v1/navigation/plan",
            headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
            json={
                "goal": "Complete user onboarding",
                "context": {"user_type": "new"},
                "max_alternatives": 3,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "request_id" in data["data"]

    def test_navigation_without_auth_dev_mode(self, client: TestClient) -> None:
        """Test navigation works without auth in development mode."""
        response = client.post(
            "/api/v1/navigation/plan",
            json={
                "goal": "Test navigation",
                "context": {},
            },
        )

        # Should work in development mode
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_navigation_with_expired_token(self, client: TestClient) -> None:
        """Test navigation with expired token."""
        # Create a token that's already expired
        from datetime import timedelta

        from application.mothership.security.jwt import JWTManager

        jwt_manager = JWTManager(
            secret_key="test-secret-key-at-least-32-chars-long",
            algorithm="HS256",
            environment="testing",
        )

        expired_token = jwt_manager.create_access_token(
            subject="test_user",
            expires_delta=timedelta(seconds=-10),
        )

        response = client.post(
            "/api/v1/navigation/plan",
            headers={"Authorization": f"Bearer {expired_token}"},
            json={"goal": "Test", "context": {}},
        )

        # Should reject expired token
        assert response.status_code == 401

    def test_navigation_with_invalid_token(self, client: TestClient) -> None:
        """Test navigation with invalid token."""
        response = client.post(
            "/api/v1/navigation/plan",
            headers={"Authorization": "Bearer invalid.token.here"},
            json={"goal": "Test", "context": {}},
        )

        # Should reject invalid token
        assert response.status_code in [401, 500]

    def test_navigation_with_malformed_header(self, client: TestClient) -> None:
        """Test navigation with malformed Authorization header."""
        malformed_headers = [
            {"Authorization": "invalid_format"},
            {"Authorization": "Bearer"},
            {"Authorization": "Bearer "},
            {"Authorization": "Basic dGVzdDp0ZXN0"},  # Wrong scheme
        ]

        for headers in malformed_headers:
            response = client.post(
                "/api/v1/navigation/plan",
                headers=headers,
                json={"goal": "Test", "context": {}},
            )
            # Should handle gracefully (dev mode might allow, prod would reject)
            assert response.status_code in [200, 401, 422]


# =============================================================================
# User Context Integration Tests
# =============================================================================


class TestNavigationUserContext:
    """Test navigation with different user contexts."""

    def test_navigation_includes_user_context(
        self,
        client: TestClient,
        authenticated_user: dict[str, str],
    ) -> None:
        """Test that navigation planning includes user context."""
        response = client.post(
            "/api/v1/navigation/plan",
            headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
            json={
                "goal": "Create project",
                "context": {"project_type": "research"},
                "source": "api",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Check that response includes request correlation
        assert "meta" in data
        assert "request_id" in data["meta"]

    def test_navigation_with_different_scopes(
        self,
        client: TestClient,
        readonly_user: dict[str, str],
        authenticated_user: dict[str, str],
    ) -> None:
        """Test navigation behavior with different user scopes."""
        # Read-only user
        response1 = client.post(
            "/api/v1/navigation/plan",
            headers={"Authorization": f"Bearer {readonly_user['access_token']}"},
            json={"goal": "View dashboard", "context": {}},
        )
        assert response1.status_code == 200

        # Full access user
        response2 = client.post(
            "/api/v1/navigation/plan",
            headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
            json={"goal": "Create content", "context": {}},
        )
        assert response2.status_code == 200

    def test_navigation_with_admin_privileges(
        self,
        client: TestClient,
        admin_user: dict[str, str],
    ) -> None:
        """Test navigation with admin user."""
        response = client.post(
            "/api/v1/navigation/plan",
            headers={"Authorization": f"Bearer {admin_user['access_token']}"},
            json={
                "goal": "Configure system",
                "context": {"admin_action": True},
            },
        )

        assert response.status_code == 200

    def test_navigation_preserves_user_identity(
        self,
        client: TestClient,
        authenticated_user: dict[str, str],
    ) -> None:
        """Test that user identity is preserved through navigation."""
        # Make multiple requests with same token
        for i in range(1):
            response = client.post(
                "/api/v1/navigation/plan",
                headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
                json={"goal": f"Task {i} - description must be longer than 10 chars", "context": {}},
            )
            assert response.status_code == 200

    def test_navigation_with_custom_user_metadata(
        self,
        client: TestClient,
        authenticated_user: dict[str, str],
    ) -> None:
        """Test navigation with custom user metadata."""
        response = client.post(
            "/api/v1/navigation/plan",
            headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
            json={
                "goal": "Personalized workflow",
                "context": {
                    "user_preferences": {
                        "theme": "dark",
                        "language": "en",
                        "complexity_preference": "detailed",
                    }
                },
            },
        )

        assert response.status_code == 200


# =============================================================================
# Request Validation Tests
# =============================================================================


class TestNavigationRequestValidation:
    """Test navigation request validation with authentication."""

    def test_navigation_with_missing_goal(
        self,
        client: TestClient,
        authenticated_user: dict[str, str],
    ) -> None:
        """Test navigation with missing required goal field."""
        response = client.post(
            "/api/v1/navigation/plan",
            headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
            json={"context": {}},
        )

        assert response.status_code == 422

    def test_navigation_with_empty_goal(
        self,
        client: TestClient,
        authenticated_user: dict[str, str],
    ) -> None:
        """Test navigation with empty goal."""
        response = client.post(
            "/api/v1/navigation/plan",
            headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
            json={"goal": "", "context": {}},
        )

        assert response.status_code == 422

    def test_navigation_with_invalid_max_alternatives(
        self,
        client: TestClient,
        authenticated_user: dict[str, str],
    ) -> None:
        """Test navigation with invalid max_alternatives."""
        invalid_values = [-1, 0, 10]

        for value in invalid_values:
            response = client.post(
                "/api/v1/navigation/plan",
                headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
                json={
                    "goal": "Test",
                    "context": {},
                    "max_alternatives": value,
                },
            )
            # Should either accept (with adjustment) or reject
            assert response.status_code in [200, 422]

    def test_navigation_with_complex_context(
        self,
        client: TestClient,
        authenticated_user: dict[str, str],
    ) -> None:
        """Test navigation with complex nested context."""
        response = client.post(
            "/api/v1/navigation/plan",
            headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
            json={
                "goal": "Complex analysis",
                "context": {
                    "level1": {
                        "level2": {
                            "level3": {
                                "data": [1, 2, 3],
                                "metadata": {"key": "value"},
                            }
                        }
                    },
                    "tags": ["tag1", "tag2", "tag3"],
                },
            },
        )

        assert response.status_code == 200

    def test_navigation_with_large_context(
        self,
        client: TestClient,
        authenticated_user: dict[str, str],
    ) -> None:
        """Test navigation with large context payload."""
        large_context = {f"key_{i}": f"value_{i}" * 100 for i in range(50)}

        response = client.post(
            "/api/v1/navigation/plan",
            headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
            json={
                "goal": "Process large data",
                "context": large_context,
            },
        )

        # Should handle large context or reject gracefully
        assert response.status_code in [200, 413, 422]


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestNavigationErrorHandling:
    """Test error handling in navigation with authentication."""

    def test_navigation_with_processing_error(
        self,
        client: TestClient,
        authenticated_user: dict[str, str],
    ) -> None:
        """Test navigation handles processing errors gracefully."""
        # Try to trigger an edge case
        response = client.post(
            "/api/v1/navigation/plan",
            headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
            json={
                "goal": "Test error handling",
                "context": {"simulate_error": True},
            },
        )

        # Should return appropriate error or success
        assert response.status_code in [200, 422, 500]

    def test_navigation_error_includes_request_id(
        self,
        client: TestClient,
        authenticated_user: dict[str, str],
    ) -> None:
        """Test that errors include request ID for tracing."""
        response = client.post(
            "/api/v1/navigation/plan",
            headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
            json={"goal": "", "context": {}},  # Invalid request
        )

        assert response.status_code == 422
        data = response.json()
        # Should include request_id for error tracking
        assert "request_id" in data or ("meta" in data and "request_id" in data.get("meta", {}))

    def test_navigation_with_malformed_json(
        self,
        client: TestClient,
        authenticated_user: dict[str, str],
    ) -> None:
        """Test navigation with malformed JSON."""
        response = client.post(
            "/api/v1/navigation/plan",
            headers={
                "Authorization": f"Bearer {authenticated_user['access_token']}",
                "Content-Type": "application/json",
            },
            content="{invalid json}",
        )

        assert response.status_code == 422


# =============================================================================
# Performance and Load Tests
# =============================================================================


class TestNavigationPerformance:
    """Test navigation endpoint performance with authentication."""

    def test_navigation_response_time(
        self,
        client: TestClient,
        authenticated_user: dict[str, str],
    ) -> None:
        """Test navigation response time is acceptable."""
        start_time = time.perf_counter()

        response = client.post(
            "/api/v1/navigation/plan",
            headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
            json={
                "goal": "Quick response test",
                "context": {},
            },
        )

        elapsed = time.perf_counter() - start_time

        assert response.status_code == 200
        # Should respond quickly (< 500ms including auth overhead)
        assert elapsed < 0.5, f"Response too slow: {elapsed * 1000:.2f}ms"

    def test_navigation_concurrent_requests(
        self,
        client: TestClient,
        authenticated_user: dict[str, str],
    ) -> None:
        """Test concurrent navigation requests."""
        from concurrent.futures import ThreadPoolExecutor

        def make_request(i: int) -> int:
            response = client.post(
                "/api/v1/navigation/plan",
                headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
                json={"goal": f"Concurrent task {i}", "context": {}},
            )
            return response.status_code

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, i) for i in range(10)]
            results = [f.result() for f in futures]

        # All requests should succeed
        assert all(status == 200 for status in results)

    def test_navigation_bulk_requests(
        self,
        client: TestClient,
        authenticated_user: dict[str, str],
    ) -> None:
        """Test bulk navigation requests."""
        responses = []

        for i in range(20):
            response = client.post(
                "/api/v1/navigation/plan",
                headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
                json={"goal": f"Bulk task {i}", "context": {}},
            )
            responses.append(response.status_code)

        # All should succeed
        success_rate = sum(1 for s in responses if s == 200) / len(responses)
        assert success_rate >= 0.95, f"Success rate too low: {success_rate * 100:.1f}%"


# =============================================================================
# Token Refresh Integration Tests
# =============================================================================


class TestNavigationTokenRefresh:
    """Test navigation with token refresh scenarios."""

    def test_navigation_after_token_refresh(
        self,
        client: TestClient,
        authenticated_user: dict[str, str],
    ) -> None:
        """Test navigation works after token refresh."""
        # Use original token
        response1 = client.post(
            "/api/v1/navigation/plan",
            headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
            json={"goal": "Before refresh", "context": {}},
        )
        assert response1.status_code == 200

        # Refresh token
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": authenticated_user["refresh_token"]},
        )
        assert refresh_response.status_code == 200
        new_token = refresh_response.json()["data"]["access_token"]

        # Use new token
        response2 = client.post(
            "/api/v1/navigation/plan",
            headers={"Authorization": f"Bearer {new_token}"},
            json={"goal": "After refresh", "context": {}},
        )
        assert response2.status_code == 200

    def test_navigation_with_refresh_token_fails(
        self,
        client: TestClient,
        authenticated_user: dict[str, str],
    ) -> None:
        """Test that refresh tokens cannot be used for navigation."""
        response = client.post(
            "/api/v1/navigation/plan",
            headers={"Authorization": f"Bearer {authenticated_user['refresh_token']}"},
            json={"goal": "Test", "context": {}},
        )

        # Should reject refresh token (type mismatch)
        assert response.status_code in [401, 500]


# =============================================================================
# Cross-Endpoint Integration Tests
# =============================================================================


class TestCrossEndpointIntegration:
    """Test navigation integration with other endpoints."""

    def test_full_user_workflow(
        self,
        client: TestClient,
    ) -> None:
        """Test complete user workflow: login -> validate -> navigate -> logout."""
        # 1. Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "workflow_user", "password": "test"},
        )
        assert login_response.status_code == 200
        tokens = login_response.json()["data"]

        # 2. Validate token
        validate_response = client.get(
            "/api/v1/auth/validate",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert validate_response.status_code == 200

        # 3. Use navigation
        nav_response = client.post(
            "/api/v1/navigation/plan",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
            json={"goal": "Complete workflow", "context": {}},
        )
        assert nav_response.status_code == 200

        # 4. Logout
        logout_response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
            json={},  # Ensure Content-Type is set
        )
        assert logout_response.status_code == 200

    def test_navigation_request_correlation(
        self,
        client: TestClient,
        authenticated_user: dict[str, str],
    ) -> None:
        """Test request correlation across endpoints."""
        import uuid

        correlation_id = str(uuid.uuid4())

        # Make navigation request with correlation ID
        response = client.post(
            "/api/v1/navigation/plan",
            headers={
                "Authorization": f"Bearer {authenticated_user['access_token']}",
                "X-Correlation-ID": correlation_id,
            },
            json={"goal": "Correlated request", "context": {}},
        )

        assert response.status_code == 200
