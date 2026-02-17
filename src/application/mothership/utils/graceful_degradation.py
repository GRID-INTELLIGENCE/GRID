"""
Graceful Degradation Utilities for Chaos Resilience.

Provides fallback mechanisms and degraded operation modes when the system
is under heavy load or when critical components fail during chaos testing.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class DegradationLevel(str, Enum):
    """System degradation levels."""

    NORMAL = "normal"  # Full functionality
    DEGRADED = "degraded"  # Reduced functionality, fallbacks active
    CRITICAL = "critical"  # Minimal functionality, emergency mode
    FAILSAFE = "failsafe"  # Bare minimum operations only


class ServiceStatus(str, Enum):
    """Service operational status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DOWN = "down"


class ServiceHealth:
    """Health status of a service component."""

    def __init__(self, name: str, check_interval_seconds: float = 30.0):
        self.name = name
        self.status = ServiceStatus.HEALTHY
        self.last_check = 0.0
        self.check_interval = check_interval_seconds
        self.failure_count = 0
        self.success_count = 0
        self.metadata: dict[str, Any] = {}

    def record_success(self) -> None:
        """Record successful health check."""
        self.success_count += 1
        self.failure_count = 0
        if self.status != ServiceStatus.HEALTHY:
            logger.info(f"Service {self.name} recovered to healthy")
        self.status = ServiceStatus.HEALTHY
        self.last_check = asyncio.get_event_loop().time()

    def record_failure(self) -> None:
        """Record failed health check."""
        self.failure_count += 1
        self.success_count = 0

        # Progressive degradation
        if self.failure_count >= 5:
            if self.status != ServiceStatus.DOWN:
                logger.warning(f"Service {self.name} marked as down after {self.failure_count} failures")
            self.status = ServiceStatus.DOWN
        elif self.failure_count >= 3:
            if self.status != ServiceStatus.UNHEALTHY:
                logger.warning(f"Service {self.name} marked as unhealthy after {self.failure_count} failures")
            self.status = ServiceStatus.UNHEALTHY
        elif self.failure_count >= 1:
            if self.status != ServiceStatus.DEGRADED:
                logger.warning(f"Service {self.name} marked as degraded after {self.failure_count} failures")
            self.status = ServiceStatus.DEGRADED

        self.last_check = asyncio.get_event_loop().time()

    def needs_check(self) -> bool:
        """Check if health check is due."""
        return asyncio.get_event_loop().time() - self.last_check >= self.check_interval

    def is_available(self) -> bool:
        """Check if service is available for use."""
        return self.status in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED]


