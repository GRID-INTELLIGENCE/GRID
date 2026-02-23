"""
Unified Mothership Cockpit FastAPI Application with DRT + Accountability Enforcement.

Integrates:
- Unified DRT middleware using core DRTMonitor engine
- Enhanced accountability contract enforcement with RBAC
- Complete security and monitoring stack
"""

from __future__ import annotations

import logging
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from application.api_docs import setup_api_docs

# Observability & Documentation
from application.monitoring import get_metrics_router, setup_metrics
from application.skills.api import router as skills_router
from application.tracing import setup_tracing

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from infrastructure.parasite_guard import add_parasite_guard

from .config import get_settings
from .db.engine import dispose_async_engine, get_async_engine
from .dependencies import get_cockpit_service
from .exceptions import MothershipError

# Accountability contract imports
from .middleware.accountability_contract import AccountabilityContractMiddleware, set_accountability_middleware

# Existing imports
# Unified DRT imports
from .middleware.drt_middleware_unified import UnifiedDRTMiddleware, set_unified_drt_middleware
from .routers import create_api_router
from .routers.agentic import router as agentic_router
from .routers.cockpit import router as cockpit_router
from .routers.corruption_monitoring import router as corruption_router
from .routers.drt_monitoring_unified import router as unified_drt_router
from .routers.health import router as health_router

# Security Infrastructure
from .security.api_sentinels import API_DEFAULTS, apply_defaults

# =============================================================================
# Logging Configuration
# =============================================================================

# Check for quiet mode (used by RAG chat and other CLI tools)
_quiet_mode = os.environ.get("GRID_QUIET", "").lower() in ("1", "true", "yes")
_log_level = logging.CRITICAL if _quiet_mode else logging.INFO

