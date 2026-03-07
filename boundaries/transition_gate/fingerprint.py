"""
Cryptographic fingerprint utilities for the Transition Gate.

Provides three fingerprint primitives:
- user_fingerprint: HMAC-SHA256 over a shared secret + machine identity
- machine_fingerprint: SHA-256 over stable machine attributes
- payload_hash: SHA-256 over the serialized artifact payload

All functions are pure and deterministic given the same inputs.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import platform
from typing import Any


def compute_user_fingerprint(
    user_secret: str,
    *,
    machine_id: str | None = None,
    extra_context: str | None = None,
) -> str:
    """
    Compute HMAC-SHA256 user fingerprint.

    Binds the user's secret to the machine identity so the same secret
    on a different machine produces a different fingerprint.

    Args:
        user_secret: Shared secret known to both seal and verify sides.
        machine_id: Optional explicit machine identifier. If None, uses
                     compute_machine_fingerprint() output.
        extra_context: Optional additional context string to mix in
                       (e.g. session ID, partition label).

    Returns:
        Hex-encoded HMAC-SHA256 digest.
    """
    if not user_secret:
        raise ValueError("user_secret must not be empty")

    if machine_id is None:
        machine_id = compute_machine_fingerprint()

    message = f"transition_gate:user:{machine_id}"
    if extra_context:
        message = f"{message}:{extra_context}"

    return hmac.new(
        key=user_secret.encode("utf-8"),
        msg=message.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()


def compute_machine_fingerprint(
    *,
    node_name: str | None = None,
    platform_system: str | None = None,
    platform_machine: str | None = None,
    username: str | None = None,
) -> str:
    """
    Compute SHA-256 machine fingerprint from stable OS attributes.

    Uses platform node name, OS name, architecture, and current username
    to produce a stable-per-machine identifier. This is NOT a secret —
    it's a binding factor, not an authentication credential.

    Args:
        node_name: Override for platform.node().
        platform_system: Override for platform.system().
        platform_machine: Override for platform.machine().
        username: Override for os.getlogin().

    Returns:
        Hex-encoded SHA-256 digest.
    """
    _node = node_name or platform.node()
    _system = platform_system or platform.system()
    _machine = platform_machine or platform.machine()

    try:
        _user = username or os.getlogin()
    except OSError:
        # Fallback when running in a non-interactive context (e.g. service, CI)
        _user = username or os.environ.get("USERNAME", os.environ.get("USER", "unknown"))

    canonical = f"transition_gate:machine:{_node}:{_system}:{_machine}:{_user}"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_payload_hash(payload: Any) -> str:
    """
    Compute SHA-256 hash of the payload.

    The payload is serialized to canonical JSON (sorted keys, no extra
    whitespace) before hashing so the digest is reproducible regardless
    of dict insertion order.

    Args:
        payload: Any JSON-serializable object (dict, list, str, etc.).

    Returns:
        Hex-encoded SHA-256 digest.

    Raises:
        TypeError: If payload is not JSON-serializable.
    """
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def fingerprints_match(
    fingerprint_a: str,
    fingerprint_b: str,
) -> bool:
    """
    Timing-safe comparison of two fingerprint hex strings.

    Uses hmac.compare_digest to prevent timing side-channel attacks.

    Args:
        fingerprint_a: First fingerprint hex string.
        fingerprint_b: Second fingerprint hex string.

    Returns:
        True if fingerprints are identical.
    """
    return hmac.compare_digest(fingerprint_a, fingerprint_b)
