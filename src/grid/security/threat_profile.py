"""
GRID Threat Profile & Security Guardrails
==========================================

Centralized threat intelligence, detection thresholds, and security guardrails.
Based on comprehensive security analysis conducted 2026-02-05.

This module provides:
1. ThreatProfile - Current threat landscape configuration
2. SecurityGuardrails - Strengthened detection rules and thresholds
3. MitigationStrategies - Active defense mechanisms
4. PreventionFramework - Future-proof security patterns

Author: GRID Security Framework
Version: 2.0.0
Date: 2026-02-05
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import sys
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import IntEnum, StrEnum, auto
from pathlib import Path
from typing import Any, Callable, TypeVar

log = logging.getLogger("grid.security.threat_profile")

T = TypeVar("T")


# =============================================================================
# THREAT SEVERITY LEVELS
# =============================================================================


class ThreatSeverity(IntEnum):
    """Threat severity classification aligned with CVSS scoring."""

    CRITICAL = 10  # System compromise, data exfiltration, RCE
    HIGH = 8  # Privilege escalation, authentication bypass
    MEDIUM = 5  # Information disclosure, DoS potential
    LOW = 2  # Minor issues, defense-in-depth violations
    INFO = 0  # Informational, no immediate risk


class ThreatCategory(StrEnum):
    """Categories of security threats."""

    INJECTION = auto()  # SQL, Command, Code, Template injection
    XSS = auto()  # Cross-site scripting
    TRAVERSAL = auto()  # Path traversal, directory escape
    AUTHENTICATION = auto()  # Auth bypass, credential theft
    AUTHORIZATION = auto()  # Privilege escalation, IDOR
    DESERIALIZATION = auto()  # Insecure deserialization
    CRYPTOGRAPHIC = auto()  # Weak crypto, key exposure
    CONFIGURATION = auto()  # Misconfigurations, insecure defaults
    PARASITIC = auto()  # Parasitic code patterns, infinite loops
    SUPPLY_CHAIN = auto()  # Dependency attacks, package tampering
    RATE_ABUSE = auto()  # DDoS, brute force, resource exhaustion
    DATA_EXPOSURE = auto()  # PII leakage, secrets exposure


# =============================================================================
# THREAT PROFILE - Current Threat Landscape
# =============================================================================


@dataclass(frozen=True)
class ThreatIndicator:
    """Individual threat indicator with detection pattern."""

    name: str
    category: ThreatCategory
    severity: ThreatSeverity
    pattern: str  # Regex pattern for detection
    description: str
    mitre_attack_id: str | None = None  # MITRE ATT&CK mapping
    cwe_id: str | None = None  # CWE mapping
    action: str = "REJECT"  # REJECT, SANITIZE, LOG_ONLY, ALERT


@dataclass
class ThreatProfile:
    """
    Current threat landscape configuration.

    Aggregates all known threats, their indicators, and detection patterns.
    Updated based on security analysis from 2026-02-05.
    """

    # Profile metadata
    version: str = "2.0.0"
    last_updated: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    environment: str = field(default_factory=lambda: os.getenv("GRID_ENVIRONMENT", "development"))

    # Known threat indicators
    indicators: list[ThreatIndicator] = field(default_factory=list)

    # Active threat sources (IPs, user agents, etc.)
    active_threat_sources: set[str] = field(default_factory=set)

    # Threat statistics
    detections_by_category: dict[ThreatCategory, int] = field(default_factory=lambda: defaultdict(int))
    detections_by_severity: dict[ThreatSeverity, int] = field(default_factory=lambda: defaultdict(int))

    def __post_init__(self):
        """Initialize with default threat indicators if empty."""
        if not self.indicators:
            self.indicators = self._get_default_indicators()

    @staticmethod
    def _get_default_indicators() -> list[ThreatIndicator]:
        """Get comprehensive default threat indicators."""
        return [
            # === SQL Injection (4 patterns) ===
            ThreatIndicator(
                name="sql_keyword_sequence",
                category=ThreatCategory.INJECTION,
                severity=ThreatSeverity.CRITICAL,
                pattern=r"(?i)\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE)\b.*\b(FROM|INTO|TABLE|DATABASE)\b",
                description="SQL keyword sequences indicating injection attempt",
                mitre_attack_id="T1190",
                cwe_id="CWE-89",
                action="REJECT",
            ),
            ThreatIndicator(
                name="sql_boolean_injection",
                category=ThreatCategory.INJECTION,
                severity=ThreatSeverity.HIGH,
                pattern=r"(?i)\b(OR|AND)\b\s+[\'\"]?\d+[\'\"]?\s*=\s*[\'\"]?\d+[\'\"]?",
                description="Boolean-based SQL injection (1=1, 1=2)",
                mitre_attack_id="T1190",
                cwe_id="CWE-89",
                action="REJECT",
            ),
            ThreatIndicator(
                name="sql_comment_injection",
                category=ThreatCategory.INJECTION,
                severity=ThreatSeverity.MEDIUM,
                pattern=r"(--|#|/\*|\*/)",
                description="SQL comment sequences for query manipulation",
                mitre_attack_id="T1190",
                cwe_id="CWE-89",
                action="SANITIZE",
            ),
            ThreatIndicator(
                name="sql_stored_procedure",
                category=ThreatCategory.INJECTION,
                severity=ThreatSeverity.CRITICAL,
                pattern=r"(?i)\b(EXEC|EXECUTE|xp_|sp_)\b",
                description="Stored procedure execution attempt",
                mitre_attack_id="T1190",
                cwe_id="CWE-89",
                action="REJECT",
            ),
            # === XSS (5 patterns - enhanced) ===
            ThreatIndicator(
                name="xss_script_tag",
                category=ThreatCategory.XSS,
                severity=ThreatSeverity.CRITICAL,
                pattern=r"(?i)<script[^>]*>.*?</script>",
                description="Script tag injection",
                mitre_attack_id="T1059.007",
                cwe_id="CWE-79",
                action="REJECT",
            ),
            ThreatIndicator(
                name="xss_event_handler",
                category=ThreatCategory.XSS,
                severity=ThreatSeverity.HIGH,
                pattern=r"(?i)\bon\w+\s*=",
                description="Event handler injection (onclick, onerror, etc.)",
                mitre_attack_id="T1059.007",
                cwe_id="CWE-79",
                action="SANITIZE",
            ),
            ThreatIndicator(
                name="xss_javascript_protocol",
                category=ThreatCategory.XSS,
                severity=ThreatSeverity.CRITICAL,
                pattern=r"(?i)javascript\s*:",
                description="JavaScript protocol in URL",
                mitre_attack_id="T1059.007",
                cwe_id="CWE-79",
                action="REJECT",
            ),
            ThreatIndicator(
                name="xss_embedded_content",
                category=ThreatCategory.XSS,
                severity=ThreatSeverity.HIGH,
                pattern=r"(?i)<(iframe|object|embed|applet|form|input|button)",
                description="Embedded content tags for XSS/clickjacking",
                mitre_attack_id="T1059.007",
                cwe_id="CWE-79",
                action="REJECT",
            ),
            ThreatIndicator(
                name="xss_data_uri",
                category=ThreatCategory.XSS,
                severity=ThreatSeverity.HIGH,
                pattern=r"(?i)data\s*:\s*(text/html|application/javascript)",
                description="Data URI with executable content",
                mitre_attack_id="T1059.007",
                cwe_id="CWE-79",
                action="REJECT",
            ),
            # === Command Injection (4 patterns - enhanced) ===
            ThreatIndicator(
                name="command_shell_metachar",
                category=ThreatCategory.INJECTION,
                severity=ThreatSeverity.CRITICAL,
                pattern=r"[;&|`$]|\$\(|\$\{|\||&&",
                description="Shell metacharacters for command chaining",
                mitre_attack_id="T1059",
                cwe_id="CWE-78",
                action="REJECT",
            ),
            ThreatIndicator(
                name="command_dangerous_exec",
                category=ThreatCategory.INJECTION,
                severity=ThreatSeverity.HIGH,
                pattern=r"(?i)\b(cat|ls|rm|mv|cp|chmod|chown|wget|curl|nc|bash|sh|python|perl|ruby|php|node)\b\s+",
                description="Dangerous command execution attempt",
                mitre_attack_id="T1059",
                cwe_id="CWE-78",
                action="LOG_ONLY",
            ),
            ThreatIndicator(
                name="command_reverse_shell",
                category=ThreatCategory.INJECTION,
                severity=ThreatSeverity.CRITICAL,
                pattern=r"(?i)(nc\s+-[eln]+|bash\s+-i|/dev/tcp/|mkfifo|telnet.*\|)",
                description="Reverse shell pattern detection",
                mitre_attack_id="T1059",
                cwe_id="CWE-78",
                action="REJECT",
            ),
            ThreatIndicator(
                name="command_env_injection",
                category=ThreatCategory.INJECTION,
                severity=ThreatSeverity.HIGH,
                pattern=r"(?i)(LD_PRELOAD|LD_LIBRARY_PATH|PYTHONPATH|PATH)\s*=",
                description="Environment variable injection",
                mitre_attack_id="T1574",
                cwe_id="CWE-426",
                action="REJECT",
            ),
            # === Path Traversal (3 patterns - enhanced) ===
            ThreatIndicator(
                name="path_traversal_basic",
                category=ThreatCategory.TRAVERSAL,
                severity=ThreatSeverity.HIGH,
                pattern=r"(\.\./|\.\.\\|%2e%2e%2f|%2e%2e/|\.%2e/|%2e\.)",
                description="Directory traversal sequences",
                mitre_attack_id="T1083",
                cwe_id="CWE-22",
                action="REJECT",
            ),
            ThreatIndicator(
                name="path_traversal_absolute",
                category=ThreatCategory.TRAVERSAL,
                severity=ThreatSeverity.HIGH,
                pattern=r"(?i)^(/etc/|/var/|/tmp/|/proc/|/sys/|c:\\|c:/)",
                description="Absolute path to sensitive directories",
                mitre_attack_id="T1083",
                cwe_id="CWE-22",
                action="REJECT",
            ),
            ThreatIndicator(
                name="path_null_byte",
                category=ThreatCategory.TRAVERSAL,
                severity=ThreatSeverity.CRITICAL,
                pattern=r"%00|\x00",
                description="Null byte injection for path truncation",
                mitre_attack_id="T1083",
                cwe_id="CWE-626",
                action="REJECT",
            ),
            # === SSRF (2 patterns) ===
            ThreatIndicator(
                name="ssrf_internal_network",
                category=ThreatCategory.INJECTION,
                severity=ThreatSeverity.HIGH,
                pattern=r"(?i)(localhost|127\.0\.0\.1|0\.0\.0\.0|::1|169\.254\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+|192\.168\.\d+\.\d+)",
                description="Internal network address for SSRF",
                mitre_attack_id="T1090",
                cwe_id="CWE-918",
                action="LOG_ONLY",
            ),
            ThreatIndicator(
                name="ssrf_cloud_metadata",
                category=ThreatCategory.INJECTION,
                severity=ThreatSeverity.CRITICAL,
                pattern=r"(?i)(169\.254\.169\.254|metadata\.google\.internal|metadata\.azure\.com)",
                description="Cloud metadata endpoint SSRF",
                mitre_attack_id="T1552.005",
                cwe_id="CWE-918",
                action="REJECT",
            ),
            # === Template Injection (2 patterns) ===
            ThreatIndicator(
                name="template_injection_jinja",
                category=ThreatCategory.INJECTION,
                severity=ThreatSeverity.HIGH,
                pattern=r"\{\{.*\}\}|\{%.*%\}",
                description="Jinja2/Django template injection",
                mitre_attack_id="T1059",
                cwe_id="CWE-94",
                action="SANITIZE",
            ),
            ThreatIndicator(
                name="template_injection_expression",
                category=ThreatCategory.INJECTION,
                severity=ThreatSeverity.HIGH,
                pattern=r"\$\{.*\}|#\{.*\}",
                description="Expression language injection",
                mitre_attack_id="T1059",
                cwe_id="CWE-917",
                action="SANITIZE",
            ),
            # === Header Injection (2 patterns) ===
            ThreatIndicator(
                name="header_crlf_injection",
                category=ThreatCategory.INJECTION,
                severity=ThreatSeverity.MEDIUM,
                pattern=r"(\r\n|\r|\n)",
                description="CRLF injection for header manipulation",
                mitre_attack_id="T1071",
                cwe_id="CWE-93",
                action="SANITIZE",
            ),
            ThreatIndicator(
                name="header_host_injection",
                category=ThreatCategory.INJECTION,
                severity=ThreatSeverity.HIGH,
                pattern=r"(?i)(host|x-forwarded-host)\s*:\s*[^\s]+\s+(host|x-forwarded-host)",
                description="Host header injection",
                mitre_attack_id="T1071",
                cwe_id="CWE-644",
                action="REJECT",
            ),
            # === Deserialization (2 patterns) ===
            ThreatIndicator(
                name="deserialization_pickle",
                category=ThreatCategory.DESERIALIZATION,
                severity=ThreatSeverity.CRITICAL,
                pattern=r"(?i)(pickle\.loads?|cPickle\.loads?|_pickle\.loads?)",
                description="Python pickle deserialization (code execution risk)",
                mitre_attack_id="T1059.006",
                cwe_id="CWE-502",
                action="ALERT",
            ),
            ThreatIndicator(
                name="deserialization_yaml",
                category=ThreatCategory.DESERIALIZATION,
                severity=ThreatSeverity.HIGH,
                pattern=r"(?i)(yaml\.load\s*\([^)]*Loader\s*=\s*yaml\.(Unsafe|Full)Loader)",
                description="Unsafe YAML loading",
                mitre_attack_id="T1059.006",
                cwe_id="CWE-502",
                action="ALERT",
            ),
            # === Parasitic Code Patterns (5 patterns - NEW) ===
            ThreatIndicator(
                name="parasitic_function_name",
                category=ThreatCategory.PARASITIC,
                severity=ThreatSeverity.MEDIUM,
                pattern=r"(?i)(hook_|intercept_|monkey_patch_|inject_|proxy_|bypass_|override_|hide_|mask_)",
                description="Function names indicating parasitic behavior",
                mitre_attack_id="T1055",
                cwe_id="CWE-506",
                action="LOG_ONLY",
            ),
            ThreatIndicator(
                name="parasitic_eval_exec",
                category=ThreatCategory.PARASITIC,
                severity=ThreatSeverity.CRITICAL,
                pattern=r"(?i)\b(eval|exec|compile)\s*\(",
                description="Dynamic code execution",
                mitre_attack_id="T1059.006",
                cwe_id="CWE-95",
                action="ALERT",
            ),
            ThreatIndicator(
                name="parasitic_import_hook",
                category=ThreatCategory.PARASITIC,
                severity=ThreatSeverity.HIGH,
                pattern=r"(?i)(sys\.meta_path|importlib\.abc|__import__|imp\.load_module)",
                description="Import system manipulation",
                mitre_attack_id="T1574",
                cwe_id="CWE-426",
                action="LOG_ONLY",
            ),
            ThreatIndicator(
                name="parasitic_settrace",
                category=ThreatCategory.PARASITIC,
                severity=ThreatSeverity.HIGH,
                pattern=r"(?i)sys\.(settrace|setprofile|_getframe)",
                description="Python tracing/debugging manipulation",
                mitre_attack_id="T1055",
                cwe_id="CWE-506",
                action="LOG_ONLY",
            ),
            ThreatIndicator(
                name="parasitic_ctypes",
                category=ThreatCategory.PARASITIC,
                severity=ThreatSeverity.CRITICAL,
                pattern=r"(?i)(ctypes\.CDLL|ctypes\.windll|ctypes\.pythonapi)",
                description="Native code loading via ctypes",
                mitre_attack_id="T1055.001",
                cwe_id="CWE-829",
                action="ALERT",
            ),
            # === Rate Abuse Indicators ===
            ThreatIndicator(
                name="rate_abuse_user_agent",
                category=ThreatCategory.RATE_ABUSE,
                severity=ThreatSeverity.LOW,
                pattern=r"(?i)(bot|crawler|spider|scraper|scanner|fuzzer|nikto|sqlmap|nmap|burp|zap)",
                description="Suspicious automated tool user agent",
                mitre_attack_id="T1595",
                cwe_id="CWE-799",
                action="LOG_ONLY",
            ),
        ]

    def check_input(self, input_value: str) -> list[tuple[ThreatIndicator, re.Match]]:
        """Check input against all threat indicators."""
        matches = []
        for indicator in self.indicators:
            try:
                compiled = re.compile(indicator.pattern)
                match = compiled.search(input_value)
                if match:
                    matches.append((indicator, match))
                    self.detections_by_category[indicator.category] += 1
                    self.detections_by_severity[indicator.severity] += 1
            except re.error as e:
                log.warning("Invalid regex pattern for %s: %s", indicator.name, e)
        return matches

    def get_max_severity(self, matches: list[tuple[ThreatIndicator, re.Match]]) -> ThreatSeverity:
        """Get the maximum severity from a list of matches."""
        if not matches:
            return ThreatSeverity.INFO
        return max((m[0].severity for m in matches), key=lambda s: s.value)

    def to_dict(self) -> dict[str, Any]:
        """Serialize threat profile to dictionary."""
        return {
            "version": self.version,
            "last_updated": self.last_updated.isoformat(),
            "environment": self.environment,
            "indicator_count": len(self.indicators),
            "active_threat_sources": list(self.active_threat_sources),
            "detections_by_category": {k.name: v for k, v in self.detections_by_category.items()},
            "detections_by_severity": {k.name: v for k, v in self.detections_by_severity.items()},
        }


# =============================================================================
# SECURITY GUARDRAILS - Strengthened Detection Rules
# =============================================================================


@dataclass
class DetectionThreshold:
    """Detection threshold configuration with adaptive capabilities."""

    name: str
    base_value: float
    min_value: float
    max_value: float
    adaptive: bool = True
    decay_rate: float = 0.95  # Decay factor per time period
    surge_multiplier: float = 1.5  # Multiplier during high threat periods

    _current_value: float = field(init=False, default=0.0)
    _last_adjustment: datetime = field(init=False, default_factory=lambda: datetime.now(tz=UTC))

    def __post_init__(self):
        self._current_value = self.base_value

    @property
    def value(self) -> float:
        """Get current threshold value."""
        return self._current_value

    def adjust(self, threat_level: float) -> None:
        """Adjust threshold based on current threat level (0.0 to 1.0)."""
        if not self.adaptive:
            return

        # Higher threat = lower threshold (more sensitive)
        adjusted = self.base_value * (1 - (threat_level * (1 - self.min_value / self.base_value)))
        self._current_value = max(self.min_value, min(self.max_value, adjusted))
        self._last_adjustment = datetime.now(tz=UTC)

    def surge(self) -> None:
        """Temporarily increase sensitivity during high threat periods."""
        self._current_value = max(self.min_value, self._current_value / self.surge_multiplier)

    def reset(self) -> None:
        """Reset to base value."""
        self._current_value = self.base_value


@dataclass
class SecurityGuardrails:
    """
    Strengthened detection rules and thresholds.

    Provides adaptive thresholds that adjust based on threat levels.
    """

    # === Rate Limiting Thresholds ===
    rate_limit_per_second: DetectionThreshold = field(
        default_factory=lambda: DetectionThreshold(
            name="rate_limit_per_second",
            base_value=10.0,  # Tightened from previous
            min_value=1.0,
            max_value=100.0,
        )
    )

    rate_limit_burst: DetectionThreshold = field(
        default_factory=lambda: DetectionThreshold(
            name="rate_limit_burst",
            base_value=5.0,  # Tightened from previous
            min_value=1.0,
            max_value=20.0,
        )
    )

    # === Parasite Detection Thresholds ===
    frequency_detection_threshold: DetectionThreshold = field(
        default_factory=lambda: DetectionThreshold(
            name="frequency_detection",
            base_value=5.0,  # Requests in window to trigger
            min_value=2.0,  # More sensitive during threats
            max_value=20.0,
        )
    )

    frequency_window_seconds: DetectionThreshold = field(
        default_factory=lambda: DetectionThreshold(
            name="frequency_window",
            base_value=60.0,
            min_value=10.0,
            max_value=300.0,
            adaptive=False,  # Keep window fixed
        )
    )

    # === Anomaly Detection Thresholds ===
    z_score_threshold: DetectionThreshold = field(
        default_factory=lambda: DetectionThreshold(
            name="z_score_threshold",
            base_value=3.5,  # Standard Z-score threshold
            min_value=2.0,  # More sensitive during threats
            max_value=5.0,
        )
    )

    anomaly_confidence_threshold: DetectionThreshold = field(
        default_factory=lambda: DetectionThreshold(
            name="anomaly_confidence",
            base_value=0.95,  # 95% confidence required
            min_value=0.80,
            max_value=0.99,
        )
    )

    # === Input Validation Thresholds ===
    max_input_length: DetectionThreshold = field(
        default_factory=lambda: DetectionThreshold(
            name="max_input_length",
            base_value=1_000_000.0,  # 1MB
            min_value=10_000.0,  # 10KB during threats
            max_value=10_000_000.0,  # 10MB max
        )
    )

    max_json_depth: DetectionThreshold = field(
        default_factory=lambda: DetectionThreshold(
            name="max_json_depth",
            base_value=10.0,
            min_value=3.0,
            max_value=20.0,
        )
    )

    max_request_size_mb: DetectionThreshold = field(
        default_factory=lambda: DetectionThreshold(
            name="max_request_size_mb",
            base_value=10.0,
            min_value=1.0,
            max_value=50.0,
        )
    )

    # === Timeout Thresholds ===
    request_timeout_seconds: DetectionThreshold = field(
        default_factory=lambda: DetectionThreshold(
            name="request_timeout",
            base_value=30.0,
            min_value=5.0,
            max_value=300.0,
            adaptive=False,
        )
    )

    detection_timeout_ms: DetectionThreshold = field(
        default_factory=lambda: DetectionThreshold(
            name="detection_timeout_ms",
            base_value=100.0,
            min_value=10.0,
            max_value=500.0,
            adaptive=False,
        )
    )

    # === Alert Thresholds ===
    alert_escalation_count: DetectionThreshold = field(
        default_factory=lambda: DetectionThreshold(
            name="alert_escalation_count",
            base_value=3.0,  # Alerts before escalation
            min_value=1.0,  # Immediate escalation during threats
            max_value=10.0,
        )
    )

    alert_window_seconds: DetectionThreshold = field(
        default_factory=lambda: DetectionThreshold(
            name="alert_window",
            base_value=300.0,  # 5 minutes
            min_value=60.0,
            max_value=3600.0,
            adaptive=False,
        )
    )

    # === Circuit Breaker Thresholds ===
    circuit_breaker_failure_threshold: DetectionThreshold = field(
        default_factory=lambda: DetectionThreshold(
            name="circuit_breaker_failures",
            base_value=5.0,
            min_value=2.0,
            max_value=20.0,
        )
    )

    circuit_breaker_recovery_timeout: DetectionThreshold = field(
        default_factory=lambda: DetectionThreshold(
            name="circuit_breaker_recovery",
            base_value=30.0,
            min_value=10.0,
            max_value=120.0,
            adaptive=False,
        )
    )

    # Current threat level (0.0 = normal, 1.0 = critical)
    _threat_level: float = field(init=False, default=0.0)
    _threat_level_lock: threading.Lock = field(init=False, default_factory=threading.Lock)

    def set_threat_level(self, level: float) -> None:
        """Set current threat level and adjust all thresholds."""
        with self._threat_level_lock:
            self._threat_level = max(0.0, min(1.0, level))

            # Adjust all adaptive thresholds
            for attr_name in dir(self):
                attr = getattr(self, attr_name)
                if isinstance(attr, DetectionThreshold) and attr.adaptive:
                    attr.adjust(self._threat_level)

    def surge_all(self) -> None:
        """Surge all thresholds for high threat response."""
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, DetectionThreshold):
                attr.surge()

    def reset_all(self) -> None:
        """Reset all thresholds to base values."""
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, DetectionThreshold):
                attr.reset()

    @property
    def threat_level(self) -> float:
        """Get current threat level."""
        return self._threat_level

    def to_dict(self) -> dict[str, Any]:
        """Serialize guardrails to dictionary."""
        result = {"threat_level": self._threat_level, "thresholds": {}}
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, DetectionThreshold):
                result["thresholds"][attr.name] = {
                    "base": attr.base_value,
                    "current": attr.value,
                    "min": attr.min_value,
                    "max": attr.max_value,
                    "adaptive": attr.adaptive,
                }
        return result


# =============================================================================
# MITIGATION STRATEGIES - Active Defense Mechanisms
# =============================================================================


class MitigationAction(StrEnum):
    """Actions that can be taken to mitigate threats."""

    BLOCK = auto()  # Block the request/connection
    THROTTLE = auto()  # Apply rate limiting
    QUARANTINE = auto()  # Isolate for analysis
    SANITIZE = auto()  # Remove malicious content
    CHALLENGE = auto()  # Require CAPTCHA/verification
    LOG = auto()  # Log for monitoring
    ALERT = auto()  # Send security alert
    ESCALATE = auto()  # Escalate to security team


@dataclass
class MitigationRule:
    """A rule defining how to mitigate a specific threat."""

    name: str
    trigger_category: ThreatCategory
    trigger_severity: ThreatSeverity
    actions: list[MitigationAction]
    cooldown_seconds: int = 60
    max_triggers_per_window: int = 3
    auto_block_threshold: int = 5

    _trigger_count: int = field(init=False, default=0)
    _last_trigger: datetime | None = field(init=False, default=None)
    _blocked_sources: set[str] = field(init=False, default_factory=set)

    def should_trigger(self, category: ThreatCategory, severity: ThreatSeverity) -> bool:
        """Check if this rule should trigger for the given threat."""
        return category == self.trigger_category and severity.value >= self.trigger_severity.value

    def trigger(self, source: str) -> list[MitigationAction]:
        """Trigger this rule and return actions to take."""
        now = datetime.now(tz=UTC)

        # Check cooldown
        if self._last_trigger:
            elapsed = (now - self._last_trigger).total_seconds()
            if elapsed < self.cooldown_seconds:
                return []

        self._trigger_count += 1
        self._last_trigger = now

        # Check auto-block threshold
        if self._trigger_count >= self.auto_block_threshold:
            self._blocked_sources.add(source)
            return [MitigationAction.BLOCK, MitigationAction.ALERT]

        return self.actions

    def is_blocked(self, source: str) -> bool:
        """Check if a source is blocked by this rule."""
        return source in self._blocked_sources

    def reset(self) -> None:
        """Reset rule state."""
        self._trigger_count = 0
        self._last_trigger = None
        self._blocked_sources.clear()


@dataclass
class MitigationStrategies:
    """
    Active defense mechanisms for threat mitigation.

    Provides automated response to detected threats.
    """

    rules: list[MitigationRule] = field(default_factory=list)
    _global_blocked: set[str] = field(init=False, default_factory=set)
    _quarantine_queue: list[tuple[str, datetime, dict]] = field(init=False, default_factory=list)

    def __post_init__(self):
        """Initialize default mitigation rules."""
        if not self.rules:
            self.rules = self._get_default_rules()

    @staticmethod
    def _get_default_rules() -> list[MitigationRule]:
        """Get default mitigation rules."""
        return [
            # Critical injection - immediate block
            MitigationRule(
                name="critical_injection_block",
                trigger_category=ThreatCategory.INJECTION,
                trigger_severity=ThreatSeverity.CRITICAL,
                actions=[MitigationAction.BLOCK, MitigationAction.ALERT, MitigationAction.LOG],
                cooldown_seconds=0,  # No cooldown for critical
                auto_block_threshold=1,  # Immediate block
            ),
            # High severity injection - throttle then block
            MitigationRule(
                name="high_injection_throttle",
                trigger_category=ThreatCategory.INJECTION,
                trigger_severity=ThreatSeverity.HIGH,
                actions=[MitigationAction.THROTTLE, MitigationAction.LOG],
                cooldown_seconds=30,
                auto_block_threshold=3,
            ),
            # XSS - sanitize and log
            MitigationRule(
                name="xss_sanitize",
                trigger_category=ThreatCategory.XSS,
                trigger_severity=ThreatSeverity.HIGH,
                actions=[MitigationAction.SANITIZE, MitigationAction.LOG],
                cooldown_seconds=10,
                auto_block_threshold=5,
            ),
            # Path traversal - immediate block
            MitigationRule(
                name="traversal_block",
                trigger_category=ThreatCategory.TRAVERSAL,
                trigger_severity=ThreatSeverity.HIGH,
                actions=[MitigationAction.BLOCK, MitigationAction.LOG],
                cooldown_seconds=0,
                auto_block_threshold=1,
            ),
            # Parasitic code - quarantine for analysis
            MitigationRule(
                name="parasitic_quarantine",
                trigger_category=ThreatCategory.PARASITIC,
                trigger_severity=ThreatSeverity.HIGH,
                actions=[MitigationAction.QUARANTINE, MitigationAction.ALERT],
                cooldown_seconds=60,
                auto_block_threshold=3,
            ),
            # Rate abuse - throttle
            MitigationRule(
                name="rate_abuse_throttle",
                trigger_category=ThreatCategory.RATE_ABUSE,
                trigger_severity=ThreatSeverity.LOW,
                actions=[MitigationAction.THROTTLE, MitigationAction.LOG],
                cooldown_seconds=60,
                auto_block_threshold=10,
            ),
            # Deserialization - alert and escalate
            MitigationRule(
                name="deserialization_escalate",
                trigger_category=ThreatCategory.DESERIALIZATION,
                trigger_severity=ThreatSeverity.CRITICAL,
                actions=[MitigationAction.BLOCK, MitigationAction.ESCALATE, MitigationAction.ALERT],
                cooldown_seconds=0,
                auto_block_threshold=1,
            ),
        ]

    def evaluate(self, category: ThreatCategory, severity: ThreatSeverity, source: str) -> list[MitigationAction]:
        """Evaluate threat and return mitigation actions."""
        # Check global block list
        if source in self._global_blocked:
            return [MitigationAction.BLOCK]

        actions = []
        for rule in self.rules:
            if rule.is_blocked(source):
                return [MitigationAction.BLOCK]

            if rule.should_trigger(category, severity):
                actions.extend(rule.trigger(source))

        return list(set(actions))  # Deduplicate

    def global_block(self, source: str) -> None:
        """Add source to global block list."""
        self._global_blocked.add(source)

    def quarantine(self, source: str, metadata: dict) -> None:
        """Add to quarantine queue for analysis."""
        self._quarantine_queue.append((source, datetime.now(tz=UTC), metadata))

    def get_quarantine_queue(self) -> list[tuple[str, datetime, dict]]:
        """Get current quarantine queue."""
        return self._quarantine_queue.copy()

    def clear_quarantine(self) -> None:
        """Clear quarantine queue."""
        self._quarantine_queue.clear()

    def reset_all(self) -> None:
        """Reset all mitigation state."""
        self._global_blocked.clear()
        self._quarantine_queue.clear()
        for rule in self.rules:
            rule.reset()


# =============================================================================
# PREVENTION FRAMEWORK - Future-Proof Security Patterns
# =============================================================================


@dataclass
class SecurityAssertion:
    """A security assertion that must hold true."""

    name: str
    description: str
    check: Callable[[], bool]
    severity: ThreatSeverity
    auto_remediate: bool = False
    remediation: Callable[[], None] | None = None


class PreventionFramework:
    """
    Future-proof security patterns and assertions.

    Provides continuous security validation and hardening.
    """

    def __init__(self):
        self._assertions: list[SecurityAssertion] = []
        self._baseline_hashes: dict[str, str] = {}
        self._module_baseline: set[str] = set()
        self._last_validation: datetime | None = None
        self._validation_interval = timedelta(minutes=5)
        self._lock = threading.Lock()

        # Initialize with default assertions
        self._setup_default_assertions()

    def _setup_default_assertions(self) -> None:
        """Set up default security assertions."""
        self._assertions = [
            SecurityAssertion(
                name="no_debug_mode_production",
                description="Debug mode must be disabled in production",
                check=lambda: (
                    os.getenv("GRID_ENVIRONMENT") != "production"
                    or os.getenv("DEBUG", "0").lower() not in ("1", "true")
                ),
                severity=ThreatSeverity.HIGH,
            ),
            SecurityAssertion(
                name="https_required_production",
                description="HTTPS must be required in production",
                check=lambda: (
                    os.getenv("GRID_ENVIRONMENT") != "production"
                    or os.getenv("REQUIRE_HTTPS", "1").lower() in ("1", "true")
                ),
                severity=ThreatSeverity.HIGH,
            ),
            SecurityAssertion(
                name="secrets_not_in_env",
                description="Secrets should use secrets manager, not environment",
                check=lambda: (
                    not any(
                        k.endswith(("_KEY", "_SECRET", "_TOKEN", "_PASSWORD")) and len(v) > 10
                        for k, v in os.environ.items()
                        if not k.startswith("GRID_")
                    )
                ),
                severity=ThreatSeverity.MEDIUM,
            ),
            SecurityAssertion(
                name="parasite_guard_enabled",
                description="Parasite guard must be enabled",
                check=lambda: os.getenv("PARASITE_GUARD", "1").lower() in ("1", "true"),
                severity=ThreatSeverity.MEDIUM,
            ),
            SecurityAssertion(
                name="no_writable_system_paths",
                description="System paths should not be writable",
                check=self._check_writable_system_paths,
                severity=ThreatSeverity.MEDIUM,
            ),
        ]

    @staticmethod
    def _check_writable_system_paths() -> bool:
        """Check that system paths are not writable."""
        system_paths = [
            "/usr",
            "/bin",
            "/sbin",
            "/lib",
        ]
        if sys.platform == "win32":
            system_paths.extend(
                [
                    os.environ.get("SystemRoot", "C:\\Windows"),
                    os.environ.get("ProgramFiles", "C:\\Program Files"),
                    os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
                ]
            )
        for path in system_paths:
            if os.path.exists(path) and os.access(path, os.W_OK):
                return False
        return True

    def add_assertion(self, assertion: SecurityAssertion) -> None:
        """Add a security assertion."""
        with self._lock:
            self._assertions.append(assertion)

    def capture_baseline(self) -> None:
        """Capture security baseline for drift detection."""
        with self._lock:
            # Capture module baseline
            self._module_baseline = set(sys.modules.keys())

            # Capture critical file hashes
            critical_files = [
                Path(__file__),  # This module
                Path(__file__).parent / "__init__.py",
                Path(__file__).parent / "parasite_guard.py",
            ]

            for file_path in critical_files:
                if file_path.exists():
                    content = file_path.read_bytes()
                    self._baseline_hashes[str(file_path)] = hashlib.sha256(content).hexdigest()

            log.info(
                "Security baseline captured: %d modules, %d file hashes",
                len(self._module_baseline),
                len(self._baseline_hashes),
            )

    def detect_drift(self) -> list[dict[str, Any]]:
        """Detect drift from security baseline."""
        drift = []

        with self._lock:
            # Check for new modules
            current_modules = set(sys.modules.keys())
            new_modules = current_modules - self._module_baseline

            # Filter out expected dynamic modules
            suspicious_modules = [
                m
                for m in new_modules
                if not any(m.startswith(prefix) for prefix in ("importlib", "_frozen", "encodings", "__pycache__"))
            ]

            if suspicious_modules:
                drift.append(
                    {
                        "type": "new_modules",
                        "severity": ThreatSeverity.MEDIUM.name,
                        "details": suspicious_modules[:10],  # Limit to first 10
                        "count": len(suspicious_modules),
                    }
                )

            # Check file integrity
            for file_path, expected_hash in self._baseline_hashes.items():
                path = Path(file_path)
                if path.exists():
                    current_hash = hashlib.sha256(path.read_bytes()).hexdigest()
                    if current_hash != expected_hash:
                        drift.append(
                            {
                                "type": "file_modified",
                                "severity": ThreatSeverity.HIGH.name,
                                "file": file_path,
                                "expected": expected_hash[:16] + "...",
                                "actual": current_hash[:16] + "...",
                            }
                        )
                else:
                    drift.append(
                        {
                            "type": "file_missing",
                            "severity": ThreatSeverity.CRITICAL.name,
                            "file": file_path,
                        }
                    )

        return drift

    def validate_assertions(self) -> list[dict[str, Any]]:
        """Validate all security assertions."""
        violations = []

        with self._lock:
            for assertion in self._assertions:
                try:
                    if not assertion.check():
                        violation = {
                            "assertion": assertion.name,
                            "description": assertion.description,
                            "severity": assertion.severity.name,
                            "auto_remediate": assertion.auto_remediate,
                        }

                        # Attempt auto-remediation
                        if assertion.auto_remediate and assertion.remediation:
                            try:
                                assertion.remediation()
                                violation["remediated"] = True
                            except Exception as e:
                                violation["remediation_error"] = str(e)
                                violation["remediated"] = False

                        violations.append(violation)
                except Exception as e:
                    violations.append(
                        {
                            "assertion": assertion.name,
                            "error": str(e),
                            "severity": ThreatSeverity.LOW.name,
                        }
                    )

            self._last_validation = datetime.now(tz=UTC)

        return violations

    def run_continuous_validation(self) -> dict[str, Any]:
        """Run continuous validation if interval has passed."""
        now = datetime.now(tz=UTC)

        if self._last_validation:
            elapsed = now - self._last_validation
            if elapsed < self._validation_interval:
                return {"skipped": True, "reason": "validation_interval_not_reached"}

        # Run validation
        assertion_violations = self.validate_assertions()
        drift = self.detect_drift()

        return {
            "timestamp": now.isoformat(),
            "assertion_violations": assertion_violations,
            "drift_detections": drift,
            "status": "healthy" if not (assertion_violations or drift) else "violations_detected",
        }

    def harden(self) -> dict[str, Any]:
        """Apply hardening measures."""
        applied = []

        # Disable debug mode if in production
        if os.getenv("GRID_ENVIRONMENT") == "production":
            if os.getenv("DEBUG", "0").lower() in ("1", "true"):
                os.environ["DEBUG"] = "0"
                applied.append("disabled_debug_mode")

        # Enable parasite guard if disabled
        if os.getenv("PARASITE_GUARD", "1").lower() not in ("1", "true"):
            os.environ["PARASITE_GUARD"] = "1"
            applied.append("enabled_parasite_guard")

        # Set secure defaults
        secure_defaults = {
            "PARASITE_DETECT_THRESHOLD": "5",
            "PARASITE_GUARD_MODE": "DETECT",
            "PG_PRUNE_ENABLED": "0",  # Keep pruning disabled for safety
        }

        for key, value in secure_defaults.items():
            if key not in os.environ:
                os.environ[key] = value
                applied.append(f"set_default_{key.lower()}")

        return {
            "hardening_applied": applied,
            "timestamp": datetime.now(tz=UTC).isoformat(),
        }


# =============================================================================
# SINGLETON INSTANCES
# =============================================================================

# Global threat profile instance
_threat_profile: ThreatProfile | None = None
_threat_profile_lock = threading.Lock()


def get_threat_profile() -> ThreatProfile:
    """Get the global threat profile instance."""
    global _threat_profile
    with _threat_profile_lock:
        if _threat_profile is None:
            _threat_profile = ThreatProfile()
        return _threat_profile


# Global security guardrails instance
_guardrails: SecurityGuardrails | None = None
_guardrails_lock = threading.Lock()


def get_guardrails() -> SecurityGuardrails:
    """Get the global security guardrails instance."""
    global _guardrails
    with _guardrails_lock:
        if _guardrails is None:
            _guardrails = SecurityGuardrails()
        return _guardrails


# Global mitigation strategies instance
_mitigation: MitigationStrategies | None = None
_mitigation_lock = threading.Lock()


def get_mitigation_strategies() -> MitigationStrategies:
    """Get the global mitigation strategies instance."""
    global _mitigation
    with _mitigation_lock:
        if _mitigation is None:
            _mitigation = MitigationStrategies()
        return _mitigation


# Global prevention framework instance
_prevention: PreventionFramework | None = None
_prevention_lock = threading.Lock()


def get_prevention_framework() -> PreventionFramework:
    """Get the global prevention framework instance."""
    global _prevention
    with _prevention_lock:
        if _prevention is None:
            _prevention = PreventionFramework()
        return _prevention


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def check_threat(input_value: str, source: str = "unknown") -> dict[str, Any]:
    """
    Convenience function to check input for threats and get mitigation actions.

    Returns:
        dict with keys: detected, severity, indicators, actions
    """
    profile = get_threat_profile()
    mitigation = get_mitigation_strategies()

    matches = profile.check_input(input_value)

    if not matches:
        return {
            "detected": False,
            "severity": ThreatSeverity.INFO.name,
            "indicators": [],
            "actions": [],
        }

    max_severity = profile.get_max_severity(matches)
    max_category = matches[0][0].category  # Use first match category

    actions = mitigation.evaluate(max_category, max_severity, source)

    return {
        "detected": True,
        "severity": max_severity.name,
        "indicators": [
            {
                "name": m[0].name,
                "category": m[0].category.name,
                "severity": m[0].severity.name,
                "matched": m[1].group(),
            }
            for m in matches
        ],
        "actions": [a.name for a in actions],
    }


def get_security_status() -> dict[str, Any]:
    """Get comprehensive security status."""
    profile = get_threat_profile()
    guardrails = get_guardrails()
    prevention = get_prevention_framework()

    return {
        "timestamp": datetime.now(tz=UTC).isoformat(),
        "threat_profile": profile.to_dict(),
        "guardrails": guardrails.to_dict(),
        "validation": prevention.run_continuous_validation(),
    }


def initialize_security() -> None:
    """Initialize all security components."""
    log.info("Initializing GRID security components...")

    # Initialize all singletons
    profile = get_threat_profile()
    guardrails = get_guardrails()
    mitigation = get_mitigation_strategies()
    prevention = get_prevention_framework()

    # Capture baseline
    prevention.capture_baseline()

    # Apply initial hardening
    hardening = prevention.harden()

    log.info(
        "Security initialized: %d threat indicators, %d guardrails, %d mitigation rules",
        len(profile.indicators),
        len([a for a in dir(guardrails) if isinstance(getattr(guardrails, a), DetectionThreshold)]),
        len(mitigation.rules),
    )

    if hardening["hardening_applied"]:
        log.info("Applied hardening: %s", ", ".join(hardening["hardening_applied"]))
