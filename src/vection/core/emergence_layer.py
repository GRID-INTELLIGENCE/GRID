"""EmergenceLayer - Pattern discovery without explicit rules.

Discovers patterns through observation of request streams rather than
through predefined rules. Uses statistical co-occurrence, temporal
clustering, and signal correlation to surface emergent context.

The key insight: patterns emerge from behavior, not configuration.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol, TypeVar

from vection.schemas.emergence_signal import EmergenceSignal, SignalType

logger = logging.getLogger(__name__)

T = TypeVar("T")


class Observable(Protocol):
    """Protocol for observable entities."""

    def to_dict(self) -> dict[str, Any]: ...


@dataclass
class ObservationWindow:
    """A sliding window of observations for pattern detection."""

    max_size: int = 100
    max_age_seconds: float = 3600.0
    observations: deque[tuple[float, dict[str, Any]]] = field(default_factory=lambda: deque(maxlen=100))

    def add(self, data: dict[str, Any]) -> None:
        """Add an observation with current timestamp."""
        self.observations.append((time.time(), data))

    def get_recent(self, seconds: float = 300.0) -> list[dict[str, Any]]:
        """Get observations from the last N seconds."""
        cutoff = time.time() - seconds
        return [data for ts, data in self.observations if ts >= cutoff]

    def prune_stale(self) -> int:
        """Remove observations older than max_age_seconds."""
        cutoff = time.time() - self.max_age_seconds
        initial_size = len(self.observations)
        self.observations = deque(
            [(ts, data) for ts, data in self.observations if ts >= cutoff],
            maxlen=self.max_size,
        )
        return initial_size - len(self.observations)


@dataclass
class PatternCandidate:
    """A candidate pattern being evaluated for emergence."""

    pattern_id: str
    pattern_type: SignalType
    description: str
    evidence: list[str] = field(default_factory=list)
    support_count: int = 0
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    confidence_accumulator: float = 0.0

    @property
    def age_seconds(self) -> float:
        """How long this pattern has been tracked."""
        return time.time() - self.first_seen

    @property
    def recency_seconds(self) -> float:
        """Time since last supporting evidence."""
        return time.time() - self.last_seen

    @property
    def confidence(self) -> float:
        """Current confidence based on accumulated evidence."""
        if self.support_count == 0:
            return 0.0
        base_confidence = min(1.0, self.confidence_accumulator / self.support_count)
        # Apply recency decay
        recency_penalty = min(0.5, self.recency_seconds / 600.0)  # 10 min decay
        return max(0.0, base_confidence - recency_penalty)

    def add_evidence(self, evidence_id: str, confidence_boost: float = 0.1) -> None:
        """Add supporting evidence for this pattern."""
        self.evidence.append(evidence_id)
        self.support_count += 1
        self.last_seen = time.time()
        self.confidence_accumulator += confidence_boost

        # Cap evidence list
        if len(self.evidence) > 50:
            self.evidence = self.evidence[-50:]

    def should_emerge(self, threshold: float = 0.5) -> bool:
        """Check if pattern has sufficient evidence to emerge."""
        return self.confidence >= threshold and self.support_count >= 3


class EmergenceLayer:
    """Pattern discovery without explicit rules.

    Discovers patterns by observing signals and finding:
    - Co-occurrence patterns (things that happen together)
    - Sequence patterns (things that happen in order)
    - Cluster patterns (groups of similar events)
    - Deviation patterns (anomalies from baseline)
    - Recurrence patterns (periodic behavior)

    Usage:
        layer = EmergenceLayer()
        await layer.observe({"action": "search", "topic": "auth"})
        signals = await layer.query_emergent("authentication")
        salience = await layer.get_salience_map()
    """

    def __init__(
        self,
        observation_window_size: int = 100,
        pattern_threshold: float = 0.5,
        min_pattern_support: int = 3,
        decay_interval_seconds: float = 300.0,
    ) -> None:
        """Initialize the emergence layer.

        Args:
            observation_window_size: Max observations to retain.
            pattern_threshold: Confidence threshold for emergence.
            min_pattern_support: Minimum evidence count for patterns.
            decay_interval_seconds: How often to decay patterns.
        """
        self._observation_window = ObservationWindow(max_size=observation_window_size)
        self._pattern_candidates: dict[str, PatternCandidate] = {}
        self._emerged_signals: deque[EmergenceSignal] = deque(maxlen=200)
        self._salience_scores: dict[str, float] = {}
        self._co_occurrence_matrix: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._sequence_tracker: deque[str] = deque(maxlen=50)
        self._pattern_threshold = pattern_threshold
        self._min_pattern_support = min_pattern_support
        self._decay_interval = decay_interval_seconds
        self._last_decay_time = time.time()
        self._observation_hooks: list[Callable[[dict[str, Any]], None]] = []
        self._total_observations = 0
        self._lock = asyncio.Lock()

        logger.info(f"EmergenceLayer initialized: threshold={pattern_threshold}, min_support={min_pattern_support}")

    async def observe(self, signal: Any, event_id: str | None = None) -> None:
        """Observe a signal without blocking.

        This is the primary entry point for feeding data to the emergence layer.
        Patterns are discovered asynchronously from observations.

        Args:
            signal: The signal to observe (dict or object with to_dict).
            event_id: Optional event identifier for tracing.
        """
        async with self._lock:
            # Normalize signal to dict
            data: dict[str, Any]
            if isinstance(signal, dict):
                data = dict(signal)  # Copy to avoid mutation
            elif hasattr(signal, "to_dict") and callable(signal.to_dict):
                result = signal.to_dict()
                data = dict(result) if isinstance(result, dict) else {"raw": str(signal)}
            else:
                data = {"raw": str(signal)}

            # Add observation metadata
            data["_observed_at"] = time.time()
            data["_event_id"] = event_id or self._generate_event_id()

            # Store observation
            self._observation_window.add(data)
            self._total_observations += 1

            # Update tracking structures
            self._update_co_occurrence(data)
            self._update_sequence(data)

            # Run hooks
            for hook in self._observation_hooks:
                try:
                    hook(data)
                except Exception as e:
                    logger.warning(f"Observation hook failed: {e}")

            # Periodic pattern evaluation and decay
            await self._maybe_evaluate_patterns()
            await self._maybe_decay()

    async def query_emergent(self, query: str) -> list[EmergenceSignal]:
        """What has emerged relevant to this query?

        Searches accumulated emerged signals for patterns matching
        the query string.

        Args:
            query: Query string to match against patterns.

        Returns:
            List of EmergenceSignal instances matching the query.
        """
        if not query:
            return []

        matches: list[tuple[float, EmergenceSignal]] = []

        for signal in self._emerged_signals:
            score = signal.matches_query(query)
            if score > 0.2:
                matches.append((score, signal))

        # Sort by match score
        matches.sort(key=lambda x: x[0], reverse=True)
        return [signal for _, signal in matches[:10]]

    async def get_salience_map(self) -> dict[str, float]:
        """What matters right now based on emergence?

        Returns a map of topics/patterns to their current salience scores.
        Higher scores indicate more recently active and confident patterns.

        Returns:
            Dictionary mapping pattern descriptions to salience (0.0-1.0).
        """
        salience: dict[str, float] = {}

        # From emerged signals
        for signal in self._emerged_signals:
            key = signal.description[:50]
            salience[key] = max(salience.get(key, 0.0), signal.effective_salience)

        # From pattern candidates close to emergence
        for candidate in self._pattern_candidates.values():
            if candidate.confidence > 0.3:
                key = candidate.description[:50]
                salience[key] = max(salience.get(key, 0.0), candidate.confidence * 0.7)

        # Sort and return top entries
        sorted_salience = sorted(salience.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_salience[:20])

    async def get_emerged_signals(self, min_salience: float = 0.0) -> list[EmergenceSignal]:
        """Get all emerged signals above a salience threshold.

        Args:
            min_salience: Minimum effective salience to include.

        Returns:
            List of qualifying EmergenceSignal instances.
        """
        return [s for s in self._emerged_signals if s.effective_salience >= min_salience]

    async def get_candidate_patterns(self) -> list[dict[str, Any]]:
        """Get current pattern candidates (not yet emerged).

        Returns:
            List of candidate pattern info dictionaries.
        """
        return [
            {
                "pattern_id": c.pattern_id,
                "type": c.pattern_type.value,
                "description": c.description,
                "confidence": round(c.confidence, 3),
                "support_count": c.support_count,
                "age_seconds": round(c.age_seconds, 1),
            }
            for c in self._pattern_candidates.values()
        ]

    def add_observation_hook(self, hook: Callable[[dict[str, Any]], None]) -> None:
        """Add a hook to be called on each observation.

        Args:
            hook: Callable that receives observation data.
        """
        self._observation_hooks.append(hook)

    def get_stats(self) -> dict[str, Any]:
        """Get layer statistics.

        Returns:
            Dictionary with layer statistics.
        """
        return {
            "total_observations": self._total_observations,
            "window_size": len(self._observation_window.observations),
            "candidate_patterns": len(self._pattern_candidates),
            "emerged_signals": len(self._emerged_signals),
            "salience_entries": len(self._salience_scores),
            "sequence_length": len(self._sequence_tracker),
        }

    # =========================================================================
    # Internal Pattern Discovery Methods
    # =========================================================================

    def _generate_event_id(self) -> str:
        """Generate a unique event ID."""
        hash_input = f"{time.time()}:{self._total_observations}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:10]  # noqa: S324 non-cryptographic use

    def _update_co_occurrence(self, data: dict[str, Any]) -> None:
        """Update co-occurrence matrix from observation."""
        # Extract feature keys
        features: list[str] = []

        features.extend(f"{key}:{data[key]}" for key in ("action", "type", "intent", "topic") if key in data and data[key])

        # Update pairwise co-occurrence
        for i, f1 in enumerate(features):
            for f2 in features[i + 1 :]:
                self._co_occurrence_matrix[f1][f2] += 1
                self._co_occurrence_matrix[f2][f1] += 1

    def _update_sequence(self, data: dict[str, Any]) -> None:
        """Update sequence tracker from observation."""
        # Extract action/type for sequence
        action = data.get("action") or data.get("type") or data.get("intent")
        if action:
            self._sequence_tracker.append(str(action))

    async def _maybe_evaluate_patterns(self) -> None:
        """Evaluate observations for emerging patterns."""
        # Run pattern detection every 10 observations
        if self._total_observations % 10 != 0:
            return

        # Detect co-occurrence patterns
        await self._detect_co_occurrence_patterns()

        # Detect sequence patterns
        await self._detect_sequence_patterns()

        # Detect cluster patterns
        await self._detect_cluster_patterns()

        # Promote candidates to emerged signals
        await self._promote_candidates()

    async def _detect_co_occurrence_patterns(self) -> None:
        """Detect co-occurrence patterns from matrix."""
        for f1, co_features in self._co_occurrence_matrix.items():
            for f2, count in co_features.items():
                if count >= self._min_pattern_support:
                    pattern_id = self._pattern_id(SignalType.CORRELATION, f"{f1}+{f2}")
                    candidate = self._get_or_create_candidate(
                        pattern_id,
                        SignalType.CORRELATION,
                        f"Co-occurrence: {f1} ↔ {f2}",
                    )
                    candidate.add_evidence(f"count:{count}", confidence_boost=0.1)

    async def _detect_sequence_patterns(self) -> None:
        """Detect sequence patterns from tracker."""
        if len(self._sequence_tracker) < 3:
            return

        sequence = list(self._sequence_tracker)

        # Find repeated subsequences
        for length in (2, 3):
            subsequences: dict[tuple[str, ...], int] = defaultdict(int)
            for i in range(len(sequence) - length + 1):
                subseq = tuple(sequence[i : i + length])
                subsequences[subseq] += 1

            for subseq, count in subsequences.items():
                if count >= 2:
                    pattern_id = self._pattern_id(SignalType.SEQUENCE, "→".join(subseq))
                    candidate = self._get_or_create_candidate(
                        pattern_id,
                        SignalType.SEQUENCE,
                        f"Sequence: {' → '.join(subseq)}",
                    )
                    candidate.add_evidence(f"occurrence:{count}", confidence_boost=0.15)

    async def _detect_cluster_patterns(self) -> None:
        """Detect cluster patterns from recent observations."""
        recent = self._observation_window.get_recent(seconds=300.0)
        if len(recent) < 5:
            return

        # Group by action/type
        action_counts: dict[str, int] = defaultdict(int)
        for obs in recent:
            action = obs.get("action") or obs.get("type")
            if action:
                action_counts[str(action)] += 1

        # Find dominant actions
        total = sum(action_counts.values())
        for action, count in action_counts.items():
            ratio = count / total if total > 0 else 0
            if ratio > 0.3 and count >= 3:
                pattern_id = self._pattern_id(SignalType.CLUSTER, f"focus:{action}")
                candidate = self._get_or_create_candidate(
                    pattern_id,
                    SignalType.CLUSTER,
                    f"Action cluster: {action} ({round(ratio * 100)}%)",
                )
                candidate.add_evidence(f"dominance:{round(ratio, 2)}", confidence_boost=ratio * 0.2)

    async def _promote_candidates(self) -> None:
        """Promote qualifying candidates to emerged signals."""
        promoted: list[str] = []

        for pattern_id, candidate in self._pattern_candidates.items():
            if candidate.should_emerge(threshold=self._pattern_threshold):
                signal = EmergenceSignal.create(
                    signal_type=candidate.pattern_type,
                    description=candidate.description,
                    confidence=candidate.confidence,
                    salience=min(0.9, candidate.confidence + 0.1),
                    metadata={
                        "evidence_count": candidate.support_count,
                        "age_seconds": candidate.age_seconds,
                    },
                )
                self._emerged_signals.append(signal)
                promoted.append(pattern_id)

                logger.debug(f"Pattern emerged: {candidate.description} (confidence={candidate.confidence:.2f})")

        # Remove promoted candidates
        for pattern_id in promoted:
            del self._pattern_candidates[pattern_id]

    def _pattern_id(self, signal_type: SignalType, key: str) -> str:
        """Generate a deterministic pattern ID."""
        hash_input = f"{signal_type.value}:{key}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]  # noqa: S324 non-cryptographic use

    def _get_or_create_candidate(self, pattern_id: str, pattern_type: SignalType, description: str) -> PatternCandidate:
        """Get existing candidate or create new one."""
        if pattern_id not in self._pattern_candidates:
            self._pattern_candidates[pattern_id] = PatternCandidate(
                pattern_id=pattern_id,
                pattern_type=pattern_type,
                description=description,
            )
        return self._pattern_candidates[pattern_id]

    async def _maybe_decay(self) -> None:
        """Apply periodic decay to patterns and signals."""
        now = time.time()
        if now - self._last_decay_time < self._decay_interval:
            return

        self._last_decay_time = now

        # Prune stale observations
        pruned = self._observation_window.prune_stale()
        if pruned > 0:
            logger.debug(f"Pruned {pruned} stale observations")

        # Decay emerged signals
        for signal in self._emerged_signals:
            signal.decay(factor=0.05)

        # Remove expired signals
        self._emerged_signals = deque(
            [s for s in self._emerged_signals if not s.is_expired()],
            maxlen=200,
        )

        # Prune stale candidates
        stale_candidates = [
            pid
            for pid, c in self._pattern_candidates.items()
            if c.recency_seconds > 1800 and c.confidence < 0.2  # 30 min stale
        ]
        for pid in stale_candidates:
            del self._pattern_candidates[pid]

        # Decay co-occurrence matrix
        for f1 in list(self._co_occurrence_matrix.keys()):
            for f2 in list(self._co_occurrence_matrix[f1].keys()):
                self._co_occurrence_matrix[f1][f2] = int(self._co_occurrence_matrix[f1][f2] * 0.9)
                if self._co_occurrence_matrix[f1][f2] < 1:
                    del self._co_occurrence_matrix[f1][f2]
            if not self._co_occurrence_matrix[f1]:
                del self._co_occurrence_matrix[f1]

        logger.debug(f"Decay applied: {len(self._emerged_signals)} signals, {len(self._pattern_candidates)} candidates")

    def reset(self) -> None:
        """Reset all layer state (for testing)."""
        self._observation_window = ObservationWindow(max_size=self._observation_window.max_size)
        self._pattern_candidates.clear()
        self._emerged_signals.clear()
        self._salience_scores.clear()
        self._co_occurrence_matrix.clear()
        self._sequence_tracker.clear()
        self._total_observations = 0
        self._last_decay_time = time.time()
        logger.info("EmergenceLayer reset")
