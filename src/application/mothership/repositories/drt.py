"""DRT (Distributed Request Tracking) repository pattern.

Provides database persistence operations for behavioral signatures,
attack vectors, violations, and escalated endpoints.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models_drt import (
    DRTAttackVectorRow,
    DRTBehavioralSignatureRow,
    DRTConfigurationRow,
    DRTEscalatedEndpointRow,
    DRTFalsePositivePatternRow,
    DRTFalsePositiveRow,
    DRTViolationRow,
)
from ..middleware.drt_middleware import BehavioralSignature


def _generate_id() -> str:
    """Generate a unique ID."""
    return secrets.token_urlsafe(32)


def _signature_to_row(signature: BehavioralSignature, retention_hours: int = 96) -> DRTBehavioralSignatureRow:
    """Convert BehavioralSignature to database row."""
    return DRTBehavioralSignatureRow(
        id=_generate_id(),
        path_pattern=signature.path_pattern,
        method=signature.method,
        headers=list(signature.headers),
        body_pattern=signature.body_pattern,
        query_pattern=signature.query_pattern,
        request_count=signature.request_count,
        timestamp=signature.timestamp,
        retention_hours=retention_hours,
        meta={},  # Reserved for future use
    )


def _row_to_signature(row: DRTBehavioralSignatureRow) -> BehavioralSignature:
    """Convert database row to BehavioralSignature."""
    sig = BehavioralSignature(
        path_pattern=row.path_pattern,
        method=row.method,
        headers=tuple(row.headers),
        body_pattern=row.body_pattern,
        query_pattern=row.query_pattern,
    )
    sig.timestamp = row.timestamp
    sig.request_count = row.request_count
    return sig


def _attack_vector_to_row(
    signature: BehavioralSignature, severity: str = "medium", description: str | None = None
) -> DRTAttackVectorRow:
    """Convert BehavioralSignature to attack vector database row."""
    return DRTAttackVectorRow(
        id=_generate_id(),
        path_pattern=signature.path_pattern,
        method=signature.method,
        headers=list(signature.headers),
        body_pattern=signature.body_pattern,
        query_pattern=signature.query_pattern,
        severity=severity,
        description=description,
        active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        meta={},  # Reserved for future use
    )


def _row_to_attack_vector(row: DRTAttackVectorRow) -> BehavioralSignature:
    """Convert database row to BehavioralSignature."""
    sig = BehavioralSignature(
        path_pattern=row.path_pattern,
        method=row.method,
        headers=tuple(row.headers),
        body_pattern=row.body_pattern,
        query_pattern=row.query_pattern,
    )
    sig.timestamp = row.created_at
    sig.request_count = 0  # Attack vectors don't track request count
    return sig


class DRTBehavioralSignatureRepository:
    """Repository for behavioral signature persistence."""

    def __init__(self, session: AsyncSession):
        self._db = session

    async def save(self, signature: BehavioralSignature, retention_hours: int = 96) -> str:
        """Save a behavioral signature to the database."""
        row = _signature_to_row(signature, retention_hours)
        self._db.add(row)
        await self._db.flush()
        return row.id

    async def save_many(self, signatures: list[BehavioralSignature], retention_hours: int = 96) -> list[str]:
        """Save multiple behavioral signatures."""
        ids = []
        for signature in signatures:
            row = _signature_to_row(signature, retention_hours)
            self._db.add(row)
            ids.append(row.id)
        await self._db.flush()
        return ids

    async def get_recent(self, hours: int = 96) -> list[BehavioralSignature]:
        """Get signatures from the last N hours."""
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        result = await self._db.execute(
            select(DRTBehavioralSignatureRow)
            .where(DRTBehavioralSignatureRow.timestamp >= cutoff)
            .order_by(DRTBehavioralSignatureRow.timestamp.desc())
        )
        rows = result.scalars().all()
        return [_row_to_signature(row) for row in rows]

    async def get_by_path(self, path_pattern: str, method: str | None = None) -> list[BehavioralSignature]:
        """Get signatures by path pattern."""
        query = select(DRTBehavioralSignatureRow).where(DRTBehavioralSignatureRow.path_pattern == path_pattern)
        if method:
            query = query.where(DRTBehavioralSignatureRow.method == method)

        result = await self._db.execute(query)
        rows = result.scalars().all()
        return [_row_to_signature(row) for row in rows]

    async def count(self) -> int:
        """Get total count of behavioral signatures."""
        result = await self._db.execute(select(func.count()).select_from(DRTBehavioralSignatureRow))
        return int(result.scalar_one())

    async def cleanup_old(self, retention_hours: int = 96) -> int:
        """Remove old signatures beyond retention period."""
        cutoff = datetime.now(UTC) - timedelta(hours=retention_hours)
        result = await self._db.execute(
            delete(DRTBehavioralSignatureRow).where(DRTBehavioralSignatureRow.timestamp < cutoff)
        )
        return result.rowcount or 0


class DRTAttackVectorRepository:
    """Repository for attack vector persistence."""

    def __init__(self, session: AsyncSession):
        self._db = session

    async def save(
        self, signature: BehavioralSignature, severity: str = "medium", description: str | None = None
    ) -> str:
        """Save an attack vector to the database."""
        row = _attack_vector_to_row(signature, severity, description)
        self._db.add(row)
        await self._db.flush()
        return row.id

    async def get_all(self, active_only: bool = True) -> list[tuple[str, BehavioralSignature, str]]:
        """Get all attack vectors with their IDs and severity."""
        query = select(DRTAttackVectorRow)
        if active_only:
            query = query.where(DRTAttackVectorRow.active == True)

        result = await self._db.execute(query)
        rows = result.scalars().all()
        return [(row.id, _row_to_attack_vector(row), row.severity) for row in rows]

    async def get_by_path(self, path_pattern: str, method: str | None = None) -> list[tuple[str, BehavioralSignature]]:
        """Get attack vectors by path pattern."""
        query = select(DRTAttackVectorRow).where(
            DRTAttackVectorRow.path_pattern == path_pattern, DRTAttackVectorRow.active == True
        )
        if method:
            query = query.where(DRTAttackVectorRow.method == method)

        result = await self._db.execute(query)
        rows = result.scalars().all()
        return [(row.id, _row_to_attack_vector(row)) for row in rows]

    async def deactivate(self, attack_vector_id: str) -> bool:
        """Deactivate an attack vector."""
        result = await self._db.execute(
            update(DRTAttackVectorRow)
            .where(DRTAttackVectorRow.id == attack_vector_id)
            .values(active=False, updated_at=datetime.now(UTC))
        )
        return (result.rowcount or 0) > 0

    async def delete(self, attack_vector_id: str) -> bool:
        """Permanently delete an attack vector."""
        result = await self._db.execute(delete(DRTAttackVectorRow).where(DRTAttackVectorRow.id == attack_vector_id))
        return (result.rowcount or 0) > 0

    async def count(self, active_only: bool = True) -> int:
        """Get count of attack vectors."""
        query = select(func.count()).select_from(DRTAttackVectorRow)
        if active_only:
            query = query.where(DRTAttackVectorRow.active == True)

        result = await self._db.execute(query)
        return int(result.scalar_one())


class DRTViolationRepository:
    """Repository for violation record persistence."""

    def __init__(self, session: AsyncSession):
        self._db = session

    async def record(
        self,
        signature: BehavioralSignature,
        attack_vector_id: str,
        similarity_score: float,
        request_path: str,
        request_method: str,
        client_ip: str | None = None,
        user_agent: str | None = None,
        was_blocked: bool = False,
        action_taken: str = "escalate",
        meta: dict[str, Any] | None = None,
    ) -> str:
        """Record a detected violation."""
        # First save the signature
        sig_repo = DRTBehavioralSignatureRepository(self._db)
        signature_id = await sig_repo.save(signature)

        # Then record the violation
        row = DRTViolationRow(
            id=_generate_id(),
            signature_id=signature_id,
            attack_vector_id=attack_vector_id,
            similarity_score=similarity_score,
            request_path=request_path,
            request_method=request_method,
            client_ip=client_ip,
            user_agent=user_agent,
            was_blocked=was_blocked,
            action_taken=action_taken,
            timestamp=datetime.now(UTC),
            meta=meta or {},
        )
        self._db.add(row)
        await self._db.flush()
        return row.id

    async def get_recent(self, hours: int = 24, min_similarity: float = 0.0) -> list[dict[str, Any]]:
        """Get recent violations with filtering."""
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        result = await self._db.execute(
            select(DRTViolationRow)
            .where(DRTViolationRow.timestamp >= cutoff)
            .where(DRTViolationRow.similarity_score >= min_similarity)
            .order_by(DRTViolationRow.timestamp.desc())
        )
        rows = result.scalars().all()

        return [
            {
                "id": row.id,
                "similarity_score": row.similarity_score,
                "request_path": row.request_path,
                "request_method": row.request_method,
                "client_ip": row.client_ip,
                "was_blocked": row.was_blocked,
                "timestamp": row.timestamp.isoformat(),
            }
            for row in rows
        ]

    async def count(self, hours: int | None = None) -> int:
        """Get total count of violations."""
        query = select(func.count()).select_from(DRTViolationRow)
        if hours:
            cutoff = datetime.now(UTC) - timedelta(hours=hours)
            query = query.where(DRTViolationRow.timestamp >= cutoff)

        result = await self._db.execute(query)
        return int(result.scalar_one())


class DRTEscalatedEndpointRepository:
    """Repository for escalated endpoint persistence."""

    def __init__(self, session: AsyncSession):
        self._db = session

    async def save(
        self,
        path: str,
        expires_at: datetime,
        similarity_score: float = 0.0,
        attack_vector_id: str | None = None,
        escalation_reason: str = "behavioral_similarity",
    ) -> str:
        """Save or update an escalated endpoint."""
        # Check if already exists
        existing = await self._db.execute(select(DRTEscalatedEndpointRow).where(DRTEscalatedEndpointRow.path == path))
        row = existing.scalar_one_or_none()

        if row:
            # Update existing
            row.escalation_count += 1
            row.expires_at = expires_at
            row.similarity_score = max(row.similarity_score, similarity_score)
            row.is_active = True
            await self._db.flush()
            return row.id
        else:
            # Create new
            new_row = DRTEscalatedEndpointRow(
                id=_generate_id(),
                path=path,
                escalation_reason=escalation_reason,
                similarity_score=similarity_score,
                matched_attack_vector_id=attack_vector_id,
                escalation_count=1,
                expires_at=expires_at,
                is_active=True,
                alert_sent=False,
            )
            self._db.add(new_row)
            await self._db.flush()
            return new_row.id

    async def get_active(self) -> list[tuple[str, datetime, float]]:
        """Get all currently active escalated endpoints."""
        now = datetime.now(UTC)
        result = await self._db.execute(
            select(DRTEscalatedEndpointRow)
            .where(DRTEscalatedEndpointRow.is_active == True)
            .where(DRTEscalatedEndpointRow.expires_at > now)
            .order_by(DRTEscalatedEndpointRow.expires_at.desc())
        )
        rows = result.scalars().all()
        return [(row.path, row.expires_at, row.similarity_score) for row in rows]

    async def deactivate(self, path: str) -> bool:
        """Deactivate an escalated endpoint."""
        result = await self._db.execute(
            update(DRTEscalatedEndpointRow).where(DRTEscalatedEndpointRow.path == path).values(is_active=False)
        )
        return (result.rowcount or 0) > 0

    async def cleanup_expired(self) -> int:
        """Deactivate all expired endpoints."""
        now = datetime.now(UTC)
        result = await self._db.execute(
            update(DRTEscalatedEndpointRow)
            .where(DRTEscalatedEndpointRow.expires_at < now)
            .where(DRTEscalatedEndpointRow.is_active == True)
            .values(is_active=False)
        )
        return result.rowcount or 0

    async def count_active(self) -> int:
        """Get count of active escalated endpoints."""
        now = datetime.now(UTC)
        result = await self._db.execute(
            select(func.count())
            .select_from(DRTEscalatedEndpointRow)
            .where(DRTEscalatedEndpointRow.is_active == True)
            .where(DRTEscalatedEndpointRow.expires_at > now)
        )
        return int(result.scalar_one())


class DRTConfigurationRepository:
    """Repository for DRT configuration persistence."""

    def __init__(self, session: AsyncSession):
        self._db = session

    async def get_or_create(self, config_id: str = "global") -> DRTConfigurationRow:
        """Get configuration or create with defaults."""
        result = await self._db.execute(select(DRTConfigurationRow).where(DRTConfigurationRow.id == config_id))
        row = result.scalar_one_or_none()

        if not row:
            row = DRTConfigurationRow(id=config_id)
            self._db.add(row)
            await self._db.flush()

        return row

    async def update(self, config_id: str = "global", **kwargs) -> bool:
        """Update configuration values."""
        # Remove any invalid keys
        valid_keys = {
            "enabled",
            "similarity_threshold",
            "retention_hours",
            "websocket_overhead",
            "auto_escalate",
            "escalation_timeout_minutes",
            "rate_limit_multiplier",
            "sampling_rate",
            "alert_on_escalation",
            "meta",
        }
        updates = {k: v for k, v in kwargs.items() if k in valid_keys}
        updates["updated_at"] = datetime.now(UTC)

        result = await self._db.execute(
            update(DRTConfigurationRow).where(DRTConfigurationRow.id == config_id).values(**updates)
        )
        return (result.rowcount or 0) > 0

    async def get_config_dict(self, config_id: str = "global") -> dict[str, Any]:
        """Get configuration as dictionary."""
        row = await self.get_or_create(config_id)
        return {
            "enabled": row.enabled,
            "similarity_threshold": row.similarity_threshold,
            "retention_hours": row.retention_hours,
            "websocket_overhead": row.websocket_overhead,
            "auto_escalate": row.auto_escalate,
            "escalation_timeout_minutes": row.escalation_timeout_minutes,
            "rate_limit_multiplier": row.rate_limit_multiplier,
            "alert_on_escalation": row.alert_on_escalation,
            "updated_at": row.updated_at.isoformat(),
            "meta": row.meta,
        }


class DRTFalsePositiveRepository:
    """Repository for false positive tracking."""

    def __init__(self, session: AsyncSession):
        self._db = session

    async def mark_false_positive(
        self,
        violation_id: str,
        marked_by: str | None = None,
        reason: str | None = None,
        confidence: float = 1.0,
        meta: dict[str, Any] | None = None,
    ) -> str:
        """Mark a violation as a false positive."""
        row = DRTFalsePositiveRow(
            id=_generate_id(),
            violation_id=violation_id,
            marked_by=marked_by,
            reason=reason,
            confidence=confidence,
            created_at=datetime.now(UTC),
            meta=meta or {},
        )
        self._db.add(row)
        await self._db.flush()
        return row.id

    async def get_by_violation(self, violation_id: str) -> DRTFalsePositiveRow | None:
        """Get false positive record for a specific violation."""
        result = await self._db.execute(
            select(DRTFalsePositiveRow).where(DRTFalsePositiveRow.violation_id == violation_id)
        )
        return result.scalar_one_or_none()

    async def get_recent(self, hours: int = 24, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent false positive records."""
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        result = await self._db.execute(
            select(DRTFalsePositiveRow)
            .where(DRTFalsePositiveRow.created_at >= cutoff)
            .order_by(DRTFalsePositiveRow.created_at.desc())
            .limit(limit)
        )
        rows = result.scalars().all()
        return [
            {
                "id": row.id,
                "violation_id": row.violation_id,
                "marked_by": row.marked_by,
                "reason": row.reason,
                "confidence": row.confidence,
                "created_at": row.created_at.isoformat(),
                "meta": row.meta,
            }
            for row in rows
        ]

    async def count(self, hours: int | None = None) -> int:
        """Count false positive records."""
        query = select(func.count()).select_from(DRTFalsePositiveRow)
        if hours:
            cutoff = datetime.now(UTC) - timedelta(hours=hours)
            query = query.where(DRTFalsePositiveRow.created_at >= cutoff)

        result = await self._db.execute(query)
        return int(result.scalar_one())

    async def get_false_positive_rate(self, hours: int = 24) -> float:
        """Calculate false positive rate over a time period."""
        cutoff = datetime.now(UTC) - timedelta(hours=hours)

        # Get total violations in time period
        violation_query = select(func.count()).select_from(DRTViolationRow).where(DRTViolationRow.timestamp >= cutoff)
        violation_result = await self._db.execute(violation_query)
        total_violations = int(violation_result.scalar_one())

        # Get false positives in time period
        fp_query = select(func.count()).select_from(DRTFalsePositiveRow).where(DRTFalsePositiveRow.created_at >= cutoff)
        fp_result = await self._db.execute(fp_query)
        false_positives = int(fp_result.scalar_one())

        if total_violations == 0:
            return 0.0

        return false_positives / total_violations


