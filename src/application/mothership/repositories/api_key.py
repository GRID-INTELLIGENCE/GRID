"""
API key repository.

Repository implementation for API keys using in-memory StateStore.
Will be migrated to database in Phase 2.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from ..models.api_key import APIKey
from . import BaseRepository, StateStore, get_state_store

logger = logging.getLogger(__name__)


class APIKeyRepository(BaseRepository[APIKey]):
    """Repository for API keys."""

    def __init__(self, store: Optional[StateStore] = None):
        self._store = store or get_state_store()

    async def get(self, id: str) -> Optional[APIKey]:
        """Get API key by ID."""
        return self._store.api_keys.get(id)

    async def get_all(self) -> List[APIKey]:
        """Get all API keys."""
        return list(self._store.api_keys.values())

    async def add(self, entity: APIKey) -> APIKey:
        """Add a new API key."""
        async with self._store.transaction():
            self._store.api_keys[entity.id] = entity
        return entity

    async def update(self, entity: APIKey) -> APIKey:
        """Update an existing API key."""
        from ..models.api_key import utc_now

        async with self._store.transaction():
            if entity.id not in self._store.api_keys:
                raise ValueError(f"API key not found: {entity.id}")
            entity.updated_at = utc_now()
            self._store.api_keys[entity.id] = entity
        return entity

    async def delete(self, id: str) -> bool:
        """Delete an API key."""
        async with self._store.transaction():
            if id in self._store.api_keys:
                del self._store.api_keys[id]
                return True
        return False

    async def exists(self, id: str) -> bool:
        """Check if API key exists."""
        return id in self._store.api_keys

    async def count(self) -> int:
        """Count all API keys."""
        return len(self._store.api_keys)

    async def get_by_user(self, user_id: str) -> List[APIKey]:
        """Get all API keys for a user."""
        return [k for k in self._store.api_keys.values() if k.user_id == user_id]

    async def get_by_key_hash(self, key_hash: str) -> Optional[APIKey]:
        """Get API key by hash (for authentication)."""
        for key in self._store.api_keys.values():
            if key.key_hash == key_hash:
                return key
        return None
