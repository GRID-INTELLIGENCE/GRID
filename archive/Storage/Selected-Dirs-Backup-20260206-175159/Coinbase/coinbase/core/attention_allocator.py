"""
Attention Allocator
===================
Selective attention allocation - Compass pattern.

Reference: Compass - Points to direction (focus allocation)
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class FocusLevel(Enum):
    """Focus intensity levels."""

    LOW = 0.3
    MEDIUM = 0.5
    HIGH = 0.7
    EXTREME = 0.9


@dataclass
class FocusAllocation:
    """Focus allocation result."""

    task: str
    priority: float
    timestamp: datetime
    focus_intensity: float
    direction: str
    estimated_duration: float | None = None


class AttentionAllocator:
    """
    Selective attention allocation system.

    Like a Compass pointing to direction.
    Allocates focus based on priority and context.
    """

    def __init__(self) -> None:
        """Initialize attention allocator."""
        self.current_focus: FocusAllocation | None = None
        self.focus_history: list[FocusAllocation] = []
        self.max_history = 100

    def allocate(
        self,
        task: str,
        priority: float,
        context: dict[str, Any] | None = None,
        estimated_duration: float | None = None,
    ) -> FocusAllocation:
        """
        Allocate attention to a task.

        Args:
            task: Task description
            priority: Priority level (0.0 to 1.0)
            context: Additional context for allocation
            estimated_duration: Estimated duration in seconds

        Returns:
            FocusAllocation with allocation details
        """
        # Calculate focus intensity based on priority
        focus_intensity = self._calculate_focus(priority)

        # Determine direction like a Compass
        direction = self._determine_direction(focus_intensity)

        # Create allocation
        allocation = FocusAllocation(
            task=task,
            priority=priority,
            timestamp=datetime.now(),
            focus_intensity=focus_intensity,
            direction=direction,
            estimated_duration=estimated_duration,
        )

        # Update current focus
        self.current_focus = allocation

        # Add to history
        self.focus_history.append(allocation)
        if len(self.focus_history) > self.max_history:
            self.focus_history.pop(0)

        logger.info(
            f"Attention allocated: {task} | "
            f"Priority: {priority:.2f} | "
            f"Focus: {focus_intensity:.2f} | "
            f"Direction: {direction}"
        )

        return allocation

    def _calculate_focus(self, priority: float) -> float:
        """
        Calculate focus intensity.

        Args:
            priority: Priority level

        Returns:
            Focus intensity (0.0 to 1.0)
        """
        # 80% of priority determines focus
        return priority * 0.8

    def _determine_direction(self, focus_intensity: float) -> str:
        """
        Determine direction like a Compass.

        Args:
            focus_intensity: Focus intensity

        Returns:
            Direction string
        """
        if focus_intensity >= 0.8:
            return "NORTH"  # High priority
        elif focus_intensity >= 0.6:
            return "NORTHEAST"  # Medium-high
        elif focus_intensity >= 0.4:
            return "EAST"  # Medium
        elif focus_intensity >= 0.2:
            return "SOUTHEAST"  # Low-medium
        else:
            return "SOUTH"  # Low

    def get_focus_summary(self) -> dict[str, Any]:
        """
        Get summary of current and recent focus.

        Returns:
            Focus summary dictionary
        """
        if not self.focus_history:
            return {"current_focus": None, "total_allocations": 0, "average_focus": 0.0}

        recent = self.focus_history[-10:]
        average_focus = sum(f.focus_intensity for f in recent) / len(recent)

        return {
            "current_focus": (
                {
                    "task": self.current_focus.task if self.current_focus else None,
                    "priority": self.current_focus.priority if self.current_focus else 0.0,
                    "direction": self.current_focus.direction if self.current_focus else None,
                }
                if self.current_focus
                else None
            ),
            "total_allocations": len(self.focus_history),
            "average_focus": average_focus,
            "recent_tasks": [f.task for f in recent],
        }

    def clear_focus(self) -> None:
        """Clear current focus."""
        self.current_focus = None
        logger.info("Focus cleared")


# Example usage
def example_usage() -> None:
    """Example usage of AttentionAllocator."""
    allocator = AttentionAllocator()

    # Allocate focus to high priority task
    focus1 = allocator.allocate(
        task="Databricks integration", priority=0.9, estimated_duration=300.0
    )
    print(f"Focus 1: {focus1.task} | {focus1.direction} | {focus1.focus_intensity:.2f}")

    # Allocate focus to medium priority task
    focus2 = allocator.allocate(task="Portfolio analysis", priority=0.6, estimated_duration=180.0)
    print(f"Focus 2: {focus2.task} | {focus2.direction} | {focus2.focus_intensity:.2f}")

    # Get summary
    summary = allocator.get_focus_summary()
    print(f"\nTotal allocations: {summary['total_allocations']}")
    print(f"Average focus: {summary['average_focus']:.2f}")


if __name__ == "__main__":
    example_usage()
