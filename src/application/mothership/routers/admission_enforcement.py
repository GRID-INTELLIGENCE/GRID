"""API endpoints for admission gate enforcement, penalty management, and policy compliance.

Exposes the AdmissionGateMiddleware's entity attribution engine, penalty system,
and policy billboard as queryable/actionable REST endpoints. These are the precise
tool call definitions that make the admission gate's enforcement mechanisms
externally callable — by the CLI, MCP servers, frontends, or automated pipelines.

Endpoints:
    GET  /admission/policy              — current policy billboard snapshot
    GET  /admission/stats               — gate counters and rejection breakdown
    GET  /admission/entity/{entity_id}  — full entity report (violations, penalty, tier)
    GET  /admission/entities/bannered   — list all bannered entities
    POST /admission/compliance/check    — dry-run payload compliance check
    POST /admission/penalty/apply       — manually apply penalty to entity
    POST /admission/penalty/revoke      — revoke banner or reduce penalty
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ..dependencies import AdminAuth
from ..middleware.admission_gate import (
    BILLBOARD_VERSION,
    PROFIT_MASK_SIGNALS,
    EntityAttributionEngine,
    PolicyBillboard,
    ViolationType,
)
from ..security.merit_standing import ActionClass as MeritActionClass
from ..security.merit_standing import Scope as MeritScope
from ..security.merit_standing import get_merit_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admission", tags=["Admission Gate Enforcement"])


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------


class PolicyBillboardResponse(BaseModel):
    """Full policy billboard snapshot with version and timestamp."""

    billboard_version: str
    principles: dict[str, bool]
    ethical_dos: list[str]
    ethical_donts: list[str]
    penalty_tiers: dict[str, str]
    caution: str
    evolution_notice: str
    timestamp: str


class GateStatsResponse(BaseModel):
    """Admission gate operational statistics."""

    total_admitted: int
    total_rejected: int
    rejection_reasons: dict[str, int]
    tracked_entities: int
    bannered_entities: int
    timestamp: str


class ViolationDetail(BaseModel):
    """Single violation record."""

    type: str
    penalty_points: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class EntityReportResponse(BaseModel):
    """Full entity report — violations, penalty, tier classification."""

    entity_id: str
    found: bool
    violation_count: int = 0
    total_penalty_points: int = 0
    bannered: bool = False
    banner_reason: str = ""
    profit_mask_violations: int = 0
    penalty_tier: str = "none"
    tier_description: str = ""
    violations: list[ViolationDetail] = Field(default_factory=list)
    timestamp: str = ""


class BanneredEntitiesResponse(BaseModel):
    """List of all bannered entities."""

    count: int
    entities: list[EntityReportResponse]
    timestamp: str


class ComplianceCheckRequest(BaseModel):
    """Dry-run compliance check against the admission policy."""

    payload: dict[str, Any] = Field(..., description="Payload body to check")
    headers: dict[str, str] = Field(default_factory=dict, description="Headers to scan for profit-mask signals")
    entity_id: str | None = Field(None, description="Entity ID for context (optional)")
    target_path: str = Field("/api/v1/intelligence/process", description="Simulated request path")


class PermissionCheckRequest(BaseModel):
    """Permission check request for merit standing gate."""

    entity_id: str = Field(..., description="Entity identifier (e.g., mcp:server:session)")
    action_class: str = Field(..., description="Action class: public_basic, analysis_read, action_write, control_admin")
    required_scope: str | None = Field(
        None,
        description="Optional specific scope required: read, write, admin, analysis, control",
    )


class PermissionCheckResponse(BaseModel):
    """Merit standing permission decision (shape matches @cascade/shared-types PermissionCheckResult)."""

    allowed: bool
    entity_id: str
    action_class: str
    required_badge: str
    actual_badge: str
    has_badge: bool
    required_scopes: list[str]
    eligible_scopes: list[str]
    has_scopes: bool
    required_scope: str | None = None
    has_specific_scope: bool
    score: int
    roll_number: int


class ComplianceCheckResponse(BaseModel):
    """Result of a dry-run compliance check."""

    compliant: bool
    violations: list[str]
    profit_mask_signals: list[str]
    estimated_tokens: int
    context_ceiling_exceeded: bool
    has_required_structure: bool
    entity_penalty_points: int = 0
    entity_bannered: bool = False
    policy: dict[str, Any]
    timestamp: str


class PenaltyApplyRequest(BaseModel):
    """Manually apply a penalty to an entity."""

    entity_id: str = Field(..., description="Entity to penalize")
    violation_type: str = Field(
        ...,
        description="One of: budget_exceeded, origin_denied, context_overflow, "
        "invalid_body, missing_structure, profit_masking",
    )
    profit_masked: bool = Field(False, description="Apply 3x multiplier for profit-masking")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional context")
    reason: str = Field("manual_enforcement", description="Human-readable reason")


class PenaltyApplyResponse(BaseModel):
    """Result of penalty application."""

    success: bool
    entity_id: str
    violation_type: str
    penalty_points_applied: int
    total_penalty_points: int
    bannered: bool
    penalty_tier: str
    message: str
    timestamp: str


class PenaltyRevokeRequest(BaseModel):
    """Revoke a banner or reduce penalty for an entity."""

    entity_id: str = Field(..., description="Entity to modify")
    action: str = Field(
        ...,
        description="One of: revoke_banner, reduce_penalty, full_reset",
    )
    reduction_points: int = Field(0, description="Points to subtract (for reduce_penalty)")
    reason: str = Field("", description="Reason for revocation")


# Merit Standing request/response models
class MeritStandingResponse(BaseModel):
    """Merit standing for an entity."""

    entity_id: str
    badge: str
    score: int
    roll_number: int
    total_penalty_points: int
    recent_critical_penalty: int
    clean_streak: int
    clean_streak_bonus: int
    review_adjustment: int
    last_reviewed_at: str | None
    eligible_scopes: list[str]
    first_seen_at: str | None
    last_seen_at: str | None
    violation_count: int
    timestamp: str


class MeritLeaderboardResponse(BaseModel):
    """Merit standing leaderboard."""

    entities: list[MeritStandingResponse]
    count: int
    timestamp: str


class ReviewAdjustRequest(BaseModel):
    """Request to adjust entity review standing."""

    entity_id: str = Field(..., description="Entity to adjust")
    adjustment: int = Field(..., ge=-10, le=10, description="Adjustment value -10 to +10")
    reason: str = Field("", description="Reason for adjustment")


class ReviewAdjustResponse(BaseModel):
    """Response from review adjustment."""

    success: bool
    entity_id: str
    adjustment: int
    new_score: int
    new_badge: str
    new_roll_number: int
    message: str
    timestamp: str


class PenaltyRevokeResponse(BaseModel):
    """Result of penalty revocation."""

    success: bool
    entity_id: str
    action: str
    previous_points: int
    current_points: int
    was_bannered: bool
    is_bannered: bool
    message: str
    timestamp: str



# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_attribution(request: Request) -> EntityAttributionEngine:
    """Retrieve the shared EntityAttributionEngine from app state."""
    attr = getattr(request.app.state, "admission_attribution", None)
    if attr is None:
        raise HTTPException(
            status_code=503,
            detail="Admission gate is not active. Enable it in Mothership settings.",
        )
    return attr


def _classify_tier(record) -> tuple[str, str]:
    """Classify an entity's current penalty tier."""
    if record.profit_mask_violations > 0:
        return "intentional_scheming", ("3x accelerated penalty. Profit-masking or safety bypass detected.")
    if record.violation_count > 1 and record.total_penalty_points > 0:
        return "environment_pollution", ("1x compounding penalty. Repeated violations reducing effective budget.")
    if record.violation_count > 0:
        return "runtime_mistake", "1x base penalty. Correctable incident."
    return "none", "No violations recorded."


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/policy",
    response_model=PolicyBillboardResponse,
    summary="Get current policy billboard",
    description=(
        "Returns the full ethical participation contract displayed at the top "
        "of every execution chain. Includes principles, dos/don'ts, penalty "
        "tiers, caution, and evolution notice."
    ),
)
async def get_policy_billboard(request: Request) -> PolicyBillboardResponse:
    _get_attribution(request)  # ensure gate is active
    billboard = getattr(request.app.state, "admission_billboard", None)
    if billboard is None:
        raise HTTPException(status_code=503, detail="Admission billboard not loaded.")
    snap = billboard.snapshot()
    return PolicyBillboardResponse(**snap, timestamp=_now_iso())


