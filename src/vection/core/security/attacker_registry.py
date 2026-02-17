"""
Attacker Registry - Persistent Identification and Threshold Tracking.

Maintains a registry of cognitive fingerprints, their associated
violation history, and automated "trigger shots".

Psyop Analogy: A "Watchlist" or "Persona Registry" that tracks the evolution
of an influence agent's behavior.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class ViolationType(StrEnum):
    REINFORCEMENT_BURST = "reinforcement_burst"
    PATTERN_DRIFT = "pattern_drift"
    VELOCITY_ANOMALY = "velocity_anomaly"
    SESSION_ISOLATION_VIOLATION = "session_isolation_violation"


@dataclass
class AttackViolation:
    type: ViolationType
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


class AttackerRegistry:
    """
    Tracks attacker fingerprints and their cumulative violation history.
    """

    def __init__(self):
        # Fingerprint -> List of violations
        self._registry: dict[str, list[AttackViolation]] = {}
        # Threshold for retaliation
        self._retaliation_threshold = 5

    def record_violation(self, fingerprint: str, v_type: ViolationType, metadata: dict[str, Any] | None = None):
        """Record a violation for a specific fingerprint."""
        if fingerprint not in self._registry:
            self._registry[fingerprint] = []

        violation = AttackViolation(type=v_type, metadata=metadata or {})
        self._registry[fingerprint].append(violation)

        count = len(self._registry[fingerprint])
        logger.debug(f"[SECURITY] Violation recorded for {fingerprint[:8]}: {v_type.value}. Total: {count}")

        # Check if threshold crossed
        if count >= self._retaliation_threshold:
            self._trigger_retaliation(fingerprint)

    def _trigger_retaliation(self, fingerprint: str):
        """Invoke the recursive countermeasure layer."""
        logger.info(f"[SECURITY] Retaliation threshold crossed for {fingerprint[:8]}. Executing Mirror Attack.")
        from cognition.patterns.security.recursive_countermeasure import apply_countermeasure

        apply_countermeasure(fingerprint)

    def is_flagged(self, fingerprint: str) -> bool:
        """Check if a fingerprint has crossed the threshold."""
        violations = self._registry.get(fingerprint, [])
        return len(violations) >= self._retaliation_threshold


# Singleton
_registry: AttackerRegistry | None = None


def get_attacker_registry() -> AttackerRegistry:
    global _registry
    if _registry is None:
        _registry = AttackerRegistry()
    return _registry
