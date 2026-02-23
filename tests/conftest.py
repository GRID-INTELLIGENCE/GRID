"""
Tests conftest: auto-markers, environment setup, and shared fixtures.

Path resolution is handled by pyproject.toml's pythonpath = ["src"] setting.
No sys.path manipulation needed.
"""

import os
from unittest.mock import AsyncMock, Mock

import pytest

# ---------------------------------------------------------------------------
# Auto-marker: apply markers based on directory structure so selective runs
# work even when individual tests are not explicitly decorated.
# Usage: uv run pytest -m unit          (only fast unit tests)
#        uv run pytest -m safety        (safety enforcement)
#        uv run pytest -m "not slow"    (skip slow tests)
#        uv run pytest --lf             (last-failed only — incremental)
#        uv run pytest -n auto          (parallel via xdist)
# ---------------------------------------------------------------------------
_DIR_MARKER_MAP = {
    "unit": "unit",
    "integration": "integration",
    "api": "api",
    "e2e": "integration",
    "chaos": "slow",
    "smoke": "smoke",
    "skills": "unit",
    "redteam": "redteam",
    "performance": "slow",
    "load": "slow",
}


def pytest_collection_modifyitems(config, items):
    """Auto-apply markers based on test file path."""
    for item in items:
        rel = str(item.fspath)
        # Safety subtree
        if "safety" + os.sep + "tests" in rel:
            item.add_marker(pytest.mark.safety)
        # Boundaries subtree
        if "boundaries" + os.sep + "tests" in rel:
            item.add_marker(pytest.mark.safety)
        # Directory-based markers
        for dirname, marker_name in _DIR_MARKER_MAP.items():
            if os.sep + dirname + os.sep in rel:
                item.add_marker(getattr(pytest.mark, marker_name))
                break


@pytest.fixture(scope="session", autouse=True)
def setup_env():
    """Set test environment variables without triggering DB connections.

    CRITICAL: Do NOT call reload_settings() here as it can trigger database
    connection attempts that may hang or timeout. Settings will be loaded
    lazily when needed with the test environment variables set.
    """
    os.environ["MOTHERSHIP_ENVIRONMENT"] = "test"
    # Generate secure test key: python -c "import secrets; print(secrets.token_urlsafe(32))"
    os.environ["MOTHERSHIP_SECRET_KEY"] = os.environ.get(
        "MOTHERSHIP_SECRET_KEY", "test-secret-key-at-least-32-chars-long-placeholder"
    )
    os.environ["MOTHERSHIP_RATE_LIMIT_ENABLED"] = "false"

    # CRITICAL: Disable database connections in test mode to prevent hangs
    os.environ["MOTHERSHIP_DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["MOTHERSHIP_USE_DATABRICKS"] = "false"
    os.environ["MOTHERSHIP_REDIS_ENABLED"] = "false"

    # Bypass Redis safety checks in test mode (middleware fails closed without Redis)
    os.environ["SAFETY_BYPASS_REDIS"] = "true"


@pytest.fixture(autouse=True)
def reset_services():
    """Reset singleton services before and after each test for isolation."""
    # Lazy import — runs at fixture call, not collection
    try:
        from application.resonance.api.dependencies import reset_resonance_service
    except ImportError:
        reset_resonance_service = None

    # Reset before test
    if reset_resonance_service:
        reset_resonance_service()

    yield

    # Reset after test
    if reset_resonance_service:
        reset_resonance_service()


@pytest.fixture
def mock_event_bus():
    """Shared mock for EventBus."""
    bus = Mock()
    bus.publish = AsyncMock()
    bus.subscribe = Mock()
    bus.get_history = Mock(return_value=[])
    return bus


@pytest.fixture
def mock_cockpit_service():
    """Shared mock for CockpitService."""
    service = Mock()
    service.state = Mock()
    service.state.components = {}
    service.state.alerts = {}
    service.state.started_at = None
    service.state.uptime_seconds = 0.0
    service.execute_task = AsyncMock(return_value={"status": "completed"})
    return service


@pytest.fixture
def mock_rag_engine():
    """Shared mock for RAG Engine."""
    engine = Mock()
    engine.query = AsyncMock(return_value={"answer": "Mocked answer", "sources": []})
    engine.index = AsyncMock(return_value={"status": "success"})
    return engine


@pytest.fixture
def mock_agentic_system(mock_event_bus):
    """Shared mock for AgenticSystem."""
    system = Mock()
    system.event_bus = mock_event_bus
    system.process_case = AsyncMock(return_value={"case_id": "test_case", "status": "completed"})
    system.get_case = AsyncMock(return_value={"case_id": "test_case", "status": "completed"})
    return system
