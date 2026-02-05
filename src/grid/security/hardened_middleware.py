"""
GRID Hardened Security Middleware
=================================

Enhanced security middleware with integrated threat detection,
adaptive guardrails, and automated mitigation.

This module provides:
1. HardenedSecurityMiddleware - Production-grade request protection
2. ThreatResponseHandler - Automated threat response
3. SecurityContextManager - Request-scoped security context

Author: GRID Security Framework
Version: 2.0.0
Date: 2026-02-05
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from .threat_profile import (
    MitigationAction,
    ThreatCategory,
    ThreatSeverity,
    check_threat,
    get_guardrails,
    get_mitigation_strategies,
    get_prevention_framework,
    get_threat_profile,
)

log = logging.getLogger("grid.security.hardened_middleware")

# Context variable for request-scoped security context
_security_context: ContextVar[SecurityContext | None] = ContextVar("security_context", default=None)


# =============================================================================
# SECURITY CONTEXT
# =============================================================================


@dataclass
class SecurityContext:
    """Request-scoped security context."""

    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str | None = None
    client_ip: str = ""
    user_agent: str = ""
    path: str = ""
    method: str = ""
    start_time: float = field(default_factory=time.monotonic)

    # Security state
    authenticated: bool = False
    auth_level: str = "NONE"
    user_id: str | None = None

    # Threat tracking
    threats_detected: list[dict[str, Any]] = field(default_factory=list)
    mitigation_actions: list[str] = field(default_factory=list)
    blocked: bool = False
    block_reason: str | None = None

    # Rate limiting
    rate_limit_remaining: int = -1
    rate_limit_reset: datetime | None = None

    # Audit trail
    audit_entries: list[dict[str, Any]] = field(default_factory=list)

    def add_threat(self, threat: dict[str, Any]) -> None:
        """Add detected threat to context."""
        self.threats_detected.append(threat)

    def add_action(self, action: str) -> None:
        """Add mitigation action to context."""
        if action not in self.mitigation_actions:
            self.mitigation_actions.append(action)

    def block(self, reason: str) -> None:
        """Block the request."""
        self.blocked = True
        self.block_reason = reason
        self.add_action("BLOCK")

    def audit(self, event: str, details: dict[str, Any] | None = None) -> None:
        """Add audit entry."""
        self.audit_entries.append({
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "event": event,
            "details": details or {},
        })

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for logging."""
        return {
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
            "client_ip": self.client_ip,
            "path": self.path,
            "method": self.method,
            "authenticated": self.authenticated,
            "auth_level": self.auth_level,
            "threats_detected": len(self.threats_detected),
            "mitigation_actions": self.mitigation_actions,
            "blocked": self.blocked,
            "block_reason": self.block_reason,
            "duration_ms": (time.monotonic() - self.start_time) * 1000,
        }


def get_security_context() -> SecurityContext | None:
    """Get current request's security context."""
    return _security_context.get()


def set_security_context(ctx: SecurityContext) -> None:
    """Set security context for current request."""
    _security_context.set(ctx)


# =============================================================================
# RATE LIMITER
# =============================================================================


