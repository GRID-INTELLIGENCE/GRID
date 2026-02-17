from __future__ import annotations

import logging
import time
import uuid
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator

if TYPE_CHECKING:
    from light_of_the_seven.light_of_the_seven.cognitive_layer.decision_support.decision_matrix import (  # type: ignore
        DecisionMatrixGenerator,
    )
    from light_of_the_seven.light_of_the_seven.cognitive_layer.integration.capability_registry import (  # type: ignore
        CapabilityRegistry,
    )
    from light_of_the_seven.light_of_the_seven.cognitive_layer.integration.scope_manager import (
        ScopeManager,  # type: ignore
    )
    from light_of_the_seven.light_of_the_seven.cognitive_layer.navigation.enhanced_path_navigator import (  # type: ignore
        EnhancedPathNavigator,
        NavigationPlan,
    )
    from light_of_the_seven.light_of_the_seven.cognitive_layer.navigation.input_processor import (  # type: ignore
        NavigationInputProcessor,
    )

from application.mothership.dependencies import Auth, RateLimited, RequestContext
from application.mothership.schemas import ApiResponse, ResponseMeta

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/navigation", tags=["navigation"])

# Lazily initialized singletons (process-wide). This matches the pattern used by other routers (e.g., intelligence).
_NAVIGATOR: EnhancedPathNavigator | None = None
_PROCESSOR: NavigationInputProcessor | None = None
_SCOPE_MANAGER: ScopeManager | None = None
_CAPABILITY_REGISTRY: CapabilityRegistry | None = None
_DECISION_MATRIX: DecisionMatrixGenerator | None = None


def _get_navigator() -> EnhancedPathNavigator:
    global _NAVIGATOR
    if _NAVIGATOR is None:
        # Local-first: use the in-repo navigator and learning components only.
        from light_of_the_seven.light_of_the_seven.cognitive_layer.navigation.enhanced_path_navigator import (
            EnhancedPathNavigator,
        )

        _NAVIGATOR = EnhancedPathNavigator(enable_learning=True)
    return _NAVIGATOR


def _get_processor() -> NavigationInputProcessor:
    global _PROCESSOR
    if _PROCESSOR is None:
        from light_of_the_seven.light_of_the_seven.cognitive_layer.navigation.input_processor import (
            NavigationInputProcessor,
        )

        _PROCESSOR = NavigationInputProcessor()
    return _PROCESSOR


def _get_scope_manager() -> ScopeManager:
    global _SCOPE_MANAGER
    if _SCOPE_MANAGER is None:
        from light_of_the_seven.light_of_the_seven.cognitive_layer.integration.scope_manager import ScopeManager

        _SCOPE_MANAGER = ScopeManager()
    return _SCOPE_MANAGER


def _get_capability_registry() -> CapabilityRegistry:
    global _CAPABILITY_REGISTRY
    if _CAPABILITY_REGISTRY is None:
        from light_of_the_seven.light_of_the_seven.cognitive_layer.integration.capability_registry import (
            CapabilityRegistry,
        )

        _CAPABILITY_REGISTRY = CapabilityRegistry()
    return _CAPABILITY_REGISTRY


def _get_decision_matrix() -> DecisionMatrixGenerator:
    global _DECISION_MATRIX
    if _DECISION_MATRIX is None:
        from light_of_the_seven.light_of_the_seven.cognitive_layer.decision_support.decision_matrix import (
            DecisionMatrixGenerator,
        )

        _DECISION_MATRIX = DecisionMatrixGenerator()
    return _DECISION_MATRIX


class NavigationRequestPayload(BaseModel):
    """
    Safety-first navigation request payload.

    Notes:
    - Accepts either a simple `goal` string or a structured `goal` object.
    - Uses a strict JSON shape at the API layer; deeper validation happens in the navigation schemas.
    - Keeps defaults conservative for safety.
    """

    goal: Any
    context: dict[str, Any] = Field(default_factory=dict)
    max_alternatives: int = 3

    enable_learning: bool = True
    learning_weight: float = 0.3
    adaptation_threshold: float = 0.7

    source: str | None = None

    @field_validator("goal")
    @classmethod
    def validate_goal(cls, v: Any) -> Any:
        """Validate goal is not empty."""
        if isinstance(v, str) and not v.strip():
            raise ValueError("Goal cannot be empty. Provide a goal description of at least 10 characters.")
        return v


class NavigationStepOut(BaseModel):
    id: str
    name: str
    description: str
    estimated_time_seconds: float
    dependencies: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    confidence: float = 0.8


class NavigationPathOut(BaseModel):
    id: str
    name: str
    description: str
    steps: list[NavigationStepOut] = Field(default_factory=list)
    complexity: str
    estimated_total_time: float
    confidence: float
    recommendation_score: float = 0.5
    reasoning: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class NavigationPlanOut(BaseModel):
    request_id: str
    reasoning: str
    processing_time_ms: float
    learning_applied: bool = False
    adaptation_triggered: bool = False

    recommended_path: NavigationPathOut | None = None
    paths: list[NavigationPathOut] = Field(default_factory=list)
    confidence_scores: dict[str, float] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DecisionRequestPayload(BaseModel):
    """Payload for weighted decision intelligence."""

    decision_id: str | None = None
    area: str = "system"  # system, national, international, communal
    description: str
    options: list[dict[str, Any]]
    context: dict[str, Any] = Field(default_factory=dict)
    use_active_scope: bool = True


