"""Tests for AI safety provider base utilities."""

from __future__ import annotations

from typing import Any

from grid.skills.ai_safety.base import SafetyCategory, SafetyViolation, ThreatLevel
from grid.skills.ai_safety.providers.base import ProviderSafetySkill, provider_handler_factory


class DummyProvider(ProviderSafetySkill):
    """Dummy provider for base class testing."""

    def __init__(self) -> None:
        super().__init__("dummy")

    def check_content(self, content: str, **kwargs: Any) -> list[SafetyViolation]:
        return []


def test_create_violation_sets_provider() -> None:
    """Provider-created violations should include provider metadata."""
    provider = DummyProvider()

    violation = provider.create_violation(
        category=SafetyCategory.HARMFUL_CONTENT,
        severity=ThreatLevel.HIGH,
        confidence=0.8,
        description="Test",
        evidence={"source": "unit"},
    )

    assert violation.provider == "dummy"
    assert violation.category == SafetyCategory.HARMFUL_CONTENT


def test_provider_handler_factory_success() -> None:
    """Handler factory should return violations and metadata."""
    violation = SafetyViolation(
        category=SafetyCategory.HARMFUL_CONTENT,
        severity=ThreatLevel.LOW,
        confidence=0.2,
        description="Test",
        provider="dummy",
    )

    def check_func(content: str, **kwargs: Any) -> list[SafetyViolation]:
        return [violation]

    handler_skill = provider_handler_factory("dummy", check_func)
    result = handler_skill.run({"content": "Test content"})

    assert result["success"] is True
    assert result["provider"] == "dummy"
    assert result["violation_count"] == 1


def test_provider_handler_factory_empty_content() -> None:
    """Handler factory should short-circuit for empty content."""

    def check_func(content: str, **kwargs: Any) -> list[SafetyViolation]:
        return []

    handler_skill = provider_handler_factory("dummy", check_func)
    result = handler_skill.run({"content": ""})

    assert result["success"] is True
    assert result["violations"] == []
    assert result["message"] == "No content provided"


def test_provider_handler_factory_exception() -> None:
    """Handler factory should return error on exceptions."""

    def check_func(content: str, **kwargs: Any) -> list[SafetyViolation]:
        raise RuntimeError("boom")

    handler_skill = provider_handler_factory("dummy", check_func)
    result = handler_skill.run({"content": "Test"})

    assert result["success"] is False
    assert result["error"] == "boom"
    assert result["provider"] == "dummy"
