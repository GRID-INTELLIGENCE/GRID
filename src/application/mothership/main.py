"""
Mothership Cockpit FastAPI Application.

Main application factory and entry point for the Mothership Cockpit
local integration backend. Implements comprehensive FastAPI setup with
middleware, routers, exception handlers, and lifecycle management.

Usage:
    # Development
    uvicorn application.mothership.main:app --reload --port 8080

    # Production
    gunicorn application.mothership.main:app -w 4 -k uvicorn.workers.UvicornWorker

    # Programmatic
    from application.mothership.main import create_app
    app = create_app()
"""

from __future__ import annotations

import asyncio
import importlib
import logging
import os
import sys
import time
import uuid
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from application.api_docs import setup_api_docs

# Observability & Documentation
from application.monitoring import get_metrics_router, setup_metrics
from application.skills.api import router as skills_router
from application.tracing import setup_fastapi_tracing, setup_tracing

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from infrastructure.parasite_guard import add_parasite_guard

from .config import MothershipSettings, get_settings
from .db.engine import dispose_async_engine, get_async_engine
from .dependencies import get_cockpit_service, get_uow, reset_cockpit_service
from .exceptions import MothershipError
from .middleware.data_corruption import DataCorruptionDetectionMiddleware
from .middleware.stream_monitor import StreamMonitorMiddleware
from .routers import create_api_router
from .routers.agentic import router as agentic_router
from .routers.cockpit import router as cockpit_router
from .routers.corruption_monitoring import router as corruption_router
from .routers.health import router as health_router
from .routers.payment import get_payment_gateway
from .routers.safety import router as safety_router

# Security Infrastructure
from .security.api_sentinels import API_DEFAULTS, apply_defaults
from .services.payment import reconciliation_loop

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
    """Validation error detail."""

    loc: list
    msg: str
    type: str


# =============================================================================
# Exception Handlers
# =============================================================================


async def mothership_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle custom Mothership exceptions."""
    exc = cast(MothershipError, exc)
    logger.error("MothershipError: %s - %s", exc.code, exc.message)

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            error={
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
            request_id=request.headers.get("X-Request-ID"),
            timestamp=datetime.now(UTC).isoformat(),
        ).model_dump(),
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle standard HTTP exceptions."""
    exc = cast(HTTPException, exc)
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            error={
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "details": {},
            },
            request_id=request.headers.get("X-Request-ID"),
            timestamp=datetime.now(UTC).isoformat(),
        ).model_dump(),
    )


async def validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle Pydantic validation errors."""
    exc = cast(RequestValidationError, exc)
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "loc": list(error.get("loc", [])),
                "msg": error.get("msg", "Validation error"),
                "type": error.get("type", "value_error"),
            }
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=ErrorResponse(
            success=False,
            error={
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {"errors": errors},
            },
            request_id=request.headers.get("X-Request-ID"),
            timestamp=datetime.now(UTC).isoformat(),
        ).model_dump(),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.exception("Unexpected error: %s", exc)

    # Don't expose internal errors in production
    settings = get_settings()
    message = str(exc) if settings.is_development else "Internal server error"

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            success=False,
            error={
                "code": "INTERNAL_ERROR",
                "message": message,
                "details": {},
            },
            request_id=request.headers.get("X-Request-ID"),
            timestamp=datetime.now(UTC).isoformat(),
        ).model_dump(),
    )


# =============================================================================
# Payment Helpers
# =============================================================================


def _build_payment_gateway_for_scheduler(settings: MothershipSettings):
    """Build payment gateway for scheduled reconciliation loop."""
    try:
        return get_payment_gateway(settings)
    except HTTPException as exc:
        logger.warning("Payment reconciliation scheduler disabled due to gateway configuration: %s", exc.detail)
        return None


# =============================================================================
# Middleware
# =============================================================================


async def request_id_middleware(request: Request, call_next: Callable) -> Response:
    """Add request ID to all requests."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    # Store in request state for access in handlers
    request.state.request_id = request_id

    response = await call_next(request)

    # Add to response headers
    response.headers["X-Request-ID"] = request_id

    return response


async def timing_middleware(request: Request, call_next: Callable) -> Response:
    """Add request timing information."""
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}"

    return response


