"""Cognitive Fingerprint - Attacker Identification.

Extracts unique cognitive fingerprints from call stack patterns.
The fingerprint is stable per attacker but varies across different
code paths, enabling long-term tracking.

The key principle: Each attacker has a unique cognitive signature
based on how they interact with the system.
"""

from __future__ import annotations

import hashlib
import inspect
import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# ============================================================================
# Data Structures
# ============================================================================


@dataclass
class ReinforcementSignature:
    """Signature of a reinforcement action."""

    fingerprint: str
    signal_id: str
    boost: float
    timestamp: float
    session_id: str | None = None

    @property
    def is_burst(self) -> bool:
        """Check if this appears to be a burst attack."""
        # Burst attacks have high boost values
        return self.boost > 0.3


@dataclass
class FingerprintProfile:
    """Profile for a cognitive fingerprint."""

    fingerprint: str
    first_seen: float
    last_seen: float
    reinforcement_count: int
    creation_count: int
    violation_count: int
    sessions_touched: set[str]
    signal_ids: set[str]
    burst_count: int
    avg_reinforcement_interval: float

    @property
    def age_seconds(self) -> float:
        """Get age in seconds."""
        return time.time() - self.first_seen

    @property
    def is_suspicious(self) -> bool:
        """Check if this fingerprint shows suspicious behavior."""
        # Suspicious if: high burst rate, many sessions touched, or many violations
        return self.burst_count > 3 or len(self.sessions_touched) > 3 or self.violation_count > 2

    @property
    def burst_ratio(self) -> float:
        """Get ratio of burst reinforcements."""
        if self.reinforcement_count == 0:
            return 0.0
        return self.burst_count / self.reinforcement_count


# ============================================================================
# Cognitive Fingerprint Extractor
# ============================================================================


