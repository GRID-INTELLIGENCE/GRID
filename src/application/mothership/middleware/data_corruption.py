"""Data corruption detection middleware for FastAPI.

This middleware automatically detects and reports data corruption events during
request processing. It integrates with the DataCorruptionPenaltyTracker to apply
penalties to endpoints that cause data or environment corruption.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from grid.resilience.data_corruption_penalty import (
    CorruptionSeverity,
    CorruptionType,
    DataCorruptionPenaltyTracker,
    record_corruption_event,
)

logger = logging.getLogger(__name__)

class DataCorruptionDetectionMiddleware(BaseHTTPMiddleware):
    """Middleware that detects and reports data corruption events."""
    
    def __init__(
        self,
        app: ASGIApp,
        tracker: DataCorruptionPenaltyTracker | None = None,
        critical_endpoints: set[str] | None = None,
        corruption_indicators: dict[str, dict[str, Any]] | None = None,
    ):
        super().__init__(app)
        self.tracker = tracker or DataCorruptionPenaltyTracker()
        self.critical_endpoints = critical_endpoints or set()
        self.corruption_indicators = corruption_indicators or {
            "500": {
                "severity": CorruptionSeverity.MEDIUM,
                "corruption_type": CorruptionType.ENVIRONMENT,
                "description": "Internal server error - potential data corruption",
            },
            "503": {
                "severity": CorruptionSeverity.HIGH,
                "corruption_type": CorruptionType.ENVIRONMENT,
                "description": "Service unavailable - environment instability",
            },
            "integrity_error": {
                "severity": CorruptionSeverity.CRITICAL,
                "corruption_type": CorruptionType.REFERENTIAL_INTEGRITY,
                "description": "Database integrity constraint violated",
            },
            "validation_error": {
                "severity": CorruptionSeverity.MEDIUM,
                "corruption_type": CorruptionType.DATA_VALIDATION,
                "description": "Data validation failed - corrupt input data",
            },
            "deadlock": {
                "severity": CorruptionSeverity.HIGH,
                "corruption_type": CorruptionType.PERFORMANCE,
                "description": "Deadlock detected - concurrent data corruption risk",
            },
            "timeout": {
                "severity": CorruptionSeverity.LOW,
                "corruption_type": CorruptionType.PERFORMANCE,
                "description": "Request timeout - potential resource issue",
            },
        }
        self._tracked_requests: dict[str, dict[str, Any]] = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process a request and detect any corruption events."""
        request_id = str(id(request))
        correlation_id = request.headers.get("X-Correlation-ID", str(datetime.now(UTC).timestamp()))
        endpoint = f"{request.method} {request.url.path}"
        
        # Track request metadata
        self._tracked_requests[request_id] = {
            "endpoint": endpoint,
            "correlation_id": correlation_id,
            "start_time": datetime.now(UTC),
            "metadata": {
                "user_agent": request.headers.get("User-Agent"),
                "content_type": request.headers.get("Content-Type"),
                "client_ip": request.client.host if request.client else None,
            }
        }
        
        try:
            response = await call_next(request)
            
            # Check for corruption indicators in response
            await self._check_response_for_corruption(
                request_id, response, correlation_id
            )
            
            # Add corruption penalty headers to response
            penalty = self.tracker.get_endpoint_penalty(endpoint)
            response.headers["X-Data-Penalty-Score"] = str(penalty)
            response.headers["X-Data-Penalty-Correlation-ID"] = correlation_id
            
            if self.tracker.is_endpoint_critical(endpoint):
                response.headers["X-Endpoint-Critical"] = "true"
                response.headers["X-Endpoint-Warning"] = "Data corruption detected"
            
            return response
            
        except Exception as e:
            # Record exception as potential corruption event
            await self._record_exception_as_corruption(
                request_id, e, correlation_id
            )
            
            # Re-raise the exception to let other handlers deal with it
            raise
        finally:
            # Clean up tracking data
            self._tracked_requests.pop(request_id, None)
    
    async def _check_response_for_corruption(
        self,
        request_id: str,
        response: Response,
        correlation_id: str,
    ) -> None:
        """Check response for indicators of data corruption."""
        request_data = self._tracked_requests.get(request_id)
        if not request_data:
            return
        
        endpoint = request_data["endpoint"]
        status_code = str(response.status_code)
        
        # Check status code indicators
        if status_code in self.corruption_indicators:
            indicator = self.corruption_indicators[status_code]
            
            # Only record if it's a server error
            if response.status_code >= 500:
                self._record_corruption_from_indicator(
                    endpoint, correlation_id, indicator, request_data
                )
    
    def _record_corruption_from_indicator(
        self,
        endpoint: str,
        correlation_id: str,
        indicator: dict[str, Any],
        request_data: dict[str, Any],
    ) -> None:
        """Record a corruption event from a detected indicator."""
        severity = indicator.get("severity", CorruptionSeverity.LOW)
        corruption_type = indicator.get("corruption_type", CorruptionType.ENVIRONMENT)
        description = indicator.get("description", "Unknown corruption detected")
        
        penalty = record_corruption_event(
            endpoint=endpoint,
            severity=severity,
            corruption_type=corruption_type,
            description=description,
            correlation_id=correlation_id,
            metadata=request_data.get("metadata", {}),
        )
        
        logger.warning(
            "Corruption indicator detected for %s: %s (penalty: %.2f)",
            endpoint, description, penalty
        )
    
    async def _record_exception_as_corruption(
        self,
        request_id: str,
        exception: Exception,
        correlation_id: str,
    ) -> None:
        """Record an exception as a potential corruption event."""
        request_data = self._tracked_requests.get(request_id)
        if not request_data:
            return
        
        endpoint = request_data["endpoint"]
        exception_type = type(exception).__name__
        
        # Determine severity and type based on exception
        corruption_info = self._classify_exception(exception)
        
        penalty = record_corruption_event(
            endpoint=endpoint,
            severity=corruption_info["severity"],
            corruption_type=corruption_info["corruption_type"],
            description=f"{corruption_info['description']}: {str(exception)}",
            correlation_id=correlation_id,
            metadata={
                **request_data.get("metadata", {}),
                "exception_type": exception_type,
            },
            stack_trace=str(exception) if hasattr(exception, "__traceback__") else None,
        )
        
        logger.error(
            "Exception detected as corruption for %s: %s (penalty: %.2f)",
            endpoint, str(exception), penalty,
            exc_info=True
        )
    
    def _classify_exception(self, exception: Exception) -> dict[str, Any]:
        """Classify an exception to determine corruption severity and type."""
        exception_name = type(exception).__name__.lower()
        exception_str = str(exception).lower()
        
        # Database integrity errors
        if any(term in exception_name for term in ["integrity", "constraint", "foreign"]):
            return {
                "severity": CorruptionSeverity.CRITICAL,
                "corruption_type": CorruptionType.REFERENTIAL_INTEGRITY,
                "description": "Database integrity constraint violated",
            }
        
        # Validation errors
        if any(term in exception_name for term in ["validation", "value", "type"]):
            return {
                "severity": CorruptionSeverity.MEDIUM,
                "corruption_type": CorruptionType.DATA_VALIDATION,
                "description": "Data validation failed",
            }
        
        # Deadlock and concurrency issues
        if any(term in exception_str for term in ["deadlock", "lock timeout", "concurrent"]):
            return {
                "severity": CorruptionSeverity.HIGH,
                "corruption_type": CorruptionType.PERFORMANCE,
                "description": "Concurrency issue detected",
            }
        
        # Schema errors
        if any(term in exception_str for term in ["column", "table", "schema", "does not exist"]):
            return {
                "severity": CorruptionSeverity.HIGH,
                "corruption_type": CorruptionType.SCHEMA_VIOLATION,
                "description": "Schema violation detected",
            }
        
        # Connection and environment errors
        if any(term in exception_name for term in ["connection", "timeout", "refused", "unavailable"]):
            return {
                "severity": CorruptionSeverity.HIGH,
                "corruption_type": CorruptionType.ENVIRONMENT,
                "description": "Environment connectivity issue",
            }
        
        # Default: environment error with medium severity
        return {
            "severity": CorruptionSeverity.MEDIUM,
            "corruption_type": CorruptionType.ENVIRONMENT,
            "description": "Unhandled exception detected",
        }
    
    def get_endpoint_health_report(self, endpoint: str) -> dict[str, Any]:
        """Get a health report for a specific endpoint."""
        return self.tracker.get_endpoint_health(endpoint)
    
    def get_critical_endpoints_report(self) -> list[dict[str, Any]]:
        """Get a report of all critical endpoints."""
        critical = self.tracker.get_critical_endpoints()
        return [
            {
                "endpoint": endpoint,
                "penalty_score": penalty,
                **self.tracker.get_endpoint_health(endpoint)
            }
            for endpoint, penalty in critical
        ]
    
    def add_corruption_indicator(
        self,
        name: str,
        severity: CorruptionSeverity,
        corruption_type: CorruptionType,
        description: str,
    ) -> None:
        """Add a custom corruption indicator."""
        self.corruption_indicators[name] = {
            "severity": severity,
            "corruption_type": corruption_type,
            "description": description,
        }


def create_data_corruption_middleware(
    app: FastAPI,
    tracker: DataCorruptionPenaltyTracker | None = None,
    critical_endpoints: set[str] | None = None,
) -> DataCorruptionDetectionMiddleware:
    """Create and attach the data corruption detection middleware to a FastAPI app.
    
    Args:
        app: The FastAPI application
        tracker: Optional custom tracker instance
        critical_endpoints: Set of endpoints to always monitor closely
        
    Returns:
        The configured middleware instance
    """
    middleware = DataCorruptionDetectionMiddleware(
        app=app,
        tracker=tracker,
        critical_endpoints=critical_endpoints,
    )
    
    # Add middleware to app (it will be handled by FastAPI's middleware stack)
    app.add_middleware(DataCorruptionDetectionMiddleware)
    
    logger.info("Data corruption detection middleware initialized")
    return middleware
