"""
Mothership Cockpit Domain Models.

Core domain models representing cockpit state, sessions, operations,
and system components. Uses dataclasses for clean, Pythonic design
with full type annotations.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timezone
from enum import Enum, StrEnum
from typing import Any

# =============================================================================
# Enumerations
# =============================================================================


class SessionStatus(StrEnum):
    """Session lifecycle states."""

    INITIALIZING = "initializing"
    ACTIVE = "active"
    IDLE = "idle"
    SUSPENDED = "suspended"
    TERMINATING = "terminating"
    TERMINATED = "terminated"


class OperationStatus(StrEnum):
    """Operation execution states."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class OperationType(StrEnum):
    """Types of cockpit operations."""

    SYSTEM_CHECK = "system_check"
    INTEGRATION_SYNC = "integration_sync"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    CONFIGURATION_UPDATE = "configuration_update"
    DIAGNOSTIC = "diagnostic"
    MAINTENANCE = "maintenance"
    BACKUP = "backup"
    RESTORE = "restore"
    DEPLOYMENT = "deployment"
    CUSTOM = "custom"


class SystemState(StrEnum):
    """Overall system states."""

    OFFLINE = "offline"
    STARTING = "starting"
    ONLINE = "online"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    SHUTDOWN = "shutdown"
    ERROR = "error"


class ComponentHealth(StrEnum):
    """Health status for system components."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class AlertSeverity(StrEnum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Priority(int, Enum):
    """Operation priority levels."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


# =============================================================================
# Utility Functions
# =============================================================================


def generate_id(prefix: str = "") -> str:
    """Generate a unique identifier with optional prefix."""
    uid = uuid.uuid4().hex[:12]
    return f"{prefix}_{uid}" if prefix else uid


def utc_now() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(UTC)


# =============================================================================
# Core Domain Models
# =============================================================================


@dataclass
class Session:
    """
    Represents a user session in the Mothership Cockpit.

    Sessions track user connections, activity, and associated resources.
    """

    id: str = field(default_factory=lambda: generate_id("session"))
    user_id: str = ""
    status: SessionStatus = SessionStatus.INITIALIZING
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    expires_at: datetime | None = None
    last_activity_at: datetime | None = None

    # Connection info
    client_ip: str | None = None
    user_agent: str | None = None
    connection_type: str = "http"  # http, websocket

    # Session data
    metadata: dict[str, Any] = field(default_factory=dict)
    permissions: set[str] = field(default_factory=set)
    active_operations: list[str] = field(default_factory=list)

    def is_active(self) -> bool:
        """Check if session is currently active."""
        return self.status in {SessionStatus.ACTIVE, SessionStatus.IDLE}

    def is_expired(self) -> bool:
        """Check if session has expired."""
        if self.expires_at is None:
            return False
        return utc_now() > self.expires_at

    def touch(self) -> None:
        """Update last activity timestamp."""
        self.last_activity_at = utc_now()
        self.updated_at = utc_now()
        if self.status == SessionStatus.IDLE:
            self.status = SessionStatus.ACTIVE

    def suspend(self) -> None:
        """Suspend the session."""
        self.status = SessionStatus.SUSPENDED
        self.updated_at = utc_now()

    def terminate(self) -> None:
        """Terminate the session."""
        self.status = SessionStatus.TERMINATED
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        """Serialize session to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_activity_at": (self.last_activity_at.isoformat() if self.last_activity_at else None),
            "connection_type": self.connection_type,
            "is_active": self.is_active(),
            "is_expired": self.is_expired(),
        }


@dataclass
class Operation:
    """
    Represents an operation or task in the Mothership Cockpit.

    Operations are discrete units of work that can be tracked,
    paused, resumed, or cancelled.
    """

    id: str = field(default_factory=lambda: generate_id("op"))
    type: OperationType = OperationType.CUSTOM
    name: str = ""
    description: str = ""
    status: OperationStatus = OperationStatus.PENDING
    priority: Priority = Priority.NORMAL

    # Timestamps
    created_at: datetime = field(default_factory=utc_now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    updated_at: datetime = field(default_factory=utc_now)

    # Ownership
    session_id: str | None = None
    user_id: str | None = None
    parent_operation_id: str | None = None

    # Progress tracking
    progress_percent: float = 0.0
    progress_message: str = ""
    steps_total: int = 0
    steps_completed: int = 0

    # Input/Output
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: dict[str, Any] = field(default_factory=dict)

    # Error handling
    error_message: str | None = None
    error_details: dict[str, Any] | None = None
    retry_count: int = 0
    max_retries: int = 3

    # Metadata
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def start(self) -> None:
        """Mark operation as started."""
        self.status = OperationStatus.RUNNING
        self.started_at = utc_now()
        self.updated_at = utc_now()

    def complete(self, output: dict[str, Any] | None = None) -> None:
        """Mark operation as completed."""
        self.status = OperationStatus.COMPLETED
        self.completed_at = utc_now()
        self.updated_at = utc_now()
        self.progress_percent = 100.0
        if output:
            self.output_data = output

    def fail(self, error: str, details: dict[str, Any] | None = None) -> None:
        """Mark operation as failed."""
        self.status = OperationStatus.FAILED
        self.completed_at = utc_now()
        self.updated_at = utc_now()
        self.error_message = error
        self.error_details = details

    def cancel(self) -> None:
        """Cancel the operation."""
        self.status = OperationStatus.CANCELLED
        self.completed_at = utc_now()
        self.updated_at = utc_now()

    def pause(self) -> None:
        """Pause the operation."""
        self.status = OperationStatus.PAUSED
        self.updated_at = utc_now()

    def resume(self) -> None:
        """Resume a paused operation."""
        if self.status == OperationStatus.PAUSED:
            self.status = OperationStatus.RUNNING
            self.updated_at = utc_now()

    def update_progress(
        self,
        percent: float | None = None,
        message: str | None = None,
        step: int | None = None,
    ) -> None:
        """Update operation progress."""
        if percent is not None:
            self.progress_percent = min(100.0, max(0.0, percent))
        if message is not None:
            self.progress_message = message
        if step is not None:
            self.steps_completed = step
            if self.steps_total > 0:
                self.progress_percent = (step / self.steps_total) * 100.0
        self.updated_at = utc_now()

    def can_retry(self) -> bool:
        """Check if operation can be retried."""
        return self.status == OperationStatus.FAILED and self.retry_count < self.max_retries

    def is_terminal(self) -> bool:
        """Check if operation is in a terminal state."""
        return self.status in {
            OperationStatus.COMPLETED,
            OperationStatus.FAILED,
            OperationStatus.CANCELLED,
            OperationStatus.TIMEOUT,
        }

    @property
    def duration_seconds(self) -> float | None:
        """Calculate operation duration in seconds."""
        if self.started_at is None:
            return None
        end_time = self.completed_at or utc_now()
        return (end_time - self.started_at).total_seconds()

    def to_dict(self) -> dict[str, Any]:
        """Serialize operation to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (self.completed_at.isoformat() if self.completed_at else None),
            "progress_percent": self.progress_percent,
            "progress_message": self.progress_message,
            "steps_total": self.steps_total,
            "steps_completed": self.steps_completed,
            "error_message": self.error_message,
            "duration_seconds": self.duration_seconds,
            "is_terminal": self.is_terminal(),
            "tags": self.tags,
        }


