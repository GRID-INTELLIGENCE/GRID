"""Tests for NVIDIA provider safety checks."""

from __future__ import annotations

from typing import Any

import grid.skills.ai_safety.providers.nvidia as nvidia_provider
from grid.skills.ai_safety.base import SafetyCategory, ThreatLevel


class DummyConfig:
    """Dummy config for NVIDIA provider tests."""

    def is_provider_enabled(self, provider_name: str) -> bool:
        return provider_name == "nvidia"


def test_check_nvidia_safety_security(monkeypatch: Any) -> None:
    """NVIDIA checks should flag security risk patterns."""
    monkeypatch.setattr(nvidia_provider, "get_config", lambda: DummyConfig())

    violations = nvidia_provider.check_nvidia_safety("Exploit a zero-day vulnerability")

    assert len(violations) == 1
    violation = violations[0]
    assert violation.category == SafetyCategory.HARMFUL_CONTENT
    assert violation.severity == ThreatLevel.HIGH
    assert violation.provider == "nvidia"


def test_check_nvidia_safety_compliance(monkeypatch: Any) -> None:
    """NVIDIA checks should flag compliance violations."""
    monkeypatch.setattr(nvidia_provider, "get_config", lambda: DummyConfig())

    violations = nvidia_provider.check_nvidia_safety("This is a GDPR violation")

    assert len(violations) == 1
    violation = violations[0]
    assert violation.category == SafetyCategory.MISINFORMATION
    assert violation.severity == ThreatLevel.MEDIUM
    assert violation.provider == "nvidia"
