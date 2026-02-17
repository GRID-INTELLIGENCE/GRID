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
        headers = {"x-request-id": "req_test_123"}

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


def test_openai_handler_fail_closed_on_provider_error(monkeypatch: Any) -> None:
    """Provider failures must fail closed by default."""

    class ErrorResponse:
        status_code = 500
        headers = {"x-request-id": "req_err_500"}

        def json(self) -> dict[str, Any]:
            return {"error": {"message": "server error"}}

    def dummy_post(*args: Any, **kwargs: Any) -> ErrorResponse:
        return ErrorResponse()

    dummy_requests = types.SimpleNamespace(post=dummy_post)
    monkeypatch.setattr(openai_provider, "get_config", lambda: DummyConfig())
    monkeypatch.setitem(sys.modules, "requests", dummy_requests)

    result = openai_provider.openai_handler({"content": "unsafe content", "max_retries": 0})
    assert result["success"] is False
    assert result["degraded"] is True
    assert result["fail_closed"] is True
    assert result["request_id"] == "req_err_500"


def test_openai_handler_explicit_fail_open_override(monkeypatch: Any) -> None:
    """Callers can explicitly opt into fail-open behavior."""

    class ErrorResponse:
        status_code = 503
        headers = {"x-request-id": "req_err_503"}

        def json(self) -> dict[str, Any]:
            return {"error": {"message": "unavailable"}}

    def dummy_post(*args: Any, **kwargs: Any) -> ErrorResponse:
        return ErrorResponse()

    dummy_requests = types.SimpleNamespace(post=dummy_post)
    monkeypatch.setattr(openai_provider, "get_config", lambda: DummyConfig())
    monkeypatch.setitem(sys.modules, "requests", dummy_requests)

    result = openai_provider.openai_handler(
        {"content": "test content", "fail_closed": False, "max_retries": 0}
    )
    assert result["success"] is True
    assert result["degraded"] is True
    assert result["fail_closed"] is False
    assert result["request_id"] == "req_err_503"


def test_check_openai_safety_retries_transient_then_succeeds(monkeypatch: Any) -> None:
    """Transient HTTP errors should be retried with eventual success."""
    call_count = {"count": 0}

    class TransientResponse:
        status_code = 429
        headers = {"Retry-After": "0", "x-request-id": "req_retry_1"}

        def json(self) -> dict[str, Any]:
            return {"error": {"message": "rate limited"}}

    class SuccessResponse:
        status_code = 200
        headers = {"x-request-id": "req_retry_2"}

        def json(self) -> dict[str, Any]:
            return {
                "results": [
                    {
                        "categories": {"violence": True},
                        "category_scores": {"violence": 0.85},
                    }
                ]
            }

    def dummy_post(*args: Any, **kwargs: Any) -> Any:
        call_count["count"] += 1
        if call_count["count"] == 1:
            return TransientResponse()
        return SuccessResponse()

    dummy_requests = types.SimpleNamespace(post=dummy_post)
    monkeypatch.setattr(openai_provider, "get_config", lambda: DummyConfig())
    monkeypatch.setitem(sys.modules, "requests", dummy_requests)

    result = openai_provider.check_openai_safety_detailed(
        "Test content", max_retries=1, retry_base_seconds=0
    )
    assert result.degraded is False
    assert result.retries_attempted == 1
    assert len(result.violations) == 1
    assert call_count["count"] == 2


def test_map_openai_category_default() -> None:
    """Unknown categories should map to harmful content."""
    assert openai_provider.map_openai_category("unknown") == SafetyCategory.HARMFUL_CONTENT