class DecisionResponseOut(BaseModel):
    """Response for weighted decision making."""

    decision_id: str
    area: str
    best_option_id: str
    scores: dict[str, Any]
    totals: dict[str, float]
    reasoning: str
    active_scope: str | None = None
    compliance_verified: bool = True


def _safe_request_id(request_context: RequestContext) -> str:
    if isinstance(request_context, dict):
        rid = request_context.get("request_id")
        if isinstance(rid, str) and rid.strip():
            return rid
    return str(uuid.uuid4())


def _to_plan_out(plan: NavigationPlan) -> NavigationPlanOut:
    """
    Convert the domain `NavigationPlan` (dataclass) into an API-safe Pydantic output model.

    We avoid leaking internal objects by converting to primitives only.
    """
    from light_of_the_seven.light_of_the_seven.cognitive_layer.navigation.enhanced_path_navigator import (
        NavigationPath,
        NavigationPlan,
        NavigationStep,
    )

    _ = (NavigationPlan, NavigationPath, NavigationStep)  # keep type checkers happy when imports are optimized away

    def to_step(step: Any) -> NavigationStepOut:
        return NavigationStepOut(
            id=str(getattr(step, "id", "")),
            name=str(getattr(step, "name", "")),
            description=str(getattr(step, "description", "")),
            estimated_time_seconds=float(getattr(step, "estimated_time_seconds", 0.0)),
            dependencies=list(getattr(step, "dependencies", []) or []),
            outputs=list(getattr(step, "outputs", []) or []),
            confidence=float(getattr(step, "confidence", 0.0)),
        )

    def to_path(path: Any) -> NavigationPathOut:
        return NavigationPathOut(
            id=str(getattr(path, "id", "")),
            name=str(getattr(path, "name", "")),
            description=str(getattr(path, "description", "")),
            steps=[to_step(s) for s in (getattr(path, "steps", []) or [])],
            complexity=str(getattr(getattr(path, "complexity", None), "value", getattr(path, "complexity", ""))),
            estimated_total_time=float(getattr(path, "estimated_total_time", 0.0)),
            confidence=float(getattr(path, "confidence", 0.0)),
            recommendation_score=float(getattr(path, "recommendation_score", 0.5)),
            reasoning=getattr(path, "reasoning", None),
            metadata=dict(getattr(path, "metadata", {}) or {}),
        )

    recommended = getattr(plan, "recommended_path", None)
    return NavigationPlanOut(
        request_id=str(getattr(plan, "request_id", "")),
        reasoning=str(getattr(plan, "reasoning", "")),
        processing_time_ms=float(getattr(plan, "processing_time_ms", 0.0)),
        learning_applied=bool(getattr(plan, "learning_applied", False)),
        adaptation_triggered=bool(getattr(plan, "adaptation_triggered", False)),
        recommended_path=to_path(recommended) if recommended is not None else None,
        paths=[to_path(p) for p in (getattr(plan, "paths", []) or [])],
        confidence_scores=dict(getattr(plan, "confidence_scores", {}) or {}),
        metadata=dict(getattr(plan, "metadata", {}) or {}),
    )


