"""
Mothership Cockpit Domain Models.

Core domain models representing the cockpit state, components,
and operational entities using dataclasses and enums for type safety.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

# =============================================================================
# Enums
# =============================================================================


class SystemStatus(StrEnum):
    """Overall system status indicators."""

    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"
    INITIALIZING = "initializing"
    ERROR = "error"


class ComponentType(StrEnum):
    """Types of system components managed by the cockpit."""

    API_SERVER = "api_server"
    DATABASE = "database"
    CACHE = "cache"
    QUEUE = "queue"
    WORKER = "worker"
    SCHEDULER = "scheduler"
    INTEGRATION = "integration"
    WEBSOCKET = "websocket"
    MONITOR = "monitor"


class ComponentHealth(StrEnum):
    """Health status for individual components."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"
    STARTING = "starting"
    STOPPING = "stopping"


class TaskStatus(StrEnum):
    """Status of cockpit tasks."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    RETRYING = "retrying"


class TaskPriority(StrEnum):
    """Priority levels for task scheduling."""

    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    BACKGROUND = "background"


class AlertSeverity(StrEnum):
    """Severity levels for system alerts."""

    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


class SessionState(StrEnum):
    """States for user sessions."""

    ACTIVE = "active"
    IDLE = "idle"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class OperationMode(StrEnum):
    """Cockpit operational modes."""

    NORMAL = "normal"
    MAINTENANCE = "maintenance"
    EMERGENCY = "emergency"
    READONLY = "readonly"
    RECOVERY = "recovery"


# =============================================================================
# Utility Functions
# =============================================================================


def generate_id(prefix: str = "") -> str:
    """Generate a unique identifier with optional prefix."""
    unique = uuid.uuid4().hex[:12]
    return f"{prefix}_{unique}" if prefix else unique


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(UTC)


# =============================================================================
# Component Models
# =============================================================================


@dataclass
class ComponentMetrics:
    """Performance metrics for a component."""

    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    request_count: int = 0
    error_count: int = 0
    avg_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    connections: int = 0
    uptime_seconds: float = 0.0
    last_updated: datetime = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        """Serialize metrics to dictionary."""
        return {
            "cpu_percent": self.cpu_percent,
            "memory_mb": self.memory_mb,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "avg_latency_ms": self.avg_latency_ms,
            "p99_latency_ms": self.p99_latency_ms,
            "connections": self.connections,
            "uptime_seconds": self.uptime_seconds,
            "last_updated": self.last_updated.isoformat(),
        }


@dataclass
class Component:
    """
    Represents a system component managed by the cockpit.

    Components are the building blocks of the mothership system,
    each with its own health status, metrics, and configuration.
    """

    id: str
    name: str
    component_type: ComponentType
    health: ComponentHealth = ComponentHealth.UNKNOWN
    status_message: str = ""
    version: str = "1.0.0"
    host: str = "localhost"
    port: int = 0
    enabled: bool = True
    metrics: ComponentMetrics = field(default_factory=ComponentMetrics)
    metadata: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        """Ensure ID is set."""
        if not self.id:
            self.id = generate_id("cmp")

    @property
    def is_healthy(self) -> bool:
        """Check if component is in a healthy state."""
        return self.health in {ComponentHealth.HEALTHY, ComponentHealth.STARTING}

    @property
    def endpoint(self) -> str:
        """Get component endpoint URL."""
        if self.port:
            return f"http://{self.host}:{self.port}"
        return f"http://{self.host}"

    def update_health(
        self,
        health: ComponentHealth,
        message: str = "",
    ) -> None:
        """Update component health status."""
        self.health = health
        self.status_message = message
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        """Serialize component to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "component_type": self.component_type.value,
            "health": self.health.value,
            "status_message": self.status_message,
            "version": self.version,
            "endpoint": self.endpoint,
            "enabled": self.enabled,
            "metrics": self.metrics.to_dict(),
            "metadata": self.metadata,
            "dependencies": self.dependencies,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# =============================================================================
# Task Models
# =============================================================================


@dataclass
class TaskResult:
    """Result of a completed task."""

    success: bool
    data: Any = None
    error: str | None = None
    duration_ms: float = 0.0
    retries: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize result to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "retries": self.retries,
        }


