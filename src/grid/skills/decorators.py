"""Skill function decorators for automated calling and tracking."""

import functools
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class SkillConfig:
    """Configuration for skill decorators."""

    id: str
    name: str
    description: str
    version: str = "1.0.0"
    category: str = "low-level"
    timeout_ms: int = 30000
    retry_policy: dict[str, Any] | None = None


def skill_function(
    id: str,
    name: str,
    description: str,
    version: str = "1.0.0",
    category: str = "low-level",
    timeout_ms: int = 30000,
    retry_policy: dict[str, Any] | None = None,
):
    """Decorator to convert functions into skills with automated calling."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> dict[str, Any]:
            from .execution_tracker import ExecutionStatus, SkillExecutionTracker

            start_time = time.time()
            tracker = SkillExecutionTracker.get_instance()

            try:
                # Call the function
                result = func(*args, **kwargs)

                # Normalize result to dict format
                if not isinstance(result, dict):
                    result = {"result": result}

                # Add metadata
                execution_time_ms = int((time.time() - start_time) * 1000)
                result.update(
                    {
                        "skill_id": id,
                        "status": "success",
                        "execution_time_ms": execution_time_ms,
                    }
                )

                # Track execution
                tracker.track_execution(
                    skill_id=id,
                    input_args=kwargs,
                    output=result,
                    status=ExecutionStatus.SUCCESS,
                    execution_time_ms=execution_time_ms,
                )

                return result

            except Exception as e:
                execution_time_ms = int((time.time() - start_time) * 1000)
                # Track failure
                tracker.track_execution(
                    skill_id=id,
                    input_args=kwargs,
                    output=None,
                    error=str(e),
                    status=ExecutionStatus.FAILURE,
                    execution_time_ms=execution_time_ms,
                )
                raise

        # Register the skill automatically
        from .base import SimpleSkill
        from .registry import default_registry

        skill = SimpleSkill(id=id, name=name, description=description, handler=wrapper, version=version)
        default_registry.register(skill)

        return wrapper

    return decorator
