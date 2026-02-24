"""
Reasoning stabilization router.

Provides API endpoints for stabilized reasoning traces, drift checks,
and human/system roundtable reconciliation.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, HTTPException, Query, status

from application.mothership.dependencies import Auth, RateLimited, RequestContext
from application.mothership.schemas import ApiResponse, ResponseMeta
from application.mothership.schemas.reasoning import (
    DriftCheckRequest,
    DriftCheckResponse,
    GapStatus,
    InferenceGapListResponse,
    RoundtableReconcileRequest,
    RoundtableReconcileResponse,
    StabilizeRequest,
    StabilizeResponse,
)
from application.mothership.services.reasoning_stability import ReasoningStabilityService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["reasoning"])

_SERVICE: ReasoningStabilityService | None = None


def get_reasoning_service() -> ReasoningStabilityService:
    """Get singleton reasoning stability service."""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = ReasoningStabilityService()
    return _SERVICE


def reset_reasoning_service() -> None:
    """Reset singleton service (test utility)."""
    global _SERVICE
    _SERVICE = None


def _safe_request_id(request_context: RequestContext | None) -> str:
    if request_context and isinstance(request_context, dict):
        rid = request_context.get("request_id")
        if rid:
            return str(rid)
    return str(uuid.uuid4())


@router.post("/stabilize", response_model=ApiResponse[StabilizeResponse])
async def stabilize_reasoning(
    payload: StabilizeRequest,
    request_context: RequestContext,
    _auth: Auth,
    _: RateLimited,
) -> ApiResponse[StabilizeResponse]:
    """Generate stabilized reasoning trace and quality record."""
    try:
        service = get_reasoning_service()
        request_id = _safe_request_id(request_context)
        case_id = payload.case_id or service.derive_case_id(payload.input)

        result = service.stabilize(
            input_text=payload.input,
            context=payload.context,
            task_type=payload.task_type,
            risk_level=payload.risk_level.value,
            case_id=case_id,
            include_gap_log=payload.include_gap_log,
        )

        return ApiResponse(
            success=True,
            data=result,
            meta=ResponseMeta(request_id=request_id),
            message=f"Reasoning stabilized for case_id={case_id}",
        )
    except Exception as exc:
        logger.exception("Reasoning stabilization failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Failed to stabilize reasoning: {exc}",
        ) from exc


@router.post("/drift-check", response_model=ApiResponse[DriftCheckResponse])
async def drift_check(
    payload: DriftCheckRequest,
    request_context: RequestContext,
    _auth: Auth,
    _: RateLimited,
) -> ApiResponse[DriftCheckResponse]:
    """Detect contradiction and intent drift before response release."""
    try:
        service = get_reasoning_service()
        request_id = _safe_request_id(request_context)
        fallback_case_id = service.derive_case_id(payload.candidate_response)
        case_id = payload.case_id or fallback_case_id

        result = service.drift_check(
            trace_so_far=payload.trace_so_far,
            candidate_response=payload.candidate_response,
            case_id=case_id,
            include_gap_log=payload.include_gap_log,
        )

        return ApiResponse(
            success=True,
            data=result,
            meta=ResponseMeta(request_id=request_id),
            message=f"Drift analysis completed for case_id={case_id}",
        )
    except Exception as exc:
        logger.exception("Drift check failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Failed to run drift check: {exc}",
        ) from exc


@router.post("/roundtable/reconcile", response_model=ApiResponse[RoundtableReconcileResponse])
async def roundtable_reconcile(
    payload: RoundtableReconcileRequest,
    request_context: RequestContext,
    _auth: Auth,
    _: RateLimited,
) -> ApiResponse[RoundtableReconcileResponse]:
    """Reconcile system trace with human notes using equal-weight roundtable logic."""
    try:
        service = get_reasoning_service()
        request_id = _safe_request_id(request_context)

        result = service.reconcile_roundtable(
            case_id=payload.case_id,
            human_notes=payload.human_notes,
            system_trace=payload.system_trace,
            topic=payload.topic,
        )

        return ApiResponse(
            success=True,
            data=result,
            meta=ResponseMeta(request_id=request_id),
            message=f"Roundtable reconciliation completed for case_id={payload.case_id}",
        )
    except Exception as exc:
        logger.exception("Roundtable reconciliation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Failed to reconcile roundtable: {exc}",
        ) from exc


@router.get("/inference-gaps/{case_id}", response_model=ApiResponse[InferenceGapListResponse])
async def list_inference_gaps(
    case_id: str,
    request_context: RequestContext,
    _auth: Auth,
    _: RateLimited,
    status_filter: GapStatus | None = Query(default=None, alias="status", description="Gap status filter"),
    limit: int = Query(default=100, ge=1, le=500),
) -> ApiResponse[InferenceGapListResponse]:
    """List persisted inference gaps for a case."""
    try:
        service = get_reasoning_service()
        request_id = _safe_request_id(request_context)
        records = service.list_case_gaps(case_id=case_id, status=status_filter, limit=limit)

        return ApiResponse(
            success=True,
            data=InferenceGapListResponse(case_id=case_id, total=len(records), records=records),
            meta=ResponseMeta(request_id=request_id),
        )
    except Exception as exc:
        logger.exception("Failed to list inference gaps: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Failed to list inference gaps: {exc}",
        ) from exc
