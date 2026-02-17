"""Data penalty schema for accountability tracking.

Defines penalty tiers, violation rules, and decay functions for tracking
data-related penalties that impact endpoint delivery accountability scores.

Penalty Tiers:
- Critical (20-50 pts): Severe impact on system integrity (data corruption, security breach)
- High (10-19 pts): Major impact on performance (SLA violation >5%, data inconsistency)
- Medium (5-9 pts): Noticeable impact (latency spike, partial data loss)
- Low (1-4 pts): Minor impact (warnings, retries)

Scoring Impact:
    Accountability Score = 100 - Total_Penalty_Points (capped at 0-100)

Automatic Actions by Band:
    - Score > 90: Normal operation
    - 75-90: Alert team
    - 50-74: Throttle non-critical operations
    - <50: Enter degraded mode
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum, StrEnum
from typing import Any, Callable


class PenaltySeverity(StrEnum):
    """Penalty severity levels with associated point ranges."""

    CRITICAL = "critical"  # 20-50 points
    HIGH = "high"  # 10-19 points
    MEDIUM = "medium"  # 5-9 points
    LOW = "low"  # 1-4 points


# Point ranges for each severity tier
SEVERITY_RANGES: dict[PenaltySeverity, tuple[int, int]] = {
    PenaltySeverity.CRITICAL: (20, 50),
    PenaltySeverity.HIGH: (10, 19),
    PenaltySeverity.MEDIUM: (5, 9),
    PenaltySeverity.LOW: (1, 4),
}


@dataclass
class DataPenaltySchema:
    """Schema for tracking data-related penalties.

    Attributes:
        violation_type: Type of violation (e.g., 'data_corruption', 'sla_violation')
        severity: Penalty severity level
        penalty_points: Base penalty points for this violation
        description: Human-readable description of the violation
        component: System component where violation occurred (e.g., 'rag/search')
        timestamp: When the violation was recorded
        metadata: Additional context about the violation
    """

    violation_type: str
    severity: PenaltySeverity
    penalty_points: float
    description: str
    component: str = "default"
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_metadata(self, **kwargs: Any) -> None:
        """Add additional metadata to the penalty.

        Args:
            **kwargs: Key-value pairs to add to metadata.
        """
        self.metadata.update(kwargs)

    def to_dict(self) -> dict[str, Any]:
        """Convert penalty to dictionary for serialization.

        Returns:
            Dictionary representation of the penalty.
        """
        return {
            "violation_type": self.violation_type,
            "severity": self.severity.value,
            "penalty_points": self.penalty_points,
            "description": self.description,
            "component": self.component,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DataPenaltySchema:
        """Create a penalty from dictionary.

        Args:
            data: Dictionary with penalty fields.

        Returns:
            DataPenaltySchema instance.
        """
        severity = PenaltySeverity(data["severity"]) if isinstance(data["severity"], str) else data["severity"]
        timestamp = (
            datetime.fromisoformat(data["timestamp"]) if isinstance(data["timestamp"], str) else data["timestamp"]
        )
        return cls(
            violation_type=data["violation_type"],
            severity=severity,
            penalty_points=data["penalty_points"],
            description=data["description"],
            component=data.get("component", "default"),
            timestamp=timestamp,
            metadata=data.get("metadata", {}),
        )


@dataclass
class PenaltyRule:
    """Definition of a penalty rule for automatic penalty creation.

    Attributes:
        violation_type: Unique identifier for this violation type
        severity: Default severity level
        base_points: Base penalty points
        description: Template description
        dynamic_calculator: Optional function to calculate dynamic points
            based on context (e.g., SLA violation duration)
        remediation: Suggested action to resolve the violation
    """

    violation_type: str
    severity: PenaltySeverity
    base_points: float
    description: str
    dynamic_calculator: Callable[[dict[str, Any]], float] | None = None
    remediation: str | None = None

    def calculate_points(self, context: dict[str, Any] | None = None) -> float:
        """Calculate penalty points, optionally using dynamic calculator.

        Args:
            context: Optional context for dynamic calculation.

        Returns:
            Calculated penalty points.
        """
        if self.dynamic_calculator and context:
            return self.dynamic_calculator(context)
        return self.base_points

    def create_penalty(
        self,
        component: str = "default",
        context: dict[str, Any] | None = None,
        **metadata: Any,
    ) -> DataPenaltySchema:
        """Create a penalty instance from this rule.

        Args:
            component: System component where violation occurred.
            context: Optional context for dynamic point calculation.
            **metadata: Additional metadata for the penalty.

        Returns:
            DataPenaltySchema instance.
        """
        points = self.calculate_points(context)
        return DataPenaltySchema(
            violation_type=self.violation_type,
            severity=self.severity,
            penalty_points=points,
            description=self.description,
            component=component,
            metadata=metadata,
        )


def _sla_violation_calculator(context: dict[str, Any]) -> float:
    """Calculate SLA violation penalty based on duration over threshold.

    Args:
        context: Must contain 'duration' and 'threshold' keys.

    Returns:
        Penalty points (10 points per threshold multiple).
    """
    duration = float(context.get("duration", 0))
    threshold = float(context.get("threshold", 1))
    if threshold <= 0:
        return 15.0  # Default high penalty
    return min(50.0, 10.0 * (duration / threshold))


# Predefined penalty rules for common violations
PENALTY_RULES: dict[str, PenaltyRule] = {
    "data_corruption": PenaltyRule(
        violation_type="data_corruption",
        severity=PenaltySeverity.CRITICAL,
        base_points=30.0,
        description="Detected corrupted data in storage layer",
        remediation="Trigger data repair workflow",
    ),
    "security_breach": PenaltyRule(
        violation_type="security_breach",
        severity=PenaltySeverity.CRITICAL,
        base_points=50.0,
        description="Security breach or unauthorized access detected",
        remediation="Lock affected resources and notify security team",
    ),
    "sla_violation": PenaltyRule(
        violation_type="sla_violation",
        severity=PenaltySeverity.HIGH,
        base_points=15.0,
        description="Response time exceeded SLA threshold",
        dynamic_calculator=_sla_violation_calculator,
        remediation="Investigate latency source and scale resources",
    ),
    "data_inconsistency": PenaltyRule(
        violation_type="data_inconsistency",
        severity=PenaltySeverity.HIGH,
        base_points=12.0,
        description="Data inconsistency detected between sources",
        remediation="Run reconciliation job",
    ),
    "retry_exhausted": PenaltyRule(
        violation_type="retry_exhausted",
        severity=PenaltySeverity.MEDIUM,
        base_points=8.0,
        description="Maximum retries reached for operation",
        remediation="Review error logs and retry configuration",
    ),
    "latency_spike": PenaltyRule(
        violation_type="latency_spike",
        severity=PenaltySeverity.MEDIUM,
        base_points=6.0,
        description="Latency spike detected above normal thresholds",
        remediation="Check for resource contention or upstream issues",
    ),
    "partial_data_loss": PenaltyRule(
        violation_type="partial_data_loss",
        severity=PenaltySeverity.MEDIUM,
        base_points=9.0,
        description="Partial data loss or incomplete response",
        remediation="Retry operation and verify data integrity",
    ),
    "validation_failed": PenaltyRule(
        violation_type="validation_failed",
        severity=PenaltySeverity.LOW,
        base_points=3.0,
        description="Input validation failed",
        remediation="Review input data format",
    ),
    "warning_logged": PenaltyRule(
        violation_type="warning_logged",
        severity=PenaltySeverity.LOW,
        base_points=1.0,
        description="Warning-level issue logged",
        remediation="Review logs for root cause",
    ),
    "retry_required": PenaltyRule(
        violation_type="retry_required",
        severity=PenaltySeverity.LOW,
        base_points=2.0,
        description="Operation required retry to succeed",
        remediation="Monitor for recurring issues",
    ),
}


def decay_penalty(
    penalty: DataPenaltySchema,
    now: datetime | None = None,
    half_life_hours: float = 24.0,
) -> float:
    """Calculate decayed penalty points based on time elapsed.

    Uses exponential decay so older penalties have less impact on current scores.
    Default half-life of 24 hours means penalty is halved each day.

    Formula: decayed_points = base_points * (0.5 ** (hours_since / half_life))

    Args:
        penalty: The penalty to decay.
        now: Current time (defaults to UTC now).
        half_life_hours: Hours for penalty to decay to half (default 24).

    Returns:
        Decayed penalty points.
    """
    if now is None:
        now = datetime.now(UTC)

    # Ensure both datetimes are timezone-aware for comparison
    penalty_time = penalty.timestamp
    if penalty_time.tzinfo is None:
        penalty_time = penalty_time.replace(tzinfo=UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)

    hours_since = (now - penalty_time).total_seconds() / 3600.0

    if hours_since < 0:
        # Future penalty (shouldn't happen, but handle gracefully)
        return penalty.penalty_points

    # Exponential decay: 0.5 ** (hours / half_life)
    decay_factor = 0.5 ** (hours_since / half_life_hours)
    return float(penalty.penalty_points) * decay_factor


def calculate_total_penalty(
    penalties: list[DataPenaltySchema],
    now: datetime | None = None,
    half_life_hours: float = 24.0,
) -> float:
    """Calculate total decayed penalty points from a list of penalties.

    Args:
        penalties: List of penalties to sum.
        now: Current time for decay calculation.
        half_life_hours: Half-life for decay.

    Returns:
        Total decayed penalty points.
    """
    return sum(decay_penalty(p, now, half_life_hours) for p in penalties)


def get_score_classification(score: float) -> str:
    """Classify accountability score into action bands.

    Args:
        score: Accountability score (0-100+).

    Returns:
        Classification string: 'normal', 'alert', 'throttle', or 'degraded'.
    """
    if score > 90:
        return "normal"
    elif score > 75:
        return "alert"
    elif score >= 50:
        return "throttle"
    else:
        return "degraded"


__all__ = [
    "PenaltySeverity",
    "SEVERITY_RANGES",
    "DataPenaltySchema",
    "PenaltyRule",
    "PENALTY_RULES",
    "decay_penalty",
    "calculate_total_penalty",
    "get_score_classification",
]
