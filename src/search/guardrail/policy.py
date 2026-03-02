"""Guardrail policy: defines which tools run and in which phase."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .auth import AuthSignature, GuardrailAuth, get_default_auth, validate_auth_signature
from .models import GuardrailProfile


@dataclass
class GuardrailPolicy:
    """Policy defining phases and parallel tool groups."""

    phases: dict[str, list[str]] = field(default_factory=dict)
    profiles: dict[str, GuardrailProfile] = field(default_factory=dict)
    active_profile: str | None = None
    auth: GuardrailAuth = field(default_factory=get_default_auth)

    @property
    def pre_query(self) -> list[str]:
        """Tools to run in parallel before the search query."""
        return self.phases.get("pre_query", [])

    @property
    def post_query(self) -> list[str]:
        """Tools to run in parallel after the search query."""
        return self.phases.get("post_query", [])

    def activate_profile(
        self,
        profile_name: str,
        user_id: str | None = None,
        auth_signature: AuthSignature | None = None,
        user_permissions: set[str] | None = None,
        user_role: str = "basic"
    ) -> bool:
        """Activate a persona profile with signature-based authentication and narrowed scope.

        Args:
            profile_name: Name of profile to activate
            user_id: User identifier for signature validation
            auth_signature: Authentication signature for profile access
            user_permissions: Set of explicitly granted profile permissions
            user_role: User role for scope narrowing (developer/designer/manager/admin)

        Returns:
            True if profile was activated, False if authentication failed or access denied
        """
        # Narrow accessibility scope based on role and permissions
        narrowed_profile = self.auth.narrow_access_scope(
            requested_profile=profile_name,
            user_permissions=user_permissions or set(),
            user_role=user_role
        )

        if narrowed_profile is None:
            # No access allowed - scope is too narrow
            self.active_profile = None
            return False

        # If requesting different profile due to scope narrowing, use the narrowed one
        actual_profile_name = narrowed_profile
        profile = self.profiles.get(actual_profile_name)

        if not profile:
            self.active_profile = None
            return False

        # Require authentication for non-basic profiles
        if actual_profile_name != "basic":
            if not user_id or not auth_signature:
                self.active_profile = None
                return False

            # Validate signature
            if not validate_auth_signature(profile, auth_signature, user_id, self.auth):
                self.active_profile = None
                return False

        # Activate the profile
        self.active_profile = actual_profile_name

        # Apply phase overrides if specified
        for phase, tools in profile.phase_overrides.items():
            self.phases[phase] = tools

        return True

    def create_profile_signature(
        self,
        profile_name: str,
        user_id: str,
        timestamp: int | None = None,
        extra_data: dict[str, Any] | None = None
    ) -> AuthSignature | None:
        """Create authentication signature for profile access."""
        profile = self.profiles.get(profile_name)
        if not profile:
            return None

        if timestamp is None:
            import time
            timestamp = int(time.time())

        return self.auth.generate_profile_signature(
            profile=profile,
            user_id=user_id,
            timestamp=timestamp,
            extra_data=extra_data
        )

    def get_budget_limit(self, tool_name: str) -> int:
        """Get budget limit for a tool based on active profile."""
        if self.active_profile and self.active_profile in self.profiles:
            profile = self.profiles[self.active_profile]
            return profile.budget_limits.get(tool_name, 10000)  # Default 10k chars
        return 10000

    def get_safety_rule(self, rule_name: str) -> bool:
        """Check if safety rule is enabled for active profile."""
        if self.active_profile and self.active_profile in self.profiles:
            profile = self.profiles[self.active_profile]
            return profile.safety_rules.get(rule_name, True)  # Default enabled
        return True

    def get_profile_patterns(self, tool_name: str) -> list[str]:
        """Get profile-specific patterns for a tool."""
        if self.active_profile and self.active_profile in self.profiles:
            profile = self.profiles[self.active_profile]
            return profile.patterns.get(tool_name, [])
        return []

    @property
    def active_profile_obj(self) -> GuardrailProfile | None:
        """Get the currently active profile object."""
        if self.active_profile and self.active_profile in self.profiles:
            return self.profiles[self.active_profile]
        return None

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

        # Parse profiles
        profiles: dict[str, GuardrailProfile] = {}
        raw_profiles = data.get("profiles", {})
        for profile_name, profile_data in raw_profiles.items():
            profiles[profile_name] = GuardrailProfile(
                name=profile_name,
                patterns=profile_data.get("patterns", {}),
                budget_limits=profile_data.get("budget_limits", {}),
                safety_rules=profile_data.get("safety_rules", {}),
                phase_overrides=profile_data.get("phase_overrides", {}),
            )

        return cls(
            phases=phases,
            profiles=profiles,
            active_profile=data.get("active_profile")
        )

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
            },
            profiles={
                "basic": GuardrailProfile(
                    name="basic",
                    patterns={
                        "sanitize": [
                            r"[,;{}\\]",  # JSON/DSL-like syntax
                        ]
                    },
                    budget_limits={
                        "sanitize": 2000,  # Very limited for basic users
                        "pii_redact": 5000,
                        "audit": 1000,
                    },
                    safety_rules={
                        "perpetrator_voice_prevention": True,
                        "citation_honesty": True,
                        "limitations_header": True,
                    }
                ),
                "developer": GuardrailProfile(
                    name="developer",
                    patterns={
                        "sanitize": [
                            r"[,;{}\\]",  # JSON/DSL-like syntax
                            r"(?i)(?:drop|delete|truncate|insert|update)\s+\w+",  # SQL injection
                            r"(?i)javascript\s*:",
                            r"<script",
                            r"\$\{|%\s*\{",  # Template injection
                            r"(?i)(?:import|from)\s+\w+",  # Python import injection
                            r"(?i)(?:exec|eval)\s*\(",  # Code execution
                        ]
                    },
                    budget_limits={
                        "sanitize": 5000,  # Shorter queries for dev-focused searches
                        "pii_redact": 8000,
                        "audit": 3000,
                    },
                    safety_rules={
                        "perpetrator_voice_prevention": True,
                        "citation_honesty": True,
                        "limitations_header": True,
                    }
                ),
                "designer": GuardrailProfile(
                    name="designer",
                    patterns={
                        "sanitize": [
                            r"[,;{}\\]",  # JSON/DSL-like syntax
                            r"<script",  # Script injection
                            r"javascript\s*:",  # JS injection
                            r"(?i)(?:on\w+\s*=\s*[\"'])",  # Event handler injection
                        ],
                        "pii_redact": [
                            r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b",  # SSN
                            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
                            r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",  # Phone
                        ]
                    },
                    budget_limits={
                        "sanitize": 8000,  # Longer for design content
                        "pii_redact": 10000,  # Higher for design assets
                        "audit": 5000,
                    },
                    safety_rules={
                        "perpetrator_voice_prevention": True,
                        "citation_honesty": True,
                        "limitations_header": True,
                    }
                ),
                "manager": GuardrailProfile(
                    name="manager",
                    patterns={
                        "sanitize": [
                            r"[,;{}\\]",  # JSON/DSL-like syntax
                            r"(?i)(?:drop|delete|truncate|insert|update)\s+\w+",  # SQL injection
                        ]
                    },
                    budget_limits={
                        "sanitize": 10000,  # Standard length
                        "pii_redact": 15000,  # Higher for reports
                        "audit": 8000,  # Higher audit detail
                    },
                    safety_rules={
                        "perpetrator_voice_prevention": True,
                        "citation_honesty": True,
                        "limitations_header": True,
                        "compliance_reporting": True,
                    },
                    phase_overrides={
                        "post_query": ["pii_redact", "result_filter", "audit", "compliance_report"]
                    }
                )
            }
        )
