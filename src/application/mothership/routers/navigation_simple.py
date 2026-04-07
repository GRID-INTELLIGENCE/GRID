"""
Simple navigation endpoints for integration testing.

Minimal implementation without light_of_the_seven dependencies.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from typing import Annotated, Any, Literal, cast

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator

from application.mothership.dependencies import (
    Auth,
    PublicRateLimited,
    RateLimited,
    RequestContext,
    get_optional_authentication,
)
from application.mothership.schemas import ApiResponse, ResponseMeta

logger = logging.getLogger(__name__)

# Pre-hook: Dependency check
try:
    from sse_starlette.sse import EventSourceResponse
except ImportError:
    raise RuntimeError("Missing dependency: pip install sse-starlette")


router = APIRouter(prefix="/navigation", tags=["navigation"])
NavigationEngine = Literal["simple", "advanced", "hybrid"]
_VALID_ENGINES: tuple[NavigationEngine, ...] = ("simple", "advanced", "hybrid")


def _default_navigation_engine() -> NavigationEngine:
    raw = os.getenv("NAVIGATION_ENGINE", "simple").strip().lower()
    if raw in _VALID_ENGINES:
        return cast(NavigationEngine, raw)
    logger.warning("Invalid NAVIGATION_ENGINE=%s, falling back to simple", raw)
    return "simple"


class NavigationRequest(BaseModel):
    """Navigation request payload for integration testing."""

    goal: str = Field(..., description="Navigation goal", min_length=10)
    context: dict[str, Any] = Field(default_factory=dict, description="Navigation context")
    max_alternatives: int = Field(default=3, ge=1, le=10, description="Maximum alternative paths")
    enable_learning: bool = Field(default=True, description="Enable learning features")
    learning_weight: float = Field(default=0.3, ge=0.0, le=1.0, description="Learning weight")
    adaptation_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Adaptation threshold")
    engine: NavigationEngine | None = Field(
        default=None,
        description="Navigation engine selector (simple|advanced|hybrid). Defaults to NAVIGATION_ENGINE env var.",
    )
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
    selected_engine: NavigationEngine = Field(..., description="Engine used for the final plan")
    attempted_engines: list[NavigationEngine] = Field(default_factory=list, description="Engine execution order")
    fallback_used: bool = Field(default=False, description="Whether fallback logic was applied")
    fallback_reason: str | None = Field(default=None, description="Fallback reason, if any")


def _safe_request_id(request_context: RequestContext | None) -> str:
    """Extract request ID safely."""
    if request_context and hasattr(request_context, "request_id"):
        return str(request_context.request_id)
    return str(uuid.uuid4())


def _build_simple_paths(payload: NavigationRequest) -> tuple[dict[str, Any], list[dict[str, Any]], float]:
    """Create deterministic baseline navigation plan."""
    primary_path = {
        "steps": [
            {"action": "start", "location": "current"},
            {"action": "move_toward", "target": payload.goal},
            {"action": "arrive", "location": payload.goal},
        ],
        "estimated_time": 30.0,
        "confidence": 0.8,
    }

    alternatives = [
        {
            "steps": [
                {"action": "start", "location": "current"},
                {"action": "alternative_path", "variant": i + 1},
                {"action": "arrive", "location": payload.goal},
            ],
            "estimated_time": 35.0 + i * 5,
            "confidence": max(0.35, 0.7 - i * 0.1),
        }
        for i in range(min(payload.max_alternatives - 1, 2))
    ]
    return primary_path, alternatives, 0.8


def _build_advanced_paths(
    payload: NavigationRequest, ctx: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]], float]:
    """Create context-aware navigation plan without external module dependency."""
    complexity = min(len(ctx), 8)
    confidence = min(0.94, 0.74 + complexity * 0.02)
    stations = [
        {"action": "scope_goal", "station": "intake"},
        {"action": "analyze_constraints", "station": "analysis", "context_keys": sorted(ctx.keys())[:6]},
        {"action": "sequence_milestones", "station": "planner"},
        {"action": "execute_route", "station": "delivery", "target": payload.goal},
        {"action": "verify_outcome", "station": "validation"},
    ]
    estimated_time = round(24.0 + (len(payload.goal) / 18.0) + complexity * 1.4, 2)

    primary_path = {
        "steps": stations,
        "estimated_time": estimated_time,
        "confidence": confidence,
    }

    variants = min(payload.max_alternatives - 1, 3)
    alternatives: list[dict[str, Any]] = [
        {
            "steps": [
                {"action": "scope_goal", "station": "intake"},
                {"action": "route_variant", "station": "planner", "variant": idx + 1},
                {"action": "execute_route", "station": "delivery", "target": payload.goal},
                {"action": "verify_outcome", "station": "validation"},
            ],
            "estimated_time": round(estimated_time + (idx + 1) * 3.5, 2),
            "confidence": max(0.45, round(confidence - (idx + 1) * 0.07, 2)),
        }
        for idx in range(variants)
    ]

    return primary_path, alternatives, confidence


def _select_engine(payload: NavigationRequest) -> NavigationEngine:
    return payload.engine or _default_navigation_engine()


@router.post("/plan", response_model=ApiResponse[NavigationPlan])
async def create_navigation_plan(
    payload: NavigationRequest,
    request_context: RequestContext,
    auth: Annotated[dict[str, Any], Depends(get_optional_authentication)],
    _: PublicRateLimited,
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

    requested_engine = _select_engine(payload)
    plan_id = str(uuid.uuid4())
    processing_time = time.perf_counter()

    try:
        selected_engine: NavigationEngine = requested_engine
        attempted_engines: list[NavigationEngine] = []
        fallback_used = False
        fallback_reason: str | None = None

        if requested_engine == "simple":
            attempted_engines.append("simple")
            primary_path, alternatives, confidence = _build_simple_paths(payload)
        elif requested_engine == "advanced":
            attempted_engines.append("advanced")
            try:
                primary_path, alternatives, confidence = _build_advanced_paths(payload, ctx)
            except Exception as advanced_error:
                logger.warning("Advanced navigation engine failed, using simple fallback: %s", advanced_error)
                attempted_engines.append("simple")
                primary_path, alternatives, confidence = _build_simple_paths(payload)
                selected_engine = "simple"
                fallback_used = True
                fallback_reason = f"advanced_unavailable:{advanced_error}"
        else:
            attempted_engines.append("advanced")
            primary_path, alternatives, confidence = _build_advanced_paths(payload, ctx)
            if confidence < payload.adaptation_threshold:
                attempted_engines.append("simple")
                primary_path, alternatives, confidence = _build_simple_paths(payload)
                selected_engine = "simple"
                fallback_used = True
                fallback_reason = (
                    f"advanced_confidence_{confidence:.2f}_below_threshold_{payload.adaptation_threshold:.2f}"
                )
            else:
                selected_engine = "advanced"

        processing_time_ms = (time.perf_counter() - processing_time) * 1000

        plan = NavigationPlan(
            plan_id=plan_id,
            goal=payload.goal,
            primary_path=primary_path,
            alternatives=alternatives,
            confidence=confidence,
            processing_time_ms=processing_time_ms,
            request_id=request_id,
            selected_engine=selected_engine,
            attempted_engines=attempted_engines,
            fallback_used=fallback_used,
            fallback_reason=fallback_reason,
        )

        return ApiResponse(
            data=plan, meta=ResponseMeta(request_id=request_id, timestamp="2026-01-08T00:00:00Z", version="1.0.0")
        )

    except Exception as e:
        logger.error(f"Navigation plan creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"Navigation plan creation failed: {str(e)}"
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
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"Navigation decision failed: {str(e)}"
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
        "selected_engine": _select_engine(payload),
        "attempted_engines": [_select_engine(payload)],
        "fallback_used": False,
        "fallback_reason": None,
    }


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
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"Invalid payload in query: {str(e)}"
            )

    if payload is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Missing payload")

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
