"""
Unified Fabric - Health Checks
==============================
Lightweight health status helpers for integration validation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from . import get_event_bus
from .audit import get_audit_logger
from .safety_bridge import get_safety_bridge


@dataclass
class HealthStatus:
    """Container for component health status."""

    status: str
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _safe_call(func, default: dict[str, Any]) -> dict[str, Any]:
    try:
        return func() if callable(func) else default
    except Exception as exc:  # pragma: no cover - defensive
        return {**default, "error": str(exc)}


def get_health_status() -> dict[str, Any]:
    """Return health status for unified fabric components."""
    event_bus = get_event_bus()
    audit_logger = get_audit_logger()
    safety_bridge = get_safety_bridge()

    event_bus_status = _safe_call(event_bus.get_stats, {"running": False})
    safety_status = _safe_call(safety_bridge.get_stats, {"events_enabled": False})

    audit_status = {
        "log_dir": str(audit_logger.log_dir),
        "buffer_size": audit_logger.buffer_size,
        "buffered_entries": len(getattr(audit_logger, "_buffer", [])),
    }

    overall = "healthy"
    if not event_bus_status.get("running"):
        overall = "degraded"

    return {
        "status": overall,
        "event_bus": event_bus_status,
        "safety_bridge": safety_status,
        "audit_logger": audit_status,
    }


__all__ = ["HealthStatus", "get_health_status"]
