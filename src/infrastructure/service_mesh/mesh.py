"""
Service Mesh Implementation for Arena Architecture
================================================

Provides service discovery, load balancing, circuit breaking, and inter-service communication.
Transforms static components into a dynamic, interconnected service mesh.
"""

import asyncio
import json
import logging
import time
import uuid
from collections import defaultdict
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any

from aiohttp import ClientSession, ClientTimeout, web  # type: ignore[import-not-found]


class ServiceType(StrEnum):
    """Service types in the mesh."""

    API_GATEWAY = "api_gateway"
    CORE_SERVICE = "core_service"
    AI_SERVICE = "ai_service"
    DATA_SERVICE = "data_service"
    WEBHOOK_SERVICE = "webhook_service"
    MONITORING_SERVICE = "monitoring_service"


class ServiceState(StrEnum):
    """Service states."""

    STARTING = "starting"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DRAINING = "draining"
    TERMINATED = "terminated"


@dataclass
class ServiceInstance:
    """Service instance metadata."""

    id: str
    name: str
    type: ServiceType
    host: str
    port: int
    version: str
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    state: ServiceState = ServiceState.STARTING
    registered_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)
    health_check_url: str | None = None
    endpoints: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["type"] = self.type.value
        data["state"] = self.state.value
        data["tags"] = list(self.tags)
        return data


@dataclass
class ServiceRegistration:
    """Service registration request."""

    name: str
    type: ServiceType
    host: str
    port: int
    version: str
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    health_check_url: str | None = None
    endpoints: list[str] = field(default_factory=list)


class ServiceRegistry:
    """Service registry for service discovery."""

    def __init__(self):
        self.services: dict[str, list[ServiceInstance]] = defaultdict(list)
        self.service_index: dict[str, ServiceInstance] = {}
        self.subscriptions: dict[str, list[Callable]] = defaultdict(list)
        self.config_file = "service_registry.json"
        self._lock = asyncio.Lock()

    async def register(self, registration: ServiceRegistration) -> ServiceInstance:
        """Register a new service instance."""
        async with self._lock:
            instance = ServiceInstance(
                id=str(uuid.uuid4()),
                name=registration.name,
                type=registration.type,
                host=registration.host,
                port=registration.port,
                version=registration.version,
                metadata=registration.metadata,
                tags=registration.tags,
                health_check_url=registration.health_check_url,
                endpoints=registration.endpoints,
            )

            self.services[registration.name].append(instance)
            self.service_index[instance.id] = instance

            # Notify subscribers
            await self._notify_subscribers("service_registered", instance)

            # Save to disk
            await self._save_registry()

            logging.info(f"Service registered: {registration.name} ({instance.id})")
            return instance

    async def deregister(self, service_id: str) -> bool:
        """Deregister a service instance."""
        async with self._lock:
            if service_id not in self.service_index:
                return False

            instance = self.service_index[service_id]
            instance.state = ServiceState.TERMINATED

            # Remove from active services
            if instance.name in self.services:
                self.services[instance.name] = [s for s in self.services[instance.name] if s.id != service_id]

            del self.service_index[service_id]

            # Notify subscribers
            await self._notify_subscribers("service_deregistered", instance)

            # Save to disk
            await self._save_registry()

            logging.info(f"Service deregistered: {instance.name} ({service_id})")
            return True

    async def discover(self, service_name: str, healthy_only: bool = True) -> list[ServiceInstance]:
        """Discover service instances."""
        instances = self.services.get(service_name, [])

        if healthy_only:
            instances = [s for s in instances if s.state in [ServiceState.HEALTHY, ServiceState.DEGRADED]]

        return instances.copy()

    async def get_service_by_id(self, service_id: str) -> ServiceInstance | None:
        """Get service instance by ID."""
        return self.service_index.get(service_id)

    async def update_service_state(self, service_id: str, state: ServiceState):
        """Update service state."""
        async with self._lock:
            if service_id in self.service_index:
                instance = self.service_index[service_id]
                old_state = instance.state
                instance.state = state
                instance.last_heartbeat = time.time()

                # Notify subscribers if state changed
                if old_state != state:
                    await self._notify_subscribers("service_state_changed", instance)

                await self._save_registry()

    async def heartbeat(self, service_id: str) -> bool:
        """Record service heartbeat."""
        if service_id in self.service_index:
            self.service_index[service_id].last_heartbeat = time.time()
            return True
        return False

    async def subscribe(self, event: str, callback: Callable):
        """Subscribe to service events."""
        self.subscriptions[event].append(callback)

    async def _notify_subscribers(self, event: str, instance: ServiceInstance):
        """Notify event subscribers."""
        for callback in self.subscriptions.get(event, []):
            try:
                await callback(instance)
            except Exception as e:
                logging.error(f"Subscriber callback error: {e}")

    async def _save_registry(self):
        """Save registry to disk."""
        try:
            import aiofiles

            data = {name: [instance.to_dict() for instance in instances] for name, instances in self.services.items()}

            async with aiofiles.open(self.config_file, "w") as f:
                await f.write(json.dumps(data, indent=2))
        except Exception as e:
            logging.error(f"Failed to save registry: {e}")

    async def _load_registry(self):
        """Load registry from disk."""
        try:
            import aiofiles

            async with aiofiles.open(self.config_file) as f:
                content = await f.read()
                data = json.loads(content)

            for service_name, instances_data in data.items():
                for instance_data in instances_data:
                    instance = ServiceInstance(
                        id=instance_data["id"],
                        name=instance_data["name"],
                        type=ServiceType(instance_data["type"]),
                        host=instance_data["host"],
                        port=instance_data["port"],
                        version=instance_data["version"],
                        metadata=instance_data.get("metadata", {}),
                        tags=set(instance_data.get("tags", [])),
                        state=ServiceState(instance_data.get("state", "healthy")),
                        registered_at=instance_data.get("registered_at", time.time()),
                        last_heartbeat=instance_data.get("last_heartbeat", time.time()),
                        health_check_url=instance_data.get("health_check_url"),
                        endpoints=instance_data.get("endpoints", []),
                    )

                    self.services[service_name].append(instance)
                    self.service_index[instance.id] = instance

            logging.info(f"Loaded {len(self.service_index)} services from registry")
        except FileNotFoundError:
            logging.info("No existing registry found, starting fresh")
        except Exception as e:
            logging.error(f"Failed to load registry: {e}")