@router.get(
    "/stats",
    response_model=GateStatsResponse,
    summary="Get gate statistics",
    description="Returns admission/rejection counters and breakdown by rejection reason.",
)
async def get_gate_stats(request: Request) -> GateStatsResponse:
    attr = _get_attribution(request)
    return GateStatsResponse(
        total_admitted=attr.total_admitted,
        total_rejected=attr.total_rejected,
        rejection_reasons=dict(attr.rejection_reasons),
        tracked_entities=len(attr.entities),
        bannered_entities=len(attr.bannered_entities()),
        timestamp=_now_iso(),
    )


@router.get(
    "/entity/{entity_id:path}",
    response_model=EntityReportResponse,
    summary="Get entity report",
    description=(
        "Returns the full violation history, accumulated penalty points, "
        "banner status, and classified penalty tier for an entity."
    ),
)
async def get_entity_report(request: Request, entity_id: str) -> EntityReportResponse:
    attr = _get_attribution(request)
    record = attr.peek_record(entity_id)

    if record is None:
        return EntityReportResponse(
            entity_id=entity_id,
            found=False,
            penalty_tier="none",
            tier_description="Entity not tracked.",
            timestamp=_now_iso(),
        )

    report = attr.entity_report(entity_id)
    tier, tier_desc = _classify_tier(record)

    return EntityReportResponse(
        entity_id=record.entity_id,
        found=True,
        violation_count=report["violation_count"],
        total_penalty_points=report["total_penalty_points"],
        bannered=report["bannered"],
        banner_reason=report.get("banner_reason", ""),
        profit_mask_violations=report.get("profit_mask_violations", 0),
        penalty_tier=tier,
        tier_description=tier_desc,
        violations=[
            ViolationDetail(
                type=v["type"],
                penalty_points=v["penalty_points"],
                metadata=v.get("metadata", {}),
            )
            for v in report.get("violations", [])
        ],
        timestamp=_now_iso(),
    )


