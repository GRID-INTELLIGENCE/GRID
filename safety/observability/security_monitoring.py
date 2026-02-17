#!/usr/bin/env python3
"""
Security Monitoring and Audit System
Provides comprehensive security event logging, audit trails, and real-time monitoring.
"""

import json
import logging
import os
import queue
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Any, Callable

import httpx

logger = logging.getLogger(__name__)


class SecurityEventType(StrEnum):
    """Types of security events to monitor"""

    # Authentication events
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    AUTH_BLOCKED = "auth_blocked"

    # Rate limiting events
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    IP_BLOCKED = "ip_blocked"
    BACKOFF_TRIGGERED = "backoff_triggered"

    # Input validation events
    INPUT_VALIDATION_FAILED = "input_validation_failed"
    MALICIOUS_INPUT_DETECTED = "malicious_input_detected"
    PROMPT_INJECTION_ATTEMPT = "prompt_injection_attempt"

    # AI security events
    AI_INPUT_BLOCKED = "ai_input_blocked"
    AI_OUTPUT_SANITIZED = "ai_output_sanitized"
    AI_MODEL_VIOLATION = "ai_model_violation"

    # Database security events
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    DATABASE_CONNECTION_BLOCKED = "database_connection_blocked"
    QUERY_SANITIZATION = "query_sanitization"

    # System security events
    ANOMALOUS_ACTIVITY = "anomalous_activity"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    SECURITY_POLICY_VIOLATION = "security_policy_violation"

    # Audit events
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_UPDATE = "security_update"
    AUDIT_LOG_ACCESS = "audit_log_access"


