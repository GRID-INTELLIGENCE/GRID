"""
Mothership Cockpit Services.

Business logic layer implementing core cockpit functionality.
Services coordinate between models, repositories, and external integrations.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from ..exceptions import CockpitError, OperationInProgressError, ResourceNotFoundError, StateTransitionError
from ..models import (
    Alert,
    AlertSeverity,
    CockpitState,
    Component,
    ComponentHealth,
    Operation,
    OperationStatus,
    OperationType,
    Priority,
    Session,
    SessionStatus,
    SystemState,
    utc_now,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Event Types
# =============================================================================


@dataclass
class CockpitEvent:
    """Event emitted by cockpit services for real-time updates."""

    event_type: str
    entity_type: str
    entity_id: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        """Serialize event for transmission."""
        return {
            "event_type": self.event_type,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }


EventHandler = Callable[[CockpitEvent], None]
AsyncEventHandler = Callable[[CockpitEvent], Awaitable[Any]]


# =============================================================================
# Session Service
# =============================================================================


class SessionService:
    """
    Service for managing user sessions.

    Handles session lifecycle, activity tracking, and permission management.
    """

    def __init__(
        self,
        state: CockpitState,
        default_ttl_minutes: int = 60,
        max_sessions: int = 100,
    ):
        self._state = state
        self._default_ttl = timedelta(minutes=default_ttl_minutes)
        self._max_sessions = max_sessions
        self._event_handlers: list[EventHandler] = []

    def add_event_handler(self, handler: EventHandler) -> None:
        """Register an event handler."""
        self._event_handlers.append(handler)

    def _emit_event(self, event: CockpitEvent) -> None:
        """Emit event to all handlers."""
        for handler in self._event_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")

    def create_session(
        self,
        user_id: str,
        permissions: set[str] | None = None,
        client_ip: str | None = None,
        user_agent: str | None = None,
        ttl_minutes: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Session:
        """
        Create a new user session.

        Args:
            user_id: Unique identifier for the user
            permissions: Set of permission strings
            client_ip: Client IP address
            user_agent: Client user agent string
            ttl_minutes: Session TTL in minutes (overrides default)
            metadata: Additional session metadata

        Returns:
            Created Session object

        Raises:
            CockpitError: If max sessions exceeded
        """
        if len(self._state.sessions) >= self._max_sessions:
            # Try to clean up expired sessions first
            self._cleanup_expired_sessions()
            if len(self._state.sessions) >= self._max_sessions:
                raise CockpitError(
                    "Maximum concurrent sessions exceeded",
                    code="MAX_SESSIONS_EXCEEDED",
                    status_code=429,
                )

        ttl = timedelta(minutes=ttl_minutes) if ttl_minutes else self._default_ttl
        now = utc_now()

        session = Session(
            user_id=user_id,
            status=SessionStatus.ACTIVE,
            permissions=permissions or set(),
            client_ip=client_ip,
            user_agent=user_agent,
            created_at=now,
            updated_at=now,
            last_activity_at=now,
            expires_at=now + ttl,
            metadata=metadata or {},
        )

        self._state.add_session(session)
        logger.info(f"Session created: {session.id} for user {user_id}")

        self._emit_event(
            CockpitEvent(
                event_type="created",
                entity_type="session",
                entity_id=session.id,
                data=session.to_dict(),
            )
        )

        return session

    def get_session(self, session_id: str) -> Session:
        """
        Get a session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session object

        Raises:
            ResourceNotFoundError: If session not found
        """
        session = self._state.sessions.get(session_id)
        if session is None:
            raise ResourceNotFoundError("Session", session_id)
        return session

    def get_session_or_none(self, session_id: str) -> Session | None:
        """Get a session by ID, returning None if not found."""
        return self._state.sessions.get(session_id)

    def touch_session(self, session_id: str) -> Session:
        """
        Update session activity timestamp.

        Args:
            session_id: Session identifier

        Returns:
            Updated Session object
        """
        session = self.get_session(session_id)
        if session.is_expired():
            session.status = SessionStatus.TERMINATED
            raise CockpitError(
                "Session has expired",
                code="SESSION_EXPIRED",
                status_code=401,
            )
        session.touch()
        return session

    def terminate_session(self, session_id: str) -> Session:
        """
        Terminate a session.

        Args:
            session_id: Session identifier

        Returns:
            Terminated Session object
        """
        session = self.get_session(session_id)
        session.terminate()

        self._emit_event(
            CockpitEvent(
                event_type="terminated",
                entity_type="session",
                entity_id=session.id,
                data={"user_id": session.user_id},
            )
        )

        logger.info(f"Session terminated: {session_id}")
        return session

    def list_sessions(
        self,
        user_id: str | None = None,
        active_only: bool = False,
    ) -> list[Session]:
        """
        List sessions with optional filtering.

        Args:
            user_id: Filter by user ID
            active_only: Only return active sessions

        Returns:
            List of matching sessions
        """
        sessions = list(self._state.sessions.values())

        if user_id:
            sessions = [s for s in sessions if s.user_id == user_id]
        if active_only:
            sessions = [s for s in sessions if s.is_active()]

        return sorted(sessions, key=lambda s: s.created_at, reverse=True)

    def _cleanup_expired_sessions(self) -> int:
        """Remove expired sessions and return count removed."""
        expired_ids = [s.id for s in self._state.sessions.values() if s.is_expired()]
        for session_id in expired_ids:
            self._state.remove_session(session_id)
        return len(expired_ids)


# =============================================================================
# Operation Service
# =============================================================================


class OperationService:
    """
    Service for managing cockpit operations.

    Handles operation lifecycle, progress tracking, and retry logic.
    """

    def __init__(
        self,
        state: CockpitState,
        max_concurrent_operations: int = 50,
        default_timeout_seconds: int = 300,
    ):
        self._state = state
        self._max_concurrent = max_concurrent_operations
        self._default_timeout = default_timeout_seconds
        self._event_handlers: list[EventHandler] = []
        self._running_tasks: dict[str, asyncio.Task] = {}

    def add_event_handler(self, handler: EventHandler) -> None:
        """Register an event handler."""
        self._event_handlers.append(handler)

    def _emit_event(self, event: CockpitEvent) -> None:
        """Emit event to all handlers."""
        for handler in self._event_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")

    def create_operation(
        self,
        name: str,
        operation_type: OperationType = OperationType.CUSTOM,
        description: str = "",
        priority: Priority = Priority.NORMAL,
        input_data: dict[str, Any] | None = None,
        session_id: str | None = None,
        user_id: str | None = None,
        tags: list[str] | None = None,
        max_retries: int = 3,
    ) -> Operation:
        """
        Create a new operation.

        Args:
            name: Human-readable operation name
            operation_type: Type of operation
            description: Operation description
            priority: Operation priority
            input_data: Input parameters for the operation
            session_id: Associated session ID
            user_id: Associated user ID
            tags: Operation tags
            max_retries: Maximum retry attempts

        Returns:
            Created Operation object
        """
        running_count = sum(1 for op in self._state.operations.values() if op.status == OperationStatus.RUNNING)
        if running_count >= self._max_concurrent:
            raise OperationInProgressError(
                "Maximum concurrent operations reached",
                operation_id=None,
            )

        operation = Operation(
            name=name,
            type=operation_type,
            description=description,
            priority=priority,
            input_data=input_data or {},
            session_id=session_id,
            user_id=user_id,
            tags=tags or [],
            max_retries=max_retries,
        )

        self._state.add_operation(operation)
        logger.info(f"Operation created: {operation.id} - {name}")

        self._emit_event(
            CockpitEvent(
                event_type="created",
                entity_type="operation",
                entity_id=operation.id,
                data=operation.to_dict(),
            )
        )

        return operation

    def get_operation(self, operation_id: str) -> Operation:
        """
        Get an operation by ID.

        Args:
            operation_id: Operation identifier

        Returns:
            Operation object

        Raises:
            ResourceNotFoundError: If operation not found
        """
        operation = self._state.operations.get(operation_id)
        if operation is None:
            raise ResourceNotFoundError("Operation", operation_id)
        return operation

    def start_operation(self, operation_id: str) -> Operation:
        """
        Mark an operation as started.

        Args:
            operation_id: Operation identifier

        Returns:
            Updated Operation object

        Raises:
            StateTransitionError: If operation cannot be started
        """
        operation = self.get_operation(operation_id)

        if operation.status not in {OperationStatus.PENDING, OperationStatus.QUEUED}:
            raise StateTransitionError(
                operation.status.value,
                OperationStatus.RUNNING.value,
                allowed_transitions=["pending", "queued"],
            )

        operation.start()
        self._state.running_operations += 1

        self._emit_event(
            CockpitEvent(
                event_type="started",
                entity_type="operation",
                entity_id=operation.id,
                data={"status": operation.status.value},
            )
        )

        logger.info(f"Operation started: {operation_id}")
        return operation

    def update_progress(
        self,
        operation_id: str,
        percent: float | None = None,
        message: str | None = None,
        step: int | None = None,
    ) -> Operation:
        """
        Update operation progress.

        Args:
            operation_id: Operation identifier
            percent: Progress percentage (0-100)
            message: Progress message
            step: Current step number

        Returns:
            Updated Operation object
        """
        operation = self.get_operation(operation_id)
        operation.update_progress(percent=percent, message=message, step=step)

        self._emit_event(
            CockpitEvent(
                event_type="progress",
                entity_type="operation",
                entity_id=operation.id,
                data={
                    "progress_percent": operation.progress_percent,
                    "progress_message": operation.progress_message,
                },
            )
        )

        return operation

    def complete_operation(
        self,
        operation_id: str,
        output: dict[str, Any] | None = None,
    ) -> Operation:
        """
        Mark an operation as completed successfully.

        Args:
            operation_id: Operation identifier
            output: Operation output data

        Returns:
            Completed Operation object
        """
        operation = self.get_operation(operation_id)
        was_running = operation.status == OperationStatus.RUNNING

        operation.complete(output)

        if was_running:
            self._state.running_operations = max(0, self._state.running_operations - 1)

        self._emit_event(
            CockpitEvent(
                event_type="completed",
                entity_type="operation",
                entity_id=operation.id,
                data={
                    "status": operation.status.value,
                    "duration_seconds": operation.duration_seconds,
                },
            )
        )

        logger.info(f"Operation completed: {operation_id} " f"(duration: {operation.duration_seconds:.2f}s)")
        return operation

    def fail_operation(
        self,
        operation_id: str,
        error: str,
        details: dict[str, Any] | None = None,
    ) -> Operation:
        """
        Mark an operation as failed.

        Args:
            operation_id: Operation identifier
            error: Error message
            details: Additional error details

        Returns:
            Failed Operation object
        """
        operation = self.get_operation(operation_id)
        was_running = operation.status == OperationStatus.RUNNING

        operation.fail(error, details)

        if was_running:
            self._state.running_operations = max(0, self._state.running_operations - 1)

        self._emit_event(
            CockpitEvent(
                event_type="failed",
                entity_type="operation",
                entity_id=operation.id,
                data={
                    "status": operation.status.value,
                    "error": error,
                },
            )
        )

        logger.error(f"Operation failed: {operation_id} - {error}")
        return operation

    def cancel_operation(self, operation_id: str) -> Operation:
        """
        Cancel an operation.

        Args:
            operation_id: Operation identifier

        Returns:
            Cancelled Operation object
        """
        operation = self.get_operation(operation_id)
        was_running = operation.status == OperationStatus.RUNNING

        operation.cancel()

        if was_running:
            self._state.running_operations = max(0, self._state.running_operations - 1)
            # Cancel associated async task if exists
            task = self._running_tasks.pop(operation_id, None)
            if task and not task.done():
                task.cancel()

        self._emit_event(
            CockpitEvent(
                event_type="cancelled",
                entity_type="operation",
                entity_id=operation.id,
                data={"status": operation.status.value},
            )
        )

        logger.info(f"Operation cancelled: {operation_id}")
        return operation

    def list_operations(
        self,
        status: OperationStatus | None = None,
        operation_type: OperationType | None = None,
        session_id: str | None = None,
        limit: int = 100,
    ) -> list[Operation]:
        """
        List operations with optional filtering.

        Args:
            status: Filter by status
            operation_type: Filter by type
            session_id: Filter by session ID
            limit: Maximum number of results

        Returns:
            List of matching operations
        """
        operations = list(self._state.operations.values())

        if status:
            operations = [op for op in operations if op.status == status]
        if operation_type:
            operations = [op for op in operations if op.type == operation_type]
        if session_id:
            operations = [op for op in operations if op.session_id == session_id]

        # Sort by priority (descending) then created_at (descending)
        operations.sort(
            key=lambda op: (op.priority.value, op.created_at.timestamp()),
            reverse=True,
        )

        return operations[:limit]


# =============================================================================
# Component Service
# =============================================================================


class ComponentService:
    """
    Service for managing system components.

    Handles component registration, health monitoring, and metrics collection.
    """

    def __init__(self, state: CockpitState):
        self._state = state
        self._event_handlers: list[EventHandler] = []
        self._health_check_callbacks: dict[str, Callable] = {}

    def add_event_handler(self, handler: EventHandler) -> None:
        """Register an event handler."""
        self._event_handlers.append(handler)

    def _emit_event(self, event: CockpitEvent) -> None:
        """Emit event to all handlers."""
        for handler in self._event_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")

    def register_component(
        self,
        name: str,
        endpoint_url: str | None = None,
        health_check_url: str | None = None,
        version: str = "1.0.0",
        dependencies: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Component:
        """
        Register a new component.

        Args:
            name: Component name
            endpoint_url: Component endpoint URL
            health_check_url: Health check endpoint
            version: Component version
            dependencies: List of component IDs this depends on
            metadata: Additional metadata

        Returns:
            Registered Component object
        """
        component = Component(
            name=name,
            endpoint_url=endpoint_url,
            health_check_url=health_check_url,
            version=version,
            health=ComponentHealth.UNKNOWN,
            dependencies=dependencies or [],
            metadata=metadata or {},
        )

        self._state.add_component(component)
        logger.info(f"Component registered: {component.id} - {name}")

        self._emit_event(
            CockpitEvent(
                event_type="registered",
                entity_type="component",
                entity_id=component.id,
                data=component.to_dict(),
            )
        )

        return component

    def get_component(self, component_id: str) -> Component:
        """
        Get a component by ID.

        Args:
            component_id: Component identifier

        Returns:
            Component object

        Raises:
            ResourceNotFoundError: If component not found
        """
        component = self._state.components.get(component_id)
        if component is None:
            raise ResourceNotFoundError("Component", component_id)
        return component

    def update_health(
        self,
        component_id: str,
        health: ComponentHealth,
        message: str = "",
    ) -> Component:
        """
        Update component health status.

        Args:
            component_id: Component identifier
            health: New health status
            message: Optional status message

        Returns:
            Updated Component object
        """
        component = self.get_component(component_id)
        old_health = component.health
        component.update_health(health)

        if old_health != health:
            self._emit_event(
                CockpitEvent(
                    event_type="health_changed",
                    entity_type="component",
                    entity_id=component.id,
                    data={
                        "old_health": old_health.value,
                        "new_health": health.value,
                        "message": message,
                    },
                )
            )

            # Create alert for unhealthy components
            if health == ComponentHealth.UNHEALTHY:
                self._state.add_alert(
                    Alert(
                        severity=AlertSeverity.ERROR,
                        title=f"Component Unhealthy: {component.name}",
                        message=message or f"Component {component.name} is unhealthy",
                        source="component_service",
                        component_id=component_id,
                    )
                )

        return component

    def list_components(
        self,
        healthy_only: bool = False,
    ) -> list[Component]:
        """
        List all registered components.

        Args:
            healthy_only: Only return healthy components

        Returns:
            List of components
        """
        components = list(self._state.components.values())

        if healthy_only:
            components = [c for c in components if c.is_healthy()]

        return sorted(components, key=lambda c: c.name)

    def unregister_component(self, component_id: str) -> Component:
        """
        Unregister a component.

        Args:
            component_id: Component identifier

        Returns:
            Unregistered Component object
        """
        component = self.get_component(component_id)
        self._state.components.pop(component_id)

        self._emit_event(
            CockpitEvent(
                event_type="unregistered",
                entity_type="component",
                entity_id=component.id,
                data={"name": component.name},
            )
        )

        logger.info(f"Component unregistered: {component_id}")
        return component


# =============================================================================
# Alert Service
# =============================================================================


class AlertService:
    """
    Service for managing system alerts.

    Handles alert creation, acknowledgment, and resolution.
    """

    def __init__(self, state: CockpitState, max_alerts: int = 1000):
        self._state = state
        self._max_alerts = max_alerts
        self._event_handlers: list[EventHandler] = []

    def add_event_handler(self, handler: EventHandler) -> None:
        """Register an event handler."""
        self._event_handlers.append(handler)

    def _emit_event(self, event: CockpitEvent) -> None:
        """Emit event to all handlers."""
        for handler in self._event_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")

    def create_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity = AlertSeverity.INFO,
        source: str = "system",
        component_id: str | None = None,
        operation_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Alert:
        """
        Create a new alert.

        Args:
            title: Alert title
            message: Alert message
            severity: Alert severity
            source: Alert source
            component_id: Associated component ID
            operation_id: Associated operation ID
            metadata: Additional metadata

        Returns:
            Created Alert object
        """
        # Cleanup old resolved alerts if at capacity
        if len(self._state.alerts) >= self._max_alerts:
            self._cleanup_old_alerts()

        alert = Alert(
            severity=severity,
            title=title,
            message=message,
            source=source,
            component_id=component_id,
            operation_id=operation_id,
            metadata=metadata or {},
        )

        self._state.add_alert(alert)
        logger.log(
            self._severity_to_log_level(severity),
            f"Alert created: [{severity.value}] {title}",
        )

        self._emit_event(
            CockpitEvent(
                event_type="created",
                entity_type="alert",
                entity_id=alert.id,
                data=alert.to_dict(),
            )
        )

        return alert

    def get_alert(self, alert_id: str) -> Alert:
        """
        Get an alert by ID.

        Args:
            alert_id: Alert identifier

        Returns:
            Alert object

        Raises:
            ResourceNotFoundError: If alert not found
        """
        alert = self._state.alerts.get(alert_id)
        if alert is None:
            raise ResourceNotFoundError("Alert", alert_id)
        return alert

    def acknowledge_alert(self, alert_id: str, user_id: str) -> Alert:
        """
        Acknowledge an alert.

        Args:
            alert_id: Alert identifier
            user_id: ID of user acknowledging

        Returns:
            Acknowledged Alert object
        """
        alert = self.get_alert(alert_id)
        alert.acknowledge(user_id)

        self._emit_event(
            CockpitEvent(
                event_type="acknowledged",
                entity_type="alert",
                entity_id=alert.id,
                data={"acknowledged_by": user_id},
            )
        )

        return alert

    def resolve_alert(self, alert_id: str, user_id: str) -> Alert:
        """
        Resolve an alert.

        Args:
            alert_id: Alert identifier
            user_id: ID of user resolving

        Returns:
            Resolved Alert object
        """
        alert = self.get_alert(alert_id)
        alert.resolve(user_id)

        self._emit_event(
            CockpitEvent(
                event_type="resolved",
                entity_type="alert",
                entity_id=alert.id,
                data={"resolved_by": user_id},
            )
        )

        return alert

    def list_alerts(
        self,
        severity: AlertSeverity | None = None,
        unresolved_only: bool = False,
        unacknowledged_only: bool = False,
        component_id: str | None = None,
        limit: int = 100,
    ) -> list[Alert]:
        """
        List alerts with optional filtering.

        Args:
            severity: Filter by severity
            unresolved_only: Only return unresolved alerts
            unacknowledged_only: Only return unacknowledged alerts
            component_id: Filter by component
            limit: Maximum number of results

        Returns:
            List of matching alerts
        """
        alerts = list(self._state.alerts.values())

        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if unresolved_only:
            alerts = [a for a in alerts if not a.is_resolved]
        if unacknowledged_only:
            alerts = [a for a in alerts if not a.is_acknowledged]
        if component_id:
            alerts = [a for a in alerts if a.component_id == component_id]

        # Sort by severity (descending) then created_at (descending)
        severity_order = {
            AlertSeverity.CRITICAL: 4,
            AlertSeverity.ERROR: 3,
            AlertSeverity.WARNING: 2,
            AlertSeverity.INFO: 1,
        }
        alerts.sort(
            key=lambda a: (severity_order.get(a.severity, 0), a.created_at.timestamp()),
            reverse=True,
        )

        return alerts[:limit]

    def _cleanup_old_alerts(self) -> int:
        """Remove old resolved alerts and return count removed."""
        resolved = [a for a in self._state.alerts.values() if a.is_resolved]
        resolved.sort(key=lambda a: a.resolved_at or a.created_at)

        # Remove oldest 25% of resolved alerts
        to_remove = resolved[: len(resolved) // 4]
        for alert in to_remove:
            self._state.alerts.pop(alert.id, None)

        return len(to_remove)

    def _severity_to_log_level(self, severity: AlertSeverity) -> int:
        """Convert alert severity to logging level."""
        mapping = {
            AlertSeverity.CRITICAL: logging.CRITICAL,
            AlertSeverity.ERROR: logging.ERROR,
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.INFO: logging.INFO,
        }
        return mapping.get(severity, logging.INFO)


# =============================================================================
# Cockpit Service (Facade)
# =============================================================================


class CockpitService:
    """
    Main cockpit service providing a unified interface.

    Acts as a facade coordinating all sub-services and managing
    overall cockpit state and lifecycle.
    """

    def __init__(
        self,
        session_ttl_minutes: int = 60,
        max_sessions: int = 100,
        max_concurrent_operations: int = 50,
    ):
        self._state = CockpitState()
        self._started = False

        # Initialize sub-services
        self.sessions = SessionService(
            self._state,
            default_ttl_minutes=session_ttl_minutes,
            max_sessions=max_sessions,
        )
        self.operations = OperationService(
            self._state,
            max_concurrent_operations=max_concurrent_operations,
        )
        self.components = ComponentService(self._state)
        self.alerts = AlertService(self._state)

        # Unified event handlers
        self._event_handlers: list[EventHandler] = []

    @property
    def state(self) -> CockpitState:
        """Get current cockpit state."""
        return self._state

    @property
    def is_healthy(self) -> bool:
        """Check if cockpit is healthy."""
        return (
            self._started
            and self._state.state == SystemState.ONLINE
            and all(c.is_healthy() for c in self._state.components.values())
        )

    def add_event_handler(self, handler: EventHandler) -> None:
        """Register a unified event handler for all services."""
        self._event_handlers.append(handler)
        self.sessions.add_event_handler(handler)
        self.operations.add_event_handler(handler)
        self.components.add_event_handler(handler)
        self.alerts.add_event_handler(handler)

    def start(self) -> None:
        """
        Start the cockpit system.

        Initializes state and marks system as online.
        """
        if self._started:
            return

        self._state.start()
        self._started = True
        logger.info("Mothership Cockpit started")

        # Emit system start event
        for handler in self._event_handlers:
            try:
                handler(
                    CockpitEvent(
                        event_type="started",
                        entity_type="system",
                        entity_id="cockpit",
                        data=self._state.to_dict(),
                    )
                )
            except Exception as e:
                logger.error(f"Event handler error: {e}")

    def shutdown(self) -> None:
        """
        Shutdown the cockpit system.

        Terminates all sessions and marks system as offline.
        """
        if not self._started:
            return

        # Terminate all active sessions
        for session in list(self._state.sessions.values()):
            if session.is_active():
                self.sessions.terminate_session(session.id)

        # Cancel running operations
        for operation in list(self._state.operations.values()):
            if operation.status == OperationStatus.RUNNING:
                self.operations.cancel_operation(operation.id)

        self._state.shutdown()
        self._started = False
        logger.info("Mothership Cockpit stopped")

        # Emit system stop event
        for handler in self._event_handlers:
            try:
                handler(
                    CockpitEvent(
                        event_type="stopped",
                        entity_type="system",
                        entity_id="cockpit",
                        data={},
                    )
                )
            except Exception as e:
                logger.error(f"Event handler error: {e}")

    def get_health_summary(self) -> dict[str, Any]:
        """Get health summary of the cockpit."""
        return self._state.get_health_summary()


__all__ = [
    "CockpitEvent",
    "EventHandler",
    "AsyncEventHandler",
    "SessionService",
    "OperationService",
    "ComponentService",
    "AlertService",
    "CockpitService",
]
