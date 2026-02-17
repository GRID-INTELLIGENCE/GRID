"""Session Isolator - Enforcing strict session boundaries.

Provides session isolation to prevent cross-session data leakage and
unauthorized access between sessions. Implements the AI Session Isolation
Framework (ASIF) with strict boundary enforcement.

Features:
- Session ownership validation
- Cross-session access prevention
- Session boundary enforcement for signals
- Session context isolation
- Shared resource access control
- Integration with audit logging
- Configurable isolation policies

Usage:
    from vection.security.session_isolator import SessionIsolator

    isolator = SessionIsolator()

    # Check if signal sharing is allowed
    if isolator.can_share_signal(source_session, target_session, signal):
        share_signal(signal)
    else:
        # Sharing blocked - log the attempt
        pass

    # Validate session access
    isolator.require_session_access(requester_session, target_session)
"""

from __future__ import annotations

import hashlib
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class SessionBoundaryViolation(Exception):
    """Exception raised when session boundary is violated.

    Attributes:
        source_session: Session that attempted the access.
        target_session: Session that was targeted.
        operation: Operation that was attempted.
        reason: Reason for the violation.
    """

    def __init__(
        self,
        message: str,
        source_session: str = "",
        target_session: str = "",
        operation: str = "",
        reason: str = "",
    ) -> None:
        """Initialize the exception.

        Args:
            message: Error message.
            source_session: Source session ID.
            target_session: Target session ID.
            operation: Operation that was attempted.
            reason: Reason for violation.
        """
        super().__init__(message)
        self.source_session = source_session
        self.target_session = target_session
        self.operation = operation
        self.reason = reason

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging/API responses.

        Returns:
            Dictionary with violation details.
        """
        return {
            "error": "session_boundary_violation",
            "message": str(self),
            "source_session": self.source_session,
            "target_session": self.target_session,
            "operation": self.operation,
            "reason": self.reason,
        }


class IsolationLevel(StrEnum):
    """Session isolation levels."""

    # No isolation - all sessions can access each other (not recommended)
    NONE = "none"

    # Basic isolation - sessions isolated but shared signals allowed
    BASIC = "basic"

    # Standard isolation - sessions isolated, shared signals require explicit grant
    STANDARD = "standard"

    # Strict isolation - no cross-session access allowed
    STRICT = "strict"

    # Maximum isolation - no sharing, no cross-references
    MAXIMUM = "maximum"


class AccessType(StrEnum):
    """Types of cross-session access."""

    READ = "read"
    WRITE = "write"
    SHARE = "share"
    QUERY = "query"
    REFERENCE = "reference"


@dataclass
class SessionGrant:
    """A grant allowing cross-session access.

    Attributes:
        grant_id: Unique identifier for this grant.
        source_session: Session granting access.
        target_session: Session receiving access.
        access_types: Allowed access types.
        resource_types: Allowed resource types (signals, anchors, etc.).
        expires_at: When the grant expires (None for no expiry).
        created_at: When the grant was created.
        created_by: Who created the grant.
        metadata: Additional grant metadata.
    """

    grant_id: str
    source_session: str
    target_session: str
    access_types: set[AccessType]
    resource_types: set[str] = field(default_factory=lambda: {"signal"})
    expires_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    created_by: str = "system"
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Check if the grant has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(UTC) > self.expires_at

    def allows(self, access_type: AccessType, resource_type: str = "signal") -> bool:
        """Check if this grant allows the specified access.

        Args:
            access_type: Type of access requested.
            resource_type: Type of resource being accessed.

        Returns:
            True if access is allowed.
        """
        if self.is_expired:
            return False
        return access_type in self.access_types and resource_type in self.resource_types

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "grant_id": self.grant_id,
            "source_session": self.source_session,
            "target_session": self.target_session,
            "access_types": [at.value for at in self.access_types],
            "resource_types": list(self.resource_types),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "is_expired": self.is_expired,
        }


@dataclass
class ViolationRecord:
    """Record of a session boundary violation.

    Attributes:
        violation_id: Unique identifier.
        timestamp: When the violation occurred.
        source_session: Session that attempted access.
        target_session: Target session.
        operation: Operation attempted.
        access_type: Type of access attempted.
        resource_type: Type of resource.
        reason: Why the violation occurred.
        blocked: Whether the violation was blocked.
    """

    violation_id: str
    timestamp: datetime
    source_session: str
    target_session: str
    operation: str
    access_type: AccessType
    resource_type: str
    reason: str
    blocked: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "violation_id": self.violation_id,
            "timestamp": self.timestamp.isoformat(),
            "source_session": self.source_session,
            "target_session": self.target_session,
            "operation": self.operation,
            "access_type": self.access_type.value,
            "resource_type": self.resource_type,
            "reason": self.reason,
            "blocked": self.blocked,
        }


@dataclass
class SessionIsolatorConfig:
    """Configuration for the session isolator.

    Attributes:
        isolation_level: Default isolation level.
        allow_self_access: Whether a session can always access itself.
        max_grants_per_session: Maximum grants a session can create.
        grant_expiry_hours: Default grant expiry time.
        track_violations: Whether to track violation history.
        max_violation_history: Maximum violations to retain.
        enable_logging: Whether to log isolation events.
        block_on_violation: Whether to block operations on violation.
    """

    isolation_level: IsolationLevel = IsolationLevel.STANDARD
    allow_self_access: bool = True
    max_grants_per_session: int = 100
    grant_expiry_hours: float = 24.0
    track_violations: bool = True
    max_violation_history: int = 1000
    enable_logging: bool = True
    block_on_violation: bool = True


class SessionIsolator:
    """Enforces session boundaries and prevents cross-session data leakage.

    Implements the AI Session Isolation Framework (ASIF) with configurable
    isolation levels and explicit grant management.

    Thread-safe and suitable for concurrent use.

    Usage:
        isolator = SessionIsolator()

        # Check access before cross-session operations
        if isolator.can_access(source_session, target_session, AccessType.READ):
            # Proceed with operation
            pass

        # Or use require_ methods to raise exceptions
        isolator.require_session_access(source_session, target_session, AccessType.READ)
    """

    def __init__(self, config: SessionIsolatorConfig | None = None) -> None:
        """Initialize the session isolator.

        Args:
            config: Isolator configuration.
        """
        self.config = config or SessionIsolatorConfig()
        self._lock = threading.Lock()

        # Grants storage: {source_session: {target_session: [grants]}}
        self._grants: dict[str, dict[str, list[SessionGrant]]] = {}

        # Violation history
        self._violations: list[ViolationRecord] = []

        # Statistics
        self._total_checks = 0
        self._total_allowed = 0
        self._total_blocked = 0
        self._total_grants_created = 0

        # Audit logger (lazy loaded)
        self._audit_logger: Any = None

        # Custom policy handlers
        self._policy_handlers: list[Callable[[str, str, AccessType, str], bool | None]] = []

        logger.info(f"SessionIsolator initialized with isolation level: {self.config.isolation_level.value}")

    def can_access(
        self,
        source_session: str,
        target_session: str,
        access_type: AccessType = AccessType.READ,
        resource_type: str = "signal",
    ) -> bool:
        """Check if source session can access target session.

        Args:
            source_session: Session requesting access.
            target_session: Session being accessed.
            access_type: Type of access requested.
            resource_type: Type of resource being accessed.

        Returns:
            True if access is allowed, False otherwise.
        """
        with self._lock:
            self._total_checks += 1

            # Self-access is always allowed if configured
            if self.config.allow_self_access and source_session == target_session:
                self._total_allowed += 1
                return True

            # Check isolation level
            allowed = self._check_isolation_level(source_session, target_session, access_type, resource_type)

            # Check custom policies
            for handler in self._policy_handlers:
                result = handler(source_session, target_session, access_type, resource_type)
                if result is not None:
                    allowed = result
                    break

            if allowed:
                self._total_allowed += 1
            else:
                self._total_blocked += 1
                self._record_violation(
                    source_session=source_session,
                    target_session=target_session,
                    operation="access_check",
                    access_type=access_type,
                    resource_type=resource_type,
                    reason=f"Blocked by {self.config.isolation_level.value} isolation",
                    blocked=True,
                )

            return allowed

    def _check_isolation_level(
        self,
        source_session: str,
        target_session: str,
        access_type: AccessType,
        resource_type: str,
    ) -> bool:
        """Check if access is allowed based on isolation level.

        Args:
            source_session: Source session ID.
            target_session: Target session ID.
            access_type: Type of access.
            resource_type: Type of resource.

        Returns:
            True if allowed, False otherwise.
        """
        level = self.config.isolation_level

        # No isolation - everything allowed
        if level == IsolationLevel.NONE:
            return True

        # Maximum isolation - nothing allowed across sessions
        if level == IsolationLevel.MAXIMUM:
            return False

        # Strict isolation - only explicit grants
        if level == IsolationLevel.STRICT:
            return self._has_grant(source_session, target_session, access_type, resource_type)

        # Standard isolation - grants or read-only for shared resources
        if level == IsolationLevel.STANDARD:
            if access_type == AccessType.READ and resource_type == "shared_signal":
                return True
            return self._has_grant(source_session, target_session, access_type, resource_type)

        # Basic isolation - most read operations allowed
        if level == IsolationLevel.BASIC:
            if access_type in (AccessType.READ, AccessType.QUERY):
                return True
            return self._has_grant(source_session, target_session, access_type, resource_type)

        return False

    def _has_grant(
        self,
        source_session: str,
        target_session: str,
        access_type: AccessType,
        resource_type: str,
    ) -> bool:
        """Check if there's a valid grant for the access.

        Args:
            source_session: Source session ID.
            target_session: Target session ID.
            access_type: Type of access.
            resource_type: Type of resource.

        Returns:
            True if a valid grant exists.
        """
        # Check grants from target to source (target grants access to source)
        if target_session in self._grants:
            if source_session in self._grants[target_session]:
                for grant in self._grants[target_session][source_session]:
                    if grant.allows(access_type, resource_type):
                        return True
        return False

    def require_session_access(
        self,
        source_session: str,
        target_session: str,
        access_type: AccessType = AccessType.READ,
        resource_type: str = "signal",
    ) -> None:
        """Require session access, raising exception if denied.

        Args:
            source_session: Session requesting access.
            target_session: Session being accessed.
            access_type: Type of access requested.
            resource_type: Type of resource being accessed.

        Raises:
            SessionBoundaryViolation: If access is denied.
        """
        if not self.can_access(source_session, target_session, access_type, resource_type):
            raise SessionBoundaryViolation(
                message=f"Session '{source_session}' cannot {access_type.value} {resource_type} "
                f"from session '{target_session}'",
                source_session=source_session,
                target_session=target_session,
                operation=f"{access_type.value}_{resource_type}",
                reason=f"Blocked by {self.config.isolation_level.value} isolation policy",
            )

    def can_share_signal(
        self,
        source_session: str,
        target_session: str | None = None,
        signal_id: str | None = None,
    ) -> bool:
        """Check if a signal can be shared from source session.

        Args:
            source_session: Session that owns the signal.
            target_session: Specific target session (None for global share).
            signal_id: Optional signal ID for logging.

        Returns:
            True if sharing is allowed.
        """
        # Global sharing (to shared pool)
        if target_session is None:
            if self.config.isolation_level == IsolationLevel.MAXIMUM:
                return False
            if self.config.isolation_level == IsolationLevel.STRICT:
                return False
            return True

        # Specific session sharing
        return self.can_access(
            source_session=target_session,  # Target wants to read
            target_session=source_session,  # Source's signal
            access_type=AccessType.SHARE,
            resource_type="signal",
        )

    def validate_signal_access(
        self,
        requesting_session: str,
        signal_session: str,
        signal_id: str,
    ) -> bool:
        """Validate if a session can access a specific signal.

        Args:
            requesting_session: Session requesting the signal.
            signal_session: Session that owns the signal.
            signal_id: ID of the signal.

        Returns:
            True if access is allowed.
        """
        allowed = self.can_access(
            source_session=requesting_session,
            target_session=signal_session,
            access_type=AccessType.READ,
            resource_type="signal",
        )

        if self.config.enable_logging:
            self._log_access_check(
                source_session=requesting_session,
                target_session=signal_session,
                access_type=AccessType.READ,
                resource_type="signal",
                resource_id=signal_id,
                allowed=allowed,
            )

        return allowed

    def create_grant(
        self,
        source_session: str,
        target_session: str,
        access_types: set[AccessType] | None = None,
        resource_types: set[str] | None = None,
        expiry_hours: float | None = None,
        created_by: str = "system",
    ) -> SessionGrant:
        """Create an access grant from source to target session.

        Args:
            source_session: Session granting access.
            target_session: Session receiving access.
            access_types: Allowed access types (default: READ only).
            resource_types: Allowed resource types (default: signal).
            expiry_hours: Hours until grant expires (None for config default).
            created_by: Who created the grant.

        Returns:
            The created SessionGrant.

        Raises:
            ValueError: If max grants exceeded.
        """
        with self._lock:
            # Check grant limit
            current_grants = len(self._grants.get(source_session, {}).get(target_session, []))
            if current_grants >= self.config.max_grants_per_session:
                raise ValueError(f"Maximum grants ({self.config.max_grants_per_session}) exceeded for session")

            # Set defaults
            if access_types is None:
                access_types = {AccessType.READ}
            if resource_types is None:
                resource_types = {"signal"}

            # Calculate expiry
            expiry = None
            exp_hours = expiry_hours if expiry_hours is not None else self.config.grant_expiry_hours
            if exp_hours > 0:
                from datetime import timedelta

                expiry = datetime.now(UTC) + timedelta(hours=exp_hours)

            # Generate grant ID
            grant_id = self._generate_grant_id(source_session, target_session)

            # Create grant
            grant = SessionGrant(
                grant_id=grant_id,
                source_session=source_session,
                target_session=target_session,
                access_types=access_types,
                resource_types=resource_types,
                expires_at=expiry,
                created_by=created_by,
            )

            # Store grant
            if source_session not in self._grants:
                self._grants[source_session] = {}
            if target_session not in self._grants[source_session]:
                self._grants[source_session][target_session] = []

            self._grants[source_session][target_session].append(grant)
            self._total_grants_created += 1

            # Log grant creation
            if self.config.enable_logging:
                self._log_grant_created(grant)

            logger.info(
                f"Grant created: {source_session} -> {target_session} (types: {[at.value for at in access_types]})"
            )

            return grant

    def revoke_grant(self, grant_id: str) -> bool:
        """Revoke an access grant.

        Args:
            grant_id: ID of the grant to revoke.

        Returns:
            True if grant was found and revoked.
        """
        with self._lock:
            for source_session in list(self._grants.keys()):
                for target_session in list(self._grants[source_session].keys()):
                    grants = self._grants[source_session][target_session]
                    for i, grant in enumerate(grants):
                        if grant.grant_id == grant_id:
                            grants.pop(i)
                            logger.info(f"Grant revoked: {grant_id}")
                            return True
            return False

    def revoke_all_grants(self, session_id: str) -> int:
        """Revoke all grants for a session.

        Args:
            session_id: Session ID.

        Returns:
            Number of grants revoked.
        """
        with self._lock:
            count = 0

            # Revoke grants where session is the source
            if session_id in self._grants:
                for target_grants in self._grants[session_id].values():
                    count += len(target_grants)
                del self._grants[session_id]

            # Revoke grants where session is the target
            for source_session in list(self._grants.keys()):
                if session_id in self._grants[source_session]:
                    count += len(self._grants[source_session][session_id])
                    del self._grants[source_session][session_id]

            logger.info(f"Revoked {count} grants for session {session_id}")
            return count

    def get_grants_for_session(self, session_id: str) -> list[SessionGrant]:
        """Get all grants involving a session.

        Args:
            session_id: Session ID.

        Returns:
            List of grants where session is source or target.
        """
        with self._lock:
            grants: list[SessionGrant] = []

            # Grants where session is source
            if session_id in self._grants:
                for target_grants in self._grants[session_id].values():
                    grants.extend(target_grants)

            # Grants where session is target
            for targets in self._grants.values():
                if session_id in targets:
                    grants.extend(targets[session_id])

            return grants

    def cleanup_expired_grants(self) -> int:
        """Remove expired grants.

        Returns:
            Number of grants removed.
        """
        with self._lock:
            count = 0
            for source_session in list(self._grants.keys()):
                for target_session in list(self._grants[source_session].keys()):
                    grants = self._grants[source_session][target_session]
                    original_count = len(grants)
                    self._grants[source_session][target_session] = [g for g in grants if not g.is_expired]
                    count += original_count - len(self._grants[source_session][target_session])

                    # Clean up empty entries
                    if not self._grants[source_session][target_session]:
                        del self._grants[source_session][target_session]
                if not self._grants[source_session]:
                    del self._grants[source_session]

            if count > 0:
                logger.info(f"Cleaned up {count} expired grants")
            return count

    def add_policy_handler(
        self,
        handler: Callable[[str, str, AccessType, str], bool | None],
    ) -> None:
        """Add a custom policy handler.

        The handler receives (source_session, target_session, access_type, resource_type)
        and returns True (allow), False (deny), or None (defer to next handler).

        Args:
            handler: Policy handler function.
        """
        self._policy_handlers.append(handler)

    def get_violation_history(
        self,
        session_id: str | None = None,
        limit: int = 100,
    ) -> list[ViolationRecord]:
        """Get violation history.

        Args:
            session_id: Filter by session ID (None for all).
            limit: Maximum records to return.

        Returns:
            List of violation records.
        """
        with self._lock:
            violations = self._violations

            if session_id is not None:
                violations = [v for v in violations if v.source_session == session_id or v.target_session == session_id]

            return violations[-limit:]

    def get_stats(self) -> dict[str, Any]:
        """Get isolator statistics.

        Returns:
            Dictionary with statistics.
        """
        with self._lock:
            total_grants = sum(len(grants) for targets in self._grants.values() for grants in targets.values())

            return {
                "isolation_level": self.config.isolation_level.value,
                "total_checks": self._total_checks,
                "total_allowed": self._total_allowed,
                "total_blocked": self._total_blocked,
                "block_rate_percent": (
                    round((self._total_blocked / self._total_checks) * 100, 2) if self._total_checks > 0 else 0
                ),
                "active_grants": total_grants,
                "total_grants_created": self._total_grants_created,
                "violation_count": len(self._violations),
                "policy_handlers": len(self._policy_handlers),
            }

    def _generate_grant_id(self, source_session: str, target_session: str) -> str:
        """Generate a unique grant ID."""
        timestamp = int(time.time() * 1000000)
        hash_input = f"{source_session}:{target_session}:{timestamp}"
        return f"grant_{hashlib.sha256(hash_input.encode()).hexdigest()[:12]}"

    def _record_violation(
        self,
        source_session: str,
        target_session: str,
        operation: str,
        access_type: AccessType,
        resource_type: str,
        reason: str,
        blocked: bool,
    ) -> None:
        """Record a session boundary violation."""
        if not self.config.track_violations:
            return

        violation = ViolationRecord(
            violation_id=f"viol_{int(time.time() * 1000000)}",
            timestamp=datetime.now(UTC),
            source_session=source_session,
            target_session=target_session,
            operation=operation,
            access_type=access_type,
            resource_type=resource_type,
            reason=reason,
            blocked=blocked,
        )

        self._violations.append(violation)

        # Trim history if needed
        if len(self._violations) > self.config.max_violation_history:
            self._violations = self._violations[-self.config.max_violation_history :]

        # Log to audit logger
        if self.config.enable_logging:
            self._log_violation(violation)

    def _log_access_check(
        self,
        source_session: str,
        target_session: str,
        access_type: AccessType,
        resource_type: str,
        resource_id: str | None,
        allowed: bool,
    ) -> None:
        """Log an access check to audit logger."""
        try:
            if self._audit_logger is None:
                from vection.security.audit_logger import get_audit_logger

                self._audit_logger = get_audit_logger()

            from vection.security.audit_logger import SecurityEventType

            self._audit_logger.log_event(
                event_type=SecurityEventType.SESSION_BOUNDARY_CHECK,
                session_id=source_session,
                details={
                    "target_session": target_session,
                    "access_type": access_type.value,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "allowed": allowed,
                    "isolation_level": self.config.isolation_level.value,
                },
            )
        except Exception:  # noqa: S110 intentional silent handling
            pass

    def _log_violation(self, violation: ViolationRecord) -> None:
        """Log a violation to audit logger."""
        try:
            if self._audit_logger is None:
                from vection.security.audit_logger import get_audit_logger

                self._audit_logger = get_audit_logger()

            from vection.security.audit_logger import SecurityEventType

            self._audit_logger.log_event(
                event_type=SecurityEventType.SESSION_BOUNDARY_VIOLATION,
                session_id=violation.source_session,
                details=violation.to_dict(),
            )
        except Exception:  # noqa: S110 intentional silent handling
            pass

    def _log_grant_created(self, grant: SessionGrant) -> None:
        """Log grant creation to audit logger."""
        try:
            if self._audit_logger is None:
                from vection.security.audit_logger import get_audit_logger

                self._audit_logger = get_audit_logger()

            from vection.security.audit_logger import SecurityEventType

            self._audit_logger.log_event(
                event_type=SecurityEventType.ACCESS_GRANTED,
                session_id=grant.source_session,
                details={
                    "grant_id": grant.grant_id,
                    "target_session": grant.target_session,
                    "access_types": [at.value for at in grant.access_types],
                    "resource_types": list(grant.resource_types),
                    "created_by": grant.created_by,
                },
            )
        except Exception:  # noqa: S110 intentional silent handling
            pass


# Module-level singleton
_session_isolator: SessionIsolator | None = None


def get_session_isolator(config: SessionIsolatorConfig | None = None) -> SessionIsolator:
    """Get the global session isolator instance.

    Args:
        config: Configuration (only used on first call).

    Returns:
        SessionIsolator singleton.
    """
    global _session_isolator
    if _session_isolator is None:
        _session_isolator = SessionIsolator(config)
    return _session_isolator


def validate_session_boundary(
    source_session: str,
    target_session: str,
    access_type: AccessType = AccessType.READ,
    resource_type: str = "signal",
) -> bool:
    """Convenience function to validate session boundary.

    Args:
        source_session: Session requesting access.
        target_session: Session being accessed.
        access_type: Type of access requested.
        resource_type: Type of resource.

    Returns:
        True if access is allowed.
    """
    isolator = get_session_isolator()
    return isolator.can_access(source_session, target_session, access_type, resource_type)
