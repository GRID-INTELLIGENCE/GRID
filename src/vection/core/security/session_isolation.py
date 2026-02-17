"""
Session Isolation (ASIF) - Boundary Enforcement.

Enforces strict session boundaries for cognitive signals, even
when shared globally. Prevents cross-session leakage.

Enterprise Analogy: Multi-tenant VPC isolation.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class SessionIsolationValidator:
    """
    ASIF implementation for cognitive signals.
    """

    def validate_session_boundary(self, signal: Any, current_session: str | None) -> bool:
        """
        Verify that a signal belongs to the current session or is
        explicitly authorized for cross-session access.
        """
        if not current_session:
            return True  # No session context, allow for now (system startup?)

        signal_session = getattr(signal, "_session_id", None)
        if signal_session and signal_session != current_session:
            logger.warning(
                f"[SECURITY] Session boundary violation! "
                f"Signal {getattr(signal, 'signal_id', 'unknown')} (Session {signal_session}) "
                f"accessed in Session {current_session}."
            )
            return False

        return True


# Singleton
_validator: SessionIsolationValidator | None = None


def get_session_isolation_validator() -> SessionIsolationValidator:
    global _validator
    if _validator is None:
        _validator = SessionIsolationValidator()
    return _validator


def validate_session_boundary(signal: Any, session_id: str | None) -> bool:
    v = get_session_isolation_validator()
    return v.validate_session_boundary(signal, session_id)
