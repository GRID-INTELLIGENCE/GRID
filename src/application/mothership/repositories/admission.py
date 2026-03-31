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
        from application.mothership.security.merit_standing import (
            Badge,
            MeritStanding,
            Scope,
        )

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

            # Reconstruct merit standing
            eligible_scopes = set()
            try:
                badge = Badge(row.merit_badge)
                if badge == Badge.B0_RESTRICTED:
                    eligible_scopes = set()
                elif badge == Badge.B1_TRUSTED:
                    eligible_scopes = {Scope.READ, Scope.ANALYSIS}
                elif badge == Badge.B2_VERIFIED:
                    eligible_scopes = {Scope.READ, Scope.WRITE, Scope.ANALYSIS}
                elif badge == Badge.B3_PRIVILEGED:
                    eligible_scopes = {Scope.READ, Scope.WRITE, Scope.ADMIN, Scope.ANALYSIS, Scope.CONTROL}
            except ValueError:
                badge = Badge.B0_RESTRICTED

            merit_standing = MeritStanding(
                entity_id=row.entity_id,
                badge=badge,
                score=row.merit_score,
                roll_number=row.merit_roll_number,
                total_penalty_points=row.total_penalty_points,
                clean_streak=row.merit_clean_streak,
                clean_streak_bonus=row.merit_clean_streak_bonus,
                review_adjustment=row.merit_review_adjustment,
                last_reviewed_at=row.merit_last_reviewed_at,
                last_critical_at=row.merit_last_critical_at,
                first_seen_at=row.first_seen_at,
                last_seen_at=row.last_seen_at,
                eligible_scopes=eligible_scopes,
                violation_count=len(violations),
            )

            record = EntityRecord(
                entity_id=row.entity_id,
                violations=violations,
                total_penalty_points=row.total_penalty_points,
                bannered=row.bannered,
                banner_reason=row.banner_reason,
                first_seen=time.monotonic(),
                last_seen=time.monotonic(),
                merit_standing=merit_standing,
            )
            entities[row.entity_id] = record

        logger.info("admission_persistence.loaded entities=%d", len(entities))
        return entities

    async def persist_entity(self, record: EntityRecord) -> None:
        """Upsert a single entity record and its violations."""
        async with self._session_factory() as session:
            async with session.begin():
                existing = await session.get(AdmissionEntityRow, record.entity_id)

                # Prepare merit standing values
                merit = record.merit_standing

                if existing:
                    existing.total_penalty_points = record.total_penalty_points
                    existing.bannered = record.bannered
                    existing.banner_reason = record.banner_reason

                    # Update merit standing fields
                    if merit:
                        existing.merit_badge = merit.badge.value
                        existing.merit_score = merit.score
                        existing.merit_roll_number = merit.roll_number
                        existing.merit_clean_streak = merit.clean_streak
                        existing.merit_clean_streak_bonus = merit.clean_streak_bonus
                        existing.merit_review_adjustment = merit.review_adjustment
                        existing.merit_last_reviewed_at = merit.last_reviewed_at
                        existing.merit_last_critical_at = merit.last_critical_at

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
                        merit_badge=merit.badge.value if merit else "B0_RESTRICTED",
                        merit_score=merit.score if merit else 45,
                        merit_roll_number=merit.roll_number if merit else 0,
                        merit_clean_streak=merit.clean_streak if merit else 0,
                        merit_clean_streak_bonus=merit.clean_streak_bonus if merit else 0,
                        merit_review_adjustment=merit.review_adjustment if merit else 0,
                        merit_last_reviewed_at=merit.last_reviewed_at if merit else None,
                        merit_last_critical_at=merit.last_critical_at if merit else None,
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
