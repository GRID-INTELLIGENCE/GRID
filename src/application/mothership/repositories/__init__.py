"""
Mothership Cockpit Repositories.

Repository pattern implementation for data access and state management.
Provides abstraction layer between services and data storage.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generic,
    List,
    Optional,
    TypeVar,
)

from ..models import utc_now
from ..models.cockpit import (
    Alert as CockpitAlert,
)
from ..models.cockpit import (
    CockpitState as CockpitStateModel,
)
from ..models.cockpit import (
    Component as CockpitComponent,
)
from ..models.cockpit import (
    Session as CockpitSession,
)
from ..models.cockpit import (
    Task,
    TaskStatus,
)

if TYPE_CHECKING:
    from ..models.cockpit import AlertSeverity as CockpitAlertSeverity
    from ..models.cockpit import ComponentHealth as CockpitComponentHealth
    from ..models.cockpit import OperationMode

logger = logging.getLogger(__name__)

T = TypeVar("T")


# =============================================================================
# Base Repository Interface
# =============================================================================


class BaseRepository[T](ABC):
    """Abstract base repository defining common CRUD operations."""

    @abstractmethod
    async def get(self, id: str) -> T | None:
        """Retrieve an entity by ID."""
        pass

    @abstractmethod
    async def get_all(self) -> list[T]:
        """Retrieve all entities."""
        pass

    @abstractmethod
    async def add(self, entity: T) -> T:
        """Add a new entity."""
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete an entity by ID."""
        pass

    @abstractmethod
    async def exists(self, id: str) -> bool:
        """Check if an entity exists."""
        pass

    @abstractmethod
    async def count(self) -> int:
        """Count all entities."""
        pass


# =============================================================================
# In-Memory State Store
# =============================================================================