class LoadBalancer:
    """Load balancer for service instances."""

    def __init__(self, strategy: str = "round_robin"):
        self.strategy = strategy
        self.round_robin_counters: dict[str, int] = defaultdict(int)

    def select_instance(self, instances: list[ServiceInstance]) -> ServiceInstance | None:
        """Select an instance based on strategy."""
        if not instances:
            return None

        healthy_instances = [s for s in instances if s.state in [ServiceState.HEALTHY, ServiceState.DEGRADED]]

        if not healthy_instances:
            return None

        if self.strategy == "round_robin":
            return self._round_robin_select(healthy_instances)
        elif self.strategy == "random":
            return self._random_select(healthy_instances)
        elif self.strategy == "least_connections":
            return self._least_connections_select(healthy_instances)
        else:
            return healthy_instances[0]

    def _round_robin_select(self, instances: list[ServiceInstance]) -> ServiceInstance:
        """Round-robin selection."""
        service_key = instances[0].name
        counter = self.round_robin_counters[service_key]
        selected = instances[counter % len(instances)]
        self.round_robin_counters[service_key] = counter + 1
        return selected

    def _random_select(self, instances: list[ServiceInstance]) -> ServiceInstance:
        """Random selection."""
        import random

        return random.choice(instances)  # noqa: S311 non-security random use

    def _least_connections_select(self, instances: list[ServiceInstance]) -> ServiceInstance:
        """Select instance with least connections (simulated)."""
        # For now, just return the first healthy instance
        # In a real implementation, you'd track active connections
        return instances[0]


