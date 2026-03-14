"""
Configuration management for the Transition Gate Toolkit.

Handles secrets, paths, and environment setup for both seal and verify operations.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ToolkitConfig:
    """
    Configuration container for the Transition Gate Toolkit.

    Provides defaults and environment-aware configuration for:
    - Secrets and credentials
    - Path resolution (source/target partitions)
    - Timing parameters (nonce expiry, envelope max age)
    - Audit and logging settings
    """

    # Secrets
    user_secret: str = field(default_factory=lambda: os.environ.get("TRANSITION_GATE_SECRET", ""))

    # Paths
    source_partition: str = "E:\\"
    target_partition: str = "C:\\Users\\USER\\cascadeprojects"
    staging_dir: Path = field(default_factory=lambda: Path("E:\\Fruits\\releases"))
    audit_dir: Path = field(default_factory=lambda: Path("E:\\Fruits\\releases\\audit"))

    # Timing parameters
    nonce_max_age_seconds: float = 600.0  # 10 minutes
    envelope_max_age_seconds: float = 600.0  # 10 minutes

    # Verification requirements
    require_tests: bool = True
    require_lint: bool = False

    # Audit settings
    enable_audit_logging: bool = True
    audit_format: str = "ndjson"  # ndjson or json

    # Machine fingerprint overrides (for testing/cross-machine verification)
    machine_overrides: dict[str, str] = field(default_factory=dict)
    extra_fingerprint_context: str | None = None

    def __post_init__(self) -> None:
        """Ensure paths are Path objects and directories exist."""
        self.staging_dir = Path(self.staging_dir)
        self.audit_dir = Path(self.audit_dir)

        # Create directories if they don't exist
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        self.audit_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_file(cls, path: Path | str) -> ToolkitConfig:
        """Load configuration from a JSON file."""
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, encoding="utf-8") as f:
            data = json.load(f)

        # Convert path strings to Path objects
        if "staging_dir" in data:
            data["staging_dir"] = Path(data["staging_dir"])
        if "audit_dir" in data:
            data["audit_dir"] = Path(data["audit_dir"])

        return cls(**data)

    def to_file(self, path: Path | str) -> None:
        """Save configuration to a JSON file."""
        config_path = Path(path)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "user_secret": "[REDACTED]" if self.user_secret else "",
            "source_partition": self.source_partition,
            "target_partition": self.target_partition,
            "staging_dir": str(self.staging_dir),
            "audit_dir": str(self.audit_dir),
            "nonce_max_age_seconds": self.nonce_max_age_seconds,
            "envelope_max_age_seconds": self.envelope_max_age_seconds,
            "require_tests": self.require_tests,
            "require_lint": self.require_lint,
            "enable_audit_logging": self.enable_audit_logging,
            "audit_format": self.audit_format,
            "machine_overrides": self.machine_overrides,
            "extra_fingerprint_context": self.extra_fingerprint_context,
        }

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @property
    def nonce_registry_path(self) -> Path:
        """Path to the nonce registry file."""
        return self.audit_dir / "nonce_registry.json"

    @property
    def audit_log_path(self) -> Path:
        """Path to the audit log file."""
        return self.audit_dir / "verification_audit.ndjson"

    def validate(self) -> list[str]:
        """
        Validate configuration and return list of issues.

        Returns empty list if configuration is valid.
        """
        issues = []

        if not self.user_secret:
            issues.append("user_secret is empty (set TRANSITION_GATE_SECRET env var)")

        if self.nonce_max_age_seconds <= 0:
            issues.append("nonce_max_age_seconds must be positive")

        if self.envelope_max_age_seconds <= 0:
            issues.append("envelope_max_age_seconds must be positive")

        if not self.staging_dir.exists():
            issues.append(f"staging_dir does not exist: {self.staging_dir}")

        return issues


# Default configuration instance
DEFAULT_CONFIG = ToolkitConfig()


def get_config_from_env() -> ToolkitConfig:
    """
    Build configuration from environment variables.

    Environment variables:
        TRANSITION_GATE_SECRET: Shared secret for HMAC
        TRANSITION_GATE_SOURCE: Source partition (default: E:\\)
        TRANSITION_GATE_TARGET: Target partition (default: C:\\...)
        TRANSITION_GATE_STAGING: Staging directory
        TRANSITION_GATE_AUDIT: Audit directory
        TRANSITION_GATE_MAX_AGE: Envelope max age in seconds
        TRANSITION_GATE_REQUIRE_TESTS: Require tests_passed flag
    """
    return ToolkitConfig(
        user_secret=os.environ.get("TRANSITION_GATE_SECRET", ""),
        source_partition=os.environ.get("TRANSITION_GATE_SOURCE", "E:\\"),
        target_partition=os.environ.get("TRANSITION_GATE_TARGET", "C:\\Users\\USER\\cascadeprojects"),
        staging_dir=Path(os.environ.get("TRANSITION_GATE_STAGING", "E:\\Fruits\\releases")),
        audit_dir=Path(os.environ.get("TRANSITION_GATE_AUDIT", "E:\\Fruits\\releases\\audit")),
        envelope_max_age_seconds=float(os.environ.get("TRANSITION_GATE_MAX_AGE", "600.0")),
        require_tests=os.environ.get("TRANSITION_GATE_REQUIRE_TESTS", "true").lower() == "true",
    )
