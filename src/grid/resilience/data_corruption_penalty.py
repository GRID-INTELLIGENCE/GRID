"""Data corruption penalty module for tracking and penalizing data/environment corruption.

This module provides functionality to track data corruption events and apply penalties
to endpoints that cause data or environment corruption. It integrates with the existing
accountability system to provide a comprehensive view of endpoint reliability.
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum, auto

from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)


class CorruptionSeverity(Enum):
    """Severity levels for data corruption events."""

    LOW = auto()  # Minor data inconsistencies, recoverable
    MEDIUM = auto()  # Data corruption requiring intervention
    HIGH = auto()  # Critical data loss or corruption
    CRITICAL = auto()  # System-wide corruption or data breach


class CorruptionType(Enum):
    """Types of data corruption that can occur."""

    DATA_VALIDATION = "data_validation"
    SCHEMA_VIOLATION = "schema_violation"
    REFERENTIAL_INTEGRITY = "referential_integrity"
    ENVIRONMENT = "environment"
    SECURITY = "security"
    PERFORMANCE = "performance"
    RESOURCE_LEAK = "resource_leak"


@dataclass
class DataCorruptionEvent:
    """Represents a data corruption event with relevant metadata."""

    endpoint: str
    correlation_id: str
    severity: CorruptionSeverity
    corruption_type: CorruptionType
    description: str
    affected_resources: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict = field(default_factory=dict)
    stack_trace: str | None = None
    user_id: str | None = None
    tenant_id: str | None = None

    def to_dict(self) -> dict:
        """Convert the event to a dictionary for serialization."""
        return {
            "endpoint": self.endpoint,
            "correlation_id": self.correlation_id,
            "severity": self.severity.name,
            "corruption_type": self.corruption_type.value,
            "description": self.description,
            "affected_resources": self.affected_resources,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
        }


class DataCorruptionPenaltyConfig(BaseModel):
    """Configuration for data corruption penalties."""

    severity_weights: dict[CorruptionSeverity, float] = Field(
        default_factory=lambda: {
            CorruptionSeverity.LOW: 1.0,
            CorruptionSeverity.MEDIUM: 3.0,
            CorruptionSeverity.HIGH: 10.0,
            CorruptionSeverity.CRITICAL: 30.0,
        },
        description="Weights for different severity levels",
    )
    type_weights: dict[CorruptionType, float] = Field(
        default_factory=lambda: {
            CorruptionType.DATA_VALIDATION: 1.0,
            CorruptionType.SCHEMA_VIOLATION: 2.0,
            CorruptionType.REFERENTIAL_INTEGRITY: 3.0,
            CorruptionType.ENVIRONMENT: 5.0,
            CorruptionType.SECURITY: 10.0,
            CorruptionType.PERFORMANCE: 0.5,
            CorruptionType.RESOURCE_LEAK: 2.0,
        },
        description="Weights for different corruption types",
    )
    decay_rate: float = Field(
        default=0.9, description="Penalty decay rate per hour (0.9 means 10% decay per hour)", ge=0.0, le=1.0
    )
    max_penalty: float = Field(
        default=100.0, description="Maximum penalty score before severe actions are taken", gt=0.0
    )
    critical_threshold: float = Field(
        default=50.0, description="Threshold for considering an endpoint as critical", gt=0.0
    )


class DataCorruptionPenaltyTracker:
    """Tracks data corruption penalties for endpoints."""

    def __init__(self, config: DataCorruptionPenaltyConfig | None = None):
        self.config = config or DataCorruptionPenaltyConfig()
        self._penalties: dict[str, list[tuple[datetime, float]]] = {}
        self._endpoint_penalties: dict[str, float] = {}
        self._critical_endpoints: set[str] = set()

    def record_corruption(self, event: DataCorruptionEvent) -> float:
        """Record a data corruption event and return the calculated penalty."""
        # Calculate base penalty based on severity and type
        base_penalty = self.config.severity_weights.get(event.severity, 1.0) * self.config.type_weights.get(
            event.corruption_type, 1.0
        )

        # Apply multipliers based on affected resources
        resource_multiplier = 1.0 + (0.1 * len(event.affected_resources))
        penalty = base_penalty * resource_multiplier

        # Store the penalty
        now = datetime.now(UTC)
        if event.endpoint not in self._penalties:
            self._penalties[event.endpoint] = []
        self._penalties[event.endpoint].append((now, penalty))

        # Update endpoint penalty
        self._update_endpoint_penalty(event.endpoint)

        # Log the event
        logger.warning(
            "Data corruption detected: %s (severity: %s, type: %s, penalty: %.2f)",
            event.description,
            event.severity.name,
            event.corruption_type.value,
            penalty,
            extra={
                "event": "data_corruption",
                "endpoint": event.endpoint,
                "severity": event.severity.name,
                "corruption_type": event.corruption_type.value,
                "penalty": penalty,
                "correlation_id": event.correlation_id,
                **event.metadata,
            },
        )

        return penalty

    def _update_endpoint_penalty(self, endpoint: str) -> None:
        """Update the penalty score for an endpoint, applying decay to old penalties."""
        now = datetime.now(UTC)
        penalties = self._penalties.get(endpoint, [])

        # Apply decay to old penalties
        total_penalty = 0.0
        updated_penalties = []

        for ts, penalty in penalties:
            hours_old = (now - ts).total_seconds() / 3600
            decayed_penalty = penalty * (self.config.decay_rate**hours_old)

            # Only keep penalties that are still significant
            if decayed_penalty > 0.1:
                updated_penalties.append((ts, decayed_penalty))
                total_penalty += decayed_penalty

        # Update stored penalties
        if updated_penalties:
            self._penalties[endpoint] = updated_penalties
            self._endpoint_penalties[endpoint] = total_penalty

            # Check if endpoint is now critical
            if total_penalty >= self.config.critical_threshold:
                self._critical_endpoints.add(endpoint)
                logger.critical(
                    "Endpoint %s has reached critical penalty threshold (score: %.2f)", endpoint, total_penalty
                )
            elif endpoint in self._critical_endpoints and total_penalty < self.config.critical_threshold * 0.8:
                # Remove from critical if penalty drops below 80% of threshold
                self._critical_endpoints.remove(endpoint)
                logger.info("Endpoint %s is no longer critical (score: %.2f)", endpoint, total_penalty)
        else:
            self._penalties.pop(endpoint, None)
            self._endpoint_penalties.pop(endpoint, None)
            self._critical_endpoints.discard(endpoint)

    def get_endpoint_penalty(self, endpoint: str) -> float:
        """Get the current penalty score for an endpoint."""
        self._update_endpoint_penalty(endpoint)  # Ensure penalties are up to date
        return self._endpoint_penalties.get(endpoint, 0.0)

    def is_endpoint_critical(self, endpoint: str) -> bool:
        """Check if an endpoint is currently marked as critical."""
        self._update_endpoint_penalty(endpoint)  # Ensure penalties are up to date
        return endpoint in self._critical_endpoints

    def get_critical_endpoints(self) -> list[tuple[str, float]]:
        """Get a list of all critical endpoints with their penalty scores."""
        return [(endpoint, self._endpoint_penalties[endpoint]) for endpoint in self._critical_endpoints]

    def get_endpoint_health(self, endpoint: str) -> dict:
        """Get detailed health information for an endpoint."""
        penalty = self.get_endpoint_penalty(endpoint)
        is_critical = self.is_endpoint_critical(endpoint)

        return {
            "endpoint": endpoint,
            "penalty_score": penalty,
            "is_critical": is_critical,
            "severity": self._get_severity_level(penalty),
            "recommendation": self._get_recommendation(penalty, is_critical),
        }

    def _get_severity_level(self, penalty: float) -> str:
        """Convert penalty score to a severity level."""
        if penalty <= 1.0:
            return "LOW"
        elif penalty <= 5.0:
            return "MODERATE"
        elif penalty <= self.config.critical_threshold:
            return "HIGH"
        else:
            return "CRITICAL"

    def _get_recommendation(self, penalty: float, is_critical: bool) -> str:
        """Get a recommendation based on the penalty score."""
        if penalty == 0.0:
            return "No issues detected"

        if is_critical:
            return (
                "IMMEDIATE ACTION REQUIRED: Endpoint is causing critical data corruption. "
                "Consider disabling the endpoint and performing data recovery."
            )

        if penalty > 20.0:
            return "WARNING: Endpoint has high penalty score. Review recent data corruption events and implement fixes."

        return "Monitor: Endpoint has minor issues. Review logs for details."


# Global instance for easy access
corruption_tracker = DataCorruptionPenaltyTracker()


def record_corruption_event(
    endpoint: str,
    severity: CorruptionSeverity,
    corruption_type: CorruptionType,
    description: str,
    correlation_id: str | None = None,
    affected_resources: list[str] | None = None,
    metadata: dict | None = None,
    stack_trace: str | None = None,
    user_id: str | None = None,
    tenant_id: str | None = None,
) -> float:
    """Record a data corruption event with the global corruption tracker.

    Args:
        endpoint: The API endpoint or operation where corruption was detected
        severity: Severity of the corruption
        corruption_type: Type of corruption detected
        description: Human-readable description of the issue
        correlation_id: Optional correlation ID for tracing
        affected_resources: List of affected resources (tables, files, etc.)
        metadata: Additional metadata about the event
        stack_trace: Optional stack trace if available
        user_id: ID of the user who triggered the event (if applicable)
        tenant_id: ID of the tenant (if applicable)

    Returns:
        The calculated penalty score for this event
    """
    if correlation_id is None:
        # Generate a correlation ID based on the current time and a hash of the description
        # This ensures we have a unique ID even if none is provided
        ts = datetime.now(UTC).isoformat()
        hash_input = f"{endpoint}:{ts}:{description}"
        correlation_id = hashlib.md5(hash_input.encode()).hexdigest()

    event = DataCorruptionEvent(
        endpoint=endpoint,
        correlation_id=correlation_id,
        severity=severity,
        corruption_type=corruption_type,
        description=description,
        affected_resources=affected_resources or [],
        metadata=metadata or {},
        stack_trace=stack_trace,
        user_id=user_id,
        tenant_id=tenant_id,
    )

    return corruption_tracker.record_corruption(event)
