"""
Test initialization and shared fixtures for Parasite Guard tests.
"""

from __future__ import annotations

import pytest
from pathlib import Path

# Ensure parasite_guard is importable
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def test_config():
    """Create test configuration with all components enabled."""
    from infrastructure.parasite_guard.config import ParasiteGuardConfig, GuardMode

    config = ParasiteGuardConfig()
    config.enabled = True
    config.disabled = False

    # Enable all test components
    config.enable_component("websocket", GuardMode.FULL, sanitize=True)
    config.enable_component("eventbus", GuardMode.DRY_RUN)
    config.enable_component("db", GuardMode.FULL, sanitize=True)

    return config


@pytest.fixture
def dry_run_config():
    """Create dry-run configuration for safe testing."""
    from infrastructure.parasite_guard.config import ParasiteGuardConfig, GuardMode

    config = ParasiteGuardConfig()
    config.enabled = True
    config.disabled = False
    config.global_mode = GuardMode.DRY_RUN

    return config


@pytest.fixture
def detect_mode_config():
    """Create detect-mode configuration."""
    from infrastructure.parasite_guard.config import ParasiteGuardConfig, GuardMode

    config = ParasiteGuardConfig()
    config.enabled = True
    config.disabled = False
    config.global_mode = GuardMode.DETECT

    return config


@pytest.fixture
def full_mode_config():
    """Create full-mode configuration with sanitization."""
    from infrastructure.parasite_guard.config import ParasiteGuardConfig, GuardMode

    config = ParasiteGuardConfig()
    config.enabled = True
    config.disabled = False
    config.global_mode = GuardMode.FULL

    return config


@pytest.fixture
def sample_context():
    """Create a sample ParasiteContext for testing."""
    from infrastructure.parasite_guard.models import ParasiteContext, ParasiteSeverity
    import uuid

    return ParasiteContext(
        id=uuid.UUID("12345678-1234-1234-1234-123456789abc"),
        component="websocket",
        pattern="no_ack",
        rule="websocket_no_ack",
        severity=ParasiteSeverity.CRITICAL,
        detection_metadata={
            "connection_id": "conn_123",
            "message_id": "msg_456",
        },
    )


# =============================================================================
# Test Utilities
# =============================================================================


def create_mock_scope(
    path: str = "/test",
    method: str = "GET",
    client: tuple = ("127.0.0.1", 8080),
) -> dict:
    """Create a mock ASGI scope."""
    return {
        "type": "http",
        "path": path,
        "method": method,
        "client": client,
        "headers": [],
    }


def create_mock_receive() -> callable:
    """Create a mock ASGI receive callable."""

    async def receive():
        return {"type": "http.request"}

    return receive


def create_mock_send() -> callable:
    """Create a mock ASGI send callable."""
    sent_messages = []

    async def send(message: dict):
        sent_messages.append(message)

    send.sent_messages = sent_messages
    return send


# =============================================================================
# Pytest Configuration
# =============================================================================


def pytest_configure(config):
    """Configure pytest for parasite guard tests."""
    # Add custom markers
    config.addinivalue_line(
        "markers",
        "detector: Tests for detector implementations",
    )
    config.addinivalue_line(
        "markers",
        "middleware: Tests for middleware",
    )
    config.addinivalue_line(
        "markers",
        "integration: Tests for integration helpers",
    )
    config.addinivalue_line(
        "markers",
        "slow: Mark test as slow running",
    )
