"""Tests for Anthropic provider safety checks."""

from __future__ import annotations

from typing import Any

import grid.skills.ai_safety.providers.anthropic as anthropic_provider
from grid.skills.ai_safety.base import SafetyCategory, ThreatLevel


class DummyConfig:
    """Dummy config for Anthropic provider tests."""

    def is_provider_enabled(self, provider_name: str) -> bool:
        return provider_name == "anthropic"


def test_check_anthropic_safety_detects_harmful(monkeypatch: Any) -> None:
    """Anthropic check should detect harmful patterns."""
    monkeypatch.setattr(anthropic_provider, "get_config", lambda: DummyConfig())

    violations = anthropic_provider.check_anthropic_safety("How to build dangerous things")

    assert len(violations) == 1
    violation = violations[0]
    assert violation.category == SafetyCategory.HARMFUL_CONTENT
    assert violation.severity == ThreatLevel.HIGH
    assert violation.provider == "anthropic"


def test_check_anthropic_safety_safe_content(monkeypatch: Any) -> None:
    """Safe content should return no violations."""
    monkeypatch.setattr(anthropic_provider, "get_config", lambda: DummyConfig())

    violations = anthropic_provider.check_anthropic_safety("Please summarize this article.")

    assert violations == []
