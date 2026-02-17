"""
Security Enforcer Middleware for Runtime Security Validation.

Provides defense-in-depth security enforcement at the middleware level,
integrating with the API Sentinels system for unified security policy
enforcement across all API endpoints.

Key Features:
1. Input sanitization verification
2. Authentication level enforcement
3. Request integrity validation
4. Security header enforcement
5. Audit trail generation
6. Real-time threat detection

Usage:
    from application.mothership.middleware.security_enforcer import SecurityEnforcerMiddleware

    app.add_middleware(
        SecurityEnforcerMiddleware,
        strict_mode=True,
    )
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from ..security.api_sentinels import (
    APISecurityDefaults,
    InputSanitizer,
    get_api_defaults,
)

# Import audit service (optional)
try:
    from ..services.audit_service import MothershipAuditService
except ImportError:
    MothershipAuditService = None  # type: ignore[misc, assignment]

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class SecurityViolation:
    """A security violation detected during request processing."""

    violation_type: str
    severity: str  # "low", "medium", "high", "critical"
    description: str
    path: str
    method: str
    client_ip: str | None = None
    user_id: str | None = None
    request_id: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging/storage."""
        return {
            "violation_type": self.violation_type,
            "severity": self.severity,
            "description": self.description,
            "path": self.path,
            "method": self.method,
            "client_ip": self.client_ip,
            "user_id": self.user_id,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class SecurityAuditEntry:
    """An entry in the security audit log."""

    request_id: str
    path: str
    method: str
    client_ip: str | None
    user_id: str | None
    auth_method: str | None
    auth_level: str | None
    sanitization_applied: bool
    threats_detected: int
    violations: list[SecurityViolation]
    allowed: bool
    response_code: int
    latency_ms: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "request_id": self.request_id,
            "path": self.path,
            "method": self.method,
            "client_ip": self.client_ip,
            "user_id": self.user_id,
            "auth_method": self.auth_method,
            "auth_level": self.auth_level,
            "sanitization_applied": self.sanitization_applied,
            "threats_detected": self.threats_detected,
            "violations_count": len(self.violations),
            "allowed": self.allowed,
            "response_code": self.response_code,
            "latency_ms": round(self.latency_ms, 2),
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class EnforcerMetrics:
    """Metrics for the security enforcer."""

    total_requests: int = 0
    allowed_requests: int = 0
    blocked_requests: int = 0
    sanitized_requests: int = 0
    violations_detected: int = 0
    threats_detected: int = 0
    auth_failures: int = 0

    # Per-violation type counts
    violation_counts: dict[str, int] = field(default_factory=dict)

    def record_request(
        self,
        allowed: bool,
        sanitized: bool,
        violations: list[SecurityViolation],
        threats: int,
    ) -> None:
        """Record metrics for a request."""
        self.total_requests += 1

        if allowed:
            self.allowed_requests += 1
        else:
            self.blocked_requests += 1

        if sanitized:
            self.sanitized_requests += 1

        self.violations_detected += len(violations)
        self.threats_detected += threats

        for violation in violations:
            vtype = violation.violation_type
            self.violation_counts[vtype] = self.violation_counts.get(vtype, 0) + 1

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_requests": self.total_requests,
            "allowed_requests": self.allowed_requests,
            "blocked_requests": self.blocked_requests,
            "sanitized_requests": self.sanitized_requests,
            "block_rate": (round(self.blocked_requests / self.total_requests, 4) if self.total_requests > 0 else 0.0),
            "violations_detected": self.violations_detected,
            "threats_detected": self.threats_detected,
            "auth_failures": self.auth_failures,
            "violation_counts": self.violation_counts,
        }


# =============================================================================
# Security Enforcer Middleware
# =============================================================================


