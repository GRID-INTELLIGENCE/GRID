"""Compatibility alias — canonical implementation lives in event_system_fixed.py."""

from .event_system_fixed import *  # noqa: F401, F403
from .event_system_fixed import (
    EventBus,
    EventPriority,
    Subscription,
    clear_all,
    get_eventbus,
    publish,
    subscribe,
    unsubscribe,
)

# Metrics stubs — the fixed module doesn't define prometheus counters at module level,
# but tests patch these names.  Provide patchable sentinels so the module resolves.
try:
    from prometheus_client import Counter, Gauge

    METRICS_ENABLED = True
    _subscriptions_created = Counter("eventbus_subscriptions_created_total", "Subscriptions created")
    _subscriptions_removed = Counter("eventbus_subscriptions_removed_total", "Subscriptions removed")
    _active_subscriptions = Gauge("eventbus_active_subscriptions", "Active subscriptions", ["event_type"])
except ImportError:
    METRICS_ENABLED = False
    _subscriptions_created = None  # type: ignore[assignment]
    _subscriptions_removed = None  # type: ignore[assignment]
    _active_subscriptions = None  # type: ignore[assignment]

__all__ = [
    "METRICS_ENABLED",
    "EventBus",
    "EventPriority",
    "Subscription",
    "_active_subscriptions",
    "_subscriptions_created",
    "_subscriptions_removed",
    "clear_all",
    "get_eventbus",
    "publish",
    "subscribe",
    "unsubscribe",
]
