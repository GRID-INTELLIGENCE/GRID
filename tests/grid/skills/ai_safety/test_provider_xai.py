"""Tests for xAI provider safety checks."""

from __future__ import annotations

from typing import Any

import grid.skills.ai_safety.providers.xai as xai_provider
from grid.skills.ai_safety.base import SafetyCategory, ThreatLevel


class DummyConfig:
    """Dummy config for xAI provider tests."""

    def is_provider_enabled(self, provider_name: str) -> bool:
        return provider_name == "xai"


def test_check_xai_safety_misinformation(monkeypatch: Any) -> None:
    """xAI checks should detect misinformation patterns."""
    monkeypatch.setattr(xai_provider, "get_config", lambda: DummyConfig())

    violations = xai_provider.check_xai_safety("This is fake news about events")

    assert len(violations) == 1
    violation = violations[0]
    assert violation.category == SafetyCategory.MISINFORMATION
    assert violation.severity == ThreatLevel.MEDIUM
    assert violation.provider == "xai"


def test_check_xai_safety_truth_violation(monkeypatch: Any) -> None:
    """xAI checks should detect truth suppression patterns."""
    monkeypatch.setattr(xai_provider, "get_config", lambda: DummyConfig())

    violations = xai_provider.check_xai_safety("We should cover up evidence now")

    assert len(violations) == 1
    violation = violations[0]
    assert violation.category == SafetyCategory.MANIPULATION
    assert violation.severity == ThreatLevel.HIGH
    assert violation.provider == "xai"
