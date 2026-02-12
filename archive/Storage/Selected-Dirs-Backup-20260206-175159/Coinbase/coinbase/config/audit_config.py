"""
Audit Logging Configuration
===========================
Production-ready audit logging with retention policies and log aggregation.

Usage:
    from coinbase.config.audit_config import AuditLogger, AuditConfig

    config = AuditConfig(
        log_dir="logs",
        retention_days=90,
        aggregate_logs=True
    )

    logger = AuditLogger(config)
    logger.log_event("user_login", {"user_id": "123"})
"""

import gzip
import json
import logging
import shutil
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events."""

    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    DATA_ACCESS = "data_access"
    DATA_MODIFY = "data_modify"
    DATA_DELETE = "data_delete"
    API_CALL = "api_call"
    CONFIG_CHANGE = "config_change"
    SECURITY_EVENT = "security_event"
    ERROR = "error"


class AuditSeverity(Enum):
    """Severity levels for audit events."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Single audit event."""

    event_type: AuditEventType
    timestamp: datetime
    user_id: str | None
    details: dict[str, Any]
    severity: AuditSeverity = AuditSeverity.INFO
    ip_address: str | None = None
    session_id: str | None = None
    correlation_id: str | None = None


@dataclass
class AuditConfig:
    """Configuration for audit logging."""

    log_dir: str = "logs/audit"
    retention_days: int = 90
    max_file_size_mb: int = 100
    aggregate_logs: bool = True
    compress_after_days: int = 7
    encryption_enabled: bool = False
    encryption_key: str | None = None
    include_ip_address: bool = True
    include_session_id: bool = True

    def __post_init__(self) -> None:
        if self.retention_days < 1:
            raise ValueError("retention_days must be at least 1")
        if self.max_file_size_mb < 1:
            raise ValueError("max_file_size_mb must be at least 1")


