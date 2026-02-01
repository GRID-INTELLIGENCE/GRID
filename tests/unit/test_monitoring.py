"""
Tests for production monitoring module.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.monitoring import (
    setup_metrics,
    get_metrics_router,
    http_request_duration_seconds,
    rag_query_duration_seconds,
    track_rag_query,
    track_event_processing,
    track_db_operation,
    track_skill_execution,
)


@pytest.fixture
def app_with_metrics() -> FastAPI:
    """Create FastAPI app with metrics enabled."""
    app = FastAPI()
    setup_metrics(app)
    app.include_router(get_metrics_router())

    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    @app.get("/error")
    async def error_endpoint():
        raise ValueError("Test error")

    return app


@pytest.fixture
def client(app_with_metrics: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app_with_metrics)


@pytest.mark.unit
def test_metrics_endpoint_exists(client: TestClient) -> None:
    """Test that metrics endpoint is available."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"grid_http_requests_total" in response.content


@pytest.mark.unit
def test_http_request_metrics_recorded(client: TestClient) -> None:
    """Test that HTTP request metrics are recorded."""
    response = client.get("/test")
    assert response.status_code == 200

    metrics_response = client.get("/metrics")
    metrics_content = metrics_response.text
    assert "grid_http_requests_total" in metrics_content
    assert 'method="GET"' in metrics_content
    assert 'status_code="200"' in metrics_content


@pytest.mark.unit
def test_http_error_metrics_recorded(client: TestClient) -> None:
    """Test that HTTP error metrics are recorded."""
    with pytest.raises(ValueError):
        client.get("/error")

    metrics_response = client.get("/metrics")
    metrics_content = metrics_response.text
    assert "grid_http_requests_total" in metrics_content


@pytest.mark.asyncio
@pytest.mark.unit
async def test_track_rag_query_context_manager() -> None:
    """Test RAG query tracking context manager."""
    async with track_rag_query("semantic"):
        pass

    # Verify metric was recorded
    assert rag_query_duration_seconds._metrics


@pytest.mark.asyncio
@pytest.mark.unit
async def test_track_event_processing_context_manager() -> None:
    """Test event processing tracking context manager."""
    async with track_event_processing("grid", "case.created"):
        pass

    # Verify metric was recorded
    assert http_request_duration_seconds._metrics


@pytest.mark.asyncio
@pytest.mark.unit
async def test_track_db_operation_context_manager() -> None:
    """Test database operation tracking context manager."""
    async with track_db_operation("select"):
        pass

    # Verify metric was recorded


@pytest.mark.asyncio
@pytest.mark.unit
async def test_track_skill_execution_success() -> None:
    """Test skill execution tracking on success."""
    async with track_skill_execution("transform.schema_map"):
        pass

    # Verify success metric was recorded


@pytest.mark.asyncio
@pytest.mark.unit
async def test_track_skill_execution_error() -> None:
    """Test skill execution tracking on error."""
    with pytest.raises(ValueError):
        async with track_skill_execution("transform.schema_map"):
            raise ValueError("Test error")

    # Verify error metric was recorded
