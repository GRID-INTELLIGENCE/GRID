"""
Service Discovery - Stub Implementation
"""


class ServiceDiscovery:
    """Stub service discovery manager."""

    def __init__(self) -> None:
        self.services: dict[str, dict[str, Any]] = {}

    async def get_services(self) -> dict[str, dict[str, Any]]:
        """Get all registered services."""
        return self.services

    async def register_service(self, service_data: dict[str, Any]) -> bool:
        """Register a service."""
        self.services[service_data["service_name"]] = service_data
        return True

    async def unregister_service(self, service_name: str) -> bool:
        """Unregister a service."""
        if service_name in self.services:
            del self.services[service_name]
            return True
        return False

    async def get_healthy_services(self, service_name: str) -> list[dict[str, Any]]:
        """Get healthy service instances."""
        if service_name in self.services:
            return [self.services[service_name]]
        return []

    async def heartbeat(self) -> None:
        """Send heartbeat to service registry."""
        pass

    async def cleanup(self) -> None:
        """Cleanup resources."""
        pass
