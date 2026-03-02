"""Shared models for guardrail system."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GuardrailProfile:
    """Persona-based guardrail configuration."""
    name: str
    patterns: dict[str, list[str]] = field(default_factory=dict)  # Pattern names to regex strings
    budget_limits: dict[str, int] = field(default_factory=dict)  # Tool -> character limit
    safety_rules: dict[str, bool] = field(default_factory=dict)  # Rule -> enabled
    phase_overrides: dict[str, list[str]] = field(default_factory=dict)  # Phase -> tool overrides
