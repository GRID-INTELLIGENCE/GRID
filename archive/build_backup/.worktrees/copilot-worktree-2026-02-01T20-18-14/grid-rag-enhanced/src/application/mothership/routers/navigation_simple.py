"""
Simple navigation endpoints for integration testing.

Minimal implementation without light_of_the_seven dependencies.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from application.mothership.dependencies import Auth, RateLimited, RequestContext
from application.mothership.schemas import ApiResponse, ResponseMeta

logger = logging.getLogger(__name__)

# Pre-hook: Dependency check
try:
    from sse_starlette.sse import EventSourceResponse
except ImportError:
    raise RuntimeError("Missing dependency: pip install sse-starlette")


router = APIRouter(prefix="/navigation", tags=["navigation"])


class NavigationRequest(BaseModel):
    """Navigation request payload for integration testing."""

    goal: str = Field(..., description="Navigation goal", min_length=10)
    context: dict[str, Any] = Field(default_factory=dict, description="Navigation context")
    max_alternatives: int = Field(default=3, ge=1, le=10, description="Maximum alternative paths")
    enable_learning: bool = Field(default=True, description="Enable learning features")
    learning_weight: float = Field(default=0.3, ge=0.0, le=1.0, description="Learning weight")
    adaptation_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Adaptation threshold")
    source: str | None = Field(default="api", description="Request source")

    @field_validator("goal")
    @classmethod
    def validate_goal(cls, v: str) -> str:
        """Validate goal is not empty and has sufficient length."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Goal cannot be empty. Provide a goal description of at least 10 characters.")
        if len(stripped) < 10:
            raise ValueError(f"Goal must be at least 10 characters (current: {len(stripped)}).")
        return stripped


class NavigationPlan(BaseModel):
    """Navigation plan response."""

    plan_id: str = Field(..., description="Unique plan identifier")
    goal: str = Field(..., description="Original goal")
    primary_path: dict[str, Any] = Field(..., description="Primary navigation path")
    alternatives: list[dict[str, Any]] = Field(default_factory=list, description="Alternative paths")
    confidence: float = Field(..., description="Plan confidence", ge=0.0, le=1.0)
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    request_id: str = Field(..., description="Request correlation ID")


def _safe_request_id(request_context: RequestContext | None) -> str:
    """Extract request ID safely."""
    if request_context and hasattr(request_context, "request_id"):
        return str(request_context.request_id)
    return str(uuid.uuid4())


@router.post("/plan", response_model=ApiResponse[NavigationPlan])
async def create_navigation_plan(
    payload: NavigationRequest,
    request_context: RequestContext,
    auth: Auth,
    _: RateLimited,
) -> ApiResponse[NavigationPlan]:
    """
    Create a navigation plan.

    Simple implementation for integration testing.
    Supports development mode operation without authentication.
    """
    request_id = _safe_request_id(request_context)
    logger.info(f"Navigation plan request: {payload.goal} (ID: {request_id})")

    # Build context
    ctx: dict[str, Any] = dict(payload.context or {})
    if auth and isinstance(auth, dict):
        ctx.setdefault("user_id", auth.get("user_id"))
        ctx.setdefault("scopes", auth.get("scopes"))

    # Simple mock navigation plan
    plan_id = str(uuid.uuid4())
    processing_time = time.perf_counter()

    try:
        # Mock primary path
        primary_path = {
            "steps": [
                {"action": "start", "location": "current"},
                {"action": "move_toward", "target": payload.goal},
                {"action": "arrive", "location": payload.goal},
            ],
            "estimated_time": 30.0,
            "confidence": 0.8,
        }

        # Mock alternatives
        alternatives = []
        for i in range(min(payload.max_alternatives - 1, 2)):
            alternatives.append(
                {
                    "steps": [
                        {"action": "start", "location": "current"},
                        {"action": "alternative_path", "variant": i + 1},
                        {"action": "arrive", "location": payload.goal},
                    ],
                    "estimated_time": 35.0 + i * 5,
                    "confidence": 0.7 - i * 0.1,
                }
            )

        processing_time_ms = (time.perf_counter() - processing_time) * 1000

        plan = NavigationPlan(
            plan_id=plan_id,
            goal=payload.goal,
            primary_path=primary_path,
            alternatives=alternatives,
            confidence=0.8,
            processing_time_ms=processing_time_ms,
            request_id=request_id,
        )

        return ApiResponse(
            data=plan, meta=ResponseMeta(request_id=request_id, timestamp="2026-01-08T00:00:00Z", version="1.0.0")
        )

    except Exception as e:
        logger.error(f"Navigation plan creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Navigation plan creation failed: {str(e)}"
        ) from e


