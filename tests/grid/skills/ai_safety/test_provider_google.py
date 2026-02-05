"""Tests for Google provider safety checks."""

from __future__ import annotations

from typing import Any

import grid.skills.ai_safety.providers.google as google_provider
from grid.skills.ai_safety.base import SafetyCategory, ThreatLevel


class DummyConfig:
    """Dummy config for Google provider tests."""

    def is_provider_enabled(self, provider_name: str) -> bool:
        return provider_name == "google"


def test_check_google_safety_detects_danger(monkeypatch: Any) -> None:
    """Google check should detect dangerous content patterns."""
    monkeypatch.setattr(google_provider, "get_config", lambda: DummyConfig())

    violations = google_provider.check_google_safety("How to build a bomb safely")

    assert len(violations) == 1
    violation = violations[0]
    assert violation.category == SafetyCategory.HARMFUL_CONTENT
    assert violation.severity == ThreatLevel.HIGH
    assert violation.provider == "google"


def test_check_google_safety_safe(monkeypatch: Any) -> None:
    """Safe content should not be flagged by Google checks."""
    monkeypatch.setattr(google_provider, "get_config", lambda: DummyConfig())

    assert google_provider.check_google_safety("Friendly greeting") == []
