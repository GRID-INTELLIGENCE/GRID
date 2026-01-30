"""
Usage tracking repository.

Repository for storing and querying API usage records.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from ..models.subscription import UsageRecord
from . import BaseRepository, StateStore, get_state_store

logger = logging.getLogger(__name__)


class UsageRepository(BaseRepository[UsageRecord]):
    """Repository for usage records."""

    def __init__(self, store: StateStore | None = None):
        self._store = store or get_state_store()

    async def get(self, id: str) -> UsageRecord | None:
        """Get usage record by ID."""
        return self._store.usage_records.get(id)

    async def get_all(self) -> list[UsageRecord]:
        """Get all usage records."""
        return list(self._store.usage_records.values())

    async def add(self, entity: UsageRecord) -> UsageRecord:
        """Add a new usage record."""
        async with self._store.transaction():
            self._store.usage_records[entity.id] = entity
        return entity

    async def update(self, entity: UsageRecord) -> UsageRecord:
        """Update an existing usage record (rarely used)."""
        async with self._store.transaction():
            if entity.id not in self._store.usage_records:
                raise ValueError(f"Usage record not found: {entity.id}")
            self._store.usage_records[entity.id] = entity
        return entity

    async def delete(self, id: str) -> bool:
        """Delete a usage record."""
        async with self._store.transaction():
            if id in self._store.usage_records:
                del self._store.usage_records[id]
                return True
        return False

    async def exists(self, id: str) -> bool:
        """Check if usage record exists."""
        return id in self._store.usage_records

    async def count(self) -> int:
        """Count all usage records."""
        return len(self._store.usage_records)

    async def get_by_user(
        self, user_id: str, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> list[UsageRecord]:
        """Get usage records for a user within a date range."""
        records = [r for r in self._store.usage_records.values() if r.user_id == user_id]
        if start_date:
            records = [r for r in records if r.timestamp >= start_date]
        if end_date:
            records = [r for r in records if r.timestamp <= end_date]
        return records

    async def get_usage_by_endpoint(self, user_id: str, endpoint: str, period_days: int = 30) -> int:
        """Get total cost units for a specific endpoint within a period."""
        start_date = datetime.now(UTC) - timedelta(days=period_days)
        records = await self.get_by_user(user_id, start_date=start_date)
        endpoint_records = [r for r in records if r.endpoint == endpoint]
        return sum(r.cost_units for r in endpoint_records)

    async def get_total_usage(self, user_id: str, period_days: int = 30) -> dict[str, int]:
        """Get total usage by endpoint type for a user."""
        start_date = datetime.now(UTC) - timedelta(days=period_days)
        records = await self.get_by_user(user_id, start_date=start_date)

        usage: dict[str, int] = {}
        for record in records:
            endpoint_type = record.endpoint.split("/")[0] if "/" in record.endpoint else record.endpoint
            usage[endpoint_type] = usage.get(endpoint_type, 0) + record.cost_units

        return usage