class AdaptiveRateLimiter:
    """
    Adaptive rate limiter with threat-aware thresholds.

    Features:
    - Per-client rate limiting
    - Adaptive limits based on threat level
    - Burst protection
    - Automatic cooldown
    """

    def __init__(self):
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._blocked: dict[str, datetime] = {}
        self._block_duration = timedelta(minutes=5)
        self._lock = asyncio.Lock()

    async def check(self, client_id: str) -> tuple[bool, int, datetime | None]:
        """
        Check if request is allowed.

        Returns:
            (allowed, remaining, reset_time)
        """
        async with self._lock:
            now = time.time()
            guardrails = get_guardrails()

            # Check if blocked
            if client_id in self._blocked:
                block_until = self._blocked[client_id]
                if datetime.now(tz=UTC) < block_until:
                    return False, 0, block_until
                else:
                    del self._blocked[client_id]

            # Get current thresholds
            rate_limit = int(guardrails.rate_limit_per_second.value)
            window = int(guardrails.frequency_window_seconds.value)
            burst = int(guardrails.rate_limit_burst.value)

            # Clean old requests
            cutoff = now - window
            self._requests[client_id] = [t for t in self._requests[client_id] if t > cutoff]

            # Check rate
            request_count = len(self._requests[client_id])

            # Check burst (requests in last second)
            recent_cutoff = now - 1.0
            recent_count = sum(1 for t in self._requests[client_id] if t > recent_cutoff)

            if recent_count >= burst:
                # Burst exceeded
                return False, 0, datetime.now(tz=UTC) + timedelta(seconds=1)

            if request_count >= rate_limit * window:
                # Rate limit exceeded
                reset_time = datetime.now(tz=UTC) + timedelta(seconds=window)
                return False, 0, reset_time

            # Record request
            self._requests[client_id].append(now)

            remaining = max(0, rate_limit * window - request_count - 1)
            return True, remaining, None

    async def block(self, client_id: str, duration: timedelta | None = None) -> None:
        """Block a client."""
        async with self._lock:
            block_until = datetime.now(tz=UTC) + (duration or self._block_duration)
            self._blocked[client_id] = block_until

    async def unblock(self, client_id: str) -> None:
        """Unblock a client."""
        async with self._lock:
            self._blocked.pop(client_id, None)

    async def cleanup(self) -> None:
        """Clean up expired entries."""
        async with self._lock:
            now = datetime.now(tz=UTC)
            expired = [k for k, v in self._blocked.items() if v < now]
            for k in expired:
                del self._blocked[k]


# =============================================================================
# THREAT RESPONSE HANDLER
# =============================================================================


class ThreatResponseHandler:
    """
    Handles automated threat response.

    Features:
    - Action execution
    - Response generation
    - Alert dispatching
    - Quarantine management
    """

    def __init__(self, rate_limiter: AdaptiveRateLimiter):
        self._rate_limiter = rate_limiter
        self._alert_queue: asyncio.Queue = asyncio.Queue()
        self._quarantine: dict[str, dict[str, Any]] = {}

    async def handle(
        self,
        ctx: SecurityContext,
        actions: list[MitigationAction],
        threat_info: dict[str, Any],
    ) -> Response | None:
        """
        Handle detected threat with mitigation actions.

        Returns Response if request should be blocked, None otherwise.
        """
        for action in actions:
            ctx.add_action(action.name)

            if action == MitigationAction.BLOCK:
                ctx.block(f"Threat detected: {threat_info.get('severity', 'UNKNOWN')}")
                await self._rate_limiter.block(ctx.client_ip)
                return self._create_blocked_response(ctx, threat_info)

            elif action == MitigationAction.THROTTLE:
                # Apply aggressive throttling
                await asyncio.sleep(1.0)  # Delay response

            elif action == MitigationAction.QUARANTINE:
                await self._quarantine_request(ctx, threat_info)

            elif action == MitigationAction.ALERT:
                await self._dispatch_alert(ctx, threat_info)

            elif action == MitigationAction.ESCALATE:
                await self._escalate(ctx, threat_info)

            elif action == MitigationAction.LOG:
                self._log_threat(ctx, threat_info)

        return None

    def _create_blocked_response(
        self, ctx: SecurityContext, threat_info: dict[str, Any]
    ) -> JSONResponse:
        """Create blocked response."""
        return JSONResponse(
            status_code=403,
            content={
                "error": "Request blocked by security policy",
                "request_id": ctx.request_id,
                "code": "SECURITY_VIOLATION",
            },
            headers={
                "X-Request-ID": ctx.request_id,
                "X-Security-Blocked": "true",
                "X-Block-Reason": ctx.block_reason or "security_policy",
            },
        )

    async def _quarantine_request(
        self, ctx: SecurityContext, threat_info: dict[str, Any]
    ) -> None:
        """Add request to quarantine for analysis."""
        self._quarantine[ctx.request_id] = {
            "context": ctx.to_dict(),
            "threat_info": threat_info,
            "quarantined_at": datetime.now(tz=UTC).isoformat(),
        }
        log.warning(
            "Request quarantined: %s from %s - %s",
            ctx.request_id,
            ctx.client_ip,
            threat_info.get("severity"),
        )

    async def _dispatch_alert(
        self, ctx: SecurityContext, threat_info: dict[str, Any]
    ) -> None:
        """Dispatch security alert."""
        alert = {
            "type": "security_alert",
            "severity": threat_info.get("severity", "UNKNOWN"),
            "request_id": ctx.request_id,
            "client_ip": ctx.client_ip,
            "path": ctx.path,
            "indicators": threat_info.get("indicators", []),
            "timestamp": datetime.now(tz=UTC).isoformat(),
        }
        await self._alert_queue.put(alert)
        log.warning("Security alert dispatched: %s", json.dumps(alert, default=str))

    async def _escalate(
        self, ctx: SecurityContext, threat_info: dict[str, Any]
    ) -> None:
        """Escalate to security team."""
        log.critical(
            "SECURITY ESCALATION: Request %s from %s - Severity: %s - Path: %s",
            ctx.request_id,
            ctx.client_ip,
            threat_info.get("severity"),
            ctx.path,
        )
        # In production, this would trigger PagerDuty/Slack alerts

    def _log_threat(self, ctx: SecurityContext, threat_info: dict[str, Any]) -> None:
        """Log threat detection."""
        log.info(
            "Threat detected: request=%s client=%s severity=%s indicators=%d",
            ctx.request_id,
            ctx.client_ip,
            threat_info.get("severity"),
            len(threat_info.get("indicators", [])),
        )


