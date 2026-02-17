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
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


class DynamicRouter:
    """
    Dynamic router that provides intelligent routing decisions based on
    service health, load, and AI-driven optimization.
    """

    def __init__(self):
        self.service_discovery = None  # Will be injected
        self.circuit_breaker = CircuitBreaker()
        self.load_balancer = LoadBalancer()
        self.request_transformer = RequestTransformer()
        self.route_cache = {}
        self.cache_ttl = 300  # 5 minutes

    def set_service_discovery(self, service_discovery):
        """Inject service discovery dependency."""
        self.service_discovery = service_discovery

    async def route_request(self, request, path: str) -> dict[str, Any]:
        """
        Route an incoming request to the appropriate service.

        Args:
            request: FastAPI Request object
            path: Request path

        Returns:
            Response data from the routed service
        """
        try:
            # 1. Determine target service
            service_name, service_path = self._parse_service_path(path)

            # 2. Get healthy service instances
            service_instances = await self._get_service_instances(service_name)
            if not service_instances:
                return {"error": "Service unavailable", "service": service_name, "status_code": 503}

            # 3. Select service instance (load balancing)
            target_instance = self.load_balancer.select_instance(service_instances)

            # 4. Transform request if needed
            transformed_request = await self.request_transformer.transform(request, service_name, service_path)

            # 5. Route to service with circuit breaker
            response = await self.circuit_breaker.call_service(target_instance, transformed_request)

            return response

        except Exception as e:
            logger.error(f"Routing error for path {path}: {str(e)}")
            return {"error": "Internal routing error", "details": str(e), "status_code": 500}

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

    def __init__(self, failure_threshold: int = 5, timeout: float = 30.0):
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
                self.last_failure_time[instance_id] = datetime.utcnow()

            raise e

    def _should_attempt_reset(self, instance_id: str) -> bool:
        """Check if enough time has passed to attempt resetting the circuit."""
        last_failure = self.last_failure_time.get(instance_id)
        if not last_failure:
            return True

        return (datetime.utcnow() - last_failure) > timedelta(seconds=self.timeout)

    def _record_failure(self, instance_id: str):
        """Record a service call failure."""
        self.failure_counts[instance_id] = self.failure_counts.get(instance_id, 0) + 1

    async def _make_http_call(self, instance: dict[str, Any], request_data: dict[str, Any]) -> dict[str, Any]:
        """
        Make HTTP call to service instance.
        This is a placeholder - actual implementation would use aiohttp or similar.
        """
        # Placeholder implementation
        instance_url = instance["url"]
        logger.info(f"Making call to {instance_url}")

        # Simulate service call - replace with actual HTTP client
        await asyncio.sleep(0.1)  # Simulate network latency

        return {"status": "success", "data": {"message": f"Response from {instance_url}"}, "status_code": 200}


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
        transformed = {
            "method": request.method,
            "path": service_path,
            "headers": dict(request.headers),
            "query_params": dict(request.query_params),
            "service_name": service_name,
        }

        # Add service-specific transformations
        if service_name == "ai_service":
            transformed["headers"]["X-AI-Safety"] = "enabled"
        elif service_name == "data_service":
            transformed["headers"]["X-Data-Compliance"] = "checked"

        return transformed
