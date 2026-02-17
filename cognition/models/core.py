"""
Cognition Core Models

Defines the foundational data structures for cognitive state tracking,
metrics, and activity representation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class CognitiveState(Enum):
    """Represents the current cognitive processing state."""

    IDLE = "idle"  # No active processing
    PROCESSING = "processing"  # Actively processing input
    FOCUSED = "focused"  # Deep focus state, high attention
    OVERLOADED = "overloaded"  # Cognitive capacity exceeded
    RECOVERING = "recovering"  # Transitioning from overload
    FLOW = "flow"  # Optimal performance state


class ProcessingMode(Enum):
    """Dual-process theory processing modes."""

    SYSTEM_1 = "system_1"  # Fast, automatic, intuitive
    SYSTEM_2 = "system_2"  # Slow, deliberate, analytical


class AttentionLevel(Enum):
    """Attention allocation levels."""

    AMBIENT = "ambient"  # Background awareness
    PERIPHERAL = "peripheral"  # Edge of attention
    FOCUSED = "focused"  # Direct attention
    ABSORBED = "absorbed"  # Deep concentration


class CoffeeMode(Enum):
    """Coffee House metaphor for cognitive processing intensity.

    Inspired by the Coffee House concept in recognition.py.
    """

    ESPRESSO = "espresso"  # Ultra-focused, precision, 32-char chunks
    AMERICANO = "americano"  # Balanced exploration, 64-char chunks
    COLD_BREW = "cold_brew"  # Comprehensive analysis, 128-char chunks

    @property
    def chunk_size(self) -> int:
        """Get the processing chunk size for this mode."""
        sizes = {
            CoffeeMode.ESPRESSO: 32,
            CoffeeMode.AMERICANO: 64,
            CoffeeMode.COLD_BREW: 128,
        }
        return sizes[self]

    @property
    def cognitive_load_range(self) -> tuple[float, float]:
        """Get the cognitive load range for this mode."""
        ranges = {
            CoffeeMode.ESPRESSO: (0.0, 3.0),
            CoffeeMode.AMERICANO: (3.0, 7.0),
            CoffeeMode.COLD_BREW: (7.0, 10.0),
        }
        return ranges[self]


@dataclass
class CognitiveMetrics:
    """Comprehensive cognitive performance metrics.

    All values are normalized to 0.0-1.0 range unless otherwise specified.
    """

    # Core metrics
    attention_level: float = 0.5  # Current attention allocation
    cognitive_load: float = 0.2  # Current cognitive load (0-10 scale)
    processing_speed: float = 1.0  # Relative processing speed multiplier
    memory_usage: float = 0.3  # Working memory utilization
    error_rate: float = 0.0  # Recent error frequency

    # Extended metrics
    focus_duration: float = 0.0  # Time in focused state (seconds)
    context_switches: int = 0  # Number of context switches
    pattern_matches: int = 0  # Successful pattern recognitions
    decision_confidence: float = 0.8  # Confidence in decisions

    # Temporal metrics
    time_to_first_response: float = 0.0  # Latency (seconds)
    sustained_attention_score: float = 0.5  # Ability to maintain focus
    recovery_time: float = 0.0  # Time to recover from overload

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "attention_level": self.attention_level,
            "cognitive_load": self.cognitive_load,
            "processing_speed": self.processing_speed,
            "memory_usage": self.memory_usage,
            "error_rate": self.error_rate,
            "focus_duration": self.focus_duration,
            "context_switches": self.context_switches,
            "pattern_matches": self.pattern_matches,
            "decision_confidence": self.decision_confidence,
            "time_to_first_response": self.time_to_first_response,
            "sustained_attention_score": self.sustained_attention_score,
            "recovery_time": self.recovery_time,
        }

    def is_overloaded(self) -> bool:
        """Check if cognitive load indicates overload."""
        return self.cognitive_load > 8.0

    def is_optimal(self) -> bool:
        """Check if metrics indicate optimal cognitive state."""
        return 3.0 <= self.cognitive_load <= 6.0 and self.attention_level > 0.6 and self.error_rate < 0.1

    def get_coffee_mode(self) -> CoffeeMode:
        """Determine appropriate coffee mode based on metrics."""
        if self.cognitive_load < 3.0:
            return CoffeeMode.ESPRESSO
        elif self.cognitive_load < 7.0:
            return CoffeeMode.AMERICANO
        else:
            return CoffeeMode.COLD_BREW


@dataclass
class CognitiveContext:
    """Full cognitive context for a processing session.

    Combines state, metrics, and temporal information.
    """

    state: CognitiveState = CognitiveState.IDLE
    processing_mode: ProcessingMode = ProcessingMode.SYSTEM_1
    attention: AttentionLevel = AttentionLevel.FOCUSED
    metrics: CognitiveMetrics = field(default_factory=CognitiveMetrics)
    coffee_mode: CoffeeMode = CoffeeMode.AMERICANO

    # Session tracking
    session_id: str = ""
    user_id: str = ""
    started_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)

    # Context metadata
    domain: str = ""  # Current activity domain
    task_type: str = ""  # Type of task being performed
    expertise_level: str = "intermediate"  # novice, intermediate, expert

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "state": self.state.value,
            "processing_mode": self.processing_mode.value,
            "attention": self.attention.value,
            "metrics": self.metrics.to_dict(),
            "coffee_mode": self.coffee_mode.value,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "started_at": self.started_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "domain": self.domain,
            "task_type": self.task_type,
            "expertise_level": self.expertise_level,
        }

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.now()

    def get_session_duration(self) -> float:
        """Get session duration in seconds."""
        return (datetime.now() - self.started_at).total_seconds()

    def is_in_flow(self) -> bool:
        """Check if currently in flow state."""
        return self.state == CognitiveState.FLOW


@dataclass
class ActivityContext:
    """Context for a specific activity within a cognitive session."""

    activity_id: str
    activity_type: str
    source: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Priority scoring (from HunchEngine patterns)
    hunch_score: float = 0.0
    opportunistic_score: float = 0.0
    event_driven_score: float = 0.0
    reliability_rating: float = 0.0

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    parent_id: str | None = None
    thread_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert activity to dictionary."""
        return {
            "activity_id": self.activity_id,
            "activity_type": self.activity_type,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "hunch_score": self.hunch_score,
            "opportunistic_score": self.opportunistic_score,
            "event_driven_score": self.event_driven_score,
            "reliability_rating": self.reliability_rating,
            "metadata": self.metadata,
            "tags": self.tags,
            "parent_id": self.parent_id,
            "thread_id": self.thread_id,
        }

    def calculate_reliability(self) -> float:
        """Calculate composite reliability rating."""
        self.reliability_rating = (
            self.event_driven_score * 0.5 + self.opportunistic_score * 0.3 + self.hunch_score * 0.2
        )
        return self.reliability_rating