# =============================================================================
# INPUT VALIDATOR
# =============================================================================


class HardenedInputValidator:
    """
    Hardened input validation with comprehensive threat detection.

    Features:
    - Deep JSON validation
    - Header validation
    - Query parameter validation
    - Body content validation
    """

    def __init__(self):
        self._profile = get_threat_profile()

    async def validate_request(self, request: Request) -> dict[str, Any]:
        """
        Validate all aspects of the request.

        Returns dict with validation results.
        """
        results = {
            "valid": True,
            "threats": [],
            "sanitized_fields": [],
        }

        # Validate headers
        header_threats = await self._validate_headers(request)
        results["threats"].extend(header_threats)

        # Validate query parameters
        query_threats = await self._validate_query(request)
        results["threats"].extend(query_threats)

        # Validate body (if present)
        if request.method in ("POST", "PUT", "PATCH"):
            body_threats = await self._validate_body(request)
            results["threats"].extend(body_threats)

        # Determine overall validity
        if results["threats"]:
            max_severity = max(
                ThreatSeverity[t["severity"]].value
                for t in results["threats"]
            )
            results["valid"] = max_severity < ThreatSeverity.HIGH.value
            results["max_severity"] = ThreatSeverity(max_severity).name

        return results

    async def _validate_headers(self, request: Request) -> list[dict[str, Any]]:
        """Validate request headers."""
        threats = []

        # Check User-Agent
        user_agent = request.headers.get("user-agent", "")
        result = check_threat(user_agent, request.client.host if request.client else "unknown")
        if result["detected"]:
            threats.append({
                "source": "header:user-agent",
                "severity": result["severity"],
                "indicators": result["indicators"],
            })

        # Check for suspicious headers
        suspicious_headers = ["x-forwarded-for", "x-real-ip", "x-originating-ip"]
        for header in suspicious_headers:
            value = request.headers.get(header, "")
            if value:
                result = check_threat(value, request.client.host if request.client else "unknown")
                if result["detected"]:
                    threats.append({
                        "source": f"header:{header}",
                        "severity": result["severity"],
                        "indicators": result["indicators"],
                    })

        return threats

    async def _validate_query(self, request: Request) -> list[dict[str, Any]]:
        """Validate query parameters."""
        threats = []

        for key, value in request.query_params.items():
            # Check key
            key_result = check_threat(key, request.client.host if request.client else "unknown")
            if key_result["detected"]:
                threats.append({
                    "source": f"query_key:{key}",
                    "severity": key_result["severity"],
                    "indicators": key_result["indicators"],
                })

            # Check value
            value_result = check_threat(value, request.client.host if request.client else "unknown")
            if value_result["detected"]:
                threats.append({
                    "source": f"query_value:{key}",
                    "severity": value_result["severity"],
                    "indicators": value_result["indicators"],
                })

        return threats

    async def _validate_body(self, request: Request) -> list[dict[str, Any]]:
        """Validate request body."""
        threats = []

        try:
            # Read body
            body = await request.body()
            if not body:
                return threats

            # Check size
            guardrails = get_guardrails()
            max_size = int(guardrails.max_request_size_mb.value * 1024 * 1024)
            if len(body) > max_size:
                threats.append({
                    "source": "body:size",
                    "severity": ThreatSeverity.MEDIUM.name,
                    "indicators": [{"name": "oversized_body", "size": len(body), "max": max_size}],
                })
                return threats

            # Try to parse as JSON
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                threats.extend(await self._validate_json_body(body))
            else:
                # Check raw body content
                body_str = body.decode("utf-8", errors="replace")
                result = check_threat(body_str, request.client.host if request.client else "unknown")
                if result["detected"]:
                    threats.append({
                        "source": "body:raw",
                        "severity": result["severity"],
                        "indicators": result["indicators"],
                    })

        except Exception as e:
            log.warning("Body validation error: %s", e)

        return threats

    async def _validate_json_body(self, body: bytes) -> list[dict[str, Any]]:
        """Validate JSON body recursively."""
        threats = []

        try:
            data = json.loads(body)
            threats.extend(self._check_json_recursive(data, "body"))
        except json.JSONDecodeError:
            threats.append({
                "source": "body:json",
                "severity": ThreatSeverity.LOW.name,
                "indicators": [{"name": "invalid_json"}],
            })

        return threats

    def _check_json_recursive(
        self,
        data: Any,
        path: str,
        depth: int = 0,
    ) -> list[dict[str, Any]]:
        """Recursively check JSON data for threats."""
        threats = []

        # Check depth
        guardrails = get_guardrails()
        max_depth = int(guardrails.max_json_depth.value)
        if depth > max_depth:
            threats.append({
                "source": f"{path}:depth",
                "severity": ThreatSeverity.MEDIUM.name,
                "indicators": [{"name": "excessive_nesting", "depth": depth}],
            })
            return threats

        if isinstance(data, dict):
            for key, value in data.items():
                # Check key
                key_result = check_threat(str(key), "json")
                if key_result["detected"]:
                    threats.append({
                        "source": f"{path}.{key}:key",
                        "severity": key_result["severity"],
                        "indicators": key_result["indicators"],
                    })

                # Recurse into value
                threats.extend(self._check_json_recursive(value, f"{path}.{key}", depth + 1))

        elif isinstance(data, list):
            for i, item in enumerate(data):
                threats.extend(self._check_json_recursive(item, f"{path}[{i}]", depth + 1))

        elif isinstance(data, str):
            result = check_threat(data, "json")
            if result["detected"]:
                threats.append({
                    "source": path,
                    "severity": result["severity"],
                    "indicators": result["indicators"],
                })

        return threats


