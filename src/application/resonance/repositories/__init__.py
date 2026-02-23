"""
Resonance Repository Layer (Mothership-aligned).

Implements repository pattern with StateStore for data access,
following Mothership application patterns. Includes BaseRepository
and compatibility with Mothership's StateStore.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Generic, TypeVar

T = TypeVar("T")


# =============================================================================
# Compatibility with Mothership StateStore
# =============================================================================


class StateStore:
    """In-memory StateStore compatible with Mothership patterns."""

    def __init__(self) -> None:
        """Initialize state store."""
        # Initialize resonance-specific collections
        self.resonance_activities: dict[str, Any] = {}
        self.resonance_feedback: dict[str, Any] = {}
        self.resonance_events: dict[str, Any] = {}

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[StateStore]:
        """Execute operations within a transaction (no-op for in-memory store)."""
        yield self


_state_store: StateStore | None = None


def get_state_store() -> StateStore:
    """Get or create StateStore instance (Mothership pattern)."""
    global _state_store
    if _state_store is None:
        _state_store = StateStore()
    return _state_store


# =============================================================================
# Base Repository (Mothership-aligned)
# =============================================================================


class BaseRepository[T](ABC):
    """Base repository interface (Mothership-aligned)."""

    def __init__(self, store: StateStore | None = None) -> None:
        """Initialize repository with optional StateStore."""
        self._store = store or get_state_store()

    @abstractmethod
    async def get(self, id: str) -> T | None:
        """Get entity by ID."""
        pass

    @abstractmethod
    async def add(self, entity: T) -> T:
        """Add new entity."""
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        """Update existing entity."""
        pass

    @abstractmethod
    async def delete(self, id: str) -> None:
        """Delete entity by ID."""
        pass


__all__ = [
    "StateStore",
    "get_state_store",
    "BaseRepository",
]