async def logging_middleware(request: Request, call_next: Callable) -> Response:
    """Log all requests."""
    start_time = time.time()

    # Log request
    logger.info(
        "Request: %s %s client=%s request_id=%s",
        request.method,
        request.url.path,
        request.client.host if request.client else "unknown",
        getattr(request.state, "request_id", "unknown"),
    )

    response = await call_next(request)

    # Log response
    duration = time.time() - start_time
    logger.info(
        "Response: %s %s status=%s duration=%.3fs", request.method, request.url.path, response.status_code, duration
    )

    return response


# =============================================================================
# Lifespan Management
# =============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan manager.

    Handles startup and shutdown tasks including:
    - Initializing the cockpit service
    - Setting up integrations
    - Graceful shutdown
    """
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment.value}")

    # Ensure safety directory is on sys.path once for all safety imports
    _safety_dir = Path(__file__).parent.parent.parent.parent / "safety"
    if str(_safety_dir) not in sys.path:
        sys.path.insert(0, str(_safety_dir))

    # Harden environment before starting any services
    try:
        from grid.security.startup import (
            get_hardening_level,
            harden_environment,
            should_harden_environment,
        )

        if should_harden_environment():
            level = get_hardening_level()
            base_dir = Path(__file__).parent.parent.parent.parent  # Project root
            report = harden_environment(
                level=level,
                base_dir=base_dir,
                fail_on_critical=not settings.is_development,
            )

            if report.success:
                logger.info(
                    f"Environment hardened (level: {level.value}, "
                    f"cleaned {len(report.sys_path_cleaned)} sys.path entries, "
                    f"{len(report.pythonpath_cleaned)} PYTHONPATH entries)"
                )
                if report.warnings:
                    for warning in report.warnings[:5]:  # Limit warnings
                        logger.warning(f"Environment hardening warning: {warning}")
            else:
                logger.error(f"Environment hardening failed: {report.errors}")
                if report.has_critical_issues and not settings.is_development:
                    raise RuntimeError("Environment hardening failed with critical issues")
        else:
            logger.debug("Environment hardening disabled via GRID_ENABLE_ENV_HARDENING")
    except ImportError as e:
        logger.warning(f"Environment hardening unavailable: {e}")
    except Exception as e:
        if settings.is_development:
            logger.warning(f"Environment hardening error (continuing in dev): {e}")
        else:
            logger.error(f"Environment hardening failed: {e}")
            raise

    # Startup
    try:
        # Enable async task tracking when DEBUG_ASYNC=true (non-invasive)
        if os.getenv("DEBUG_ASYNC", "").lower() == "true":
            try:
                from grid.debug.async_tracker import enable_async_tracking

                enable_async_tracking()
                logger.info("Async task tracking enabled (DEBUG_ASYNC=true)")
            except ImportError as e:
                logger.debug("Async tracking unavailable: %s", e)

        # Initialize database engine explicitly to catch connection errors early
        get_async_engine()
        logger.info("Database engine initialized")

        # Start DB metrics updater
        from .db.metrics_updater import start_metrics_updater

        await start_metrics_updater()
        logger.info("DB metrics updater started")

        # Initialize cockpit service
        cockpit = get_cockpit_service()
        logger.info("Cockpit service initialized")

        # Start payment reconciliation scheduler
        app.state.payment_reconciliation_stop = asyncio.Event()  # type: ignore[reportAttributeAccessIssue]
        app.state.payment_reconciliation_task = None  # type: ignore[reportAttributeAccessIssue]
        if settings.payment.reconciliation_enabled:
            app.state.payment_reconciliation_task = asyncio.create_task(  # type: ignore[reportAttributeAccessIssue]
                reconciliation_loop(
                    settings=settings,
                    uow_factory=get_uow,
                    gateway_factory=_build_payment_gateway_for_scheduler,
                    stop_event=app.state.payment_reconciliation_stop,  # type: ignore[reportAttributeAccessIssue]
                ),
                name="payment_reconciliation_loop",
            )
            logger.info(
                "Payment reconciliation scheduler started interval=%ss lookback=%sh",
                settings.payment.reconciliation_interval_seconds,
                settings.payment.reconciliation_lookback_hours,
            )
        else:
            logger.info("Payment reconciliation scheduler disabled by configuration")

        # Register default components
        if settings.is_development:
            logger.info("Running in development mode")

        # Validate critical settings with environment-aware fail-fast
        try:
            # This will raise exceptions in production for critical issues
            # In development, it returns issues but allows startup
            settings.validate_critical_settings()

            # Log any remaining warnings
            all_issues = settings.validate(fail_fast=False)
            warning_issues = [issue for issue in all_issues if not issue.startswith("CRITICAL")]
            for issue in warning_issues:
                logger.warning(f"Configuration issue: {issue}")

        except Exception as e:
            # In production, critical validation errors raise exceptions
            if settings.is_production:
                error_msg = (
                    f"CRITICAL: Application startup validation failed in production.\n"
                    f"Error: {str(e)}\n\n"
                    f"This is a CRITICAL security issue. "
                    f"Application cannot start until this is resolved.\n\n"
                    f"See documentation for configuration requirements: "
                    f"docs/SECRET_GENERATION_GUIDE.md"
                )
                logger.error(error_msg)
                raise ValueError(error_msg) from e
            else:
                # In non-production, log but allow startup
                logger.error(f"Configuration validation error (allowing startup in non-production): {e}")
                logger.error("This MUST be fixed before production deployment.")

        # Initialize Security Infrastructure
        try:
            # Validate security defaults are properly configured
            if not API_DEFAULTS:
                raise ValueError("Security defaults not initialized")

            logger.info("Security infrastructure initialized")
            logger.info(f"Security baseline: auth_level={API_DEFAULTS.min_auth_level.value}")

        except Exception as e:
            logger.error(f"Security infrastructure initialization failed: {e}")
            if settings.is_production:
                raise RuntimeError("Security infrastructure must initialize in production") from e

        # Initialize Safety Enforcement Infrastructure
        try:
            from safety.audit.db import check_health as check_safety_db
            from safety.audit.db import init_db as init_safety_db
            from safety.workers.worker_utils import check_redis_health, ensure_consumer_group

            # Initialize audit database
            await init_safety_db()
            db_healthy = await check_safety_db()
            if not db_healthy:
                logger.warning("Safety audit database connection failed - will fail closed on requests")
            else:
                logger.info("Safety audit database initialized")

            # Check Redis connectivity
            redis_healthy = await check_redis_health()
            if not redis_healthy:
                logger.warning("Safety Redis connection failed - will fail closed on requests")
            else:
                await ensure_consumer_group()
                logger.info("Safety Redis streams initialized")

            logger.info("Safety enforcement infrastructure initialized")

        except Exception as e:
            logger.error(f"Safety enforcement initialization failed: {e}")
            if settings.is_production:
                raise RuntimeError("Safety enforcement must initialize in production") from e
            logger.warning("Continuing startup in development mode (safety will fail closed)")

        if hasattr(app.state, "parasite_guard"):
            try:
                from infrastructure.event_bus.event_system import get_eventbus
                from infrastructure.parasite_guard.eventbus_integration import wire_parasite_guard_to_eventbus

                # Get singleton event bus (will initialize if needed, but usually configured elsewhere)
                # Note: EventBus usually needs specific config, so we assume defaults or env vars handled it
                event_bus = await get_eventbus()

                # Wire it up
                wire_parasite_guard_to_eventbus(app.state.parasite_guard, event_bus)  # type: ignore[reportAttributeAccessIssue]
                logger.info("ParasiteGuard wired to EventBus for security event emission")
            except Exception as e:
                logger.warning(f"Could not wire ParasiteGuard to EventBus: {e}")

        logger.info("Mothership Cockpit started successfully")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Mothership Cockpit...")

    try:
        # Stop payment reconciliation scheduler
        reconciliation_stop = getattr(app.state, "payment_reconciliation_stop", None)
        reconciliation_task = getattr(app.state, "payment_reconciliation_task", None)
        if reconciliation_stop is not None:
            reconciliation_stop.set()
        if reconciliation_task is not None:
            reconciliation_task.cancel()
            try:
                await reconciliation_task
            except asyncio.CancelledError:
                pass
            logger.info("Payment reconciliation scheduler stopped")

        # Graceful shutdown of cockpit service
        cockpit = get_cockpit_service()
        cockpit.shutdown()
        reset_cockpit_service()
        logger.info("Cockpit service shut down")

        # Stop DB metrics updater
        from .db.metrics_updater import stop_metrics_updater

        await stop_metrics_updater()
        logger.info("DB metrics updater stopped")

        # Dispose database engine
        await dispose_async_engine()

        # Wait for parasite sanitization to complete
        from infrastructure.parasite_guard import wait_for_sanitization

        try:
            await wait_for_sanitization(timeout=30.0)
            logger.info("Parasite sanitization completed before shutdown")
        except Exception as e:
            logger.warning(f"Error waiting for sanitization: {e}")

        # Shutdown DRT middleware
        if hasattr(app.state, "drt_middleware"):
            try:
                await app.state.drt_middleware.shutdown()  # type: ignore[reportAttributeAccessIssue]
                logger.info("DRT middleware shut down")
            except Exception as e:
                logger.warning(f"Error shutting down DRT middleware: {e}")

        # Shutdown CPU executor (ProcessPoolExecutor)
        from .utils.cpu_executor import shutdown_executor

        shutdown_executor()

        # Shutdown safety enforcement infrastructure
        try:
            from safety.api.rate_limiter import close_pool as close_rate_limiter_pool
            from safety.audit.db import close_db as close_safety_db
            from safety.workers.worker_utils import close_redis

            await close_safety_db()
            await close_redis()
            await close_rate_limiter_pool()
            logger.info("Safety enforcement infrastructure shut down")
        except Exception as e:
            logger.warning(f"Error shutting down safety enforcement: {e}")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

    logger.info("Mothership Cockpit stopped")


# =============================================================================
# Application Factory
# =============================================================================


def create_app(settings: MothershipSettings | None = None) -> FastAPI:
    """
    Create and configure the FastAPI application.

    Args:
        settings: Optional settings override (useful for testing)

    Returns:
        Configured FastAPI application instance
    """
    if settings is None:
        settings = get_settings()

    # Create FastAPI app
    app = FastAPI(
        title=settings.app_name,
        description="""
