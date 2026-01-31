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

from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import os

# Import our custom modules
from .routing.router import DynamicRouter
from .authentication.auth import AuthManager
from .rate_limiting.limiter import RateLimiter
from .service_discovery.discovery import ServiceDiscovery
from .monitoring.monitor import MonitoringManager
from .ai_safety.safety import AISafetyManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ArenaAPIGateway:
    """
    Main API Gateway class for the Arena architecture.

    This class orchestrates all components of the dynamic API system,
    providing a unified interface for routing, authentication, rate limiting,
    and service management.
    """

    def __init__(self):
        self.app = FastAPI(
            title="Arena API Gateway",
            description="Dynamic API infrastructure for Arena architecture",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )

        # Initialize core components
        self.router = DynamicRouter()
        self.auth_manager = AuthManager()
        self.rate_limiter = RateLimiter()
        self.service_discovery = ServiceDiscovery()
        self.monitoring = MonitoringManager()
        self.ai_safety = AISafetyManager()

        # Setup middleware
        self._setup_middleware()

        # Setup routes
        self._setup_routes()

        # Start background tasks
        self._start_background_tasks()

        logger.info("Arena API Gateway initialized successfully")

    def _setup_middleware(self):
        """Setup all middleware components."""

        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Trusted host middleware
        self.app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]  # Configure appropriately for production
        )

        # Custom middleware for request processing
        self.app.add_middleware(RequestProcessingMiddleware,
                              router=self.router,
                              auth_manager=self.auth_manager,
                              rate_limiter=self.rate_limiter,
                              monitoring=self.monitoring,
                              ai_safety=self.ai_safety)

    def _setup_routes(self):
        """Setup API routes."""

        # Health check endpoint
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0"
            }

        # Service discovery endpoints
        @self.app.get("/services")
        async def list_services():
            """List all registered services."""
            services = await self.service_discovery.get_services()
            return {"services": services}

        @self.app.post("/services/register")
        async def register_service(service_data: Dict[str, Any]):
            """Register a new service."""
            result = await self.service_discovery.register_service(service_data)
            return {"result": result}

        # Dynamic routing - catch-all for API calls
        @self.app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
        async def dynamic_route(request: Request, path: str):
            """Handle dynamic routing for all API calls."""
            return await self.router.route_request(request, path)

    def _start_background_tasks(self):
        """Start background tasks for monitoring and maintenance."""

        @self.app.on_event("startup")
        async def startup_event():
            """Initialize background tasks on startup."""
            # Start service discovery heartbeat
            asyncio.create_task(self.service_discovery.heartbeat())

            # Start monitoring collection
            asyncio.create_task(self.monitoring.collect_metrics())

            # Start AI safety monitoring
            asyncio.create_task(self.ai_safety.monitor_safety())

            logger.info("Background tasks started")

        @self.app.on_event("shutdown")
        async def shutdown_event():
            """Cleanup on shutdown."""
            await self.service_discovery.cleanup()
            await self.monitoring.cleanup()
            logger.info("Arena API Gateway shutdown complete")

class RequestProcessingMiddleware(BaseHTTPMiddleware):
    """
    Custom middleware for processing requests through the Arena pipeline.
    """

    def __init__(self, app, router, auth_manager, rate_limiter, monitoring, ai_safety):
        super().__init__(app)
        self.router = router
        self.auth_manager = auth_manager
        self.rate_limiter = rate_limiter
        self.monitoring = monitoring
        self.ai_safety = ai_safety

    async def dispatch(self, request: Request, call_next):
        """Process each request through the Arena pipeline."""

        start_time = time.time()

        try:
            # 1. Rate limiting check
            rate_limit_result = await self.rate_limiter.check_rate_limit(request)
            if not rate_limit_result["allowed"]:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded"
                )

            # 2. Authentication check
            auth_result = await self.auth_manager.authenticate(request)
            if not auth_result["authenticated"]:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )

            # 3. AI Safety check
            safety_result = await self.ai_safety.check_request(request)
            if not safety_result["safe"]:
                raise HTTPException(
                    status_code=403,
                    detail="Request flagged by AI safety system"
                )

            # 4. Process the request
            response = await call_next(request)

            # 5. Record metrics
            processing_time = time.time() - start_time
            await self.monitoring.record_request(
                request=request,
                response=response,
                processing_time=processing_time,
                authenticated=auth_result["authenticated"]
            )

            return response

        except Exception as e:
            # Record error metrics
            processing_time = time.time() - start_time
            await self.monitoring.record_error(
                request=request,
                error=str(e),
                processing_time=processing_time
            )
            raise

# Global gateway instance
gateway = ArenaAPIGateway()

# Export the FastAPI app for uvicorn
app = gateway.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("ARENA_API_PORT", "8000")),
        reload=True
    )
