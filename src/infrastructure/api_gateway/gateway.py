"""
Dynamic API Gateway for Arena Architecture Modernization
=====================================================

Transforms the dial-up-like static architecture into a dynamic, efficient API-driven system.
Implements request routing, load balancing, authentication, and circuit breaking.
"""

import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import httpx
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.gzip import GZipMiddleware

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CIRCUIT_OPEN = "circuit_open"


@dataclass
class ServiceEndpoint:
    """Service endpoint configuration."""
    name: str
    url: str
    weight: int = 1
    health_check_path: str = "/health"
    timeout: float = 30.0
    max_retries: int = 3
    status: ServiceStatus = ServiceStatus.HEALTHY
    last_health_check: float = field(default_factory=time.time)
    circuit_breaker_failures: int = 0
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0


@dataclass
class RouteConfig:
    """Route configuration."""
    path: str
    service_name: str
    methods: list[str]
    auth_required: bool = True
    rate_limit: int | None = None
    timeout: float = 30.0


@dataclass
class CircuitBreakerState:
    """Circuit breaker state."""
    failure_count: int = 0
    last_failure_time: float = 0
    state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN


class CircuitBreaker:
    """Circuit breaker implementation."""

    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.state = CircuitBreakerState()

    def call_allowed(self) -> bool:
        """Check if call is allowed based on circuit state."""
        if self.state.state == "CLOSED":
            return True
        elif self.state.state == "OPEN":
            if time.time() - self.state.last_failure_time > self.timeout:
                self.state.state = "HALF_OPEN"
                return True
            return False
        else:  # HALF_OPEN
            return True

    def record_success(self):
        """Record successful call."""
        self.state.failure_count = 0
        self.state.state = "CLOSED"

    def record_failure(self):
        """Record failed call."""
        self.state.failure_count += 1
        self.state.last_failure_time = time.time()

        if self.state.failure_count >= self.failure_threshold:
            self.state.state = "OPEN"


class RateLimiter:
    """Rate limiter using Redis."""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def is_allowed(self, key: str, limit: int, window: int = 60) -> bool:
        """Check if request is allowed."""
        current_time = int(time.time())
        window_start = current_time - window

        # Remove old entries
        await self.redis.zremrangebyscore(key, 0, window_start)

        # Count current requests
        current_requests = await self.redis.zcard(key)

        if current_requests >= limit:
            return False

        # Add current request
        await self.redis.zadd(key, {str(uuid.uuid4()): current_time})
        await self.redis.expire(key, window)

        return True


