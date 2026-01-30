"""Locomotion engine for state movement and transitions."""

from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from .quantizer import Quantizer

from pydantic import BaseModel, Field

from .quantizer import QuantizationLevel, QuantizedState


class MovementDirection(str, Enum):
    """Movement directions in state space."""

    FORWARD = "forward"
    BACKWARD = "backward"
    LEFT = "left"
    RIGHT = "right"
    UP = "up"
    DOWN = "down"
    ROTATE = "rotate"
    SCALE = "scale"


class MovementResult(BaseModel):
    """Result of a movement operation."""

    success: bool = Field(description="Whether movement succeeded")
    new_state: QuantizedState | None = Field(default=None, description="New state after movement")
    distance: float = Field(default=0.0, description="Distance moved")
    direction: MovementDirection = Field(description="Movement direction")
    obstacles: list[str] = Field(default_factory=list, description="Obstacles encountered")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class LocomotionEngine:
    """Engine for locomotion and state space navigation."""

    def __init__(self, quantizer: Optional["Quantizer"] = None):
        """Initialize locomotion engine.

        Args:
            quantizer: Optional quantizer instance
        """
        from .quantizer import Quantizer

        self.quantizer = quantizer or Quantizer()
        self._obstacles: dict[str, Any] = {}
        self._movement_history: list[dict[str, Any]] = []

    def move(
        self,
        current_state: QuantizedState,
        direction: MovementDirection,
        distance: float = 1.0,
        level: QuantizationLevel | None = None,
    ) -> MovementResult:
        """Move from current state in a direction.

        Args:
            current_state: Current quantized state
            direction: Movement direction
            distance: Distance to move
            level: Quantization level for new state

        Returns:
            Movement result
        """
        # Calculate new values based on direction
        new_values = current_state.values.copy()

        # Apply movement transformation
        if direction == MovementDirection.FORWARD:
            new_values = self._move_forward(new_values, distance)
        elif direction == MovementDirection.BACKWARD:
            new_values = self._move_backward(new_values, distance)
        elif direction == MovementDirection.LEFT:
            new_values = self._move_left(new_values, distance)
        elif direction == MovementDirection.RIGHT:
            new_values = self._move_right(new_values, distance)
        elif direction == MovementDirection.UP:
            new_values = self._move_up(new_values, distance)
        elif direction == MovementDirection.DOWN:
            new_values = self._move_down(new_values, distance)
        elif direction == MovementDirection.ROTATE:
            new_values = self._rotate(new_values, distance)
        elif direction == MovementDirection.SCALE:
            new_values = self._scale(new_values, distance)

        # Check for obstacles
        obstacles = self._check_obstacles(new_values)

        # Create new state
        new_state = self.quantizer.transition(current_state, new_values, level)

        # Record movement
        self._movement_history.append(
            {
                "from_state": current_state.state_id,
                "to_state": new_state.state_id,
                "direction": direction,
                "distance": distance,
            }
        )

        return MovementResult(
            success=len(obstacles) == 0,
            new_state=new_state,
            distance=distance,
            direction=direction,
            obstacles=obstacles,
        )

    def _move_forward(self, values: dict[str, Any], distance: float) -> dict[str, Any]:
        """Move forward in state space."""
        # Default: increment a position-like value
        if "x" in values:
            values["x"] = values.get("x", 0.0) + distance
        elif "position" in values:
            values["position"] = values.get("position", 0.0) + distance
        return values

    def _move_backward(self, values: dict[str, Any], distance: float) -> dict[str, Any]:
        """Move backward in state space."""
        if "x" in values:
            values["x"] = values.get("x", 0.0) - distance
        elif "position" in values:
            values["position"] = values.get("position", 0.0) - distance
        return values

    def _move_left(self, values: dict[str, Any], distance: float) -> dict[str, Any]:
        """Move left in state space."""
        if "y" in values:
            values["y"] = values.get("y", 0.0) - distance
        return values

    def _move_right(self, values: dict[str, Any], distance: float) -> dict[str, Any]:
        """Move right in state space."""
        if "y" in values:
            values["y"] = values.get("y", 0.0) + distance
        return values

    def _move_up(self, values: dict[str, Any], distance: float) -> dict[str, Any]:
        """Move up in state space."""
        if "z" in values:
            values["z"] = values.get("z", 0.0) + distance
        return values

    def _move_down(self, values: dict[str, Any], distance: float) -> dict[str, Any]:
        """Move down in state space."""
        if "z" in values:
            values["z"] = values.get("z", 0.0) - distance
        return values

    def _rotate(self, values: dict[str, Any], angle: float) -> dict[str, Any]:
        """Rotate in state space."""
        if "rotation" in values:
            values["rotation"] = values.get("rotation", 0.0) + angle
        elif "theta" in values:
            values["theta"] = values.get("theta", 0.0) + angle
        return values

    def _scale(self, values: dict[str, Any], factor: float) -> dict[str, Any]:
        """Scale in state space."""
        if "scale" in values:
            values["scale"] = values.get("scale", 1.0) * factor
        return values

    def _check_obstacles(self, values: dict[str, Any]) -> list[str]:
        """Check for obstacles at given values.

        Args:
            values: State values to check

        Returns:
            List of obstacle identifiers
        """
        obstacles = []
        for obstacle_id, obstacle_def in self._obstacles.items():
            if self._values_in_obstacle(values, obstacle_def):
                obstacles.append(obstacle_id)
        return obstacles

    def _values_in_obstacle(self, values: dict[str, Any], obstacle: dict[str, Any]) -> bool:
        """Check if values are within an obstacle region."""
        # Simple bounding box check
        if "bounds" in obstacle:
            bounds = obstacle["bounds"]
            for key, value in values.items():
                if key in bounds:
                    min_val, max_val = bounds[key]
                    if not (min_val <= value <= max_val):
                        return False
            return True
        return False

    def add_obstacle(self, obstacle_id: str, bounds: dict[str, tuple[float, float]]) -> None:
        """Add an obstacle to the state space.

        Args:
            obstacle_id: Obstacle identifier
            bounds: Bounds for each dimension
        """
        self._obstacles[obstacle_id] = {"bounds": bounds}

    def remove_obstacle(self, obstacle_id: str) -> None:
        """Remove an obstacle.

        Args:
            obstacle_id: Obstacle identifier
        """
        self._obstacles.pop(obstacle_id, None)

    def get_movement_history(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get movement history.

        Args:
            limit: Maximum number of movements

        Returns:
            List of movement records
        """
        return self._movement_history[-limit:]
