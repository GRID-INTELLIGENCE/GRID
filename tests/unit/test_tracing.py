"""
Tests for distributed tracing module.
"""

from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.tracing import SpanContext, get_tracer, setup_fastapi_tracing, setup_tracing


@pytest.fixture
def app_with_tracing() -> FastAPI:
    """Create FastAPI app with tracing enabled."""
    app = FastAPI()
    setup_fastapi_tracing(app, service_name="test-service")

    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    return app


@pytest.fixture
def client(app_with_tracing: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app_with_tracing)


@pytest.mark.unit
@patch("application.tracing.OTLPSpanExporter")
@patch("application.tracing.TracerProvider")
def test_setup_tracing(mock_provider: Mock, mock_exporter: Mock) -> None:
    """Test tracing setup."""
    provider = setup_tracing(
        service_name="test-service",
        jaeger_host="localhost",
        jaeger_port=4317,
    )

    assert provider is not None
    mock_exporter.assert_called_once()


@pytest.mark.unit
def test_get_tracer() -> None:
    """Test getting tracer instance."""
    tracer = get_tracer(__name__)
    assert tracer is not None


@pytest.mark.unit
def test_span_context() -> None:
    """Test span context manager."""
    tracer = get_tracer(__name__)

    with SpanContext(tracer, "test_span", {"key": "value"}) as span:
        assert span is not None


@pytest.mark.unit
def test_span_context_with_error() -> None:
    """Test span context manager with error."""
    tracer = get_tracer(__name__)

    try:
        with SpanContext(tracer, "test_span"):
            raise ValueError("Test error")
    except ValueError:
        pass  # Expected


@pytest.mark.integration
def test_fastapi_instrumentation(client: TestClient) -> None:
    """Test FastAPI instrumentation."""
    response = client.get("/test")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