@dataclass
class Task:
    """
    Represents an executable task in the cockpit system.

    Tasks are units of work that can be scheduled, queued,
    and executed with retry support and progress tracking.
    """

    id: str
    name: str
    task_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    progress: float = 0.0
    progress_message: str = ""
    max_retries: int = 3
    retry_count: int = 0
    timeout_seconds: int = 300
    result: TaskResult | None = None
    scheduled_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_by: str | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        """Ensure ID is set."""
        if not self.id:
            self.id = generate_id("task")

    @property
    def is_terminal(self) -> bool:
        """Check if task is in a terminal state."""
        return self.status in {
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.TIMEOUT,
        }

    @property
    def is_runnable(self) -> bool:
        """Check if task can be executed."""
        return self.status in {TaskStatus.PENDING, TaskStatus.QUEUED}

    @property
    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.status == TaskStatus.FAILED and self.retry_count < self.max_retries

    @property
    def duration_ms(self) -> float | None:
        """Calculate task duration in milliseconds."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds() * 1000
        return None

    def start(self) -> None:
        """Mark task as started."""
        self.status = TaskStatus.RUNNING
        self.started_at = utc_now()
        self.updated_at = utc_now()

    def complete(self, result: TaskResult) -> None:
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
        self.result = result
        self.completed_at = utc_now()
        self.updated_at = utc_now()
        self.progress = 100.0 if result.success else self.progress

    def fail(self, error: str) -> None:
        """Mark task as failed."""
        self.status = TaskStatus.FAILED
        self.result = TaskResult(success=False, error=error)
        self.completed_at = utc_now()
        self.updated_at = utc_now()

    def cancel(self) -> None:
        """Cancel the task."""
        self.status = TaskStatus.CANCELLED
        self.completed_at = utc_now()
        self.updated_at = utc_now()

    def update_progress(self, progress: float, message: str = "") -> None:
        """Update task progress."""
        self.progress = min(max(progress, 0.0), 100.0)
        self.progress_message = message
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        """Serialize task to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "task_type": self.task_type,
            "status": self.status.value,
            "priority": self.priority.value,
            "progress": self.progress,
            "progress_message": self.progress_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "result": self.result.to_dict() if self.result else None,
            "duration_ms": self.duration_ms,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
        }


# =============================================================================
# Alert Models
# =============================================================================


@dataclass
class Alert:
    """
    Represents a system alert or notification.

    Alerts are generated when system conditions require attention,
    with severity levels and acknowledgment tracking.
    """

    id: str
    title: str
    message: str
    severity: AlertSeverity = AlertSeverity.INFO
    source: str = "system"
    component_id: str | None = None
    metric_name: str | None = None
    metric_value: float | None = None
    threshold: float | None = None
    acknowledged: bool = False
    acknowledged_by: str | None = None
    acknowledged_at: datetime | None = None
    resolved: bool = False
    resolved_at: datetime | None = None
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        """Ensure ID is set."""
        if not self.id:
            self.id = generate_id("alert")

    @property
    def is_active(self) -> bool:
        """Check if alert is still active."""
        return not self.resolved

    @property
    def requires_action(self) -> bool:
        """Check if alert requires action."""
        return (
            not self.resolved
            and not self.acknowledged
            and self.severity in {AlertSeverity.CRITICAL, AlertSeverity.ERROR}
        )

    def acknowledge(self, user_id: str) -> None:
        """Acknowledge the alert."""
        self.acknowledged = True
        self.acknowledged_by = user_id
        self.acknowledged_at = utc_now()

    def resolve(self) -> None:
        """Mark alert as resolved."""
        self.resolved = True
        self.resolved_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        """Serialize alert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "severity": self.severity.value,
            "source": self.source,
            "component_id": self.component_id,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "threshold": self.threshold,
            "acknowledged": self.acknowledged,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
        }


# =============================================================================
# Session Models
# =============================================================================


@dataclass
class Session:
    """
    Represents a user session in the cockpit.

    Sessions track user activity, permissions, and connection state
    for both HTTP and WebSocket interactions.
    """

    id: str
    user_id: str
    username: str
    state: SessionState = SessionState.ACTIVE
    ip_address: str = ""
    user_agent: str = ""
    permissions: set[str] = field(default_factory=set)
    websocket_connected: bool = False
    last_activity: datetime = field(default_factory=utc_now)
    created_at: datetime = field(default_factory=utc_now)
    expires_at: datetime | None = None

    def __post_init__(self) -> None:
        """Ensure ID is set."""
        if not self.id:
            self.id = generate_id("sess")

    @property
    def is_active(self) -> bool:
        """Check if session is active."""
        if self.state != SessionState.ACTIVE:
            return False
        if self.expires_at and utc_now() > self.expires_at:
            return False
        return True

    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        if self.expires_at:
            return utc_now() > self.expires_at
        return False

    def has_permission(self, permission: str) -> bool:
        """Check if session has a specific permission."""
        return permission in self.permissions or "admin" in self.permissions

    def touch(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = utc_now()

    def terminate(self) -> None:
        """Terminate the session."""
        self.state = SessionState.TERMINATED

    def to_dict(self) -> dict[str, Any]:
        """Serialize session to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "state": self.state.value,
            "ip_address": self.ip_address,
            "permissions": list(self.permissions),
            "websocket_connected": self.websocket_connected,
            "last_activity": self.last_activity.isoformat(),
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