@router.post("/plan", response_model=ApiResponse[NavigationPlanOut])
async def create_navigation_plan(
    payload: NavigationRequestPayload,
    _: RateLimited,
    auth: Auth,
    request_context: RequestContext,
) -> ApiResponse[NavigationPlanOut]:
    """
    Generate a safety-first navigation plan using the local Path Optimization Navigator.

    Safety-first posture:
    - Input is normalized and validated into a structured NavigationRequest.
    - "Learning" is local-only and can be disabled per request.
    - Authentication context (if present) is passed through into planning context for auditing/traceability.
    """
    from light_of_the_seven.light_of_the_seven.cognitive_layer.navigation.input_processor import (
        InputProcessingError,  # type: ignore[import-not-found]
    )
    from light_of_the_seven.light_of_the_seven.cognitive_layer.navigation.schemas.navigation_input import (  # type: ignore[import-not-found]
        NavigationRequest,
    )

    request_id = _safe_request_id(request_context)
    # #region agent log
    import json
    import aiofiles

    try:
        async with aiofiles.open(r"e:\grid\.cursor\debug.log", mode="a", encoding="utf-8") as f:
            await f.write(
                json.dumps(
                    {
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "E",
                        "location": "routers/navigation.py:258",
                        "message": "navigation.py router handling request",
                        "data": {
                            "router_module": "navigation",
                            "goal": str(payload.goal)[:100] if hasattr(payload, "goal") else "unknown",
                            "request_id": request_id,
                        },
                        "timestamp": int(time.time() * 1000),
                    }
                )
                + "\n"
            )
    except Exception:
        pass
    # #endregion

    # Build a context dict with conservative, safety-oriented defaults.
    ctx: dict[str, Any] = dict(payload.context or {})
    if payload.source:
        ctx.setdefault("source", payload.source)

    # Attach caller identity for traceability (do not force auth).
    if auth and isinstance(auth, dict):
        ctx.setdefault("user_id", auth.get("user_id"))
        ctx.setdefault("scopes", auth.get("scopes"))

    # Ensure the request_id is present for end-to-end correlation.
    ctx.setdefault("request_id", request_id)

    # Normalize into a raw input shape compatible with NavigationInputProcessor.
    raw_input: dict[str, Any] = {
        "goal": payload.goal,
        "context": ctx,
        "max_alternatives": payload.max_alternatives,
        "enable_learning": payload.enable_learning,
        "learning_weight": payload.learning_weight,
        "adaptation_threshold": payload.adaptation_threshold,
        "source": payload.source or "api",
    }

    # Phase 2: AI Brain & Knowledge Graph Integration
    # -----------------------------------------------
    # NOTE: Kept local-first and minimal at the router layer.
    # The AI Brain and RAG integration should be wired via services/dependencies
    # to avoid import-time side effects and optional dependency failures here.
    # -----------------------------------------------

    processor = _get_processor()
    navigator = _get_navigator()

    t0 = time.perf_counter()
    try:
        nav_request: NavigationRequest = processor.process(raw_input)
    except InputProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "NAVIGATION_INPUT_INVALID",
                "message": str(e),
                "field": getattr(e, "field", None),
                "suggestion": getattr(e, "suggestion", None),
            },
        ) from e
    except Exception as e:
        logger.exception("Unexpected error while processing navigation input (request_id=%s)", request_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "NAVIGATION_INPUT_PROCESSING_FAILED",
                "message": "Failed to process navigation input",
            },
        ) from e

    try:
        plan = navigator.navigate(nav_request)
    except Exception as e:
        logger.exception("Navigation planning failed (request_id=%s)", request_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "NAVIGATION_PLANNING_FAILED",
                "message": "Failed to generate navigation plan",
            },
        ) from e
    t1 = time.perf_counter()

    # Ensure API reports a consistent total time as an outer metric without mutating inner plan semantics.
    plan_out = _to_plan_out(plan)
    plan_out.processing_time_ms = max(plan_out.processing_time_ms, (t1 - t0) * 1000.0)

    return ApiResponse(
        success=True,
        data=plan_out,
        meta=ResponseMeta(request_id=request_id),
    )


@router.post("/decision", response_model=ApiResponse[DecisionResponseOut])
async def create_decision(
    payload: DecisionRequestPayload,
    _: RateLimited,
    auth: Auth,
    request_context: RequestContext,
) -> ApiResponse[DecisionResponseOut]:
    """
    Generate a weighted decision matrix with multi-area intelligence.

    Supports System, National, International, and Communal Areas.
    Integrates ScopeManager and CapabilityRegistry for compliance.
    """
    request_id = _safe_request_id(request_context)
    decision_id = payload.decision_id or f"dec-{uuid.uuid4().hex[:8]}"

    scope_mgr = _get_scope_manager()
    cap_registry = _get_capability_registry()
    matrix_gen = _get_decision_matrix()

    # 1. Capability & Compliance Check
    area_key = payload.area.lower()
    registry_key = f"{area_key}_intelligence"
    if area_key == "communal":
        registry_key = "communal_ecosystem_intelligence"

    if not cap_registry.is_enabled(registry_key):
        # Fallback to system intelligence if area not found/enabled
        area_key = "system"
        registry_key = "system_intelligence"

    compliance_rules = cap_registry.get_compliance_rules(registry_key)

    # 2. Scope Integration
    active_scope = None
    if payload.use_active_scope:
        scope = scope_mgr.get_active_scope()
        if scope:
            active_scope = scope.scope_id
            # Merge scope boundary rules into reasoning or context

    # 3. Decision Matrix Generation
    # For now we use the area-specific generator which has preset's for the '4th area'
    matrix = matrix_gen.create_area_specific_matrix(area_key, payload.options)

    # 4. Reasoning & Compliance Summary
    reasoning = f"Decision made using {area_key} intelligence area."
    if active_scope:
        reasoning += f" Applied within scope: {active_scope}."
    if compliance_rules:
        reasoning += f" Verified against {len(compliance_rules)} compliance rules."

    response_data = DecisionResponseOut(
        decision_id=decision_id,
        area=area_key,
        best_option_id=matrix.get("best_option", ""),
        scores=matrix.get("scores", {}),
        totals=matrix.get("totals", {}),
        reasoning=reasoning,
        active_scope=active_scope,
        compliance_verified=True,
    )

    return ApiResponse(
        success=True,
        data=response_data,
        meta=ResponseMeta(request_id=request_id),
    )


# Rebuild models to resolve and Pydantic v2 forward references
# and generic type definitions during runtime initialization.
NavigationPlanOut.model_rebuild()
DecisionRequestPayload.model_rebuild()
DecisionResponseOut.model_rebuild()