class AuditLogger:
    """
    Production audit logger with rotation, retention, and aggregation.

    Features:
    - Daily log rotation
    - Configurable retention policies
    - Automatic compression of old logs
    - Structured JSON logging
    - Thread-safe operations
    """

    def __init__(self, config: AuditConfig | None = None):
        """
        Initialize audit logger.

        Args:
            config: Audit configuration
        """
        self.config = config or AuditConfig()
        self.log_dir = Path(self.config.log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self._lock = threading.Lock()
        self._current_file: Path | None = None
        self._current_size = 0

        # Initialize current log file
        self._rotate_if_needed()

    def _get_log_file(self, date: datetime | None = None) -> Path:
        """Get log file path for date."""
        date = date or datetime.now()
        filename = f"audit_{date.strftime('%Y%m%d')}.log"
        return self.log_dir / filename

    def _rotate_if_needed(self) -> None:
        """Rotate log file if needed."""
        new_file = self._get_log_file()

        if self._current_file != new_file:
            self._current_file = new_file
            self._current_size = 0

        # Check file size
        if self._current_file.exists():
            self._current_size = self._current_file.stat().st_size

            if self._current_size > self.config.max_file_size_mb * 1024 * 1024:
                # Create numbered backup
                counter = 1
                while True:
                    backup = self._current_file.with_suffix(f".{counter}.log")
                    if not backup.exists():
                        shutil.move(self._current_file, backup)
                        break
                    counter += 1
                self._current_size = 0

    def log_event(
        self,
        event_type: AuditEventType,
        details: dict[str, Any],
        user_id: str | None = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        ip_address: str | None = None,
        session_id: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """
        Log an audit event.

        Args:
            event_type: Type of event
            details: Event details
            user_id: Optional user ID
            severity: Event severity
            ip_address: Optional IP address
            session_id: Optional session ID
            correlation_id: Optional correlation ID
        """
        event = AuditEvent(
            event_type=event_type,
            timestamp=datetime.now(),
            user_id=user_id,
            details=details,
            severity=severity,
            ip_address=ip_address if self.config.include_ip_address else None,
            session_id=session_id if self.config.include_session_id else None,
            correlation_id=correlation_id,
        )

        self._write_event(event)

    def _write_event(self, event: AuditEvent) -> None:
        """Write event to log file."""
        with self._lock:
            self._rotate_if_needed()

            # Serialize event
            log_entry = {
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type.value,
                "severity": event.severity.value,
                "user_id": event.user_id,
                "ip_address": event.ip_address,
                "session_id": event.session_id,
                "correlation_id": event.correlation_id,
                "details": event.details,
            }

            # Remove None values
            log_entry = {k: v for k, v in log_entry.items() if v is not None}

            # Write to file
            if self._current_file:
                with open(self._current_file, "a") as f:
                    f.write(json.dumps(log_entry) + "\n")

            self._current_size += len(json.dumps(log_entry)) + 1

    def cleanup_old_logs(self) -> int:
        """Remove logs older than retention period."""
        cutoff = datetime.now() - timedelta(days=self.config.retention_days)
        removed = 0

        for log_file in self.log_dir.glob("audit_*.log*"):
            # Parse date from filename
            try:
                date_str = log_file.stem.split("_")[1].split(".")[0]
                file_date = datetime.strptime(date_str, "%Y%m%d")

                if file_date < cutoff:
                    log_file.unlink()
                    removed += 1
                    logger.info(f"Removed old audit log: {log_file}")
            except (ValueError, IndexError):
                continue

        return removed

    def compress_old_logs(self) -> None:
        """Compress logs older than compress_after_days."""
        cutoff = datetime.now() - timedelta(days=self.config.compress_after_days)

        for log_file in self.log_dir.glob("audit_*.log"):
            if log_file.suffix == ".gz":
                continue

            try:
                date_str = log_file.stem.split("_")[1].split(".")[0]
                file_date = datetime.strptime(date_str, "%Y%m%d")

                if file_date < cutoff and log_file != self._current_file:
                    compressed = log_file.with_suffix(".log.gz")
                    with open(log_file, "rb") as f_in:
                        with gzip.open(compressed, "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    log_file.unlink()
                    logger.info(f"Compressed audit log: {log_file} -> {compressed}")
            except (ValueError, IndexError):
                continue

    def get_logs(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        event_type: AuditEventType | None = None,
        user_id: str | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """
        Query audit logs with filters.

        Args:
            start_date: Filter events after this date
            end_date: Filter events before this date
            event_type: Filter by event type
            user_id: Filter by user ID
            limit: Maximum number of events to return

        Returns:
            List of matching log entries
        """
        results = []

        for log_file in sorted(self.log_dir.glob("audit_*.log*"), reverse=True):
            # Check if file is within date range
            try:
                date_str = log_file.stem.split("_")[1].split(".")[0]
                file_date = datetime.strptime(date_str, "%Y%m%d")

                if start_date and file_date < start_date:
                    continue
                if end_date and file_date > end_date:
                    continue
            except (ValueError, IndexError):
                continue

            # Read log file
            if log_file.suffix == ".gz":
                opener: Any = gzip.open  # type: ignore
            else:
                opener: Any = open  # type: ignore

            with opener(log_file, "rt") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())

                        # Apply filters
                        if event_type and entry.get("event_type") != event_type.value:
                            continue
                        if user_id and entry.get("user_id") != user_id:
                            continue

                        results.append(entry)

                        if len(results) >= limit:
                            return results
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        logger.error(f"Error reading {log_file}: {e}")

        return results

    def generate_summary(self, days: int = 7) -> dict[str, Any]:
        """
        Generate audit log summary.

        Args:
            days: Number of days to include

        Returns:
            Summary statistics
        """
        start_date = datetime.now() - timedelta(days=days)
        logs = self.get_logs(start_date=start_date, limit=100000)

        summary: dict[str, Any] = {
            "period_days": days,
            "total_events": len(logs),
            "events_by_type": {},
            "events_by_severity": {},
            "unique_users": set(),
            "date_range": {"start": start_date.isoformat(), "end": datetime.now().isoformat()},
        }

        for log in logs:
            event_type = log.get("event_type", "unknown")
            severity = log.get("severity", "unknown")
            user_id = log.get("user_id")

            summary["events_by_type"][event_type] = summary["events_by_type"].get(event_type, 0) + 1
            summary["events_by_severity"][severity] = (
                summary["events_by_severity"].get(severity, 0) + 1
            )

            if user_id:
                summary["unique_users"].add(user_id)

        summary["unique_users"] = len(summary["unique_users"])

        return summary


# Global audit logger instance
_global_audit_logger: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance."""
    global _global_audit_logger
    if _global_audit_logger is None:
        _global_audit_logger = AuditLogger()
    return _global_audit_logger


def configure_audit_logging(config: AuditConfig) -> AuditLogger:
    """
    Configure global audit logger.

    Args:
        config: Audit configuration

    Returns:
        Configured AuditLogger instance
    """
    global _global_audit_logger
    _global_audit_logger = AuditLogger(config)
    return _global_audit_logger


# Convenience functions
def log_audit_event(event_type: AuditEventType, details: dict[str, Any], **kwargs: Any) -> None:
    """Quick function to log an audit event."""
    logger = get_audit_logger()
    logger.log_event(event_type, details, **kwargs)
