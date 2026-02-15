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

from safety.api.auth import TrustTier, UserIdentity, get_user_from_token
from safety.api.rate_limiter import allow_request
from safety.api.security_headers import SecurityHeadersMiddleware
from safety.escalation.handler import is_user_suspended
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


class SafetyMiddleware(BaseHTTPMiddleware):
    """
    Mandatory safety enforcement middleware with security headers.

    Inserted before all business logic. Cannot be bypassed.
    """

    def __init__(self, app):
        super().__init__(app)
        # Initialize security headers middleware
        self.security_headers = SecurityHeadersMiddleware(
            None,  # app not needed for header addition
            enable_csrf_protection=True,
            allowed_origins={"http://localhost:3000", "https://localhost:3000"},  # Configure as needed
        )

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip for health/docs endpoints
        if request.url.path in _BYPASS_PATHS:
            response = await call_next(request)
            # Still add security headers even for bypass paths
            self.security_headers._add_security_headers(response, request)
            return response

        # Only enforce on POST requests to /infer and /v1/ endpoints
        # GET requests (like listing) pass through
        if request.method != "POST":
            response = await call_next(request)
            self.security_headers._add_security_headers(response, request)
            return response

        # Generate trace context
        trace_id = str(uuid.uuid4())
        request_id = str(uuid.uuid4())

        # 0. Fail-closed check: verify safety infrastructure is available
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

            return _make_refusal_response("SAFETY_UNAVAILABLE", trace_id, 503)

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

        # 2. Check user suspension
        suspended, reason = await is_user_suspended(user.id)
        if suspended:
            logger.warning("suspended_user_request", user_id=user.id, reason=reason)
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
                    details={"reason": reason, "action": "blocked_suspended_user"},
                )
            )

            response = _make_refusal_response("USER_SUSPENDED", trace_id)
            self.security_headers._add_security_headers(response, request)
            return response

        # 3. Rate limiting
        rate_result = await allow_request(
            user_id=user.id,
            trust_tier=user.trust_tier,
            feature="infer",
        )
        if not rate_result[0]:  # type: ignore[reportUnknownMemberType]
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
                    details={"reset_seconds": rate_result[2]},  # type: ignore[reportUnknownMemberType]
                )
            )

            await write_audit_event(
                event="rate_limited",
                request_id=request_id,
                user_id=user.id,
                reason="RATE_LIMITED",
                payload={"reset_seconds": rate_result[2]},  # type: ignore[reportUnknownMemberType]  # pyright: ignore[reportUnknownMemberType]
            )
            response = _make_rate_limit_response(rate_result[2], trace_id)  # type: ignore[reportUnknownMemberType]
            self.security_headers._add_security_headers(response, request)
            return response

        # 4. Pre-check detector (synchronous, <50ms)
        try:
            # 4a. Enforce Content-Length limit BEFORE reading the body to prevent
            # memory exhaustion (OOM) from oversized payloads.
            _MAX_BODY_SIZE = 50_000  # bytes — matches _MAX_INPUT_LENGTH in pre_check
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
                        return response
                except ValueError:
                    pass  # Malformed Content-Length — let body read handle it

            # 4b. Read body with bounded streaming to handle missing/lying Content-Length
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
                    return response
            try:
                body = json.loads(body_bytes)
            except (json.JSONDecodeError, UnicodeDecodeError):
                body = {}

            # Extract user_input for downstream endpoints
            user_input = body.get("user_input", "") or body.get("prompt", "") or body.get("input", "")

            # [PROJECT GUARDIAN] Use SafetyRuleManager
            blocked = False
            reason_code = None

            manager = get_rule_manager()
            is_safe, reasons = manager.evaluate_request(user_id=user.id, trust_tier=user.trust_tier.value, data=body)
            if not is_safe:
                blocked = True
                reason_code = reasons[0] if reasons else "AI_SAFETY_VIOLATION"

            DETECTOR_HEALTHY.set(1)
        except Exception as exc:
            # Fail closed: if detector errors, refuse
            logger.error("precheck_error", error=str(exc))
            DETECTOR_HEALTHY.set(0)
            REQUESTS_TOTAL.labels(outcome="refused").inc()
            response = _make_refusal_response("SAFETY_UNAVAILABLE", trace_id, 503)
            self.security_headers._add_security_headers(response, request)
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
            return response

        # 5. Pre-check passed — continue to the endpoint handler
        #    (which MUST enqueue to Redis Streams, not call model directly)
        REQUESTS_TOTAL.labels(outcome="queued").inc()
        request.state.body = body
        request.state.user_input = user_input

        return await call_next(request)
