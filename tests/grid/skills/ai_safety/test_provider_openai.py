"""Tests for OpenAI provider safety checks."""

from __future__ import annotations

import sys
import types
from dataclasses import dataclass
from typing import Any

import grid.skills.ai_safety.providers.openai as openai_provider
from grid.skills.ai_safety.base import SafetyCategory, ThreatLevel


@dataclass
class DummyProviderConfig:
    """Dummy provider config with timeout settings."""

    timeout_seconds: int = 10


class DummyConfig:
    """Dummy config for OpenAI provider tests."""

    def __init__(self) -> None:
        self.providers = {"openai": DummyProviderConfig()}

    def is_provider_enabled(self, provider_name: str) -> bool:
        return provider_name == "openai"

    def get_provider_api_key(self, provider_name: str) -> str | None:
        return "test-key" if provider_name == "openai" else None


def test_check_openai_safety_maps_violation(monkeypatch: Any) -> None:
    """OpenAI check should map violations from API response."""

    class DummyResponse:
        status_code = 200

        def json(self) -> dict[str, Any]:
            return {
                "results": [
                    {
                        "categories": {"violence": True},
                        "category_scores": {"violence": 0.9},
                    }
                ]
            }

    def dummy_post(*args: Any, **kwargs: Any) -> DummyResponse:
        return DummyResponse()

    dummy_requests = types.SimpleNamespace(post=dummy_post)
    monkeypatch.setattr(openai_provider, "get_config", lambda: DummyConfig())
    monkeypatch.setitem(sys.modules, "requests", dummy_requests)

    violations = openai_provider.check_openai_safety("Test content")

    assert len(violations) == 1
    violation = violations[0]
    assert violation.category == SafetyCategory.HARMFUL_CONTENT
    assert violation.severity == ThreatLevel.CRITICAL
    assert violation.confidence == 0.9
    assert violation.provider == "openai"


def test_map_openai_category_default() -> None:
    """Unknown categories should map to harmful content."""
    assert openai_provider.map_openai_category("unknown") == SafetyCategory.HARMFUL_CONTENT