class SecurityEnforcerMiddleware(BaseHTTPMiddleware):
    """
    Runtime security enforcement middleware.

    Provides comprehensive security validation for all API requests,
    integrating with the API Sentinels system for unified policy enforcement.

    Security Checks:
    1. Input sanitization - Validate and sanitize request bodies
    2. Authentication verification - Ensure proper auth for protected endpoints
    3. Request integrity - Validate content-type, size, and structure
    4. HTTPS enforcement - Require secure transport in production
    5. Security headers - Ensure proper response headers

    Usage:
        app.add_middleware(
            SecurityEnforcerMiddleware,
            strict_mode=True,
            audit_logging=True,
        )
    """

    def __init__(
        self,
        app: ASGIApp,
        strict_mode: bool = True,
        audit_logging: bool = True,
        sanitize_inputs: bool = True,
        enforce_https: bool = True,
        enforce_auth: bool = True,
        max_body_size: int = 10 * 1024 * 1024,  # 10MB
        allowed_content_types: list[str] | None = None,
        excluded_paths: list[str] | None = None,
        security_defaults: APISecurityDefaults | None = None,
        block_insecure_transport: bool = False,
    ):
        """
        Initialize security enforcer middleware.

        Args:
            app: ASGI application
            strict_mode: If True, block on any security violation
            audit_logging: If True, log all security events
            sanitize_inputs: If True, sanitize request bodies
            enforce_https: If True, require HTTPS in production
            enforce_auth: If True, enforce authentication requirements
            max_body_size: Maximum allowed request body size
            allowed_content_types: Allowed Content-Type values
            excluded_paths: Paths excluded from enforcement
            security_defaults: Custom security defaults
            block_insecure_transport: If True with strict_mode, block HTTP requests
        """
        super().__init__(app)

        self.strict_mode = strict_mode
        self.audit_logging = audit_logging
        self.sanitize_inputs = sanitize_inputs
        self.enforce_https = enforce_https
        self.enforce_auth = enforce_auth
        self.max_body_size = max_body_size
        self.block_insecure_transport = block_insecure_transport
        self.audit_service: Any | None = None  # Set via set_audit_service()
        self.allowed_content_types = allowed_content_types or [
            "application/json",
            "application/x-www-form-urlencoded",
            "multipart/form-data",
            "text/plain",
        ]
        self.excluded_paths = excluded_paths or [
            "/health",
            "/health/live",
            "/health/ready",
            "/health/startup",
            "/ping",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]
        self.defaults = security_defaults or get_api_defaults()

        # Initialize sanitizer
        self.sanitizer = InputSanitizer(
            strict_mode=strict_mode,
            max_input_length=max_body_size,
        )

        # Metrics
        self.metrics = EnforcerMetrics()

        # Audit log (in-memory, could be replaced with external service)
        self._audit_log: list[SecurityAuditEntry] = []
        self._max_audit_entries = 10000

    def _is_excluded(self, path: str) -> bool:
        """Check if path is excluded from security enforcement."""
        return any(path == excluded or path.startswith(excluded.rstrip("/") + "/") for excluded in self.excluded_paths)

    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public (no auth required)."""
        return any(path == pub or path.startswith(pub.rstrip("/") + "/") for pub in self.defaults.public_endpoints)

    def _get_client_ip(self, request: Request) -> str | None:
        """Extract client IP from request."""
        # Check X-Forwarded-For header (for proxied requests)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # Fall back to direct client IP
        if request.client:
            return request.client.host

        return None

    def _get_request_id(self, request: Request) -> str:
        """Get or generate request ID."""
        return request.headers.get("X-Request-ID") or str(uuid.uuid4())

    def _get_user_id(self, request: Request) -> str | None:
        """Extract user ID from request state if available."""
        if hasattr(request.state, "user_id"):
            return request.state.user_id
        if hasattr(request.state, "auth") and isinstance(request.state.auth, dict):
            return request.state.auth.get("user_id")
        return None

    def _get_auth_info(self, request: Request) -> tuple[str | None, str | None]:
        """Extract authentication info from request."""
        auth_method = None
        auth_level = None

        if hasattr(request.state, "auth") and isinstance(request.state.auth, dict):
            auth = request.state.auth
            auth_method = auth.get("method")
            auth_level = auth.get("auth_level") or auth.get("role")

        # Check for auth headers
        if not auth_method:
            if request.headers.get("Authorization"):
                auth_method = "bearer"
            elif request.headers.get("X-API-Key"):
                auth_method = "api_key"

        return auth_method, auth_level

    async def _validate_content_type(
        self,
        request: Request,
        violations: list[SecurityViolation],
    ) -> bool:
        """Validate request Content-Type header."""
        if request.method not in ("POST", "PUT", "PATCH"):
            return True

        content_type = request.headers.get("Content-Type", "")

        # Extract base content type (without charset, etc.)
        base_type = content_type.split(";")[0].strip().lower()

        if not base_type:
            violations.append(
                SecurityViolation(
                    violation_type="missing_content_type",
                    severity="medium",
                    description="Missing Content-Type header for request with body",
                    path=request.url.path,
                    method=request.method,
                )
            )
            return not self.strict_mode

        # Check if content type is allowed
        allowed = any(
            base_type == allowed.lower() or base_type.startswith(allowed.lower())
            for allowed in self.allowed_content_types
        )

        if not allowed:
            violations.append(
                SecurityViolation(
                    violation_type="invalid_content_type",
                    severity="medium",
                    description=f"Disallowed Content-Type: {base_type}",
                    path=request.url.path,
                    method=request.method,
                    metadata={"content_type": base_type},
                )
            )
            return not self.strict_mode

        return True

    async def _validate_content_length(
        self,
        request: Request,
        violations: list[SecurityViolation],
    ) -> bool:
        """Validate request Content-Length header."""
        content_length_str = request.headers.get("Content-Length")

        if content_length_str:
            try:
                content_length = int(content_length_str)
                if content_length > self.max_body_size:
                    violations.append(
                        SecurityViolation(
                            violation_type="body_too_large",
                            severity="medium",
                            description=f"Request body exceeds maximum size ({content_length} > {self.max_body_size})",
                            path=request.url.path,
                            method=request.method,
                            metadata={
                                "content_length": content_length,
                                "max_size": self.max_body_size,
                            },
                        )
                    )
                    return False
            except ValueError:
                violations.append(
                    SecurityViolation(
                        violation_type="invalid_content_length",
                        severity="low",
                        description=f"Invalid Content-Length header: {content_length_str}",
                        path=request.url.path,
                        method=request.method,
                    )
                )
                return not self.strict_mode

        return True

    async def _validate_https(
        self,
        request: Request,
        violations: list[SecurityViolation],
    ) -> bool:
        """Validate HTTPS usage."""
        if not self.enforce_https:
            return True

        # Check scheme
        is_https = request.url.scheme == "https"

        # Also check X-Forwarded-Proto for proxied requests
        forwarded_proto = request.headers.get("X-Forwarded-Proto", "").lower()
        if forwarded_proto:
            is_https = forwarded_proto == "https"

        if not is_https:
            violations.append(
                SecurityViolation(
                    violation_type="insecure_transport",
                    severity="high",
                    description="Request made over insecure HTTP connection",
                    path=request.url.path,
                    method=request.method,
                )
            )
            # Block HTTP requests in strict mode when block_insecure_transport is enabled
            if self.strict_mode and self.block_insecure_transport:
                logger.warning(
                    f"Blocking insecure HTTP request to {request.url.path} "
                    "(strict_mode=True, block_insecure_transport=True)"
                )
                return False

        return True

    async def _validate_authentication(
        self,
        request: Request,
        violations: list[SecurityViolation],
    ) -> bool:
        """Validate authentication for protected endpoints."""
        if not self.enforce_auth:
            return True

        # Skip public endpoints
        if self._is_public_endpoint(request.url.path):
            return True

        auth_method, auth_level = self._get_auth_info(request)

        # Check if any auth is present
        has_auth = bool(request.headers.get("Authorization") or request.headers.get("X-API-Key") or auth_method)

        if not has_auth:
            violations.append(
                SecurityViolation(
                    violation_type="missing_authentication",
                    severity="high",
                    description="No authentication provided for protected endpoint",
                    path=request.url.path,
                    method=request.method,
                )
            )
            self.metrics.auth_failures += 1
            return not self.strict_mode

        return True

    async def _sanitize_body(
        self,
        request: Request,
    ) -> tuple[bool, int, bytes | None]:
        """
        Sanitize request body.

        Returns:
            Tuple of (is_safe, threats_count, sanitized_body)
        """
        if not self.sanitize_inputs:
            return True, 0, None

        if request.method not in ("POST", "PUT", "PATCH"):
            return True, 0, None

        content_type = request.headers.get("Content-Type", "")

        # Only sanitize JSON bodies
        if "application/json" not in content_type.lower():
            return True, 0, None

        try:
            body = await request.body()

            if not body:
                return True, 0, None

            # Parse JSON
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                # Invalid JSON, let the application handle it
                return True, 0, None

            # Sanitize the data
            if isinstance(data, dict):
                sanitized_data, threats = self.sanitizer.sanitize_dict(data)

                if threats:
                    logger.warning(
                        f"Detected {len(threats)} threats in request body for {request.url.path}",
                        extra={"threats": threats},
                    )

                    if self.strict_mode:
                        # Check if any threats require rejection
                        reject_threats = [t for t in threats if t.get("severity", 0) >= 8]
                        if reject_threats:
                            return False, len(threats), None

                    # Return sanitized body
                    sanitized_body = json.dumps(sanitized_data).encode("utf-8")
                    return True, len(threats), sanitized_body

                return True, 0, None

            elif isinstance(data, str):
                result = self.sanitizer.sanitize_string(data)
                if not result.is_safe:
                    return False, len(result.threats_detected), None
                return True, len(result.threats_detected), None

            return True, 0, None

        except Exception as e:
            logger.error(f"Error sanitizing request body: {e}")
            return True, 0, None

    def set_audit_service(self, audit_service: Any) -> None:
        """Set the audit service for persistent logging."""
        self.audit_service = audit_service
        logger.info("Audit service configured for SecurityEnforcer")

    def _log_audit_entry(self, entry: SecurityAuditEntry) -> None:
        """Log an audit entry."""
        if not self.audit_logging:
            return

        # Use audit service if available (persistent, hash-chained)
        if self.audit_service is not None:
            try:
                self.audit_service.log_security_event(entry)
            except Exception as e:
                logger.warning(f"Audit service logging failed: {e}, using fallback")
                self._log_audit_entry_fallback(entry)
        else:
            self._log_audit_entry_fallback(entry)

    def _log_audit_entry_fallback(self, entry: SecurityAuditEntry) -> None:
        """Fallback in-memory audit logging."""
        # Add to in-memory log
        self._audit_log.append(entry)

        # Trim if too large
        if len(self._audit_log) > self._max_audit_entries:
            self._audit_log = self._audit_log[-self._max_audit_entries :]

        # Log based on severity
        if not entry.allowed:
            logger.warning(
                f"Security: Blocked request to {entry.path}",
                extra=entry.to_dict(),
            )
        elif entry.violations:
            logger.info(
                f"Security: Allowed request with {len(entry.violations)} violations",
                extra=entry.to_dict(),
            )

    def get_audit_log(
        self,
        limit: int = 100,
        path_filter: str | None = None,
        violations_only: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Get audit log entries.

        Args:
            limit: Maximum entries to return
            path_filter: Filter by path prefix
            violations_only: Only return entries with violations

        Returns:
            List of audit log entry dictionaries
        """
        entries = self._audit_log.copy()

        if path_filter:
            entries = [e for e in entries if e.path.startswith(path_filter)]

        if violations_only:
            entries = [e for e in entries if e.violations]

        # Return most recent entries
        return [e.to_dict() for e in entries[-limit:]]

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process request through security enforcer."""
        start_time = time.perf_counter()

        # Check for audit service in app state (set by middleware setup)
        if self.audit_service is None and hasattr(request.app, "state"):
            audit_svc = getattr(request.app.state, "audit_service", None)
            if audit_svc is not None:
                self.audit_service = audit_svc

        # Skip excluded paths
        if self._is_excluded(request.url.path):
            return await call_next(request)

        request_id = self._get_request_id(request)
        client_ip = self._get_client_ip(request)
        violations: list[SecurityViolation] = []
        threats_count = 0
        sanitized = False

        # Store request ID in state
        request.state.request_id = request_id

        # Validate Content-Type
        if not await self._validate_content_type(request, violations):
            return self._block_response(request_id, violations, "Invalid Content-Type")

        # Validate Content-Length
        if not await self._validate_content_length(request, violations):
            return self._block_response(request_id, violations, "Request body too large")

        # Validate HTTPS
        await self._validate_https(request, violations)

        # Validate authentication (don't block yet, just record)
        await self._validate_authentication(request, violations)

        # Sanitize body
        is_safe, threats_count, sanitized_body = await self._sanitize_body(request)

        if not is_safe and self.strict_mode:
            violations.append(
                SecurityViolation(
                    violation_type="malicious_payload",
                    severity="critical",
                    description="Malicious content detected in request body",
                    path=request.url.path,
                    method=request.method,
                    client_ip=client_ip,
                )
            )
            return self._block_response(request_id, violations, "Malicious content detected")

        if threats_count > 0:
            sanitized = True

        if sanitized_body is not None:
            request._body = sanitized_body  # type: ignore[attr-defined]
            request.state.sanitized_body = True
            request.state.threats_count = threats_count

        # Check for critical violations in strict mode
        if self.strict_mode:
            critical_violations = [v for v in violations if v.severity in ("high", "critical")]
            if critical_violations:
                return self._block_response(
                    request_id,
                    violations,
                    critical_violations[0].description,
                )

        # Process request
        try:
            response = await call_next(request)
            response_code = response.status_code
            allowed = True
        except Exception as e:
            logger.exception(f"Error processing request: {e}")
            response_code = 500
            allowed = False
            raise
        finally:
            latency_ms = (time.perf_counter() - start_time) * 1000

            # Get auth info
            auth_method, auth_level = self._get_auth_info(request)
            user_id = self._get_user_id(request)

            # Update violations with context
            for v in violations:
                v.client_ip = client_ip
                v.user_id = user_id
                v.request_id = request_id

            # Create audit entry
            audit_entry = SecurityAuditEntry(
                request_id=request_id,
                path=request.url.path,
                method=request.method,
                client_ip=client_ip,
                user_id=user_id,
                auth_method=auth_method,
                auth_level=auth_level,
                sanitization_applied=sanitized,
                threats_detected=threats_count,
                violations=violations,
                allowed=allowed,
                response_code=response_code,
                latency_ms=latency_ms,
            )

            # Log and record metrics
            self._log_audit_entry(audit_entry)
            self.metrics.record_request(
                allowed=allowed,
                sanitized=sanitized,
                violations=violations,
                threats=threats_count,
            )

        # Add security headers to response
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Security-Enforced"] = "true"

        if violations:
            response.headers["X-Security-Violations"] = str(len(violations))

        return response

    def _block_response(
        self,
        request_id: str,
        violations: list[SecurityViolation],
        message: str,
    ) -> JSONResponse:
        """Generate a blocked response."""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "success": False,
                "error": {
                    "code": "SECURITY_VIOLATION",
                    "message": message,
                    "violations_count": len(violations),
                },
                "request_id": request_id,
            },
            headers={
                "X-Request-ID": request_id,
                "X-Security-Enforced": "true",
                "X-Security-Blocked": "true",
            },
        )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "SecurityViolation",
    "SecurityAuditEntry",
    "EnforcerMetrics",
    "SecurityEnforcerMiddleware",
]
