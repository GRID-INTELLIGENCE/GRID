"""
Activity Resonance API Router.

FastAPI router exposing Activity Resonance Tool functionality as REST API
with WebSocket support for real-time activity processing.
"""

from __future__ import annotations

import logging
import os
import time
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Path, Query, WebSocket, status

from ..repositories.resonance_repository import ResonanceRepository
from ..services.resonance_service import ResonanceService as CoreResonanceService
from .dependencies import Auth, RateLimited, ResonanceServiceDep
from .performance import router as performance_router

# Tracing integration
try:
    from grid.tracing.action_trace import TraceOrigin
    from grid.tracing.trace_manager import get_trace_manager

    TRACING_ENABLED = True
except ImportError:
    TRACING_ENABLED = False
    get_trace_manager = None  # type: ignore
    TraceOrigin = None  # type: ignore
from .schemas import (
    ActivityCompleteResponse,
    ActivityEventResponse,
    ActivityEventsResponse,
    ActivityProcessRequest,
    ContextMetricsResponse,
    ContextResponse,
    DefinitiveChoiceResponse,
    DefinitiveStepRequest,
    DefinitiveStepResponse,
    EnvelopeMetricsResponse,
    FAQItemResponse,
    PathOptionResponse,
    PathTriageResponse,
    ResonanceResponse,
    UseCaseResponse,
)
from .websocket import websocket_endpoint

logger = logging.getLogger(__name__)

# =============================================================================
# Feature Flags
# =============================================================================

# Feature flag for definitive endpoint (kill-switch)
RESONANCE_DEFINITIVE_ENABLED = os.environ.get("RESONANCE_DEFINITIVE_ENABLED", "true").lower() in (
    "true",
    "1",
    "yes",
    "on",
)

# API Version metadata
API_VERSION = "1.0.0"
RESONANCE_TAGS_METADATA = [
    {
        "name": "resonance",
        "description": "Activity Resonance API - left-to-right communication layer",
        "externalDocs": {
            "description": "Resonance API documentation",
            "url": "docs/RESONANCE_API.md",
        },
    },
]

router = APIRouter()
router.include_router(performance_router)


def _get_service() -> CoreResonanceService:
    """Get a shared ResonanceService instance (Mothership pattern)."""
    if not hasattr(_get_service, "_instance"):
        _get_service._instance = CoreResonanceService(
            repository=ResonanceRepository(),
            application_path=None,  # Can be configured via env if needed
            light_path=None,
        )
    return _get_service._instance


# =============================================================================
# Helper Functions
# =============================================================================


def _convert_context_snapshot(snapshot) -> ContextResponse:
    """Convert ContextSnapshot to ContextResponse."""
    return ContextResponse(
        content=snapshot.content,
        source=snapshot.source,
        metrics=ContextMetricsResponse(
            sparsity=snapshot.metrics.sparsity,
            attention_tension=snapshot.metrics.attention_tension,
            decision_pressure=snapshot.metrics.decision_pressure,
            clarity=snapshot.metrics.clarity,
            confidence=snapshot.metrics.confidence,
        ),
        timestamp=snapshot.timestamp,
        relevance_score=snapshot.relevance_score,
    )


def _convert_path_triage(triage) -> PathTriageResponse:
    """Convert PathTriage to PathTriageResponse."""
    options = [
        PathOptionResponse(
            id=opt.id,
            name=opt.name,
            description=opt.description,
            complexity=opt.complexity.value if hasattr(opt.complexity, "value") else str(opt.complexity),
            steps=opt.steps,
            input_scenario=opt.input_scenario,
            output_scenario=opt.output_scenario,
            estimated_time=opt.estimated_time,
            confidence=opt.confidence,
            recommendation_score=opt.recommendation_score,
        )
        for opt in triage.options
    ]

    recommended = None
    if triage.recommended:
        recommended = PathOptionResponse(
            id=triage.recommended.id,
            name=triage.recommended.name,
            description=triage.recommended.description,
            complexity=(
                triage.recommended.complexity.value
                if hasattr(triage.recommended.complexity, "value")
                else str(triage.recommended.complexity)
            ),
            steps=triage.recommended.steps,
            input_scenario=triage.recommended.input_scenario,
            output_scenario=triage.recommended.output_scenario,
            estimated_time=triage.recommended.estimated_time,
            confidence=triage.recommended.confidence,
            recommendation_score=triage.recommended.recommendation_score,
        )

    return PathTriageResponse(
        goal=triage.goal,
        options=options,
        recommended=recommended,
        glimpse_summary=triage.glimpse_summary,
        total_options=triage.total_options,
    )


