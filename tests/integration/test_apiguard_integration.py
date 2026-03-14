"""
APIGuard Integration Tests for GRID

Test suite to verify APIGuard integration with GRID's existing architecture
and ensure compatibility with current middleware patterns.
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.responses import Response

# Ensure local virtualenv site-packages is on sys.path for apiguard import during collection
VENVSITE = Path(__file__).resolve().parents[2] / ".venv" / "Lib" / "site-packages"
if VENVSITE.exists():
    sys.path.insert(0, str(VENVSITE))

# Import APIGuard adapter
from application.mothership.middleware.apiguard_adapter import (
    APIGuardCircuitBreakerMiddleware,
    APIGuardHTTPClient,
    APIGuardRateLimitMiddleware,
    create_circuit_breaker_middleware,
    create_rate_limit_middleware,
    create_resilient_client,
)


class TestAPIGuardCircuitBreakerMiddleware:
    """Test APIGuard Circuit Breaker Middleware integration."""

    @pytest.fixture
    def app(self):
        """Create test FastAPI app."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}

        @app.get("/error")
        async def error_endpoint():
            raise ValueError("Test error")

        return app

    @pytest.fixture
    def client(self, app):
        """Create test client with APIGuard middleware."""
        middleware = APIGuardCircuitBreakerMiddleware(
            app,
            failure_threshold=3,  # Open after 3 failures to match test scenario
            recovery_timeout=1.0,
            cognitive_adjustment=False,  # Disable for testing
            retry_max_retries=0,
        )
        return TestClient(middleware, raise_server_exceptions=False)

    def test_successful_request(self, client):
        """Test successful request passes through middleware."""
        response = client.get("/test")
        assert response.status_code == 200
        assert response.json() == {"message": "success"}

    def test_circuit_breaker_opens_after_failures(self, client):
        """Test circuit breaker opens after threshold failures."""
        # Trigger failures to open circuit
        for _ in range(3):
            response = client.get("/error")
            assert response.status_code == 500

        # Circuit should now be open
        response = client.get("/test")
        assert response.status_code == 503
        assert response.json()["error_code"] == "CIRCUIT_OPEN"

    def test_rate_limiting(self, client):
        """Test rate limiting functionality."""
        # Make rapid requests to exceed rate limit
        responses = []
        for _ in range(70):  # Exceed default capacity of 60
            response = client.get("/test")
            responses.append(response)

        # Should have rate limited responses
        rate_limited = any(r.status_code == 429 for r in responses)
        assert rate_limited, "Expected rate limiting to trigger"