# =============================================================================
# HARDENED SECURITY MIDDLEWARE
# =============================================================================


class HardenedSecurityMiddleware(BaseHTTPMiddleware):
    """
    Production-grade security middleware with comprehensive protection.

    Features:
    - Adaptive rate limiting
    - Deep input validation
    - Threat detection and mitigation
    - Request/response logging
    - Security headers
    """

    # Paths excluded from security checks
    EXCLUDED_PATHS = frozenset([
        "/health",
        "/health/live",
        "/health/ready",
        "/ping",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json",
    ])

    def __init__(self, app: FastAPI, **kwargs):
        super().__init__(app)
        self._rate_limiter = AdaptiveRateLimiter()
        self._threat_handler = ThreatResponseHandler(self._rate_limiter)
        self._input_validator = HardenedInputValidator()
        self._prevention = get_prevention_framework()

        # Initialize baseline
        self._prevention.capture_baseline()

        log.info("HardenedSecurityMiddleware initialized")

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process request through security pipeline."""
        # Create security context
        ctx = SecurityContext(
            correlation_id=request.headers.get("x-correlation-id"),
            client_ip=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", ""),
            path=request.url.path,
            method=request.method,
        )
        set_security_context(ctx)
        ctx.audit("request_received")

        try:
            # Check if path is excluded
            if request.url.path in self.EXCLUDED_PATHS:
                response = await call_next(request)
                return self._add_security_headers(response, ctx)

            # Rate limiting
            allowed, remaining, reset_time = await self._rate_limiter.check(ctx.client_ip)
            ctx.rate_limit_remaining = remaining
            ctx.rate_limit_reset = reset_time

            if not allowed:
                ctx.block("Rate limit exceeded")
                ctx.audit("rate_limit_exceeded")
                return self._create_rate_limit_response(ctx)

            # Input validation
            validation = await self._input_validator.validate_request(request)

            if validation["threats"]:
                ctx.audit("threats_detected", {"threats": validation["threats"]})

                for threat in validation["threats"]:
                    ctx.add_threat(threat)

                # Get mitigation actions
                if validation.get("max_severity"):
                    max_severity = ThreatSeverity[validation["max_severity"]]
                    # Use first threat's category for mitigation lookup
                    category = ThreatCategory.INJECTION  # Default

                    mitigation = get_mitigation_strategies()
                    actions = mitigation.evaluate(category, max_severity, ctx.client_ip)

                    # Handle threat
                    if actions:
                        block_response = await self._threat_handler.handle(
                            ctx,
                            [MitigationAction[a] if isinstance(a, str) else a for a in actions],
                            {"severity": validation["max_severity"], "indicators": validation["threats"]},
                        )
                        if block_response:
                            return block_response

            # Run periodic security validation
            if ctx.request_id.endswith("0"):  # ~10% of requests
                validation_result = self._prevention.run_continuous_validation()
                if validation_result.get("assertion_violations"):
                    log.warning(
                        "Security assertion violations: %s",
                        validation_result["assertion_violations"],
                    )

            # Process request
            response = await call_next(request)

            # Add security headers and audit
            response = self._add_security_headers(response, ctx)
            ctx.audit("request_completed", {"status_code": response.status_code})

            # Log if threats were detected but not blocked
            if ctx.threats_detected:
                log.info(
                    "Request completed with threats: %s",
                    json.dumps(ctx.to_dict(), default=str),
                )

            return response

        except Exception as e:
            ctx.audit("request_error", {"error": str(e)})
            log.exception("Error in security middleware: %s", e)
            raise

    def _add_security_headers(self, response: Response, ctx: SecurityContext) -> Response:
        """Add security headers to response."""
        # Standard security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), usb=(), interest-cohort=()"
        )

        # Request tracking headers
        response.headers["X-Request-ID"] = ctx.request_id
        if ctx.correlation_id:
            response.headers["X-Correlation-ID"] = ctx.correlation_id

        # Security status headers
        response.headers["X-Security-Enforced"] = "true"
        if ctx.threats_detected:
            response.headers["X-Threats-Detected"] = str(len(ctx.threats_detected))
        if ctx.mitigation_actions:
            response.headers["X-Mitigation-Actions"] = ",".join(ctx.mitigation_actions)

        # Rate limit headers
        if ctx.rate_limit_remaining >= 0:
            response.headers["X-RateLimit-Remaining"] = str(ctx.rate_limit_remaining)
        if ctx.rate_limit_reset:
            response.headers["X-RateLimit-Reset"] = ctx.rate_limit_reset.isoformat()

        # HSTS for HTTPS
        if ctx.path.startswith("https"):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response

    def _create_rate_limit_response(self, ctx: SecurityContext) -> JSONResponse:
        """Create rate limit exceeded response."""
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "request_id": ctx.request_id,
                "code": "RATE_LIMIT_EXCEEDED",
                "retry_after": 60,
            },
            headers={
                "X-Request-ID": ctx.request_id,
                "Retry-After": "60",
                "X-RateLimit-Remaining": "0",
            },
        )


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================


def add_hardened_security(app: FastAPI, **kwargs) -> HardenedSecurityMiddleware:
    """Add hardened security middleware to FastAPI app."""
    middleware = HardenedSecurityMiddleware(app, **kwargs)
    app.add_middleware(HardenedSecurityMiddleware)
    return middleware


@asynccontextmanager
async def security_context_manager(
    request_id: str | None = None,
    client_ip: str = "unknown",
):
    """Context manager for manual security context."""
    ctx = SecurityContext(
        request_id=request_id or str(uuid.uuid4()),
        client_ip=client_ip,
    )
    set_security_context(ctx)
    try:
        yield ctx
    finally:
        set_security_context(None)