def _convert_envelope_metrics(metrics) -> EnvelopeMetricsResponse:
    """Convert EnvelopeMetrics to EnvelopeMetricsResponse."""
    return EnvelopeMetricsResponse(
        phase=metrics.phase.value if hasattr(metrics.phase, "value") else str(metrics.phase),
        amplitude=metrics.amplitude,
        velocity=metrics.velocity,
        time_in_phase=metrics.time_in_phase,
        total_time=metrics.total_time,
        peak_amplitude=metrics.peak_amplitude,
    )


# =============================================================================
# REST Endpoints
# =============================================================================


@router.post(
    "/process",
    response_model=ResonanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Process Activity",
    description=(
        "Process an activity with left-to-right communication. "
        "Returns context snapshot, path triage, and envelope metrics."
    ),
    tags=["resonance"],
)
async def process_activity(
    request: ActivityProcessRequest,
    service: ResonanceServiceDep,
) -> ResonanceResponse:
    """
    Process an activity with left-to-right communication.

    Provides:
    - Fast context from application/ (left)
    - Path visualization from light_of_the_seven/ (right)
    - ADSR envelope feedback
    """
    try:
        # Use injected service from dependency
        activity_id, feedback = await service.process_activity(
            query=request.query,
            activity_type=request.activity_type.value,
            context=request.context,
        )

        # Convert feedback to response
        context_response = None
        if feedback.context:
            context_response = _convert_context_snapshot(feedback.context)

        paths_response = None
        if feedback.paths:
            paths_response = _convert_path_triage(feedback.paths)

        envelope_response = None
        if feedback.envelope:
            envelope_response = _convert_envelope_metrics(feedback.envelope)

        return ResonanceResponse(
            activity_id=activity_id,
            state=feedback.state.value if hasattr(feedback.state, "value") else str(feedback.state),
            urgency=feedback.urgency,
            message=feedback.message,
            context=context_response,
            paths=paths_response,
            envelope=envelope_response,
            timestamp=datetime.now(UTC),
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error processing activity: {e}", exc_info=True)

        # Standardize errors at the application boundary:
        # - If upstream throws a Mothership exception (or anything with similar shape),
        #   wrap it into an ApplicationError so API responses stay consistent.
        from application.exceptions import ApplicationError, wrap_mothership_exception

        if not isinstance(e, ApplicationError):
            try:
                from application.mothership.exceptions import MothershipError as _MothershipError  # type: ignore

                if isinstance(e, _MothershipError):
                    e = wrap_mothership_exception(e)
            except Exception:
                # Fallback: if it looks like a structured app error, wrap it anyway
                if hasattr(e, "status_code") or hasattr(e, "code") or hasattr(e, "details"):
                    e = wrap_mothership_exception(e)

        if isinstance(e, ApplicationError):
            raise HTTPException(
                status_code=e.status_code,
                detail={
                    "code": e.code,
                    "message": e.message,
                    "details": e.details,
                },
            ) from e

        # Generic error - use standardized format
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred while processing activity",
                "details": {"error": str(e)} if logger.isEnabledFor(logging.DEBUG) else {},
            },
        ) from e


