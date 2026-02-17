"""Prometheus metrics infrastructure for parasitic leak remediation."""

from prometheus_client import CollectorRegistry, Counter, Gauge

# Global metrics registry
REGISTRY = CollectorRegistry()

# EventBus Metrics
eventbus_subscriptions_created = Counter(
    "eventbus_subscriptions_created",
    "Total EventBus subscriptions created",
    registry=REGISTRY,
)

eventbus_subscriptions_removed = Counter(
    "eventbus_subscriptions_removed",
    "Total EventBus subscriptions removed",
    registry=REGISTRY,
)

eventbus_active_subscriptions = Gauge(
    "eventbus_active_subscriptions",
    "Current active EventBus subscriptions",
    registry=REGISTRY,
)

# Database Engine Metrics
db_active_connections = Gauge(
    "db_active_connections",
    "Current active database connections",
    registry=REGISTRY,
)

db_disposal_attempts = Counter(
    "db_disposal_attempts",
    "Total database engine disposal attempts",
    registry=REGISTRY,
)

db_disposal_errors = Counter(
    "db_disposal_errors",
    "Total database engine disposal errors",
    registry=REGISTRY,
)

__all__ = [
    "REGISTRY",
    "eventbus_subscriptions_created",
    "eventbus_subscriptions_removed",
    "eventbus_active_subscriptions",
    "db_active_connections",
    "db_disposal_attempts",
    "db_disposal_errors",
]
