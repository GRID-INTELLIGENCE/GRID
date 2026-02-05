"""Accountability middleware for automatic endpoint delivery profiling.

Tracks endpoint delivery performance and adds accountability headers to responses.
Integrates with the resilience metrics and accountability calculator to provide
real-time delivery scoring.

Response Headers Added:
    - X-Delivery-Score: Numeric score (0-100+)
    - X-Delivery-Class: Classification (EXCELLENT, GOOD, DEGRADED, CRITICAL)
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

if TYPE_CHECKING:
    from fastapi import Request, Response

logger = logging.getLogger(__name__)

# Paths that should be tracked for accountability scoring
DEFAULT_TRACKED_PREFIXES = (
    "/api/",
    "/rag/",
    "/health/",
)


class AccountabilityMiddleware(BaseHTTPMiddleware):
    """Middleware to track endpoint delivery accountability.

    Automatically records operation metrics for each request and calculates
    delivery scores. Adds X-Delivery-Score and X-Delivery-Class headers
    to all responses for tracked paths.

    Attributes:
        tracked_prefixes: Tuple of path prefixes to track (default: /api/, /rag/, /health/)
        log_degraded: Whether to log warnings for DEGRADED/CRITICAL scores
    """

    def __init__(
        self,
        app: Any,
        tracked_prefixes: tuple[str, ...] | None = None,
        log_degraded: bool = True,
    ) -> None:
        """Initialize accountability middleware.

        Args:
            app: ASGI application.
            tracked_prefixes: Path prefixes to track. Defaults to /api/, /rag/, /health/.
            log_degraded: Whether to log warnings for degraded endpoints.
        """
        super().__init__(app)
        self.tracked_prefixes = tracked_prefixes or DEFAULT_TRACKED_PREFIXES
        self.log_degraded = log_degraded

    async def dispatch(
        self, request: "Request", call_next: RequestResponseEndpoint
    ) -> "Response":
        """Process request with accountability tracking.

        Args:
            request: Incoming request.
            call_next: Next middleware/handler.

        Returns:
            Response with accountability headers added.
        """
        path = request.url.path

        # Only track configured path prefixes
        if not any(path.startswith(prefix) for prefix in self.tracked_prefixes):
            return await call_next(request)

        # Build endpoint identifier
        endpoint = f"{request.method}:{path}"
        start_time = time.perf_counter()

        # Process request
        response = await call_next(request)

        # Calculate latency
        latency_ms = (time.perf_counter() - start_time) * 1000

        # Determine success based on status code
        success = response.status_code < 400

        try:
            # Import here to avoid circular imports and allow lazy loading
            from grid.resilience.accountability import get_accountability_calculator
            from grid.resilience.metrics import get_metrics_collector

            # Record the attempt in metrics
            collector = get_metrics_collector()
            collector.record_attempt(
                operation_name=endpoint,
                success=success,
                required_retry=False,
                error=None,
            )

            # Calculate delivery score
            calculator = get_accountability_calculator()
            score = calculator.calculate_score(endpoint, latency_ms)

            # Add accountability headers
            response.headers["X-Delivery-Score"] = str(round(score.score, 1))
            response.headers["X-Delivery-Class"] = score.classification

            # Log degraded/critical endpoints
            if self.log_degraded and score.classification in ("DEGRADED", "CRITICAL"):
                logger.warning(
                    "Endpoint delivery %s: %s (score: %.1f) - %s",
                    score.classification.lower(),
                    endpoint,
                    score.score,
                    score.recommendation,
                )

        except ImportError:
            # Resilience module not available, skip scoring
            logger.debug("Accountability scoring unavailable - resilience module not found")
        except Exception as e:
            # Don't let scoring errors break the request
            logger.warning("Accountability scoring failed for %s: %s", endpoint, e)

        return response


__all__ = [
    "AccountabilityMiddleware",
    "DEFAULT_TRACKED_PREFIXES",
]