@router.get(
    "/context",
    response_model=ContextResponse,
    summary="Get Fast Context",
    description="Get fast, concise context for a query (left side - application/).",
    tags=["resonance"],
)
async def get_context(
    service: ResonanceServiceDep,
    query: str = Query(..., min_length=1, max_length=1000, description="The query to get context for"),
    context_type: str = Query("general", description="Type of context (general, code, config)"),
    max_length: int = Query(200, ge=50, le=2000, description="Maximum context length"),
) -> ContextResponse:
    """
    Get fast context for a query.

    Provides vivid explanations when context is sparse and decision/attention
    metrics are tense.
    """
    try:
        # Use injected service from dependency
        snapshot = await service.get_context(
            query=query,
            context_type=context_type,
            max_length=max_length,
        )
        return _convert_context_snapshot(snapshot)
    except Exception as e:
        logger.error(f"Error getting context: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting context: {str(e)}",
        ) from e


@router.get(
    "/paths",
    response_model=PathTriageResponse,
    summary="Get Path Triage",
    description="Get path triage for a goal (right side - light_of_the_seven/).",
    tags=["resonance"],
)
async def get_paths(
    service: ResonanceServiceDep,
    goal: str = Query(..., min_length=1, max_length=1000, description="The goal or task"),
    max_options: int = Query(4, ge=1, le=10, description="Maximum number of path options"),
) -> PathTriageResponse:
    """
    Get path triage for a goal.

    Provides 3-4 path options with complexity, time, confidence, and
    input/output scenarios.
    """
    try:
        # Use injected service from dependency
        triage = await service.get_path_triage(
            goal=goal,
            context=None,
            max_options=max_options,
        )
        return _convert_path_triage(triage)
    except Exception as e:
        logger.error(f"Error getting paths: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting paths: {str(e)}",
        ) from e


@router.get(
    "/envelope/{activity_id}",
    response_model=EnvelopeMetricsResponse,
    summary="Get Envelope Metrics",
    description="Get current ADSR envelope metrics for an activity.",
    tags=["resonance"],
)
async def get_envelope(
    service: ResonanceServiceDep,
    activity_id: str = Path(..., description="Activity ID"),
) -> EnvelopeMetricsResponse:
    """
    Get current ADSR envelope metrics for an activity.

    Returns attack, decay, sustain, release phase information with
    amplitude and velocity metrics.
    """
    try:
        # Use injected service from dependency
        metrics = await service.get_envelope_metrics(activity_id)
        if metrics is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Activity {activity_id} not found",
            )
        return _convert_envelope_metrics(metrics)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting envelope: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting envelope: {str(e)}",
        ) from e


@router.post(
    "/complete/{activity_id}",
    response_model=ActivityCompleteResponse,
    summary="Complete Activity",
    description="Complete an activity (trigger release phase).",
    tags=["resonance"],
)
async def complete_activity(
    service: ResonanceServiceDep,
    activity_id: str = Path(..., description="Activity ID"),
) -> ActivityCompleteResponse:
    """
    Complete an activity.

    Triggers the release phase of the ADSR envelope and stops
    the feedback loop.
    """
    try:
        # Use injected service from dependency
        completed = await service.complete_activity(activity_id)
        if not completed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Activity {activity_id} not found",
            )
        return ActivityCompleteResponse(
            activity_id=activity_id,
            completed=True,
            message="Activity completed successfully",
            timestamp=datetime.now(UTC),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing activity: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error completing activity: {str(e)}",
        ) from e


@router.get(
    "/events/{activity_id}",
    response_model=ActivityEventsResponse,
    summary="Get Activity Events",
    description="Get activity events history.",
    tags=["resonance"],
)
async def get_events(
    service: ResonanceServiceDep,
    activity_id: str = Path(..., description="Activity ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of events to return"),
) -> ActivityEventsResponse:
    """
    Get activity events history.

    Returns list of events for the specified activity.
    """
    try:
        # Use injected service from dependency
        events = await service.get_activity_events(activity_id, limit=limit)
        event_responses = [
            ActivityEventResponse(
                event_id=event.event_id,
                timestamp=event.timestamp,
                activity_type=event.activity_type,
                payload=event.payload,
            )
            for event in events
        ]
        return ActivityEventsResponse(
            activity_id=activity_id,
            events=event_responses,
            total=len(event_responses),
        )
    except Exception as e:
        logger.error(f"Error getting events: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting events: {str(e)}",
        ) from e


