"""
Service Discovery for Arena API Gateway
======================================

This module implements dynamic service discovery and registration,
enabling the transformation from static dial-up connections to
dynamic, self-healing service mesh architecture.

Key Features:
- Service registration and deregistration
- Health checking and status monitoring
- Load balancing integration
- Service mesh capabilities
- Automatic failover and recovery
"""

import asyncio
import logging
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class ServiceInstance:
    """Represents a service instance."""

    id: str
    service_name: str
    url: str
    health_url: str
    metadata: dict[str, Any]
    registered_at: datetime
    last_heartbeat: datetime
    status: str = "unknown"  # unknown, healthy, unhealthy, down
    version: str = "1.0.0"
    tags: list[str] | None = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class ServiceHealth:
    """Service health information."""

    status: str
    response_time: float
    last_check: datetime
    consecutive_failures: int
    total_checks: int
    uptime_percentage: float


class ServiceDiscovery:
    """
    Dynamic service discovery and registration system.
    """

    def __init__(self):
        self.services: dict[str, list[ServiceInstance]] = {}
        self.service_health: dict[str, ServiceHealth] = {}
        self.heartbeat_interval = 30  # seconds
        self.health_check_interval = 60  # seconds
        self.max_consecutive_failures = 3
        self.session_timeout = 30  # seconds
        self._running = False
        self._tasks = []

    async def start(self):
        """Start the service discovery system."""
        if self._running:
            return

        self._running = True
        logger.info("Starting service discovery system")

        # Start background tasks
        self._tasks = [
            asyncio.create_task(self._heartbeat_monitor()),
            asyncio.create_task(self._health_checker()),
            asyncio.create_task(self._service_cleanup()),
        ]

    async def stop(self):
        """Stop the service discovery system."""
        self._running = False

        # Cancel all tasks
        for task in self._tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self._tasks, return_exceptions=True)

        logger.info("Service discovery system stopped")

    async def register_service(self, service_data: dict[str, Any]) -> dict[str, Any]:
        """
        Register a new service instance.

        Args:
            service_data: Service registration data

        Returns:
            Registration result
        """
        try:
            # Validate required fields
            required_fields = ["service_name", "url", "health_url"]
            for field in required_fields:
                if field not in service_data:
                    return {"success": False, "error": f"Missing required field: {field}"}

            service_name = service_data["service_name"]
            instance_id = service_data.get("id", f"{service_name}-{int(time.time() * 1000)}")

            # Create service instance
            instance = ServiceInstance(
                id=instance_id,
                service_name=service_name,
                url=service_data["url"],
                health_url=service_data["health_url"],
                metadata=service_data.get("metadata", {}),
                registered_at=datetime.now(UTC),
                last_heartbeat=datetime.now(UTC),
                status="registering",
                version=service_data.get("version", "1.0.0"),
                tags=service_data.get("tags", []),
            )

            # Add to services registry
            if service_name not in self.services:
                self.services[service_name] = []

            # Remove existing instance if it exists
            self.services[service_name] = [inst for inst in self.services[service_name] if inst.id != instance_id]

            self.services[service_name].append(instance)

            # Initialize health tracking
            self.service_health[instance_id] = ServiceHealth(
                status="unknown",
                response_time=0.0,
                last_check=datetime.now(UTC),
                consecutive_failures=0,
                total_checks=0,
                uptime_percentage=0.0,
            )

            logger.info(f"Registered service instance: {service_name}/{instance_id}")

            return {"success": True, "instance_id": instance_id, "service_name": service_name}

        except Exception as e:
            logger.error(f"Service registration error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def deregister_service(self, service_name: str, instance_id: str) -> dict[str, Any]:
        """
        Deregister a service instance.

        Args:
            service_name: Name of the service
            instance_id: ID of the instance to deregister

        Returns:
            Deregistration result
        """
        try:
            if service_name not in self.services:
                return {"success": False, "error": f"Service not found: {service_name}"}

            original_count = len(self.services[service_name])
            self.services[service_name] = [inst for inst in self.services[service_name] if inst.id != instance_id]

            if len(self.services[service_name]) < original_count:
                # Clean up health tracking
                if instance_id in self.service_health:
                    del self.service_health[instance_id]

                logger.info(f"Deregistered service instance: {service_name}/{instance_id}")

                return {"success": True, "service_name": service_name, "instance_id": instance_id}
            else:
                return {"success": False, "error": f"Instance not found: {instance_id}"}

        except Exception as e:
            logger.error(f"Service deregistration error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_services(self) -> dict[str, list[dict[str, Any]]]:
        """
        Get all registered services with their instances.

        Returns:
            Dict of service names to list of instance data
        """
        result = {}
        for service_name, instances in self.services.items():
            result[service_name] = [
                {
                    **asdict(instance),
                    "health": asdict(health) if (health := self.service_health.get(instance.id)) else None,
                }
                for instance in instances
            ]
        return result

    async def get_service_instances(self, service_name: str) -> list[dict[str, Any]]:
        """
        Get all instances of a specific service.

        Args:
            service_name: Name of the service

        Returns:
            List of service instance data
        """
        if service_name not in self.services:
            return []

        instances = []
        for instance in self.services[service_name]:
            health = self.service_health.get(instance.id)
            instances.append({**asdict(instance), "health": asdict(health) if health else None})

        return instances

    async def get_healthy_instances(self, service_name: str) -> list[dict[str, Any]]:
        """
        Get only healthy instances of a service.

        Args:
            service_name: Name of the service

        Returns:
            List of healthy service instances
        """
        instances = await self.get_service_instances(service_name)
        return [instance for instance in instances if instance.get("health", {}).get("status") == "healthy"]

    async def update_heartbeat(self, service_name: str, instance_id: str) -> dict[str, Any]:
        """
        Update heartbeat for a service instance.

        Args:
            service_name: Name of the service
            instance_id: ID of the instance

        Returns:
            Heartbeat update result
        """
        try:
            if service_name not in self.services:
                return {"success": False, "error": f"Service not found: {service_name}"}

            instance = None
            for inst in self.services[service_name]:
                if inst.id == instance_id:
                    instance = inst
                    break

            if not instance:
                return {"success": False, "error": f"Instance not found: {instance_id}"}

            instance.last_heartbeat = datetime.now(UTC)
            instance.status = "healthy"

            return {
                "success": True,
                "service_name": service_name,
                "instance_id": instance_id,
                "last_heartbeat": instance.last_heartbeat.isoformat(),
            }

        except Exception as e:
            logger.error(f"Heartbeat update error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _heartbeat_monitor(self):
        """Monitor service heartbeats and mark unhealthy services."""
        while self._running:
            try:
                await asyncio.sleep(self.heartbeat_interval)

                current_time = datetime.now(UTC)
                stale_threshold = timedelta(seconds=self.heartbeat_interval * 2)

                for service_name, instances in self.services.items():
                    for instance in instances:
                        time_since_heartbeat = current_time - instance.last_heartbeat

                        if time_since_heartbeat > stale_threshold:
                            if instance.status != "unhealthy":
                                logger.warning(f"Service instance became unhealthy: {service_name}/{instance.id}")
                                instance.status = "unhealthy"

            except Exception as e:
                logger.error(f"Heartbeat monitor error: {str(e)}")
                await asyncio.sleep(5)

    async def _health_checker(self):
        """Perform health checks on registered services."""
        while self._running:
            try:
                await asyncio.sleep(self.health_check_interval)

                for service_name, instances in list(self.services.items()):
                    for instance in instances:
                        await self._check_instance_health(instance)

            except Exception as e:
                logger.error(f"Health checker error: {str(e)}")
                await asyncio.sleep(5)

    async def _check_instance_health(self, instance: ServiceInstance):
        """Check health of a specific service instance."""
        try:
            health_info = self.service_health.get(instance.id)
            if not health_info:
                return

            start_time = time.time()

            # Perform health check
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(instance.health_url) as response:
                    response_time = time.time() - start_time

                    if response.status == 200:
                        # Service is healthy
                        instance.status = "healthy"
                        health_info.status = "healthy"
                        health_info.consecutive_failures = 0
                    else:
                        # Service returned error status
                        health_info.consecutive_failures += 1
                        if health_info.consecutive_failures >= self.max_consecutive_failures:
                            instance.status = "unhealthy"
                            health_info.status = "unhealthy"
                        else:
                            instance.status = "degraded"

                    health_info.response_time = response_time
                    health_info.last_check = datetime.now(UTC)
                    health_info.total_checks += 1

                    # Calculate uptime percentage
                    total_time = (datetime.now(UTC) - instance.registered_at).total_seconds()
                    healthy_time = (
                        total_time
                        * (health_info.total_checks - health_info.consecutive_failures)
                        / max(health_info.total_checks, 1)
                    )
                    health_info.uptime_percentage = (healthy_time / total_time) * 100 if total_time > 0 else 0

        except Exception as e:
            # Health check failed
            logger.warning(f"Health check failed for {instance.service_name}/{instance.id}: {str(e)}")

            health_info = self.service_health.get(instance.id)
            if health_info:
                health_info.consecutive_failures += 1
                health_info.response_time = 0.0
                health_info.last_check = datetime.now(UTC)

                if health_info.consecutive_failures >= self.max_consecutive_failures:
                    instance.status = "down"
                    health_info.status = "down"

    async def _service_cleanup(self):
        """Clean up old or failed service instances."""
        while self._running:
            try:
                await asyncio.sleep(300)  # Clean up every 5 minutes

                current_time = datetime.now(UTC)
                cleanup_threshold = timedelta(hours=1)  # Remove instances older than 1 hour

                for service_name, instances in list(self.services.items()):
                    active_instances = []

                    for instance in instances:
                        time_since_registration = current_time - instance.registered_at
                        time_since_heartbeat = current_time - instance.last_heartbeat

                        # Remove instances that haven't sent heartbeat in over an hour
                        # or have been registered for too long without activity
                        if time_since_heartbeat < cleanup_threshold and time_since_registration < timedelta(hours=24):
                            active_instances.append(instance)
                        else:
                            logger.info(f"Cleaning up stale service instance: {service_name}/{instance.id}")
                            if instance.id in self.service_health:
                                del self.service_health[instance.id]

                    self.services[service_name] = active_instances

                    # Remove empty service entries
                    if not self.services[service_name]:
                        del self.services[service_name]

            except Exception as e:
                logger.error(f"Service cleanup error: {str(e)}")
                await asyncio.sleep(30)

    async def cleanup(self):
        """Cleanup resources."""
        await self.stop()

    def get_service_stats(self) -> dict[str, Any]:
        """Get statistics about registered services."""
        total_services = len(self.services)
        total_instances = sum(len(instances) for instances in self.services.values())
        healthy_instances = 0
        unhealthy_instances = 0

        for instances in self.services.values():
            for instance in instances:
                health = self.service_health.get(instance.id)
                if health and health.status == "healthy":
                    healthy_instances += 1
                else:
                    unhealthy_instances += 1

        return {
            "total_services": total_services,
            "total_instances": total_instances,
            "healthy_instances": healthy_instances,
            "unhealthy_instances": unhealthy_instances,
            "health_percentage": (healthy_instances / total_instances * 100) if total_instances > 0 else 0,
        }