@dataclass
class StateStore:
    """
    Thread-safe in-memory state store for the Mothership Cockpit.

    Provides centralized state management with atomic operations,
    event notification, and query capabilities.
    """

    # Core state
    cockpit_state: CockpitStateModel = field(default_factory=CockpitStateModel)

    # Entity collections
    sessions: dict[str, CockpitSession] = field(default_factory=dict)
    tasks: dict[str, Task] = field(default_factory=dict)
    components: dict[str, CockpitComponent] = field(default_factory=dict)
    alerts: dict[str, CockpitAlert] = field(default_factory=dict)

    # Additional collections (Phase 1 in-memory storage)
    api_keys: dict[str, Any] = field(default_factory=dict)
    payment_transactions: dict[str, Any] = field(default_factory=dict)
    subscriptions: dict[str, Any] = field(default_factory=dict)
    invoices: dict[str, Any] = field(default_factory=dict)
    usage_records: dict[str, Any] = field(default_factory=dict)

    # Synchronization
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    # Event subscribers
    _subscribers: dict[str, list[Callable]] = field(default_factory=dict)

    # Metadata
    created_at: datetime = field(default_factory=utc_now)
    last_modified: datetime = field(default_factory=utc_now)

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[StateStore]:
        """Context manager for atomic state modifications."""
        async with self._lock:
            try:
                yield self
                self.last_modified = utc_now()
            except Exception as e:
                logger.error(f"Transaction failed: {e}")
                raise

    async def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe to state change events."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    async def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """Unsubscribe from state change events."""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
            except ValueError:
                pass

    async def emit(self, event_type: str, data: Any = None) -> None:
        """Emit an event to all subscribers."""
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    result = callback(event_type, data)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.error(f"Event handler error: {e}")

    def get_snapshot(self) -> dict[str, Any]:
        """Get a snapshot of the current state."""
        return {
            "cockpit_state": self.cockpit_state.to_dict(),
            "session_count": len(self.sessions),
            "task_count": len(self.tasks),
            "component_count": len(self.components),
            "alert_count": len(self.alerts),
            "created_at": self.created_at.isoformat(),
            "last_modified": self.last_modified.isoformat(),
        }


# Global state store instance
_state_store: StateStore | None = None


def get_state_store() -> StateStore:
    """Get or create the global state store instance."""
    global _state_store
    if _state_store is None:
        _state_store = StateStore()
    return _state_store


def reset_state_store() -> StateStore:
    """Reset the state store (useful for testing)."""
    global _state_store
    _state_store = StateStore()
    return _state_store


# =============================================================================
# Session Repository
# =============================================================================


class SessionRepository(BaseRepository[CockpitSession]):
    """Repository for managing user sessions."""

    def __init__(self, store: StateStore | None = None):
        self._store = store or get_state_store()

    async def get(self, id: str) -> CockpitSession | None:
        """Get session by ID."""
        return self._store.sessions.get(id)

    async def get_all(self) -> list[CockpitSession]:
        """Get all sessions."""
        return list(self._store.sessions.values())

    async def add(self, entity: CockpitSession) -> CockpitSession:
        """Add a new session."""
        async with self._store.transaction():
            self._store.sessions[entity.id] = entity
            self._store.cockpit_state.add_session(entity)
        await self._store.emit("session.created", entity)
        return entity

    async def update(self, entity: CockpitSession) -> CockpitSession:
        """Update an existing session."""
        async with self._store.transaction():
            if entity.id not in self._store.sessions:
                raise ValueError(f"Session not found: {entity.id}")
            self._store.sessions[entity.id] = entity
        await self._store.emit("session.updated", entity)
        return entity

    async def delete(self, id: str) -> bool:
        """Delete a session."""
        async with self._store.transaction():
            if id in self._store.sessions:
                session = self._store.sessions.pop(id)
                await self._store.emit("session.deleted", session)
                return True
        return False

    async def exists(self, id: str) -> bool:
        """Check if session exists."""
        return id in self._store.sessions

    async def count(self) -> int:
        """Count all sessions."""
        return len(self._store.sessions)

    async def get_by_user(self, user_id: str) -> list[CockpitSession]:
        """Get all sessions for a user."""
        return [s for s in self._store.sessions.values() if s.user_id == user_id]

    async def get_active(self) -> list[CockpitSession]:
        """Get all active sessions."""
        return [s for s in self._store.sessions.values() if s.is_active]

    async def get_expired(self) -> list[CockpitSession]:
        """Get all expired sessions."""
        return [s for s in self._store.sessions.values() if s.is_expired]

    async def cleanup_expired(self) -> int:
        """Remove expired sessions and return count removed."""
        expired = await self.get_expired()
        count = 0
        for session in expired:
            if await self.delete(session.id):
                count += 1
        return count

    async def terminate_user_sessions(self, user_id: str) -> int:
        """Terminate all sessions for a user."""
        sessions = await self.get_by_user(user_id)
        count = 0
        for session in sessions:
            session.terminate()
            await self.update(session)
            count += 1
        return count


# =============================================================================
# Task Repository
# =============================================================================


class TaskRepository(BaseRepository[Task]):
    """Repository for managing tasks."""

    def __init__(self, store: StateStore | None = None):
        self._store = store or get_state_store()

    async def get(self, id: str) -> Task | None:
        """Get task by ID."""
        return self._store.tasks.get(id)

    async def get_all(self) -> list[Task]:
        """Get all tasks."""
        return list(self._store.tasks.values())

    async def add(self, entity: Task) -> Task:
        """Add a new task."""
        async with self._store.transaction():
            self._store.tasks[entity.id] = entity
            self._store.cockpit_state.add_task(entity)
        await self._store.emit("task.created", entity)
        return entity

    async def update(self, entity: Task) -> Task:
        """Update an existing task."""
        async with self._store.transaction():
            if entity.id not in self._store.tasks:
                raise ValueError(f"Task not found: {entity.id}")
            self._store.tasks[entity.id] = entity
        await self._store.emit("task.updated", entity)
        return entity

    async def delete(self, id: str) -> bool:
        """Delete a task."""
        async with self._store.transaction():
            if id in self._store.tasks:
                task = self._store.tasks.pop(id)
                await self._store.emit("task.deleted", task)
                return True
        return False

    async def exists(self, id: str) -> bool:
        """Check if task exists."""
        return id in self._store.tasks

    async def count(self) -> int:
        """Count all tasks."""
        return len(self._store.tasks)

    async def get_by_status(self, status: TaskStatus) -> list[Task]:
        """Get tasks by status."""
        return [t for t in self._store.tasks.values() if t.status == status]

    async def get_pending(self) -> list[Task]:
        """Get all pending tasks."""
        return [t for t in self._store.tasks.values() if t.is_runnable]

    async def get_running(self) -> list[Task]:
        """Get all running tasks."""
        return await self.get_by_status(TaskStatus.RUNNING)

    async def get_by_type(self, task_type: str) -> list[Task]:
        """Get tasks by type."""
        return [t for t in self._store.tasks.values() if t.task_type == task_type]

    async def get_next_runnable(self) -> Task | None:
        """Get the next task that can be executed (highest priority first)."""
        pending = await self.get_pending()
        if not pending:
            return None
        # Sort by priority (critical=0, background=4) and created_at
        from ..models.cockpit import TaskPriority

        priority_order = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.NORMAL: 2,
            TaskPriority.LOW: 3,
            TaskPriority.BACKGROUND: 4,
        }
        pending.sort(key=lambda t: (priority_order.get(t.priority, 2), t.created_at))
        return pending[0] if pending else None

    async def cleanup_completed(self, older_than: timedelta) -> int:
        """Remove completed tasks older than specified duration."""
        cutoff = utc_now() - older_than
        to_delete = [
            t.id for t in self._store.tasks.values() if t.is_terminal and t.completed_at and t.completed_at < cutoff
        ]
        count = 0
        for task_id in to_delete:
            if await self.delete(task_id):
                count += 1
        return count


# =============================================================================
# Component Repository
# =============================================================================


class ComponentRepository(BaseRepository[CockpitComponent]):
    """Repository for managing system components."""

    def __init__(self, store: StateStore | None = None):
        self._store = store or get_state_store()

    async def get(self, id: str) -> CockpitComponent | None:
        """Get component by ID."""
        return self._store.components.get(id)

    async def get_all(self) -> list[CockpitComponent]:
        """Get all components."""
        return list(self._store.components.values())

    async def add(self, entity: CockpitComponent) -> CockpitComponent:
        """Register a new component."""
        async with self._store.transaction():
            self._store.components[entity.id] = entity
            self._store.cockpit_state.add_component(entity)
        await self._store.emit("component.registered", entity)
        return entity

    async def update(self, entity: CockpitComponent) -> CockpitComponent:
        """Update component information."""
        async with self._store.transaction():
            if entity.id not in self._store.components:
                raise ValueError(f"Component not found: {entity.id}")
            self._store.components[entity.id] = entity
        await self._store.emit("component.updated", entity)
        return entity

    async def delete(self, id: str) -> bool:
        """Unregister a component."""
        async with self._store.transaction():
            if id in self._store.components:
                component = self._store.components.pop(id)
                self._store.cockpit_state.remove_component(id)
                await self._store.emit("component.unregistered", component)
                return True
        return False

    async def exists(self, id: str) -> bool:
        """Check if component exists."""
        return id in self._store.components

    async def count(self) -> int:
        """Count all components."""
        return len(self._store.components)

    async def get_by_name(self, name: str) -> CockpitComponent | None:
        """Get component by name."""
        for component in self._store.components.values():
            if component.name == name:
                return component
        return None

    async def get_by_type(self, component_type: str) -> list[CockpitComponent]:
        """Get components by type."""
        return [c for c in self._store.components.values() if c.component_type.value == component_type]

    async def get_healthy(self) -> list[CockpitComponent]:
        """Get all healthy components."""
        return [c for c in self._store.components.values() if c.is_healthy]

    async def get_unhealthy(self) -> list[CockpitComponent]:
        """Get all unhealthy components."""
        from ..models.cockpit import ComponentHealth

        return [c for c in self._store.components.values() if c.health == ComponentHealth.UNHEALTHY]

    async def update_health(
        self,
        component_id: str,
        health: CockpitComponentHealth,
        message: str = "",
    ) -> CockpitComponent | None:
        """Update component health status."""
        component = await self.get(component_id)
        if component:
            component.update_health(health, message)
            await self.update(component)
            await self._store.emit("component.health_changed", component)
        return component


# =============================================================================
# Alert Repository
# =============================================================================


class AlertRepository(BaseRepository[CockpitAlert]):
    """Repository for managing system alerts."""

    def __init__(self, store: StateStore | None = None):
        self._store = store or get_state_store()

    async def get(self, id: str) -> CockpitAlert | None:
        """Get alert by ID."""
        return self._store.alerts.get(id)

    async def get_all(self) -> list[CockpitAlert]:
        """Get all alerts."""
        return list(self._store.alerts.values())

    async def add(self, entity: CockpitAlert) -> CockpitAlert:
        """Create a new alert."""
        async with self._store.transaction():
            self._store.alerts[entity.id] = entity
            self._store.cockpit_state.add_alert(entity)
        await self._store.emit("alert.created", entity)
        return entity

    async def update(self, entity: CockpitAlert) -> CockpitAlert:
        """Update an alert."""
        async with self._store.transaction():
            if entity.id not in self._store.alerts:
                raise ValueError(f"Alert not found: {entity.id}")
            self._store.alerts[entity.id] = entity
        await self._store.emit("alert.updated", entity)
        return entity

    async def delete(self, id: str) -> bool:
        """Delete an alert."""
        async with self._store.transaction():
            if id in self._store.alerts:
                alert = self._store.alerts.pop(id)
                await self._store.emit("alert.deleted", alert)
                return True
        return False

    async def exists(self, id: str) -> bool:
        """Check if alert exists."""
        return id in self._store.alerts

    async def count(self) -> int:
        """Count all alerts."""
        return len(self._store.alerts)

    async def get_active(self) -> list[CockpitAlert]:
        """Get all unresolved alerts."""
        return [a for a in self._store.alerts.values() if a.is_active]

    async def get_by_severity(self, severity: CockpitAlertSeverity) -> list[CockpitAlert]:
        """Get alerts by severity."""
        return [a for a in self._store.alerts.values() if a.severity == severity]

    async def get_critical(self) -> list[CockpitAlert]:
        """Get critical alerts."""
        from ..models.cockpit import AlertSeverity

        return await self.get_by_severity(AlertSeverity.CRITICAL)

    async def get_unacknowledged(self) -> list[CockpitAlert]:
        """Get unacknowledged alerts."""
        return [a for a in self._store.alerts.values() if not a.acknowledged and a.is_active]

    async def get_by_component(self, component_id: str) -> list[CockpitAlert]:
        """Get alerts for a specific component."""
        return [a for a in self._store.alerts.values() if a.component_id == component_id]

    async def acknowledge(self, alert_id: str, user_id: str) -> CockpitAlert | None:
        """Acknowledge an alert."""
        alert = await self.get(alert_id)
        if alert and not alert.acknowledged:
            alert.acknowledge(user_id)
            await self.update(alert)
            await self._store.emit("alert.acknowledged", alert)
        return alert

    async def resolve(self, alert_id: str) -> CockpitAlert | None:
        """Resolve an alert."""
        alert = await self.get(alert_id)
        if alert and not alert.resolved:
            alert.resolve()
            await self.update(alert)
            await self._store.emit("alert.resolved", alert)
        return alert

    async def cleanup_resolved(self, older_than: timedelta) -> int:
        """Remove resolved alerts older than specified duration."""
        cutoff = utc_now() - older_than
        to_delete = [
            a.id for a in self._store.alerts.values() if a.resolved and a.resolved_at and a.resolved_at < cutoff
        ]
        count = 0
        for alert_id in to_delete:
            if await self.delete(alert_id):
                count += 1
        return count


# =============================================================================
# Cockpit State Repository
# =============================================================================


class CockpitStateRepository:
    """Repository for managing overall cockpit state."""

    def __init__(self, store: StateStore | None = None):
        self._store = store or get_state_store()

    async def get_state(self) -> CockpitStateModel:
        """Get the current cockpit state."""
        return self._store.cockpit_state

    async def update_state(self, state: CockpitStateModel) -> CockpitStateModel:
        """Update the cockpit state."""
        async with self._store.transaction():
            self._store.cockpit_state = state
        await self._store.emit("cockpit.state_updated", state)
        return state

    async def get_summary(self) -> dict[str, Any]:
        """Get cockpit state summary."""
        return self._store.cockpit_state.to_dict()

    async def get_full_state(self) -> dict[str, Any]:
        """Get full cockpit state including all entities."""
        return self._store.cockpit_state.to_full_dict()

    async def set_mode(self, mode: OperationMode) -> CockpitStateModel:
        """Set the cockpit operation mode."""
        async with self._store.transaction():
            self._store.cockpit_state.mode = mode
        await self._store.emit("cockpit.mode_changed", mode)
        return self._store.cockpit_state

    async def is_healthy(self) -> bool:
        """Check if the cockpit is in a healthy state."""
        return self._store.cockpit_state.is_healthy


# =============================================================================
# Unit of Work Pattern
# =============================================================================


class UnitOfWork:
    """
    Unit of Work pattern for coordinating repository operations.

    Provides a single entry point to all repositories and ensures
    consistent state management across operations.
    """

    def __init__(self, store: StateStore | None = None):
        self._store = store or get_state_store()
        self.sessions = SessionRepository(self._store)
        self.tasks = TaskRepository(self._store)
        self.components = ComponentRepository(self._store)
        self.alerts = AlertRepository(self._store)
        self.cockpit = CockpitStateRepository(self._store)

        from .api_key import APIKeyRepository
        from .payment import InvoiceRepository, PaymentTransactionRepository, SubscriptionRepository
        from .usage import UsageRepository

        self.api_keys = APIKeyRepository(self._store)  # type: ignore[arg-type]
        self.usage = UsageRepository(self._store)  # type: ignore[arg-type]
        self.payment_transactions = PaymentTransactionRepository(self._store)  # type: ignore[arg-type]
        self.subscriptions = SubscriptionRepository(self._store)  # type: ignore[arg-type]
        self.invoices = InvoiceRepository(self._store)  # type: ignore[arg-type]

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[UnitOfWork]:
        """Execute operations within a transaction."""
        async with self._store.transaction():
            yield self

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe to state change events."""
        asyncio.create_task(self._store.subscribe(event_type, callback))

    async def get_snapshot(self) -> dict[str, Any]:
        """Get a snapshot of all state."""
        return self._store.get_snapshot()


# =============================================================================
# Factory Function
# =============================================================================


def get_unit_of_work(store: StateStore | None = None) -> UnitOfWork:
    """Get a Unit of Work instance."""
    return UnitOfWork(store)


__all__ = [
    # Base
    "BaseRepository",
    # State Store
    "StateStore",
    "get_state_store",
    "reset_state_store",
    # Repositories
    "SessionRepository",
    "TaskRepository",
    "ComponentRepository",
    "AlertRepository",
    "CockpitStateRepository",
    # Unit of Work
    "UnitOfWork",
    "get_unit_of_work",
]
