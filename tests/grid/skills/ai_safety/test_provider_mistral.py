"""Tests for Mistral provider safety checks."""

from __future__ import annotations

from typing import Any

import grid.skills.ai_safety.providers.mistral as mistral_provider
from grid.skills.ai_safety.base import SafetyCategory, ThreatLevel


class DummyConfig:
    """Dummy config for Mistral provider tests."""

    def is_provider_enabled(self, provider_name: str) -> bool:
        return provider_name == "mistral"


def test_check_mistral_safety_symbol(monkeypatch: Any) -> None:
    """Mistral checks should flag harmful symbols."""
    monkeypatch.setattr(mistral_provider, "get_config", lambda: DummyConfig())

    violations = mistral_provider.check_mistral_safety("Symbol ☠ detected")

    assert len(violations) == 1
    violation = violations[0]
    assert violation.category == SafetyCategory.HARMFUL_CONTENT
    assert violation.severity == ThreatLevel.CRITICAL
    assert violation.provider == "mistral"


def test_check_mistral_safety_code_word(monkeypatch: Any) -> None:
    """Mistral checks should flag coded hate speech."""
    monkeypatch.setattr(mistral_provider, "get_config", lambda: DummyConfig())

    violations = mistral_provider.check_mistral_safety("This references 1488")

    assert len(violations) == 2
    assert all(v.severity == ThreatLevel.HIGH for v in violations)
    assert all(v.provider == "mistral" for v in violations)


def test_check_mistral_safety_safe(monkeypatch: Any) -> None:
    """Safe content should not be flagged."""
    monkeypatch.setattr(mistral_provider, "get_config", lambda: DummyConfig())

    assert mistral_provider.check_mistral_safety("Hello world") == []
