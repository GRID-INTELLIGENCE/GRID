"""
Audit Logging for Portfolio Data
=================================
Comprehensive audit logging for portfolio data access and operations.

Security Level: CRITICAL
Privacy: Personal Sensitive Information
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Audit event types."""

    READ = "READ"
    WRITE = "WRITE"
    DELETE = "DELETE"
    EXPORT = "EXPORT"
    AI_ACCESS = "AI_ACCESS"
    ACCESS_GRANTED = "ACCESS_GRANTED"
    ACCESS_DENIED = "ACCESS_DENIED"
    DATA_READ = "DATA_READ"
    DATA_WRITE = "DATA_WRITE"
    DATA_DELETE = "DATA_DELETE"
    DATA_EXPORT = "DATA_EXPORT"
    QUERY_EXECUTED = "QUERY_EXECUTED"
    SECURITY_BREACH = "SECURITY_BREACH"
    UNAUTHORIZED_ATTEMPT = "UNAUTHORIZED_ATTEMPT"


@dataclass
class AuditEvent:
    """Audit event data."""

    event_type: AuditEventType
    user_id_hash: str
    action: str
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    ip_address: str | None = None
    user_agent: str | None = None
    session_id: str | None = None
    metadata: dict[str, Any] | None = None


class PortfolioAuditLogger:
    """
    Comprehensive audit logging for portfolio data.

    Tracks all access and operations on portfolio data.
    """

    def __init__(self, max_entries: int = 1000):
        """
        Initialize audit logger.

        Args:
            max_entries: Maximum number of audit entries to keep
        """
        self.audit_log: list[AuditEvent] = []
        self.max_entries = max_entries
        self._configure_logging()

    def _configure_logging(self) -> None:
        """Configure audit logging."""
        # Setup file handler for audit logs
        try:
            import os

            log_dir = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
            os.makedirs(log_dir, exist_ok=True)

            log_file = os.path.join(log_dir, "portfolio_audit.log")

            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.WARNING)

            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            file_handler.setFormatter(formatter)

            logger.addHandler(file_handler)

        except Exception as e:
            logger.warning(f"Failed to configure audit logging: {e}")

    def log_event(
        self,
        event_type: AuditEventType,
        user_id: str | None = None,
        user_id_hash: str | None = None,
        action: str = "",
        details: dict[str, Any] | str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Log audit event.

        Args:
            event_type: Type of event
            user_id_hash: Hashed user ID
            details: Event details
            ip_address: IP address
            user_agent: User agent
            session_id: Session ID
            metadata: Additional metadata
        """
        resolved_user_id_hash = user_id_hash or self._hash_user_id(user_id)
        normalized_details: dict[str, Any] = {}
        if isinstance(details, dict):
            normalized_details = details
        elif isinstance(details, str):
            normalized_details = {"message": details}

        event = AuditEvent(
            event_type=event_type,
            user_id_hash=resolved_user_id_hash,
            action=action,
            details=normalized_details,
            timestamp=datetime.now(),
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            metadata=metadata or {},
        )

        self.audit_log.append(event)

        # Trim audit log if too large
        if len(self.audit_log) > self.max_entries:
            self.audit_log = self.audit_log[-self.max_entries :]

        # Log to system
        log_level = (
            logging.ERROR
            if event_type in [AuditEventType.SECURITY_BREACH, AuditEventType.UNAUTHORIZED_ATTEMPT]
            else logging.WARNING
        )

        logger.log(
            log_level,
            f"Audit Event: {event_type.value} | User: {resolved_user_id_hash[:16]}... | {action}",
        )

    def _hash_user_id(self, user_id: str | None) -> str:
        """Hash user ID for audit logging."""
        if not user_id:
            return "unknown"
        return hashlib.sha256(user_id.encode()).hexdigest()

    def get_audit_log(
        self,
        event_type: AuditEventType | None = None,
        user_id_hash: str | None = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """
        Get audit log entries.

        Args:
            event_type: Event type to filter by
            user_id_hash: User ID hash to filter by
            limit: Max entries to return

        Returns:
            Filtered audit log entries
        """
        filtered = self.audit_log

        if event_type:
            filtered = [e for e in filtered if e.event_type == event_type]

        if user_id_hash:
            filtered = [e for e in filtered if e.user_id_hash == user_id_hash]

        return filtered[-limit:]

    def get_logs(self, limit: int = 100) -> list[AuditEvent]:
        """Compatibility wrapper for tests."""
        return self.get_audit_log(limit=limit)

    def get_security_events(self, limit: int = 50) -> list[AuditEvent]:
        """
        Get security-related events.

        Args:
            limit: Max entries to return

        Returns:
            Security event entries
        """
        security_events = [
            e
            for e in self.audit_log
            if e.event_type
            in [
                AuditEventType.SECURITY_BREACH,
                AuditEventType.UNAUTHORIZED_ATTEMPT,
                AuditEventType.ACCESS_DENIED,
            ]
        ]
        return security_events[-limit:]

    def export_audit_log(self, output_path: str) -> None:
        """
        Export audit log to file.

        Args:
            output_path: Path to export file
        """
        export_data = self.export_logs()

        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Audit log exported to {output_path}")

    def export_logs(self) -> list[dict[str, Any]]:
        """Export audit log entries as dictionaries."""
        return [
            {
                "event_type": event.event_type.value,
                "user_id_hash": event.user_id_hash,
                "action": event.action,
                "details": event.details,
                "timestamp": event.timestamp.isoformat(),
                "ip_address": event.ip_address,
                "user_agent": event.user_agent,
                "session_id": event.session_id,
                "metadata": event.metadata,
            }
            for event in self.audit_log
        ]


# Singleton instance
_audit_logger_instance: PortfolioAuditLogger | None = None


def get_audit_logger() -> PortfolioAuditLogger:
    """
    Get singleton audit logger instance.

    Returns:
        PortfolioAuditLogger instance
    """
    global _audit_logger_instance
    if _audit_logger_instance is None:
        _audit_logger_instance = PortfolioAuditLogger()
    return _audit_logger_instance


# Example usage
def example_usage() -> None:
    """Example usage of audit logging."""
    print("=" * 70)
    print("Portfolio Audit Logging Demo")
    print("=" * 70)
    print()

    # Initialize audit logger
    audit_logger = PortfolioAuditLogger()

    # Log access granted
    audit_logger.log_event(
        event_type=AuditEventType.ACCESS_GRANTED,
        user_id_hash="e606e38b0d8c19b2...",
        details="Portfolio data access granted for user123",
    )
    print("✓ Access granted event logged")

    # Log data read
    audit_logger.log_event(
        event_type=AuditEventType.DATA_READ,
        user_id_hash="e606e38b0d8c19b2...",
        details="Portfolio positions read from database",
        metadata={"positions_count": 5},
    )
    print("✓ Data read event logged")

    # Log unauthorized attempt
    audit_logger.log_event(
        event_type=AuditEventType.UNAUTHORIZED_ATTEMPT,
        user_id_hash="unknown_hash...",
        details="Unauthorized access attempt detected",
        ip_address="192.168.1.100",
    )
    print("✓ Unauthorized attempt event logged")

    # Get audit log
    audit_log = audit_logger.get_audit_log(limit=10)
    print(f"\nAudit Log Entries: {len(audit_log)}")
    for event in audit_log[-3:]:
        print(f"  {event.event_type.value}: {event.details}")

    # Get security events
    security_events = audit_logger.get_security_events(limit=5)
    print(f"\nSecurity Events: {len(security_events)}")
    for event in security_events:
        print(f"  {event.event_type.value}: {event.details}")


if __name__ == "__main__":
    example_usage()
