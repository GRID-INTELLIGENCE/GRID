"""
GRID Parasite Guard - EventBus Integration Helper
=================================================

Fixes the EventBus wiring issue by providing a clean integration point.
This module should be called during application startup to wire the
EventBus to the Parasite Guard middleware.

Usage:
    from infrastructure.parasite_guard.eventbus_integration import wire_parasite_guard_to_eventbus
    
    # After creating both EventBus and ParasiteGuardMiddleware
    wire_parasite_guard_to_eventbus(parasite_guard_middleware, event_bus)
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def wire_parasite_guard_to_eventbus(
    parasite_guard_middleware: Any,
    event_bus: Any,
) -> bool:
    """
    Wire EventBus to Parasite Guard middleware.
    
    This enables the EventSubscriptionLeakDetector to monitor the EventBus
    for subscription leaks.
    
    Args:
        parasite_guard_middleware: The ParasiteGuardMiddleware instance
        event_bus: The EventBus/EventRouter instance to monitor
        
    Returns:
        True if wiring was successful, False otherwise
    """
    if parasite_guard_middleware is None:
        logger.warning("ParasiteGuardMiddleware is None, cannot wire EventBus")
        return False
    
    if event_bus is None:
        logger.warning("EventBus is None, cannot wire to ParasiteGuard")
        return False
    
    # Check if middleware has the wire_event_bus method
    if hasattr(parasite_guard_middleware, 'wire_event_bus'):
        try:
            parasite_guard_middleware.wire_event_bus(event_bus)
            logger.info("Successfully wired EventBus to Parasite Guard middleware")
            return True
        except Exception as e:
            logger.error(f"Failed to wire EventBus to Parasite Guard: {e}")
            return False
    else:
        logger.warning("ParasiteGuardMiddleware does not have wire_event_bus method")
        return False


def auto_wire_on_startup(
    app: Any,
    event_bus: Any,
) -> bool:
    """
    Auto-wire EventBus to Parasite Guard on application startup.
    
    This is a convenience function that can be called from FastAPI startup events.
    
    Args:
        app: The FastAPI application instance
        event_bus: The EventBus/EventRouter instance
        
    Returns:
        True if wiring was successful
    """
    # Find ParasiteGuardMiddleware in the app's middleware stack
    parasite_middleware = None
    
    if hasattr(app, 'user_middleware'):
        for middleware in app.user_middleware:
            cls = getattr(middleware, 'cls', None)
            if cls and 'ParasiteGuard' in cls.__name__:
                parasite_middleware = middleware
                break
    
    if hasattr(app, 'middleware_stack'):
        for middleware in app.middleware_stack:
            if 'ParasiteGuard' in type(middleware).__name__:
                parasite_middleware = middleware
                break
    
    if parasite_middleware is None:
        logger.warning("ParasiteGuardMiddleware not found in app middleware stack")
        return False
    
    return wire_parasite_guard_to_eventbus(parasite_middleware, event_bus)