# Mothership Cockpit API

Local integration backend for the Mothership Cockpit system.

## Features

- **Session Management**: Create and manage user sessions
- **Operation Tracking**: Track long-running operations with progress
- **Component Health**: Monitor system component health
- **Alert System**: Create, acknowledge, and resolve alerts
- **Real-time Updates**: WebSocket support for live updates
- **Cloud Integration**: Seamless Gemini Studio integration

## Authentication

The API supports multiple authentication methods:
- API Key (X-API-Key header)
- JWT Bearer Token (Authorization header)

**NO BYPASS PERMITTED** - All requests require authentication.
        """,
        version=settings.app_version,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )

    # =========================================================================
    # Setup Observability & Documentation
    # =========================================================================

    # Setup distributed tracing (only if enabled)
    if settings.telemetry.tracing_enabled:
        setup_tracing(
            service_name="grid-mothership",
            jaeger_host=os.environ.get("JAEGER_HOST", "localhost"),
            jaeger_port=int(os.environ.get("JAEGER_PORT", "4317")),
            environment=settings.environment.value,
        )
        setup_fastapi_tracing(app, service_name="grid-mothership")
        logger.info("Distributed tracing enabled")
    else:
        logger.info("Distributed tracing disabled (set MOTHERSHIP_TRACING_ENABLED=true to enable)")

    # Setup Prometheus metrics
    setup_metrics(app)
    app.include_router(get_metrics_router())

    # Setup API documentation
    setup_api_docs(
        app,
        title="GRID Mothership API",
        version=settings.app_version,
        description="Enterprise AI framework with local-first RAG, event-driven agentic system, and cognitive decision support",
        contact={
            "name": "GRID Support",
            "url": "https://github.com/yourusername/grid",
            "email": "irfankabir02@gmail.com",
        },
        servers=[
            {"url": "http://localhost:8080", "description": "Development server"},
            {"url": "https://api.grid.example.com", "description": "Production server"},
        ],
    )

    # ==========================================================================
    # Register Exception Handlers
    # ==========================================================================

    app.add_exception_handler(MothershipError, mothership_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # ==========================================================================
    # Register Middleware
    # ==========================================================================

    # 1. Standard FastAPI/Starlette middlewares

    # CORS middleware (with secure defaults)
    from .security.cors import get_cors_config

    cors_config = get_cors_config(
        origins=settings.security.cors_origins,
        allow_credentials=settings.security.cors_allow_credentials,
        environment=settings.environment.value,
    )
    app.add_middleware(CORSMiddleware, **cors_config)

    # GZip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # 2. Mothership custom middlewares (Centralized Setup)
    from .middleware import setup_middleware
    from .middleware.accountability_contract import AccountabilityContractMiddleware
    from .middleware.drt_middleware_unified import UnifiedDRTMiddleware, set_unified_drt_middleware
    from .routers.drt_monitoring_unified import router as drt_router

    # This sets up:
    # - ErrorHandlingMiddleware
    # - SecurityHeadersMiddleware (HSTS, CSP, etc.)
    # - RequestLoggingMiddleware
    # - TimingMiddleware
    # - RequestIDMiddleware
    # - UsageTrackingMiddleware
    # - RateLimitMiddleware
    setup_middleware(app, settings)

    # 3. Security Infrastructure
    # Apply factory defaults to all endpoints
    try:
        apply_defaults(app)
        logger.info("Security factory defaults applied")
    except Exception as e:
        logger.error(f"Failed to apply security defaults: {e}")
        # Continue startup but log the security issue

    # 4. Stream Monitoring Middleware
    try:
        app.add_middleware(StreamMonitorMiddleware)
        logger.info("Stream monitoring middleware enabled")
    except ImportError:
        logger.warning(
            "Stream monitoring middleware not available. "
            "Install prometheus_client for metrics: pip install prometheus_client"
        )

    # 5. Data Corruption Detection Middleware
    # Tracks and penalizes endpoints that cause data/environment corruption
    try:
        from grid.resilience.data_corruption_penalty import DataCorruptionPenaltyTracker

        corruption_tracker = DataCorruptionPenaltyTracker()
        app.add_middleware(
            DataCorruptionDetectionMiddleware,
            tracker=corruption_tracker,
            critical_endpoints={
                "/api/v1/data/upload",
                "/api/v1/data/delete",
                "/api/v1/config/update",
                "/api/v1/cockpit/state",
            },
        )
        logger.info("Data corruption detection middleware enabled")
    except ImportError as e:
        logger.warning(f"Data corruption detection middleware not available: {e}")

    # 6. DRT (Don't Repeat Themselves) Monitoring Middleware
    # Monitors endpoint behaviors for attack vector similarities and escalates protections
    try:
        # Create unified middleware instance with settings from SecuritySettings
        # Register DRT middleware via add_middleware (single instance)
        app.add_middleware(
            UnifiedDRTMiddleware,
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
            sampling_rate=1.0,
            escalation_timeout_minutes=60,
            rate_limit_multiplier=0.5,
            alert_on_escalation=True,
        )
        # Store reference for shutdown handling and router access
        # Note: Starlette wraps the middleware, so we retrieve the actual instance
        # from the middleware stack after registration
        drt_middleware = app.middleware_stack  # type: ignore[reportAttributeAccessIssue]
        app.state.drt_middleware = drt_middleware  # type: ignore[reportAttributeAccessIssue]
        set_unified_drt_middleware(drt_middleware)
        logger.info("Unified DRT behavioral monitoring middleware enabled")
    except Exception as e:
        logger.warning(f"DRT monitoring middleware not available: {e}")

    # 6b. Accountability Contract Enforcement Middleware
    # Enforces accountability contracts with RBAC and claims support
    if settings.security.accountability_enabled:
        try:
            app.add_middleware(
                AccountabilityContractMiddleware,
                enforcement_mode=settings.security.accountability_enforcement_mode,
                contract_path=settings.security.accountability_contract_path,
                skip_paths=["/health", "/metrics", "/docs", "/redoc", "/openapi.json"],
            )
            logger.info(
                f"Accountability contract enforcement middleware enabled: mode={settings.security.accountability_enforcement_mode}"
            )
        except Exception as e:
            logger.warning(f"Accountability contract middleware not available: {e}")

    # 7. Safety Enforcement Middleware (MANDATORY)
    # This middleware MUST run before model inference endpoints
    # Enforces: auth → suspension → rate limit → pre-check → enqueue
    try:
        from safety.api.middleware import SafetyMiddleware

        app.add_middleware(SafetyMiddleware)
        logger.info("Safety enforcement middleware enabled (MANDATORY)")
    except Exception as e:
        logger.error(f"Safety enforcement middleware failed to load: {e}")
        if settings.is_production:
            raise RuntimeError("Safety middleware is mandatory in production") from e

    # 8. Parasite Guard (Total Rickall Defense)
    # Phase 3: Enable Sanitization (Production Enabled)
    if settings.security.parasite_guard_enabled:
        # Add parasite guard with appropriate mode based on pruning flag
        mode = "full" if settings.security.parasite_guard_pruning_enabled else "detect"
        middleware = add_parasite_guard(app, mode=mode)
        # Store for wiring in lifespan
        app.state.parasite_guard = middleware  # type: ignore[reportAttributeAccessIssue]
        logger.info("Parasite Guard integrated (mode=%s)", mode)

    # ==========================================================================
    # Prometheus Metrics (Phase 1 Gap Fix)
    # ==========================================================================

    if settings.telemetry.metrics_enabled:
        try:
            from prometheus_fastapi_instrumentator import (
                Instrumentator,  # type: ignore[import-not-found]
            )

            instrumentator = Instrumentator(
                should_group_status_codes=True,
                should_ignore_untemplated=True,
                should_respect_env_var=True,
                should_instrument_requests_inprogress=True,
                excluded_handlers=["/health/*", "/ping", "/metrics"],
                inprogress_name="http_requests_inprogress",
                inprogress_labels=True,
            )
            instrumentator.instrument(app).expose(
                app,
                endpoint=settings.telemetry.metrics_path,
                include_in_schema=False,
            )
            logger.info(f"Prometheus metrics enabled at {settings.telemetry.metrics_path}")
        except ImportError:
            logger.warning(
                "prometheus-fastapi-instrumentator not installed. "
                "Install with: pip install prometheus-fastapi-instrumentator"
            )

    # ==========================================================================
    # Register Routers with Security Defaults
    # ==========================================================================

    # Health check routes (no prefix for k8s compatibility)
    app.include_router(health_router)

    # Main API routes with security defaults applied
    api_router = create_api_router(prefix="/api/v1")

    # Apply security defaults to API router
    try:
        apply_defaults(api_router)
        logger.info("Security defaults applied to API router")
    except Exception as e:
        logger.error(f"Failed to apply security defaults to API router: {e}")

    # Include cockpit router
    api_router.include_router(cockpit_router, prefix="/cockpit", tags=["cockpit"])

    # Include agentic router
    api_router.include_router(agentic_router)

    # Include skills health router
    api_router.include_router(skills_router)

    # Include Grid Pulse router (Radar)
    if os.getenv("MOTHERSHIP_ENABLE_GRID_PULSE") == "1":
        try:
            pulse = importlib.import_module("grid.api.routers.pulse")

            api_router.include_router(pulse.router)
        except ModuleNotFoundError as e:
            logger.warning(
                "Grid Pulse router not loaded due to missing optional dependency: %s",
                str(e),
            )
        except SystemExit as e:
            logger.warning(
                "Grid Pulse router not loaded due to startup restriction: %s",
                str(e),
            )

    app.include_router(corruption_router)
    logger.info("Corruption monitoring API endpoints registered")

    app.include_router(drt_router)
    logger.info("DRT monitoring API endpoints registered")

    # Safety enforcement endpoints (protected by SafetyMiddleware)
    app.include_router(safety_router)
    logger.info("Safety enforcement API endpoints registered")

    app.include_router(api_router)

    # ==========================================================================
    # Root Endpoints
    # ==========================================================================

    @app.get("/", tags=["root"])
    async def root() -> dict[str, Any]:
        """Root endpoint with API information."""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "status": "operational",
            "docs": "/docs" if settings.is_development else None,
            "health": "/health/live",
            "api": "/api/v1",
        }

    @app.get("/ping", tags=["root"])
    async def ping() -> dict[str, str]:
        """Simple ping endpoint for basic connectivity check."""
        return {"ping": "pong"}

    # Security Status Endpoint
    @app.get("/security/status", tags=["security"])
    async def security_status() -> dict[str, Any]:
        """Security status endpoint for operational visibility."""
        settings = get_settings()
        return {
            "security_enabled": True,
            "factory_defaults_applied": bool(API_DEFAULTS),
            "auth_level": API_DEFAULTS.min_auth_level.value,
            "environment": settings.environment.value,
            "cors_enabled": bool(settings.security.cors_origins),
            "rate_limiting": API_DEFAULTS.rate_limit,
            "stream_monitoring": True,
        }

    return app


# =============================================================================
# Application Instance
# =============================================================================

# Create default application instance
app = create_app()


# =============================================================================
# CLI Entry Point
# =============================================================================


def main() -> None:
    """CLI entry point for running the application."""
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        "application.mothership.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.reload,
        workers=1 if settings.server.reload else settings.server.workers,
        log_level=settings.telemetry.log_level.value.lower(),
    )


if __name__ == "__main__":
    main()
