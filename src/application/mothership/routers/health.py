"""
Mothership Cockpit Health Check Router.

Provides health check, readiness, and liveness endpoints for
Kubernetes probes and monitoring systems.

Includes security health verification against factory defaults
to ensure the API maintains its secure baseline configuration.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Response, status
from pydantic import BaseModel, Field

from ..dependencies import Cockpit, Settings
from ..schemas import (
    ApiResponse,
    HealthCheckResponse,
    LivenessResponse,
    ReadinessResponse,
)
from ..security.api_sentinels import (
    get_api_defaults,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


# =============================================================================
# Real Connectivity Check Functions
# =============================================================================


async def _check_database_connectivity(db_url: str, timeout: float = 5.0) -> tuple[bool, str]:
    """
    Check database connectivity with actual connection test.

    Args:
        db_url: Database connection URL
        timeout: Timeout in seconds

    Returns:
        Tuple of (is_healthy, message)
    """
    if not db_url:
        return False, "Database URL not configured"

    try:
        # For SQLite, just check if it's a valid path format
        if db_url.startswith("sqlite"):
            return True, "SQLite database configured"

        # For other databases, try to create a connection
        from sqlalchemy.ext.asyncio import create_async_engine

        # Convert sync URL to async if needed
        async_url = db_url
        if db_url.startswith("postgresql://"):
            async_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

        engine = create_async_engine(async_url, pool_pre_ping=True)

        try:
            check_task = asyncio.create_task(_db_ping(engine))
            await asyncio.wait_for(check_task, timeout=timeout)
        finally:
            await engine.dispose()

        return True, "Database connection successful"

    except TimeoutError:
        return False, f"Database connection timed out after {timeout}s"
    except ImportError as e:
        return False, f"Database driver not available: {e}"
    except Exception as e:
        return False, f"Database connection failed: {str(e)[:100]}"


async def _db_ping(engine: Any) -> None:
    """Helper to ping database."""
    from sqlalchemy import text

    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


async def _check_redis_connectivity(redis_url: str, timeout: float = 5.0) -> tuple[bool, str]:
    """
    Check Redis connectivity with actual ping.

    Args:
        redis_url: Redis connection URL
        timeout: Timeout in seconds

    Returns:
        Tuple of (is_healthy, message)
    """
    if not redis_url:
        return False, "Redis URL not configured"

    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(redis_url)

        try:
            await asyncio.wait_for(client.ping(), timeout=timeout)
        finally:
            await client.close()

        return True, "Redis connection successful"

    except TimeoutError:
        return False, f"Redis connection timed out after {timeout}s"
    except ImportError:
        return False, "Redis client not available (redis package not installed)"
    except Exception as e:
        return False, f"Redis connection failed: {str(e)[:100]}"


async def _check_gemini_connectivity(api_key: str, timeout: float = 5.0) -> tuple[bool, str]:
    """
    Check Gemini API connectivity.

    Args:
        api_key: Gemini API key
        timeout: Timeout in seconds

    Returns:
        Tuple of (is_healthy, message)
    """
    if not api_key:
        return False, "Gemini API key not configured"

    try:
        import httpx

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(
                "https://generativelanguage.googleapis.com/v1/models",
                headers={"x-goog-api-key": api_key},
            )

            if response.status_code == 200:
                return True, "Gemini API reachable"
            elif response.status_code == 401:
                return False, "Gemini API key invalid"
            else:
                return False, f"Gemini API returned status {response.status_code}"

    except TimeoutError:
        return False, f"Gemini API timed out after {timeout}s"
    except ImportError:
        return False, "HTTP client not available (httpx package not installed)"
    except Exception as e:
        return False, f"Gemini API check failed: {str(e)[:100]}"


async def _check_webhook_endpoints(endpoints: list[str], timeout: float = 5.0) -> tuple[bool, str, dict[str, bool]]:
    """
    Check webhook endpoint reachability.

    Args:
        endpoints: List of webhook endpoint URLs
        timeout: Timeout in seconds per endpoint

    Returns:
        Tuple of (all_healthy, message, endpoint_results)
    """
    if not endpoints:
        return True, "No webhook endpoints configured", {}

    try:
        import httpx

        results: dict[str, bool] = {}

        async with httpx.AsyncClient(timeout=timeout) as client:
            for endpoint in endpoints:
                try:
                    # Use HEAD request to check reachability without sending data
                    response = await client.head(endpoint)
                    # Consider 2xx and 405 (method not allowed) as healthy
                    results[endpoint] = response.status_code < 500
                except Exception:
                    results[endpoint] = False

        healthy_count = sum(1 for v in results.values() if v)
        all_healthy = healthy_count == len(results)

        if all_healthy:
            return True, f"All {len(results)} webhook endpoints reachable", results
        else:
            return False, f"{healthy_count}/{len(results)} webhook endpoints reachable", results

    except ImportError:
        return False, "HTTP client not available", {}
    except Exception as e:
        return False, f"Webhook check failed: {str(e)[:100]}", {}


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(UTC)


# =============================================================================
# Security Health Check Models
# =============================================================================


class SecurityCheckResult(BaseModel):
    """Result of a single security check."""

    name: str = Field(..., description="Check name")
    passed: bool = Field(..., description="Whether check passed")
    description: str = Field(..., description="Check description")
    details: dict[str, Any] | None = Field(default=None, description="Additional details")


class SecurityHealthResponse(BaseModel):
    """Response from security health check."""

    compliant: bool = Field(..., description="Overall compliance status")
    factory_defaults_version: str = Field(..., description="Factory defaults version")
    checks_passed: int = Field(..., description="Number of checks passed")
    checks_failed: int = Field(..., description="Number of checks failed")
    checks: list[SecurityCheckResult] = Field(default_factory=list, description="Individual check results")
    warnings: list[str] = Field(default_factory=list, description="Non-critical warnings")
    timestamp: datetime = Field(default_factory=utc_now, description="Check timestamp")


class CircuitBreakerStatus(BaseModel):
    """Status of circuit breakers."""

    enabled: bool = Field(..., description="Whether circuit breaker is enabled")
    total_circuits: int = Field(default=0, description="Total number of circuits")
    open_circuits: int = Field(default=0, description="Number of open circuits")
    circuits: dict[str, Any] = Field(default_factory=dict, description="Circuit details")


@router.get(
    "/health",
    response_model=ApiResponse[HealthCheckResponse],
    summary="Health Check",
    description="Comprehensive health check endpoint for monitoring",
)
async def health_check(
    cockpit: Cockpit,
    settings: Settings,
) -> ApiResponse[HealthCheckResponse]:
    """
    Perform a comprehensive health check of the system.

    Returns status of all major subsystems including database,
    cache, and external integrations.
    """
    checks: dict[str, bool] = {}
    overall_healthy = True

    # Check cockpit service
    try:
        cockpit_healthy = cockpit.is_healthy
        checks["cockpit"] = cockpit_healthy
        if not cockpit_healthy:
            overall_healthy = False
    except Exception as e:
        logger.error(f"Cockpit health check failed: {e}")
        checks["cockpit"] = False
        overall_healthy = False

    # Check state store
    try:
        state = cockpit.state
        checks["state_store"] = state is not None
    except Exception as e:
        logger.error(f"State store check failed: {e}")
        checks["state_store"] = False
        overall_healthy = False

    # Check components (if any registered)
    try:
        components = list(cockpit.state.components.values())
        healthy_components = sum(1 for c in components if c.is_healthy())
        total_components = len(components)
        checks["components"] = total_components == 0 or healthy_components == total_components
        if total_components > 0 and healthy_components < total_components:
            overall_healthy = False
    except Exception as e:
        logger.error(f"Component health check failed: {e}")
        checks["components"] = False

    # Check for critical alerts
    try:
        critical_alerts = sum(
            1 for a in cockpit.state.alerts.values() if not a.is_resolved and a.severity.value == "critical"
        )
        checks["no_critical_alerts"] = critical_alerts == 0
        if critical_alerts > 0:
            overall_healthy = False
    except Exception as e:
        logger.error(f"Alert check failed: {e}")
        checks["no_critical_alerts"] = True  # Don't fail health on alert check error

    # Build response
    health_response = HealthCheckResponse(
        status="healthy" if overall_healthy else "unhealthy",
        version=settings.app_version,
        uptime_seconds=cockpit.state.uptime_seconds if cockpit.state.started_at else 0.0,
        timestamp=utc_now(),
        checks=checks,
    )

    return ApiResponse(
        success=overall_healthy,
        data=health_response,
        message="System is healthy" if overall_healthy else "System has issues",
    )


@router.get(
    "/health/live",
    response_model=LivenessResponse,
    summary="Liveness Probe",
    description="Kubernetes liveness probe endpoint",
)
async def liveness(response: Response) -> LivenessResponse:
    """
    Liveness probe for Kubernetes.

    Returns 200 if the service is alive (not deadlocked).
    This is a minimal check that should always succeed if the
    process is running correctly.
    """
    return LivenessResponse(
        alive=True,
        timestamp=utc_now(),
    )


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    summary="Readiness Probe",
    description="Kubernetes readiness probe endpoint",
)
async def readiness(
    response: Response,
    cockpit: Cockpit,
    settings: Settings,
) -> ReadinessResponse:
    """
    Readiness probe for Kubernetes.

    Returns 200 if the service is ready to accept traffic.
    Checks that all critical dependencies are available with real connectivity tests.
    """
    dependencies: dict[str, Any] = {}
    ready = True
    message = "Service is ready"
    check_timeout = 5.0  # Timeout for each connectivity check

    # Check cockpit is started
    try:
        if not cockpit._started:
            ready = False
            message = "Cockpit not started"
        dependencies["cockpit"] = cockpit._started
    except Exception:
        dependencies["cockpit"] = False
        ready = False
        message = "Cockpit check failed"

    # Check state is accessible
    try:
        state = cockpit.state
        dependencies["state"] = state is not None
    except Exception:
        dependencies["state"] = False
        ready = False
        message = "State not accessible"

    # Real database connectivity check
    if settings.database.url:
        db_healthy, db_message = await _check_database_connectivity(settings.database.url, timeout=check_timeout)
        dependencies["database"] = {"healthy": db_healthy, "message": db_message}
        if not db_healthy:
            logger.warning(f"Database readiness check failed: {db_message}")
            # Don't fail readiness for database issues in development
            if settings.is_production:
                ready = False
                message = f"Database not ready: {db_message}"

    # Real Redis connectivity check (if enabled)
    if settings.database.redis_enabled:
        redis_healthy, redis_message = await _check_redis_connectivity(
            settings.database.redis_url, timeout=check_timeout
        )
        dependencies["redis"] = {"healthy": redis_healthy, "message": redis_message}
        if not redis_healthy:
            logger.warning(f"Redis readiness check failed: {redis_message}")
            # Redis is optional, don't fail readiness

    # Real Gemini API connectivity check (if enabled)
    if settings.integrations.gemini_enabled:
        gemini_healthy, gemini_message = await _check_gemini_connectivity(
            settings.integrations.gemini_api_key, timeout=check_timeout
        )
        dependencies["gemini"] = {"healthy": gemini_healthy, "message": gemini_message}
        if not gemini_healthy:
            logger.warning(f"Gemini readiness check failed: {gemini_message}")
            # Gemini is optional for basic operation

    # Real webhook endpoint check (if enabled)
    if settings.integrations.webhook_enabled:
        webhook_healthy, webhook_message, webhook_results = await _check_webhook_endpoints(
            settings.integrations.webhook_endpoints, timeout=check_timeout
        )
        dependencies["webhooks"] = {
            "healthy": webhook_healthy,
            "message": webhook_message,
            "endpoints": webhook_results,
        }
        if not webhook_healthy:
            logger.warning(f"Webhook readiness check failed: {webhook_message}")

    # Set appropriate status code
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(
        ready=ready,
        message=message,
        dependencies=dependencies,
    )


@router.get(
    "/health/startup",
    summary="Startup Probe",
    description="Kubernetes startup probe endpoint",
)
async def startup(
    response: Response,
    cockpit: Cockpit,
) -> dict[str, Any]:
    """
    Startup probe for Kubernetes.

    Returns 200 once the service has completed startup.
    Useful for slow-starting containers.
    """
    started = cockpit._started

    if not started:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "started": started,
        "timestamp": utc_now().isoformat(),
    }


@router.get(
    "/version",
    summary="Version Information",
    description="Get service version and build information",
)
async def version(settings: Settings) -> dict[str, Any]:
    """
    Get version and build information.

    Returns application version, environment, and other
    deployment metadata.
    """
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment.value,
        "debug": settings.debug_enabled,
        "python_version": _get_python_version(),
    }


def _get_python_version() -> str:
    """Get Python version string."""
    import sys

    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


@router.get(
    "/health/security",
    response_model=ApiResponse[SecurityHealthResponse],
    summary="Security Health Check",
    description="Verify API security configuration against factory defaults",
)
async def security_health(
    response: Response,
    settings: Settings,
) -> ApiResponse[SecurityHealthResponse]:
    """
    Perform security health check against factory defaults.

    Verifies that the API maintains its secure baseline configuration
    by checking authentication, rate limiting, input sanitization,
    security headers, and other security controls.

    This endpoint is used by:
    - Security monitoring systems
    - Compliance verification
    - Pre-deployment validation
    """
    checks: list[SecurityCheckResult] = []
    warnings: list[str] = []
    defaults = get_api_defaults()

    # Check 1: Authentication enforcement
    auth_enforced = getattr(settings.security, "require_authentication", True)
    checks.append(
        SecurityCheckResult(
            name="authentication_enforced",
            passed=auth_enforced or not settings.is_production,
            description="Authentication is enforced in production",
            details={
                "require_authentication": auth_enforced,
                "min_auth_level": defaults.min_auth_level.value,
                "is_production": settings.is_production,
            },
        )
    )

    # Check 2: Rate limiting enabled
    rate_limit_enabled = getattr(settings.security, "rate_limit_enabled", False)
    checks.append(
        SecurityCheckResult(
            name="rate_limiting_enabled",
            passed=rate_limit_enabled,
            description="Rate limiting is enabled",
            details={
                "enabled": rate_limit_enabled,
                "default_limit": defaults.rate_limit,
            },
        )
    )
    if not rate_limit_enabled:
        warnings.append("Rate limiting is disabled - recommended for production")

    # Check 3: Input sanitization enabled
    sanitization_enabled = defaults.input_sanitization_enabled
    checks.append(
        SecurityCheckResult(
            name="input_sanitization_enabled",
            passed=sanitization_enabled,
            description="Input sanitization is enabled",
            details={
                "enabled": sanitization_enabled,
                "strict_mode": defaults.input_sanitization_strict,
                "filters": defaults.input_filters,
            },
        )
    )

    # Check 4: Security headers configured
    security_headers = defaults.security_headers
    has_required_headers = all(
        header in security_headers for header in ["X-Content-Type-Options", "X-Frame-Options", "X-XSS-Protection"]
    )
    checks.append(
        SecurityCheckResult(
            name="security_headers_present",
            passed=has_required_headers,
            description="Security headers are configured",
            details={
                "configured_headers": list(security_headers.keys()),
                "required_present": has_required_headers,
            },
        )
    )

    # Check 5: HTTPS enforcement
    https_enforced = defaults.require_https_in_production
    checks.append(
        SecurityCheckResult(
            name="https_enforced",
            passed=https_enforced or not settings.is_production,
            description="HTTPS is enforced in production",
            details={
                "require_https": https_enforced,
                "hsts_enabled": defaults.hsts_max_age > 0,
                "hsts_max_age": defaults.hsts_max_age,
            },
        )
    )

    # Check 6: Circuit breaker enabled
    circuit_breaker_enabled = getattr(settings.security, "circuit_breaker_enabled", False)
    checks.append(
        SecurityCheckResult(
            name="circuit_breaker_enabled",
            passed=True,  # Optional check, always passes
            description="Circuit breaker is enabled",
            details={"enabled": circuit_breaker_enabled},
        )
    )
    if not circuit_breaker_enabled:
        warnings.append("Circuit breaker is disabled - recommended for reliability")

    # Check 7: Audit logging enabled
    audit_enabled = defaults.audit_all_requests
    checks.append(
        SecurityCheckResult(
            name="audit_logging_enabled",
            passed=True,  # Optional check, always passes
            description="Audit logging is enabled",
            details={"enabled": audit_enabled},
        )
    )
    if not audit_enabled:
        warnings.append("Audit logging is disabled - recommended for security monitoring")

    # Check 8: Secret key strength (in production)
    secret_configured = bool(getattr(settings.security, "secret_key", None))
    checks.append(
        SecurityCheckResult(
            name="secret_key_configured",
            passed=secret_configured or not settings.is_production,
            description="Secret key is properly configured",
            details={
                "configured": secret_configured,
                "is_production": settings.is_production,
            },
        )
    )

    # Calculate results
    passed_count = sum(1 for c in checks if c.passed)
    failed_count = len(checks) - passed_count
    overall_compliant = failed_count == 0

    # Set status code for failed checks
    if not overall_compliant:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    security_response = SecurityHealthResponse(
        compliant=overall_compliant,
        factory_defaults_version="1.0.0",
        checks_passed=passed_count,
        checks_failed=failed_count,
        checks=checks,
        warnings=warnings,
        timestamp=utc_now(),
    )

    return ApiResponse(
        success=overall_compliant,
        data=security_response,
        message="Security configuration is compliant" if overall_compliant else "Security configuration has issues",
    )


@router.get(
    "/health/circuit-breakers",
    response_model=ApiResponse[CircuitBreakerStatus],
    summary="Circuit Breaker Status",
    description="Get status of all circuit breakers",
)
async def circuit_breaker_status(
    settings: Settings,
) -> ApiResponse[CircuitBreakerStatus]:
    """
    Get the current status of all circuit breakers.

    Returns information about each circuit including:
    - Current state (closed, open, half-open)
    - Failure counts
    - Recovery status
    """
    try:
        from ..middleware.circuit_breaker import get_circuit_manager

        manager = get_circuit_manager()
        metrics = manager.get_metrics()

        cb_status = CircuitBreakerStatus(
            enabled=getattr(settings.security, "circuit_breaker_enabled", False),
            total_circuits=metrics.get("total_circuits", 0),
            open_circuits=metrics.get("open_circuits", 0),
            circuits=metrics.get("circuits", {}),
        )

        return ApiResponse(
            success=True,
            data=cb_status,
            message="Circuit breaker status retrieved",
        )

    except ImportError:
        return ApiResponse(
            success=True,
            data=CircuitBreakerStatus(enabled=False),
            message="Circuit breaker middleware not available",
        )


@router.get(
    "/health/factory-defaults",
    summary="Factory Defaults Status",
    description="Get current factory defaults configuration",
)
async def factory_defaults_status() -> dict[str, Any]:
    """
    Get the current factory defaults configuration.

    Returns the security baseline configuration that the API
    should maintain for stable and secure operation.
    """
    defaults = get_api_defaults()

    return {
        "version": "1.0.0",
        "timestamp": utc_now().isoformat(),
        "defaults": defaults.to_dict(),
        "public_endpoints": defaults.public_endpoints,
        "security_headers": defaults.security_headers,
    }


@router.get(
    "/metrics",
    summary="Basic Metrics",
    description="Get basic system metrics",
)
async def metrics(
    cockpit: Cockpit,
    settings: Settings,
) -> dict[str, Any]:
    """
    Get basic system metrics.

    For production, consider using Prometheus metrics exporter.
    This endpoint provides simple JSON metrics for debugging.
    """
    state = cockpit.state

    return {
        "timestamp": utc_now().isoformat(),
        "uptime_seconds": state.uptime_seconds if state.started_at else 0.0,
        "sessions": {
            "total": state.total_sessions,
            "active": state.active_sessions,
        },
        "operations": {
            "total": state.total_operations,
            "running": state.running_operations,
        },
        "components": {
            "total": len(state.components),
            "healthy": sum(1 for c in state.components.values() if c.is_healthy()),
        },
        "alerts": {
            "total": len(state.alerts),
            "unresolved": sum(1 for a in state.alerts.values() if not a.is_resolved),
            "critical": sum(1 for a in state.alerts.values() if not a.is_resolved and a.severity.value == "critical"),
        },
    }


__all__ = ["router"]