class DegradationManager:
    """
    Manages system degradation levels and fallback strategies.

    Automatically adjusts system behavior based on component health
    and resource availability.
    """

    def __init__(self):
        self._degradation_level = DegradationLevel.NORMAL
        self._services: dict[str, ServiceHealth] = {}
        self._fallback_strategies: dict[str, list[Callable]] = {}
        self._degradation_thresholds = {
            DegradationLevel.NORMAL: 0.8,  # 80% services healthy
            DegradationLevel.DEGRADED: 0.5,  # 50% services healthy
            DegradationLevel.CRITICAL: 0.2,  # 20% services healthy
        }

    def register_service(self, name: str, check_interval_seconds: float = 30.0) -> ServiceHealth:
        """Register a service for health monitoring."""
        if name not in self._services:
            self._services[name] = ServiceHealth(name, check_interval_seconds)
        return self._services[name]

    def update_service_health(self, name: str, healthy: bool) -> None:
        """Update service health status."""
        if name in self._services:
            if healthy:
                self._services[name].record_success()
            else:
                self._services[name].record_failure()
            self._update_degradation_level()

    def get_service_health(self, name: str) -> ServiceHealth | None:
        """Get service health information."""
        return self._services.get(name)

    @property
    def degradation_level(self) -> DegradationLevel:
        """Get current degradation level."""
        return self._degradation_level

    def _calculate_health_score(self) -> float:
        """Calculate overall system health score (0.0 to 1.0)."""
        if not self._services:
            return 1.0

        healthy_count = sum(1 for s in self._services.values() if s.is_available())
        return healthy_count / len(self._services)

    def _update_degradation_level(self) -> None:
        """Update system degradation level based on health scores."""
        health_score = self._calculate_health_score()

        new_level = DegradationLevel.NORMAL
        if health_score <= self._degradation_thresholds[DegradationLevel.CRITICAL]:
            new_level = DegradationLevel.CRITICAL
        elif health_score <= self._degradation_thresholds[DegradationLevel.DEGRADED]:
            new_level = DegradationLevel.DEGRADED

        if new_level != self._degradation_level:
            logger.info(f"System degradation level changed: {self._degradation_level} -> {new_level}")
            self._degradation_level = new_level

    def should_use_fallback(self, service_name: str) -> bool:
        """Check if fallback should be used for a service."""
        service = self._services.get(service_name)
        if service and not service.is_available():
            return True

        # Also use fallbacks in degraded/critical modes for non-essential services
        return self._degradation_level in [DegradationLevel.DEGRADED, DegradationLevel.CRITICAL]

    async def execute_with_fallback(
        self,
        primary_func: Callable,
        service_name: str,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Execute function with automatic fallback if service is degraded.

        Args:
            primary_func: Primary function to execute
            service_name: Service name for health checking
            *args: Arguments for primary function
            **kwargs: Keyword arguments for primary function

        Returns:
            Function result (primary or fallback)
        """
        try:
            # Try primary function first
            if not self.should_use_fallback(service_name):
                return await primary_func(*args, **kwargs)

            # Use fallback if available
            fallbacks = self._fallback_strategies.get(service_name, [])
            for fallback_func in fallbacks:
                try:
                    logger.info(f"Using fallback for service {service_name}")
                    return await fallback_func(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"Fallback failed for {service_name}: {e}")
                    continue

            # No working fallback, try primary anyway
            logger.warning(f"No working fallback for {service_name}, attempting primary")
            return await primary_func(*args, **kwargs)

        except Exception as e:
            # Record service failure
            self.update_service_health(service_name, False)

            # Try fallbacks if primary failed
            fallbacks = self._fallback_strategies.get(service_name, [])
            for fallback_func in fallbacks:
                try:
                    logger.warning(f"Primary failed for {service_name}, using fallback: {e}")
                    return await fallback_func(*args, **kwargs)
                except Exception as fallback_e:
                    logger.warning(f"Fallback also failed for {service_name}: {fallback_e}")
                    continue

            raise

    def register_fallback(self, service_name: str, fallback_func: Callable) -> None:
        """Register a fallback function for a service."""
        if service_name not in self._fallback_strategies:
            self._fallback_strategies[service_name] = []
        self._fallback_strategies[service_name].append(fallback_func)

    def get_system_status(self) -> dict[str, Any]:
        """Get comprehensive system status."""
        return {
            "degradation_level": self._degradation_level.value,
            "health_score": self._calculate_health_score(),
            "services": {
                name: {
                    "status": service.status.value,
                    "failure_count": service.failure_count,
                    "success_count": service.success_count,
                    "last_check": service.last_check,
                }
                for name, service in self._services.items()
            },
        }


# Global degradation manager instance
_degradation_manager = DegradationManager()


def get_degradation_manager() -> DegradationManager:
    """Get the global degradation manager instance."""
    return _degradation_manager


@asynccontextmanager
async def degraded_operation(
    service_name: str,
    fallback_result: Any = None,
) -> AsyncIterator[bool]:
    """
    Context manager for operations that may need fallback behavior.

    Usage:
        async with degraded_operation("database") as use_fallback:
            if use_fallback:
                return cached_result
            return await database_query()

    Args:
        service_name: Service to check for degradation
        fallback_result: Default result if operation fails

    Yields:
        True if fallback should be used, False for normal operation
    """
    manager = get_degradation_manager()
    use_fallback = manager.should_use_fallback(service_name)

    try:
        yield use_fallback
        # Operation succeeded
        manager.update_service_health(service_name, True)
    except Exception:
        # Operation failed
        manager.update_service_health(service_name, False)
        if use_fallback and fallback_result is not None:
            logger.info(f"Operation failed for {service_name}, using fallback result")
            # Note: We don't re-raise here since we're providing a fallback
        else:
            raise


# Common fallback functions
async def cached_fallback(cache_key: str, ttl: int = 300) -> Any:
    """Fallback that returns cached data if available."""
    # Implementation would depend on cache system
    # For now, return None to indicate no cached data
    logger.info(f"Cache fallback requested for key: {cache_key}")
    return None


async def degraded_fallback(message: str = "Service temporarily unavailable") -> dict[str, Any]:
    """Fallback that returns a degraded service response."""
    return {
        "status": "degraded",
        "message": message,
        "data": None,
    }


async def emergency_fallback() -> dict[str, Any]:
    """Emergency fallback for critical operations."""
    return {
        "status": "emergency",
        "message": "System operating in emergency mode",
        "data": None,
    }
