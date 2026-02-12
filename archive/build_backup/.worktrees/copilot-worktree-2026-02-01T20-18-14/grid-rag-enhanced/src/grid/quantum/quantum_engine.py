"""Quantum engine combining quantizer and locomotion."""

from typing import Any

from .locomotion import LocomotionEngine, MovementDirection, MovementResult
from .quantizer import QuantizationLevel, QuantizedState, Quantizer


class QuantumEngine:
    """Unified engine for quantized architecture with locomotion."""

    def __init__(self, default_level: QuantizationLevel = QuantizationLevel.MEDIUM):
        """Initialize quantum engine.

        Args:
            default_level: Default quantization level
        """
        self.quantizer = Quantizer(default_level=default_level)
        self.locomotion = LocomotionEngine(quantizer=self.quantizer)
        self._current_state: QuantizedState | None = None

    def initialize_state(
        self,
        state_id: str,
        values: dict[str, Any],
        level: QuantizationLevel | None = None,
    ) -> QuantizedState:
        """Initialize a quantized state.

        Args:
            state_id: State identifier
            values: Initial state values
            level: Quantization level

        Returns:
            Quantized state
        """
        self._current_state = self.quantizer.create_state(state_id, values, level)
        return self._current_state

    def get_current_state(self) -> QuantizedState | None:
        """Get current state."""
        return self._current_state

    def move(
        self,
        direction: MovementDirection,
        distance: float = 1.0,
        level: QuantizationLevel | None = None,
    ) -> MovementResult:
        """Move from current state.

        Args:
            direction: Movement direction
            distance: Distance to move
            level: Quantization level

        Returns:
            Movement result
        """
        if not self._current_state:
            raise ValueError("No current state. Call initialize_state first.")

        result = self.locomotion.move(self._current_state, direction, distance, level)
        if result.success and result.new_state:
            self._current_state = result.new_state

        return result

    def transition_to(
        self,
        target_values: dict[str, Any],
        level: QuantizationLevel | None = None,
    ) -> QuantizedState:
        """Transition directly to target values.

        Args:
            target_values: Target state values
            level: Quantization level

        Returns:
            New quantized state
        """
        if not self._current_state:
            raise ValueError("No current state. Call initialize_state first.")

        new_state = self.quantizer.transition(self._current_state, target_values, level)
        self._current_state = new_state
        return new_state

    def get_state_sequence(self, limit: int = 10) -> list[QuantizedState]:
        """Get sequence of states from root to current.

        Args:
            limit: Maximum number of states

        Returns:
            List of states from root to current
        """
        if not self._current_state:
            return []

        sequence = []
        current = self._current_state
        count = 0

        while current and count < limit:
            sequence.insert(0, current)
            if current.parent_state_id:
                # In a real implementation, we'd look up the parent state
                # For now, we'll just return the sequence we have
                break
            count += 1

        return sequence
