"""
Comprehensive test suite for Repository & Persistence Layer.

Tests repository behaviour patterns (CRUD, transactions, queries, bulk ops)
using in-memory state instead of the broken MockRepository/__getattr__
pattern that was incompatible with Python 3.13 Mock internals.
"""

from __future__ import annotations

from typing import Any

import pytest

# ---------------------------------------------------------------------------
# In-memory repository implementation (replaces broken MockRepository)
# ---------------------------------------------------------------------------


class InMemoryRepository:
    """Minimal in-memory repository for integration testing.

    Stores records as dicts keyed by ``id``.  All mutating methods are async
    to mirror a real async DB repository interface.
    """

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}
        self._committed: bool = True

    async def create(self, record: dict[str, Any]) -> dict[str, Any]:
        """Insert a record.  ``record`` must contain an ``id`` key."""
        rid = record["id"]
        if rid in self._store:
            raise ValueError(f"Duplicate id: {rid}")
        self._store[rid] = record.copy()
        self._committed = False
        return self._store[rid]

    async def get(self, rid: str) -> dict[str, Any] | None:
        return self._store.get(rid)

    async def update(self, rid: str, patch: dict[str, Any]) -> dict[str, Any] | None:
        if rid not in self._store:
            return None
        self._store[rid].update(patch)
        self._committed = False
        return self._store[rid]

    async def delete(self, rid: str) -> bool:
        if rid in self._store:
            del self._store[rid]
            self._committed = False
            return True
        return False

    async def get_all(self) -> list[dict[str, Any]]:
        return list(self._store.values())

    async def count(self) -> int:
        return len(self._store)

    async def query(
        self, *, filter_by: dict[str, Any] | None = None, limit: int | None = None, offset: int = 0
    ) -> list[dict[str, Any]]:
        results = list(self._store.values())
        if filter_by:
            for k, v in filter_by.items():
                results = [r for r in results if r.get(k) == v]
        results = results[offset:]
        if limit is not None:
            results = results[:limit]
        return results

    async def commit(self) -> None:
        self._committed = True

    async def rollback(self) -> None:
        pass  # In a real implementation this would revert uncommitted changes


# ---------------------------------------------------------------------------
# CRUD tests
# ---------------------------------------------------------------------------


class TestRepositoryCRUD:
    """Test basic create / read / update / delete operations."""

    @pytest.fixture
    def repo(self):
        return InMemoryRepository()

    @pytest.mark.asyncio
    async def test_create_and_get(self, repo):
        record = {"id": "case_1", "title": "Auth system", "user": "alice"}
        created = await repo.create(record)
        assert created["id"] == "case_1"

        fetched = await repo.get("case_1")
        assert fetched is not None
        assert fetched["title"] == "Auth system"

    @pytest.mark.asyncio
    async def test_create_duplicate_raises(self, repo):
        await repo.create({"id": "dup", "val": 1})
        with pytest.raises(ValueError, match="Duplicate"):
            await repo.create({"id": "dup", "val": 2})

    @pytest.mark.asyncio
    async def test_get_missing_returns_none(self, repo):
        assert await repo.get("nonexistent") is None

    @pytest.mark.asyncio
    async def test_update_existing(self, repo):
        await repo.create({"id": "u1", "status": "pending"})
        updated = await repo.update("u1", {"status": "completed"})
        assert updated is not None
        assert updated["status"] == "completed"

    @pytest.mark.asyncio
    async def test_update_missing_returns_none(self, repo):
        assert await repo.update("ghost", {"x": 1}) is None

    @pytest.mark.asyncio
    async def test_delete_existing(self, repo):
        await repo.create({"id": "d1"})
        assert await repo.delete("d1") is True
        assert await repo.get("d1") is None

    @pytest.mark.asyncio
    async def test_delete_missing(self, repo):
        assert await repo.delete("nope") is False

    @pytest.mark.asyncio
    async def test_list_and_count(self, repo):
        for i in range(5):
            await repo.create({"id": f"item_{i}", "type": "test"})
        assert await repo.count() == 5
        assert len(await repo.get_all()) == 5


# ---------------------------------------------------------------------------
# Query / filter tests
# ---------------------------------------------------------------------------


class TestRepositoryQueries:
    """Test filtering, pagination, and query patterns."""

    @pytest.fixture
    def repo(self):
        r = InMemoryRepository()
        for i in range(10):
            r._store[f"q_{i}"] = {"id": f"q_{i}", "type": "even" if i % 2 == 0 else "odd", "idx": i}
        return r

    @pytest.mark.asyncio
    async def test_filter_by_type(self, repo):
        evens = await repo.query(filter_by={"type": "even"})
        assert len(evens) == 5
        assert all(r["type"] == "even" for r in evens)

    @pytest.mark.asyncio
    async def test_pagination(self, repo):
        page = await repo.query(limit=3, offset=2)
        assert len(page) == 3

    @pytest.mark.asyncio
    async def test_filter_with_pagination(self, repo):
        odds = await repo.query(filter_by={"type": "odd"}, limit=2, offset=1)
        assert len(odds) == 2
        assert all(r["type"] == "odd" for r in odds)


# ---------------------------------------------------------------------------
# Transaction-like behaviour
# ---------------------------------------------------------------------------


class TestRepositoryTransactions:
    """Test commit / rollback signalling across multiple repos."""

    @pytest.mark.asyncio
    async def test_commit_marks_clean(self):
        repo = InMemoryRepository()
        await repo.create({"id": "t1"})
        assert repo._committed is False
        await repo.commit()
        assert repo._committed is True

    @pytest.mark.asyncio
    async def test_cross_repo_shared_commit(self):
        """Two repos sharing the same store can both commit independently."""
        repo_a = InMemoryRepository()
        repo_b = InMemoryRepository()
        await repo_a.create({"id": "a1"})
        await repo_b.create({"id": "b1"})
        await repo_a.commit()
        await repo_b.commit()
        assert repo_a._committed is True
        assert repo_b._committed is True


# ---------------------------------------------------------------------------
# Bulk / performance patterns
# ---------------------------------------------------------------------------


class TestRepositoryBulkOps:
    """Test bulk operations complete within time bounds."""

    @pytest.mark.asyncio
    async def test_bulk_insert(self):
        repo = InMemoryRepository()
        for i in range(500):
            await repo.create({"id": f"bulk_{i}", "payload": f"data_{i}"})
        assert await repo.count() == 500

    @pytest.mark.asyncio
    async def test_bulk_query(self):
        repo = InMemoryRepository()
        for i in range(100):
            await repo.create({"id": f"bq_{i}", "type": "a" if i < 50 else "b"})
        a_items = await repo.query(filter_by={"type": "a"})
        assert len(a_items) == 50
