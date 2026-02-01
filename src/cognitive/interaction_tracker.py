"""Track user interactions for cognitive state inference.

The InteractionTracker monitors and records user interactions to provide
data for cognitive state inference and profile learning.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ActionType(str, Enum):
    """Types of user actions."""

    CASE_START = "case_start"
    CASE_COMPLETE = "case_complete"
    QUERY = "query"
    COMMAND = "command"
    DECISION = "decision"
    CHOICE = "choice"
    NAVIGATION = "navigation"
    ERROR = "error"
    RETRY = "retry"
    HELP = "help"
    FEEDBACK = "feedback"


class Sentiment(str, Enum):
    """User sentiment indicators."""

    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    FRUSTRATED = "frustrated"
    CONFUSED = "confused"
    SATISFIED = "satisfied"


@dataclass
class InteractionEvent:
    """Represents a user interaction event."""

    # Identification
    user_id: str
    action: ActionType

    # Timing
    timestamp: datetime = field(default_factory=datetime.now)
    duration: float = 0.0  # Seconds taken to complete the action

    # Context
    case_id: str | None = None
    category: str | None = None
    domain: str | None = None

    # Content
    query_text: str | None = None
    response_text: str | None = None

    # User feedback
    sentiment: Sentiment = Sentiment.NEUTRAL
    explicit_feedback: str | None = None  # User's explicit feedback text

    # Cognitive indicators (explicit or inferred)
    cognitive_load: float | None = None  # 0-10 scale if user reports
    perceived_difficulty: float | None = None  # 0-1 scale
    confidence: float | None = None  # User's confidence in their action

    # Outcome
    outcome: str = "unknown"  # success, partial, failure, unknown

    # Additional metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage/transmission."""
        return {
            "user_id": self.user_id,
            "action": self.action.value,
            "timestamp": self.timestamp.isoformat(),
            "duration": self.duration,
            "case_id": self.case_id,
            "category": self.category,
            "domain": self.domain,
            "query_text": self.query_text,
            "response_text": self.response_text,
            "sentiment": self.sentiment.value,
            "explicit_feedback": self.explicit_feedback,
            "cognitive_load": self.cognitive_load,
            "perceived_difficulty": self.perceived_difficulty,
            "confidence": self.confidence,
            "outcome": self.outcome,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> InteractionEvent:
        """Create from dictionary."""
        return cls(
            user_id=data["user_id"],
            action=ActionType(data["action"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            duration=data.get("duration", 0.0),
            case_id=data.get("case_id"),
            category=data.get("category"),
            domain=data.get("domain"),
            query_text=data.get("query_text"),
            response_text=data.get("response_text"),
            sentiment=Sentiment(data.get("sentiment", "neutral")),
            explicit_feedback=data.get("explicit_feedback"),
            cognitive_load=data.get("cognitive_load"),
            perceived_difficulty=data.get("perceived_difficulty"),
            confidence=data.get("confidence"),
            outcome=data.get("outcome", "unknown"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class InteractionSummary:
    """Summary of interactions for analysis."""

    total_interactions: int = 0
    success_rate: float = 0.0
    avg_duration: float = 0.0
    sentiment_distribution: dict[str, int] = field(default_factory=dict)
    action_distribution: dict[str, int] = field(default_factory=dict)
    recent_errors: int = 0
    retry_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_interactions": self.total_interactions,
            "success_rate": self.success_rate,
            "avg_duration": self.avg_duration,
            "sentiment_distribution": self.sentiment_distribution,
            "action_distribution": self.action_distribution,
            "recent_errors": self.recent_errors,
            "retry_count": self.retry_count,
        }


class InteractionTracker:
    """Tracks user interactions for cognitive state inference.

    Monitors and records user interactions to provide data for:
    - Cognitive state inference
    - Profile learning
    - Pattern recognition
    - Mental model alignment detection
    """

    def __init__(self, storage_path: Path | None = None, max_events_per_user: int = 1000):
        """Initialize the interaction tracker.

        Args:
            storage_path: Path to store interaction logs
            max_events_per_user: Maximum events to keep per user in memory
        """
        if storage_path is None:
            storage_path = Path.home() / ".grid" / "interactions"

        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.max_events_per_user = max_events_per_user

        # In-memory storage: user_id -> list of events
        self._events: dict[str, list[InteractionEvent]] = defaultdict(list)

        # Active sessions for duration tracking: session_id -> (start_time, case_id)
        self._active_sessions: dict[str, tuple[datetime, str]] = {}

        logger.info(f"InteractionTracker initialized with path: {self.storage_path}")

    async def track(self, event: InteractionEvent) -> None:
        """Track an interaction event.

        Args:
            event: Interaction event to track
        """
        # Store in memory
        user_events = self._events[event.user_id]
        user_events.append(event)

        # Limit memory usage
        if len(user_events) > self.max_events_per_user:
            # Write oldest events to disk and remove from memory
            to_persist = user_events[: len(user_events) - self.max_events_per_user]
            await self._persist_events(event.user_id, to_persist)
            self._events[event.user_id] = user_events[-self.max_events_per_user :]

        # Log for debugging
        logger.debug(
            f"Tracked interaction: {event.action.value} for {event.user_id}, "
            f"duration={event.duration:.2f}s, outcome={event.outcome}"
        )

    async def start_session(self, session_id: str, case_id: str, user_id: str) -> None:
        """Start tracking a new session.

        Args:
            session_id: Unique session identifier
            case_id: Associated case ID
            user_id: User identifier
        """
        self._active_sessions[session_id] = (datetime.now(), case_id)
        logger.debug(f"Started session {session_id} for user {user_id}, case {case_id}")

    async def end_session(
        self,
        session_id: str,
        user_id: str,
        outcome: str = "unknown",
        sentiment: Sentiment = Sentiment.NEUTRAL,
    ) -> InteractionEvent | None:
        """End a session and create a completion event.

        Args:
            session_id: Session identifier
            user_id: User identifier
            outcome: Session outcome
            sentiment: User sentiment

        Returns:
            Completion interaction event if session found
        """
        if session_id not in self._active_sessions:
            logger.warning(f"Session {session_id} not found")
            return None

        start_time, case_id = self._active_sessions[session_id]
        duration = (datetime.now() - start_time).total_seconds()

        # Create completion event
        event = InteractionEvent(
            user_id=user_id,
            action=ActionType.CASE_COMPLETE,
            duration=duration,
            case_id=case_id,
            outcome=outcome,
            sentiment=sentiment,
        )

        await self.track(event)
        del self._active_sessions[session_id]

        return event

    async def get_events(
        self,
        user_id: str,
        limit: int = 50,
        since: datetime | None = None,
    ) -> list[InteractionEvent]:
        """Get interaction events for a user.

        Args:
            user_id: User identifier
            limit: Maximum number of events to return
            since: Optional start time filter

        Returns:
            List of interaction events
        """
        events = self._events.get(user_id, [])

        # Apply time filter
        if since:
            events = [e for e in events if e.timestamp >= since]

        # Limit and sort (newest first)
        return sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]

    async def get_summary(
        self,
        user_id: str,
        time_window: timedelta = timedelta(hours=24),
    ) -> InteractionSummary:
        """Get a summary of recent interactions.

        Args:
            user_id: User identifier
            time_window: Time window to analyze

        Returns:
            Interaction summary
        """
        since = datetime.now() - time_window
        events = await self.get_events(user_id, limit=None, since=since)

        if not events:
            return InteractionSummary()

        # Calculate summary statistics
        summary = InteractionSummary(
            total_interactions=len(events),
            sentiment_distribution=defaultdict(int),
            action_distribution=defaultdict(int),
        )

        # Count outcomes and calculate success rate
        successes = sum(1 for e in events if e.outcome == "success")
        summary.success_rate = successes / len(events)

        # Count durations
        durations = [e.duration for e in events if e.duration > 0]
        summary.avg_duration = sum(durations) / len(durations) if durations else 0.0

        # Count sentiment and action distributions
        for event in events:
            summary.sentiment_distribution[event.sentiment.value] += 1
            summary.action_distribution[event.action.value] += 1

        # Count recent errors and retries
        recent_window = timedelta(minutes=30)
        recent_since = datetime.now() - recent_window
        recent = [e for e in events if e.timestamp >= recent_since]

        summary.recent_errors = sum(1 for e in recent if e.outcome in ["failure", "error"])
        summary.retry_count = sum(1 for e in recent if e.action == ActionType.RETRY)

        return summary

    async def detect_patterns(
        self,
        user_id: str,
        time_window: timedelta = timedelta(days=7),
    ) -> dict[str, Any]:
        """Detect patterns in user interactions.

        Args:
            user_id: User identifier
            time_window: Time window to analyze

        Returns:
            Dictionary of detected patterns
        """
        events = await self.get_events(user_id, limit=None, since=datetime.now() - time_window)

        if not events:
            return {}

        patterns: dict[str, Any] = {}

        # Detect frustration patterns (negative sentiment + errors + retries)
        negative_events = [e for e in events if e.sentiment in [Sentiment.NEGATIVE, Sentiment.FRUSTRATED]]
        error_events = [e for e in events if e.outcome in ["failure", "error"]]
        retry_events = [e for e in events if e.action == ActionType.RETRY]

        patterns["frustration_level"] = (len(negative_events) + len(error_events) + len(retry_events) * 2) / len(events)

        # Detect engagement patterns (time spent per interaction)
        durations = [e.duration for e in events if e.duration > 0]
        if durations:
            avg_duration = sum(durations) / len(durations)
            patterns["engagement_level"] = "high" if avg_duration > 30 else "medium" if avg_duration > 10 else "low"
            patterns["avg_session_duration"] = avg_duration

        # Detect learning patterns (improvement over time)
        if len(events) > 10:
            first_half = events[len(events) // 2 :]
            second_half = events[: len(events) // 2]

            first_success = sum(1 for e in first_half if e.outcome == "success")
            second_success = sum(1 for e in second_half if e.outcome == "success")

            first_rate = first_success / len(first_half) if first_half else 0
            second_rate = second_success / len(second_half) if second_half else 0

            patterns["learning_trend"] = (
                "improving" if second_rate > first_rate else "stable" if second_rate == first_rate else "declining"
            )
            patterns["success_rate_change"] = second_rate - first_rate

        # Detect domain preferences
        domains = [e.domain for e in events if e.domain]
        if domains:
            from collections import Counter

            domain_counts = Counter(domains)
            patterns["preferred_domains"] = [d for d, _ in domain_counts.most_common(5)]

        return patterns

    async def get_session_duration(self, session_id: str) -> float | None:
        """Get the duration of an active session.

        Args:
            session_id: Session identifier

        Returns:
            Duration in seconds if session active, None otherwise
        """
        if session_id not in self._active_sessions:
            return None

        start_time, _ = self._active_sessions[session_id]
        return (datetime.now() - start_time).total_seconds()

    async def infer_sentiment_from_text(self, text: str) -> Sentiment:
        """Infer sentiment from text using simple heuristics.

        Args:
            text: Text to analyze

        Returns:
            Inferred sentiment
        """
        text_lower = text.lower()

        # Frustration indicators
        frustration_words = ["frustrated", "annoying", "stuck", "can't", "doesn't work"]
        if any(word in text_lower for word in frustration_words):
            return Sentiment.FRUSTRATED

        # Confusion indicators
        confusion_words = ["confused", "don't understand", "unclear", "what", "how"]
        if any(word in text_lower for word in confusion_words):
            return Sentiment.CONFUSED

        # Negative indicators
        negative_words = ["bad", "wrong", "error", "fail", "no", "not"]
        if any(word in text_lower for word in negative_words):
            return Sentiment.NEGATIVE

        # Positive indicators
        positive_words = ["good", "great", "thanks", "yes", "perfect", "helpful"]
        if any(word in text_lower for word in positive_words):
            return Sentiment.POSITIVE

        # Satisfaction indicators
        satisfaction_words = ["satisfied", "worked", "solved", "fixed"]
        if any(word in text_lower for word in satisfaction_words):
            return Sentiment.SATISFIED

        return Sentiment.NEUTRAL

    async def _persist_events(self, user_id: str, events: list[InteractionEvent]) -> None:
        """Persist events to disk.

        Args:
            user_id: User identifier
            events: Events to persist
        """
        if not events:
            return

        user_log_path = self.storage_path / f"{user_id}.jsonl"

        try:
            with open(user_log_path, "a") as f:
                for event in events:
                    f.write(json.dumps(event.to_dict()) + "\n")
        except Exception as e:
            logger.error(f"Error persisting events for {user_id}: {e}")

    async def load_from_disk(self, user_id: str, limit: int = 100) -> list[InteractionEvent]:
        """Load persisted events from disk.

        Args:
            user_id: User identifier
            limit: Maximum number of events to load

        Returns:
            List of loaded events
        """
        user_log_path = self.storage_path / f"{user_id}.jsonl"

        if not user_log_path.exists():
            return []

        events = []
        try:
            with open(user_log_path) as f:
                for line in f:
                    if line.strip():
                        events.append(InteractionEvent.from_dict(json.loads(line)))
        except Exception as e:
            logger.error(f"Error loading events for {user_id}: {e}")

        # Return newest first
        return sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]

    async def clear_events(self, user_id: str) -> None:
        """Clear all events for a user.

        Args:
            user_id: User identifier
        """
        self._events[user_id].clear()

        # Also clear disk storage
        user_log_path = self.storage_path / f"{user_id}.jsonl"
        if user_log_path.exists():
            try:
                user_log_path.unlink()
            except Exception as e:
                logger.error(f"Error clearing events for {user_id}: {e}")


# Global instance for convenience
_interaction_tracker: InteractionTracker | None = None


def get_interaction_tracker(storage_path: Path | None = None) -> InteractionTracker:
    """Get the global interaction tracker instance.

    Args:
        storage_path: Optional custom storage path

    Returns:
        Interaction tracker singleton
    """
    global _interaction_tracker
    if _interaction_tracker is None:
        _interaction_tracker = InteractionTracker(storage_path)
    return _interaction_tracker
