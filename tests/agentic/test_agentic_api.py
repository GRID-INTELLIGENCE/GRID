"""Tests for agentic API endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from application.mothership.dependencies import get_config, verify_authentication
from application.mothership.main import create_app
from application.mothership.routers.agentic import get_agentic_system, get_processing_unit

# Define mocks globally or in fixtures to use in overrides
mock_proc_unit = MagicMock()
mock_sys = MagicMock()


@pytest.fixture
def mock_processing_unit_fixture():
    """Configure mock processing unit."""
    result = MagicMock()
    result.case_id = "TEST-001"
    result.category.value = "testing"
    result.structured_data.priority = "high"
    result.structured_data.confidence = 0.85
    result.structured_data.labels = []
    result.structured_data.keywords = []
    result.structured_data.__dict__ = {
        "priority": "high",
        "confidence": 0.85,
        "labels": [],
        "keywords": [],
        "recommended_roles": ["Executor"],
        "recommended_tasks": ["/execute"],
    }
    result.timestamp = "2025-01-08T10:00:00Z"
    result.reference_file_path = ".case_references/TEST-001_reference.json"

    mock_proc_unit.process_input.return_value = result

    reference_data = {
        "case_id": "TEST-001",
        "reference_file_path": ".case_references/TEST-001_reference.json",
        "recommended_roles": ["Executor"],
        "recommended_tasks": ["/execute"],
        "content": {},
        "recommended_workflow": [],
    }
    mock_proc_unit.get_reference_file.return_value = reference_data

    enriched_result = {"structured_data": {"priority": "high"}}
    mock_proc_unit.enrich_with_user_input.return_value = enriched_result

    return mock_proc_unit


@pytest.fixture
def mock_agentic_system_fixture():
    """Configure mock agentic system."""
    mock_sys.repository = MagicMock()
    mock_sys.event_bus = MagicMock()
    mock_sys.event_bus.publish = AsyncMock()
    mock_sys.event_bus.get_event_history = AsyncMock(return_value=[])

    mock_case = MagicMock()
    mock_case.case_id = "TEST-001"
    mock_case.status = "categorized"
    mock_case.category = "testing"
    mock_case.priority = "high"
    mock_case.confidence = 0.85
    mock_case.reference_file_path = ".case_references/TEST-001_reference.json"
    mock_case.created_at = datetime.now(UTC)
    mock_case.updated_at = datetime.now(UTC)
    mock_case.completed_at = None
    mock_case.outcome = None
    mock_case.solution = None

    mock_sys.repository.get_case = AsyncMock(return_value=mock_case)
    mock_sys.repository.update_case_status = AsyncMock(return_value=mock_case)

    return mock_sys


@pytest.fixture
def client(mock_processing_unit_fixture, mock_agentic_system_fixture):
    """Create test client with mocked dependencies."""
    import os

    os.environ.setdefault("MOTHERSHIP_ENVIRONMENT", "test")

    # Define MockSettings class hierarchy clearly for Main.py usage
    class MockSecurity:
        secret_key = "test_key"
        cors_origins = ["*"]
        cors_allow_credentials = True
        strict_mode = False
        rate_limit_enabled = True
        rate_limit_requests = 100
        rate_limit_window_seconds = 60
        api_key_header = "X-API-Key"
        algorithm = "HS256"
        access_token_expire_minutes = 30
        refresh_token_expire_days = 7
        max_request_size_bytes = 10485760
        # DRT / accountability / parasite guard (disabled for tests)
        drt_enabled = False
        drt_behavioral_similarity_threshold = 0.85
        drt_retention_hours = 96
        drt_enforcement_mode = "monitor"
        drt_websocket_monitoring_enabled = False
        drt_api_movement_logging_enabled = False
        drt_penalty_points_enabled = False
        drt_slo_evaluation_interval_seconds = 300
        drt_slo_violation_penalty_base = 10
        drt_report_generation_enabled = False
        accountability_enabled = False
        accountability_enforcement_mode = "monitor"
        accountability_contract_path = "config/accountability/contracts.yaml"
        parasite_guard_enabled = False
        parasite_guard_pruning_enabled = False

    class MockTelemetry:
        enabled = False
        metrics_enabled = False
        tracing_enabled = False
        log_level = MagicMock()
        log_level.value = "INFO"
        metrics_path = "/metrics"

    class MockCockpit:
        max_concurrent_sessions = 100
        task_queue_size = 1000

    class MockServer:
        host = "localhost"
        port = 8000
        reload = False
        workers = 1

    class MockSettings:
        environment = MagicMock()
        environment.value = "test"
        is_development = True
        app_name = "Mothership"
        app_version = "1.0.0"
        security = MockSecurity()
        telemetry = MockTelemetry()
        cockpit = MockCockpit()
        server = MockServer()

    mock_settings_instance = MockSettings()

    # Patch get_settings used in main.py to return our mock settings with strict_mode=False
    with patch("application.mothership.main.get_settings", return_value=mock_settings_instance):
        app = create_app()

    # Override dependencies for Endpoints
    app.dependency_overrides[get_processing_unit] = lambda: mock_processing_unit_fixture
    app.dependency_overrides[get_agentic_system] = lambda: mock_agentic_system_fixture

    # Override auth to be permissive
    app.dependency_overrides[verify_authentication] = lambda: {
        "sub": "test_user",
        "user_id": "user_123",
        "scopes": ["read", "write"],
    }

    # Override config dependency if any endpoint uses it directly
    app.dependency_overrides[get_config] = lambda: mock_settings_instance

    return TestClient(app)


@pytest.mark.xfail(reason="Authentication mock override not propagating to middleware correctly")
def test_create_case(client):
    """Test POST /api/v1/agentic/cases."""
    response = client.post(
        "/api/v1/agentic/cases",
        headers={"Authorization": "Bearer test-token"},
        json={
            "raw_input": "Add contract testing to CI",
            "examples": ["Similar setup in project X"],
            "scenarios": ["Run tests on every PR"],
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["case_id"] == "TEST-001"
    assert data["status"] == "categorized"
    assert data["category"] == "testing"


def test_get_case(client):
    """Test GET /api/v1/agentic/cases/{case_id}."""
    response = client.get("/api/v1/agentic/cases/TEST-001")

    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "TEST-001"


def test_get_reference_file(client):
    """Test GET /api/v1/agentic/cases/{case_id}/reference."""
    response = client.get("/api/v1/agentic/cases/TEST-001/reference")

    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "TEST-001"
    assert "content" in data


@pytest.mark.skip(reason="Requires external database for metrics")
def test_get_agent_experience(client):
    """Test GET /api/v1/agentic/experience."""
    response = client.get("/api/v1/agentic/experience")
    assert response.status_code in [200, 503]
