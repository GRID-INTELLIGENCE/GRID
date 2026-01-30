"""
Test fixtures for Activity Resonance API tests.

Provides TestClient, WebSocket client, and service mocks for testing.
"""

from __future__ import annotations

import asyncio

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.resonance.api.dependencies import reset_resonance_service
from application.resonance.api.router import router
from application.resonance.api.service import ResonanceService


@pytest.fixture
def app() -> FastAPI:
    """
    Create FastAPI application for testing.

    Returns:
        FastAPI application instance
    """
    app = FastAPI()
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
    reset_resonance_service()
    from application.resonance.api.dependencies import get_resonance_service

    return get_resonance_service()


@pytest.fixture(autouse=True)
def cleanup_service():
    """
    Cleanup service after each test.

    This ensures tests don't interfere with each other.
    """
    yield
    reset_resonance_service()


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