@dataclass
class Component:
    """
    Represents a system component in the Mothership Cockpit.

    Components are individual services or subsystems that can be
    monitored and managed.
    """

    id: str = field(default_factory=lambda: generate_id("comp"))
    name: str = ""
    type: str = "service"
    version: str = ""
    health: ComponentHealth = ComponentHealth.UNKNOWN
    status: str = "unknown"

    # Endpoints
    endpoint_url: str | None = None
    health_check_url: str | None = None

    # Timestamps
    registered_at: datetime = field(default_factory=utc_now)
    last_health_check: datetime | None = None
    last_healthy_at: datetime | None = None

    # Metrics
    uptime_seconds: float = 0.0
    request_count: int = 0
    error_count: int = 0

    # Configuration
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)

    def update_health(self, health: ComponentHealth) -> None:
        """Update component health status."""
        self.health = health
        self.last_health_check = utc_now()
        if health == ComponentHealth.HEALTHY:
            self.last_healthy_at = utc_now()

    def is_healthy(self) -> bool:
        """Check if component is healthy."""
        return self.health == ComponentHealth.HEALTHY

    def to_dict(self) -> dict[str, Any]:
        """Serialize component to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "version": self.version,
            "health": self.health.value,
            "status": self.status,
            "endpoint_url": self.endpoint_url,
            "last_health_check": (self.last_health_check.isoformat() if self.last_health_check else None),
            "uptime_seconds": self.uptime_seconds,
            "is_healthy": self.is_healthy(),
            "dependencies": self.dependencies,
            "tags": self.tags,
        }


@dataclass
class Alert:
    """
    Represents an alert or notification in the Mothership Cockpit.
    """

    id: str = field(default_factory=lambda: generate_id("alert"))
    severity: AlertSeverity = AlertSeverity.INFO
    title: str = ""
    message: str = ""
    source: str = ""

    # Timestamps
    created_at: datetime = field(default_factory=utc_now)
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None

    # Status
    is_acknowledged: bool = False
    is_resolved: bool = False
    acknowledged_by: str | None = None
    resolved_by: str | None = None

    # Context
    component_id: str | None = None
    operation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def acknowledge(self, user_id: str) -> None:
        """Acknowledge the alert."""
        self.is_acknowledged = True
        self.acknowledged_at = utc_now()
        self.acknowledged_by = user_id

    def resolve(self, user_id: str) -> None:
        """Resolve the alert."""
        self.is_resolved = True
        self.resolved_at = utc_now()
        self.resolved_by = user_id
        if not self.is_acknowledged:
            self.acknowledge(user_id)

    def to_dict(self) -> dict[str, Any]:
        """Serialize alert to dictionary."""
        return {
            "id": self.id,
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "source": self.source,
            "created_at": self.created_at.isoformat(),
            "acknowledged_at": (self.acknowledged_at.isoformat() if self.acknowledged_at else None),
            "resolved_at": (self.resolved_at.isoformat() if self.resolved_at else None),
            "is_acknowledged": self.is_acknowledged,
            "is_resolved": self.is_resolved,
            "component_id": self.component_id,
            "operation_id": self.operation_id,
        }


@dataclass
class CockpitState:
    """
    Represents the overall state of the Mothership Cockpit.

    This is the central model that aggregates system state,
    active sessions, running operations, and component health.
    """

    id: str = field(default_factory=lambda: generate_id("state"))
    state: SystemState = SystemState.OFFLINE
    version: str = "1.0.0"

    # Timestamps
    started_at: datetime | None = None
    updated_at: datetime = field(default_factory=utc_now)

    # Collections
    sessions: dict[str, Session] = field(default_factory=dict)
    operations: dict[str, Operation] = field(default_factory=dict)
    components: dict[str, Component] = field(default_factory=dict)
    alerts: dict[str, Alert] = field(default_factory=dict)

    # Metrics
    total_sessions: int = 0
    active_sessions: int = 0
    total_operations: int = 0
    running_operations: int = 0

    # Configuration
    metadata: dict[str, Any] = field(default_factory=dict)

    def start(self) -> None:
        """Start the cockpit system."""
        self.state = SystemState.ONLINE
        self.started_at = utc_now()
        self.updated_at = utc_now()

    def shutdown(self) -> None:
        """Shutdown the cockpit system."""
        self.state = SystemState.SHUTDOWN
        self.updated_at = utc_now()

    def add_session(self, session: Session) -> None:
        """Add a session to the cockpit."""
        self.sessions[session.id] = session
        self.total_sessions += 1
        if session.is_active():
            self.active_sessions += 1
        self.updated_at = utc_now()

    def remove_session(self, session_id: str) -> Session | None:
        """Remove a session from the cockpit."""
        session = self.sessions.pop(session_id, None)
        if session and session.is_active():
            self.active_sessions -= 1
        self.updated_at = utc_now()
        return session

    def add_operation(self, operation: Operation) -> None:
        """Add an operation to the cockpit."""
        self.operations[operation.id] = operation
        self.total_operations += 1
        if operation.status == OperationStatus.RUNNING:
            self.running_operations += 1
        self.updated_at = utc_now()

    def add_component(self, component: Component) -> None:
        """Register a component with the cockpit."""
        self.components[component.id] = component
        self.updated_at = utc_now()

    def add_alert(self, alert: Alert) -> None:
        """Add an alert to the cockpit."""
        self.alerts[alert.id] = alert
        self.updated_at = utc_now()

    def get_health_summary(self) -> dict[str, Any]:
        """Get overall health summary."""
        healthy_components = sum(1 for c in self.components.values() if c.is_healthy())
        total_components = len(self.components)

        unresolved_alerts = sum(1 for a in self.alerts.values() if not a.is_resolved)
        critical_alerts = sum(
            1 for a in self.alerts.values() if not a.is_resolved and a.severity == AlertSeverity.CRITICAL
        )

        return {
            "state": self.state.value,
            "healthy_components": healthy_components,
            "total_components": total_components,
            "health_percentage": ((healthy_components / total_components * 100) if total_components > 0 else 100),
            "active_sessions": self.active_sessions,
            "running_operations": self.running_operations,
            "unresolved_alerts": unresolved_alerts,
            "critical_alerts": critical_alerts,
        }

    @property
    def uptime_seconds(self) -> float:
        """Calculate system uptime in seconds."""
        if self.started_at is None:
            return 0.0
        return (utc_now() - self.started_at).total_seconds()

    def to_dict(self) -> dict[str, Any]:
        """Serialize cockpit state to dictionary."""
        return {
            "id": self.id,
            "state": self.state.value,
            "version": self.version,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "updated_at": self.updated_at.isoformat(),
            "uptime_seconds": self.uptime_seconds,
            "metrics": {
                "total_sessions": self.total_sessions,
                "active_sessions": self.active_sessions,
                "total_operations": self.total_operations,
                "running_operations": self.running_operations,
            },
            "health_summary": self.get_health_summary(),
        }


__all__ = [
    # Enums
    "SessionStatus",
    "OperationStatus",
    "OperationType",
    "SystemState",
    "ComponentHealth",
    "AlertSeverity",
    "Priority",
    # Models
    "Session",
    "Operation",
    "Component",
    "Alert",
    "CockpitState",
    # Utilities
    "generate_id",
    "utc_now",
]
