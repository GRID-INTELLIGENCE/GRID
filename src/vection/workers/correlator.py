"""Correlator Worker - Cross-request correlation detection.

A background worker that detects correlations between events
across requests, sessions, and time windows. It identifies
patterns where events tend to occur together or in response
to each other.

Correlation Types Detected:
- Temporal: Events occurring close in time
- Causal: Events that seem to trigger other events
- Semantic: Events with similar content/meaning
- Behavioral: Events reflecting similar user behavior
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from vection.schemas.emergence_signal import EmergenceSignal, SignalType

logger = logging.getLogger(__name__)


class CorrelationType(StrEnum):
    """Types of correlation detected."""

    TEMPORAL = "temporal"  # Events close in time
    CAUSAL = "causal"  # A seems to cause B
    SEMANTIC = "semantic"  # Similar content
    BEHAVIORAL = "behavioral"  # Similar user patterns
    SEQUENCE = "sequence"  # Ordered occurrence
    CO_OCCURRENCE = "co_occurrence"  # Happening together


@dataclass
class CorrelationCandidate:
    """A potential correlation being evaluated."""

    candidate_id: str
    correlation_type: CorrelationType
    item_a: str
    item_b: str
    occurrence_count: int = 0
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    confidence_accumulator: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def age_seconds(self) -> float:
        """Get candidate age in seconds."""
        return time.time() - self.first_seen

    @property
    def confidence(self) -> float:
        """Calculate current confidence."""
        if self.occurrence_count < 2:
            return 0.0
        base = min(1.0, self.confidence_accumulator / self.occurrence_count)
        # Apply recency factor
        recency_penalty = min(0.3, (time.time() - self.last_seen) / 600.0)
        return max(0.0, base - recency_penalty)

    def add_occurrence(self, confidence_boost: float = 0.1) -> None:
        """Record another occurrence of this correlation."""
        self.occurrence_count += 1
        self.last_seen = time.time()
        self.confidence_accumulator += confidence_boost

    def should_emit(self, threshold: float = 0.5) -> bool:
        """Check if this candidate should become a signal."""
        return self.confidence >= threshold and self.occurrence_count >= 3


@dataclass
class EventObservation:
    """An observed event for correlation analysis."""

    event_id: str
    timestamp: float
    event_type: str
    session_id: str
    keys: list[str]
    data: dict[str, Any] = field(default_factory=dict)


class Correlator:
    """Background worker for cross-request correlation detection.

    Observes events and detects correlations between them,
    emitting EmergenceSignal instances when patterns are found.

    Usage:
        correlator = Correlator()
        await correlator.start()
        correlator.observe(event_data, session_id)
        # ... later ...
        signals = correlator.get_emitted_signals()
        await correlator.stop()
    """

    def __init__(
        self,
        temporal_window_seconds: float = 60.0,
        min_occurrences: int = 3,
        confidence_threshold: float = 0.5,
        max_observations: int = 1000,
        processing_interval: float = 5.0,
    ) -> None:
        """Initialize the correlator worker.

        Args:
            temporal_window_seconds: Window for temporal correlation.
            min_occurrences: Minimum occurrences for correlation.
            confidence_threshold: Threshold for emitting signals.
            max_observations: Maximum observations to retain.
            processing_interval: Seconds between processing runs.
        """
        self._temporal_window = temporal_window_seconds
        self._min_occurrences = min_occurrences
        self._confidence_threshold = confidence_threshold
        self._max_observations = max_observations
        self._processing_interval = processing_interval

        self._observations: deque[EventObservation] = deque(maxlen=max_observations)
        self._candidates: dict[str, CorrelationCandidate] = {}
        self._emitted_signals: deque[EmergenceSignal] = deque(maxlen=200)
        self._co_occurrence_matrix: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._sequence_tracker: dict[str, list[str]] = defaultdict(list)

        self._running = False
        self._task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()

        self._total_observations = 0
        self._total_correlations_found = 0
        self._started_at: datetime | None = None
        self._callbacks: list[Callable[[EmergenceSignal], None]] = []

        logger.info(f"Correlator initialized: window={temporal_window_seconds}s, threshold={confidence_threshold}")

    @property
    def is_running(self) -> bool:
        """Check if worker is running."""
        return self._running

    @property
    def observation_count(self) -> int:
        """Get current observation count."""
        return len(self._observations)

    @property
    def candidate_count(self) -> int:
        """Get current candidate count."""
        return len(self._candidates)

    async def start(self) -> None:
        """Start the correlator worker."""
        if self._running:
            logger.warning("Correlator already running")
            return

        self._running = True
        self._started_at = datetime.now(UTC)
        self._task = asyncio.create_task(self._processing_loop())
        logger.info("Correlator worker started")

    async def stop(self) -> None:
        """Stop the correlator worker."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        logger.info("Correlator worker stopped")

    def observe(
        self,
        event_data: dict[str, Any],
        session_id: str,
        event_id: str | None = None,
    ) -> None:
        """Observe an event for correlation analysis.

        Args:
            event_data: Event data dictionary.
            session_id: Session identifier.
            event_id: Optional event identifier.
        """
        event_id = event_id or self._generate_event_id()
        event_type = event_data.get("action") or event_data.get("type") or "unknown"
        keys = self._extract_keys(event_data)

        observation = EventObservation(
            event_id=event_id,
            timestamp=time.time(),
            event_type=str(event_type),
            session_id=session_id,
            keys=keys,
            data=event_data,
        )

        self._observations.append(observation)
        self._total_observations += 1

        # Update co-occurrence matrix immediately
        self._update_co_occurrence(observation)

        # Update sequence tracker
        self._sequence_tracker[session_id].append(event_type)
        if len(self._sequence_tracker[session_id]) > 20:
            self._sequence_tracker[session_id] = self._sequence_tracker[session_id][-20:]

        logger.debug(f"Observed event: {event_type} in session {session_id}")

    def on_correlation(self, callback: Callable[[EmergenceSignal], None]) -> None:
        """Register a callback for new correlation signals.

        Args:
            callback: Function called when correlation is detected.
        """
        self._callbacks.append(callback)

    def get_emitted_signals(self, limit: int = 50) -> list[EmergenceSignal]:
        """Get recently emitted correlation signals.

        Args:
            limit: Maximum signals to return.

        Returns:
            List of EmergenceSignal instances.
        """
        return list(self._emitted_signals)[-limit:]

    def get_candidates(self) -> list[dict[str, Any]]:
        """Get current correlation candidates.

        Returns:
            List of candidate information dictionaries.
        """
        return [
            {
                "candidate_id": c.candidate_id,
                "type": c.correlation_type.value,
                "item_a": c.item_a,
                "item_b": c.item_b,
                "occurrences": c.occurrence_count,
                "confidence": round(c.confidence, 3),
                "age_seconds": round(c.age_seconds, 1),
            }
            for c in self._candidates.values()
        ]

    def get_stats(self) -> dict[str, Any]:
        """Get correlator statistics.

        Returns:
            Dictionary with worker statistics.
        """
        return {
            "is_running": self._running,
            "total_observations": self._total_observations,
            "current_observations": len(self._observations),
            "candidates": len(self._candidates),
            "correlations_found": self._total_correlations_found,
            "emitted_signals": len(self._emitted_signals),
            "temporal_window": self._temporal_window,
            "confidence_threshold": self._confidence_threshold,
            "uptime_seconds": ((datetime.now(UTC) - self._started_at).total_seconds() if self._started_at else 0),
        }

    def reset(self) -> None:
        """Reset correlator state."""
        self._observations.clear()
        self._candidates.clear()
        self._emitted_signals.clear()
        self._co_occurrence_matrix.clear()
        self._sequence_tracker.clear()
        self._total_observations = 0
        self._total_correlations_found = 0
        logger.info("Correlator reset")

    # =========================================================================
    # Internal Processing
    # =========================================================================

    async def _processing_loop(self) -> None:
        """Main processing loop."""
        while self._running:
            try:
                await asyncio.sleep(self._processing_interval)
                await self._process_correlations()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Correlator processing error: {e}")

    async def _process_correlations(self) -> None:
        """Process observations for correlations."""
        async with self._lock:
            # Detect temporal correlations
            await self._detect_temporal_correlations()

            # Detect sequence correlations
            await self._detect_sequence_correlations()

            # Promote qualifying candidates
            await self._promote_candidates()

            # Decay and prune
            await self._decay_candidates()

    async def _detect_temporal_correlations(self) -> None:
        """Detect temporally correlated events."""
        recent = [o for o in self._observations if time.time() - o.timestamp < self._temporal_window]

        if len(recent) < 2:
            return

        # Find pairs occurring within time window
        for i, obs_a in enumerate(recent):
            for obs_b in recent[i + 1 :]:
                time_diff = abs(obs_b.timestamp - obs_a.timestamp)
                if time_diff > self._temporal_window:
                    continue

                # Same type events in same session
                if obs_a.event_type == obs_b.event_type and obs_a.session_id == obs_b.session_id:
                    continue

                candidate_id = self._make_candidate_id(
                    CorrelationType.TEMPORAL,
                    obs_a.event_type,
                    obs_b.event_type,
                )

                candidate = self._get_or_create_candidate(
                    candidate_id,
                    CorrelationType.TEMPORAL,
                    obs_a.event_type,
                    obs_b.event_type,
                )

                # Closer in time = higher confidence
                proximity_boost = 0.1 * (1.0 - time_diff / self._temporal_window)
                candidate.add_occurrence(proximity_boost)

    async def _detect_sequence_correlations(self) -> None:
        """Detect sequence patterns in sessions."""
        for sequence in self._sequence_tracker.values():
            if len(sequence) < 3:
                continue

            # Find repeated pairs
            pairs: dict[tuple[str, str], int] = defaultdict(int)
            for i in range(len(sequence) - 1):
                pair = (sequence[i], sequence[i + 1])
                if pair[0] != pair[1]:  # Skip self-loops
                    pairs[pair] += 1

            for pair, count in pairs.items():
                if count >= 2:
                    candidate_id = self._make_candidate_id(
                        CorrelationType.SEQUENCE,
                        pair[0],
                        pair[1],
                    )

                    candidate = self._get_or_create_candidate(
                        candidate_id,
                        CorrelationType.SEQUENCE,
                        pair[0],
                        pair[1],
                    )

                    candidate.add_occurrence(0.1 * count)

    async def _promote_candidates(self) -> None:
        """Promote qualifying candidates to signals."""
        to_promote = [c for c in self._candidates.values() if c.should_emit(self._confidence_threshold)]

        for candidate in to_promote:
            signal = self._create_signal(candidate)
            self._emitted_signals.append(signal)
            self._total_correlations_found += 1

            # Notify callbacks
            for callback in self._callbacks:
                try:
                    callback(signal)
                except Exception as e:
                    logger.warning(f"Correlation callback error: {e}")

            # Remove promoted candidate
            del self._candidates[candidate.candidate_id]

            logger.debug(
                f"Correlation detected: {candidate.item_a} ↔ {candidate.item_b} "
                f"(type={candidate.correlation_type.value}, conf={candidate.confidence:.2f})"
            )

    async def _decay_candidates(self) -> None:
        """Decay and remove stale candidates."""
        stale = [
            cid
            for cid, c in self._candidates.items()
            if c.age_seconds > 3600 and c.confidence < 0.2  # 1 hour stale
        ]

        for cid in stale:
            del self._candidates[cid]

        # Prune co-occurrence matrix
        for key_a in list(self._co_occurrence_matrix.keys()):
            for key_b in list(self._co_occurrence_matrix[key_a].keys()):
                self._co_occurrence_matrix[key_a][key_b] = int(self._co_occurrence_matrix[key_a][key_b] * 0.95)
                if self._co_occurrence_matrix[key_a][key_b] < 1:
                    del self._co_occurrence_matrix[key_a][key_b]
            if not self._co_occurrence_matrix[key_a]:
                del self._co_occurrence_matrix[key_a]

    def _generate_event_id(self) -> str:
        """Generate a unique event ID."""
        hash_input = f"{time.time()}:{self._total_observations}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:10]  # noqa: S324 non-cryptographic use

    def _extract_keys(self, event_data: dict[str, Any]) -> list[str]:
        """Extract correlation keys from event data."""
        keys: list[str] = []

        keys.extend(
            f"{key}:{event_data[key]}"
            for key in ("action", "type", "intent", "topic", "category")
            if key in event_data and event_data[key]
        )

        return keys

    def _update_co_occurrence(self, observation: EventObservation) -> None:
        """Update co-occurrence matrix."""
        keys = observation.keys
        for i, key_a in enumerate(keys):
            for key_b in keys[i + 1 :]:
                self._co_occurrence_matrix[key_a][key_b] += 1
                self._co_occurrence_matrix[key_b][key_a] += 1

    def _make_candidate_id(
        self,
        correlation_type: CorrelationType,
        item_a: str,
        item_b: str,
    ) -> str:
        """Generate a deterministic candidate ID."""
        # Normalize order for consistency
        items = sorted([item_a, item_b])
        hash_input = f"{correlation_type.value}:{items[0]}:{items[1]}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]  # noqa: S324 non-cryptographic use

    def _get_or_create_candidate(
        self,
        candidate_id: str,
        correlation_type: CorrelationType,
        item_a: str,
        item_b: str,
    ) -> CorrelationCandidate:
        """Get existing candidate or create new one."""
        if candidate_id not in self._candidates:
            self._candidates[candidate_id] = CorrelationCandidate(
                candidate_id=candidate_id,
                correlation_type=correlation_type,
                item_a=item_a,
                item_b=item_b,
            )
        return self._candidates[candidate_id]

    def _create_signal(self, candidate: CorrelationCandidate) -> EmergenceSignal:
        """Create an EmergenceSignal from a candidate."""
        description = f"{candidate.correlation_type.value.title()} correlation: {candidate.item_a} ↔ {candidate.item_b}"

        return EmergenceSignal.create(
            signal_type=SignalType.CORRELATION,
            description=description,
            confidence=candidate.confidence,
            salience=min(0.9, candidate.confidence + 0.1),
            metadata={
                "correlation_type": candidate.correlation_type.value,
                "item_a": candidate.item_a,
                "item_b": candidate.item_b,
                "occurrence_count": candidate.occurrence_count,
            },
        )


# Module-level singleton
_correlator: Correlator | None = None


def get_correlator() -> Correlator:
    """Get the global correlator instance.

    Returns:
        Correlator singleton.
    """
    global _correlator
    if _correlator is None:
        _correlator = Correlator()
    return _correlator