# =============================================================================
# Cockpit State
# =============================================================================


@dataclass
class CockpitState:
    """
    Represents the overall state of the Mothership Cockpit.

    This is the central model aggregating all system state,
    including components, tasks, alerts, and operational mode.
    """

    status: SystemStatus = SystemStatus.INITIALIZING
    mode: OperationMode = OperationMode.NORMAL
    version: str = "1.0.0"
    started_at: datetime = field(default_factory=utc_now)
    components: dict[str, Component] = field(default_factory=dict)
    tasks: dict[str, Task] = field(default_factory=dict)
    alerts: dict[str, Alert] = field(default_factory=dict)
    sessions: dict[str, Session] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def uptime_seconds(self) -> float:
        """Calculate system uptime in seconds."""
        return (utc_now() - self.started_at).total_seconds()

    @property
    def healthy_components(self) -> int:
        """Count healthy components."""
        return sum(1 for c in self.components.values() if c.is_healthy)

    @property
    def active_tasks(self) -> int:
        """Count active tasks."""
        return sum(1 for t in self.tasks.values() if t.status == TaskStatus.RUNNING)

    @property
    def pending_tasks(self) -> int:
        """Count pending tasks."""
        return sum(1 for t in self.tasks.values() if t.is_runnable)

    @property
    def active_alerts(self) -> int:
        """Count active (unresolved) alerts."""
        return sum(1 for a in self.alerts.values() if a.is_active)

    @property
    def critical_alerts(self) -> int:
        """Count critical alerts."""
        return sum(1 for a in self.alerts.values() if a.is_active and a.severity == AlertSeverity.CRITICAL)

    @property
    def active_sessions(self) -> int:
        """Count active sessions."""
        return sum(1 for s in self.sessions.values() if s.is_active)

    @property
    def is_healthy(self) -> bool:
        """Check if overall system is healthy."""
        return (
            self.status == SystemStatus.OPERATIONAL
            and self.critical_alerts == 0
            and self.healthy_components == len(self.components)
        )

    def add_component(self, component: Component) -> None:
        """Add or update a component."""
        self.components[component.id] = component
        self._update_status()

    def remove_component(self, component_id: str) -> Component | None:
        """Remove a component."""
        component = self.components.pop(component_id, None)
        self._update_status()
        return component

    def add_task(self, task: Task) -> None:
        """Add a task."""
        self.tasks[task.id] = task

    def add_alert(self, alert: Alert) -> None:
        """Add an alert."""
        self.alerts[alert.id] = alert
        self._update_status()

    def add_session(self, session: Session) -> None:
        """Add a session."""
        self.sessions[session.id] = session

    def _update_status(self) -> None:
        """Update overall system status based on components and alerts."""
        if not self.components:
            self.status = SystemStatus.INITIALIZING
            return

        if self.critical_alerts > 0:
            self.status = SystemStatus.ERROR
            return

        unhealthy = sum(1 for c in self.components.values() if c.health == ComponentHealth.UNHEALTHY)

        if unhealthy > 0:
            self.status = SystemStatus.DEGRADED
        elif self.mode == OperationMode.MAINTENANCE:
            self.status = SystemStatus.MAINTENANCE
        else:
            self.status = SystemStatus.OPERATIONAL

    def to_dict(self) -> dict[str, Any]:
        """Serialize cockpit state to dictionary."""
        return {
            "status": self.status.value,
            "mode": self.mode.value,
            "version": self.version,
            "uptime_seconds": self.uptime_seconds,
            "started_at": self.started_at.isoformat(),
            "summary": {
                "total_components": len(self.components),
                "healthy_components": self.healthy_components,
                "active_tasks": self.active_tasks,
                "pending_tasks": self.pending_tasks,
                "active_alerts": self.active_alerts,
                "critical_alerts": self.critical_alerts,
                "active_sessions": self.active_sessions,
            },
            "is_healthy": self.is_healthy,
            "metadata": self.metadata,
        }

    def to_full_dict(self) -> dict[str, Any]:
        """Serialize full cockpit state including all entities."""
        result = self.to_dict()
        result["components"] = {k: v.to_dict() for k, v in self.components.items()}
        result["tasks"] = {k: v.to_dict() for k, v in self.tasks.items()}
        result["alerts"] = {k: v.to_dict() for k, v in self.alerts.items()}
        result["sessions"] = {k: v.to_dict() for k, v in self.sessions.items()}
        return result


__all__ = [
    # Enums
    "SystemStatus",
    "ComponentType",
    "ComponentHealth",
    "TaskStatus",
    "TaskPriority",
    "AlertSeverity",
    "SessionState",
    "OperationMode",
    # Utilities
    "generate_id",
    "utc_now",
    # Models
    "ComponentMetrics",
    "Component",
    "TaskResult",
    "Task",
    "Alert",
    "Session",
    "CockpitState",
]
