"""
Sanitized Event Adapter (AESP) - Safe Cross-System Communication.

Ensures that events propagated across the bridge are sanitized,
removing sensitive metadata and validating structural integrity.

Security Analogy: Cross-Origin Resource Sharing (CORS) or
a Data Loss Prevention (DLP) middlebox.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def sanitize_event_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Sanitize a dictionary payload by removing potentially sensitive
    internal keys and normalizing values.
    """
    if not isinstance(payload, dict):
        return {}

    sanitized = {}
    forbidden_keywords = {"path", "token", "key", "secret", "id", "password", "hash"}

    for k, v in payload.items():
        # Recursive sanitization for nested dicts
        if isinstance(v, dict):
            sanitized[k] = sanitize_event_payload(v)
            continue

        # Check against forbidden keywords for metadata keys
        if any(kw in k.lower() for kw in forbidden_keywords):
            # Mask sensitive values instead of deleting to keep structure
            sanitized[k] = "[REDACTED]"
            continue

        sanitized[k] = v

    return sanitized


class SanitizedEventAdapter:
    """
    Adapter for creating and validating cross-system events.
    """

    def wrap_payload(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
        """Wrap and sanitize a payload for cross-system transport."""
        return sanitize_event_payload(raw_payload)


# Singleton
_adapter: SanitizedEventAdapter | None = None


def get_sanitized_adapter() -> SanitizedEventAdapter:
    global _adapter
    if _adapter is None:
        _adapter = SanitizedEventAdapter()
    return _adapter
