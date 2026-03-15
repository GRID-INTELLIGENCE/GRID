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

# Anomaly detection factory functions and config
from .anomaly_detector import (
    AdaptiveAnomalyDetector,
    AnomalyResult,
    BaselineMetrics,
    MultiWindowAnomalyDetector,
    RateLimitAnomalyDetector,
    create_adaptive_anomaly_detector,
    create_multi_window_detector,
    create_rate_limit_detector,
)
from .config import ComponentConfig, GuardMode, ParasiteGuardConfig
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
# Note: ParasiteContext, DetectionResult, SanitizationResult, SourceMap are in .models
# ParasiteSeverity replaces the stale ParasiteRisk from definitions.py
# ParasiteDetector protocol removed - use Detector from .detectors instead
from .integration import add_parasite_guard
from .middleware import ParasiteGuardMiddleware
from .models import DetectionResult, ParasiteContext, ParasiteSeverity, SanitizationResult, SourceMap
from .state_machine import (
    GuardState,
    InvalidTransitionError,
    ParasiteGuardStateMachine,
    TransitionProbability,
    TransitionRecord,
)

# Lazy imports for optional components (to avoid import cycles and heavy deps)
# These can be imported explicitly when needed:
# - from .precision_validator import PrecisionValidator
# - from .metrics import *

__all__ = [
    # Core definitions (from models.py)
    "ParasiteContext",
    "ParasiteSeverity",
    "SourceMap",
    # Detector (use Detector from .detectors for implementations)
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
    # Configuration
    "ParasiteGuardConfig",
    "ComponentConfig",
    "GuardMode",
    # Anomaly detection
    "AdaptiveAnomalyDetector",
    "MultiWindowAnomalyDetector",
    "RateLimitAnomalyDetector",
    "AnomalyResult",
    "BaselineMetrics",
    # Factory functions (config-driven)
    "create_adaptive_anomaly_detector",
    "create_multi_window_detector",
    "create_rate_limit_detector",
]
