from __future__ import annotations

import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol


class Skill(Protocol):
    """Protocol defining the skill interface."""

    id: str
    name: str
    description: str
    version: str  # Semantic version for contract stability

    def run(self, args: Mapping[str, Any]) -> dict[str, Any]: ...


@dataclass(frozen=True)
class SimpleSkill:
    """Simple skill implementation with handler function."""

    id: str
    name: str
    description: str
    handler: Any
    version: str = "1.0.0"  # Default version for backwards compatibility

    def run(self, args: Mapping[str, Any]) -> dict[str, Any]:
        """Run skill with execution tracking."""
        from .execution_tracker import ExecutionStatus, SkillExecutionTracker

        start_time = time.time()
        tracker = SkillExecutionTracker.get_instance()

        try:
            result = self.handler(args)

            # Track successful execution
            tracker.track_execution(
                skill_id=self.id,
                input_args=dict(args),
                output=result,
                status=ExecutionStatus.SUCCESS,
                confidence_score=result.get("confidence") if isinstance(result, dict) else None,
                fallback_used=result.get("fallback_used", False) if isinstance(result, dict) else False,
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

            return result

        except Exception as e:
            # Track failed execution
            tracker.track_execution(
                skill_id=self.id,
                input_args=dict(args),
                output=None,
                error=str(e),
                status=ExecutionStatus.FAILURE,
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
            raise