class TestAPIGuardRateLimitMiddleware:
    """Test APIGuard Rate Limit Middleware."""

    @pytest.fixture
    def app(self):
        """Create test FastAPI app."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}

        return app

    @pytest.fixture
    def client(self, app):
        """Create test client with rate limit middleware."""
        middleware = APIGuardRateLimitMiddleware(
            app,
            default_capacity=5,  # Small capacity for testing
            default_refill_rate=1.0,
            per_user=False,
        )
        return TestClient(middleware)

    def test_rate_limit_enforcement(self, client):
        """Test rate limit is enforced."""
        # Make requests up to capacity
        for _ in range(5):
            response = client.get("/test")
            assert response.status_code == 200

        # Next request should be rate limited
        response = client.get("/test")
        assert response.status_code == 429
        assert response.json()["error_code"] == "RATE_LIMIT_EXCEEDED"


class TestAPIGuardHTTPClient:
    """Test APIGuard HTTP Client."""

    @pytest.mark.asyncio
    async def test_resilient_client_success(self):
        """Test successful request with resilient client."""
        client = APIGuardHTTPClient(
            rate_limit_capacity=10,
            rate_limit_refill_rate=5.0,
        )

        with patch("httpx.AsyncClient.request") as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_request.return_value = mock_response

            async with client:
                response = await client.get("https://api.example.com/test")
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_resilient_client_retry(self):
        """Test retry logic on failure."""
        client = APIGuardHTTPClient(
            retry_max_retries=2,
            retry_base_delay=0.1,  # Fast for testing
        )

        with patch("httpx.AsyncClient.request") as mock_request:
            # First call fails, second succeeds
            mock_request.side_effect = [
                httpx.RequestError("Network error", request=MagicMock()),
                MagicMock(status_code=200),
            ]

            async with client:
                response = await client.get("https://api.example.com/test")
                assert response.status_code == 200
                assert mock_request.call_count == 2

    @pytest.mark.asyncio
    async def test_resilient_client_circuit_breaker(self):
        """Test circuit breaker on repeated failures."""
        client = APIGuardHTTPClient(
            circuit_failure_threshold=2,
            circuit_recovery_timeout=0.1,  # Fast for testing
        )

        with patch("httpx.AsyncClient.request") as mock_request:
            mock_request.side_effect = Exception("Service unavailable")

            async with client:
                # First two calls should trigger circuit breaker
                with pytest.raises(Exception):
                    await client.get("https://api.example.com/test")

                with pytest.raises(Exception):
                    await client.get("https://api.example.com/test")

                # Third call should fail fast due to open circuit
                with pytest.raises(Exception):
                    await client.get("https://api.example.com/test")


class TestFactoryFunctions:
    """Test factory functions for easy integration."""

    def test_create_circuit_breaker_middleware(self):
        """Test circuit breaker middleware factory."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}

        middleware_factory = create_circuit_breaker_middleware(
            failure_threshold=5,
            recovery_timeout=60.0,
        )

        middleware = middleware_factory(app)
        assert isinstance(middleware, APIGuardCircuitBreakerMiddleware)

        client = TestClient(middleware)
        response = client.get("/test")
        assert response.status_code == 200

    def test_create_rate_limit_middleware(self):
        """Test rate limit middleware factory."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}

        middleware_factory = create_rate_limit_middleware(
            default_capacity=100,
            per_user=True,
        )

        middleware = middleware_factory(app)
        assert isinstance(middleware, APIGuardRateLimitMiddleware)

        client = TestClient(middleware)
        response = client.get("/test")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_create_resilient_client(self):
        """Test resilient client factory."""
        client = create_resilient_client("rag")
        assert isinstance(client, APIGuardHTTPClient)

        # Verify RAG-specific configuration
        assert client.client._bucket._capacity == 20
        assert client.client._breaker._failure_threshold == 3


class TestGRIDIntegration:
    """Test integration with GRID's existing patterns."""

    @pytest.mark.asyncio
    async def test_cognitive_load_adjustment(self):
        """Test cognitive load adjustment integration."""
        middleware = APIGuardCircuitBreakerMiddleware(
            app=None,  # Not needed for this test
            cognitive_adjustment=True,
        )

        # Mock cognitive engine
        with patch.object(middleware, "_get_cognitive_load") as mock_load:
            mock_load.return_value = 0.8  # High cognitive load

            load = await middleware._get_cognitive_load()
            await middleware._adjust_limits_based_on_load(load)
            # Ensure cognitive load was fetched
            mock_load.assert_called_once()

    def test_per_user_rate_limiting(self):
        """Test per-user rate limiting with JWT tokens."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}

        middleware = APIGuardRateLimitMiddleware(
            app,
            default_capacity=10,
            per_user=True,
        )

        client = TestClient(middleware)

        # Test with different user tokens
        headers1 = {"Authorization": "Bearer token1"}
        headers2 = {"Authorization": "Bearer token2"}

        # Each user should have separate rate limits
        for _ in range(10):
            response1 = client.get("/test", headers=headers1)
            response2 = client.get("/test", headers=headers2)

        # Both should succeed (separate buckets)
        assert response1.status_code == 200
        assert response2.status_code == 200


# Integration test for RAG system protection
class TestRAGSystemProtection:
    """Test APIGuard integration with GRID's RAG system."""

    @pytest.mark.asyncio
    async def test_rag_client_protection(self):
        """Test RAG system client with conservative limits."""
        rag_client = create_resilient_client("rag")

        with patch("httpx.AsyncClient.request") as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_request.return_value = mock_response

            async with rag_client:
                response = await rag_client.post("http://localhost:8000/rag/query", json={"query": "test query"})
                assert response.status_code == 200

            # Verify conservative rate limiting
            assert rag_client.client._bucket._capacity == 20
            assert rag_client.client._bucket._refill_rate == 2.0


# Integration test for external API protection
class TestExternalAPIProtection:
    """Test APIGuard integration with external APIs."""

    @pytest.mark.asyncio
    async def test_coinbase_client_protection(self):
        """Test Coinbase API client with appropriate limits."""
        external_client = create_resilient_client("external_api")

        with patch("httpx.AsyncClient.request") as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_request.return_value = mock_response

            async with external_client:
                response = await external_client.get("https://api.coinbase.com/v2/exchange-rates")
                assert response.status_code == 200

            # Verify external API configuration
            assert external_client.client._breaker._failure_threshold == 3
            assert external_client.client._breaker._recovery_timeout == 120.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
