"""Guardrail policy: defines which tools run and in which phase."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class GuardrailPolicy:
    """Policy defining phases and parallel tool groups."""

    phases: dict[str, list[str]] = field(default_factory=dict)

    @property
    def pre_query(self) -> list[str]:
        """Tools to run in parallel before the search query."""
        return self.phases.get("pre_query", [])

    @property
    def post_query(self) -> list[str]:
        """Tools to run in parallel after the search query."""
        return self.phases.get("post_query", [])

    def get_parallel_group(self, phase: str) -> list[str]:
        """Return tools to run in parallel for a phase."""
        return self.phases.get(phase, [])

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GuardrailPolicy:
        """Build policy from a dictionary."""
        phases: dict[str, list[str]] = {}
        raw_phases = data.get("phases", {})
        for phase_name, tools in raw_phases.items():
            if isinstance(tools, list):
                phases[phase_name] = list(tools)
            elif isinstance(tools, dict) and "parallel" in tools:
                phases[phase_name] = list(tools["parallel"])
            else:
                phases[phase_name] = []
        return cls(phases=phases)

    @classmethod
    def load(cls, path: Path) -> GuardrailPolicy:
        """Load policy from a YAML or JSON file."""
        content = path.read_text()
        if path.suffix in (".yaml", ".yml"):
            data = yaml.safe_load(content) or {}
        elif path.suffix == ".json":
            import json

            data = json.loads(content)
        else:
            data = yaml.safe_load(content) or {}
        return cls.from_dict(data)

    @classmethod
    def default(cls) -> GuardrailPolicy:
        """Default policy with auth, rate_limit, sanitize, access_control pre_query;
        pii_redact, result_filter, audit post_query."""
        return cls(
            phases={
                "pre_query": ["auth", "rate_limit", "sanitize", "access_control"],
                "post_query": ["pii_redact", "result_filter", "audit"],
            }
        )
