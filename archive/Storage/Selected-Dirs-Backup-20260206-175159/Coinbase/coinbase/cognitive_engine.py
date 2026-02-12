"""Cognitive engine for tracking user state and interaction."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CognitiveLoad(Enum):
    """Levels of cognitive load."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class CognitiveState:
    """Represents the user's cognitive state."""

    load: CognitiveLoad = CognitiveLoad.MEDIUM
    confidence: float = 0.8
    processing_mode: str = "standard"
    interaction_count: int = 0
    last_interaction_time: str | None = None


@dataclass
class InteractionEvent:
    """An interaction event for cognitive tracking."""

    user_id: str
    action: str
    context: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: __import__("datetime").datetime.now().isoformat()
    )


class CognitiveEngine:
    """Tracks cognitive state and adapts based on user interaction."""

    def __init__(self) -> None:
        self.states: dict[str, CognitiveState] = {}
        self.interaction_history: list[InteractionEvent] = []

    def track_interaction(self, interaction: InteractionEvent) -> CognitiveState:
        """Track an interaction and update cognitive state."""
        user_id = interaction.user_id

        # Get or create state
        if user_id not in self.states:
            self.states[user_id] = CognitiveState()

        state = self.states[user_id]

        # Update interaction tracking
        state.interaction_count += 1
        state.last_interaction_time = interaction.timestamp

        # Record interaction
        self.interaction_history.append(interaction)

        # Adjust cognitive load based on interaction
        self._update_cognitive_load(state, interaction)

        # Adjust processing mode based on load
        self._adjust_processing_mode(state)

        return state

    def _update_cognitive_load(self, state: CognitiveState, interaction: InteractionEvent) -> None:
        """Update cognitive load based on interaction patterns."""
        action = interaction.action.lower()

        # High cognitive load indicators
        if any(x in action for x in ["error", "fail", "retry", "confused"]):
            state.load = CognitiveLoad.HIGH
            state.confidence = max(0.0, state.confidence - 0.1)
        # Low cognitive load indicators
        elif any(x in action for x in ["success", "complete", "done", "understand"]):
            state.load = CognitiveLoad.LOW
            state.confidence = min(1.0, state.confidence + 0.1)
        # Medium cognitive load
        else:
            state.load = CognitiveLoad.MEDIUM

    def _adjust_processing_mode(self, state: CognitiveState) -> None:
        """Adjust processing mode based on cognitive load."""
        if state.load == CognitiveLoad.HIGH:
            state.processing_mode = "scaffolded"  # Provide more guidance
        elif state.load == CognitiveLoad.LOW:
            state.processing_mode = "autonomous"  # Let user lead
        else:
            state.processing_mode = "standard"

    def get_state(self, user_id: str) -> CognitiveState | None:
        """Get cognitive state for a user."""
        return self.states.get(user_id)

    def should_apply_scaffolding(self, user_id: str) -> bool:
        """Check if scaffolding should be applied based on cognitive load."""
        state = self.get_state(user_id)
        return state is not None and state.load == CognitiveLoad.HIGH
