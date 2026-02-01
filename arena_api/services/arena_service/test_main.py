"""
Arena Service Tests
"""

import os
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "Arena", "the_chase", "python", "src"))

from main import app

client = TestClient(app)


def test_health():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "cache_entries" in data


def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Arena Service"


def test_adsr_trigger():
    """Test ADSR trigger endpoint."""
    response = client.post("/adsr/test_entity/trigger")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["phase"] == "attack"


def test_adsr_metrics():
    """Test ADSR metrics endpoint."""
    client.post("/adsr/test_entity/trigger")
    response = client.get("/adsr/test_entity")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "metrics" in data
    metrics = data["metrics"]
    assert metrics["amplitude"] >= 0.0


def test_adsr_release():
    """Test ADSR release endpoint."""
    client.post("/adsr/test_entity/trigger")
    response = client.post("/adsr/test_entity/release")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_reward_state():
    """Test get reward state endpoint."""
    response = client.get("/rewards/test_entity")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["state"]["entity_id"] == "test_entity"
    assert "honor" in data["state"]


def test_add_achievement():
    """Test add achievement endpoint."""
    achievement = {"type": "significant", "points": 12, "description": "Test achievement"}
    response = client.post("/rewards/test_entity/achievement", json=achievement)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["state"]["honor"] == 12.0
    assert data["state"]["level"] == "acknowledged"


def test_honor_decay():
    """Test honor decay endpoint."""
    client.post("/rewards/decay_entity/achievement", json={"type": "significant", "points": 12})
    response = client.post("/rewards/decay_entity/decay?rate=0.5")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["state"]["honor"] == 6.0


def test_achievement_escalation():
    """Test achievement level escalation."""
    for i in range(5):
        client.post("/rewards/escalate_entity/achievement", json={"type": "moderate", "points": 8})

    response = client.get("/rewards/escalate_entity")
    data = response.json()
    assert data["state"]["level"] in ["rewarded", "promoted"]
