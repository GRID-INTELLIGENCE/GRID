"""Resilience module for error recovery, metrics, and accountability.

Provides:
- Retry and fallback decorators
- Operation metrics collection
- Accountability scoring and penalty tracking
- Policy-based error handling
"""

from .accountability import (
    AccountabilityCalculator,
    DeliveryClassification,
    DeliveryScore,
    DevContract,
    get_accountability_calculator,
    get_contract,
)
from .accountability import (
    activate as activate_contract,
)
from .metrics import (
    MetricsCollector,
    OperationMetrics,
    RetryMetrics,
    get_metrics_collector,
)
from .penalties import (
    PENALTY_RULES,
    SEVERITY_RANGES,
    DataPenaltySchema,
    PenaltyRule,
    PenaltySeverity,
    calculate_total_penalty,
    decay_penalty,
    get_score_classification,
)

__all__ = [
    # Metrics
    "OperationMetrics",
    "RetryMetrics",
    "MetricsCollector",
    "get_metrics_collector",
    # Accountability
    "DeliveryClassification",
    "DeliveryScore",
    "AccountabilityCalculator",
    "get_accountability_calculator",
    # Governance contract (TUV-001)
    "DevContract",
    "activate_contract",
    "get_contract",
    # Penalties
    "PenaltySeverity",
    "SEVERITY_RANGES",
    "DataPenaltySchema",
    "PenaltyRule",
    "PENALTY_RULES",
    "decay_penalty",
    "calculate_total_penalty",
    "get_score_classification",
]
