"""
Tests for API documentation module.
"""

import pytest
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.api_docs import (
    setup_api_docs,
    export_openapi_spec,
    export_html_docs,
)


@pytest.fixture
def app() -> FastAPI:
    """Create test FastAPI app."""
    app = FastAPI()

    @app.get("/test")
    async def test_endpoint():
        """Test endpoint."""
        return {"status": "ok"}

    @app.post("/users", tags=["Users"])
    async def create_user(name: str, email: str):
        """Create a new user."""
        return {"name": name, "email": email}

    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app)


@pytest.mark.unit
def test_setup_api_docs(app: FastAPI) -> None:
    """Test API documentation setup."""
    setup_api_docs(
        app,
        title="Test API",
        version="1.0.0",
        description="Test description",
    )

    # Verify OpenAPI schema is generated
    openapi_schema = app.openapi()
    assert openapi_schema is not None
    assert openapi_schema["info"]["title"] == "Test API"
    assert openapi_schema["info"]["version"] == "1.0.0"


@pytest.mark.unit
def test_openapi_security_schemes(app: FastAPI) -> None:
    """Test security schemes in OpenAPI schema."""
    setup_api_docs(app)
    openapi_schema = app.openapi()

    # Verify security schemes
    assert "components" in openapi_schema
    assert "securitySchemes" in openapi_schema["components"]
    assert "BearerAuth" in openapi_schema["components"]["securitySchemes"]


@pytest.mark.unit
def test_redoc_endpoint(app: FastAPI, client: TestClient) -> None:
    """Test ReDoc endpoint availability."""
    setup_api_docs(app)

    response = client.get("/redoc")
    assert response.status_code == 200
    assert b"redoc" in response.content.lower()


@pytest.mark.unit
def test_export_openapi_spec(app: FastAPI, tmp_path: Path) -> None:
    """Test OpenAPI spec export."""
    setup_api_docs(app)
    output_file = tmp_path / "openapi.json"

    export_openapi_spec(app, output_file)

    assert output_file.exists()
    assert output_file.stat().st_size > 0

    # Verify valid JSON
    import json

    with open(output_file) as f:
        data = json.load(f)
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data


@pytest.mark.unit
def test_export_html_docs(app: FastAPI, tmp_path: Path) -> None:
    """Test HTML documentation export."""
    setup_api_docs(app, title="Test API")
    output_file = tmp_path / "docs.html"

    export_html_docs(app, output_file)

    assert output_file.exists()
    assert output_file.stat().st_size > 0

    # Verify HTML content
    content = output_file.read_text()
    assert "<!DOCTYPE html>" in content
    assert "Test API" in content
    assert "swagger-ui" in content.lower()


@pytest.mark.unit
def test_openapi_endpoint(app: FastAPI, client: TestClient) -> None:
    """Test OpenAPI JSON endpoint."""
    setup_api_docs(app)

    response = client.get("/openapi.json")
    assert response.status_code == 200

    data = response.json()
    assert "openapi" in data
    assert "paths" in data


@pytest.mark.unit
def test_swagger_ui_endpoint(app: FastAPI, client: TestClient) -> None:
    """Test Swagger UI endpoint."""
    setup_api_docs(app)

    response = client.get("/docs")
    assert response.status_code == 200
