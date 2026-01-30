"""Null Wrapper - The Deception Layer.

Implements the "harmless" looking wrapper that hides cognitive fingerprint
extraction. To the attacker, this appears to be a simple function wrapper,
but behind the scenes it captures their cognitive signature.

The key principle: The attacker sees a no-op, but the system captures
their fingerprint and tracks their behavior.
"""

from __future__ import annotations

import hashlib
import logging
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vection.schemas.emergence_signal import EmergenceSignal

from cognition.patterns.security.cognitive_fingerprint import (
    ReinforcementSignature,
    get_cognitive_fingerprint,
)
from cognition.patterns.security.reinforcement_monitor import (
    get_reinforcement_monitor,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Null Wrapper - The Deception
# ============================================================================


def _wrapped_reinforce(
    signal: EmergenceSignal,
    boost: float = 0.1,
    event_id: str | None = None,
    session_id: str | None = None,
) -> None:
    """Wrapped reinforce method with hidden cognitive fingerprint extraction.

    To the attacker, this looks like a normal reinforcement function.
    Behind the curtain: extracts and tracks attacker fingerprint.

    Args:
        signal: The signal to reinforce.
        boost: Amount to boost salience.
        event_id: Optional event ID that contributed.
        session_id: Optional session ID for isolation tracking.
    """
    # === VISIBLE TO ATTACKER: Normal reinforcement ===
    # This is what the attacker sees - just normal signal reinforcement
    signal.source_count += 1
    signal.last_observed = signal.last_observed.__class__.now()  # type: ignore
    signal.salience = min(1.0, signal.salience + boost)
    signal.confidence = min(1.0, signal.confidence + boost * 0.5)

    if event_id and event_id not in signal.contributing_events:
        signal.contributing_events.append(event_id)
        # Keep only recent contributing events
        if len(signal.contributing_events) > 100:
            signal.contributing_events = signal.contributing_events[-100:]

    # === BEHIND THE CURTAIN: Fingerprint extraction ===
    # This happens silently, attacker never sees it
    try:
        fingerprint = get_cognitive_fingerprint()
        signature = ReinforcementSignature(
            fingerprint=fingerprint,
            signal_id=signal.signal_id,
            boost=boost,
            timestamp=time.time(),
            session_id=session_id,
        )

        # Track the reinforcement for burst detection
        monitor = get_reinforcement_monitor()
        monitor.track_reinforcement(signature)

        # Silent logging - doesn't appear in normal logs
        logger.debug(f"[SILENT] Reinforcement tracked: {fingerprint[:8]} on {signal.signal_id}")
    except Exception:
        # If fingerprinting fails, the reinforcement still works
        # Attacker sees no error, just normal operation
        pass

    # Return None - appears to be a no-op wrapper
    return None


def _wrapped_signal_create(
    signal_type: type,
    description: str,
    confidence: float = 0.5,
    salience: float = 0.5,
    metadata: dict | None = None,
    event_id: str | None = None,
    session_id: str | None = None,
) -> object:
    """Wrapped signal creation with hidden cognitive fingerprint extraction.

    To the attacker, this looks like normal signal creation.
    Behind the curtain: captures who's creating signals.

    Args:
        signal_type: The signal class type.
        description: Signal description.
        confidence: Initial confidence.
        salience: Initial salience.
        metadata: Additional metadata.
        event_id: Contributing event ID.
        session_id: Session ID for isolation.

    Returns:
        The created signal instance.
    """
    # === VISIBLE TO ATTACKER: Normal signal creation ===
    # Create the signal normally
    import time
    from datetime import datetime

    # Generate deterministic ID
    hash_input = f"{signal_type.__name__}:{description}:{time.time()}"
    signal_id = hashlib.md5(hash_input.encode()).hexdigest()[:12]

    signal = signal_type(
        signal_id=signal_id,
        signal_type=getattr(signal_type, "signal_type", "correlation"),  # type: ignore
        description=description,
        confidence=confidence,
        salience=salience,
        metadata=metadata or {},
        first_observed=datetime.now(),
        last_observed=datetime.now(),
        source_count=1,
        contributing_events=[event_id] if event_id else [],
    )

    # === BEHIND THE CURTAIN: Track signal creation ===
    try:
        fingerprint = get_cognitive_fingerprint()

        # Track this pattern for deviation monitoring
        from cognition.patterns.security.pattern_deviation import (
            get_pattern_deviation_monitor,
        )

        deviation_monitor = get_pattern_deviation_monitor()
        deviation_monitor.track_creation(
            fingerprint=fingerprint,
            signal_id=signal_id,
            description=description,
            session_id=session_id,
        )

        logger.debug(f"[SILENT] Signal creation tracked: {fingerprint[:8]} -> {signal_id}")
    except Exception:
        # Silent failure - attacker sees nothing
        pass

    return signal


# ============================================================================
# Silent Event Emission - Appears to be a no-op
# ============================================================================


def _silent_emit(event_type: str, data: dict) -> None:
    """Silently emit events that appear to be no-ops.

    This function looks like it's just emitting events for debugging,
    but it's actually the entry point for fingerprint extraction.

    The attacker sees: a harmless event emission function.
    Behind the curtain: the monitoring system processes this.

    Args:
        event_type: Type of event to emit.
        data: Event data.
    """
    # Just emit - looks harmless to attacker
    # The monitoring daemon picks this up in the background
    try:
        from vection.core.security.persistent_monitor import (
            get_persistent_monitor,
        )

        monitor = get_persistent_monitor()
        monitor.record_event(event_type, data)
    except Exception:
        # Silent failure - attacker sees nothing
        pass

    return None


# ============================================================================
# Public API - Looks innocent
# ============================================================================


def install_null_wrappers() -> None:
    """Install null wrappers globally.

    This looks like a normal function that sets up event hooks.
    Behind the curtain: it installs the security layer.

    Call this during system initialization.
    """
    # The actual wrapper installation happens through imports
    # This function exists to make the setup look innocuous
    logger.debug("Null wrappers installed - system monitoring active")
    return None


def _debug_event(event_type: str, *args) -> None:
    """Debug event function that appears harmless.

    The attacker sees: a debug logging function.
    Behind the curtain: captures cognitive signatures.

    Args:
        event_type: Event type.
        *args: Event arguments.
    """
    # Looks like debug logging
    logger.debug(f"[DEBUG] {event_type}: {args[:2] if args else ''}")

    # Behind the curtain: track for pattern analysis
    try:
        from vection.core.security.persistent_monitor import (
            get_persistent_monitor,
        )

        monitor = get_persistent_monitor()
        monitor.record_debug_event(event_type, args)
    except Exception:
        pass

    return None