@router.get(
    "/entities/bannered",
    response_model=BanneredEntitiesResponse,
    summary="List bannered entities",
    description="Returns all entities currently bannered (hard-blocked) by the admission gate.",
)
async def list_bannered_entities(request: Request) -> BanneredEntitiesResponse:
    attr = _get_attribution(request)
    bannered = attr.bannered_entities()

    entities = []
    for record in bannered:
        tier, tier_desc = _classify_tier(record)
        entities.append(
            EntityReportResponse(
                entity_id=record.entity_id,
                found=True,
                violation_count=record.violation_count,
                total_penalty_points=record.total_penalty_points,
                bannered=True,
                banner_reason=record.banner_reason,
                profit_mask_violations=record.profit_mask_violations,
                penalty_tier=tier,
                tier_description=tier_desc,
                violations=[
                    ViolationDetail(
                        type=v.violation_type.value,
                        penalty_points=v.penalty_points,
                        metadata=v.metadata,
                    )
                    for v in record.violations
                ],
                timestamp=_now_iso(),
            )
        )

    return BanneredEntitiesResponse(
        count=len(entities),
        entities=entities,
        timestamp=_now_iso(),
    )


@router.post(
    "/compliance/check",
    response_model=ComplianceCheckResponse,
    summary="Dry-run policy compliance check",
    description=(
        "Checks a payload against the admission policy without actually "
        "sending a request through the pipeline. Reports violations, "
        "profit-mask signals, context token estimate, and structural "
        "conformance. Use this to pre-validate before submission."
    ),
)
async def check_compliance(request: Request, body: ComplianceCheckRequest) -> ComplianceCheckResponse:
    attr = _get_attribution(request)
    context_ceiling = getattr(request.app.state, "admission_context_ceiling", 25_000)
    billboard = getattr(request.app.state, "admission_billboard", None)

    violations: list[str] = []
    import json

    # Profit-mask scan
    signals = attr.detect_profit_masking(body.payload, body.headers or None)
    if signals:
        violations.append(f"profit_masking: {', '.join(signals)}")

    # Context token estimate
    payload_bytes = len(json.dumps(body.payload, default=str).encode())
    estimated_tokens = payload_bytes // 4
    ceiling_exceeded = estimated_tokens > context_ceiling
    if ceiling_exceeded:
        violations.append(f"context_overflow: {estimated_tokens} tokens > ceiling {context_ceiling}")

    # Structure check
    has_structure = True
    if "/intelligence/" in body.target_path:
        if "data" not in body.payload:
            has_structure = False
            violations.append("missing_structure: 'data' key required for intelligence paths")

    # Entity context
    entity_points = 0
    entity_bannered = False
    if body.entity_id:
        record = attr.peek_record(body.entity_id)
        if record:
            entity_points = record.total_penalty_points
            entity_bannered = record.bannered
            if entity_bannered:
                violations.append(f"entity_bannered: {record.banner_reason}")

    policy_snap = billboard.snapshot() if billboard else {}
    return ComplianceCheckResponse(
        compliant=len(violations) == 0,
        violations=violations,
        profit_mask_signals=signals,
        estimated_tokens=estimated_tokens,
        context_ceiling_exceeded=ceiling_exceeded,
        has_required_structure=has_structure,
        entity_penalty_points=entity_points,
        entity_bannered=entity_bannered,
        policy=policy_snap,
        timestamp=_now_iso(),
    )