class CognitiveFingerprintExtractor:
    """Extracts unique cognitive fingerprints from call patterns."""

    _lock = threading.Lock()
    _fingerprint_cache: dict[str, str] = {}

    def __init__(self, cache_ttl: float = 300.0) -> None:
        """Initialize the fingerprint extractor.

        Args:
            cache_ttl: Time-to-live for cached fingerprints in seconds.
        """
        self._cache_ttl = cache_ttl
        self._cache_timestamps: dict[str, float] = {}

    def extract(self) -> str:
        """Extract cognitive fingerprint from current call stack.

        The fingerprint is generated from:
        - Caller module and line number
        - Reinforcement interval patterns
        - Session isolation violation attempts
        - Thread ID

        Returns:
            16-character hex string representing the fingerprint.
        """
        stack = inspect.stack()

        # Extract caller information (skip this function and its caller)
        caller_frame = stack[2] if len(stack) > 2 else stack[0]

        fingerprint_components = {
            # Module-level identification
            "module": caller_frame.filename,
            "line": caller_frame.lineno,
            "function": caller_frame.function,
            # Contextual information
            "thread_id": threading.get_ident(),
            "process_id": id(self),
            # Temporal patterns
            "timestamp_bucket": int(time.time() // 60),  # 1-minute buckets
            # Call stack depth (indicates recursion/automation)
            "stack_depth": len(stack),
        }

        # Generate stable hash
        hash_input = "|".join(f"{k}:{v}" for k, v in fingerprint_components.items())
        full_hash = hashlib.sha256(hash_input.encode()).hexdigest()

        # Return 16-character prefix for efficiency
        return full_hash[:16]

    def get_fingerprint_with_context(self, signal_id: str | None = None) -> str:
        """Get fingerprint with additional context.

        Args:
            signal_id: Optional signal ID being reinforced.

        Returns:
            Fingerprint string.
        """
        base_fingerprint = self.extract()

        # Add signal-specific context
        if signal_id:
            hash_input = f"{base_fingerprint}:{signal_id[:8]}"
            return hashlib.md5(hash_input.encode()).hexdigest()[:16]

        return base_fingerprint


# ============================================================================
# Fingerprint Registry
# ============================================================================


class FingerprintRegistry:
    """Registry for tracking cognitive fingerprints."""

    _lock = threading.Lock()
    _profiles: dict[str, FingerprintProfile] = {}
    _reinforcement_history: dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
    _creation_history: dict[str, deque] = defaultdict(lambda: deque(maxlen=50))

    def __init__(self) -> None:
        """Initialize the registry."""
        self._extractor = CognitiveFingerprintExtractor()

    def get_fingerprint(self, signal_id: str | None = None) -> str:
        """Get current cognitive fingerprint.

        Args:
            signal_id: Optional signal ID for context.

        Returns:
            Fingerprint string.
        """
        return self._extractor.get_fingerprint_with_context(signal_id)

    def record_reinforcement(
        self,
        fingerprint: str,
        signal_id: str,
        boost: float,
        session_id: str | None = None,
    ) -> FingerprintProfile:
        """Record a reinforcement action.

        Args:
            fingerprint: The cognitive fingerprint.
            signal_id: Signal being reinforced.
            boost: Boost amount.
            session_id: Session ID.

        Returns:
            Updated fingerprint profile.
        """
        now = time.time()

        with self._lock:
            # Get or create profile
            profile = self._profiles.get(fingerprint)
            if profile is None:
                profile = FingerprintProfile(
                    fingerprint=fingerprint,
                    first_seen=now,
                    last_seen=now,
                    reinforcement_count=0,
                    creation_count=0,
                    violation_count=0,
                    sessions_touched=set(),
                    signal_ids=set(),
                    burst_count=0,
                    avg_reinforcement_interval=0.0,
                )
                self._profiles[fingerprint] = profile

            # Update profile
            profile.last_seen = now
            profile.reinforcement_count += 1
            profile.signal_ids.add(signal_id)
            if session_id:
                profile.sessions_touched.add(session_id)

            # Track burst behavior
            if boost > 0.3:
                profile.burst_count += 1

            # Record history
            self._reinforcement_history[fingerprint].append(
                {
                    "timestamp": now,
                    "signal_id": signal_id,
                    "boost": boost,
                    "session_id": session_id,
                }
            )

            # Calculate average interval
            history = self._reinforcement_history[fingerprint]
            if len(history) >= 2:
                intervals = [history[i]["timestamp"] - history[i - 1]["timestamp"] for i in range(1, len(history))]
                profile.avg_reinforcement_interval = sum(intervals) / len(intervals)

        return profile

    def record_creation(
        self,
        fingerprint: str,
        signal_id: str,
        description: str,
        session_id: str | None = None,
    ) -> FingerprintProfile:
        """Record a signal creation.

        Args:
            fingerprint: The cognitive fingerprint.
            signal_id: Created signal ID.
            description: Signal description.
            session_id: Session ID.

        Returns:
            Updated fingerprint profile.
        """
        now = time.time()

        with self._lock:
            # Get or create profile
            profile = self._profiles.get(fingerprint)
            if profile is None:
                profile = FingerprintProfile(
                    fingerprint=fingerprint,
                    first_seen=now,
                    last_seen=now,
                    reinforcement_count=0,
                    creation_count=0,
                    violation_count=0,
                    sessions_touched=set(),
                    signal_ids=set(),
                    burst_count=0,
                    avg_reinforcement_interval=0.0,
                )
                self._profiles[fingerprint] = profile

            # Update profile
            profile.last_seen = now
            profile.creation_count += 1
            profile.signal_ids.add(signal_id)
            if session_id:
                profile.sessions_touched.add(session_id)

            # Record history
            self._creation_history[fingerprint].append(
                {
                    "timestamp": now,
                    "signal_id": signal_id,
                    "description": description,
                    "session_id": session_id,
                }
            )

        return profile

    def record_violation(
        self,
        fingerprint: str,
        violation_type: str,
        details: dict,
    ) -> None:
        """Record a security violation.

        Args:
            fingerprint: The cognitive fingerprint.
            violation_type: Type of violation.
            details: Violation details.
        """
        with self._lock:
            profile = self._profiles.get(fingerprint)
            if profile:
                profile.violation_count += 1

    def get_profile(self, fingerprint: str) -> FingerprintProfile | None:
        """Get fingerprint profile.

        Args:
            fingerprint: Fingerprint to query.

        Returns:
            FingerprintProfile or None.
        """
        return self._profiles.get(fingerprint)

    def get_all_profiles(self) -> dict[str, FingerprintProfile]:
        """Get all fingerprint profiles.

        Returns:
            Dictionary mapping fingerprints to profiles.
        """
        return dict(self._profiles)

    def cleanup_stale_profiles(self, max_age_hours: float = 24.0) -> int:
        """Remove stale fingerprint profiles.

        Args:
            max_age_hours: Maximum age in hours.

        Returns:
            Number of profiles removed.
        """
        time.time()
        max_age_seconds = max_age_hours * 3600
        to_remove = []

        with self._lock:
            for fingerprint, profile in self._profiles.items():
                if profile.age_seconds > max_age_seconds:
                    to_remove.append(fingerprint)

            for fingerprint in to_remove:
                del self._profiles[fingerprint]
                if fingerprint in self._reinforcement_history:
                    del self._reinforcement_history[fingerprint]
                if fingerprint in self._creation_history:
                    del self._creation_history[fingerprint]

        return len(to_remove)


# ============================================================================
# Module-level API
# ============================================================================

_registry: FingerprintRegistry | None = None
_registry_lock = threading.Lock()


def get_fingerprint_registry() -> FingerprintRegistry:
    """Get the global fingerprint registry.

    Returns:
        FingerprintRegistry singleton.
    """
    global _registry
    with _registry_lock:
        if _registry is None:
            _registry = FingerprintRegistry()
        return _registry


def get_cognitive_fingerprint(signal_id: str | None = None) -> str:
    """Get current cognitive fingerprint.

    This is the public API used by the null wrapper.

    Args:
        signal_id: Optional signal ID for context.

    Returns:
        16-character fingerprint string.
    """
    registry = get_fingerprint_registry()
    return registry.get_fingerprint(signal_id)


def track_reinforcement(
    fingerprint: str,
    signal_id: str,
    boost: float,
    session_id: str | None = None,
) -> FingerprintProfile:
    """Track a reinforcement action.

    Args:
        fingerprint: Cognitive fingerprint.
        signal_id: Signal being reinforced.
        boost: Boost amount.
        session_id: Session ID.

    Returns:
        Updated fingerprint profile.
    """
    registry = get_fingerprint_registry()
    return registry.record_reinforcement(
        fingerprint=fingerprint,
        signal_id=signal_id,
        boost=boost,
        session_id=session_id,
    )


def track_creation(
    fingerprint: str,
    signal_id: str,
    description: str,
    session_id: str | None = None,
) -> FingerprintProfile:
    """Track a signal creation.

    Args:
        fingerprint: Cognitive fingerprint.
        signal_id: Created signal ID.
        description: Signal description.
        session_id: Session ID.

    Returns:
        Updated fingerprint profile.
    """
    registry = get_fingerprint_registry()
    return registry.record_creation(
        fingerprint=fingerprint,
        signal_id=signal_id,
        description=description,
        session_id=session_id,
    )
