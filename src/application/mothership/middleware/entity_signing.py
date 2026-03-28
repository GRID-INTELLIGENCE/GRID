"""HMAC-SHA256 signing and verification for X-Entity-Id headers.

Prevents entity spoofing by requiring a valid signature when an entity
ID is explicitly claimed via the X-Entity-Id header. Unsigned claims
silently fall through to IP/API-key resolution.
"""

from __future__ import annotations

import hashlib
import hmac
import time

ENTITY_SIGNATURE_MAX_AGE = 300  # 5-minute replay window


def sign_entity_id(entity_id: str, secret: str, timestamp: int | None = None) -> tuple[str, int]:
    """Return (signature_hex, timestamp) for an entity ID."""
    ts = timestamp or int(time.time())
    msg = f"{entity_id}:{ts}".encode()
    sig = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()
    return sig, ts


def verify_entity_signature(
    entity_id: str,
    signature: str,
    timestamp: str,
    secret: str,
) -> bool:
    """Verify HMAC signature. Reject if expired or invalid."""
    try:
        ts = int(timestamp)
    except (ValueError, TypeError):
        return False
    if abs(time.time() - ts) > ENTITY_SIGNATURE_MAX_AGE:
        return False
    expected = hmac.new(secret.encode(), f"{entity_id}:{ts}".encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)
