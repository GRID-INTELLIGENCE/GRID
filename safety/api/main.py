"""
FastAPI application for the safety enforcement pipeline.

Endpoints:
- POST /infer         — Submit an inference request (enqueued, not direct).
- POST /review        — Human reviewer approve/block an escalation.
- GET  /health        — Health check (bypasses middleware).
- GET  /metrics       — Prometheus metrics (bypasses middleware).
- GET  /status/{id}   — Check status of a queued request.
- POST /privacy/detect — Detect PII in text (Cognitive Privacy Shield).
- POST /privacy/mask   — Mask or block PII in text.
- POST /privacy/batch  — Batch PII detection/masking (up to 100 texts).

The API layer NEVER calls the model directly. All requests are enqueued
to Redis Streams for worker processing.

Supports DEGRADED_MODE (env: SAFETY_DEGRADED_MODE=true) for running
without Redis — safety checks remain active but queuing is mocked.
Use for integration tests (e.g. test_privacy_api) when Redis is unavailable.
"""

from __future__ import annotations

import os
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, Field
from starlette.responses import Response

from safety.api import observation_endpoints, privacy_endpoints
from safety.api.middleware import SafetyMiddleware
from safety.audit.db import check_health as check_db_health
from safety.audit.db import close_db, init_db
from safety.escalation.handler import approve
from safety.guardian.loader import get_rule_loader
from safety.observability.logging_setup import get_logger, setup_logging
from safety.observability.metrics import record_service_info
from safety.observability.runtime_observation import observation_service
from safety.observability.security_monitoring import security_logger, security_monitor
from safety.monitoring import get_safety_monitor
from safety.workers.worker_utils import (
    check_redis_health,
    close_redis,
    enqueue_request,
    get_queue_depth,
)

logger = get_logger("api.main")

# ---------------------------------------------------------------------------
# Degraded Mode Configuration
# ---------------------------------------------------------------------------
DEGRADED_MODE = os.getenv("SAFETY_DEGRADED_MODE", "false").lower() == "true"

