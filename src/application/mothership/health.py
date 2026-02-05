"""Health check endpoints for parasitic leak remediation."""

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

logger = logging.getLogger(__name__)


async def check_eventbus_health() -> dict[str, Any]:
    """Check EventBus health."""
    try:
        from infrastructure.event_bus.event_system import EventBus

        # Check if EventBus is initialized
        # For now, return healthy if module can be imported
        return {
            "healthy": True,
            "active_subscriptions": 0,  # Will be updated when EventBus singleton is implemented
            "stale_subscriptions": 0,
        }
    except Exception as e:
        logger.error(f"EventBus health check failed: {e}")
        return {
            "healthy": False,
            "error": str(e),
        }


async def check_db_engine_health() -> dict[str, Any]:
    """Check database engine health."""
    try:
        from application.mothership.db.engine import get_async_engine

        engine = get_async_engine()
        pool_size = engine.pool.size() if engine.pool else 0
        checked_out = engine.pool.checkedout() if engine.pool else 0

        return {
            "healthy": True,
            "active_connections": pool_size,
            "checked_out": checked_out,
            "pool_utilization": checked_out / pool_size if pool_size > 0 else 0,
        }
    except Exception as e:
        logger.error(f"DB engine health check failed: {e}")
        return {
            "healthy": False,
            "error": str(e),
        }


async def check_metrics_health() -> dict[str, Any]:
    """Check metrics collection health."""
    try:
        from infrastructure.metrics import REGISTRY

        # Check if registry can be accessed
        return {
            "healthy": True,
            "metrics_count": len(list(REGISTRY.collect())),
        }
    except Exception as e:
        logger.error(f"Metrics health check failed: {e}")
        return {
            "healthy": False,
            "error": str(e),
        }


async def health_check() -> dict[str, Any]:
    """
    Comprehensive health check for parasitic leak remediation.

    Returns:
        Health status with component checks.
    """
    components = {
        "eventbus": await check_eventbus_health(),
        "db_engine": await check_db_engine_health(),
        "metrics": await check_metrics_health(),
    }

    status = "healthy" if all(c.get("healthy", False) for c in components.values()) else "unhealthy"

    return {
        "status": status,
        "components": components,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
