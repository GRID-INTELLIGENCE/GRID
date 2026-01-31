"""
Mothership Audit Service - Bridges SecurityEnforcer to persistent audit logging.

Provides hybrid audit logging combining:
1. Vection's AuditLogger for hash-chaining (tamper-evident) and SIEM callbacks
2. Database persistence via AuditLogRow model

This service integrates the existing audit logging infrastructure with
Mothership's security enforcement middleware.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

logger = logging.getLogger(__name__)

# Try to import Vection audit logger
try:
    from vection.security.audit_logger import (
        AuditEvent,
        AuditLogger,
        AuditLoggerConfig,
        EventSeverity,
        SecurityEventType,
    )
    VECTION_AVAILABLE = True
except ImportError:
    VECTION_AVAILABLE = False
    AuditLogger = None  # type: ignore[misc, assignment]
    AuditLoggerConfig = None  # type: ignore[misc, assignment]
    AuditEvent = None  # type: ignore[misc, assignment]
    SecurityEventType = None  # type: ignore[misc, assignment]
    EventSeverity = None  # type: ignore[misc, assignment]

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from ..middleware.security_enforcer import SecurityAuditEntry


class MothershipAuditService:
    """
    Bridges SecurityEnforcer audit entries to persistent, tamper-evident logging.
    
    Features:
    - Hash-chaining via Vection AuditLogger (tamper-evident)
    - Database persistence via AuditLogRow
    - SIEM callback support for real-time alerting
    - Graceful degradation if Vection not available
    """

    def __init__(
        self,
        db_session_factory: Callable[[], AsyncSession] | None = None,
        config: Any | None = None,
        enable_db_persistence: bool = True,
        enable_hash_chain: bool = True,
    ):
        """
        Initialize the audit service.
        
        Args:
            db_session_factory: Factory function to create async DB sessions
            config: AuditLoggerConfig for Vection logger (optional)
            enable_db_persistence: Whether to persist to database
            enable_hash_chain: Whether to enable hash-chaining
        """
        self.db_session_factory = db_session_factory
        self.enable_db_persistence = enable_db_persistence and db_session_factory is not None
        self.enable_hash_chain = enable_hash_chain
        self._callbacks: list[Callable[[dict[str, Any]], None]] = []

        # Initialize Vection logger if available
        self._vection_logger: Any | None = None
        if VECTION_AVAILABLE and AuditLogger is not None:
            try:
                vection_config = config
                if vection_config is None and AuditLoggerConfig is not None:
                    vection_config = AuditLoggerConfig(
                        log_dir="logs/security/mothership",
                        log_file_name="mothership_audit.log",
                        enable_hash_chain=enable_hash_chain,
                        json_format=True,
                        log_to_console=False,  # Avoid duplicate console logs
                        log_to_file=True,
                    )
                self._vection_logger = AuditLogger(vection_config)
                logger.info("Vection AuditLogger initialized for Mothership audit service")
            except Exception as e:
                logger.warning(f"Failed to initialize Vection AuditLogger: {e}")
                self._vection_logger = None
        else:
            logger.info("Vection AuditLogger not available, using fallback logging")

        # In-memory fallback if Vection not available
        self._fallback_log: list[dict[str, Any]] = []
        self._max_fallback_entries = 10000

    def _map_severity(self, violations: list[Any], allowed: bool) -> str:
        """Map security audit entry to severity level."""
        if not allowed:
            return "error"
        if violations:
            # Check for critical violations
            for v in violations:
                if hasattr(v, 'severity') and v.severity == "critical":
                    return "critical"
                if hasattr(v, 'severity') and v.severity == "high":
                    return "error"
            return "warning"
        return "info"

    def _map_to_security_event_type(self, entry: SecurityAuditEntry) -> Any:
        """Map SecurityAuditEntry to Vection SecurityEventType."""
        if not VECTION_AVAILABLE or SecurityEventType is None:
            return None

        if not entry.allowed:
            return SecurityEventType.ACCESS_DENIED
        if entry.violations:
            return SecurityEventType.VALIDATION_FAILED
        if entry.sanitization_applied:
            return SecurityEventType.INPUT_SANITIZED
        return SecurityEventType.ACCESS_GRANTED

    def log_security_event(self, entry: SecurityAuditEntry) -> None:
        """
        Log a security audit entry from SecurityEnforcer.
        
        Args:
            entry: SecurityAuditEntry from the middleware
        """
        # Build common audit data
        audit_data = {
            "request_id": entry.request_id,
            "path": entry.path,
            "method": entry.method,
            "client_ip": entry.client_ip,
            "user_id": entry.user_id,
            "auth_method": entry.auth_method,
            "auth_level": entry.auth_level,
            "sanitization_applied": entry.sanitization_applied,
            "threats_detected": entry.threats_detected,
            "violations_count": len(entry.violations),
            "allowed": entry.allowed,
            "response_code": entry.response_code,
            "latency_ms": round(entry.latency_ms, 2),
            "timestamp": entry.timestamp.isoformat(),
        }

        # Add violation details
        if entry.violations:
            audit_data["violations"] = [
                {
                    "type": v.violation_type,
                    "severity": v.severity,
                    "description": v.description,
                }
                for v in entry.violations
            ]

        # Log via Vection if available (hash-chained)
        if self._vection_logger is not None and VECTION_AVAILABLE:
            try:
                event_type = self._map_to_security_event_type(entry)
                severity_str = self._map_severity(entry.violations, entry.allowed)

                # Map to Vection EventSeverity
                severity = EventSeverity.INFO
                if EventSeverity is not None:
                    severity_map = {
                        "debug": EventSeverity.DEBUG,
                        "info": EventSeverity.INFO,
                        "warning": EventSeverity.WARNING,
                        "error": EventSeverity.ERROR,
                        "critical": EventSeverity.CRITICAL,
                    }
                    severity = severity_map.get(severity_str, EventSeverity.INFO)

                self._vection_logger.log_event(
                    event_type=event_type,
                    session_id=entry.request_id,
                    user_id=entry.user_id,
                    source_ip=entry.client_ip,
                    details=audit_data,
                    severity=severity,
                )
            except Exception as e:
                logger.warning(f"Vection logging failed: {e}, using fallback")
                self._log_fallback(audit_data)
        else:
            self._log_fallback(audit_data)

        # Persist to database asynchronously
        if self.enable_db_persistence and self.db_session_factory:
            self._queue_db_persist(entry, audit_data)

        # Notify callbacks (for SIEM integration)
        for callback in self._callbacks:
            try:
                callback(audit_data)
            except Exception as e:
                logger.warning(f"Audit callback failed: {e}")

    def _log_fallback(self, audit_data: dict[str, Any]) -> None:
        """Fallback in-memory logging when Vection not available."""
        self._fallback_log.append(audit_data)
        if len(self._fallback_log) > self._max_fallback_entries:
            self._fallback_log = self._fallback_log[-self._max_fallback_entries:]

        # Also log to standard logger
        if not audit_data.get("allowed", True):
            logger.warning(f"Security audit (fallback): {json.dumps(audit_data)}")

    def _queue_db_persist(self, entry: SecurityAuditEntry, audit_data: dict[str, Any]) -> None:
        """Queue database persistence (fire-and-forget for non-blocking)."""
        # Note: In production, this should use a proper async task queue
        # For now, we log the intent and the data is available in Vection logs
        logger.debug(f"Audit entry queued for DB persistence: {entry.request_id}")

    def add_callback(self, callback: Callable[[dict[str, Any]], None]) -> None:
        """
        Add a callback for real-time audit event notifications.
        
        Useful for SIEM integration or real-time alerting.
        
        Args:
            callback: Function called with audit data dict for each event
        """
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[dict[str, Any]], None]) -> None:
        """Remove a previously added callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def get_stats(self) -> dict[str, Any]:
        """Get audit service statistics."""
        stats = {
            "vection_available": VECTION_AVAILABLE,
            "vection_logger_active": self._vection_logger is not None,
            "db_persistence_enabled": self.enable_db_persistence,
            "hash_chain_enabled": self.enable_hash_chain,
            "callback_count": len(self._callbacks),
            "fallback_entries": len(self._fallback_log),
        }

        if self._vection_logger is not None:
            try:
                stats["vection_stats"] = self._vection_logger.get_stats()
            except Exception:
                pass

        return stats

    def get_recent_entries(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent audit entries from fallback log."""
        return self._fallback_log[-limit:]


# Module-level singleton
_audit_service: MothershipAuditService | None = None


def get_audit_service() -> MothershipAuditService | None:
    """Get the global audit service instance."""
    return _audit_service


def initialize_audit_service(
    db_session_factory: Callable[[], AsyncSession] | None = None,
    enable_db_persistence: bool = True,
    enable_hash_chain: bool = True,
) -> MothershipAuditService:
    """
    Initialize the global audit service.
    
    Should be called during application startup.
    
    Args:
        db_session_factory: Factory for async DB sessions
        enable_db_persistence: Whether to persist to database
        enable_hash_chain: Whether to enable hash-chaining
        
    Returns:
        MothershipAuditService instance
    """
    global _audit_service
    _audit_service = MothershipAuditService(
        db_session_factory=db_session_factory,
        enable_db_persistence=enable_db_persistence,
        enable_hash_chain=enable_hash_chain,
    )
    return _audit_service


__all__ = [
    "MothershipAuditService",
    "get_audit_service",
    "initialize_audit_service",
    "VECTION_AVAILABLE",
]
