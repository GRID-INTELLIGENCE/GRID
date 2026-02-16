"""
Parasite Guard Configuration System.

Manages feature flags, thresholds, and component-specific settings.
Supports three-phase rollout: dry_run → detect → full.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class GuardMode(Enum):
    """Operating modes for the parasite guard."""

    DISABLED = auto()  # Completely disabled
    DRY_RUN = auto()  # Phase 1: Detect and log only, no action
    DETECT = auto()  # Phase 2: Detection with validation
    FULL = auto()  # Phase 3: Detection + deferred sanitization


@dataclass
class ComponentConfig:
    """Configuration for a single component."""

    enabled: bool = False
    mode: GuardMode = GuardMode.DRY_RUN
    sanitize: bool = False
    async_delay_seconds: int = 5
    thresholds: dict[str, Any] = field(default_factory=dict)
    whitelist: list[str] = field(default_factory=list)
    blacklist: list[str] = field(default_factory=list)

    @classmethod
    def from_env(cls, component: str, prefix: str = "PARASITE_GUARD") -> ComponentConfig:
        """Create config from environment variables."""
        env_prefix = f"{prefix}_{component.upper()}"

        # Check if component is enabled
        enabled = os.getenv(f"{env_prefix}", "0").lower() in ("1", "true", "yes")

        # Get mode
        mode_str = os.getenv(f"{env_prefix}_MODE", "dry_run").upper()
        mode = GuardMode[mode_str] if mode_str in GuardMode.__members__ else GuardMode.DRY_RUN

        # Get sanitization flag
        sanitize = os.getenv(f"{env_prefix}_SANITIZATION", "0").lower() in ("1", "true", "yes")

        # Get async delay
        delay = int(os.getenv(f"{env_prefix}_ASYNC_DELAY", "5"))

        # Get thresholds (JSON or comma-separated key=value)
        thresholds = {}
        thresholds_str = os.getenv(f"{env_prefix}_THRESHOLDS", "")
        if thresholds_str:
            for pair in thresholds_str.split(","):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    try:
                        value = int(value)
                    except ValueError:
                        try:
                            value = float(value)
                        except ValueError:
                            pass
                    thresholds[key] = value

        return cls(
            enabled=enabled,
            mode=mode,
            sanitize=sanitize,
            async_delay_seconds=delay,
            thresholds=thresholds,
        )


@dataclass
class ParasiteGuardConfig:
    """Master configuration for parasite guard."""

    # Master switches
    enabled: bool = field(default_factory=lambda: os.getenv("PARASITE_GUARD", "0").lower() in ("1", "true", "yes"))
    disabled: bool = field(
        default_factory=lambda: os.getenv("PARASITE_GUARD_DISABLE", "0").lower() in ("1", "true", "yes")
    )

    # Global mode (overrides component modes if set)
    global_mode: GuardMode | None = field(
        default_factory=lambda: (
            GuardMode[os.getenv("PARASITE_GUARD_MODE", "DISABLED").upper()]
            if os.getenv("PARASITE_GUARD_MODE")
            else None
        )
    )

    # Component-specific configs
    components: dict[str, ComponentConfig] = field(default_factory=dict)

    # Detection settings
    detection_timeout_ms: int = field(default_factory=lambda: int(os.getenv("PARASITE_DETECT_TIMEOUT_MS", "100")))
    max_detection_depth: int = field(default_factory=lambda: int(os.getenv("PARASITE_MAX_DEPTH", "5")))

    # Anomaly detection settings (tunable thresholds)
    anomaly_z_threshold: float = field(default_factory=lambda: float(os.getenv("PARASITE_ANOMALY_Z_THRESHOLD", "3.5")))
    anomaly_window_size: int = field(default_factory=lambda: int(os.getenv("PARASITE_ANOMALY_WINDOW_SIZE", "60")))
    anomaly_adaptive_percentile: float = field(
        default_factory=lambda: float(os.getenv("PARASITE_ANOMALY_ADAPTIVE_PERCENTILE", "99.0"))
    )
    # Rate limit detector specific thresholds
    rate_limit_window_seconds: float = field(
        default_factory=lambda: float(os.getenv("PARASITE_RATE_LIMIT_WINDOW", "60.0"))
    )
    rate_limit_max_rate: float = field(
        default_factory=lambda: float(os.getenv("PARASITE_RATE_LIMIT_MAX_RATE", "100.0"))
    )
    rate_limit_z_threshold: float = field(
        default_factory=lambda: float(os.getenv("PARASITE_RATE_LIMIT_Z_THRESHOLD", "3.0"))
    )

    # Response settings for detected parasites
    # 403 = Forbidden (explicit block), 200 = OK (stealth null response)
    parasite_response_status_code: int = field(
        default_factory=lambda: int(os.getenv("PARASITE_RESPONSE_STATUS_CODE", "403"))
    )

    # Sanitization settings
    sanitize_async: bool = True
    sanitize_timeout_seconds: int = field(default_factory=lambda: int(os.getenv("PARASITE_SANITIZE_TIMEOUT", "30")))
    max_concurrent_sanitizations: int = field(default_factory=lambda: int(os.getenv("PARASITE_MAX_CONCURRENT", "10")))

    # Logging settings
    log_level: str = field(default_factory=lambda: os.getenv("PARASITE_LOG_LEVEL", "INFO"))
    log_structured: bool = field(
        default_factory=lambda: os.getenv("PARASITE_LOG_STRUCTURED", "1").lower() in ("1", "true", "yes")
    )

    # Metrics settings
    metrics_enabled: bool = field(
        default_factory=lambda: os.getenv("PARASITE_METRICS", "1").lower() in ("1", "true", "yes")
    )
    metrics_prefix: str = field(default_factory=lambda: os.getenv("PARASITE_METRICS_PREFIX", "parasite"))

    def __post_init__(self):
        """Initialize component configs if not provided."""
        if not self.components:
            # Auto-discover components from environment
            for component in ["websocket", "eventbus", "db", "circuit", "batch", "trace"]:
                self.components[component] = ComponentConfig.from_env(component)

    def is_component_enabled(self, component: str) -> bool:
        """Check if a component is enabled."""
        if self.disabled:
            return False
        if not self.enabled:
            return False

        comp_config = self.components.get(component)
        if not comp_config:
            return False

        return comp_config.enabled

    def get_component_mode(self, component: str) -> GuardMode:
        """Get effective mode for a component."""
        # Global override
        if self.global_mode:
            return self.global_mode

        comp_config = self.components.get(component)
        if not comp_config:
            return GuardMode.DISABLED

        return comp_config.mode

    def should_sanitize(self, component: str) -> bool:
        """Check if sanitization is enabled for a component."""
        mode = self.get_component_mode(component)
        if mode != GuardMode.FULL:
            return False

        comp_config = self.components.get(component)
        if not comp_config:
            return False

        return comp_config.sanitize

    def get_component_threshold(self, component: str, threshold: str, default: Any = None) -> Any:
        """Get a threshold value for a component."""
        comp_config = self.components.get(component)
        if not comp_config:
            return default

        return comp_config.thresholds.get(threshold, default)

    def enable_component(self, component: str, mode: GuardMode = GuardMode.DRY_RUN, sanitize: bool = False):
        """Enable a component programmatically."""
        if component not in self.components:
            self.components[component] = ComponentConfig()

        self.components[component].enabled = True
        self.components[component].mode = mode
        self.components[component].sanitize = sanitize

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary for logging/debugging."""
        return {
            "enabled": self.enabled,
            "disabled": self.disabled,
            "global_mode": self.global_mode.name if self.global_mode else None,
            "components": {
                name: {
                    "enabled": cfg.enabled,
                    "mode": cfg.mode.name,
                    "sanitize": cfg.sanitize,
                    "async_delay": cfg.async_delay_seconds,
                    "thresholds": cfg.thresholds,
                }
                for name, cfg in self.components.items()
            },
            "detection_timeout_ms": self.detection_timeout_ms,
            "sanitize_async": self.sanitize_async,
            "sanitize_timeout_seconds": self.sanitize_timeout_seconds,
            "max_concurrent_sanitizations": self.max_concurrent_sanitizations,
            # Anomaly detection thresholds
            "anomaly_z_threshold": self.anomaly_z_threshold,
            "anomaly_window_size": self.anomaly_window_size,
            "anomaly_adaptive_percentile": self.anomaly_adaptive_percentile,
            "rate_limit_window_seconds": self.rate_limit_window_seconds,
            "rate_limit_max_rate": self.rate_limit_max_rate,
            "rate_limit_z_threshold": self.rate_limit_z_threshold,
            # Response settings
            "parasite_response_status_code": self.parasite_response_status_code,
        }
