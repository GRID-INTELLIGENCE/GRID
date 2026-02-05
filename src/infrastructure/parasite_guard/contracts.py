from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Protocol, runtime_checkable


@dataclass
class HealthStatus:
    healthy: bool
    latency_ms: float
    error_rate: float
    confidence: float  # Statistical confidence level

@dataclass
class PrecisionMetrics:
    """Precision metrics for detector validation."""
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int

    @property
    def precision(self) -> float:
        total = self.true_positives + self.false_positives
        return self.true_positives / total if total > 0 else 0.0

    @property
    def recall(self) -> float:
        total = self.true_positives + self.false_negatives
        return self.true_positives / total if total > 0 else 0.0

    @property
    def f1_score(self) -> float:
        p, r = self.precision, self.recall
        return 2 * (p * r) / (p + r) if (p + r) > 0 else 0.0

    @property
    def accuracy(self) -> float:
        total = self.true_positives + self.false_positives + self.true_negatives + self.false_negatives
        return (self.true_positives + self.true_negatives) / total if total > 0 else 0.0

@dataclass
class DetectionResult:
    """Standardized detection result."""
    detected: bool
    confidence: float
    details: dict[str, Any]

@dataclass
class ParasiteContext:
    """Context information for a potential parasite."""
    component: str
    severity: str
    pattern: str
    details: dict[str, Any]

@dataclass
class SanitizationResult:
    """Result of a sanitization attempt."""
    success: bool
    details: dict[str, Any]

class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@runtime_checkable
class DetectorContract(Protocol):
    """Strict contract for all detectors."""
    name: str
    component: str

    async def detect(self, context: dict) -> DetectionResult: ...
    def validate_config(self) -> bool: ...
    def get_health(self) -> HealthStatus: ...
    def get_precision_metrics(self) -> PrecisionMetrics: ...

@runtime_checkable
class SanitizerContract(Protocol):
    """Strict contract for all sanitizers."""
    component: str
    success_rate: float  # Target: 99.2%+ for WebSocket, 97.5%+ for EventBus

    async def sanitize(self, context: ParasiteContext) -> SanitizationResult: ...
    async def rollback(self, context: ParasiteContext) -> bool: ...
    def can_sanitize(self, context: ParasiteContext) -> bool: ...

@dataclass
class Alert:
    """Alert structure."""
    id: str
    severity: Severity
    component: str
    pattern: str
    message: str
    timestamp: datetime
    context: Any | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

@runtime_checkable
class AlertChannel(Protocol):
    """Protocol for alert channels."""
    async def send(self, alert: Alert) -> None: ...

@runtime_checkable
class AlerterContract(Protocol):
    """Contract for alerting system."""
    async def alert(self, context: ParasiteContext, severity: Severity) -> None: ...
    async def escalate(self, context: ParasiteContext) -> None: ...


# Contract validation helpers


def validate_detector_contract(detector: Any) -> tuple[bool, list[str]]:
    """Validate that an object satisfies DetectorContract.

    Args:
        detector: Object to validate.

    Returns:
        Tuple of (is_valid, list of errors).
    """
    errors: list[str] = []

    if not isinstance(detector, DetectorContract):
        errors.append("Does not implement DetectorContract protocol")

    if not hasattr(detector, "name") or not isinstance(getattr(detector, "name", None), str):
        errors.append("Missing or invalid 'name' attribute")

    if not hasattr(detector, "component") or not isinstance(
        getattr(detector, "component", None), str
    ):
        errors.append("Missing or invalid 'component' attribute")

    if not callable(getattr(detector, "detect", None)):
        errors.append("Missing 'detect' method")

    if not callable(getattr(detector, "validate_config", None)):
        errors.append("Missing 'validate_config' method")

    if not callable(getattr(detector, "get_health", None)):
        errors.append("Missing 'get_health' method")

    if not callable(getattr(detector, "get_precision_metrics", None)):
        errors.append("Missing 'get_precision_metrics' method")

    return len(errors) == 0, errors


def validate_sanitizer_contract(sanitizer: Any) -> tuple[bool, list[str]]:
    """Validate that an object satisfies SanitizerContract.

    Args:
        sanitizer: Object to validate.

    Returns:
        Tuple of (is_valid, list of errors).
    """
    errors: list[str] = []

    if not isinstance(sanitizer, SanitizerContract):
        errors.append("Does not implement SanitizerContract protocol")

    if not hasattr(sanitizer, "component") or not isinstance(
        getattr(sanitizer, "component", None), str
    ):
        errors.append("Missing or invalid 'component' attribute")

    if not hasattr(sanitizer, "success_rate"):
        errors.append("Missing 'success_rate' attribute")
    else:
        rate = getattr(sanitizer, "success_rate", None)
        if not isinstance(rate, (int, float)) or not (0.0 <= rate <= 1.0):
            errors.append("'success_rate' must be a float between 0.0 and 1.0")

    if not callable(getattr(sanitizer, "sanitize", None)):
        errors.append("Missing 'sanitize' method")

    if not callable(getattr(sanitizer, "rollback", None)):
        errors.append("Missing 'rollback' method")

    if not callable(getattr(sanitizer, "can_sanitize", None)):
        errors.append("Missing 'can_sanitize' method")

    return len(errors) == 0, errors


def validate_alerter_contract(alerter: Any) -> tuple[bool, list[str]]:
    """Validate that an object satisfies AlerterContract.

    Args:
        alerter: Object to validate.

    Returns:
        Tuple of (is_valid, list of errors).
    """
    errors: list[str] = []

    if not isinstance(alerter, AlerterContract):
        errors.append("Does not implement AlerterContract protocol")

    if not callable(getattr(alerter, "alert", None)):
        errors.append("Missing 'alert' method")

    if not callable(getattr(alerter, "escalate", None)):
        errors.append("Missing 'escalate' method")

    return len(errors) == 0, errors
