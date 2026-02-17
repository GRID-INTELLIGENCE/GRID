"""
Service Discovery - Stub Implementation
"""


class ServiceDiscovery:
    """Stub service discovery manager."""

    def __init__(self):
        self.services = {}

    async def get_services(self) -> dict:
        """Get all registered services."""
        return self.services

    async def register_service(self, service_data: dict) -> bool:
        """Register a service."""
        self.services[service_data["service_name"]] = service_data
        return True

    async def unregister_service(self, service_name: str) -> bool:
        """Unregister a service."""
        if service_name in self.services:
            del self.services[service_name]
            return True
        return False

    async def get_healthy_services(self, service_name: str) -> list:
        """Get healthy service instances."""
        if service_name in self.services:
            return [self.services[service_name]]
        return []

    async def heartbeat(self):
        """Send heartbeat to service registry."""
        pass

    async def cleanup(self):
        """Cleanup resources."""
        pass