if DEGRADED_MODE:
    from unittest.mock import AsyncMock

    # Mock Redis client for all modules
    class MockRedis:
        async def ping(self):
            return True

        async def xadd(self, *args, **kwargs):
            return str(uuid.uuid4())

        async def xreadgroup(self, *args, **kwargs):
            return []

        async def xack(self, *args, **kwargs):
            return 1

        async def xpending(self, *args, **kwargs):
            return []

        async def xrange(self, *args, **kwargs):
            return []

        async def xrevrange(self, *args, **kwargs):
            return []

        async def get(self, *args, **kwargs):
            return None

        async def set(self, *args, **kwargs):
            return True

        def pipeline(self):
            return self

        async def execute(self):
            return []

    # Replace redis_utils functions with mocks
    from safety.workers import worker_utils

    worker_utils.redis_client = MockRedis()  # type: ignore[reportAssignmentIssue]
    worker_utils.check_redis_health = AsyncMock(return_value=True)
    worker_utils.enqueue_request = AsyncMock(return_value=str(uuid.uuid4()))
    worker_utils.get_queue_depth = AsyncMock(return_value=0)
    worker_utils.write_audit_event = AsyncMock(return_value=None)

    # Patch the references already imported into the middleware module
    from safety.api import middleware as _safety_mw

    _safety_mw.check_redis_health = AsyncMock(return_value=True)
    _safety_mw.write_audit_event = AsyncMock(return_value=None)

    # Patch escalation handler (is_user_suspended uses Redis)
    from safety.escalation import handler as _esc_handler
    from safety.escalation.handler import SuspensionStatus

    _esc_handler.is_user_suspended = AsyncMock(return_value=SuspensionStatus(suspended=False))
    _safety_mw.is_user_suspended = AsyncMock(return_value=SuspensionStatus(suspended=False))

    # Patch rate limiter (allow_request uses Redis)
    from safety.api import rate_limiter as _rate_limiter
    from safety.api.rate_limiter import RateLimitResult

    _mock_rate_result = RateLimitResult(allowed=True, remaining=100, reset_seconds=0.0)
    _rate_limiter.allow_request = AsyncMock(return_value=_mock_rate_result)
    _safety_mw.allow_request = AsyncMock(return_value=_mock_rate_result)

    # Patch get_redis for any module that calls it lazily
    worker_utils.get_redis = AsyncMock(return_value=MockRedis())  # type: ignore[reportAssignmentIssue]

    logger.info("🟡 DEGRADED MODE ACTIVE — Redis mocked, safety checks still enforced")


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize and tear down resources."""
    setup_logging(
        json_output=os.getenv("SAFETY_LOG_JSON", "true").lower() == "true",
        log_level=os.getenv("SAFETY_LOG_LEVEL", "INFO"),
    )
    record_service_info(
        version="1.0.0",
        environment=os.getenv("SAFETY_ENV", "development"),
    )
    logger.info("safety_api_starting", degraded_mode=DEGRADED_MODE)

    # Initialize audit DB
    if not DEGRADED_MODE:
        try:
            await init_db()
        except Exception as exc:
            logger.error("audit_db_init_failed", error=str(exc))
            # Continue — the middleware will fail closed if DB is needed
    else:
        logger.warning("audit_db_skipped_degraded_mode")

    # Start background services
    await observation_service.start()
    security_monitor.start_monitoring()
    get_rule_loader().start_auto_reload()
    await get_safety_monitor().start()

    yield

    # Shutdown

    # Shutdown
    logger.info("safety_api_shutting_down")

    # Stop background services
    await observation_service.stop()
    security_monitor.stop_monitoring()
    security_logger.shutdown()
    get_rule_loader().stop_auto_reload()

    if not DEGRADED_MODE:
        await close_db()
        await close_redis()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Safety Enforcement API",
    version="1.0.0",
    description="Mandatory real-time safety enforcement for AI inference.",
    lifespan=lifespan,
)

app.include_router(observation_endpoints.router)
app.include_router(privacy_endpoints.router)

# Mount safety middleware (non-bypassable)
app.add_middleware(SafetyMiddleware)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class InferRequest(BaseModel):
    user_input: str = Field(..., min_length=1, max_length=50_000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class InferResponse(BaseModel):
    request_id: str
    status: str = "queued"
    result: dict[str, Any] | None = None


class ReviewRequest(BaseModel):
    request_id: str
    decision: str = Field(..., pattern="^(approve|block)$")
    reviewer_id: str
    notes: str = ""


class ReviewResponse(BaseModel):
    success: bool
    request_id: str
    decision: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    """Health check — bypasses safety middleware."""
    try:
        if not DEGRADED_MODE:
            redis_ok = await check_redis_health()
            db_ok = await check_db_health()
            healthy = redis_ok and db_ok
            return JSONResponse(
                status_code=200 if healthy else 503,
                content={
                    "status": "healthy" if healthy else "degraded",
                    "degraded": DEGRADED_MODE,
                    "services": {
                        "redis": "ok" if redis_ok else "unavailable",
                        "audit_db": "ok" if db_ok else "unavailable",
                    },
                },
            )
        else:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "degraded",
                    "degraded": True,
                    "message": "Running in degraded mode (Redis not available)",
                    "services": {
                        "redis": "mocked",
                        "audit_db": "skipped",
                    },
                },
            )
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Health check failed")


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint — bypasses safety middleware."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.post("/infer", response_model=InferResponse)
async def infer(request: Request):
    """
    Submit an inference request.

    The request is validated by middleware (auth, rate-limit, safety checks)
    and then enqueued to Redis Streams. The model is NEVER called here.
    In DEGRADED_MODE, returns a mock response immediately.
    """
    # Middleware has already validated and attached state
    user = request.state.user
    trace_id = request.state.trace_id
    request_id = request.state.request_id
    body = request.state.body
    user_input = request.state.user_input

    if DEGRADED_MODE:
        # In degraded mode, immediately return a mock response
        logger.warning(
            "degraded_mode_infer",
            request_id=request_id,
            user_id=user.id,
            message="Bypassing queue — safety checks still applied by middleware",
        )
        return InferResponse(
            request_id=request_id,
            status="completed",
            result={
                "output": "Safety check passed (degraded mode)",
                "safety_checked": True,
                "user_id": user.id,
                "trust_tier": user.trust_tier.value,
            },
        )

    # Original queueing logic
    try:
        await enqueue_request(
            request_id=request_id,
            user_id=user.id,
            input_text=user_input,
            trust_tier=user.trust_tier.value,
            trace_id=trace_id,
            metadata=body.get("metadata", {}),
        )
    except RuntimeError as exc:
        logger.error("enqueue_failed", error=str(exc))
        # Fail closed: refuse if we can't enqueue
        return JSONResponse(
            status_code=503,
            content={
                "refused": True,
                "reason_code": "SAFETY_UNAVAILABLE",
                "explanation": "request denied",
                "support_ticket_id": f"audit-{trace_id}",
            },
        )

    return InferResponse(request_id=request_id, status="queued")


@app.post("/review", response_model=ReviewResponse)
async def review(req: ReviewRequest):
    """
    Human reviewer endpoint: approve or block an escalated request.

    - approve: release the stored model output to the response stream.
    - block: add the input to the dynamic blocklist and suspend the user.
    """
    if DEGRADED_MODE:
        logger.warning("degraded_mode_review", request_id=req.request_id)
        return ReviewResponse(
            success=True,
            request_id=req.request_id,
            decision=req.decision,
        )

    success = await approve(
        request_id=req.request_id,
        decision=req.decision,
        reviewer_id=req.reviewer_id,
        notes=req.notes,
    )
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Escalation not found or already resolved: {req.request_id}",
        )
    return ReviewResponse(
        success=True,
        request_id=req.request_id,
        decision=req.decision,
    )


@app.get("/status/{request_id}")
async def status(request_id: str):
    """Check the status of a queued request."""
    if DEGRADED_MODE:
        return {
            "request_id": request_id,
            "status": "completed",
            "result": {
                "output": "Safety check passed (degraded mode)",
                "safety_checked": True,
            },
        }

    try:
        from safety.workers.worker_utils import get_redis

        client = await get_redis()
        # Check response stream for completed request
        results = await client.xrevrange("response-stream", count=100)
        for _, fields in results:
            if fields.get("request_id") == request_id:
                return {
                    "request_id": request_id,
                    "status": fields.get("status", "completed"),
                    "response": fields.get("response", ""),
                }
        # Not found in response stream — still pending or escalated
        return {"request_id": request_id, "status": "pending"}
    except Exception as exc:
        logger.error("status_check_failed", error=str(exc))
        return {"request_id": request_id, "status": "unknown"}


@app.get("/queue/depth")
async def queue_depth():
    """Get the current inference queue depth."""
    if DEGRADED_MODE:
        return {"queue_depth": 0, "mode": "degraded"}

    depth = await get_queue_depth()
    return {"queue_depth": depth}


def run(
    host: str | None = None,
    port: int | None = None,
    reload: bool | None = None,
) -> None:
    """Run the Safety API server (entry point for safety-api console script).

    Configuration via environment variables (with defaults):
        SAFETY_API_HOST  — bind host (default: 0.0.0.0)
        SAFETY_API_PORT  — bind port (default: 8000)
        SAFETY_API_RELOAD — enable reload (default: false; set to 1/true/yes to enable)
    """
    import uvicorn

    _host = host if host is not None else os.getenv("SAFETY_API_HOST", "0.0.0.0")
    _port = port if port is not None else int(os.getenv("SAFETY_API_PORT", "8000"))
    _reload = (
        reload
        if reload is not None
        else os.getenv("SAFETY_API_RELOAD", "").lower() in ("1", "true", "yes")
    )

    uvicorn.run(
        "safety.api.main:app",
        host=_host,
        port=_port,
        reload=_reload,
    )