class DRTFalsePositivePatternRepository:
    """Repository for false positive pattern learning."""

    def __init__(self, session: AsyncSession):
        self._db = session

    async def record_pattern(
        self,
        signature: BehavioralSignature,
        is_false_positive: bool,
    ) -> None:
        """Record or update a pattern based on false positive feedback."""
        # Find existing pattern
        result = await self._db.execute(
            select(DRTFalsePositivePatternRow).where(
                DRTFalsePositivePatternRow.path_pattern == signature.path_pattern,
                DRTFalsePositivePatternRow.method == signature.method,
                DRTFalsePositivePatternRow.active == True,
            )
        )
        pattern = result.scalar_one_or_none()

        if pattern:
            # Update existing pattern
            pattern.total_violations += 1
            if is_false_positive:
                pattern.false_positive_count += 1
            pattern.false_positive_rate = pattern.false_positive_count / pattern.total_violations
            pattern.last_updated = datetime.now(UTC)

            # Update patterns if they match closely
            if signature.headers and set(signature.headers) != set(pattern.headers):
                # Merge header sets
                pattern.headers = list(set(pattern.headers) | set(signature.headers))

            if signature.body_pattern and signature.body_pattern != pattern.body_pattern:
                # For simplicity, keep the first pattern encountered
                pass

            if signature.query_pattern and signature.query_pattern != pattern.query_pattern:
                # For simplicity, keep the first pattern encountered
                pass
        else:
            # Create new pattern
            pattern = DRTFalsePositivePatternRow(
                id=_generate_id(),
                path_pattern=signature.path_pattern,
                method=signature.method,
                headers=list(signature.headers) if signature.headers else [],
                body_pattern=signature.body_pattern,
                query_pattern=signature.query_pattern,
                false_positive_count=1 if is_false_positive else 0,
                total_violations=1,
                false_positive_rate=1.0 if is_false_positive else 0.0,
                active=True,
                last_updated=datetime.now(UTC),
            )
            self._db.add(pattern)

        await self._db.flush()

    async def get_patterns_above_threshold(
        self, threshold: float = 0.8, active_only: bool = True
    ) -> list[dict[str, Any]]:
        """Get patterns with false positive rate above threshold."""
        query = select(DRTFalsePositivePatternRow).where(DRTFalsePositivePatternRow.false_positive_rate >= threshold)
        if active_only:
            query = query.where(DRTFalsePositivePatternRow.active == True)

        result = await self._db.execute(query)
        rows = result.scalars().all()
        return [
            {
                "id": row.id,
                "path_pattern": row.path_pattern,
                "method": row.method,
                "headers": row.headers,
                "body_pattern": row.body_pattern,
                "query_pattern": row.query_pattern,
                "false_positive_count": row.false_positive_count,
                "total_violations": row.total_violations,
                "false_positive_rate": row.false_positive_rate,
                "last_updated": row.last_updated.isoformat(),
            }
            for row in rows
        ]

    async def deactivate_pattern(self, pattern_id: str) -> bool:
        """Deactivate a false positive pattern."""
        result = await self._db.execute(
            update(DRTFalsePositivePatternRow)
            .where(DRTFalsePositivePatternRow.id == pattern_id)
            .values(active=False, last_updated=datetime.now(UTC))
        )
        return (result.rowcount or 0) > 0

    async def cleanup_old_patterns(self, days: int = 90) -> int:
        """Remove patterns that haven't been updated in specified days."""
        cutoff = datetime.now(UTC) - timedelta(days=days)
        result = await self._db.execute(
            delete(DRTFalsePositivePatternRow).where(
                DRTFalsePositivePatternRow.last_updated < cutoff, DRTFalsePositivePatternRow.active == True
            )
        )
        return result.rowcount or 0