@router.post(
    "/definitive",
    response_model=DefinitiveStepResponse,
    status_code=status.HTTP_200_OK,
    summary="Definitive (Canvas Flip) Step",
    description=(
        "A mid-process checkpoint (~65%) that flips a chaotic/free-form view into a coherent, "
        "audience-aligned explanation. Combines Resonance context + path triage with Skills "
        "(schema transform, compression, optional cross-reference) and optional local-first RAG."
    ),
    tags=["resonance"],
)
async def definitive_step(
    request: DefinitiveStepRequest,
    service: ResonanceServiceDep,
    _rate_limit: RateLimited,
    auth: Auth,
) -> DefinitiveStepResponse:
    # Feature flag check (kill-switch)
    if not RESONANCE_DEFINITIVE_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Definitive endpoint is currently disabled. Set RESONANCE_DEFINITIVE_ENABLED=true to enable.",
        )

    start_time = time.perf_counter()
    trace_context = None

    # Start tracing if available
    # NOTE: In environments where tracing imports fail, TraceOrigin is set to None.
    # Avoid referencing TraceOrigin.API_REQUEST in that case to prevent diagnostics/type issues.
    if TRACING_ENABLED and get_trace_manager is not None and TraceOrigin is not None:
        trace_manager = get_trace_manager()
        trace_context = trace_manager.create_trace(
            action_type="api.definitive_step",
            action_name="Definitive Step (Canvas Flip)",
            origin=TraceOrigin.API_REQUEST,
            user_id=auth.get("user_id") if isinstance(auth, dict) else None,
            metadata={
                "progress": request.progress,
                "target_schema": request.target_schema,
                "use_rag": request.use_rag,
                "use_llm": request.use_llm,
            },
            tags={"resonance", "definitive", "api"},
        )

    try:
        # 1) Generate resonance context + paths (the red-light decision surface)
        # Use injected service from dependency
        activity_id, feedback = await service.process_activity(
            query=request.query,
            activity_type=request.activity_type.value,
            context=request.context,
        )

        context_response = _convert_context_snapshot(feedback.context) if feedback.context else None
        paths_response = _convert_path_triage(feedback.paths) if feedback.paths else None

        # 2) Run skills (local-first; LLM is optional and gated by request.use_llm)
        skills: dict[str, Any] = {}

        refined_text = request.query
        try:
            from grid.skills.registry import default_registry

            refine_skill = default_registry.get("context.refine")
            if refine_skill is not None:
                refine_out = refine_skill.run({"text": request.query, "use_llm": bool(request.use_llm)})
                skills["context.refine"] = refine_out
                if bool(request.use_llm) and refine_out.get("status") == "success" and refine_out.get("output"):
                    refined_text = str(refine_out["output"])

            transform_skill = default_registry.get("transform.schema_map")
            transform_out: dict[str, Any]
            if transform_skill is not None:
                transform_out = transform_skill.run(
                    {
                        "text": refined_text,
                        "target_schema": request.target_schema,
                        "output_format": "json",
                        "use_llm": bool(request.use_llm),
                    }
                )
            else:
                transform_out = {
                    "skill": "transform.schema_map",
                    "status": "error",
                    "error": "Skill not available",
                }
            skills["transform.schema_map"] = transform_out

            # Cross-reference (optional narrative bridge; heuristic fallback is ok)
            xref_skill = default_registry.get("cross_reference.explain")
            if xref_skill is not None:
                skills["cross_reference.explain"] = xref_skill.run(
                    {
                        "concept": "definitive checkpoint (canvas flip at ~65%)",
                        "source_domain": "stage performance / theater",
                        "target_domain": "API orchestration / system execution",
                        "use_llm": bool(request.use_llm),
                    }
                )

            # Compress to a tight 'audience one-liner'
            compress_skill = default_registry.get("compress.articulate")
            summary_text = (
                "At the ~65% red-light checkpoint, Resonance aligns the view: it surfaces fast context, "
                "triages left/right/straight paths, and uses skills to transform and compress free-form work "
                "into a coherent, audience-readable explanation."
            )
            if compress_skill is not None:
                skills["compress.articulate"] = compress_skill.run(
                    {"text": summary_text, "max_chars": int(request.max_chars), "use_llm": bool(request.use_llm)}
                )
            else:
                skills["compress.articulate"] = {
                    "skill": "compress.articulate",
                    "status": "error",
                    "error": "Skill not available",
                }

            rag_payload = None
            if request.use_rag:
                rag_skill = default_registry.get("rag.query_knowledge")
                if rag_skill is not None:
                    rag_payload = rag_skill.run(
                        {
                            "query": (
                                "resonance api definitive endpoint skills schema transform compress cross_reference"
                            ),
                            "top_k": 5,
                            "temperature": 0.2,
                        }
                    )
                else:
                    rag_payload = {"skill": "rag.query_knowledge", "status": "error", "error": "Skill not available"}

        except Exception as e:
            # Keep the endpoint resilient even if optional skill modules are unavailable.
            skills["error"] = str(e)
            transform_out = {}
            rag_payload = None

        # 3) Build audience-facing explanation artifacts
        canvas_before = (
            "Canvas inverted: free-form work looks chaotic because the viewing frame is flipped. "
            "Signals exist, but meaning is misaligned."
        )
        canvas_after = (
            "Canvas flipped: context, options, and structured intent become visible. "
            "The system answers 'what is this?' and shows decision paths to reach the goal."
        )

        compress_out = skills.get("compress.articulate", {})
        summary = str(compress_out.get("output") or "").strip() or "Definitive checkpoint executed."

        structured = {}
        ts = skills.get("transform.schema_map", {})
        if isinstance(ts, dict) and ts.get("status") == "success":
            structured = ts.get("output") or {}

        faq = [
            FAQItemResponse(
                question="What is this?",
                answer=(
                    "A mid-process checkpoint that turns free-form activity into a coherent explanation by "
                    "combining resonance context + path triage with skills (schema transform + compression)."
                ),
            ),
            FAQItemResponse(
                question="What are the participants doing at the red light?",
                answer=(
                    "Evaluating left/right/straight options surfaced by path triage, validating the next step "
                    "before progressing (StepBloom-style IF-THEN checkpoint)."
                ),
            ),
            FAQItemResponse(
                question="Where do the skills connect?",
                answer=(
                    "Skills are invoked inside the definitive step to refine text, map it into a target schema, "
                    "cross-reference the metaphor, and compress the explanation for audience readability."
                ),
            ),
        ]

        use_cases = [
            UseCaseResponse(
                audience="Builders (developers)",
                scenario="Convert a vague goal into structured plan + clear next actions.",
                entrypoint="POST /api/v1/resonance/definitive",
                output="Structured schema + path choices + compressed summary",
            ),
            UseCaseResponse(
                audience="Communicators (PM/strategy)",
                scenario="Explain what is being built and why the process looks chaotic until the checkpoint.",
                entrypoint="POST /api/v1/resonance/definitive",
                output="FAQ + audience-aligned one-liner + mechanics",
            ),
            UseCaseResponse(
                audience="Researchers (sensemaking)",
                scenario="Ask the system where features connect and retrieve supporting sources (local-first RAG).",
                entrypoint="POST /api/v1/resonance/definitive with use_rag=true",
                output="RAG payload + structured transform",
            ),
        ]

        api_mechanics = [
            "POST /api/v1/resonance/process → context + path triage + envelope",
            "POST /api/v1/resonance/definitive → checkpoint (canvas flip) + skills orchestration",
            "GET /api/v1/resonance/context → fast context snapshot",
            "GET /api/v1/resonance/paths → left/right/straight style path options",
            "python -m grid skills list / python -m grid skills run <skill_id>",
            "python -m tools.rag.cli index . --rebuild --curate / python -m tools.rag.cli query '...'",
        ]

        # 4) Translate paths into metaphor choices (left/right/straight)
        choices = []
        if paths_response is not None and paths_response.options:
            opts = {opt.id: opt for opt in paths_response.options}

            def _pick(option_id: str, fallback_index: int) -> PathOptionResponse:
                if option_id in opts:
                    return opts[option_id]
                return paths_response.options[min(fallback_index, len(paths_response.options) - 1)]

            left = _pick("incremental", 0)
            right = _pick("pattern", 1)
            straight = _pick("comprehensive", 2)

            choices = [
                DefinitiveChoiceResponse(
                    direction="left",
                    option=left,
                    why="Loop to buy time: iterate, test, and reduce risk before committing to speed.",
                ),
                DefinitiveChoiceResponse(
                    direction="right",
                    option=right,
                    why="Enter the neighborhood: follow existing patterns and integrate cleanly with the codebase.",
                ),
                DefinitiveChoiceResponse(
                    direction="straight",
                    option=straight,
                    why="Merge onto the freeway: commit to a comprehensive path when momentum and completeness matter.",
                ),
            ]

        # Complete trace on success
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        if trace_context is not None:
            trace_context.complete(
                success=True,
                output_data={
                    "activity_id": activity_id,
                    "elapsed_ms": elapsed_ms,
                    "skills_invoked": list(skills.keys()),
                },
            )

        # Emit metrics stub (placeholder for Prometheus/OpenTelemetry)
        logger.info(
            "definitive_step_metrics",
            extra={
                "activity_id": activity_id,
                "elapsed_ms": elapsed_ms,
                "progress": request.progress,
                "use_rag": request.use_rag,
                "use_llm": request.use_llm,
                "skills_count": len(skills),
            },
        )

        return DefinitiveStepResponse(
            activity_id=activity_id,
            progress=float(request.progress),
            canvas_before=canvas_before,
            canvas_after=canvas_after,
            summary=summary,
            faq=faq,
            use_cases=use_cases,
            api_mechanics=api_mechanics,
            structured=structured,
            context=context_response,
            paths=paths_response,
            choices=choices,
            skills=skills,
            rag=rag_payload,
        )
    except Exception as e:
        # Complete trace on failure
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        if trace_context is not None:
            trace_context.complete(success=False, error=str(e))

        logger.error(
            f"Error running definitive step: {e}",
            exc_info=True,
            extra={"elapsed_ms": elapsed_ms},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running definitive step: {str(e)}",
        ) from e


# =============================================================================
# WebSocket Endpoint
# =============================================================================


@router.websocket("/ws/{activity_id}")
async def websocket_feedback(
    websocket: WebSocket,
    activity_id: str,
) -> None:
    """
    WebSocket endpoint for real-time activity feedback.

    Streams resonance feedback updates including:
    - ADSR envelope metrics
    - Context updates
    - Path triage updates
    - State changes
    """
    from typing import cast

    from .dependencies import get_resonance_service
    from .service import ResonanceService as ApiResonanceService

    # get_resonance_service() returns the application-layer ResonanceService implementation.
    # websocket_endpoint expects the API-layer ResonanceService type alias/protocol.
    # At runtime they are compatible; cast to satisfy static diagnostics/type checking.
    service = cast(ApiResonanceService, get_resonance_service())
    await websocket_endpoint(websocket, activity_id, service)


# =============================================================================
# Debug Endpoints
# =============================================================================


@router.get("/debug/config", tags=["debug"], summary="Get Debug Config")
async def get_debug_config() -> dict[str, Any]:
    """Get current debug configuration."""
    return {
        "timestamp": datetime.now(UTC),
        "logger_level": logging.getLogger().getEffectiveLevel(),
        "router": "Resonance API",
    }


__all__ = ["router"]
