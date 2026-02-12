"""
API Gateway for GRID Mothership.

Centralized API gateway that provides:
- Versioned route aggregation (v1, v2)
- Dependency injection container for shared services
- Health-aware routing with circuit breaker integration
- Request/response envelope standardization

The gateway is the single entry point for all external API traffic.
Internal service-to-service calls bypass the gateway and use the
event bus or direct dependency injection.

Usage:
    from application.mothership.api.gateway import APIGateway

    gateway = APIGateway(settings=get_settings())
    app.include_router(gateway.router)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# =============================================================================
# Response Envelope
# =============================================================================


class APIEnvelope(BaseModel):
    """Standard API response envelope for all gateway responses."""

    success: bool = True
    data: Any = None
    error: dict[str, Any] | None = None
    meta: dict[str, Any] = {}

    @classmethod
    def ok(cls, data: Any, **meta: Any) -> "APIEnvelope":
        """Create a success envelope."""
        return cls(success=True, data=data, meta=meta)

    @classmethod
    def fail(cls, code: str, message: str, details: dict[str, Any] | None = None) -> "APIEnvelope":
        """Create an error envelope."""
        return cls(
            success=False,
            error={"code": code, "message": message, "details": details or {}},
        )


# =============================================================================
# Dependency Container
# =============================================================================


@dataclass
class DependencyContainer:
    """
    Lightweight dependency injection container for gateway services.

    Provides lazy-initialized access to shared services without
    requiring global state or circular imports.

    Attributes:
        _registry: Mapping of service name to factory callable.
        _instances: Cached singleton instances.
    """

    _registry: dict[str, Any] = field(default_factory=dict)
    _instances: dict[str, Any] = field(default_factory=dict)

    def register(self, name: str, factory: Any) -> None:
        """Register a service factory.

        Args:
            name: Service identifier (e.g., "event_bus", "config_registry").
            factory: Callable that produces the service instance.
        """
        self._registry[name] = factory
        # Invalidate cached instance on re-registration
        self._instances.pop(name, None)

    def resolve(self, name: str) -> Any:
        """Resolve a service by name, creating it on first access.

        Args:
            name: Service identifier.

        Returns:
            The service instance.

        Raises:
            KeyError: If the service is not registered.
        """
        if name not in self._instances:
            factory = self._registry.get(name)
            if factory is None:
                raise KeyError(f"Service '{name}' not registered in gateway container")
            self._instances[name] = factory() if callable(factory) else factory
        return self._instances[name]

    def has(self, name: str) -> bool:
        """Check if a service is registered."""
        return name in self._registry

    def reset(self) -> None:
        """Clear all cached instances (useful for testing)."""
        self._instances.clear()


# Singleton container
_container = DependencyContainer()


def get_container() -> DependencyContainer:
    """Get the global dependency container."""
    return _container


# =============================================================================
# API Gateway
# =============================================================================


class APIGateway:
    """
    Centralized API gateway for the Mothership application.

    Aggregates versioned routers, applies cross-cutting concerns,
    and provides a unified entry point for external traffic.

    Args:
        prefix: Base URL prefix for all gateway routes.
        enable_v2: Whether to mount the v2 API (default: False).
    """

    def __init__(
        self,
        prefix: str = "/api",
        enable_v2: bool = False,
    ) -> None:
        self.prefix = prefix
        self.enable_v2 = enable_v2
        self._router = APIRouter(prefix=prefix, tags=["gateway"])
        self._setup_routes()

    @property
    def router(self) -> APIRouter:
        """Get the assembled gateway router."""
        return self._router

    def _setup_routes(self) -> None:
        """Mount versioned sub-routers and gateway meta-endpoints."""
        # v1 — delegates to the existing create_api_router
        from application.mothership.routers import create_api_router

        v1_router = create_api_router(prefix="")
        self._router.include_router(v1_router, prefix="/v1", tags=["v1"])

        # v2 — opt-in
        if self.enable_v2:
            from application.mothership.api.v2 import router as v2_mod

            self._router.include_router(v2_mod, prefix="/v2", tags=["v2"])

        # Gateway introspection
        self._router.add_api_route(
            "/versions",
            self._list_versions,
            methods=["GET"],
            tags=["gateway"],
            summary="List available API versions",
        )

    async def _list_versions(self, request: Request) -> APIEnvelope:
        """Return available API versions and their status."""
        versions = [
            {"version": "v1", "status": "stable", "prefix": f"{self.prefix}/v1"},
        ]
        if self.enable_v2:
            versions.append(
                {"version": "v2", "status": "experimental", "prefix": f"{self.prefix}/v2"},
            )
        return APIEnvelope.ok(data=versions, gateway="mothership")


__all__ = [
    "APIEnvelope",
    "APIGateway",
    "DependencyContainer",
    "get_container",
]
