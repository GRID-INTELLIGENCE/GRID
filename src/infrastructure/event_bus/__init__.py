"""Event bus infrastructure for GRID."""


# Lazy imports to avoid dependency issues
def __getattr__(name: str):
    if name in ("EventBus", "get_eventbus", "subscribe", "unsubscribe", "publish", "clear_all"):
        from .event_system import (
            EventBus,
            clear_all,
            get_eventbus,
            publish,
            subscribe,
            unsubscribe,
        )

        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "EventBus",
    "get_eventbus",
    "subscribe",
    "unsubscribe",
    "publish",
    "clear_all",
]