logging.basicConfig(
    level=_log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

# =============================================================================
# Response Models
# =============================================================================


class ErrorResponse(BaseModel):
    """Standard error response model."""

    success: bool = False
    error: dict[str, Any]
    request_id: str | None = None
    timestamp: str


class ValidationErrorDetail(BaseModel):
    """Validation error detail model."""

    loc: list[str | int]
    msg: str
    type: str


# =============================================================================
# Application Factory
# =============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager."""
    logger.info("Starting Mothership Cockpit application...")

    try:
        # Initialize database
        _engine = get_async_engine()  # noqa: F841 side-effect: initializes connection pool
        logger.info("Database engine initialized")

        # Initialize services
        cockpit_service = get_cockpit_service()
        await cockpit_service.initialize()
        logger.info("Cockpit service initialized")

        yield

    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    finally:
        # Cleanup
        try:
            await dispose_async_engine()
            logger.info("Database engine disposed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def create_app() -> FastAPI:
    """Create and configure FastAPI application with unified DRT + accountability."""

    # Load configuration
    settings = get_settings()

    # Create FastAPI app
    app = FastAPI(
        title="Mothership Cockpit",
        description="GRID Mothership Cockpit - Unified DRT & Accountability Enforcement",
        version="2.1.0",
        docs_url="/docs" if settings.environment.value != "production" else None,
        redoc_url="/redoc" if settings.environment.value != "production" else None,
        lifespan=lifespan,
    )

    # Setup API documentation
    setup_api_docs(app)

    # Setup tracing and metrics
    setup_tracing(app, settings)
    setup_metrics(app, settings)

    # =============================================================================
    # Middleware Setup (Unified Stack)
    # =============================================================================

    # 1. FastAPI built-in middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # 2. Mothership custom middlewares (Unified Setup)

    # Add Parasite Guard first (total Rickall defense)
    add_parasite_guard(app, settings)

    # Add Unified DRT Middleware with full security settings
    unified_drt_middleware = UnifiedDRTMiddleware(
        app=app,
        enabled=settings.security.drt_enabled,
        similarity_threshold=settings.security.drt_behavioral_similarity_threshold,
        retention_hours=settings.security.drt_retention_hours,
        enforcement_mode=settings.security.drt_enforcement_mode,
        websocket_monitoring_enabled=settings.security.drt_websocket_monitoring_enabled,
        api_movement_logging_enabled=settings.security.drt_api_movement_logging_enabled,
        penalty_points_enabled=settings.security.drt_penalty_points_enabled,
        slo_evaluation_interval_seconds=settings.security.drt_slo_evaluation_interval_seconds,
        slo_violation_penalty_base=settings.security.drt_slo_violation_penalty_base,
        report_generation_enabled=settings.security.drt_report_generation_enabled,
        sampling_rate=1.0,  # Sample all requests for security
        escalation_timeout_minutes=60,
        rate_limit_multiplier=0.5,
        alert_on_escalation=True,
    )

    # Set global DRT middleware for router access
    set_unified_drt_middleware(unified_drt_middleware)

    # Add DRT middleware to app
    app.add_middleware(lambda app: unified_drt_middleware)
    logger.info("Unified DRT middleware enabled")

    # Add Accountability Contract Middleware
    accountability_middleware = AccountabilityContractMiddleware(
        app=app,
        enforcement_mode=settings.security.drt_enforcement_mode,
        contract_path=None,  # Use default path
        skip_paths=[
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/favicon.ico",
            "/redoc",
        ],
    )

    # Set global accountability middleware
    set_accountability_middleware(accountability_middleware)

    # Add accountability middleware to app
    app.add_middleware(lambda app: accountability_middleware)
    logger.info("Accountability contract middleware enabled")

    # Add existing security and monitoring middleware
    from .middleware import setup_middleware

    setup_middleware(app, settings)

    # =============================================================================
    # Router Registration
    # =============================================================================

    # API router (core endpoints)
    api_router = create_api_router()
    app.include_router(api_router, prefix="/api/v1")

    # Specialized routers
    app.include_router(health_router, prefix="/health")
    app.include_router(cockpit_router, prefix="/api/v1/cockpit")
    app.include_router(agentic_router, prefix="/api/v1/agentic")
    app.include_router(skills_router, prefix="/api/v1/skills")
    app.include_router(corruption_router, prefix="/api/v1/corruption")

    # Unified DRT router (replaces original DRT router)
    app.include_router(unified_drt_router, prefix="/api/v1/drt")

    # Metrics router
    if settings.telemetry.enabled:
        metrics_router = get_metrics_router()
        app.include_router(metrics_router, prefix="/metrics")

    # =============================================================================
    # Exception Handlers
    # =============================================================================

    @app.exception_handler(MothershipError)
    async def mothership_exception_handler(request: Request, exc: MothershipError) -> JSONResponse:
        """Handle Mothership-specific exceptions."""
        request_id = getattr(request.state, "request_id", None)

        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error={"code": exc.error_code, "message": str(exc)},
                request_id=request_id,
                timestamp=datetime.now(UTC).isoformat(),
            ).dict(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle FastAPI request validation errors."""
        request_id = getattr(request.state, "request_id", None)

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=ErrorResponse(
                error={
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": exc.errors(),
                },
                request_id=request_id,
                timestamp=datetime.now(UTC).isoformat(),
            ).dict(),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle FastAPI HTTP exceptions."""
        request_id = getattr(request.state, "request_id", None)

        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error={"code": "HTTP_ERROR", "message": exc.detail},
                request_id=request_id,
                timestamp=datetime.now(UTC).isoformat(),
            ).dict(),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unhandled exceptions."""
        request_id = getattr(request.state, "request_id", None)
        logger.exception(f"Unhandled exception in request {request_id}: {exc}")

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error={"code": "INTERNAL_ERROR", "message": "Internal server error"},
                request_id=request_id,
                timestamp=datetime.now(UTC).isoformat(),
            ).dict(),
        )

    # =============================================================================
    # 3. Security Infrastructure
    # =============================================================================

    # Apply factory defaults to all endpoints
    apply_defaults(API_DEFAULTS, settings)

    # Add security middleware (already handled in setup_middleware)
    # This ensures authentication runs before accountability enforcement

    # =============================================================================
    # Application Info
    # =============================================================================

    @app.get("/info", tags=["System"])
    async def app_info() -> dict[str, Any]:
        """Get application information and configuration."""
        return {
            "name": "Mothership Cockpit",
            "version": "2.1.0-unified",
            "description": "GRID Mothership Cockpit with Unified DRT & Accountability Enforcement",
            "environment": settings.environment.value,
            "features": {
                "unified_drt": {
                    "enabled": settings.security.drt_enabled,
                    "enforcement_mode": settings.security.drt_enforcement_mode,
                    "similarity_threshold": settings.security.drt_behavioral_similarity_threshold,
                    "retention_hours": settings.security.drt_retention_hours,
                },
                "accountability_contracts": {
                    "enabled": True,
                    "enforcement_mode": settings.security.drt_enforcement_mode,
                },
                "security": {
                    "strict_mode": settings.security.strict_mode,
                    "input_sanitization_enabled": settings.security.input_sanitization_enabled,
                    "circuit_breaker_enabled": settings.security.circuit_breaker_enabled,
                    "parasite_guard_enabled": settings.security.parasite_guard_enabled,
                },
                "telemetry": {
                    "enabled": settings.telemetry.enabled,
                    "metrics_enabled": settings.telemetry.metrics_enabled,
                    "tracing_enabled": settings.telemetry.tracing_enabled,
                },
            },
            "timestamp": datetime.now(UTC).isoformat(),
        }

    logger.info("Mothership Cockpit application created with unified DRT + accountability")
    return app


# =============================================================================
# Entry Points
# =============================================================================


def main() -> FastAPI:
    """Main entry point for the application."""
    return create_app()


if __name__ == "__main__":
    import uvicorn

    app = main()

    # Get configuration from environment or defaults
    host = os.getenv("MOTHERSHIP_HOST", "0.0.0.0")  # noqa: S104 bind-all is intentional for container deployment
    port = int(os.getenv("MOTHERSHIP_PORT", "8080"))
    reload = os.getenv("MOTHERSHIP_RELOAD", "false").lower() == "true"
    workers = int(os.getenv("MOTHERSHIP_WORKERS", "1"))

    logger.info(f"Starting Mothership Cockpit on {host}:{port}")

    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        workers=workers if not reload else 1,
        log_level="info" if not _quiet_mode else "critical",
    )
