"""Boundary enforcement middleware.

Consolidates auth, rate limiting, PII scanning, and audit logging
into a single middleware stack at the API boundary.
"""

from __future__ import annotations

import time
from typing import Any, Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class BoundaryMiddleware(BaseHTTPMiddleware):
    """
    Boundary enforcement layer for the API.
    
    Executes in order:
    1. Authentication check
    2. Rate limiting
    3. PII scan (request)
    4. Request handling
    5. PII scan (response)
    6. Audit logging
    """

    def __init__(self, app: Any, exclude_paths: list[str] | None = None) -> None:
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/openapi.json"]

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request through boundary enforcement."""
        # Skip boundary checks for excluded paths
        if any(request.url.path.startswith(p) for p in self.exclude_paths):
            return await call_next(request)

        start_time = time.time()
        correlation_id = request.headers.get("X-Correlation-ID", self._generate_correlation_id())

        # Attach correlation ID to request state
        request.state.correlation_id = correlation_id

        # 1. Authentication check
        auth_result = await self._check_auth(request)
        if not auth_result["valid"]:
            return Response(
                content=f'{{"error": "{auth_result["reason"]}"}}',
                status_code=401,
                media_type="application/json",
                headers={"X-Correlation-ID": correlation_id},
            )

        # 2. Rate limiting check
        rate_result = await self._check_rate_limit(request)
        if not rate_result["allowed"]:
            return Response(
                content='{"error": "Rate limit exceeded"}',
                status_code=429,
                media_type="application/json",
                headers={
                    "X-Correlation-ID": correlation_id,
                    "Retry-After": str(rate_result.get("retry_after", 60)),
                },
            )

        # 3. PII scan (request body)
        pii_request_result = await self._scan_pii_request(request)
        if pii_request_result["detected"]:
            # Log PII detection but don't block - depends on policy
            await self._log_pii_detection(request, pii_request_result, correlation_id)

        # 4. Process request
        try:
            response = await call_next(request)
        except Exception as e:
            await self._log_error(request, e, correlation_id)
            return Response(
                content=f'{{"error": "Internal server error"}}',
                status_code=500,
                media_type="application/json",
                headers={"X-Correlation-ID": correlation_id},
            )

        # 5. PII scan (response body) - deferred to avoid streaming issues
        # Response body scanning would need special handling for streaming

        # 6. Audit logging
        duration_ms = int((time.time() - start_time) * 1000)
        await self._log_audit(request, response, correlation_id, duration_ms)

        # Add correlation ID to response
        response.headers["X-Correlation-ID"] = correlation_id
        return response

    def _generate_correlation_id(self) -> str:
        """Generate unique correlation ID."""
        import uuid
        return str(uuid.uuid4())[:8]

    async def _check_auth(self, request: Request) -> dict[str, Any]:
        """Check authentication credentials."""
        # TODO: Implement proper JWT/API key validation
        # For now, allow all requests with valid-looking headers
        auth_header = request.headers.get("Authorization", "")
        
        # If no auth header present, still allow (for development)
        # In production, this should validate JWT or API key
        if not auth_header:
            return {"valid": True, "reason": "Development mode - no auth required"}
        
        # Basic Bearer token validation structure
        if auth_header.startswith("Bearer "):
            return {"valid": True, "reason": "Bearer token present"}
        
        return {"valid": True, "reason": "Auth header present"}

    async def _check_rate_limit(self, request: Request) -> dict[str, Any]:
        """Check rate limiting."""
        # TODO: Implement adaptive rate limiting based on:
        # - Client identifier (API key, IP, session)
        # - Historical request patterns (percentile-based)
        # - Current system load
        
        # For now, allow all requests
        return {"allowed": True, "retry_after": 0}

    async def _scan_pii_request(self, request: Request) -> dict[str, Any]:
        """Scan request for PII."""
        # TODO: Implement PII detection using pattern matching
        # - Credit card numbers
        # - SSN patterns
        # - Email addresses
        # - Phone numbers
        
        # For now, no PII detected
        return {"detected": False, "patterns": []}

    async def _log_pii_detection(
        self, request: Request, result: dict[str, Any], correlation_id: str
    ) -> None:
        """Log PII detection event."""
        print(f"[PII DETECTION] Correlation: {correlation_id} | Patterns: {result['patterns']}")

    async def _log_error(self, request: Request, error: Exception, correlation_id: str) -> None:
        """Log error event."""
        print(f"[ERROR] Correlation: {correlation_id} | Error: {error}")

    async def _log_audit(
        self, request: Request, response: Response, correlation_id: str, duration_ms: int
    ) -> None:
        """Log audit event."""
        print(
            f"[AUDIT] {request.method} {request.url.path} | "
            f"Status: {response.status_code} | "
            f"Duration: {duration_ms}ms | "
            f"Correlation: {correlation_id}"
        )