@router.post(
    "/check-permission",
    response_model=PermissionCheckResponse,
    summary="Check merit permission for an entity",
    description=(
        "Returns the merit standing permission decision for an entity. "
        "This endpoint is used by MCP servers to fail-closed on gated tools."
    ),
)
async def check_permission(body: PermissionCheckRequest) -> PermissionCheckResponse:
    engine = get_merit_engine()

    try:
        action = MeritActionClass(body.action_class)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"invalid_action_class: {body.action_class}") from e

    scope: MeritScope | None = None
    if body.required_scope:
        try:
            scope = MeritScope(body.required_scope)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"invalid_scope: {body.required_scope}") from e

    _allowed, details = engine.check_permission(body.entity_id, action, scope)
    return PermissionCheckResponse(**details)


@router.post(
    "/penalty/apply",
    response_model=PenaltyApplyResponse,
    summary="Apply penalty to entity",
    description=(
        "Manually apply a penalty to an entity. Used for out-of-band enforcement "
        "— when violations are detected by external systems (MCP servers, CLI, "
        "monitoring) outside the HTTP request flow. The 3x profit-mask multiplier "
        "is applied when profit_masked=true."
    ),
)
async def apply_penalty(request: Request, body: PenaltyApplyRequest, auth: AdminAuth) -> PenaltyApplyResponse:
    attr = _get_attribution(request)

    # Validate violation type
    try:
        vtype = ViolationType(body.violation_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid violation_type '{body.violation_type}'. Valid: {[v.value for v in ViolationType]}",
        )

    meta = {**body.metadata, "reason": body.reason, "source": "manual_enforcement"}

    violation = attr.record_violation(
        body.entity_id,
        vtype,
        profit_masked=body.profit_masked,
        metadata=meta,
    )

    record = attr.get_record(body.entity_id)
    tier, _ = _classify_tier(record)

    logger.info(
        "admission_enforcement.penalty_applied entity=%s type=%s points=%d total=%d bannered=%s",
        body.entity_id,
        body.violation_type,
        violation.penalty_points,
        record.total_penalty_points,
        record.bannered,
    )

    return PenaltyApplyResponse(
        success=True,
        entity_id=body.entity_id,
        violation_type=body.violation_type,
        penalty_points_applied=violation.penalty_points,
        total_penalty_points=record.total_penalty_points,
        bannered=record.bannered,
        penalty_tier=tier,
        message=f"Penalty applied: +{violation.penalty_points} points ({tier})",
        timestamp=_now_iso(),
    )


@router.post(
    "/penalty/revoke",
    response_model=PenaltyRevokeResponse,
    summary="Revoke banner or reduce penalty",
    description=(
        "Revoke a banner, reduce accumulated penalty points, or fully reset "
        "an entity's record. Used for remediation after an entity has corrected "
        "course. Actions: revoke_banner, reduce_penalty, full_reset."
    ),
)
async def revoke_penalty(request: Request, body: PenaltyRevokeRequest, auth: AdminAuth) -> PenaltyRevokeResponse:
    attr = _get_attribution(request)

    valid_actions = {"revoke_banner", "reduce_penalty", "full_reset"}
    if body.action not in valid_actions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action '{body.action}'. Valid: {sorted(valid_actions)}",
        )

    record = attr.get_record(body.entity_id)
    previous_points = record.total_penalty_points
    was_bannered = record.bannered

    match body.action:
        case "revoke_banner":
            record.bannered = False
            record.banner_reason = ""
            message = "Banner revoked. Entity may resume requests."
        case "reduce_penalty":
            reduction = min(body.reduction_points, record.total_penalty_points)
            record.total_penalty_points -= reduction
            # Un-banner if dropped below threshold
            if record.bannered and record.total_penalty_points < attr.banner_threshold:
                record.bannered = False
                record.banner_reason = ""
            message = f"Penalty reduced by {reduction} points."
        case "full_reset":
            record.violations.clear()
            record.total_penalty_points = 0
            record.bannered = False
            record.banner_reason = ""
            message = "Entity record fully reset."
        case _:
            raise HTTPException(status_code=400, detail=f"Unknown action: {body.action}")

    # Persist updated state to SQLite
    attr.persist_record(record)

    logger.info(
        "admission_enforcement.penalty_revoked entity=%s action=%s prev=%d curr=%d reason=%s",
        body.entity_id,
        body.action,
        previous_points,
        record.total_penalty_points,
        body.reason,
    )

    return PenaltyRevokeResponse(
        success=True,
        entity_id=body.entity_id,
        action=body.action,
        previous_points=previous_points,
        current_points=record.total_penalty_points,
        was_bannered=was_bannered,
        is_bannered=record.bannered,
        message=message,
        timestamp=_now_iso(),
    )


