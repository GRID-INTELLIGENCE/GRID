"""
Dynamic Router for Arena API Gateway
====================================

This module implements dynamic routing capabilities that transform the
static dial-up-like system into a flexible, service-aware routing layer.

Key Features:
- Dynamic service discovery integration
- Load balancing across service instances
- Request transformation and routing
- Circuit breaking for resilient routing
- Health-aware routing decisions
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Awaitable, Callable, Optional

import httpx

logger = logging.getLogger(__name__)


class DynamicRouter:
    """
    Dynamic router that provides intelligent routing decisions based on
    service health, load, and AI-driven optimization.
    """

    def __init__(self):
        self.service_discovery = None  # Will be injected
        self.client = httpx.AsyncClient(timeout=30.0)
        self.circuit_breaker = CircuitBreaker(client=self.client)
        self.load_balancer = LoadBalancer()
        self.request_transformer = RequestTransformer()
        self.route_cache = {}
        self.cache_ttl = 300  # 5 minutes

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    def set_service_discovery(self, service_discovery):
        """Inject service discovery dependency."""
        self.service_discovery = service_discovery

    async def route_request(self, request: Any, path: str) -> Response:
        """
        Route an incoming request to the appropriate service.

        Args:
            request: FastAPI Request object
            path: Request path

        Returns:
            Response from the routed service
        """
        from fastapi.responses import JSONResponse
        from application.mothership.api.versioning import get_version_metadata

        try:
            # 1. Determine target service
            service_name, service_path = self._parse_service_path(path)

            # 2. Get healthy service instances
            service_instances = await self._get_service_instances(service_name)
            if not service_instances:
                return JSONResponse(
                    status_code=503,
                    content={"error": "Service unavailable", "service": service_name}
                )

            # 3. Select service instance (load balancing)
            target_instance = self.load_balancer.select_instance(service_instances)

            # 4. Transform request if needed
            transformed_request = await self.request_transformer.transform(request, service_name, service_path)

            # 5. Route to service with circuit breaker
            response_data = await self.circuit_breaker.call_service(target_instance, transformed_request)

            # Create final response
            status_code = response_data.get("status_code", 200)
            response = JSONResponse(
                status_code=status_code,
                content=response_data.get("data"),
                headers=response_data.get("headers")
            )

            # Inject versioning headers based on path
            version_str = "v1"
            if path.startswith("api/v2") or "/api/v2" in path:
                version_str = "v2"
            
            version_meta = get_version_metadata(version_str)
            if version_meta:
                version_meta.inject_headers(response)

            return response

        except Exception as e:
            logger.error(f"Routing error for path {path}: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal routing error", "details": str(e)}
            )

    def _parse_service_path(self, path: str) -> tuple[str, str]:
        """
        Parse the request path to determine service name and path.

        Expected format: /service-name/api/v1/endpoint
        """
        parts = path.strip("/").split("/")
        if len(parts) < 2:
            return "default", path

        service_name = parts[0]
        service_path = "/" + "/".join(parts[1:])
        return service_name, service_path

    async def _get_service_instances(self, service_name: str) -> list[dict[str, Any]]:
        """Get healthy instances of a service."""
        if not self.service_discovery:
            logger.warning("Service discovery not available")
            return []

        try:
            instances = await self.service_discovery.get_service_instances(service_name)
            # Filter for healthy instances
            healthy_instances = [
                instance for instance in instances if instance.get("health", {}).get("status") == "healthy"
            ]
            return healthy_instances
        except Exception as e:
            logger.error(f"Error getting service instances for {service_name}: {str(e)}")
            return []


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for resilient service calls.
    """

    def __init__(self, client: httpx.AsyncClient, failure_threshold: int = 5, timeout: float = 30.0):
        self.client = client
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_counts = {}
        self.last_failure_time = {}
        self.state = {}  # closed, open, half_open

    async def call_service(self, instance: dict[str, Any], request_data: dict[str, Any]) -> dict[str, Any]:
        """
        Call a service instance with circuit breaker protection.
        """
        instance_id = instance["id"]
        state = self.state.get(instance_id, "closed")

        if state == "open":
            # Check if we should transition to half-open
            if self._should_attempt_reset(instance_id):
                state = "half_open"
                self.state[instance_id] = state
            else:
                raise Exception("Circuit breaker is open")

        try:
            # Make the actual service call
            response = await self._make_http_call(instance, request_data)

            # Success - reset failure count and close circuit
            self.failure_counts[instance_id] = 0
            self.state[instance_id] = "closed"

            return response

        except Exception as e:
            # Failure - increment count and potentially open circuit
            self._record_failure(instance_id)
            if self.failure_counts.get(instance_id, 0) >= self.failure_threshold:
                self.state[instance_id] = "open"
                self.last_failure_time[instance_id] = datetime.now(timezone.utc)

            raise e

    def _should_attempt_reset(self, instance_id: str) -> bool:
        """Check if enough time has passed to attempt resetting the circuit."""
        last_failure = self.last_failure_time.get(instance_id)
        if not last_failure:
            return True

        return (datetime.now(timezone.utc) - last_failure) > timedelta(seconds=self.timeout)

    def _record_failure(self, instance_id: str):
        """Record a service call failure."""
        self.failure_counts[instance_id] = self.failure_counts.get(instance_id, 0) + 1

    async def _make_http_call(self, instance: dict[str, Any], request_data: dict[str, Any]) -> dict[str, Any]:
        """
        Make actual HTTP call to service instance using httpx.
        """
        instance_url = instance["url"]
        path = request_data["path"]
        url = f"{instance_url.rstrip('/')}/{path.lstrip('/')}"

        logger.info(f"Routing {request_data['method']} request to {url}")

        try:
            async with asyncio.timeout(self.timeout):
                response = await self.client.request(
                    method=request_data["method"],
                    url=url,
                    headers=request_data["headers"],
                    params=request_data["query_params"],
                    content=request_data.get("content"),
                )

                # Return structured response
                return {
                    "status": "success" if response.status_code < 400 else "error",
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "data": response.json() if "application/json" in response.headers.get("content-type", "") else response.text,
                }
        except asyncio.TimeoutError:
            logger.error(f"Timeout calling service {url}")
            raise Exception(f"Service call timed out: {url}")
        except httpx.RequestError as e:
            logger.error(f"HTTP request error calling {url}: {str(e)}")
            raise Exception(f"Failed to connect to service: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error calling service {url}: {str(e)}")
            raise


