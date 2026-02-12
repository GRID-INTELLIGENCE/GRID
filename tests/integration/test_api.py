import pytest
from fastapi.testclient import TestClient
from src.grid.api.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def auth_client(client):
    """Client with authentication token"""
    # Get auth token
    response = client.post("/auth/token", data={"username": "testuser", "password": "testpass"})
    if response.status_code == 200:
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        return TestClient(app, headers=headers)
    else:
        # If auth fails, return client without auth (for testing endpoints that don't require auth)
        return client

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "version": "1.0.0"}

def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "GRID API" in response.json()["message"]

def test_inference_endpoint(auth_client):
    response = auth_client.post(
        "/api/v1/inference/",
        json={"prompt": "Test prompt", "model": "default"}
    )
    assert response.status_code == 200
    assert "result" in response.json()

def test_privacy_detection(auth_client):
    response = auth_client.post(
        "/api/v1/privacy/detect",
        json={"text": "Contact me at test@example.com"}
    )
    assert response.status_code == 200
    assert len(response.json()["detected_entities"]) > 0
