"""
Safety enforcement middleware for FastAPI.

Pipeline (in order, non-bypassable):
1. Authenticate and resolve trust tier.
2. Check user suspension.
3. Rate limit.
4. Synchronous pre-check detector (<50ms).
5. If flagged: deterministic refusal.
6. If passed: enqueue to Redis Streams.

Fail-closed: if any safety component is unavailable, deny the request.
"""

from __future__ import annotations

import json
import os
import time
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from safety.ai_workflow_safety import (
    TemporalSafetyConfig,
    get_ai_workflow_safety_engine,
)
from safety.api.auth import TrustTier, UserIdentity, get_user_from_token
from safety.api.rate_limiter import allow_request
from safety.api.security_headers import SecurityHeadersMiddleware
from safety.config import SecureConfig
from safety.content_safety_checker import ContentSafetyChecker
from safety.escalation.handler import is_user_suspended
from safety.monitoring import SafetyEvent, get_safety_monitor
from safety.observability.logging_setup import get_logger, set_trace_context
from safety.observability.metrics import (
    DETECTOR_HEALTHY,
    REQUESTS_TOTAL,
)
from safety.observability.security_monitoring import (
    SecurityEvent,
    SecurityEventSeverity,
    SecurityEventType,
    security_logger,
)

# [PROJECT GUARDIAN] Integration
from safety.rules.manager import get_rule_manager
from safety.workers.worker_utils import check_redis_health, write_audit_event

logger = get_logger("api.middleware")

# Maximum request body size (bytes) â€” matches _MAX_INPUT_LENGTH in pre_check
_MAX_BODY_SIZE = 50_000

# Paths that bypass safety middleware (health, metrics only).
# API docs are only bypassed in development mode to prevent
# exposing internal API schema to unauthenticated users in production.
_is_dev_env = os.getenv("GRID_ENV", "production").lower() in ("development", "dev", "test")

_BYPASS_PATHS: set[str] = {
    "/health",
    "/healthz",
    "/ready",
    "/metrics",
}

if _is_dev_env:
    _BYPASS_PATHS |= {"/docs", "/openapi.json", "/redoc"}


