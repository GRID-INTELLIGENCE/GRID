"""
Boundaries module: schema and enforcement for boundaries, consent, and guardrails.
Preserves the right to refuse service at any instance with WebSocket-persistent logging.
Includes preparedness framework (risk tiers, gates, biosecurity scope) and overwatch (monitoring/alerting).
"""
from boundaries.boundary import Boundary, BoundaryEngine, Consent, Guardrail
from boundaries.logger_ws import BoundaryEventLogger, get_logger
from boundaries.overwatch import Overwatch, wrap_logger_with_overwatch
from boundaries.preparedness import BiosecurityScope, Gate, PreparednessFramework, RiskTier
from boundaries.refusal import RefusalRights, check_refusal, refuse_service

__all__ = [
    "BoundaryEngine",
    "Boundary",
    "Consent",
    "Guardrail",
    "RefusalRights",
    "refuse_service",
    "check_refusal",
    "BoundaryEventLogger",
    "get_logger",
    "PreparednessFramework",
    "RiskTier",
    "Gate",
    "BiosecurityScope",
    "Overwatch",
    "wrap_logger_with_overwatch",
]

__version__ = "1.0.0"
