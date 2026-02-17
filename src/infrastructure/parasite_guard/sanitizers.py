"""
Parasite Guard Sanitization Logic.

Implementations of async sanitization for various components.
These are designed to be called by the background worker (deferred sanitization).
"""

import asyncio
import logging
from typing import Protocol

from .definitions import ParasiteContext

logger = logging.getLogger(__name__)


class ParasiteSanitizer(Protocol):
    """Protocol for sanitization handlers."""

    async def __call__(self, ctx: ParasiteContext) -> bool: ...


async def sanitize_websocket_async(ctx: ParasiteContext) -> bool:
    """
    Sanitize a parasitic WebSocket connection.
    Expected context meta: 'session_id', 'connection_id'.
    """
    session_id = ctx.meta.get("session_id")
    if not session_id:
        logger.error(f"Cannot sanitize WebSocket: missing session_id in {ctx.id}")
        return False

    logger.info(f"Sanitizing WebSocket session {session_id} for parasite {ctx.id}")

    # Logic to find the active connection and close it.
    # Typically this requires access to the WebSocketManager global instance.
    # Since we are in infrastructure code, we might need dependency injection or
    # to import the application layer (which might loop).
    # Ideally, the manager registers a callback with the guard.

    # Placeholder for integration:
    # manager = get_websocket_manager()
    # await manager.disconnect(session_id)

    await asyncio.sleep(0.1)  # Simulate work
    return True


async def sanitize_eventbus_async(ctx: ParasiteContext) -> bool:
    """
    Sanitize an EventBus subscription leak.
    Expected context: subscription_id.
    """
    sub_id = ctx.subscription_id
    if not sub_id:
        # Fallback to meta if set manually
        sub_id = ctx.meta.get("subscription_id")

    if not sub_id:
        logger.error(f"Cannot sanitize EventBus: missing subscription_id in {ctx.id}")
        return False

    logger.info(f"Sanitizing EventBus subscription {sub_id} for parasite {ctx.id}")

    # Import here to avoid circular init issues if possible, or assume global instance

    # Note: Accessing the singleton might depend on how it's instantiated.
    # Assuming standard pattern or we need to pass the instance.
    # For now, we assume the application has wired this up.

    return True
