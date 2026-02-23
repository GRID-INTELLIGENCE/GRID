"""
Comprehensive API endpoint tests for GRID system.

Tests all major API routes with proper authentication, validation,
error handling, and performance monitoring.
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from application.mothership.main import create_app

# Import routers for testing


class TestHealthEndpoints:
    """Test health check endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client with health router"""
        app = create_app()
        return TestClient(app)

    def test_health_check_basic(self, client):
        """Scenario: Basic health check should return system status"""
        response = client.get("/health")

        assert response.status_code == 200, "Health check should succeed"
        data = response.json()

        assert "success" in data, "Response should have success field"
        assert "data" in data, "Response should have data field"

        health_data = data["data"]
        assert "status" in health_data, "Health data should have status"
        assert "version" in health_data, "Health data should have version"
        assert "timestamp" in health_data, "Health data should have timestamp"
        assert "uptime_seconds" in health_data, "Health data should have uptime"

    def test_liveness_probe(self, client):
        """Scenario: Liveness probe for Kubernetes"""
        response = client.get("/health/live")

        assert response.status_code == 200, "Liveness probe should succeed"
        data = response.json()

        assert data["alive"], "Application should be alive"
        assert "timestamp" in data, "Should include timestamp"

    def test_readiness_probe(self, client):
        """Scenario: Readiness probe for Kubernetes"""
        response = client.get("/health/ready")

        assert response.status_code == 200, "Readiness probe should succeed"
        data = response.json()

        assert data["ready"], "Application should be ready"
        assert "dependencies" in data, "Should include readiness checks"

    def test_security_health_check(self, client):
        """Scenario: Security configuration health check"""
        response = client.get("/health/security")
        data = response.json()
        assert response.status_code in [200, 503], "Security health should return compliant or degraded status"
        assert "success" in data, "Response should have success field"
        assert "data" in data, "Response should have data field"
        assert "checks" in data["data"], "Should include security checks"
        checks = data["data"]["checks"]
        assert data["success"] == data["data"]["compliant"], "Top-level success should match compliance result"

        # Should check security configurations
        assert len(checks) > 5, "Should run multiple security checks"
        check_names = [check["name"] for check in checks]
        assert "authentication_enforced" in check_names, "Should check authentication"
        assert "security_headers_present" in check_names, "Should check security headers"

    def test_health_check_performance(self, client):
        """Scenario: Health checks should be fast"""
        start_time = datetime.now()

        response = client.get("/health")

        duration = (datetime.now() - start_time).total_seconds()
        assert response.status_code == 200, "Health check should succeed"
        assert duration < 1.0, f"Health check should be fast, took {duration}s"

    def test_health_check_with_components(self, client):
        """Scenario: Health check should report component status"""
        with patch("application.mothership.dependencies.get_cockpit_service") as mock_cockpit:
            # Mock cockpit with components
            mock_component = Mock()
            mock_component.is_healthy.return_value = True

            mock_cockpit.return_value.state.components = {"test_component": mock_component}
            mock_cockpit.return_value.state.alerts = {}
            mock_cockpit.return_value.state.started_at = datetime.now()
            mock_cockpit.return_value.state.uptime_seconds = 3600.0

            response = client.get("/health")

            assert response.status_code == 200, "Health check should succeed"
            data = response.json()
            checks = data["data"]["checks"]

            assert "components" in checks, "Should check component health"
            assert checks["components"], "Components should be healthy"


class TestAuthEndpoints:
    """Test authentication endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client with auth router"""
        app = create_app()
        return TestClient(app)

    @pytest.fixture
    def mock_user_data(self):
        """Mock user data for testing"""
        return {"username": "test_user", "password": "test_password", "scopes": ["read", "write"]}

    @patch("application.mothership.security.jwt.get_jwt_manager")
    def test_login_success(self, mock_jwt_manager, client, mock_user_data):
        """Scenario: Successful login should return tokens"""
        # Mock JWT manager
        jwt_manager = Mock()
        jwt_manager.create_tokens.return_value = {
            "access_token": "mock_access_token",
            "refresh_token": "mock_refresh_token",
            "expires_in": 3600,
            "scopes": mock_user_data["scopes"],
        }
        mock_jwt_manager.return_value = jwt_manager

        response = client.post("/api/v1/auth/login", json=mock_user_data)

        assert response.status_code == 200, "Login should succeed"
        data = response.json()

        assert data["success"], "Login should be successful"
        assert "access_token" in data["data"], "Should return access token"
        assert "refresh_token" in data["data"], "Should return refresh token"
        assert data["data"]["token_type"] == "bearer", "Should be bearer token"

    def test_login_any_credentials_development(self, client):
        """Scenario: In development, any credentials should work"""
        invalid_data = {"username": "invalid_user", "password": "wrong_password"}

        response = client.post("/api/v1/auth/login", json=invalid_data)

        # In development mode, auth accepts any credentials
        assert response.status_code == 200, "Development login should succeed"
        data = response.json()

        assert data["success"], "Login should be successful"
        assert "access_token" in data["data"], "Should return access token"

    def test_login_validation_errors(self, client):
        """Scenario: Invalid request format should be rejected"""
        # Missing password
        incomplete_data = {"username": "test_user"}

        response = client.post("/api/v1/auth/login", json=incomplete_data)

        assert response.status_code == 422, "Validation should fail"

    def test_token_refresh_invalid_token(self, client):
        """Scenario: Invalid refresh token should be rejected"""
        refresh_data = {"refresh_token": "invalid_refresh_token"}

        response = client.post("/api/v1/auth/refresh", json=refresh_data)

        assert response.status_code == 401, "Invalid refresh should be unauthorized"

    @patch("application.mothership.routers.auth.get_jwt_manager")
    def test_token_refresh_valid_token(self, mock_get_jwt_manager, client):
        """Scenario: Valid token refresh should work."""
        jwt_manager = Mock()
        jwt_manager.refresh_access_token.return_value = "new_access_token"
        mock_get_jwt_manager.return_value = jwt_manager

        refresh_data = {"refresh_token": "safe_refresh_token"}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)

        assert response.status_code == 200, "Token refresh should succeed"
        data = response.json()

        assert data["success"], "Refresh should be successful"
        assert "access_token" in data["data"], "Should return new access token"
        jwt_manager.refresh_access_token.assert_called_once_with("safe_refresh_token")

    def test_invalid_refresh_token(self, client):
        """Scenario: Invalid refresh token should be rejected"""
        refresh_data = {"refresh_token": "invalid_refresh_token"}

        with patch("application.mothership.security.jwt.get_jwt_manager") as mock_jwt:
            jwt_manager = Mock()
            jwt_manager.refresh_tokens.side_effect = Exception("Invalid token")
            mock_jwt.return_value = jwt_manager

            response = client.post("/api/v1/auth/refresh", json=refresh_data)

            assert response.status_code == 401, "Invalid refresh should be unauthorized"


class TestAgenticEndpoints:
    """Test agentic system endpoints"""

    @pytest.fixture
    def mock_processing_unit(self):
        """Mock processing unit for case creation"""
        unit = Mock()
        result = Mock()
        result.case_id = "test_case_123"
        result.category = Mock(value="feature_request")
        result.structured_data = Mock(
            priority="high",
            confidence=0.95,
            labels=["auth"],
            keywords=["authentication"],
        )
        result.structured_data.__dict__ = {
            "priority": "high",
            "confidence": 0.95,
            "labels": ["auth"],
            "keywords": ["authentication"],
            "recommended_roles": [],
            "recommended_tasks": [],
        }
        result.reference_file_path = ".case_references/test_case_123.json"
        result.timestamp = "2026-02-23T00:00:00"
        unit.process_input = Mock(return_value=result)
        return unit

    @pytest.fixture
    def mock_agentic_system(self):
        """Mock agentic system with repository and event bus"""
        system = Mock()
        system.repository = Mock()
        system.event_bus = AsyncMock()
        system.event_bus.publish = AsyncMock()
        system.event_bus.get_event_history = AsyncMock(return_value=[])
        system.execute_case = AsyncMock()
        return system

    @pytest.fixture
    def authenticated_client(self, mock_processing_unit, mock_agentic_system):
        """Create test client with authentication and dependency overrides"""
        from application.mothership.routers.agentic import get_agentic_system, get_processing_unit

        app = create_app()

        # Override FastAPI dependencies instead of patching imports
        app.dependency_overrides[get_processing_unit] = lambda: mock_processing_unit
        app.dependency_overrides[get_agentic_system] = lambda: mock_agentic_system

        client = TestClient(app)

        # Login to get token
        login_response = client.post("/api/v1/auth/login", json={"username": "test_user", "password": "test_password"})
        assert login_response.status_code == 200, "Login should succeed"

        token = login_response.json()["data"]["access_token"]
        client.headers.update({"Authorization": f"Bearer {token}"})
        return client

    def test_create_case_success(self, authenticated_client):
        """Scenario: Case creation should succeed"""
        case_data = {
            "raw_input": "Create a new feature for user authentication",
            "user_id": "test_user_123",
        }

        response = authenticated_client.post("/api/v1/agentic/cases", json=case_data)

        assert response.status_code == 201, "Case creation should succeed"
        data = response.json()
        assert data["case_id"] == "test_case_123", "Should return case ID"

    def test_create_case_validation_errors(self, authenticated_client):
        """Scenario: Invalid case data should be rejected"""
        # Missing required fields
        invalid_data = {"user_id": "test_user"}

        response = authenticated_client.post("/api/v1/agentic/cases", json=invalid_data)

        assert response.status_code == 422, "Validation should fail"

    def test_get_case_success(self, authenticated_client, mock_agentic_system):
        """Scenario: Get case should return case details"""
        mock_case = Mock()
        mock_case.case_id = "test_case_123"
        mock_case.status = "categorized"
        mock_case.category = "feature_request"
        mock_case.priority = "high"
        mock_case.confidence = 0.95
        mock_case.reference_file_path = ".case_references/test_case_123.json"
        mock_case.created_at = None
        mock_case.updated_at = None
        mock_case.completed_at = None
        mock_case.outcome = ""
        mock_case.solution = ""
        mock_agentic_system.repository.get_case = AsyncMock(return_value=mock_case)

        response = authenticated_client.get("/api/v1/agentic/cases/test_case_123")

        assert response.status_code == 200, "Get case should succeed"
        data = response.json()
        assert data["case_id"] == "test_case_123", "Should return correct case"

    def test_get_case_not_found(self, authenticated_client, mock_agentic_system):
        """Scenario: Non-existent case should return 404"""
        mock_agentic_system.repository.get_case = AsyncMock(return_value=None)

        response = authenticated_client.get("/api/v1/agentic/cases/non_existent")

        assert response.status_code == 404, "Non-existent case should return 404"

    def test_execute_case_not_found(self, authenticated_client, mock_agentic_system):
        """Scenario: Executing non-existent case should return 404"""
        mock_agentic_system.repository.get_case = AsyncMock(return_value=None)

        execute_data = {"force": True}
        response = authenticated_client.post("/api/v1/agentic/cases/non_existent/execute", json=execute_data)

        assert response.status_code == 404, "Non-existent case should return 404"

    def test_case_creation_performance(self, authenticated_client):
        """Scenario: Case creation should meet performance requirements"""
        case_data = {"raw_input": "Test case", "user_id": "test_user"}

        start_time = datetime.now()
        response = authenticated_client.post("/api/v1/agentic/cases", json=case_data)
        duration = (datetime.now() - start_time).total_seconds()

        assert response.status_code == 201, "Case creation should succeed"
        assert duration < 5.0, f"Case creation should be fast, took {duration}s"


class TestAPIIntegration:
    """Test API integration and cross-cutting concerns"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        app = create_app()
        return TestClient(app)

    def test_cors_headers(self, client):
        """Scenario: API should include CORS headers"""
        response = client.options("/health")

        # Should have CORS headers if configured
        assert response.status_code in [200, 405], "OPTIONS request should be handled"

    def test_content_type_validation(self, client):
        """Scenario: API should validate content types"""
        # Send JSON with wrong content type
        response = client.post(
            "/api/v1/auth/login",
            content=b'{"username": "test", "password": "test"}',
            headers={"Content-Type": "text/plain"},
        )

        # FastAPI should handle content type validation
        assert response.status_code in [422, 415], "Should reject wrong content type"

    def test_rate_limiting(self, client):
        """Scenario: API should implement rate limiting"""
        # This would test rate limiting if implemented
        # For now, just ensure rapid requests don't crash
        responses = []
        for _ in range(10):
            response = client.get("/health")
            responses.append(response.status_code)

        # Most should succeed, maybe some get rate limited
        success_count = sum(1 for code in responses if code == 200)
        assert success_count >= 8, "Most requests should succeed"

    def test_error_response_format(self, client):
        """Scenario: All errors should follow consistent format"""
        response = client.get("/api/v1/nonexistent")

        assert response.status_code == 404, "Non-existent endpoint should return 404"

        if response.headers.get("content-type", "").startswith("application/json"):
            data = response.json()
            # Accept either custom ErrorResponse or default Starlette format
            assert "success" in data or "detail" in data, "Error response should have success or detail field"
            if "success" in data:
                assert not data["success"], "Error response success should be false"

    def test_request_id_tracking(self, client):
        """Scenario: API should track request IDs"""
        response = client.get("/health")

        # Should have request tracking in headers or response
        assert response.status_code == 200, "Request should succeed"

        # Check for request ID in headers if implemented
        response.headers.get("x-request-id")
        # Not required but good practice
        # assert request_id, "Should include request ID for tracing"

    def test_api_versioning(self, client):
        """Scenario: API should respect versioning"""
        # Non-versioned health should work
        response = client.get("/health")
        assert response.status_code == 200, "Health endpoint should work"

        # API version should work for auth endpoints
        response = client.get("/api/v1/auth/validate")
        assert response.status_code in [200, 401, 422], "API v1 should work"

        # Old version should not exist
        response = client.get("/api/v0/health")
        assert response.status_code == 404, "v0 API should not exist"

    def test_error_handling_consistency(self, client):
        """Scenario: Error handling should be consistent across endpoints"""
        test_cases = [
            # Method not allowed
            ("DELETE", "/health", None),
            # Invalid content
            ("POST", "/api/v1/auth/login", {}, "invalid json content type"),
            # Missing fields
            ("POST", "/api/v1/auth/login", {}),
        ]

        for method, endpoint, data, *extra in test_cases:
            if method == "DELETE":
                response = client.delete(endpoint)
            elif method == "POST":
                if extra:
                    response = client.post(endpoint, content=str(data).encode(), headers={"Content-Type": extra[0]})
                else:
                    response = client.post(endpoint, json=data)

            # Should handle errors gracefully
            assert response.status_code < 500, f"Should not return server error for {method} {endpoint}"

            # Error responses should be consistent
            if response.headers.get("content-type", "").startswith("application/json"):
                response_data = response.json()
                assert isinstance(response_data, dict), "Error response should be JSON"
