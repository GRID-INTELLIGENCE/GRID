import os
import sys

import pytest

# Configure path to ensure correct shadowing of the light_of_the_seven package
# We need to import the INNER light_of_the_seven (located at root/light_of_the_seven/light_of_the_seven)
# So we must add root/light_of_the_seven to the path BEFORE root.

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOTS_OUTER_DIR = os.path.join(ROOT_DIR, "light_of_the_seven")
ARCHIVE_DIR = os.path.join(ROOT_DIR, "archive")
LEGACY_SRC_DIR = os.path.join(ARCHIVE_DIR, "legacy_src")
LEGACY_DIR = os.path.join(ARCHIVE_DIR, "legacy")
ARCHIVE_LOTS_DIR = os.path.join(ARCHIVE_DIR, "light_of_the_seven")
SCRIPTS_DIR = os.path.join(ROOT_DIR, "scripts")
# DEFINITION module is at src/cognitive/context/DEFINITION.py
CONTEXT_DIR = os.path.join(ROOT_DIR, "src", "cognitive", "context")

# Insert at specific index to prioritize over root (usually sys.path[0] or [1])
if LOTS_OUTER_DIR not in sys.path:
    sys.path.insert(0, LOTS_OUTER_DIR)

# Add archive paths for legacy modules
if LEGACY_SRC_DIR not in sys.path:
    sys.path.insert(1, LEGACY_SRC_DIR)

if LEGACY_DIR not in sys.path:
    sys.path.insert(2, LEGACY_DIR)

if ARCHIVE_LOTS_DIR not in sys.path:
    sys.path.insert(3, ARCHIVE_LOTS_DIR)

# Also ensure root is in path for 'application' packages
if ROOT_DIR not in sys.path:
    sys.path.insert(4, ROOT_DIR)

# Add scripts directory for git_intelligence and other script modules
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(5, SCRIPTS_DIR)

# Add .context directory for GCI DEFINITION module
context_candidates = [
    CONTEXT_DIR,
    os.path.join(ROOT_DIR, "src", "cognitive", "context"),
]
for candidate in context_candidates:
    if os.path.isdir(candidate) and candidate not in sys.path:
        sys.path.insert(6, candidate)


@pytest.fixture(scope="session", autouse=True)
def setup_env():
    """Set test environment variables without triggering DB connections.

    CRITICAL: Do NOT call reload_settings() here as it can trigger database
    connection attempts that may hang or timeout. Settings will be loaded
    lazily when needed with the test environment variables set.
    """
    import os

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

    # DON'T call reload_settings() here - it can trigger DB connections
    # Settings will be loaded lazily when needed with test environment


@pytest.fixture(autouse=True)
def reset_services():
    """Reset singleton services before and after each test for isolation."""
    # Reset before test
    try:
        from application.resonance.api.dependencies import reset_resonance_service

        reset_resonance_service()
    except ImportError:
        pass

    yield

    # Reset after test
    try:
        from application.resonance.api.dependencies import reset_resonance_service

        reset_resonance_service()
    except ImportError:
        pass


from unittest.mock import AsyncMock, Mock


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
