"""Comprehensive logging and monitoring for rights-preserving boundary enforcement.

Provides:
- Immutable audit trails with cryptographic integrity
- Real-time metrics collection
- Alerting on rights violations
- Performance monitoring
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional
from uuid import uuid4

from api.schema.rights_boundary import (
    AuditLogEntry,
    BoundaryDecision,
    HumanRightsImpact,
    MonitoringMetrics,
    RightsPreservingRequest,
    RiskLevel,
)


class AuditLevel(str, Enum):
    """Audit logging levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    RIGHTS_VIOLATION = "rights_violation"


@dataclass
class AuditChain:
    """Immutable audit chain for tamper-evident logging."""
    entries: list[AuditLogEntry] = field(default_factory=list)
    chain_hash: str = field(default="")

    def add_entry(self, entry: AuditLogEntry) -> None:
        """Add entry with cryptographic chaining."""
        # Compute hash including previous chain hash
        entry_data = json.dumps(entry.dict(), sort_keys=True)
        hash_input = f"{self.chain_hash}:{entry_data}"
        entry.integrity_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
        entry.previous_entry_hash = self.chain_hash if self.chain_hash else None

        self.entries.append(entry)
        self.chain_hash = entry.integrity_hash

    def verify_integrity(self) -> bool:
        """Verify the integrity of the entire chain."""
        previous_hash = ""
        for entry in self.entries:
            entry_data = json.dumps(entry.dict(), sort_keys=True)
            expected_hash = hashlib.sha256(
                f"{previous_hash}:{entry_data}".encode()
            ).hexdigest()[:16]

            if entry.integrity_hash != expected_hash:
                return False
            if entry.previous_entry_hash != previous_hash:
                return False

            previous_hash = entry.integrity_hash

        return True