class LoadBalancer:
    """
    Load balancer for distributing requests across service instances.
    """

    def __init__(self):
        self.current_index = {}

    def select_instance(self, instances: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Select a service instance using round-robin algorithm.
        """
        if not instances:
            raise Exception("No service instances available")

        # Simple round-robin selection
        service_name = instances[0].get("service_name", "default")
        current_idx = self.current_index.get(service_name, 0)

        selected_instance = instances[current_idx % len(instances)]
        self.current_index[service_name] = (current_idx + 1) % len(instances)

        return selected_instance


class RequestTransformer:
    """
    Transform requests before routing to services.
    """

    async def transform(self, request, service_name: str, service_path: str) -> dict[str, Any]:
        """
        Transform the request for the target service.
        """
        # Basic transformation - can be extended for specific service requirements
        try:
            body = await request.body()
        except Exception:
            body = None

        transformed = {
            "method": request.method,
            "path": service_path,
            "headers": dict(request.headers),
            "query_params": dict(request.query_params),
            "service_name": service_name,
            "content": body,
        }

        # Add service-specific transformations
        if service_name == "ai_service":
            transformed["headers"]["X-AI-Safety"] = "enabled"
        elif service_name == "data_service":
            transformed["headers"]["X-Data-Compliance"] = "checked"

        return transformed