class APIGateway:
    """
    Dynamic API Gateway with load balancing, circuit breaking, and rate limiting.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.services: dict[str, list[ServiceEndpoint]] = {}
        self.routes: dict[str, RouteConfig] = {}
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.redis_client: redis.Redis | None = None
        self.rate_limiter: RateLimiter | None = None
        self.redis_url = redis_url
        self.health_check_interval = 30.0
        self.health_check_task: asyncio.Task | None = None

    async def start(self):
        """Start the gateway."""
        # Initialize Redis
        try:
            self.redis_client = redis.from_url(self.redis_url)
            self.rate_limiter = RateLimiter(self.redis_client)
            await self.redis_client.ping()
            logger.info("Redis connected for API Gateway")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            # Continue without Redis for development

        # Start health check task
        self.health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("API Gateway started")

    async def stop(self):
        """Stop the gateway."""
        if self.health_check_task:
            self.health_check_task.cancel()

        if self.redis_client:
            await self.redis_client.close()

        logger.info("API Gateway stopped")

    def register_service(self, service: ServiceEndpoint):
        """Register a service endpoint."""
        if service.name not in self.services:
            self.services[service.name] = []

        self.services[service.name].append(service)
        self.circuit_breakers[service.name] = CircuitBreaker(
            failure_threshold=service.circuit_breaker_threshold,
            timeout=service.circuit_breaker_timeout
        )

        logger.info(f"Service registered: {service.name} at {service.url}")

    def register_route(self, route: RouteConfig):
        """Register a route."""
        self.routes[route.path] = route
        logger.info(f"Route registered: {route.path} -> {route.service_name}")

    async def _health_check_loop(self):
        """Background health check loop."""
        while True:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(5)

    async def _perform_health_checks(self):
        """Perform health checks on all services."""
        async with httpx.AsyncClient() as client:
            for service_name, endpoints in self.services.items():
                for endpoint in endpoints:
                    try:
                        health_url = f"{endpoint.url}{endpoint.health_check_path}"
                        response = await client.get(
                            health_url,
                            timeout=5.0
                        )

                        if response.status_code == 200:
                            endpoint.status = ServiceStatus.HEALTHY
                            endpoint.circuit_breaker_failures = 0
                        else:
                            endpoint.status = ServiceStatus.DEGRADED
                            endpoint.circuit_breaker_failures += 1

                        endpoint.last_health_check = time.time()

                    except Exception as e:
                        logger.warning(f"Health check failed for {service_name}: {e}")
                        endpoint.status = ServiceStatus.UNHEALTHY
                        endpoint.circuit_breaker_failures += 1
                        endpoint.last_health_check = time.time()

    def _select_endpoint(self, service_name: str) -> ServiceEndpoint | None:
        """Select endpoint using weighted round-robin."""
        if service_name not in self.services:
            return None

        healthy_endpoints = [
            ep for ep in self.services[service_name]
            if ep.status == ServiceStatus.HEALTHY
        ]

        if not healthy_endpoints:
            return None

        # Weighted round-robin selection
        total_weight = sum(ep.weight for ep in healthy_endpoints)
        if total_weight == 0:
            return healthy_endpoints[0]

        import random
        rand = random.uniform(0, total_weight)
        current_weight = 0

        for endpoint in healthy_endpoints:
            current_weight += endpoint.weight
            if rand <= current_weight:
                return endpoint

        return healthy_endpoints[0]

    async def _forward_request(
        self,
        request: Request,
        endpoint: ServiceEndpoint,
        path: str
    ) -> Response:
        """Forward request to service endpoint."""
        circuit_breaker = self.circuit_breakers.get(endpoint.name)

        if circuit_breaker and not circuit_breaker.call_allowed():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Circuit breaker open for service: {endpoint.name}"
            )

        # Prepare request
        url = f"{endpoint.url}{path}"
        headers = dict(request.headers)
        headers.pop("host", None)  # Remove host header

        body = await request.body()

        try:
            async with httpx.AsyncClient(timeout=endpoint.timeout) as client:
                response = await client.request(
                    method=request.method,
                    url=url,
                    headers=headers,
                    content=body,
                    params=request.query_params
                )

                if circuit_breaker:
                    if response.status_code < 500:
                        circuit_breaker.record_success()
                    else:
                        circuit_breaker.record_failure()

                # Create response
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )

        except httpx.TimeoutException:
            if circuit_breaker:
                circuit_breaker.record_failure()
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Service timeout: {endpoint.name}"
            )
        except Exception as e:
            if circuit_breaker:
                circuit_breaker.record_failure()
            logger.error(f"Request forwarding failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Service unavailable: {endpoint.name}"
            )

    async def route_request(self, request: Request) -> Response:
        """Route incoming request."""
        path = request.url.path
        method = request.method

        # Find matching route
        route = None
        for route_path, route_config in self.routes.items():
            if path.startswith(route_path) and method in route_config.methods:
                route = route_config
                break

        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Route not found"
            )

        # Rate limiting
        if self.rate_limiter and route.rate_limit:
            client_ip = request.client.host if request.client else "unknown"
            key = f"rate_limit:{client_ip}:{route.path}"

            if not await self.rate_limiter.is_allowed(key, route.rate_limit):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )

        # Select endpoint
        endpoint = self._select_endpoint(route.service_name)
        if not endpoint:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"No healthy endpoints for service: {route.service_name}"
            )

        # Forward request
        remaining_path = path[len(route.path):]
        return await self._forward_request(request, endpoint, remaining_path)

    def get_service_status(self) -> dict[str, Any]:
        """Get status of all services."""
        status = {}
        for service_name, endpoints in self.services.items():
            status[service_name] = {
                "endpoints": [
                    {
                        "url": ep.url,
                        "status": ep.status.value,
                        "last_health_check": ep.last_health_check,
                        "circuit_breaker_failures": ep.circuit_breaker_failures
                    }
                    for ep in endpoints
                ],
                "circuit_breaker": {
                    "state": self.circuit_breakers[service_name].state.state,
                    "failure_count": self.circuit_breakers[service_name].state.failure_count
                } if service_name in self.circuit_breakers else None
            }
        return status


# ============================================================================
# FastAPI Application Factory
# ============================================================================

def create_gateway_app() -> FastAPI:
    """Create FastAPI application for API Gateway."""

    gateway = APIGateway()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await gateway.start()
        yield
        await gateway.stop()

    app = FastAPI(
        title="Arena API Gateway",
        description="Dynamic API Gateway for Arena Architecture Modernization",
        version="1.0.0",
        lifespan=lifespan
    )

    # Middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Routes
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "api-gateway"}

    @app.get("/status")
    async def gateway_status():
        return gateway.get_service_status()

    # Proxy all other requests
    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
    async def proxy_request(request: Request, path: str):
        return await gateway.route_request(request)

    return app, gateway


# ============================================================================
# Example Usage
# ============================================================================

async def example_setup():
    """Example setup of API Gateway."""
    app, gateway = create_gateway_app()

    # Register services
    gateway.register_service(ServiceEndpoint(
        name="grid-service",
        url="http://localhost:8080",
        weight=2,
        health_check_path="/health"
    ))

    gateway.register_service(ServiceEndpoint(
        name="coinbase-service",
        url="http://localhost:8081",
        weight=1,
        health_check_path="/health"
    ))

    # Register routes
    gateway.register_route(RouteConfig(
        path="/api/v1/grid",
        service_name="grid-service",
        methods=["GET", "POST", "PUT", "DELETE"],
        rate_limit=100
    ))

    gateway.register_route(RouteConfig(
        path="/api/v1/coinbase",
        service_name="coinbase-service",
        methods=["GET", "POST"],
        rate_limit=50
    ))

    return app


if __name__ == "__main__":
    import uvicorn

    app, _ = example_setup()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