class CircuitBreaker:
    """Circuit breaker for inter-service communication."""

    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        self.state = "CLOSED"

    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


class ServiceMesh:
    """
    Service mesh implementation for dynamic architecture.
    """

    def __init__(self, registry_port: int = 8500):
        self.registry = ServiceRegistry()
        self.load_balancer = LoadBalancer()
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.registry_port = registry_port
        self.health_check_interval = 30.0
        self.health_check_task: asyncio.Task | None = None
        self.session: ClientSession | None = None

    async def start(self):
        """Start the service mesh."""
        # Load existing registry
        await self.registry._load_registry()

        # Start HTTP session
        self.session = ClientSession(timeout=ClientTimeout(total=30))

        # Start health check task
        self.health_check_task = asyncio.create_task(self._health_check_loop())

        # Start registry server
        await self._start_registry_server()

        logging.info("Service mesh started")

    async def stop(self):
        """Stop the service mesh."""
        if self.health_check_task:
            self.health_check_task.cancel()

        if self.session:
            await self.session.close()

        logging.info("Service mesh stopped")

    async def register_service(self, registration: ServiceRegistration) -> str:
        """Register a service."""
        instance = await self.registry.register(registration)

        # Initialize circuit breaker
        self.circuit_breakers[instance.id] = CircuitBreaker()

        return instance.id

    async def deregister_service(self, service_id: str) -> bool:
        """Deregister a service."""
        if service_id in self.circuit_breakers:
            del self.circuit_breakers[service_id]

        return await self.registry.deregister(service_id)

    async def discover_service(self, service_name: str) -> ServiceInstance | None:
        """Discover and select a service instance."""
        instances = await self.registry.discover(service_name)
        return self.load_balancer.select_instance(instances)

    async def call_service(self, service_name: str, endpoint: str, method: str = "GET", **kwargs) -> Any:
        """Call a service endpoint with circuit breaker and fallback."""
        instance = await self.discover_service(service_name)
        if not instance:
            logging.warning(f"No healthy instances found for {service_name}, using fallback")
            return await self._get_fallback_response(service_name)

        circuit_breaker = self.circuit_breakers.get(instance.id)
        if not circuit_breaker:
            circuit_breaker = CircuitBreaker()
            self.circuit_breakers[instance.id] = circuit_breaker

        url = f"http://{instance.host}:{instance.port}{endpoint}"

        async def make_request():
            async with self.session.request(method, url, **kwargs) as response:
                if response.status >= 500:
                    raise Exception(f"Service error: {response.status}")
                return await response.json()

        try:
            return await circuit_breaker.call(make_request)
        except Exception as e:
            if "Circuit breaker is OPEN" in str(e) or "Service error" in str(e):
                logging.warning(f"Circuit breaker error or service failure for {service_name}: {e}, using fallback")
                return await self._get_fallback_response(service_name)
            raise e

    async def _get_fallback_response(self, service_name: str) -> dict[str, Any]:
        """Provide a fallback response for service mesh calls."""
        fallback_data = {
            "error": "Service temporarily unavailable (Mesh Fallback)",
            "service": service_name,
            "status": "degraded_mode",
            "message": "The service is currently unavailable. Returning simplified data.",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "fallback": True,
        }

        # Service-specific simplified data
        if "ai" in service_name.lower():
            fallback_data["generated_text"] = "AI features are temporarily unavailable."
            fallback_data["confidence"] = 0.0
        elif "discussion" in service_name.lower():
            fallback_data["topics"] = []
            fallback_data["reasoning_chain"] = ["Fallback: reasoning engine unavailable"]

        return fallback_data

    async def _health_check_loop(self):
        """Background health check loop."""
        while True:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Health check error: {e}")
                await asyncio.sleep(5)

    async def _perform_health_checks(self):
        """Perform health checks on all services."""
        for service_name, instances in self.registry.services.items():
            for instance in instances:
                if instance.state == ServiceState.TERMINATED:
                    continue

                try:
                    if instance.health_check_url:
                        url = f"http://{instance.host}:{instance.port}{instance.health_check_url}"
                        async with self.session.get(url, timeout=5) as response:
                            if response.status == 200:
                                await self.registry.update_service_state(instance.id, ServiceState.HEALTHY)
                            else:
                                await self.registry.update_service_state(instance.id, ServiceState.DEGRADED)
                    else:
                        # Default health check - just update heartbeat
                        await self.registry.heartbeat(instance.id)

                except Exception as e:
                    logging.warning(f"Health check failed for {service_name}: {e}")
                    await self.registry.update_service_state(instance.id, ServiceState.UNHEALTHY)

    async def _start_registry_server(self):
        """Start the HTTP registry server."""
        app = web.Application()

        app.add_routes(
            [
                web.get("/services", self._list_services),
                web.get("/services/{service_name}", self._get_service),
                web.post("/services/register", self._register_service),
                web.delete("/services/{service_id}", self._deregister_service),
                web.post("/services/{service_id}/heartbeat", self._heartbeat),
                web.get("/health", self._health_check),
            ]
        )

        runner = web.AppRunner(app)
        await runner.setup()

        site = web.TCPSite(runner, "0.0.0.0", self.registry_port)  # noqa: S104 bind-all is intentional for container deployment
        await site.start()

        logging.info(f"Service registry started on port {self.registry_port}")

    async def _list_services(self, request):
        """List all services."""
        services = {}
        for name, instances in self.registry.services.items():
            services[name] = [instance.to_dict() for instance in instances]

        return web.json_response(services)

    async def _get_service(self, request):
        """Get service instances."""
        service_name = request.match_info["service_name"]
        instances = await self.registry.discover(service_name)

        return web.json_response([instance.to_dict() for instance in instances])

    async def _register_service(self, request):
        """Register a new service."""
        data = await request.json()

        registration = ServiceRegistration(
            name=data["name"],
            type=ServiceType(data["type"]),
            host=data["host"],
            port=data["port"],
            version=data["version"],
            metadata=data.get("metadata", {}),
            tags=set(data.get("tags", [])),
            health_check_url=data.get("health_check_url"),
            endpoints=data.get("endpoints", []),
        )

        instance = await self.registry.register(registration)
        return web.json_response(instance.to_dict())

    async def _deregister_service(self, request):
        """Deregister a service."""
        service_id = request.match_info["service_id"]
        success = await self.registry.deregister(service_id)

        return web.json_response({"success": success})

    async def _heartbeat(self, request):
        """Service heartbeat."""
        service_id = request.match_info["service_id"]
        success = await self.registry.heartbeat(service_id)

        return web.json_response({"success": success})

    async def _health_check(self, request):
        """Registry health check."""
        return web.json_response({"status": "healthy", "services": len(self.registry.service_index)})


# ============================================================================
# Example Usage
# ============================================================================


async def example_mesh_setup():
    """Example setup of service mesh."""
    mesh = ServiceMesh()
    await mesh.start()

    # Register GRID service
    await mesh.register_service(
        ServiceRegistration(
            name="grid-service",
            type=ServiceType.CORE_SERVICE,
            host="localhost",
            port=8080,
            version="1.0.0",
            health_check_url="/health",
            tags={"core", "intelligence"},
        )
    )

    # Register Coinbase service
    await mesh.register_service(
        ServiceRegistration(
            name="coinbase-service",
            type=ServiceType.DATA_SERVICE,
            host="localhost",
            port=8081,
            version="1.0.0",
            health_check_url="/health",
            tags={"crypto", "finance"},
        )
    )

    # Call a service
    try:
        result = await mesh.call_service("grid-service", "/api/v1/status", method="GET")
        print(f"Service call result: {result}")
    except Exception as e:
        print(f"Service call failed: {e}")

    return mesh


if __name__ == "__main__":

    async def main():
        mesh = await example_mesh_setup()

        try:
            # Keep running
            while True:  # noqa: ASYNC110 busy-wait is intentional for polling pattern
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await mesh.stop()

    asyncio.run(main())
