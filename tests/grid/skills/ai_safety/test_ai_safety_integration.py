"""Integration tests for AI safety monitor and providers."""

from __future__ import annotations

from typing import Any, Generator

import pytest

import grid.skills.ai_safety.monitor as monitor_module
from grid.skills.ai_safety.base import SafetyCategory, SafetyViolation, ThreatLevel
from grid.skills.ai_safety.monitor import SafetyMonitor
from grid.skills.ai_safety.providers.base import provider_handler_factory


@pytest.fixture()
def reset_monitor() -> Generator[None]:
    """Reset global monitor singleton for isolation."""
    monitor_module._monitor = None
    yield
    monitor_module._monitor = None


class DummyProvider:
    """Dummy provider for integration testing."""

    def check_content(self, content: str, **kwargs: Any) -> list[SafetyViolation]:
        return [
            SafetyViolation(
                category=SafetyCategory.HARMFUL_CONTENT,
                severity=ThreatLevel.HIGH,
                confidence=0.9,
                description="Dummy violation",
                provider="dummy",
            )
        ]


def test_monitor_integration_with_provider(reset_monitor: None, monkeypatch: Any) -> None:
    """Monitor should integrate with provider handler outputs."""
    provider = DummyProvider()
    provider_skill = provider_handler_factory("dummy", provider.check_content)
    monitor = SafetyMonitor()
    session = monitor.create_session("stream")

    result = provider_skill.run({"content": "Unsafe content"})

    assert result["success"] is True
    assert result["violation_count"] == 1

    report = monitor.check_content(session.session_id, "Unsafe content")

    assert report.threat_level
    assert report.metadata["session_id"] == session.session_id