def _make_refusal_response(
    reason_code: str,
    trace_id: str,
    status_code: int = 403,
) -> JSONResponse:
    """Create a deterministic refusal response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "refused": True,
            "reason_code": reason_code,
            "explanation": "request denied",
            "support_ticket_id": f"audit-{trace_id}",
        },
    )


def _make_rate_limit_response(reset_seconds: float, trace_id: str) -> JSONResponse:
    """Create a rate-limit refusal response."""
    return JSONResponse(
        status_code=429,
        content={
            "rate_limited": True,
            "window_seconds": int(reset_seconds),
            "support_ticket_id": f"audit-{trace_id}",
        },
    )


def _add_safety_pact_headers(response: Response):
    """Add mandatory Safety Pact headers to the response"""
    response.headers["X-Safety-Pact-Awaiting"] = "AWAITED"
    response.headers["X-Safety-Pact-Concurrency"] = "STAMINA_YIELDED"
    response.headers["X-Safety-Pact-Sovereignty"] = "DETERMINISTIC"


class SafetyMiddleware(BaseHTTPMiddleware):
    """
    Mandatory safety enforcement middleware with security headers.

    Inserted before all business logic. Cannot be bypassed.
    """

    def __init__(self, app):
        super().__init__(app)
        # Initialize security components
        self.secure_config = SecureConfig()
        self.content_checker = ContentSafetyChecker()
        self.safety_monitor = get_safety_monitor()

        # Initialize security headers middleware
        _csrf_enabled = os.getenv("SAFETY_CSRF_ENABLED", "false").lower() in ("1", "true", "yes")
        self.security_headers = SecurityHeadersMiddleware(
            None,  # app not needed for header addition
            enable_csrf_protection=_csrf_enabled,
            allowed_origins={"http://localhost:3000", "https://localhost:3000"},  # Configure as needed
        )

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip for health/docs endpoints
        if request.url.path in _BYPASS_PATHS:
            response = await call_next(request)
            # Still add security headers even for bypass paths
            self.security_headers._add_security_headers(response, request)
            _add_safety_pact_headers(response)
            return response

        # Only enforce on POST requests to /infer and /v1/ endpoints
        # GET requests (like listing) pass through
        if request.method != "POST":
            response = await call_next(request)
            self.security_headers._add_security_headers(response, request)
            _add_safety_pact_headers(response)
            return response

        # Generate trace context
        trace_id = str(uuid.uuid4())
        request_id = str(uuid.uuid4())

        # 0. Fail-closed check: verify safety infrastructure is available
        _bypass_redis = os.getenv("SAFETY_BYPASS_REDIS", "").lower() in ("1", "true", "yes")
        
        if _bypass_redis:
            redis_ok = True
        else:
            redis_ok = await check_redis_health()

        if not redis_ok:
            logger.error("safety_infra_unavailable", component="redis")
            REQUESTS_TOTAL.labels(outcome="refused").inc()

            # Log critical infrastructure failure for observation
            security_logger.log_event(
                SecurityEvent(
                    event_id=str(uuid.uuid4()),
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    event_type=SecurityEventType.ANOMALOUS_ACTIVITY,
                    severity=SecurityEventSeverity.CRITICAL,
                    source="api.middleware",
                    user_id="system",
                    ip_address=request.client.host if request.client else None,
                    session_id=trace_id,
                    details={"error": "Redis unavailable", "trace_id": trace_id},
                )
            )

            response = _make_refusal_response("SAFETY_UNAVAILABLE", trace_id, 503)
            self.security_headers._add_security_headers(response, request)
            _add_safety_pact_headers(response)
            return response

        # 1. Authenticate and resolve trust tier
        try:
            user = get_user_from_token(request)
        except Exception as exc:
            logger.error("auth_failed", error=str(exc))
            user = UserIdentity(id="anon:auth-error", trust_tier=TrustTier.ANON)

        set_trace_context(trace_id=trace_id, request_id=request_id, user_id=user.id)

        # Store user and trace info in request state for downstream use
        request.state.user = user
        request.state.trace_id = trace_id
        request.state.request_id = request_id

        # 2. Check user suspension (skip if Redis bypass is enabled)
        if not _bypass_redis:
            suspension = await is_user_suspended(user.id)
        else:
            suspension = None
        if suspension and suspension.suspended:
            logger.warning("suspended_user_request", user_id=user.id, reason=suspension.reason)
            REQUESTS_TOTAL.labels(outcome="refused").inc()

            # Log suspension enforcement
            security_logger.log_event(
                SecurityEvent(
                    event_id=str(uuid.uuid4()),
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    event_type=SecurityEventType.AUTH_BLOCKED,
                    severity=SecurityEventSeverity.HIGH,
                    source="api.middleware",
                    user_id=user.id,
                    ip_address=request.client.host if request.client else None,
                    session_id=trace_id,
                    details={"reason": suspension.reason, "action": "blocked_suspended_user"},
                )
            )

            response = _make_refusal_response("USER_SUSPENDED", trace_id)
            self.security_headers._add_security_headers(response, request)
            _add_safety_pact_headers(response)
            return response

        # 3. Rate limiting
        rate_result = await allow_request(
            user_id=user.id,
            trust_tier=user.trust_tier,
            feature="infer",
        )
        if not rate_result.allowed:
            REQUESTS_TOTAL.labels(outcome="rate_limited").inc()

            # Log rate limit event
            security_logger.log_event(
                SecurityEvent(
                    event_id=str(uuid.uuid4()),
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
                    severity=SecurityEventSeverity.MEDIUM,
                    source="api.middleware",
                    user_id=user.id,
                    ip_address=request.client.host if request.client else None,
                    session_id=trace_id,
                    details={"reset_seconds": rate_result.reset_seconds},
                )
            )

            await write_audit_event(
                event="rate_limited",
                request_id=request_id,
                user_id=user.id,
                reason="RATE_LIMITED",
                payload={"reset_seconds": rate_result.reset_seconds},
            )
            response = _make_rate_limit_response(rate_result.reset_seconds, trace_id)
            self.security_headers._add_security_headers(response, request)
            _add_safety_pact_headers(response)
            return response

        # 3.5 Privacy Shield (Cognitive Privacy)
        # Enforce privacy rules on the request body for /infer endpoints
        if request.url.path.endswith("/infer"):
            from safety.privacy.core.engine import get_privacy_engine
            from safety.privacy.core.presets import PrivacyPreset

            # Use BALANCED preset by default, or could be driven by TrustTier
            privacy_engine = get_privacy_engine(preset=PrivacyPreset.BALANCED)

            # Read body with bounded streaming
            body_bytes = b""
            async for chunk in request.stream():
                body_bytes += chunk
                if len(body_bytes) > _MAX_BODY_SIZE:
                    REQUESTS_TOTAL.labels(outcome="refused").inc()
                    logger.warning("request_body_exceeded", user_id=user.id)
                    response = _make_refusal_response("INPUT_TOO_LONG", trace_id)
                    self.security_headers._add_security_headers(response, request)
                    _add_safety_pact_headers(response)
                    return response

            try:
                body = json.loads(body_bytes)
            except (json.JSONDecodeError, UnicodeDecodeError):
                body = {}

            user_input = body.get("user_input", "") or body.get("prompt", "") or body.get("input", "")

            if user_input:
                privacy_result = await privacy_engine.process(user_input)

                # Store results for audit
                request.state.privacy_results = privacy_result

                # Fail-closed: if privacy processing itself failed, deny
                if not privacy_result.success:
                    REQUESTS_TOTAL.labels(outcome="refused").inc()
                    logger.error("privacy_engine_failure", user_id=user.id, error=privacy_result.error)
                    response = _make_refusal_response("PRIVACY_UNAVAILABLE", trace_id, 503)
                    self.security_headers._add_security_headers(response, request)
                    _add_safety_pact_headers(response)
                    return response

                if privacy_result.blocked:
                    REQUESTS_TOTAL.labels(outcome="refused").inc()
                    logger.warning("privacy_blocked", user_id=user.id, detections=len(privacy_result.detections))
                    response = _make_refusal_response("PRIVACY_VIOLATION", trace_id, 400)
                    self.security_headers._add_security_headers(response, request)
                    _add_safety_pact_headers(response)
                    return response

                if privacy_result.masked:
                    # Update body with masked text
                    body["user_input"] = privacy_result.processed_text
                    # Re-serialize for downstream
                    # Note: We need to override receive() to return this new body
                    # to the application, or just update request.state.body
                    # Since existing code relies on request.state.body in step 5,
                    # we just update that variable below.
                    user_input = privacy_result.processed_text

            # Make body available to downstream validation
            # IMPORTANT: Starlette Request.stream() is consumed.
            # We must reconstruct it if call_next needs it, but our middleware pattern
            # passes data via request.state for /infer.
            # However, for 4b logic to work without re-reading stream, we need to adjust 4b.
            # The existing 4b logic reads stream again which will hang/fail.
            # We will refactor 4b to use the body we read here.
            request.state.body_bytes = body_bytes
            request.state.body = body
            request.state.user_input = user_input

            user_age = getattr(user, "age", None)

            # 4.5 Content Safety Check (Input)
            # Content safety must run BEFORE AI workflow safety to feed into "Heat" (Rule 2)
            content_assessment = self.content_checker.check_content(user_input, user_age)
            if not content_assessment["is_safe"]:
                logger.warning("content_safety_violation", user_id=user.id, issues=content_assessment["issues"])
                self.safety_monitor.record_event(
                    SafetyEvent(
                        event_type="content_violation",
                        severity="high",
                        user_id=user.id,
                        session_id=trace_id,
                        metadata={"issues": content_assessment["issues"], "input_length": len(user_input)},
                    )
                )
                response = _make_refusal_response("CONTENT_SAFETY_VIOLATION", trace_id, 400)
                self.security_headers._add_security_headers(response, request)
                _add_safety_pact_headers(response)
                return response

            # 4.6 AI Workflow Safety Evaluation (Governed by Safety Pact)
            # Evaluate interaction patterns for cognitive safety, hook detection, and Fair Play rules
            try:
                # Get or create AI workflow safety engine for this user
                safety_engine = await get_ai_workflow_safety_engine(
                    user_id=user.id,
                    config=TemporalSafetyConfig(
                        enable_hook_detection=True,
                        enable_wellbeing_tracking=True,
                        developmental_safety_mode=user_age is not None and user_age < 18,
                    ),
                    user_age=user_age,
                )

                # Rules 1-3 are evaluated here
                safety_assessment = await safety_engine.evaluate_request(
                    user_input=user_input,
                    current_time=time.time(),
                    sensitive_detections=len(content_assessment["issues"]),
                )

                # Record status in request state
                request.state.ai_workflow_safety = safety_assessment

                if not safety_assessment["safety_allowed"]:
                    reason = safety_assessment.get("blocked_reason") or (
                        "STAMINA_EXHAUSTED" if not safety_assessment.get("stamina_allowed") else "SAFETY_VIOLATION"
                    )
                    logger.warning("AI workflow safety violation", user_id=user.id, reason=reason)

                    self.safety_monitor.record_event(
                        SafetyEvent(
                            event_type="safety_violation",
                            severity="high",
                            user_id=user.id,
                            session_id=trace_id,
                            metadata={"reason": reason, "assessment": safety_assessment},
                        )
                    )

                    response = _make_refusal_response(
                        reason, trace_id, 429 if "STAMINA" in reason or "COOLDOWN" in reason else 403
                    )
                    self.security_headers._add_security_headers(response, request)
                    _add_safety_pact_headers(response)
                    return response

                # Add safety context to request metadata for worker processing
                if "metadata" not in body:
                    body["metadata"] = {}

                body["metadata"]["safety_pact"] = {
                    "stamina_remaining": safety_assessment.get("remaining_stamina"),
                    "current_heat": safety_assessment.get("current_heat"),
                    "flow_bonus": safety_assessment.get("flow_bonus", 1.0),
                }

            except Exception as exc:
                logger.error("ai_workflow_safety_error", error=str(exc), user_id=user.id)
                # Continue processing - safety is still enforced by other layers

        try:
            # 4a. Enforce Content-Length limit
            content_length = request.headers.get("content-length")
            if content_length is not None:
                try:
                    if int(content_length) > _MAX_BODY_SIZE:
                        REQUESTS_TOTAL.labels(outcome="refused").inc()
                        logger.warning(
                            "request_body_too_large",
                            content_length=content_length,
                            user_id=user.id,
                            trace_id=trace_id,
                        )
                        response = _make_refusal_response("INPUT_TOO_LONG", trace_id)
                        self.security_headers._add_security_headers(response, request)
                        _add_safety_pact_headers(response)
                        return response
                except ValueError:
                    pass  # Malformed Content-Length â€” let body read handle it

            # 4b. Read body with bounded streaming to handle missing/lying Content-Length

            # If body was already read by Privacy Step (3.5), reuse it
            if hasattr(request.state, "body_bytes"):
                body_bytes = request.state.body_bytes
                body = request.state.body
            else:
                body_bytes = b""
                async for chunk in request.stream():
                    body_bytes += chunk
                    if len(body_bytes) > _MAX_BODY_SIZE:
                        REQUESTS_TOTAL.labels(outcome="refused").inc()
                        logger.warning(
                            "request_body_exceeded_stream_limit",
                            bytes_read=len(body_bytes),
                            user_id=user.id,
                            trace_id=trace_id,
                        )
                        response = _make_refusal_response("INPUT_TOO_LONG", trace_id)
                        self.security_headers._add_security_headers(response, request)
                        _add_safety_pact_headers(response)
                        return response
                try:
                    body = json.loads(body_bytes)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    body = {}

            # [STREAMS] Restore body for downstream consumers
            # Setting _body allows Starlette/FastAPI to re-read the body from memory
            # bypassing the consumed stream.
            request._body = body_bytes

            # Extract user_input for downstream endpoints
            user_input = body.get("user_input", "") or body.get("prompt", "") or body.get("input", "")

            # [PROJECT GUARDIAN] Use SafetyRuleManager
            blocked = False
            reason_code = None

            manager = get_rule_manager()
            eval_result = manager.evaluate_request(user_id=user.id, trust_tier=user.trust_tier.value, data=body)
            if not eval_result.is_safe:
                blocked = True
                reason_code = eval_result.violations[0] if eval_result.violations else "AI_SAFETY_VIOLATION"

            DETECTOR_HEALTHY.set(1)
        except Exception as exc:
            # Fail closed: if detector errors, refuse
            logger.error("precheck_error", error=str(exc))
            DETECTOR_HEALTHY.set(0)
            REQUESTS_TOTAL.labels(outcome="refused").inc()
            response = _make_refusal_response("SAFETY_UNAVAILABLE", trace_id, 503)
            self.security_headers._add_security_headers(response, request)
            _add_safety_pact_headers(response)
            return response

        if blocked:
            REQUESTS_TOTAL.labels(outcome="refused").inc()

            # Log content blocking
            security_logger.log_event(
                SecurityEvent(
                    event_id=str(uuid.uuid4()),
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    event_type=SecurityEventType.AI_INPUT_BLOCKED,
                    severity=SecurityEventSeverity.HIGH,
                    source="api.middleware.pre_check",
                    user_id=user.id,
                    ip_address=request.client.host if request.client else None,
                    session_id=trace_id,
                    details={"reason_code": reason_code, "input_length": len(user_input)},
                )
            )

            await write_audit_event(
                event="refusal",
                request_id=request_id,
                user_id=user.id,
                reason=reason_code or "UNKNOWN",
                payload={"trust_tier": user.trust_tier.value},
            )
            logger.info(
                "request_refused",
                request_id=request_id,
                user_id=user.id,
                reason_code=reason_code,
            )
            response = _make_refusal_response(reason_code or "BLOCKED", trace_id)
            self.security_headers._add_security_headers(response, request)
            _add_safety_pact_headers(response)
            return response

        # 5. Pre-check passed â€” continue to the endpoint handler
        #    (which MUST enqueue to Redis Streams, not call model directly)
        REQUESTS_TOTAL.labels(outcome="queued").inc()
        request.state.body = body
        request.state.user_input = user_input

        # request._body is set, so downstream can read it
        response = await call_next(request)
        _add_safety_pact_headers(response)
        return response
