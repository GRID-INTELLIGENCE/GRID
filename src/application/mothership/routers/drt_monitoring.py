"""
DRT (Don't Repeat Themselves) Monitoring Router.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..middleware.drt_middleware import BehavioralSignature, ComprehensiveDRTMiddleware

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..repositories.drt import (
    DRTAttackVectorRepository,
    DRTBehavioralSignatureRepository,
    DRTConfigurationRepository,
    DRTEscalatedEndpointRepository,
    DRTFalsePositivePatternRepository,
    DRTFalsePositiveRepository,
    DRTViolationRepository,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/drt", tags=["DRT Monitoring"])

_drt_middleware: ComprehensiveDRTMiddleware | None = None


def get_drt_middleware() -> ComprehensiveDRTMiddleware:
    global _drt_middleware
    if _drt_middleware is None:
        raise HTTPException(status_code=503, detail="DRT middleware not initialized")
    return _drt_middleware


class AttackVectorAddRequest(BaseModel):
    path_pattern: str
    method: str
    headers: list[str]
    body_pattern: str | None = None
    query_pattern: str | None = None


class StatusResponse(BaseModel):
    enabled: bool
    similarity_threshold: float
    retention_hours: int
    auto_escalate: bool
    escalated_endpoints_count: int
    behavioral_history_count: int
    attack_vectors_count: int
    timestamp: str


class FalsePositiveRequest(BaseModel):
    violation_id: str
    reason: str | None = None
    confidence: float = 1.0


class FalsePositiveResponse(BaseModel):
    id: str
    violation_id: str
    marked_by: str | None
    reason: str | None
    confidence: float
    created_at: str


class FalsePositiveStatsResponse(BaseModel):
    total_false_positives: int
    false_positive_rate: float
    recent_false_positives: int
    patterns_learned: int
    timestamp: str


@router.get("/status", response_model=StatusResponse)
async def get_drt_status(middleware: ComprehensiveDRTMiddleware = Depends(get_drt_middleware)) -> StatusResponse:
    status = middleware.get_status()
    return StatusResponse(
        enabled=status["enabled"],
        similarity_threshold=status["similarity_threshold"],
        retention_hours=status["retention_hours"],
        auto_escalate=status["auto_escalate"],
        escalated_endpoints_count=status["escalated_endpoints"],
        behavioral_history_count=status["behavioral_history_count"],
        attack_vectors_count=status["attack_vectors_count"],
        timestamp=datetime.now(UTC).isoformat(),
    )


@router.post("/attack-vectors")
async def add_attack_vector(
    request: AttackVectorAddRequest, middleware: ComprehensiveDRTMiddleware = Depends(get_drt_middleware)
) -> dict[str, str]:
    signature = BehavioralSignature(
        path_pattern=request.path_pattern,
        method=request.method,
        headers=tuple(request.headers),
        body_pattern=request.body_pattern,
        query_pattern=request.query_pattern,
    )
    middleware.add_attack_vector(signature)
    return {"status": "success", "message": f"Attack vector added: {request.path_pattern}"}


@router.get("/escalated-endpoints")
async def get_escalated_endpoints(
    middleware: ComprehensiveDRTMiddleware = Depends(get_drt_middleware),
) -> dict[str, Any]:
    now = datetime.now(UTC)
    escalated = {path: expires.isoformat() for path, expires in middleware.ESCALATED_ENDPOINTS.items() if expires > now}
    return {"escalated_endpoints": escalated}


@router.post("/escalate/{path:path}")
async def escalate_endpoint(
    path: str, middleware: ComprehensiveDRTMiddleware = Depends(get_drt_middleware)
) -> dict[str, str]:
    middleware._escalate_endpoint(path)
    return {"status": "success", "message": f"Endpoint escalated: {path}"}


@router.post("/de-escalate/{path:path}")
async def de_escalate_endpoint(
    path: str, middleware: ComprehensiveDRTMiddleware = Depends(get_drt_middleware)
) -> dict[str, str]:
    if path in middleware.ESCALATED_ENDPOINTS:
        del middleware.ESCALATED_ENDPOINTS[path]
        return {"status": "success", "message": f"Endpoint de-escalated: {path}"}
    return {"status": "warning", "message": f"Endpoint not found in escalated list: {path}"}


@router.get("/behavioral-history")
async def get_behavioral_history(
    middleware: ComprehensiveDRTMiddleware = Depends(get_drt_middleware),
) -> dict[str, Any]:
    history = [
        {
            "path_pattern": b.path_pattern,
            "method": b.method,
            "timestamp": b.timestamp.isoformat(),
            "request_count": b.request_count,
        }
        for b in middleware.behavioral_history[-100:]
    ]
    return {"behavioral_history": history}


@router.post("/false-positives", response_model=FalsePositiveResponse)
async def mark_false_positive(
    request: FalsePositiveRequest, middleware: ComprehensiveDRTMiddleware = Depends(get_drt_middleware)
) -> FalsePositiveResponse:
    """Mark a violation as a false positive."""
    from ..db.engine import get_db_session
    from ..middleware.drt_metrics import record_false_positive

    async with get_db_session() as session:
        fp_repo = DRTFalsePositiveRepository(session)
        pattern_repo = DRTFalsePositivePatternRepository(session)
        violation_repo = DRTViolationRepository(session)

        # Mark the violation as false positive
        fp_id = await fp_repo.mark_false_positive(
            violation_id=request.violation_id,
            reason=request.reason,
            confidence=request.confidence,
            marked_by="api_user",  # Could be enhanced to get actual user
        )

        # Record metrics
        record_false_positive()

        # Get violation details for pattern learning
        violation = await violation_repo.get_recent(limit=1, min_similarity=0.0)
        if violation:
            # Extract signature from violation (simplified - in real implementation
            # you'd reconstruct the signature from violation metadata)
            from ..middleware.drt_middleware import BehavioralSignature

            signature = BehavioralSignature(
                path_pattern=violation[0]["request_path"],
                method=violation[0]["request_method"],
                headers=[],  # Would need to extract from meta
            )

            # Record pattern for learning
            await pattern_repo.record_pattern(signature, is_false_positive=True)

        return FalsePositiveResponse(
            id=fp_id,
            violation_id=request.violation_id,
            marked_by="api_user",
            reason=request.reason,
            confidence=request.confidence,
            created_at=datetime.now(UTC).isoformat(),
        )


@router.get("/false-positives/stats", response_model=FalsePositiveStatsResponse)
async def get_false_positive_stats(
    middleware: ComprehensiveDRTMiddleware = Depends(get_drt_middleware),
) -> FalsePositiveStatsResponse:
    """Get false positive statistics."""
    from ..db.engine import get_db_session

    async with get_db_session() as session:
        fp_repo = DRTFalsePositiveRepository(session)
        pattern_repo = DRTFalsePositivePatternRepository(session)

        # Get statistics
        total_fp = await fp_repo.count()
        recent_fp = await fp_repo.count(hours=24)
        fp_rate = await fp_repo.get_false_positive_rate(hours=24)

        # Get learned patterns
        patterns = await pattern_repo.get_patterns_above_threshold(threshold=0.5)
        patterns_learned = len(patterns)

        return FalsePositiveStatsResponse(
            total_false_positives=total_fp,
            false_positive_rate=fp_rate,
            recent_false_positives=recent_fp,
            patterns_learned=patterns_learned,
            timestamp=datetime.now(UTC).isoformat(),
        )


@router.get("/false-positives/recent")
async def get_recent_false_positives(
    hours: int = 24, limit: int = 50, middleware: ComprehensiveDRTMiddleware = Depends(get_drt_middleware)
) -> dict[str, Any]:
    """Get recent false positive records."""
    from ..db.engine import get_db_session

    async with get_db_session() as session:
        fp_repo = DRTFalsePositiveRepository(session)

        false_positives = await fp_repo.get_recent(hours=hours, limit=limit)

        return {
            "false_positives": false_positives,
            "count": len(false_positives),
            "hours": hours,
            "timestamp": datetime.now(UTC).isoformat(),
        }


@router.get("/false-positive-patterns")
async def get_false_positive_patterns(
    threshold: float = 0.8,
    active_only: bool = True,
    middleware: ComprehensiveDRTMiddleware = Depends(get_drt_middleware),
) -> dict[str, Any]:
    """Get learned false positive patterns."""
    from ..db.engine import get_db_session

    async with get_db_session() as session:
        pattern_repo = DRTFalsePositivePatternRepository(session)

        patterns = await pattern_repo.get_patterns_above_threshold(threshold=threshold, active_only=active_only)

        return {
            "patterns": patterns,
            "count": len(patterns),
            "threshold": threshold,
            "active_only": active_only,
            "timestamp": datetime.now(UTC).isoformat(),
        }


@router.delete("/false-positive-patterns/{pattern_id}")
async def deactivate_false_positive_pattern(
    pattern_id: str, middleware: ComprehensiveDRTMiddleware = Depends(get_drt_middleware)
) -> dict[str, str]:
    """Deactivate a false positive pattern."""
    from ..db.engine import get_db_session

    async with get_db_session() as session:
        pattern_repo = DRTFalsePositivePatternRepository(session)

        success = await pattern_repo.deactivate_pattern(pattern_id)

        if success:
            return {"status": "success", "message": f"Pattern {pattern_id} deactivated"}
        else:
            raise HTTPException(status_code=404, detail=f"Pattern {pattern_id} not found")


def set_drt_middleware(middleware: ComprehensiveDRTMiddleware) -> None:
    global _drt_middleware
    _drt_middleware = middleware
