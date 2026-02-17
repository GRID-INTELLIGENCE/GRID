"""
Arena Architecture Orchestrator
===============================

Main orchestrator that integrates all components of the modernized arena architecture.
Transforms the dial-up-like static system into a dynamic, efficient, wrist-watch-like mechanism.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import Any

from ..ai_ml.intelligence_system import (  # type: ignore[import-not-found]
    AISafetyLevel,
    DataSensitivity,
    FrontierIntelligenceSystem,
)
from ..api_gateway.gateway import APIGateway, RouteConfig, ServiceEndpoint  # type: ignore[import-not-found]
from ..event_bus.event_system import EventBus, EventPriority  # type: ignore[import-not-found]
from ..service_mesh.mesh import ServiceMesh, ServiceRegistration, ServiceType  # type: ignore[import-not-found]


class OrchestratorState(StrEnum):
    """Orchestrator states."""

    INITIALIZING = "initializing"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class ServiceConfig:
    """Service configuration."""

    name: str
    type: ServiceType
    host: str
    port: int
    version: str
    health_check_path: str = "/health"
    routes: list[RouteConfig] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class OrchestratorConfig:
    """Orchestrator configuration."""

    gateway_port: int = 8000
    mesh_registry_port: int = 8500
    redis_url: str = "redis://localhost:6379"
    rabbitmq_url: str = "amqp://localhost:5672"
    region: str = "southeast_asia"
    ai_safety_level: AISafetyLevel = AISafetyLevel.PERMITTED
    enable_monitoring: bool = True
    enable_ai_ml: bool = True
    health_check_interval: float = 30.0
    max_retries: int = 3
    timeout: float = 30.0


class ArenaOrchestrator:
    """
    Main orchestrator for the modernized arena architecture.

    Integrates:
    - API Gateway for request routing and load balancing
    - Service Mesh for service discovery and communication
    - Event Bus for asynchronous communication
    - AI/ML System for intelligent capabilities
    """

    def __init__(self, config: OrchestratorConfig):
        self.config = config
        self.state = OrchestratorState.INITIALIZING

        # Core components
        self.api_gateway: APIGateway | None = None
        self.service_mesh: ServiceMesh | None = None
        self.event_bus: EventBus | None = None
        self.intelligence_system: FrontierIntelligenceSystem | None = None

        # Service registry
        self.services: dict[str, ServiceConfig] = {}
        self.service_instances: dict[str, str] = {}  # name -> instance_id

        # Monitoring
        self.metrics: dict[str, Any] = {
            "start_time": 0,
            "requests_processed": 0,
            "requests_failed": 0,
            "events_processed": 0,
            "ai_predictions": 0,
            "active_services": 0,
        }

        # Health monitoring
        self.health_status: dict[str, dict[str, Any]] = {}
        self.health_check_task: asyncio.Task | None = None

        logging.info("Arena Orchestrator initialized")

    async def start(self):
        """Start the orchestrator and all components."""
        try:
            self.state = OrchestratorState.STARTING
            self.metrics["start_time"] = time.time()

            logging.info("Starting Arena Orchestrator...")

            # Start components in dependency order
            await self._start_event_bus()
            await self._start_service_mesh()
            await self._start_api_gateway()
            await self._start_intelligence_system()

            # Start health monitoring
            if self.config.enable_monitoring:
                self.health_check_task = asyncio.create_task(self._health_monitoring_loop())

            # Register core services
            await self._register_core_services()

            self.state = OrchestratorState.RUNNING
            logging.info("Arena Orchestrator started successfully")

        except Exception as e:
            self.state = OrchestratorState.ERROR
            logging.error(f"Failed to start orchestrator: {e}")
            raise

    async def stop(self):
        """Stop the orchestrator and all components."""
        try:
            self.state = OrchestratorState.STOPPING
            logging.info("Stopping Arena Orchestrator...")

            # Stop health monitoring
            if self.health_check_task:
                self.health_check_task.cancel()

            # Stop components in reverse order
            if self.intelligence_system:
                await self.intelligence_system.stop()

            if self.api_gateway:
                await self.api_gateway.stop()

            if self.service_mesh:
                await self.service_mesh.stop()

            if self.event_bus:
                await self.event_bus.stop()

            self.state = OrchestratorState.STOPPED
            logging.info("Arena Orchestrator stopped")

        except Exception as e:
            self.state = OrchestratorState.ERROR
            logging.error(f"Error stopping orchestrator: {e}")

    async def register_service(self, service_config: ServiceConfig) -> str:
        """Register a service with the orchestrator."""
        self.services[service_config.name] = service_config

        # Register with service mesh
        registration = ServiceRegistration(
            name=service_config.name,
            type=service_config.type,
            host=service_config.host,
            port=service_config.port,
            version=service_config.version,
            metadata=service_config.metadata,
            health_check_url=service_config.health_check_path,
        )

        instance_id = await self.service_mesh.register_service(registration)
        self.service_instances[service_config.name] = instance_id

        # Register routes with API gateway
        for route in service_config.routes:
            self.api_gateway.register_route(route)

        # Register service endpoint with API gateway
        endpoint = ServiceEndpoint(
            name=service_config.name,
            url=f"http://{service_config.host}:{service_config.port}",
            health_check_path=service_config.health_check_path,
        )
        self.api_gateway.register_service(endpoint)

        logging.info(f"Service registered: {service_config.name}")
        return instance_id

    async def deregister_service(self, service_name: str) -> bool:
        """Deregister a service."""
        if service_name in self.service_instances:
            instance_id = self.service_instances[service_name]
            await self.service_mesh.deregister_service(instance_id)
            del self.service_instances[service_name]

        if service_name in self.services:
            del self.services[service_name]

        logging.info(f"Service deregistered: {service_name}")
        return True

    async def call_service(self, service_name: str, endpoint: str, method: str = "GET", **kwargs) -> Any:
        """Call a service through the service mesh."""
        return await self.service_mesh.call_service(service_name, endpoint, method, **kwargs)

    async def publish_event(
        self,
        event_type: str,
        data: dict[str, Any],
        source: str = "orchestrator",
        priority: EventPriority = EventPriority.NORMAL,
    ) -> str:
        """Publish an event through the event bus."""
        event_id = await self.event_bus.publish(event_type, data, source, priority)

        self.metrics["events_processed"] += 1
        return event_id

    async def make_prediction(
        self,
        model_name: str,
        input_data: dict[str, Any],
        safety_level: AISafetyLevel = AISafetyLevel.PERMITTED,
        data_sensitivity: DataSensitivity = DataSensitivity.PUBLIC,
    ) -> Any:
        """Make an AI prediction."""
        if not self.intelligence_system:
            raise Exception("AI/ML system not enabled")

        response = await self.intelligence_system.predict(model_name, input_data, safety_level, data_sensitivity)

        self.metrics["ai_predictions"] += 1
        return response

    async def get_system_status(self) -> dict[str, Any]:
        """Get comprehensive system status."""
        status = {
            "orchestrator": {"state": self.state.value, "uptime": time.time() - self.metrics["start_time"]},
            "services": {"registered": len(self.services), "active": len(self.service_instances), "details": {}},
            "components": {},
            "metrics": self.metrics.copy(),
        }

        # Service details
        for name, config in self.services.items():
            status["services"]["details"][name] = {
                "type": config.type.value,
                "host": f"{config.host}:{config.port}",
                "version": config.version,
                "active": name in self.service_instances,
            }

        # Component status
        if self.api_gateway:
            status["components"]["api_gateway"] = self.api_gateway.get_service_status()

        if self.service_mesh:
            # Get service mesh status
            status["components"]["service_mesh"] = {"status": "running"}

        if self.event_bus:
            status["components"]["event_bus"] = await self.event_bus.get_metrics()

        if self.intelligence_system:
            status["components"]["intelligence_system"] = await self.intelligence_system.get_metrics()

        return status

    async def _start_event_bus(self):
        """Start the event bus."""
        self.event_bus = EventBus(redis_url=self.config.redis_url, rabbitmq_url=self.config.rabbitmq_url)
        await self.event_bus.start()
        logging.info("Event bus started")

    async def _start_service_mesh(self):
        """Start the service mesh."""
        self.service_mesh = ServiceMesh(registry_port=self.config.mesh_registry_port)
        await self.service_mesh.start()
        logging.info("Service mesh started")

    async def _start_api_gateway(self):
        """Start the API gateway."""
        self.api_gateway = APIGateway(redis_url=self.config.redis_url)
        await self.api_gateway.start()
        logging.info("API gateway started")

    async def _start_intelligence_system(self):
        """Start the AI/ML system."""
        if self.config.enable_ai_ml:
            self.intelligence_system = FrontierIntelligenceSystem(
                region=self.config.region, redis_url=self.config.redis_url, event_bus=self.event_bus
            )
            await self.intelligence_system.start()
            logging.info("AI/ML system started")

    async def _register_core_services(self):
        """Register core orchestrator services."""
        # Register orchestrator as a service
        orchestrator_config = ServiceConfig(
            name="arena-orchestrator",
            type=ServiceType.API_GATEWAY,
            host="localhost",
            port=self.config.gateway_port,
            version="1.0.0",
            health_check_path="/health",
            metadata={"component": "orchestrator"},
        )

        await self.register_service(orchestrator_config)

    async def _health_monitoring_loop(self):
        """Background health monitoring loop."""
        while self.state == OrchestratorState.RUNNING:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.config.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Health monitoring error: {e}")
                await asyncio.sleep(5)

    async def _perform_health_checks(self):
        """Perform health checks on all components."""
        health_status = {"timestamp": time.time(), "components": {}}

        # Check API Gateway
        if self.api_gateway:
            try:
                # Simple health check
                health_status["components"]["api_gateway"] = "healthy"
            except Exception as e:
                health_status["components"]["api_gateway"] = f"unhealthy: {e}"

        # Check Service Mesh
        if self.service_mesh:
            try:
                # Check if registry is accessible
                health_status["components"]["service_mesh"] = "healthy"
            except Exception as e:
                health_status["components"]["service_mesh"] = f"unhealthy: {e}"

        # Check Event Bus
        if self.event_bus:
            try:
                await self.event_bus.get_metrics()
                health_status["components"]["event_bus"] = "healthy"
            except Exception as e:
                health_status["components"]["event_bus"] = f"unhealthy: {e}"

        # Check AI/ML System
        if self.intelligence_system:
            try:
                await self.intelligence_system.get_metrics()
                health_status["components"]["intelligence_system"] = "healthy"
            except Exception as e:
                health_status["components"]["intelligence_system"] = f"unhealthy: {e}"

        self.health_status = health_status


# ============================================================================
# Example Usage
# ============================================================================


async def example_orchestrator_setup():
    """Example setup of arena orchestrator."""
    config = OrchestratorConfig(gateway_port=8000, mesh_registry_port=8500, enable_ai_ml=True, region="southeast_asia")

    orchestrator = ArenaOrchestrator(config)
    await orchestrator.start()

    # Register GRID service
    grid_config = ServiceConfig(
        name="grid-service",
        type=ServiceType.CORE_SERVICE,
        host="localhost",
        port=8080,
        version="1.0.0",
        routes=[
            RouteConfig(path="/api/v1/grid", service_name="grid-service", methods=["GET", "POST", "PUT", "DELETE"])
        ],
    )

    await orchestrator.register_service(grid_config)

    # Register Coinbase service
    coinbase_config = ServiceConfig(
        name="coinbase-service",
        type=ServiceType.DATA_SERVICE,
        host="localhost",
        port=8081,
        version="1.0.0",
        routes=[RouteConfig(path="/api/v1/coinbase", service_name="coinbase-service", methods=["GET", "POST"])],
    )

    await orchestrator.register_service(coinbase_config)

    # Publish events
    await orchestrator.publish_event(
        "system.started", {"services": len(orchestrator.services)}, source="orchestrator", priority=EventPriority.HIGH
    )

    # Get system status
    status = await orchestrator.get_system_status()
    print(f"System status: {json.dumps(status, indent=2)}")

    return orchestrator


if __name__ == "__main__":

    async def main():
        orchestrator = await example_orchestrator_setup()

        try:
            # Keep running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await orchestrator.stop()

    asyncio.run(main())
