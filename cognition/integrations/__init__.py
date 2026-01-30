"""GRID Cognition Integration Module.

Provides secure integration adapters for cross-system communication.
Implements the AI Event Sanitization Protocol (AESP).
"""

from cognition.integrations.sanitized_event_adapter import (
    SanitizedCrossSystemEvent,
    SanitizedEventAdapter,
    get_sanitized_adapter,
    sanitize_event_payload,
)

__all__ = [
    "SanitizedEventAdapter",
    "sanitize_event_payload",
    "SanitizedCrossSystemEvent",
    "get_sanitized_adapter",
]