class SecurityEventSeverity(StrEnum):
    """Severity levels for security events"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """Security event record"""

    event_id: str
    timestamp: str
    event_type: SecurityEventType
    severity: SecurityEventSeverity
    source: str  # Component that generated the event
    user_id: str | None
    ip_address: str | None
    session_id: str | None
    details: dict[str, Any]
    risk_score: float = 0.0
    mitigation_action: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data["event_type"] = self.event_type.value
        data["severity"] = self.severity.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SecurityEvent":
        """Create from dictionary"""
        data["event_type"] = SecurityEventType(data["event_type"])
        data["severity"] = SecurityEventSeverity(data["severity"])
        return cls(**data)


class SecurityLogger:
    """Enhanced security event logger with audit trails"""

    def __init__(self, log_dir: str | None = None, max_events_in_memory: int = 10000):
        self.log_dir = Path(log_dir or "logs/security")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # In-memory event buffer for real-time monitoring
        self.event_buffer = deque(maxlen=max_events_in_memory)
        self.event_listeners: list[Callable[[SecurityEvent], None]] = []

        # Statistics
        self.stats = defaultdict(int)
        self.severity_counts = defaultdict(int)

        # File rotation settings
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.max_files = 30

        # Background writer thread
        self._write_queue: queue.Queue[SecurityEvent] = queue.Queue(maxsize=50000)
        self._stop_writer = threading.Event()
        self._writer_thread = threading.Thread(target=self._writer_loop, name="SecurityLoggerWriter", daemon=True)
        self._writer_thread.start()

    def _writer_loop(self):
        """Background thread to handle blocking file I/O."""
        while not self._stop_writer.is_set() or not self._write_queue.empty():
            try:
                # Use a small timeout to allow checking stop_writer event
                event = self._write_queue.get(timeout=1.0)
                self._write_to_file_blocking(event)
                self._write_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                # Fallback to stderr if logging fails to prevent complete loss
                print(f"CRITICAL: SecurityLogger writer error: {e}")

    def shutdown(self, timeout: float = 10.0):
        """Shut down the writer thread gracefully."""
        self._stop_writer.set()
        if self._writer_thread.is_alive():
            self._writer_thread.join(timeout=timeout)

    def log_event(self, event: SecurityEvent) -> None:
        """Log a security event (non-blocking)."""
        # Add to in-memory buffer
        self.event_buffer.append(event)

        # Update statistics
        self.stats[event.event_type.value] += 1
        self.severity_counts[event.severity.value] += 1

        # Queue for background write (non-blocking)
        try:
            self._write_queue.put_nowait(event)
        except queue.Full:
            # Fallback to immediate log to avoid losing event
            logger.error("security_log_queue_full", extra={"event_id": event.event_id})

        # Notify listeners
        for listener in self.event_listeners:
            try:
                listener(event)
            except Exception as e:
                logger.error(f"Error in security event listener: {e}")

        # Log critical events immediately
        if event.severity in [SecurityEventSeverity.HIGH, SecurityEventSeverity.CRITICAL]:
            logger.warning(
                f"CRITICAL SECURITY EVENT: {event.event_type.value} "
                f"(severity: {event.severity.value}, risk: {event.risk_score:.2f})"
            )

    def add_listener(self, listener: Callable[[SecurityEvent], None]) -> None:
        """Add an event listener"""
        self.event_listeners.append(listener)

    def remove_listener(self, listener: Callable[[SecurityEvent], None]) -> None:
        """Remove an event listener"""
        if listener in self.event_listeners:
            self.event_listeners.remove(listener)

    def _write_to_file_blocking(self, event: SecurityEvent) -> None:
        """Internal method to write event to log file (blocking)."""
        date_str = datetime.now().strftime("%Y%m%d")
        log_file = self.log_dir / f"security_{date_str}.jsonl"

        # Check if rotation needed
        if log_file.exists() and log_file.stat().st_size > self.max_file_size:
            self._rotate_file(log_file)

        # Write event
        with open(log_file, "a", encoding="utf-8") as f:
            json.dump(event.to_dict(), f, ensure_ascii=False)
            f.write("\n")

    def _rotate_file(self, log_file: Path) -> None:
        """Rotate log file"""
        base_name = log_file.stem
        extension = log_file.suffix

        # Remove oldest file if at limit
        oldest_file = self.log_dir / f"{base_name}.{self.max_files}{extension}"
        if oldest_file.exists():
            oldest_file.unlink()

        # Rotate existing files
        for i in range(self.max_files - 1, 0, -1):
            old_file = self.log_dir / f"{base_name}.{i}{extension}"
            new_file = self.log_dir / f"{base_name}.{i + 1}{extension}"
            if old_file.exists():
                old_file.rename(new_file)

        # Rotate current file
        rotated_file = self.log_dir / f"{base_name}.1{extension}"
        log_file.rename(rotated_file)

    def get_recent_events(
        self,
        limit: int = 100,
        event_type: SecurityEventType | None = None,
        severity: SecurityEventSeverity | None = None,
        user_id: str | None = None,
    ) -> list[SecurityEvent]:
        """Get recent events with optional filtering"""
        events = list(self.event_buffer)

        # Apply filters
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if severity:
            events = [e for e in events if e.severity == severity]
        if user_id:
            events = [e for e in events if e.user_id == user_id]

        return events[-limit:]

    def get_statistics(self) -> dict[str, Any]:
        """Get security event statistics"""
        return {
            "total_events": len(self.event_buffer),
            "event_counts": dict(self.stats),
            "severity_counts": dict(self.severity_counts),
            "buffer_size": len(self.event_buffer),
            "max_buffer_size": self.event_buffer.maxlen,
        }

    def get_stats(self) -> dict[str, Any]:
        """Alias for get_statistics() - for backwards compatibility"""
        return self.get_statistics()

    def search_events(
        self,
        query: dict[str, Any],
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 1000,
    ) -> list[SecurityEvent]:
        """Search events in log files"""
        # Search through recent buffer first
        matching_events = [event for event in self.event_buffer if self._matches_query(event, query)]

        # Search through log files if needed
        if len(matching_events) < limit:
            date_range = self._get_date_range(start_date, end_date)
            for date_str in date_range:
                log_file = self.log_dir / f"security_{date_str}.jsonl"
                if log_file.exists():
                    matching_events.extend(self._search_file(log_file, query, limit - len(matching_events)))
                    if len(matching_events) >= limit:
                        break

        return matching_events[:limit]

    def _matches_query(self, event: SecurityEvent, query: dict[str, Any]) -> bool:
        """Check if event matches search query"""
        for key, value in query.items():
            event_value = getattr(event, key, None)
            if event_value != value:
                # Check in details dict
                if (
                    key not in ["event_type", "severity", "source", "user_id", "ip_address"]
                    and event.details.get(key) != value
                ):
                    return False
        return True

    def _get_date_range(self, start_date: datetime | None, end_date: datetime | None) -> list[str]:
        """Get date range for log file search"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=7)
        if not end_date:
            end_date = datetime.now()

        dates = []
        current = start_date
        while current <= end_date:
            dates.append(current.strftime("%Y%m%d"))
            current += timedelta(days=1)
        return dates

    def _search_file(self, log_file: Path, query: dict[str, Any], max_results: int) -> list[SecurityEvent]:
        """Search a single log file"""
        results = []
        try:
            with open(log_file, encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        event = SecurityEvent.from_dict(data)
                        if self._matches_query(event, query):
                            results.append(event)
                            if len(results) >= max_results:
                                break
                    except (json.JSONDecodeError, TypeError):
                        continue
        except Exception as e:
            logger.error(f"Error searching log file {log_file}: {e}")

        return results


class RealTimeMonitor:
    """Real-time security monitoring and alerting"""

    def __init__(self, security_logger: SecurityLogger):
        self.security_logger = security_logger
        self.alert_thresholds = {
            SecurityEventSeverity.CRITICAL: 1,  # Alert on any critical event
            SecurityEventSeverity.HIGH: 5,  # Alert if 5+ high severity in window
            SecurityEventSeverity.MEDIUM: 20,  # Alert if 20+ medium severity in window
        }
        self.monitoring_window = timedelta(minutes=5)
        self.alert_cooldown = timedelta(minutes=10)  # Prevent alert spam

        self.last_alert_time = defaultdict(lambda: datetime.min)
        self.event_counts = defaultdict(lambda: defaultdict(int))

        # Monitoring thread with interruptible sleep
        self._stop_monitoring = threading.Event()
        self.monitor_thread: threading.Thread | None = None

    def start_monitoring(self) -> None:
        """Start real-time monitoring"""
        if self.monitor_thread is not None and self.monitor_thread.is_alive():
            return

        self._stop_monitoring.clear()
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Security monitoring started")

    def stop_monitoring(self) -> None:
        """Stop real-time monitoring (interruptible — returns within ~2s)."""
        self._stop_monitoring.set()
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        logger.info("Security monitoring stopped")

    def _monitoring_loop(self) -> None:
        """Main monitoring loop with interruptible sleep."""
        while not self._stop_monitoring.is_set():
            try:
                self._check_alerts()
                self._cleanup_old_counts()
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
            # Interruptible sleep — returns immediately when stop is set
            self._stop_monitoring.wait(30)

    def _check_alerts(self) -> None:
        """Check if any alert thresholds have been exceeded"""
        now = datetime.now()
        cutoff = now - self.monitoring_window

        # Count events in monitoring window — iterate newest-first and stop early
        window_counts = defaultdict(int)
        for event in reversed(self.security_logger.event_buffer):
            try:
                event_time = datetime.fromisoformat(event.timestamp)
            except (ValueError, TypeError):
                continue
            if event_time < cutoff:
                break  # All remaining events are older — done
            window_counts[event.severity] += 1

        # Check thresholds
        for severity, threshold in self.alert_thresholds.items():
            count = window_counts.get(severity, 0)
            if count >= threshold:
                last_alert = self.last_alert_time[severity]
                if now - last_alert >= self.alert_cooldown:
                    self._trigger_alert(severity, count)
                    self.last_alert_time[severity] = now

    def _trigger_alert(self, severity: SecurityEventSeverity, count: int) -> None:
        """Trigger a security alert"""
        minutes = self.monitoring_window.total_seconds() / 60
        alert_msg = f"SECURITY ALERT: {count} {severity.value} severity events in {minutes:.0f} minutes"

        # Log the alert
        alert_event = SecurityEvent(
            event_id=f"alert_{int(time.time())}",
            timestamp=datetime.now().isoformat(),
            event_type=SecurityEventType.ANOMALOUS_ACTIVITY,
            severity=SecurityEventSeverity.HIGH,
            source="security_monitor",
            user_id=None,
            ip_address=None,
            session_id=None,
            details={
                "alert_type": "threshold_exceeded",
                "severity": severity.value,
                "event_count": count,
                "time_window_minutes": self.monitoring_window.total_seconds() / 60,
            },
            risk_score=0.9,
        )

        self.security_logger.log_event(alert_event)

        # Send external alerts via configured webhook
        self._send_webhook_alert(severity, count, alert_msg)
        logger.critical(alert_msg)

    def _send_webhook_alert(self, severity: SecurityEventSeverity, count: int, message: str) -> None:
        """Send alert to configured webhook endpoint."""
        webhook_url = os.getenv("SECURITY_ALERT_WEBHOOK_URL", "")
        if not webhook_url:
            return

        payload = {
            "alert": "security_threshold_exceeded",
            "severity": severity.value,
            "event_count": count,
            "message": message,
            "window_minutes": self.monitoring_window.total_seconds() / 60,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # Fire and forget in a daemon thread to avoid blocking the monitor loop
            def send():
                try:
                    with httpx.Client(timeout=2.0) as client:
                        resp = client.post(webhook_url, json=payload)
                        resp.raise_for_status()
                except Exception as e:
                    logger.error(f"Webhook delivery failed: {e}")

            threading.Thread(target=send, daemon=True).start()
        except Exception as e:
            logger.error(f"Failed to start security alert webhook thread: {e}")

    def _cleanup_old_counts(self) -> None:
        """Clean up old event counts"""
        cutoff = datetime.now() - self.monitoring_window
        for severity_counts in self.event_counts.values():
            # Remove entries older than monitoring window
            to_remove = [k for k, v in severity_counts.items() if k < cutoff]
            for key in to_remove:
                del severity_counts[key]


class SecurityAudit:
    """Security audit trail and compliance reporting"""

    def __init__(self, security_logger: SecurityLogger):
        self.security_logger = security_logger

    def generate_audit_report(
        self, start_date: datetime, end_date: datetime, include_details: bool = False
    ) -> dict[str, Any]:
        """Generate comprehensive security audit report"""
        events = self.security_logger.search_events(
            query={},
            start_date=start_date,
            end_date=end_date,
            limit=50000,  # Large limit for audit
        )

        # Analyze events
        event_summary = defaultdict(int)
        severity_summary = defaultdict(int)
        user_activity = defaultdict(lambda: defaultdict(int))
        ip_activity = defaultdict(lambda: defaultdict(int))

        for event in events:
            event_summary[event.event_type.value] += 1
            severity_summary[event.severity.value] += 1

            if event.user_id:
                user_activity[event.user_id][event.event_type.value] += 1

            if event.ip_address:
                ip_activity[event.ip_address][event.event_type.value] += 1

        # Identify high-risk users and IPs
        high_risk_users = self._identify_high_risk_entities({k: dict(v) for k, v in user_activity.items()})
        high_risk_ips = self._identify_high_risk_entities({k: dict(v) for k, v in ip_activity.items()})

        return {
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_events": len(events),
            },
            "event_summary": dict(event_summary),
            "severity_summary": dict(severity_summary),
            "high_risk_users": high_risk_users,
            "high_risk_ips": high_risk_ips,
            "recommendations": self._generate_recommendations(events),
            "events": [event.to_dict() for event in events] if include_details else [],
        }

    def _identify_high_risk_entities(
        self, activity_dict: dict[str, dict[str, int]] | defaultdict[str, defaultdict[str, int]]
    ) -> list[dict[str, Any]]:
        """Identify high-risk users/IPs based on activity patterns"""
        high_risk = []

        for entity_id, activities in activity_dict.items():
            risk_score = 0
            total_events = sum(activities.values())

            # Risk scoring based on event types
            risk_weights = {
                SecurityEventType.SQL_INJECTION_ATTEMPT.value: 10,
                SecurityEventType.PROMPT_INJECTION_ATTEMPT.value: 8,
                SecurityEventType.AUTH_FAILURE.value: 5,
                SecurityEventType.RATE_LIMIT_EXCEEDED.value: 3,
                SecurityEventType.INPUT_VALIDATION_FAILED.value: 2,
            }

            for event_type, count in activities.items():
                risk_score += risk_weights.get(event_type, 1) * count

            # Normalize by total events and apply threshold
            normalized_risk = risk_score / max(total_events, 1)
            if normalized_risk >= 5.0:  # High risk threshold
                high_risk.append(
                    {
                        "entity_id": entity_id,
                        "total_events": total_events,
                        "risk_score": normalized_risk,
                        "activities": activities,
                    }
                )

        return sorted(high_risk, key=lambda x: x["risk_score"], reverse=True)

    def _generate_recommendations(self, events: list[SecurityEvent]) -> list[str]:
        """Generate security recommendations based on event analysis"""
        recommendations = []

        # Analyze patterns
        auth_failures = sum(1 for e in events if e.event_type == SecurityEventType.AUTH_FAILURE)
        rate_limits = sum(1 for e in events if e.event_type == SecurityEventType.RATE_LIMIT_EXCEEDED)
        injections = sum(1 for e in events if "injection" in e.event_type.value)

        if auth_failures > 10:
            recommendations.append("Consider implementing stricter authentication policies")

        if rate_limits > 50:
            recommendations.append("Review rate limiting configuration - may need tightening")

        if injections > 5:
            recommendations.append("Strengthen input validation and sanitization")

        if len(events) > 1000:
            recommendations.append("High event volume detected - consider increasing monitoring resources")

        return recommendations


# Global security monitoring instance
security_logger = SecurityLogger()
security_monitor = RealTimeMonitor(security_logger)
security_audit = SecurityAudit(security_logger)
