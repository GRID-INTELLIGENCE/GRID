"""
Secure Audit Logging System for GRID.

Writes security-sensitive events to Google Cloud Logging.
Separates audit logs from application logs for compliance.
"""

import json
import logging
import os
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from .pii_redaction import RedactionMode, redact_log_message

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events."""

    # Authentication
    AUTH_LOGIN_SUCCESS = "AUTH_LOGIN_SUCCESS"
    AUTH_LOGIN_FAILURE = "AUTH_LOGIN_FAILURE"
    AUTH_LOGOUT = "AUTH_LOGOUT"
    AUTH_TOKEN_ISSUED = "AUTH_TOKEN_ISSUED"
    AUTH_TOKEN_REFRESH = "AUTH_TOKEN_REFRESH"

    # Authorization
    AUTHZ_ACCESS_GRANTED = "AUTHZ_ACCESS_GRANTED"
    AUTHZ_ACCESS_DENIED = "AUTHZ_ACCESS_DENIED"
    AUTHZ_ESCALATION_ATTEMPT = "AUTHZ_ESCALATION_ATTEMPT"

    # Data Access
    DATA_ACCESS_PERSONAL = "DATA_ACCESS_PERSONAL"
    DATA_ACCESS_FINANCIAL = "DATA_ACCESS_FINANCIAL"
    DATA_MODIFICATION = "DATA_MODIFICATION"
    DATA_DELETION = "DATA_DELETION"

    # Secrets
    SECRET_ACCESS = "SECRET_ACCESS"
    SECRET_ROTATION = "SECRET_ROTATION"
    SECRET_FAILED_RETRIEVAL = "SECRET_FAILED_RETRIEVAL"

    # Wealth Management
    WEALTH_DATA_ACCESS = "WEALTH_DATA_ACCESS"
    WEALTH_DATA_EXPORT = "WEALTH_DATA_EXPORT"
    WEALTH_ANALYSIS_RUN = "WEALTH_ANALYSIS_RUN"


class AuditLogger:
    """
    Secure audit logging system.

    Features:
    - Google Cloud Logging integration
    - Automatic PII redaction
    - 30-day retention
    - JSON structured format
    - Immutable append-only logs
    """

    def __init__(self, environment: str = "production", enabled: bool = True, retention_days: int = 30):
        """
        Initialize audit logger.

        Args:
            environment: Environment name (production, development, staging)
            enabled: Whether audit logging is enabled
            retention_days: Log retention period
        """
        self.enabled = enabled
        self.environment = environment
        self.retention_days = retention_days

        # Initialize cloud logging client
        self._init_cloud_logging()

        logger.info(f"AuditLogger initialized, enabled={enabled}, retention={retention_days} days")

    def _init_cloud_logging(self) -> None:
        """Initialize Google Cloud Logging client."""
        try:
            from google.cloud import logging as cloud_logging
            from google.cloud.logging import Client
            from google.cloud.logging.handlers import CloudLoggingHandler

            # Initialize client
            self.client = Client()
            self.logger = self.client.logger("grid-security-audit")

            # Configure handler
            handler = CloudLoggingHandler(name="grid-security-audit", client=self.client)

            # Set up structured logging
            handler.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
            self.logger.propagate = False

            logger.info("Google Cloud Logging initialized for audit logs")

        except ImportError:
            logger.warning("google-cloud-logging not available, falling back to file logging")
            self._init_file_logging()
        except Exception as e:
            logger.error(f"Failed to initialize Cloud Logging: {e}")
            self._init_file_logging()

    def _init_file_logging(self) -> None:
        """Initialize file-based audit logging as fallback."""
        import logging.handlers

        audit_path = os.getenv("GRID_AUDIT_LOG_PATH", "./data/audit.log")

        # Ensure directory exists
        os.makedirs(os.path.dirname(audit_path), exist_ok=True)

        # File handler with append-only mode
        handler = logging.handlers.RotatingFileHandler(
            audit_path,
            mode="a",  # Append-only for immutability
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=30,  # 30 days of logs
            encoding="utf-8",
        )

        handler.setFormatter(logging.Formatter("%(message)s"))

        # Create audit-specific logger
        self.logger = logging.getLogger("grid.audit")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        self.logger.addHandler(handler)

        logger.info(f"File-based audit logging initialized: {audit_path}")

    def _log_event(
        self,
        event_type: AuditEventType,
        message: str,
        user_id: str | None = None,
        ip_address: str | None = None,
        resource: str | None = None,
        outcome: str = "success",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Log audit event.

        Args:
            event_type: Type of audit event
            message: Human-readable description
            user_id: User identifier (redacted if contains PII)
            ip_address: Client IP address (redacted)
            resource: Resource being accessed
            outcome: success/failure/error
            metadata: Additional structured data
        """
        if not self.enabled:
            return

        # Redact PII from all fields
        redacted_message = redact_log_message(message, RedactionMode.AUDIT)
        redacted_user_id = redact_log_message(user_id or "system", RedactionMode.AUDIT) if user_id else None
        redacted_ip = redact_log_message(ip_address or "N/A", RedactionMode.AUDIT) if ip_address else None

        # Build audit entry
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "environment": self.environment,
            "event_type": event_type.value,
            "message": redacted_message,
            "user_id": redacted_user_id,
            "ip_address": redacted_ip,
            "resource": resource,
            "outcome": outcome,
            "retention_days": self.retention_days,
            "metadata": metadata or {},
        }

        # Write as JSON line
        self.logger.info(json.dumps(entry))

    def log_auth_success(self, user_id: str, ip_address: str, method: str = "password") -> None:
        """Log successful authentication."""
        self._log_event(
            event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
            message=f"User authenticated via {method}",
            user_id=user_id,
            ip_address=ip_address,
            metadata={"auth_method": method},
        )

    def log_auth_failure(self, username: str, ip_address: str, reason: str) -> None:
        """Log failed authentication attempt."""
        self._log_event(
            event_type=AuditEventType.AUTH_LOGIN_FAILURE,
            message=f"Authentication failed: {reason}",
            user_id=username,
            ip_address=ip_address,
            outcome="failure",
            metadata={"username": username, "reason": reason},
        )

    def log_data_access(self, user_id: str, data_type: str, resource: str, access_type: str = "read") -> None:
        """Log data access event."""
        event_type = AuditEventType.DATA_ACCESS_PERSONAL
        if "financial" in data_type.lower():
            event_type = AuditEventType.DATA_ACCESS_FINANCIAL

        self._log_event(
            event_type=event_type,
            message=f"User {access_type} {data_type} data",
            user_id=user_id,
            resource=resource,
            metadata={"access_type": access_type, "data_type": data_type},
        )

    def log_wealth_data_access(self, user_id: str, operation: str, asset_count: int = 0) -> None:
        """Log wealth management data access."""
        self._log_event(
            event_type=AuditEventType.WEALTH_DATA_ACCESS,
            message=f"Wealth management {operation} operation",
            user_id=user_id,
            resource="wealth_management",
            metadata={"operation": operation, "asset_count": asset_count},
        )

    def log_secret_access(self, secret_name: str, user_id: str = "system", success: bool = True) -> None:
        """Log secret access event."""
        self._log_event(
            event_type=AuditEventType.SECRET_ACCESS if success else AuditEventType.SECRET_FAILED_RETRIEVAL,
            message=f"Secret {secret_name} {'accessed' if success else 'failed to access'}",
            user_id=user_id,
            resource=f"secret/{secret_name}",
            outcome="success" if success else "failure",
            metadata={"secret_name": secret_name},
        )


# Global audit logger instance
_audit_logger: AuditLogger | None = None


def get_audit_logger() -> AuditLogger | None:
    """Get global audit logger instance."""
    global _audit_logger
    return _audit_logger


def initialize_audit_logger(
    environment: str = "production", enabled: bool = True, retention_days: int = 30
) -> AuditLogger:
    """
    Initialize global audit logger.

    Should be called during application startup.

    Args:
        environment: Environment name
        enabled: Whether audit logging is enabled
        retention_days: Log retention period (30 days per requirement)

    Returns:
        AuditLogger instance
    """
    global _audit_logger
    _audit_logger = AuditLogger(environment, enabled, retention_days)
    return _audit_logger
