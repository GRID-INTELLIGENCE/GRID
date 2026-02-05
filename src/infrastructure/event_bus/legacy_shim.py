"""Legacy EventBus shim for backward compatibility."""

import logging
from typing import Any, Callable

from .event_system import EventBus, Subscription

logger = logging.getLogger(__name__)


async def subscribe_legacy(event: str, handler: Callable[[Any], None]) -> Subscription:
    """
    Legacy subscribe API for backward compatibility.

    Automatically manages subscription lifecycle and logs deprecation warning.

    Args:
        event: Event type to subscribe to
        handler: Handler function for events

    Returns:
        Subscription object

    Warning:
        This is a legacy API. Use subscribe() instead.
    """
    logger.warning(
        "subscribe_legacy is deprecated; use subscribe() instead. "
        "This will be removed in a future version."
    )

    # Get EventBus instance and subscribe
    from . import get_eventbus

    bus = await get_eventbus()
    return await bus.subscribe(event, handler)


__all__ = ["subscribe_legacy"]