class DecisionRequest(BaseModel):
    """Decision request payload."""

    goal: str = Field(..., description="Decision goal", min_length=1, max_length=1000)
    context: dict[str, Any] = Field(default_factory=dict, description="Decision context")


@router.post("/decision", response_model=ApiResponse[dict[str, Any]])
async def create_navigation_decision(
    payload: DecisionRequest,
    request_context: RequestContext | None = None,
    auth: Auth | None = None,
    rate_limit: RateLimited = True,
) -> ApiResponse[dict[str, Any]]:
    """
    Make a navigation decision.

    Simple implementation for integration testing.
    """
    request_id = _safe_request_id(request_context)
    logger.info(f"Navigation decision request: {payload.goal} (ID: {request_id})")

    try:
        # Mock decision
        decision = {
            "decision_id": str(uuid.uuid4()),
            "goal": payload.goal,
            "recommended_action": "proceed",
            "confidence": 0.85,
            "reasoning": f"Simple mock reasoning for goal: {payload.goal}",
            "context_used": payload.context,
            "request_id": request_id,
        }

        return ApiResponse(
            data=decision, meta=ResponseMeta(request_id=request_id, timestamp="2026-01-08T00:00:00Z", version="1.0.0")
        )

    except Exception as e:
        logger.error(f"Navigation decision failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Navigation decision failed: {str(e)}"
        ) from e


def _mock_plan_result(payload: NavigationRequest, request_id: str) -> dict:
    """Generate a mock plan result for streaming."""
    return {
        "plan_id": str(uuid.uuid4()),
        "goal": payload.goal,
        "primary_path": {
            "steps": [
                {"action": "start", "location": "current"},
                {"action": "move_toward", "target": payload.goal},
                {"action": "arrive", "location": payload.goal},
            ],
            "estimated_time": 30.0,
            "confidence": 0.8,
        },
        "alternatives": [],
        "confidence": 0.8,
        "processing_time_ms": 1500.0,  # Simulated
        "request_id": request_id,
    }


from fastapi import APIRouter, Query

# ... (rest of imports)

# ... (existing code)


@router.post("/plan-stream", response_class=EventSourceResponse)
@router.get("/plan-stream", response_class=EventSourceResponse)
async def streaming_navigation_plan(
    payload: NavigationRequest | None = None,
    payload_str: str | None = Query(None, alias="payload"),
    request_context: RequestContext | None = None,
):
    # Handle GET request with payload query param
    if payload is None and payload_str:
        try:
            data = json.loads(payload_str)
            payload = NavigationRequest(**data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid payload in query: {str(e)}"
            )

    if payload is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Missing payload")

    request_id = _safe_request_id(request_context)

    async def event_generator():
        # Stage 1: Processing started
        yield {"event": "status", "data": json.dumps({"stage": "processing"})}

        # Stage 2: Simulate incremental results
        for i in range(1, 6):
            await asyncio.sleep(0.3)
            yield {"event": "progress", "data": json.dumps({"step": i, "progress": i * 20})}

        # Stage 3: Final payload
        result = _mock_plan_result(payload, request_id)
        yield {"event": "result", "data": json.dumps(result)}

    return EventSourceResponse(event_generator())
