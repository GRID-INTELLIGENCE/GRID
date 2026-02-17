"""
Accountability Contract Middleware.
Enforces accountability contracts with RBAC and claims support.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Callable

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from grid.resilience.accountability.contracts import EnforcementResult

# Import enhanced enforcer
from grid.resilience.accountability.enforcer_enhanced import (
    get_enhanced_accountability_enforcer,
)

logger = logging.getLogger(__name__)


class AccountabilityContractMiddleware(BaseHTTPMiddleware):
    """Middleware that enforces accountability contracts for all requests."""

    def __init__(
        self,
        app: Any,
        enforcement_mode: str = "monitor",  # monitor, enforce, disabled
        contract_path: str | None = None,
        skip_paths: list[str] | None = None,
    ):
        """Initialize accountability contract middleware.

        Args:
            app: FastAPI application
            enforcement_mode: How to handle violations (monitor/enforce/disabled)
            contract_path: Path to contract file (optional)
            skip_paths: List of paths to skip enforcement
        """
        super().__init__(app)

        self.enforcement_mode = enforcement_mode
        self.contract_path = contract_path
        self.skip_paths = skip_paths or [
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/favicon.ico",
        ]

        # Initialize enhanced enforcer
        self.enforcer = get_enhanced_accountability_enforcer()
        self.enforcer.enforcement_mode = enforcement_mode
        if contract_path:
            self.enforcer.contract_path = contract_path

        logger.info(
            f"Accountability contract middleware initialized: mode={enforcement_mode}, "
            f"skip_paths={len(self.skip_paths)}"
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through accountability contract enforcement."""

        # Skip enforcement for certain paths
        if self._should_skip_enforcement(request):
            return await call_next(request)

        start_time = time.time()

        try:
            # Extract authentication context
            auth_context = await self._extract_auth_context(request)

            # Extract request data
            request_data = await self._extract_request_data(request)

            # Enforce request contract
            request_result = self.enforcer.enforce_request(
                path=request.url.path,
                method=request.method,
                auth_context=auth_context,
                request_data=request_data,
                client_ip=self._get_client_ip(request),
            )

            # Handle request enforcement result
            if not request_result.allowed:
                return self._create_blocked_response(request_result)

            # Process request
            response = await call_next(request)

            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000

            # Extract response data for validation
            response_data = await self._extract_response_data(response)

            # Enforce response contract
            response_result = self.enforcer.enforce_response(
                path=request.url.path,
                method=request.method,
                response_data=response_data,
                response_status=response.status_code,
                response_time_ms=response_time_ms,
            )

            # Add enforcement headers
            self._add_enforcement_headers(response, request_result, response_result)

            # Log violations
            self._log_violations(request, request_result, response_result)

            return response

        except Exception as e:
            logger.error(f"Accountability middleware error: {e}")
            # In case of middleware error, allow request but log
            response = await call_next(request)
            response.headers["X-Accountability-Error"] = "middleware_error"
            return response

    def _should_skip_enforcement(self, request: Request) -> bool:
        """Check if enforcement should be skipped for this request."""
        path = request.url.path

        # Skip exact matches
        if path in self.skip_paths:
            return True

        # Skip prefix matches
        for skip_path in self.skip_paths:
            if path.startswith(skip_path):
                return True

        return False

    async def _extract_auth_context(self, request: Request) -> dict[str, Any] | None:
        """Extract authentication context from request."""
        try:
            # Try to get auth context from request state (set by auth middleware)
            if hasattr(request.state, "auth_context"):
                return request.state.auth_context

            # Try to extract from headers (fallback)
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # This would need JWT verification - for now, just mark as authenticated
                return {
                    "authenticated": True,
                    "user_id": "unknown",
                    "roles": ["user"],  # Default role
                    "permissions": ["read", "execute"],
                }

            api_key = request.headers.get("x-api-key")
            if api_key:
                return {
                    "authenticated": True,
                    "user_id": "api_user",
                    "roles": ["service_account"],
                    "permissions": ["read", "write", "execute"],
                }

            # No authentication found
            return {
                "authenticated": False,
                "user_id": "anonymous",
                "roles": ["anonymous"],
                "permissions": ["read"],
            }

        except Exception as e:
            logger.warning(f"Failed to extract auth context: {e}")
            return None

    async def _extract_request_data(self, request: Request) -> dict[str, Any] | None:
        """Extract request data for validation."""
        try:
            # Only extract for methods that typically have bodies
            if request.method in ["POST", "PUT", "PATCH"]:
                # For JSON requests
                if "application/json" in request.headers.get("content-type", ""):
                    return await request.json()

                # For form requests
                if "application/x-www-form-urlencoded" in request.headers.get("content-type", ""):
                    form_data = await request.form()
                    return dict(form_data)

            # For GET requests, extract query params
            if request.method == "GET":
                return dict(request.query_params)

            return None

        except Exception as e:
            logger.debug(f"Failed to extract request data: {e}")
            return None

    async def _extract_response_data(self, response: Response) -> dict[str, Any] | None:
        """Extract response data for validation."""
        try:
            # Only attempt validation for JSON responses
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                # Note: This is a simplified approach
                # In practice, you'd need to capture the response body
                # before it's sent to the client
                return None  # Would need response body capture

            return None

        except Exception as e:
            logger.debug(f"Failed to extract response data: {e}")
            return None

    def _get_client_ip(self, request: Request) -> str | None:
        """Extract client IP from request."""
        try:
            # Check for forwarded headers
            forwarded_for = request.headers.get("x-forwarded-for")
            if forwarded_for:
                return forwarded_for.split(",")[0].strip()

            real_ip = request.headers.get("x-real-ip")
            if real_ip:
                return real_ip

            return request.client.host if request.client else None

        except Exception:
            return None

    def _create_blocked_response(self, request_result: EnforcementResult) -> Response:
        """Create response for blocked requests."""

        # Find the most critical violation
        critical_violations = [v for v in request_result.violations if v.severity.value == "critical"]
        high_violations = [v for v in request_result.violations if v.severity.value == "high"]

        if critical_violations:
            status_code = status.HTTP_403_FORBIDDEN
            detail = "Access denied: Critical security violations"
        elif high_violations:
            status_code = status.HTTP_403_FORBIDDEN
            detail = "Access denied: Security policy violations"
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            detail = "Access denied: Policy violations"

        # Create JSON error response
        error_response = {
            "error": "access_denied",
            "detail": detail,
            "violations": [
                {
                    "type": v.type.value,
                    "severity": v.severity.value,
                    "message": v.message,
                    "field": v.field,
                }
                for v in request_result.violations
            ],
            "enforcement_mode": self.enforcement_mode,
        }

        return Response(
            content=json.dumps(error_response),
            status_code=status_code,
            media_type="application/json",
        )

    def _log_violations(
        self,
        request: Request,
        request_result: EnforcementResult,
        response_result: EnforcementResult | None,
    ) -> None:
        """Log accountability violations for audit trail."""
        all_violations = list(request_result.violations)
        if response_result:
            all_violations.extend(response_result.violations)

        if not all_violations:
            return

        for violation in all_violations:
            log_data = {
                "path": str(request.url.path),
                "method": request.method,
                "type": violation.type.value,
                "severity": violation.severity.value,
                "message": violation.message,
                "field": violation.field,
                "penalty_points": violation.penalty_points,
                "enforcement_mode": self.enforcement_mode,
            }

            if violation.severity.value in ["critical", "high"]:
                logger.error(f"Accountability violation: {log_data}")
            else:
                logger.warning(f"Accountability violation: {log_data}")

        # Log summary
        logger.info(
            f"Accountability check: {request.method} {request.url.path} "
            f"- {len(all_violations)} violations, mode={self.enforcement_mode}"
        )


# Global middleware instance for access
_global_accountability_middleware: AccountabilityContractMiddleware | None = None


def get_accountability_middleware() -> AccountabilityContractMiddleware:
    """Get the global accountability contract middleware instance."""
    global _global_accountability_middleware
    if _global_accountability_middleware is None:
        raise RuntimeError("Accountability contract middleware not initialized")
    return _global_accountability_middleware


def set_accountability_middleware(middleware: AccountabilityContractMiddleware) -> None:
    """Set the global accountability contract middleware instance."""
    global _global_accountability_middleware
    _global_accountability_middleware = middleware
