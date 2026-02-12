"""VECTION Core Security Module.

Provides session isolation, persistent monitoring, and attacker tracking.
Implements the AI Session Isolation Framework (ASIF).
"""

from vection.core.security.session_isolation import (
    validate_session_boundary,
    SessionIsolationValidator,
    get_session_isolation_validator,
)
from vection.core.security.persistent_monitor import (
    PersistentMonitor,
    start_monitoring_daemon,
    stop_monitoring_daemon,
    get_persistent_monitor,
)
from vection.core.security.attacker_registry import (
    AttackerRegistry,
    get_attacker_registry,
    AttackViolation,
    ViolationType,
    CountermeasureConfig,
)

__all__ = [
    # Session isolation (ASIF)
    "validate_session_boundary",
    "SessionIsolationValidator",
    "get_session_isolation_validator",
    # Persistent monitoring
    "PersistentMonitor",
    "start_monitoring_daemon",
    "stop_monitoring_daemon",
    "get_persistent_monitor",
    # Attacker registry
    "AttackerRegistry",
    "get_attacker_registry",
    "AttackViolation",
    "ViolationType",
    "CountermeasureConfig",
]