class RightsPreservingLogger:
    """Logger with built-in human rights violation detection and alerting."""

    def __init__(self, log_dir: Path | None = None, service_name: str = "grid-sovereign-api"):
        self.service_name = service_name
        self.log_dir = log_dir or Path("logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Audit chains per correlation ID
        self.audit_chains: dict[str, AuditChain] = {}

        # Metrics
        self.metrics = MonitoringMetrics()
        self._metrics_history: list[MonitoringMetrics] = []

        # Alert handlers
        self.alert_handlers: list[Callable] = []

        # Setup logging
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure structured logging."""
        self.logger = logging.getLogger(self.service_name)
        self.logger.setLevel(logging.DEBUG)

        # Console handler
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console.setFormatter(formatter)
        self.logger.addHandler(console)

        # File handler for audit logs
        audit_file = logging.FileHandler(self.log_dir / "audit.log")
        audit_file.setLevel(logging.DEBUG)
        audit_formatter = logging.Formatter(
            "%(asctime)s - AUDIT - %(message)s"
        )
        audit_file.setFormatter(audit_formatter)
        self.logger.addHandler(audit_file)

        # Violations log (separate file for security)
        violation_file = logging.FileHandler(self.log_dir / "violations.log")
        violation_file.setLevel(logging.WARNING)
        self.logger.addHandler(violation_file)

    def log_request_received(
        self, request: RightsPreservingRequest
    ) -> AuditLogEntry:
        """Log when a request is received."""
        entry = AuditLogEntry(
            request_id=request.request_id,
            correlation_id=request.correlation_id,
            event_type="request_received",
            event_data={
                "request_type": request.request_type,
                "source_ip": request.source_ip,
                "user_id": self._hash_identifier(request.user_id) if request.user_id else None,
                "declared_purpose": request.declared_purpose,
                "consent_obtained": request.consent_obtained,
            },
            actor_type="user" if request.user_id else "anonymous",
            actor_id=request.user_id,
            service_name=self.service_name,
        )

        self._add_to_audit_chain(request.correlation_id, entry)
        self.logger.info(f"Request received: {request.request_id}")

        # Update metrics
        self.metrics.total_requests += 1
        self.metrics.requests_by_type[request.request_type] = \
            self.metrics.requests_by_type.get(request.request_type, 0) + 1

        return entry

    def log_rights_check(
        self,
        request_id: str,
        correlation_id: str,
        impact: HumanRightsImpact,
        content_preview: str | None = None,
    ) -> AuditLogEntry:
        """Log human rights impact assessment."""
        entry = AuditLogEntry(
            request_id=request_id,
            correlation_id=correlation_id,
            event_type="rights_check",
            event_data={
                "risk_level": impact.risk_level,
                "rights_categories": [r.value for r in impact.rights_categories],
                "potential_harms": impact.potential_harms,
                "mitigation_required": impact.mitigation_required,
                "requires_human_review": impact.requires_human_review,
                "content_preview": content_preview[:100] if content_preview else None,
            },
            actor_type="system",
            service_name=self.service_name,
        )

        self._add_to_audit_chain(correlation_id, entry)

        # Alert on violations
        if impact.risk_level == RiskLevel.VIOLATION:
            self._alert_rights_violation(request_id, impact)
            self.metrics.rights_violations_detected += 1
            self.metrics.violations_by_category[impact.rights_categories[0].value if impact.rights_categories else "unknown"] = \
                self.metrics.violations_by_category.get(
                    impact.rights_categories[0].value if impact.rights_categories else "unknown", 0
                ) + 1
        elif impact.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            self.metrics.high_risk_requests += 1

        if impact.requires_human_review:
            self.metrics.human_reviews_triggered += 1

        return entry

    def log_boundary_decision(
        self,
        decision: BoundaryDecision,
    ) -> AuditLogEntry:
        """Log boundary enforcement decision."""
        entry = AuditLogEntry(
            request_id=decision.request_id,
            correlation_id=str(uuid4())[:12],  # New correlation for decision
            event_type="boundary_decision",
            event_data={
                "decision_id": decision.decision_id,
                "action": decision.action.value,
                "action_reason": decision.action_reason,
                "policy_rules_triggered": decision.policy_rules_triggered,
                "rights_protected": [r.value for r in decision.rights_categories_protected],
                "override_used": decision.override_used,
                "requires_follow_up": decision.requires_follow_up,
            },
            actor_type="system",
            service_name=self.service_name,
        )

        self._add_to_audit_chain(decision.request_id, entry)

        # Update metrics based on action
        if decision.action.value == "allow":
            self.metrics.allowed_requests += 1
        elif decision.action.value == "deny":
            self.metrics.denied_requests += 1
        elif decision.action.value == "quarantine":
            self.metrics.quarantined_requests += 1

        self.logger.info(
            f"Boundary decision: {decision.action.value} for request {decision.request_id}"
        )

        return entry

    def log_processing_complete(
        self,
        request_id: str,
        correlation_id: str,
        processing_time_ms: int,
        success: bool,
        error: str | None = None,
    ) -> AuditLogEntry:
        """Log request processing completion."""
        entry = AuditLogEntry(
            request_id=request_id,
            correlation_id=correlation_id,
            event_type="processing_complete" if success else "processing_error",
            event_data={
                "processing_time_ms": processing_time_ms,
                "success": success,
                "error": error,
            },
            actor_type="system",
            service_name=self.service_name,
        )

        self._add_to_audit_chain(correlation_id, entry)

        # Update performance metrics
        self.metrics.avg_processing_time_ms = (
            (self.metrics.avg_processing_time_ms * (self.metrics.total_requests - 1) + processing_time_ms)
            / self.metrics.total_requests
        )

        return entry

    def log_websocket_event(
        self,
        client_id: str,
        event_type: str,
        message_type: str | None = None,
        status: str | None = None,
        rights_violations: list[str] | None = None,
    ) -> AuditLogEntry:
        """Log WebSocket-related events."""
        correlation_id = str(uuid4())[:12]
        entry = AuditLogEntry(
            request_id=client_id,
            correlation_id=correlation_id,
            event_type=f"websocket_{event_type}",
            event_data={
                "client_id": client_id,
                "message_type": message_type,
                "status": status,
                "rights_violations": rights_violations or [],
            },
            actor_type="system",
            service_name=self.service_name,
        )

        self._add_to_audit_chain(correlation_id, entry)

        if rights_violations:
            self.logger.warning(
                f"WebSocket rights violations from {client_id}: {rights_violations}"
            )

        return entry

    def _add_to_audit_chain(self, correlation_id: str, entry: AuditLogEntry) -> None:
        """Add entry to audit chain for correlation ID."""
        if correlation_id not in self.audit_chains:
            self.audit_chains[correlation_id] = AuditChain()

        self.audit_chains[correlation_id].add_entry(entry)

    def _hash_identifier(self, identifier: str | None) -> str | None:
        """Hash user identifiers for privacy."""
        if not identifier:
            return None
        return hashlib.sha256(identifier.encode()).hexdigest()[:16]

    def _alert_rights_violation(
        self,
        request_id: str,
        impact: HumanRightsImpact,
    ) -> None:
        """Trigger alerts for rights violations."""
        alert_data = {
            "alert_type": "rights_violation",
            "severity": "critical",
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "risk_level": impact.risk_level,
            "rights_violated": [r.value for r in impact.rights_categories],
            "harms": impact.potential_harms,
            "requires_immediate_action": True,
        }

        # Log to violations file
        self.logger.critical(f"RIGHTS VIOLATION: {json.dumps(alert_data)}")

        # Call alert handlers
        for handler in self.alert_handlers:
            try:
                handler(alert_data)
            except Exception as e:
                self.logger.error(f"Alert handler failed: {e}")

    def register_alert_handler(self, handler: Callable) -> None:
        """Register a handler for rights violation alerts."""
        self.alert_handlers.append(handler)

    def get_metrics(self) -> MonitoringMetrics:
        """Get current monitoring metrics."""
        return self.metrics

    def get_audit_chain(self, correlation_id: str) -> AuditChain | None:
        """Get audit chain for a correlation ID."""
        return self.audit_chains.get(correlation_id)

    def verify_audit_integrity(self, correlation_id: str) -> bool:
        """Verify audit chain integrity for a correlation ID."""
        chain = self.audit_chains.get(correlation_id)
        if not chain:
            return False
        return chain.verify_integrity()

    def export_audit_log(self, correlation_id: str, filepath: Path) -> bool:
        """Export audit chain to file."""
        chain = self.audit_chains.get(correlation_id)
        if not chain:
            return False

        try:
            data = {
                "correlation_id": correlation_id,
                "export_timestamp": datetime.utcnow().isoformat(),
                "integrity_verified": chain.verify_integrity(),
                "entries": [entry.dict() for entry in chain.entries],
                "final_chain_hash": chain.chain_hash,
            }

            with open(filepath, "w") as f:
                json.dump(data, f, indent=2, default=str)

            return True
        except Exception as e:
            self.logger.error(f"Failed to export audit log: {e}")
            return False


# Global logger instance
boundary_logger = RightsPreservingLogger()

__all__ = [
    "RightsPreservingLogger",
    "AuditChain",
    "AuditLevel",
    "boundary_logger",
]
