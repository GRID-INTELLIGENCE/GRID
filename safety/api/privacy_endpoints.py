from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from safety.api.auth import UserIdentity, get_current_user
from safety.observability.metrics import (
    PRIVACY_DETECTION_REQUESTS_TOTAL,
    PRIVACY_DETECTION_TOTAL,
    PRIVACY_MASKED_TOTAL,
)
from safety.privacy.core.engine import (
    get_privacy_engine,
    invalidate_context,
)
from safety.privacy.core.presets import PrivacyPreset
from safety.privacy.core.types import PrivacyAction, PrivacyResult

router = APIRouter(prefix="/privacy", tags=["privacy"])


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class DetectionRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to analyze for PII")
    context_id: str | None = Field(None, description="Workspace/Team ID for collaborative mode")
    preset: PrivacyPreset = Field(PrivacyPreset.BALANCED, description="Privacy strictness")


class MaskingRequest(DetectionRequest):
    user_choice: str | None = Field(None, description="User decision for interactive mode")


class BatchRequest(BaseModel):
    texts: list[str] = Field(..., max_length=100, description="List of texts to analyze")
    context_id: str | None = None
    preset: PrivacyPreset = PrivacyPreset.BALANCED


class PrivacyResponse(BaseModel):
    original_text: str
    processed_text: str | None
    detections: list[dict[str, Any]]
    action_taken: str | None
    masked: bool
    blocked: bool
    requires_user_input: bool


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/detect", response_model=PrivacyResponse)
async def detect_pii(
    request: DetectionRequest,
    user: UserIdentity = Depends(get_current_user),
):
    """
    Detect PII in text without modifying it.
    Useful for checking if content contains sensitive information.
    """
    PRIVACY_DETECTION_REQUESTS_TOTAL.labels(direction="input").inc()

    engine = get_privacy_engine(
        collaborative=bool(request.context_id),
        context_id=request.context_id,
        preset=request.preset,
    )

    detections = await engine.detect(request.text, request.context_id)

    # Record metrics
    for det in detections:
        PRIVACY_DETECTION_TOTAL.labels(
            pii_type=det["pii_type"],
            action="detect",
        ).inc()

    return PrivacyResponse(
        original_text=request.text,
        processed_text=request.text,
        detections=detections,
        action_taken=None,
        masked=False,
        blocked=False,
        requires_user_input=False,
    )


@router.post("/mask", response_model=PrivacyResponse)
async def mask_pii(
    request: MaskingRequest,
    user: UserIdentity = Depends(get_current_user),
):
    """
    Process text through the privacy shield, applying masking/blocking rules.
    If 'requires_user_input' returns True, the client should prompt the user
    and retry with 'user_choice'.
    """
    PRIVACY_DETECTION_REQUESTS_TOTAL.labels(direction="input").inc()

    engine = get_privacy_engine(
        collaborative=bool(request.context_id),
        context_id=request.context_id,
        preset=request.preset,
    )

    result: PrivacyResult = await engine.process(
        text=request.text,
        user_choice=request.user_choice,
        context_id=request.context_id,
    )

    if result.error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error,
        )

    # Record metrics for actions
    if result.detections:
        for det in result.detections:
            pii_type = det.get("pii_type", "UNKNOWN")
            action = result.action_taken

            if result.masked:
                PRIVACY_MASKED_TOTAL.labels(
                    pii_type=pii_type,
                    strategy="mask",
                ).inc()

    return PrivacyResponse(
        original_text=result.original_text,
        processed_text=result.processed_text,
        detections=result.detections,
        action_taken=result.action_taken.value if result.action_taken else None,
        masked=result.masked,
        blocked=result.blocked,
        requires_user_input=result.requires_user_input,
    )


@router.post("/batch", response_model=list[PrivacyResponse])
async def batch_process(
    request: BatchRequest,
    user: UserIdentity = Depends(get_current_user),
):
    """
    Process multiple text snippets in parallel.
    Efficient for scanning documents or chat history.
    """
    import asyncio

    engine = get_privacy_engine(
        collaborative=bool(request.context_id),
        context_id=request.context_id,
        preset=request.preset,
    )

    async def _process_one(text: str):
        res = await engine.process(text, context_id=request.context_id)
        return PrivacyResponse(
            original_text=res.original_text,
            processed_text=res.processed_text,
            detections=res.detections,
            action_taken=res.action_taken.value if res.action_taken else None,
            masked=res.masked,
            blocked=res.blocked,
            requires_user_input=res.requires_user_input,
        )

    tasks = [_process_one(t) for t in request.texts]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out exceptions (or handle them)
    final_results = []
    for r in results:
        if isinstance(r, Exception):
            # In a real batch pipeline, we might return error objects
            # For now, return a failed response
            final_results.append(
                PrivacyResponse(
                    original_text="<error>",
                    processed_text=None,
                    detections=[],
                    action_taken=None,
                    masked=False,
                    blocked=False,
                    requires_user_input=False,
                )
            )
        else:
            final_results.append(r)

    return final_results


@router.post("/context/invalidate")
async def invalidate_privacy_context(
    context_id: str,
    user: UserIdentity = Depends(get_current_user),
):
    """
    Invalidate the privacy cache for a specific context (workspace/team).
    Useful when privacy rules or permissions change for a group.
    """
    count = await invalidate_context(context_id)
    return {"status": "ok", "invalidated_entries": count}
