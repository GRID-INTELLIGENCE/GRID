"""Async repository for admission gate entity persistence.

Loads entity records + violations from SQLite on startup, persists changes
after each violation recording, banner, or revocation.
"""

from __future__ import annotations

import logging
import time

from sqlalchemy import select

from ..db.models_admission import AdmissionEntityRow, AdmissionViolationRow
from ..middleware.admission_gate import EntityRecord, EntityViolation, ViolationType

logger = logging.getLogger(__name__)


class AdmissionEntityRepository:
    """Async CRUD layer between EntityAttributionEngine and SQLite."""

    def __init__(self, session_factory) -> None:
        """Accept an async_sessionmaker (or callable returning AsyncSession)."""
        self._session_factory = session_factory

    async def load_all(self) -> dict[str, EntityRecord]:
        """Load all persisted entities into in-memory EntityRecord dict."""
        async with self._session_factory() as session:
            result = await session.execute(select(AdmissionEntityRow))
            rows = result.scalars().all()

        entities: dict[str, EntityRecord] = {}
        for row in rows:
            violations = [
                EntityViolation(
                    entity_id=v.entity_id,
                    violation_type=ViolationType(v.violation_type),
                    timestamp=v.created_at.timestamp(),
                    penalty_points=v.penalty_points,
                    metadata=v.violation_metadata or {},
                )
                for v in row.violations
            ]
            record = EntityRecord(
                entity_id=row.entity_id,
                violations=violations,
                total_penalty_points=row.total_penalty_points,
                bannered=row.bannered,
                banner_reason=row.banner_reason,
                first_seen=time.monotonic(),
                last_seen=time.monotonic(),
            )
            entities[row.entity_id] = record

        logger.info("admission_persistence.loaded entities=%d", len(entities))
        return entities

    async def persist_entity(self, record: EntityRecord) -> None:
        """Upsert a single entity record and its violations."""
        async with self._session_factory() as session:
            async with session.begin():
                existing = await session.get(AdmissionEntityRow, record.entity_id)

                if existing:
                    existing.total_penalty_points = record.total_penalty_points
                    existing.bannered = record.bannered
                    existing.banner_reason = record.banner_reason
                    # Sync violations: detect reset vs append-only
                    persisted_count = len(existing.violations)
                    if len(record.violations) < persisted_count:
                        # Reset occurred — clear DB violations and re-insert from memory
                        existing.violations.clear()
                        for v in record.violations:
                            existing.violations.append(
                                AdmissionViolationRow(
                                    entity_id=record.entity_id,
                                    violation_type=v.violation_type.value,
                                    penalty_points=v.penalty_points,
                                    violation_metadata=v.metadata,
                                )
                            )
                    else:
                        # Append-only: add new violations beyond persisted count
                        for v in record.violations[persisted_count:]:
                            existing.violations.append(
                                AdmissionViolationRow(
                                    entity_id=record.entity_id,
                                    violation_type=v.violation_type.value,
                                    penalty_points=v.penalty_points,
                                    violation_metadata=v.metadata,
                                )
                            )
                else:
                    entity_row = AdmissionEntityRow(
                        entity_id=record.entity_id,
                        total_penalty_points=record.total_penalty_points,
                        bannered=record.bannered,
                        banner_reason=record.banner_reason,
                    )
                    for v in record.violations:
                        entity_row.violations.append(
                            AdmissionViolationRow(
                                entity_id=record.entity_id,
                                violation_type=v.violation_type.value,
                                penalty_points=v.penalty_points,
                                violation_metadata=v.metadata,
                            )
                        )
                    session.add(entity_row)

    async def delete_entity(self, entity_id: str) -> None:
        """Remove an entity and its violations (for full_reset)."""
        async with self._session_factory() as session:
            async with session.begin():
                existing = await session.get(AdmissionEntityRow, entity_id)
                if existing:
                    await session.delete(existing)

    async def ensure_tables(self) -> None:
        """Create admission tables if they don't exist."""
        from ..db.models_base import Base

        async with self._session_factory() as session:
            conn = await session.connection()
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[
                    AdmissionEntityRow.__table__,
                    AdmissionViolationRow.__table__,
                ],
            )
            await session.commit()

        logger.info("admission_persistence.tables_ensured")
