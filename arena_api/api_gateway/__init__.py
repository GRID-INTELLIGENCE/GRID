"""
Arena API Gateway - Dynamic API Infrastructure
===========================================

This module implements the API Gateway for the Arena architecture,
providing dynamic routing, authentication, rate limiting, and service
discovery capabilities to transform the dial-up-like system into
a modern, scalable API infrastructure.

Key Features:
- Dynamic service discovery and routing
- Authentication and authorization
- Rate limiting and throttling
- Request/response transformation
- Circuit breaking and health checks
- AI safety compliance
"""

import asyncio
import json
import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta, timezone
from typing import Any, AsyncIterator

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware

from .ai_safety.safety import AISafetyManager
from .authentication.auth import AuthManager
from .monitoring.monitor import MonitoringManager
from .rate_limiting.limiter import RateLimiter

# Import our custom modules
from .routing.router import DynamicRouter
from .service_discovery.discovery import ServiceDiscovery

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class ArenaAPIGateway:
    """
    Main API Gateway class for the Arena architecture.

    This class orchestrates all components of the dynamic API system,
    providing a unified interface for routing, authentication, rate limiting,
    and service management.
    """

    def __init__(self) -> None:
        self.app: FastAPI = FastAPI(
            title="Arena API Gateway",
            description="Dynamic API infrastructure for Arena architecture",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
            lifespan=self.lifespan,
        )

        # Initialize core components
        self.router: DynamicRouter = DynamicRouter()
        self.auth_manager: AuthManager = AuthManager()
        self.rate_limiter: RateLimiter = RateLimiter()
        self.service_discovery: ServiceDiscovery = ServiceDiscovery()
        self.monitoring: MonitoringManager = MonitoringManager()
        self.ai_safety: AISafetyManager = AISafetyManager()

        # Setup middleware
        self._setup_middleware()

        # Setup routes
        self._setup_routes()

        # Start background tasks
        self._start_background_tasks()

        logger.info("Arena API Gateway initialized successfully")

    def _setup_middleware(self) -> None:
        """Setup all middleware components."""

        # CORS middleware
        allowed_origins = os.getenv("ARENA_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Trusted host middleware
        allowed_hosts = os.getenv("ARENA_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
        self.app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=allowed_hosts,
        )

        # Custom middleware for request processing
        self.app.add_middleware(
            RequestProcessingMiddleware,
            router=self.router,
            auth_manager=self.auth_manager,
            rate_limiter=self.rate_limiter,
            monitoring=self.monitoring,
            ai_safety=self.ai_safety,
        )

    @asynccontextmanager
    async def lifespan(self, app: FastAPI) -> AsyncIterator[None]:
        """Lifespan manager for the API Gateway."""
        logger.info("Starting Arena API Gateway background tasks...")

        # 1. Start background tasks
        heartbeat_task = asyncio.create_task(self.service_discovery.heartbeat())
        metrics_task = asyncio.create_task(self.monitoring.collect_metrics())
        safety_task = asyncio.create_task(self.ai_safety.monitor_safety())

        # 2. Register services from configuration
        await self._register_configured_services()

        logger.info("Background tasks started")

        yield

        # 3. Cleanup on shutdown
        logger.info("Shutting down Arena API Gateway...")
        heartbeat_task.cancel()
        metrics_task.cancel()
        safety_task.cancel()

        await asyncio.gather(
            self.service_discovery.cleanup(),
            self.monitoring.cleanup(),
            return_exceptions=True
        )
        logger.info("Arena API Gateway shutdown complete")

    async def _register_configured_services(self) -> None:
        """Register services from environment or configuration file."""
        # In a real app, this would come from a config file or environment variable
        # For now, we externalize the logic from the startup event
        default_services = [
            {
                "service_name": "arena_service",
                "url": os.getenv("ARENA_SERVICE_URL", "http://localhost:8002"),
                "health_url": os.getenv("ARENA_SERVICE_HEALTH_URL", "http://localhost:8002/health"),
                "metadata": {"version": "1.0.0", "capabilities": ["cache", "rewards", "adsr", "honor_decay"]},
            },
            {
                "service_name": "ai_service",
                "url": os.getenv("AI_SERVICE_URL", "http://localhost:8001"),
                "health_url": os.getenv("AI_SERVICE_HEALTH_URL", "http://localhost:8001/health"),
                "metadata": {"version": "1.0.0", "capabilities": ["text_generation", "safety_checks"]},
            },
            {
                "service_name": "discussion_service",
                "url": os.getenv("DISCUSSION_SERVICE_URL", "http://localhost:8003"),
                "health_url": os.getenv("DISCUSSION_SERVICE_HEALTH_URL", "http://localhost:8003/health"),
                "metadata": {
                    "version": "1.0.0",
                    "capabilities": ["current_events", "topic_extraction", "recursive_reasoning", "wall_board"],
                },
            },
        ]

        for service_data in default_services:
            await self.service_discovery.register_service(service_data)
            logger.info(f"Registered service: {service_data['service_name']} at {service_data['url']}")

    def _setup_routes(self) -> None:
        """Setup API routes."""

        # Health check endpoint
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "timestamp": datetime.now(UTC).isoformat(), "version": "1.0.0"}

        # Service discovery endpoints
        @self.app.get("/services")
        async def list_services():
            """List all registered services."""
            services = await self.service_discovery.get_services()
            return {"services": services}

        @self.app.post("/services/register")
        async def register_service(service_data: dict[str, Any]):
            """Register a new service."""
            result = await self.service_discovery.register_service(service_data)
            return {"result": result}

        # Dynamic routing - catch-all for API calls
        @self.app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
        async def dynamic_route(request: Request, path: str):
            """Handle dynamic routing for all API calls."""
            return await self.router.route_request(request, path)

    def _start_background_tasks(self) -> None:
        """No-op as tasks are now handled in lifespan."""
        pass


