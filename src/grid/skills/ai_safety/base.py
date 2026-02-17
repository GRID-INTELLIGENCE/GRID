"""AI Safety Skills Base Module.

Defines shared types and base classes for AI safety skills following
the Wellness Studio AI SAFETY framework patterns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Protocol


class ThreatLevel(str, Enum):
    """Threat severity levels."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SafetyCategory(str, Enum):
    """Safety evaluation categories."""

    HARMFUL_CONTENT = "harmful_content"
    PRIVACY_VIOLATION = "privacy_violation"
    MANIPULATION = "manipulation"
    HARASSMENT = "harassment"
    MISINFORMATION = "misinformation"
    CULTURAL_SENSITIVITY = "cultural_sensitivity"
    MENTAL_HEALTH_RISK = "mental_health_risk"


class ActionType(str, Enum):
    """Remediation action types."""

    BLOCK = "block"
    ESCALATE = "escalate"
    REVIEW = "review"
    LOG = "log"
    ALLOW = "allow"


@dataclass
class SafetyViolation:
    """Individual safety violation detected."""

    category: SafetyCategory
    severity: ThreatLevel
    confidence: float
    description: str
    evidence: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    provider: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "description": self.description,
            "evidence": self.evidence,
            "timestamp": self.timestamp.isoformat(),
            "provider": self.provider,
        }


@dataclass
class SafetyReport:
    """Comprehensive safety evaluation report."""

    overall_score: float
    threat_level: ThreatLevel
    violations: list[SafetyViolation] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0
    content_hash: str = ""

    @property
    def is_safe(self) -> bool:
        """Check if content is safe (no critical violations)."""
        return self.threat_level in [ThreatLevel.NONE, ThreatLevel.LOW]

    @property
    def requires_review(self) -> bool:
        """Check if content requires human review."""
        return self.threat_level in [ThreatLevel.MEDIUM, ThreatLevel.HIGH]

    @property
    def should_block(self) -> bool:
        """Check if content should be blocked immediately."""
        return self.threat_level == ThreatLevel.CRITICAL

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "overall_score": self.overall_score,
            "threat_level": self.threat_level.value,
            "violations": [v.to_dict() for v in self.violations],
            "metadata": self.metadata,
            "processing_time": self.processing_time,
            "content_hash": self.content_hash,
            "is_safe": self.is_safe,
            "requires_review": self.requires_review,
            "should_block": self.should_block,
            "timestamp": datetime.now(UTC).isoformat(),
        }


@dataclass
class ActionResult:
    """Result of executing a safety action."""

    action: ActionType
    success: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "action": self.action.value,
            "success": self.success,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


class AISafetySkill(Protocol):
    """Protocol defining AI safety skill interface.

    Extends base Skill with AI safety specific attributes.
    """

    id: str
    name: str
    description: str
    version: str
    provider: str
    action_type: str
    severity_threshold: ThreatLevel

    def run(self, args: dict[str, Any]) -> dict[str, Any]:
        """Execute the safety skill."""
        ...


def calculate_safety_score(violations: list[SafetyViolation]) -> float:
    """Calculate overall safety score from violations.

    Args:
        violations: List of detected violations.

    Returns:
        Safety score between 0.0 and 1.0 (higher is safer).
    """
    if not violations:
        return 1.0

    severity_weights = {
        ThreatLevel.NONE: 0.0,
        ThreatLevel.LOW: 0.1,
        ThreatLevel.MEDIUM: 0.3,
        ThreatLevel.HIGH: 0.6,
        ThreatLevel.CRITICAL: 1.0,
    }

    total_weight = 0.0
    for violation in violations:
        weight = severity_weights[violation.severity] * violation.confidence
        total_weight += weight

    return max(0.0, 1.0 - total_weight)


def determine_threat_level(
    safety_score: float,
    violations: list[SafetyViolation],
    thresholds: dict[str, float] | None = None,
) -> ThreatLevel:
    """Determine overall threat level.

    Args:
        safety_score: Calculated safety score.
        violations: List of detected violations.
        thresholds: Optional custom thresholds.

    Returns:
        Overall threat level.
    """
    default_thresholds = {"safe": 0.8, "warning": 0.6, "danger": 0.4}
    thresholds = thresholds or default_thresholds

    # Check for critical violations first
    if any(v.severity == ThreatLevel.CRITICAL for v in violations):
        return ThreatLevel.CRITICAL

    # Check for multiple high-severity violations
    high_severity_count = sum(1 for v in violations if v.severity == ThreatLevel.HIGH)
    if high_severity_count >= 2:
        return ThreatLevel.CRITICAL
    elif high_severity_count >= 1:
        return ThreatLevel.HIGH

    # Use safety score thresholds
    if safety_score >= thresholds["safe"]:
        return ThreatLevel.NONE
    elif safety_score >= thresholds["warning"]:
        return ThreatLevel.LOW
    elif safety_score >= thresholds["danger"]:
        return ThreatLevel.MEDIUM
    else:
        return ThreatLevel.HIGH
