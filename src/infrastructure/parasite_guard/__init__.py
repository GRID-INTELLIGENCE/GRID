"""
Parasite Guard Infrastructure.

Exports core components for detection and middleware.
"""

from .alerter import (
    EscalationPolicy,
    InMemoryAlertChannel,
    LoggingAlertChannel,
    ParasiteAlerter,
    SecurityAuditChannel,
    WebhookAlertChannel,
)
from .contracts import (
    Alert,
    AlertChannel,
    AlerterContract,
    DetectorContract,
    HealthStatus,
    PrecisionMetrics,
    SanitizerContract,
    Severity,
    validate_alerter_contract,
    validate_detector_contract,
    validate_sanitizer_contract,
)
from .definitions import ParasiteAction, ParasiteContext, ParasiteRisk, SourceMap
from .detector import ParasiteDetector
from .integration import add_parasite_guard
from .middleware import ParasiteGuardMiddleware
from .models import DetectionResult, ParasiteSeverity, SanitizationResult
from .state_machine import (
    GuardState,
    InvalidTransitionError,
    ParasiteGuardStateMachine,
    TransitionProbability,
    TransitionRecord,
)

# Lazy imports for optional components (to avoid import cycles and heavy deps)
# These can be imported explicitly when needed:
# - from .anomaly_detector import AdaptiveAnomalyDetector
# - from .precision_validator import PrecisionValidator
# - from .metrics import *

__all__ = [
    # Core definitions
    "ParasiteContext",
    "ParasiteRisk",
    "ParasiteAction",
    "ParasiteSeverity",
    "SourceMap",
    # Detector
    "ParasiteDetector",
    # Middleware
    "ParasiteGuardMiddleware",
    "add_parasite_guard",
    # Models
    "DetectionResult",
    "SanitizationResult",
    # Contracts
    "DetectorContract",
    "SanitizerContract",
    "AlerterContract",
    "AlertChannel",
    "Alert",
    "Severity",
    "HealthStatus",
    "PrecisionMetrics",
    # Contract validators
    "validate_detector_contract",
    "validate_sanitizer_contract",
    "validate_alerter_contract",
    # State machine
    "GuardState",
    "ParasiteGuardStateMachine",
    "TransitionProbability",
    "TransitionRecord",
    "InvalidTransitionError",
    # Alerter
    "ParasiteAlerter",
    "EscalationPolicy",
    "LoggingAlertChannel",
    "SecurityAuditChannel",
    "WebhookAlertChannel",
    "InMemoryAlertChannel",
]