class RequestProcessingMiddleware(BaseHTTPMiddleware):
    """
    Custom middleware for processing requests through the Arena pipeline.
    """

    def __init__(
        self,
        app: Any,
        router: DynamicRouter,
        auth_manager: AuthManager,
        rate_limiter: RateLimiter,
        monitoring: MonitoringManager,
        ai_safety: AISafetyManager,
    ) -> None:
        super().__init__(app)
        self.router = router
        self.auth_manager = auth_manager
        self.rate_limiter = rate_limiter
        self.monitoring = monitoring
        self.ai_safety = ai_safety

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Process each request through the Arena pipeline."""

        start_time = time.time()

        try:
            # 1. Rate limiting check
            rate_limit_result = await self.rate_limiter.check_rate_limit(request)
            if not rate_limit_result["allowed"]:
                raise HTTPException(status_code=429, detail="Rate limit exceeded")

            # 2. Authentication check
            auth_result = await self.auth_manager.authenticate(request)
            if not auth_result["authenticated"]:
                raise HTTPException(status_code=401, detail="Authentication required")

            # 3. AI Safety check
            safety_result = await self.ai_safety.check_request(request)
            if not safety_result["safe"]:
                raise HTTPException(status_code=403, detail="Request flagged by AI safety system")

            # 4. Process the request with circuit breaker fallback
            try:
                response = await call_next(request)
                # Record success metrics
                processing_time = time.time() - start_time
                await self.monitoring.record_request(
                    request=request,
                    response=response,
                    processing_time=processing_time,
                    authenticated=auth_result["authenticated"],
                )
                return response
            except Exception as e:
                # Check if it was a circuit breaker open exception
                if "Circuit breaker is open" in str(e):
                    logger.warning(f"Circuit breaker open for {request.url.path}, using fallback")
                    return await self._get_fallback_response(request)
                
                # Record error metrics
                processing_time = time.time() - start_time
                await self.monitoring.record_error(request=request, error=str(e), processing_time=processing_time)
                raise

        except Exception as e:
            # Record error metrics
            processing_time = time.time() - start_time
            await self.monitoring.record_error(request=request, error=str(e), processing_time=processing_time)
            raise

    async def _get_fallback_response(self, request: Request) -> Response:
        """Provide a fallback response when services are unavailable."""
        from fastapi.responses import JSONResponse
        
        # Determine service name from path
        path_parts = request.url.path.strip("/").split("/")
        service_name = path_parts[0] if path_parts else "unknown"
        
        # Generic fallback data
        fallback_data = {
            "error": "Service temporarily unavailable",
            "service": service_name,
            "status": "degraded_mode",
            "message": "We are experiencing technical difficulties. Please try again later.",
            "timestamp": datetime.now(UTC).isoformat()
        }
        
        # Service-specific fallbacks could be added here
        if service_name == "ai_service":
            fallback_data["message"] = "AI features are temporarily unavailable. Static processing active."
        
        return JSONResponse(
            status_code=503,
            content=fallback_data,
            headers={"X-Gateway-Fallback": "true"}
        )


# Global gateway instance
gateway = ArenaAPIGateway()

# Export the FastAPI app for uvicorn
app = gateway.app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("ARENA_API_PORT", "8000")), reload=True)