# ---------------------------------------------------------------------------
# Merit Standing Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/standing/{entity_id:path}",
    response_model=MeritStandingResponse,
    summary="Get merit standing for an entity",
    description=(
        "Returns the full merit standing for an entity including badge, score, "
        "roll number, eligible scopes, clean streak, and review adjustment."
    ),
)
async def get_merit_standing(request: Request, entity_id: str) -> MeritStandingResponse:
    attr = _get_attribution(request)
    standing = attr.get_merit_standing(entity_id)

    if standing is None:
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

    return MeritStandingResponse(
        entity_id=standing.entity_id,
        badge=standing.badge.value,
        score=standing.score,
        roll_number=standing.roll_number,
        total_penalty_points=standing.total_penalty_points,
        recent_critical_penalty=standing.recent_critical_penalty,
        clean_streak=standing.clean_streak,
        clean_streak_bonus=standing.clean_streak_bonus,
        review_adjustment=standing.review_adjustment,
        last_reviewed_at=standing.last_reviewed_at.isoformat() if standing.last_reviewed_at else None,
        eligible_scopes=[s.value for s in standing.eligible_scopes],
        first_seen_at=standing.first_seen_at.isoformat() if standing.first_seen_at else None,
        last_seen_at=standing.last_seen_at.isoformat() if standing.last_seen_at else None,
        violation_count=standing.violation_count,
        timestamp=_now_iso(),
    )


@router.get(
    "/leaderboard",
    response_model=MeritLeaderboardResponse,
    summary="Get merit leaderboard",
    description=(
        "Returns the ranked merit leaderboard. Entities are ordered by roll number "
        "(descending score, then lower penalties, then longer clean streak, then earlier first-seen)."
    ),
)
async def get_merit_leaderboard(request: Request, limit: int = 100) -> MeritLeaderboardResponse:
    attr = _get_attribution(request)
    standings = attr.get_merit_leaderboard(limit)

    entities = [
        MeritStandingResponse(
            entity_id=s["entity_id"],
            badge=s["badge"],
            score=s["score"],
            roll_number=s["roll_number"],
            total_penalty_points=s["total_penalty_points"],
            recent_critical_penalty=s["recent_critical_penalty"],
            clean_streak=s["clean_streak"],
            clean_streak_bonus=s["clean_streak_bonus"],
            review_adjustment=s["review_adjustment"],
            last_reviewed_at=s["last_reviewed_at"],
            eligible_scopes=s["eligible_scopes"],
            first_seen_at=s["first_seen_at"],
            last_seen_at=s["last_seen_at"],
            violation_count=s["violation_count"],
            timestamp=_now_iso(),
        )
        for s in standings
    ]

    return MeritLeaderboardResponse(
        entities=entities,
        count=len(entities),
        timestamp=_now_iso(),
    )


@router.post(
    "/review/adjust",
    response_model=ReviewAdjustResponse,
    summary="Apply manual review adjustment",
    description=(
        "Apply a manual review adjustment (-10 to +10) to an entity's merit standing. "
        "Used for twice-weekly review cadence to reward good behavior or penalize issues "
        "detected outside the automatic gate. Requires admin privileges."
    ),
)
async def apply_review_adjustment(
    request: Request,
    body: ReviewAdjustRequest,
    auth: AdminAuth,
) -> ReviewAdjustResponse:
    attr = _get_attribution(request)

    try:
        standing = attr.apply_review_adjustment(body.entity_id, body.adjustment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    logger.info(
        "admission_enforcement.review_adjusted entity=%s adjustment=%d new_score=%d badge=%s reason=%s",
        body.entity_id,
        body.adjustment,
        standing.score,
        standing.badge.value,
        body.reason,
    )

    return ReviewAdjustResponse(
        success=True,
        entity_id=body.entity_id,
        adjustment=body.adjustment,
        new_score=standing.score,
        new_badge=standing.badge.value,
        new_roll_number=standing.roll_number,
        message=f"Review adjustment applied: {body.adjustment:+d} points. New score: {standing.score}",
        timestamp=_now_iso(),
    )
