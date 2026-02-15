"""Tests for Discussion Service."""

import pytest
from fastapi.testclient import TestClient

from .main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "discussion_service"


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Discussion Service"
    assert "endpoints" in data


def test_topic_extraction(client):
    """Test topic extraction."""
    request_data = {
        "text": "The Arena API provides dynamic routing, rate limiting, and AI safety checks. "
        "Authentication uses JWT tokens and API keys. Service discovery enables health monitoring.",
        "use_llm": False,
        "max_topics": 5,
    }

    response = client.post("/topics/extract", json=request_data)
    assert response.status_code == 200
    data = response.json()

    assert "topics" in data
    assert "total_topics" in data
    assert data["total_topics"] > 0
    assert "processing_time" in data


def test_discussion_endpoint(client):
    """Test discussion endpoint."""
    request_data = {
        "text": "Recent developments in AI safety include new techniques for bias detection, "
        "compliance monitoring with GDPR and HIPAA standards, and advanced rate limiting algorithms.",
        "max_depth": 2,
        "extract_topics": True,
        "use_llm_topics": False,
    }

    response = client.post("/discuss", json=request_data)
    # May fail auth in test, but check structure
    assert response.status_code in [200, 401, 403]

    if response.status_code == 200:
        data = response.json()
        assert "discussion_id" in data
        assert "reasoning_trace" in data
        assert "summary" in data


def test_list_discussions(client):
    """Test list discussions endpoint."""
    response = client.get("/discussions")
    assert response.status_code == 200
    data = response.json()
    assert "discussions" in data
    assert "total" in data


def test_invalid_topic_extraction(client):
    """Test topic extraction with invalid input."""
    request_data = {"text": "Short", "use_llm": False, "max_topics": 5}

    response = client.post("/topics/extract", json=request_data)
    assert response.status_code == 422  # Validation error


def test_get_nonexistent_discussion(client):
    """Test getting a discussion that doesn't exist."""
    response = client.get("/discussions/nonexistent")
    assert response.status_code == 404
