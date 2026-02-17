"""Quantizer for discrete state representation."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class QuantizationLevel(StrEnum):
    """Quantization granularity levels."""

    COARSE = "coarse"  # Large steps, low precision
    MEDIUM = "medium"  # Balanced
    FINE = "fine"  # Small steps, high precision
    ULTRA_FINE = "ultra_fine"  # Very small steps, very high precision


class QuantizedState(BaseModel):
    """Quantized state representation."""

    state_id: str = Field(description="Unique state identifier")
    level: QuantizationLevel = Field(description="Quantization level")
    values: dict[str, Any] = Field(default_factory=dict, description="Quantized values")
    step_index: int = Field(default=0, description="Step index in sequence")
    parent_state_id: str | None = Field(default=None, description="Parent state ID")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class Quantizer:
    """Quantizes continuous values into discrete steps."""

    def __init__(self, default_level: QuantizationLevel = QuantizationLevel.MEDIUM):
        """Initialize quantizer.

        Args:
            default_level: Default quantization level
        """
        self.default_level = default_level
        self._level_configs = {
            QuantizationLevel.COARSE: {"step_size": 1.0, "precision": 1},
            QuantizationLevel.MEDIUM: {"step_size": 0.1, "precision": 2},
            QuantizationLevel.FINE: {"step_size": 0.01, "precision": 4},
            QuantizationLevel.ULTRA_FINE: {"step_size": 0.001, "precision": 6},
        }

    def quantize_value(self, value: float, level: QuantizationLevel | None = None) -> float:
        """Quantize a single value.

        Args:
            value: Value to quantize
            level: Quantization level (defaults to default_level)

        Returns:
            Quantized value
        """
        level = level or self.default_level
        config = self._level_configs[level]
        step_size = config["step_size"]

        quantized = round(value / step_size) * step_size
        return round(quantized, config["precision"])

    def quantize_dict(self, data: dict[str, Any], level: QuantizationLevel | None = None) -> dict[str, Any]:
        """Quantize all numeric values in a dictionary.

        Args:
            data: Dictionary to quantize
            level: Quantization level

        Returns:
            Quantized dictionary
        """
        level = level or self.default_level
        quantized: dict[str, Any] = {}

        for key, value in data.items():
            if isinstance(value, (int, float)):
                quantized[key] = self.quantize_value(float(value), level)
            elif isinstance(value, dict):
                quantized[key] = self.quantize_dict(value, level)
            elif isinstance(value, list):
                quantized[key] = [self.quantize_value(v, level) if isinstance(v, (int, float)) else v for v in value]
            else:
                quantized[key] = value

        return quantized

    def create_state(
        self,
        state_id: str,
        values: dict[str, Any],
        level: QuantizationLevel | None = None,
        step_index: int = 0,
        parent_state_id: str | None = None,
    ) -> QuantizedState:
        """Create a quantized state.

        Args:
            state_id: State identifier
            values: State values
            level: Quantization level
            step_index: Step index
            parent_state_id: Parent state ID

        Returns:
            Quantized state
        """
        level = level or self.default_level
        quantized_values = self.quantize_dict(values, level)

        return QuantizedState(
            state_id=state_id,
            level=level,
            values=quantized_values,
            step_index=step_index,
            parent_state_id=parent_state_id,
        )

    def transition(
        self,
        from_state: QuantizedState,
        to_values: dict[str, Any],
        level: QuantizationLevel | None = None,
    ) -> QuantizedState:
        """Create a transition to a new state.

        Args:
            from_state: Source state
            to_values: Target values
            level: Quantization level (defaults to from_state level)

        Returns:
            New quantized state
        """
        level = level or from_state.level
        new_state_id = f"{from_state.state_id}_step_{from_state.step_index + 1}"

        return self.create_state(
            state_id=new_state_id,
            values=to_values,
            level=level,
            step_index=from_state.step_index + 1,
            parent_state_id=from_state.state_id,
        )

    def get_step_size(self, level: QuantizationLevel | None = None) -> float:
        """Get step size for a quantization level.

        Args:
            level: Quantization level

        Returns:
            Step size
        """
        level = level or self.default_level
        return self._level_configs[level]["step_size"]
