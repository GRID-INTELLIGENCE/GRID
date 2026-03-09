"""
Test fixtures for Activity Resonance API tests.

Provides TestClient, WebSocket client, and service mocks for testing.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from application.resonance.services.resonance_service import ResonanceService


async def _mock_verify_authentication() -> dict[str, Any]:
    """Mock auth dependency that allows all requests for testing."""
    return {
        "authenticated": True,
        "method": "test_bypass",
        "user_id": "test_user",
        "permissions": {"read", "write"},
    }


async def _mock_check_rate_limit() -> bool:
    """Mock rate limit dependency that allows all requests for testing."""
    return True


@pytest.fixture
def app() -> FastAPI:
    """
    Create FastAPI application for testing.

    Returns:
        FastAPI application instance
    """
    from application.mothership.dependencies import check_rate_limit, verify_authentication
    from application.resonance.api.router import router

    app = FastAPI()
    # Override the underlying dependency functions for unauthenticated testing
    # Auth = Annotated[dict[str, Any], Depends(verify_authentication)]
    # RateLimited = Annotated[bool, Depends(check_rate_limit)]
    app.dependency_overrides[verify_authentication] = _mock_verify_authentication
    app.dependency_overrides[check_rate_limit] = _mock_check_rate_limit
    app.include_router(router, prefix="/api/v1/resonance", tags=["resonance"])
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """
    Create TestClient for API testing.

    Args:
        app: FastAPI application

    Returns:
        TestClient instance
    """
    return TestClient(app)


@pytest.fixture
def service() -> ResonanceService:
    """
    Create ResonanceService instance for testing.

    Returns:
        ResonanceService instance
    """
    from application.resonance.api.dependencies import get_resonance_service, reset_resonance_service

    reset_resonance_service()
    return get_resonance_service()


@pytest.fixture(autouse=True)
def cleanup_service():
    """
    Cleanup service after each test.

    This ensures tests don't interfere with each other.
    """
    yield
    try:
        from application.resonance.api.dependencies import reset_resonance_service

        reset_resonance_service()
    except ImportError:
        pass


@pytest.fixture
def sample_activity_id(service: ResonanceService) -> str:
    """
    Create a sample activity for testing.

    Simplified fixture that works with sync tests.
    Uses asyncio.run() which is safe when no event loop is running
    (pytest-asyncio auto mode ensures this).

    Args:
        service: ResonanceService instance

    Returns:
        Activity ID
    """
    # Use asyncio.run() - simpler and safer than nested event loops
    # pytest-asyncio auto mode ensures no event loop is running here
    activity_id, _ = asyncio.run(
        service.process_activity(
            query="test activity",
            activity_type="general",
            context={},
        )
    )
    return activity_id


@pytest.fixture
def websocket_client(app: FastAPI):
    """
    Create WebSocket test client.

    Args:
        app: FastAPI application

    Returns:
        WebSocket test client function
    """
    from fastapi.testclient import TestClient

    client = TestClient(app)

    def connect_websocket(path: str):
        """Connect to WebSocket endpoint."""
        return client.websocket_connect(path)

    return connect_websocket
