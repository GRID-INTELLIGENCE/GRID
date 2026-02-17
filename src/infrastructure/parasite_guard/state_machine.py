from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum, StrEnum, auto


class GuardState(StrEnum):
    INITIALIZING = auto()
    MONITORING = auto()
    DETECTING = auto()
    MITIGATING = auto()
    ALERTING = auto()


class InvalidTransitionError(Exception):
    def __init__(self, from_state: GuardState, to_state: GuardState):
        self.message = f"Invalid transition from {from_state} to {to_state}"
        super().__init__(self.message)


@dataclass
class TransitionProbability:
    """Probability weights for state transitions."""

    to_state: GuardState
    probability: float  # 0.0 to 1.0
    confidence: float  # Statistical confidence


@dataclass
class TransitionRecord:
    """Record of a state transition."""

    from_state: GuardState
    to_state: GuardState
    timestamp: datetime
    confidence: float = 1.0


class ParasiteGuardStateMachine:
    """Manages guard state transitions with probabilistic validation."""

    VALID_TRANSITIONS: dict[GuardState, list[TransitionProbability]] = {
        GuardState.INITIALIZING: [TransitionProbability(GuardState.MONITORING, 1.0, 1.0)],
        GuardState.MONITORING: [TransitionProbability(GuardState.DETECTING, 0.95, 0.95)],
        GuardState.DETECTING: [
            TransitionProbability(GuardState.MITIGATING, 0.98, 0.98),
            TransitionProbability(GuardState.MONITORING, 0.02, 0.95),  # False positive
        ],
        GuardState.MITIGATING: [
            TransitionProbability(GuardState.MONITORING, 0.90, 0.90),  # Resolved
            TransitionProbability(GuardState.ALERTING, 0.10, 0.95),  # Critical
        ],
        GuardState.ALERTING: [TransitionProbability(GuardState.MONITORING, 1.0, 1.0)],
    }

    def __init__(self):
        self.state = GuardState.INITIALIZING
        self._transition_history: list[tuple[GuardState, GuardState, datetime]] = []

    def transition(self, to_state: GuardState, confidence: float = 1.0) -> bool:
        valid_transitions = {t.to_state for t in self.VALID_TRANSITIONS.get(self.state, [])}
        if to_state not in valid_transitions:
            raise InvalidTransitionError(self.state, to_state)

        self._transition_history.append((self.state, to_state, datetime.now(UTC)))
        self._emit_metric(self.state, to_state, confidence)
        self.state = to_state
        return True

    def _emit_metric(self, from_state: GuardState, to_state: GuardState, confidence: float) -> None:
        """Emit Prometheus metrics for state transition."""
        try:
            from .metrics import record_state_transition

            # Calculate duration in previous state (approximate)
            if self._transition_history:
                last_transition = self._transition_history[-1]
                duration = (datetime.now(UTC) - last_transition[2]).total_seconds()
            else:
                duration = 0.0

            record_state_transition(
                from_state=from_state.name,
                to_state=to_state.name,
                confidence=confidence,
                duration_in_previous_state=duration,
            )
        except ImportError:
            pass  # Metrics not available

    def get_transition_stats(self) -> dict[str, float]:
        """Calculate transition success rates for monitoring."""
        return {
            "total_transitions": len(self._transition_history),
            "alerting_rate": self._calculate_alerting_rate(),
            "resolution_rate": self._calculate_resolution_rate(),
        }

    def _calculate_alerting_rate(self) -> float:
        if not self._transition_history:
            return 0.0
        alerts = sum(1 for _, to_s, _ in self._transition_history if to_s == GuardState.ALERTING)
        return alerts / len(self._transition_history)

    def _calculate_resolution_rate(self) -> float:
        # Assuming resolution is specific to MITIGATING -> MONITORING
        mitigations = [t for t in self._transition_history if t[0] == GuardState.MITIGATING]
        if not mitigations:
            return 0.0
        resolutions = sum(1 for _, to_s, _ in mitigations if to_s == GuardState.MONITORING)
        return resolutions / len(mitigations)
