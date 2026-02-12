"""VECTION Main Engine - Context Emergence Orchestrator.

The Vection engine is the primary coordinator for context emergence.
It manages session contexts, orchestrates discovery workers, and provides
the interface for establishing, querying, and projecting context.

Usage:
    from vection.core.engine import Vection

    engine = Vection.get_instance()
    context = await engine.establish(session_id, event)
    signals = await engine.query_emergent(session_id, "pattern")
    projections = await engine.project(session_id, steps=3)
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Any, TypeVar

from vection.schemas.context_state import Anchor, ContextStatus, VectionContext
from vection.schemas.emergence_signal import EmergenceSignal
from vection.schemas.velocity_vector import DirectionCategory, VelocityVector

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class SessionState:
    """Internal state tracking for a session."""

    context: VectionContext
    event_buffer: deque[dict[str, Any]] = field(default_factory=lambda: deque(maxlen=50))
    last_directions: deque[str] = field(default_factory=lambda: deque(maxlen=10))
    topic_frequency: dict[str, int] = field(default_factory=dict)
    intent_sequence: list[str] = field(default_factory=list)


class Vection:
    """VECTION Context Emergence Engine.

    The main orchestrator for context emergence. Manages session contexts,
    coordinates discovery, and provides the interface for context operations.

    This is a singleton - use get_instance() for global access.
    """

    _instance: Vection | None = None
    _lock: Lock = Lock()

    def __init__(self) -> None:
        """Initialize the VECTION engine."""
        self._sessions: dict[str, SessionState] = {}
        self._global_signals: deque[EmergenceSignal] = deque(maxlen=500)
        self._started_at: datetime = datetime.now()
        self._total_interactions: int = 0
        self._decay_interval: float = 300.0  # 5 minutes
        self._last_decay: float = time.time()

        logger.info("VECTION engine initialized")

    @classmethod
    def get_instance(cls) -> Vection:
        """Get the singleton VECTION instance.

        Returns:
            Vection: The global engine instance.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (for testing)."""
        with cls._lock:
            cls._instance = None

    async def establish(self, session_id: str, event: Any) -> VectionContext:
        """Establish or update context for a session.

        This is the primary entry point for context establishment.
        It observes the event, updates session state, calculates velocity,
        and returns the current context.

        Args:
            session_id: Unique session identifier.
            event: The interaction event to process.

        Returns:
            VectionContext: The established/updated context.
        """
        self._total_interactions += 1

        # Get or create session state
        state = self._get_or_create_session(session_id)

        # Extract event data
        event_data = self._extract_event_data(event)

        # Observe the event
        await self._observe_event(state, event_data)

        # Update velocity
        await self._update_velocity(state, event_data)

        # Discover emergent patterns
        await self._discover_patterns(state, event_data)

        # Update context status
        state.context.update_status()

        # Extend temporal window
        state.context.extend_temporal_window()

        # Periodic decay
        await self._maybe_decay()

        logger.debug(
            f"Context established for {session_id}: "
            f"status={state.context.status.value}, "
            f"anchors={state.context.anchor_count}, "
            f"signals={state.context.signal_count}"
        )

        return state.context

    async def query_emergent(self, session_id: str, query: str) -> list[EmergenceSignal]:
        """Query emergent patterns for a session.

        Searches accumulated signals and global signals for patterns
        matching the query.

        Args:
            session_id: Unique session identifier.
            query: Query string for pattern matching.

        Returns:
            List of matching EmergenceSignal instances.
        """
        if not query:
            return []

        state = self._sessions.get(session_id)
        if state is None:
            return []

        matches: list[tuple[float, EmergenceSignal]] = []

        # Search session signals
        for signal in state.context.accumulated_signals:
            if isinstance(signal, EmergenceSignal):
                score = signal.matches_query(query)
                if score > 0.2:
                    matches.append((score, signal))

        # Search global signals with lower weight
        for signal in self._global_signals:
            score = signal.matches_query(query) * 0.5
            if score > 0.2:
                matches.append((score, signal))

        # Sort by score and return signals
        matches.sort(key=lambda x: x[0], reverse=True)
        return [signal for _, signal in matches[:10]]

    async def project(self, session_id: str, steps: int = 3) -> list[str]:
        """Project future context needs.

        Uses the cognitive velocity vector to predict what context
        will likely be needed in upcoming interactions.

        Args:
            session_id: Unique session identifier.
            steps: Number of steps to project forward.

        Returns:
            List of projected context need descriptions.
        """
        state = self._sessions.get(session_id)
        if state is None:
            return ["DATA_MISSING: session not found"]

        velocity = state.context.cognitive_velocity
        if velocity is None or not isinstance(velocity, VelocityVector):
            return ["DATA_MISSING: no velocity tracked"]

        return velocity.project(steps)

    async def dissolve(self, session_id: str) -> bool:
        """Dissolve a session context.

        Marks the context as dissolved and cleans up resources.

        Args:
            session_id: Session to dissolve.

        Returns:
            True if session was found and dissolved.
        """
        state = self._sessions.get(session_id)
        if state is None:
            return False

        state.context.dissolve()
        del self._sessions[session_id]

        logger.info(f"Session {session_id} dissolved")
        return True

    def get_context(self, session_id: str) -> VectionContext | None:
        """Get current context for a session.

        Args:
            session_id: Session identifier.

        Returns:
            VectionContext or None if not found.
        """
        state = self._sessions.get(session_id)
        return state.context if state else None

    def get_all_sessions(self) -> list[str]:
        """Get all active session IDs.

        Returns:
            List of session identifiers.
        """
        return list(self._sessions.keys())

    def get_stats(self) -> dict[str, Any]:
        """Get engine statistics.

        Returns:
            Dictionary with engine stats.
        """
        return {
            "uptime_seconds": (datetime.now() - self._started_at).total_seconds(),
            "active_sessions": len(self._sessions),
            "total_interactions": self._total_interactions,
            "global_signals": len(self._global_signals),
        }

    # =========================================================================
    # Internal Methods
    # =========================================================================

    def _get_or_create_session(self, session_id: str) -> SessionState:
        """Get existing session or create new one.

        Args:
            session_id: Session identifier.

        Returns:
            SessionState for the session.
        """
        if session_id not in self._sessions:
            context = VectionContext.create(session_id)
            self._sessions[session_id] = SessionState(context=context)
            logger.debug(f"Created new session: {session_id}")

        return self._sessions[session_id]

    def _extract_event_data(self, event: Any) -> dict[str, Any]:
        """Extract relevant data from an event.

        Args:
            event: The interaction event.

        Returns:
            Normalized event data dictionary.
        """
        if isinstance(event, dict):
            return event

        # Try to extract from object attributes
        data: dict[str, Any] = {}

        for attr in ("user_id", "action", "case_id", "metadata", "payload", "content", "query", "type"):
            if hasattr(event, attr):
                value = getattr(event, attr)
                if value is not None:
                    data[attr] = value

        # Try to_dict method
        if hasattr(event, "to_dict") and callable(event.to_dict):
            try:
                result = event.to_dict()
                if isinstance(result, dict):
                    data.update(result)
            except Exception:
                pass

        return data if data else {"raw_event": str(event)}

    async def _observe_event(self, state: SessionState, event_data: dict[str, Any]) -> None:
        """Observe an event and update session state.

        Args:
            state: Session state to update.
            event_data: Event data to observe.
        """
        # Buffer the event
        state.event_buffer.append(
            {
                "timestamp": time.time(),
                "data": event_data,
            }
        )

        # Extract and add anchors
        await self._extract_anchors(state, event_data)

        # Track topic frequency
        topics = self._extract_topics(event_data)
        for topic in topics:
            state.topic_frequency[topic] = state.topic_frequency.get(topic, 0) + 1

        # Track intent sequence
        intent = self._extract_intent(event_data)
        if intent:
            state.intent_sequence.append(intent)
            if len(state.intent_sequence) > 20:
                state.intent_sequence = state.intent_sequence[-20:]

    async def _extract_anchors(self, state: SessionState, event_data: dict[str, Any]) -> None:
        """Extract anchors from event data.

        Args:
            state: Session state to update.
            event_data: Event data to analyze.
        """
        # Topic anchors from content/query
        content = event_data.get("content") or event_data.get("query") or event_data.get("payload")
        if content and isinstance(content, str):
            # Simple keyword extraction (could be enhanced with NLP)
            words = content.lower().split()
            significant_words = [w for w in words if len(w) > 5 and w.isalpha()]
            for word in significant_words[:3]:
                anchor = Anchor.topic(word, weight=0.4)
                state.context.add_anchor(anchor)

        # Intent anchor from action
        action = event_data.get("action") or event_data.get("type")
        if action and isinstance(action, str):
            anchor = Anchor.intent(action, weight=0.6)
            state.context.add_anchor(anchor)

        # Task anchor from case_id
        case_id = event_data.get("case_id")
        if case_id:
            anchor = Anchor.task(str(case_id), weight=0.7)
            state.context.add_anchor(anchor)

    def _extract_topics(self, event_data: dict[str, Any]) -> list[str]:
        """Extract topic keywords from event data.

        Args:
            event_data: Event data to analyze.

        Returns:
            List of topic strings.
        """
        topics: list[str] = []

        content = event_data.get("content") or event_data.get("query") or ""
        if isinstance(content, str):
            words = content.lower().split()
            topics.extend([w for w in words if len(w) > 4 and w.isalpha()][:5])

        action = event_data.get("action") or event_data.get("type")
        if action:
            topics.append(str(action).lower())

        return topics

    def _extract_intent(self, event_data: dict[str, Any]) -> str | None:
        """Extract intent from event data.

        Args:
            event_data: Event data to analyze.

        Returns:
            Intent string or None.
        """
        # Direct action/type field
        action = event_data.get("action") or event_data.get("type")
        if action:
            return str(action)

        # Infer from content keywords
        content = str(event_data.get("content") or event_data.get("query") or "").lower()

        intent_keywords = {
            "analyze": ["analyze", "analysis", "examine", "investigate"],
            "create": ["create", "make", "build", "generate"],
            "search": ["search", "find", "look", "query"],
            "execute": ["run", "execute", "perform", "do"],
            "explain": ["explain", "why", "how", "what"],
        }

        for intent, keywords in intent_keywords.items():
            if any(kw in content for kw in keywords):
                return intent

        return None

    async def _update_velocity(self, state: SessionState, event_data: dict[str, Any]) -> None:
        """Update cognitive velocity for the session.

        Args:
            state: Session state to update.
            event_data: Current event data.
        """
        # Determine current direction
        direction = self._determine_direction(state, event_data)
        state.last_directions.append(direction)

        # Calculate velocity components
        magnitude = self._calculate_magnitude(state)
        momentum = self._calculate_momentum(state)
        drift = self._calculate_drift(state)
        confidence = self._calculate_velocity_confidence(state)

        # Create or update velocity vector
        velocity = VelocityVector(
            direction=self._categorize_direction(direction),
            direction_detail=direction,
            magnitude=magnitude,
            momentum=momentum,
            drift=drift,
            confidence=confidence,
            history=list(state.last_directions),
        )

        state.context.update_velocity(velocity)

    def _determine_direction(self, state: SessionState, event_data: dict[str, Any]) -> str:
        """Determine cognitive direction from event.

        Args:
            state: Session state.
            event_data: Current event data.

        Returns:
            Direction string.
        """
        intent = self._extract_intent(event_data)
        if intent:
            return intent

        # Infer from topic frequency trends
        if state.topic_frequency:
            top_topic = max(state.topic_frequency.items(), key=lambda x: x[1])[0]
            return f"focus_{top_topic}"

        return "unknown"

    def _categorize_direction(self, direction: str) -> DirectionCategory:
        """Categorize direction string.

        Args:
            direction: Direction string.

        Returns:
            DirectionCategory enum.
        """
        direction_lower = direction.lower()

        mappings = {
            DirectionCategory.EXPLORATION: ["search", "find", "explore", "browse"],
            DirectionCategory.INVESTIGATION: ["analyze", "debug", "investigate", "why"],
            DirectionCategory.EXECUTION: ["execute", "run", "create", "build", "do"],
            DirectionCategory.SYNTHESIS: ["combine", "merge", "integrate"],
            DirectionCategory.REFLECTION: ["review", "summarize", "evaluate"],
        }

        for category, keywords in mappings.items():
            if any(kw in direction_lower for kw in keywords):
                return category

        return DirectionCategory.UNKNOWN

    def _calculate_magnitude(self, state: SessionState) -> float:
        """Calculate velocity magnitude.

        Args:
            state: Session state.

        Returns:
            Magnitude value (0.0 - 1.0).
        """
        # Based on interaction rate
        if len(state.event_buffer) < 2:
            return 0.3

        recent_events = list(state.event_buffer)[-5:]
        if len(recent_events) < 2:
            return 0.3

        time_span = recent_events[-1]["timestamp"] - recent_events[0]["timestamp"]
        if time_span <= 0:
            return 0.5

        rate = len(recent_events) / time_span  # events per second

        # Normalize: 0.1 events/sec = low, 1+ events/sec = high
        magnitude = min(1.0, rate * 0.5 + 0.2)
        return magnitude

    def _calculate_momentum(self, state: SessionState) -> float:
        """Calculate velocity momentum.

        Args:
            state: Session state.

        Returns:
            Momentum value (0.0 - 1.0).
        """
        if len(state.last_directions) < 2:
            return 0.5

        # Momentum increases with consistent direction
        directions = list(state.last_directions)
        if not directions:
            return 0.5

        # Count consecutive same directions from end
        last_dir = directions[-1]
        consecutive = 1
        for d in reversed(directions[:-1]):
            if d == last_dir:
                consecutive += 1
            else:
                break

        momentum = min(1.0, 0.3 + (consecutive * 0.15))
        return momentum

    def _calculate_drift(self, state: SessionState) -> float:
        """Calculate velocity drift.

        Args:
            state: Session state.

        Returns:
            Drift value (-1.0 to 1.0).
        """
        if len(state.last_directions) < 3:
            return 0.0

        directions = list(state.last_directions)
        unique_recent = len(set(directions[-5:]))

        # High uniqueness = high drift
        drift = (unique_recent - 1) / 4.0  # normalize to 0-1
        return min(1.0, max(-1.0, drift))

    def _calculate_velocity_confidence(self, state: SessionState) -> float:
        """Calculate velocity confidence.

        Args:
            state: Session state.

        Returns:
            Confidence value (0.0 - 1.0).
        """
        factors = []

        # More events = higher confidence
        event_factor = min(1.0, len(state.event_buffer) / 10.0)
        factors.append(event_factor)

        # More anchors = higher confidence
        anchor_factor = min(1.0, state.context.anchor_count / 5.0)
        factors.append(anchor_factor)

        # Consistent direction = higher confidence
        if state.last_directions:
            unique_ratio = len(set(state.last_directions)) / len(state.last_directions)
            direction_factor = 1.0 - (unique_ratio * 0.5)
            factors.append(direction_factor)

        return sum(factors) / len(factors) if factors else 0.3

    async def _discover_patterns(self, state: SessionState, event_data: dict[str, Any]) -> None:
        """Discover emergent patterns from session state.

        Args:
            state: Session state to analyze.
            event_data: Current event data.
        """
        # Sequence patterns from intent
        if len(state.intent_sequence) >= 3:
            recent_intents = state.intent_sequence[-5:]
            if len(set(recent_intents)) <= 2:
                # Repetitive intent pattern
                signal = EmergenceSignal.sequence(
                    description=f"Repetitive intent: {recent_intents[-1]}",
                    steps=recent_intents,
                    confidence=0.6,
                )
                state.context.add_signal(signal)

        # Topic cluster patterns
        if state.topic_frequency:
            top_topics = sorted(state.topic_frequency.items(), key=lambda x: x[1], reverse=True)[:3]
            if len(top_topics) >= 2 and top_topics[0][1] >= 3:
                signal = EmergenceSignal.cluster(
                    description=f"Topic focus: {top_topics[0][0]}",
                    members=[t[0] for t in top_topics],
                    confidence=min(0.9, top_topics[0][1] / 5.0),
                )
                state.context.add_signal(signal)

        # Correlation patterns from event buffer
        if len(state.event_buffer) >= 5:
            await self._detect_correlations(state)

    async def _detect_correlations(self, state: SessionState) -> None:
        """Detect correlation patterns in event buffer.

        Args:
            state: Session state to analyze.
        """
        recent_events = list(state.event_buffer)[-10:]

        # Extract action pairs
        actions = []
        for event in recent_events:
            action = event["data"].get("action") or event["data"].get("type")
            if action:
                actions.append(str(action))

        if len(actions) < 2:
            return

        # Find co-occurring actions
        from collections import Counter

        pairs: list[tuple[str, str]] = []
        for i in range(len(actions) - 1):
            pair = tuple(sorted([actions[i], actions[i + 1]]))
            pairs.append(pair)  # type: ignore

        pair_counts = Counter(pairs)
        for pair, count in pair_counts.most_common(2):
            if count >= 2:
                signal = EmergenceSignal.correlation(
                    description=f"Action correlation: {pair[0]} → {pair[1]}",
                    items=list(pair),
                    confidence=min(0.8, count / 3.0),
                )
                state.context.add_signal(signal)
                self._global_signals.append(signal)

    async def _maybe_decay(self) -> None:
        """Apply periodic decay to all sessions."""
        now = time.time()
        if now - self._last_decay < self._decay_interval:
            return

        self._last_decay = now

        for session_id, state in list(self._sessions.items()):
            state.context.decay_all(factor=0.05)

            # Remove dissolved or very stale sessions
            if state.context.status == ContextStatus.DISSOLVED:
                del self._sessions[session_id]
            elif state.context.staleness > 3600:  # 1 hour
                state.context.dissolve()
                del self._sessions[session_id]
                logger.info(f"Session {session_id} expired and dissolved")

        logger.debug(f"Decay applied. Active sessions: {len(self._sessions)}")
