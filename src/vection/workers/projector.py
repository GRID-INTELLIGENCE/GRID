"""Projector Worker - Future context projection.

A background worker that projects future context needs based on
current trajectory, velocity, and historical patterns. This enables
VECTION's anticipatory intelligence - knowing what you'll need
before you need it.

Projection Types:
- Velocity-based: Project based on current direction/momentum
- Pattern-based: Project based on historical patterns
- Sequence-based: Project next steps in detected sequences
- Contextual: Project based on accumulated context anchors
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from vection.schemas.velocity_vector import DirectionCategory, VelocityVector

logger = logging.getLogger(__name__)


class ProjectionType(str, Enum):
    """Types of projections."""

    VELOCITY = "velocity"  # Based on current velocity
    PATTERN = "pattern"  # Based on historical patterns
    SEQUENCE = "sequence"  # Based on detected sequences
    CONTEXTUAL = "contextual"  # Based on context anchors
    COMPOSITE = "composite"  # Combined from multiple sources


@dataclass
class Projection:
    """A future context projection."""

    projection_id: str
    projection_type: ProjectionType
    description: str
    confidence: float
    horizon_steps: int
    source_session: str | None = None
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def age_seconds(self) -> float:
        """Get projection age in seconds."""
        return time.time() - self.created_at

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "projection_id": self.projection_id,
            "projection_type": self.projection_type.value,
            "description": self.description,
            "confidence": round(self.confidence, 3),
            "horizon_steps": self.horizon_steps,
            "source_session": self.source_session,
            "age_seconds": round(self.age_seconds, 1),
            "metadata": self.metadata,
        }


@dataclass
class ProjectionInput:
    """Input data for projection calculation."""

    session_id: str
    velocity: VelocityVector | None
    recent_intents: list[str]
    topic_frequency: dict[str, int]
    anchor_values: list[str]
    timestamp: float = field(default_factory=time.time)


@dataclass
class ProjectionResult:
    """Result of a projection operation."""

    projections: list[str]
    confidence: float
    projection_type: ProjectionType
    horizon: int
    source: str
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "projections": self.projections,
            "confidence": round(self.confidence, 3),
            "type": self.projection_type.value,
            "horizon": self.horizon,
            "source": self.source,
            "evidence": self.evidence,
        }


class Projector:
    """Background worker for future context projection.

    Analyzes current state and historical patterns to project
    what context will likely be needed in future interactions.

    Usage:
        projector = Projector()
        await projector.start()
        result = projector.project(session_id, velocity, context)
        # ... later ...
        await projector.stop()
    """

    def __init__(
        self,
        default_horizon: int = 3,
        confidence_threshold: float = 0.3,
        max_projections: int = 100,
        processing_interval: float = 10.0,
        decay_interval: float = 300.0,
    ) -> None:
        """Initialize the projector worker.

        Args:
            default_horizon: Default projection horizon (steps).
            confidence_threshold: Minimum confidence to emit projection.
            max_projections: Maximum projections to retain.
            processing_interval: Seconds between processing runs.
            decay_interval: Seconds between decay operations.
        """
        self._default_horizon = default_horizon
        self._confidence_threshold = confidence_threshold
        self._max_projections = max_projections
        self._processing_interval = processing_interval
        self._decay_interval = decay_interval

        self._projections: deque[Projection] = deque(maxlen=max_projections)
        self._session_inputs: dict[str, ProjectionInput] = {}
        self._sequence_patterns: dict[str, list[str]] = {}
        self._direction_history: dict[str, list[DirectionCategory]] = {}

        self._running = False
        self._task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()

        self._total_projections = 0
        self._started_at: datetime | None = None
        self._last_decay: float = time.time()
        self._callbacks: list[Callable[[Projection], None]] = []

        # Direction-based projection mappings
        self._direction_projections = {
            DirectionCategory.EXPLORATION: [
                "broader_context_needed",
                "related_topics_retrieval",
                "discovery_support",
                "search_expansion",
            ],
            DirectionCategory.INVESTIGATION: [
                "causal_analysis_context",
                "root_cause_patterns",
                "diagnostic_support",
                "deep_dive_resources",
            ],
            DirectionCategory.EXECUTION: [
                "task_completion_context",
                "action_guidance",
                "implementation_patterns",
                "execution_checklist",
            ],
            DirectionCategory.SYNTHESIS: [
                "integration_context",
                "combination_patterns",
                "creative_support",
                "synthesis_frameworks",
            ],
            DirectionCategory.REFLECTION: [
                "retrospective_context",
                "summary_patterns",
                "evaluation_support",
                "review_templates",
            ],
            DirectionCategory.TRANSITION: [
                "context_shift_preparation",
                "bridging_context",
                "mode_switch_support",
                "transition_guidance",
            ],
            DirectionCategory.UNKNOWN: [
                "general_context",
                "exploratory_support",
                "baseline_retrieval",
            ],
        }

        logger.info(f"Projector initialized: horizon={default_horizon}, threshold={confidence_threshold}")

    @property
    def is_running(self) -> bool:
        """Check if worker is running."""
        return self._running

    @property
    def projection_count(self) -> int:
        """Get current projection count."""
        return len(self._projections)

    async def start(self) -> None:
        """Start the projector worker."""
        if self._running:
            logger.warning("Projector already running")
            return

        self._running = True
        self._started_at = datetime.now()
        self._task = asyncio.create_task(self._processing_loop())
        logger.info("Projector worker started")

    async def stop(self) -> None:
        """Stop the projector worker."""
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

        logger.info("Projector worker stopped")

    def update_session(
        self,
        session_id: str,
        velocity: VelocityVector | None = None,
        recent_intents: list[str] | None = None,
        topic_frequency: dict[str, int] | None = None,
        anchor_values: list[str] | None = None,
    ) -> None:
        """Update session data for projection.

        Args:
            session_id: Session identifier.
            velocity: Current velocity vector.
            recent_intents: Recent user intents.
            topic_frequency: Topic frequency map.
            anchor_values: Context anchor values.
        """
        if session_id not in self._session_inputs:
            self._session_inputs[session_id] = ProjectionInput(
                session_id=session_id,
                velocity=velocity,
                recent_intents=recent_intents or [],
                topic_frequency=topic_frequency or {},
                anchor_values=anchor_values or [],
            )
        else:
            input_data = self._session_inputs[session_id]
            if velocity is not None:
                input_data.velocity = velocity
            if recent_intents is not None:
                input_data.recent_intents = recent_intents
            if topic_frequency is not None:
                input_data.topic_frequency = topic_frequency
            if anchor_values is not None:
                input_data.anchor_values = anchor_values
            input_data.timestamp = time.time()

        # Track direction history
        if velocity is not None:
            if session_id not in self._direction_history:
                self._direction_history[session_id] = []
            self._direction_history[session_id].append(velocity.direction)
            # Limit history size
            if len(self._direction_history[session_id]) > 20:
                self._direction_history[session_id] = self._direction_history[session_id][-20:]

    def project(
        self,
        session_id: str,
        steps: int | None = None,
    ) -> ProjectionResult:
        """Generate projections for a session.

        Args:
            session_id: Session identifier.
            steps: Projection horizon (defaults to default_horizon).

        Returns:
            ProjectionResult with projections and confidence.
        """
        horizon = steps or self._default_horizon
        input_data = self._session_inputs.get(session_id)

        if input_data is None or input_data.velocity is None:
            return ProjectionResult(
                projections=["DATA_MISSING: insufficient trajectory data"],
                confidence=0.0,
                projection_type=ProjectionType.VELOCITY,
                horizon=horizon,
                source=session_id,
            )

        # Combine multiple projection strategies
        results: list[ProjectionResult] = []

        # Velocity-based projection
        velocity_result = self._project_from_velocity(input_data, horizon)
        results.append(velocity_result)

        # Sequence-based projection
        sequence_result = self._project_from_sequence(input_data, horizon)
        if sequence_result.confidence > 0:
            results.append(sequence_result)

        # Context-based projection
        context_result = self._project_from_context(input_data, horizon)
        if context_result.confidence > 0:
            results.append(context_result)

        # Combine results
        combined = self._combine_projections(results, horizon, session_id)

        # Store projection if confident enough
        if combined.confidence >= self._confidence_threshold:
            self._store_projection(combined, session_id)

        return combined

    def project_for_all_sessions(self) -> dict[str, ProjectionResult]:
        """Generate projections for all tracked sessions.

        Returns:
            Dictionary mapping session IDs to ProjectionResults.
        """
        results: dict[str, ProjectionResult] = {}
        for session_id in self._session_inputs:
            results[session_id] = self.project(session_id)
        return results

    def on_projection(self, callback: Callable[[Projection], None]) -> None:
        """Register a callback for new projections.

        Args:
            callback: Function called when projection is generated.
        """
        self._callbacks.append(callback)

    def get_projections(
        self,
        session_id: str | None = None,
        min_confidence: float = 0.0,
        limit: int = 20,
    ) -> list[Projection]:
        """Get stored projections.

        Args:
            session_id: Optional filter by session.
            min_confidence: Minimum confidence threshold.
            limit: Maximum projections to return.

        Returns:
            List of Projection instances.
        """
        filtered = []
        for proj in self._projections:
            if proj.confidence < min_confidence:
                continue
            if session_id is not None and proj.source_session != session_id:
                continue
            filtered.append(proj)

        return filtered[-limit:]

    def get_stats(self) -> dict[str, Any]:
        """Get projector statistics.

        Returns:
            Dictionary with worker statistics.
        """
        return {
            "is_running": self._running,
            "total_projections": self._total_projections,
            "stored_projections": len(self._projections),
            "tracked_sessions": len(self._session_inputs),
            "default_horizon": self._default_horizon,
            "confidence_threshold": self._confidence_threshold,
            "uptime_seconds": ((datetime.now() - self._started_at).total_seconds() if self._started_at else 0),
        }

    def reset(self) -> None:
        """Reset projector state."""
        self._projections.clear()
        self._session_inputs.clear()
        self._sequence_patterns.clear()
        self._direction_history.clear()
        self._total_projections = 0
        logger.info("Projector reset")

    # =========================================================================
    # Internal Processing
    # =========================================================================

    async def _processing_loop(self) -> None:
        """Main processing loop."""
        while self._running:
            try:
                await asyncio.sleep(self._processing_interval)
                await self._process_projections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Projector processing error: {e}")

    async def _process_projections(self) -> None:
        """Process projections for all sessions."""
        async with self._lock:
            # Generate projections for active sessions
            now = time.time()
            for session_id, input_data in list(self._session_inputs.items()):
                # Skip stale sessions
                if now - input_data.timestamp > 1800:  # 30 minutes
                    continue

                # Generate projection
                result = self.project(session_id)
                if result.confidence >= self._confidence_threshold:
                    logger.debug(
                        f"Projection for {session_id}: {result.projections[:2]}... (conf={result.confidence:.2f})"
                    )

            # Apply decay
            await self._maybe_decay()

    async def _maybe_decay(self) -> None:
        """Apply periodic decay."""
        now = time.time()
        if now - self._last_decay < self._decay_interval:
            return

        self._last_decay = now

        # Remove stale session inputs
        stale_sessions = [
            sid
            for sid, inp in self._session_inputs.items()
            if now - inp.timestamp > 3600  # 1 hour
        ]
        for sid in stale_sessions:
            del self._session_inputs[sid]
            if sid in self._direction_history:
                del self._direction_history[sid]

        # Remove old projections
        self._projections = deque(
            [p for p in self._projections if p.age_seconds < 1800],
            maxlen=self._max_projections,
        )

        logger.debug(
            f"Projector decay: {len(stale_sessions)} sessions removed, {len(self._projections)} projections remaining"
        )

    def _project_from_velocity(
        self,
        input_data: ProjectionInput,
        horizon: int,
    ) -> ProjectionResult:
        """Generate projections from velocity vector."""
        velocity = input_data.velocity
        if velocity is None:
            return ProjectionResult(
                projections=[],
                confidence=0.0,
                projection_type=ProjectionType.VELOCITY,
                horizon=horizon,
                source=input_data.session_id,
            )

        # Get base projections for direction
        base_projections = self._direction_projections.get(
            velocity.direction,
            self._direction_projections[DirectionCategory.UNKNOWN],
        )

        # Select projections based on horizon
        projections = base_projections[:horizon]

        # Calculate confidence from velocity
        confidence = velocity.confidence * velocity.momentum
        # Penalize high drift
        confidence *= 1.0 - (abs(velocity.drift) * 0.3)

        return ProjectionResult(
            projections=projections,
            confidence=confidence,
            projection_type=ProjectionType.VELOCITY,
            horizon=horizon,
            source=input_data.session_id,
            evidence=[
                f"direction:{velocity.direction.value}",
                f"momentum:{velocity.momentum:.2f}",
            ],
        )

    def _project_from_sequence(
        self,
        input_data: ProjectionInput,
        horizon: int,
    ) -> ProjectionResult:
        """Generate projections from intent sequences."""
        intents = input_data.recent_intents
        if len(intents) < 2:
            return ProjectionResult(
                projections=[],
                confidence=0.0,
                projection_type=ProjectionType.SEQUENCE,
                horizon=horizon,
                source=input_data.session_id,
            )

        # Look for patterns in intent sequence
        projections: list[str] = []
        confidence = 0.0

        # Check for repeated patterns
        last_intent = intents[-1]
        same_count = sum(1 for i in intents[-5:] if i == last_intent)

        if same_count >= 2:
            # User is focused on this intent
            projections.append(f"continue_{last_intent}_context")
            projections.append(f"{last_intent}_completion_support")
            confidence = min(0.8, 0.3 + same_count * 0.1)

        # Check for alternating patterns
        if len(intents) >= 4:
            if intents[-1] == intents[-3] and intents[-2] == intents[-4]:
                projections.append("pattern_continuation_support")
                confidence = max(confidence, 0.6)

        return ProjectionResult(
            projections=projections[:horizon],
            confidence=confidence,
            projection_type=ProjectionType.SEQUENCE,
            horizon=horizon,
            source=input_data.session_id,
            evidence=[f"last_intent:{last_intent}", f"sequence_length:{len(intents)}"],
        )

    def _project_from_context(
        self,
        input_data: ProjectionInput,
        horizon: int,
    ) -> ProjectionResult:
        """Generate projections from context anchors."""
        anchors = input_data.anchor_values
        topics = input_data.topic_frequency

        if not anchors and not topics:
            return ProjectionResult(
                projections=[],
                confidence=0.0,
                projection_type=ProjectionType.CONTEXTUAL,
                horizon=horizon,
                source=input_data.session_id,
            )

        projections: list[str] = []
        confidence = 0.0

        # Project from dominant topics
        if topics:
            top_topic = max(topics.items(), key=lambda x: x[1])
            projections.append(f"{top_topic[0]}_deep_context")
            confidence = min(0.7, top_topic[1] / 10.0 + 0.2)

        # Project from anchors
        if anchors:
            projections.append("anchor_related_context")
            confidence = max(confidence, min(0.6, len(anchors) / 5.0 + 0.2))

        return ProjectionResult(
            projections=projections[:horizon],
            confidence=confidence,
            projection_type=ProjectionType.CONTEXTUAL,
            horizon=horizon,
            source=input_data.session_id,
            evidence=[
                f"anchor_count:{len(anchors)}",
                f"topic_count:{len(topics)}",
            ],
        )

    def _combine_projections(
        self,
        results: list[ProjectionResult],
        horizon: int,
        session_id: str,
    ) -> ProjectionResult:
        """Combine multiple projection results."""
        if not results:
            return ProjectionResult(
                projections=["DATA_MISSING: no projection sources"],
                confidence=0.0,
                projection_type=ProjectionType.COMPOSITE,
                horizon=horizon,
                source=session_id,
            )

        # Weight by confidence
        total_confidence = sum(r.confidence for r in results)
        if total_confidence == 0:
            return results[0]

        # Merge projections, prioritizing high-confidence sources
        seen: set[str] = set()
        merged_projections: list[str] = []
        all_evidence: list[str] = []

        for result in sorted(results, key=lambda r: r.confidence, reverse=True):
            for proj in result.projections:
                if proj not in seen:
                    seen.add(proj)
                    merged_projections.append(proj)
            all_evidence.extend(result.evidence)

        # Combined confidence is weighted average
        combined_confidence = sum(r.confidence**2 for r in results) / total_confidence

        return ProjectionResult(
            projections=merged_projections[: horizon * 2],  # Allow more combined
            confidence=min(0.95, combined_confidence),
            projection_type=ProjectionType.COMPOSITE,
            horizon=horizon,
            source=session_id,
            evidence=all_evidence[:10],
        )

    def _store_projection(
        self,
        result: ProjectionResult,
        session_id: str,
    ) -> None:
        """Store a projection result."""
        projection = Projection(
            projection_id=self._generate_projection_id(),
            projection_type=result.projection_type,
            description="; ".join(result.projections[:3]),
            confidence=result.confidence,
            horizon_steps=result.horizon,
            source_session=session_id,
            metadata={
                "projections": result.projections,
                "evidence": result.evidence,
            },
        )

        self._projections.append(projection)
        self._total_projections += 1

        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(projection)
            except Exception as e:
                logger.warning(f"Projection callback error: {e}")

    def _generate_projection_id(self) -> str:
        """Generate a unique projection ID."""
        hash_input = f"{time.time()}:{self._total_projections}"
        return f"proj_{hashlib.md5(hash_input.encode()).hexdigest()[:10]}"


# Module-level singleton
_projector: Projector | None = None


def get_projector() -> Projector:
    """Get the global projector instance.

    Returns:
        Projector singleton.
    """
    global _projector
    if _projector is None:
        _projector = Projector()
    return _projector
