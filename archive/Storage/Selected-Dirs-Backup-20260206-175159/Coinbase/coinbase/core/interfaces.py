"""Core interfaces for the GRID agentic system."""

from collections.abc import Callable
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ITracer(Protocol):
    """Protocol for behavior tracking."""

    def start_trace(self, case_id: str, agent_role: str, task_type: str) -> Any: ...
    def end_trace(self, trace_id: str, outcome: Any) -> None: ...
    def get_performance_stats(self) -> dict[str, Any]: ...


@runtime_checkable
class IEventBus(Protocol):
    """Protocol for event-driven communication."""

    def publish(self, event: dict[str, Any]) -> None: ...
    def subscribe(self, event_type: str, handler: Callable[[dict[str, Any]], None]) -> None: ...


@runtime_checkable
class IRecoveryEngine(Protocol):
    """Protocol for error recovery."""

    def execute_with_recovery(self, task_fn: Callable, *args: Any, **kwargs: Any) -> Any: ...


@runtime_checkable
class ILearningCoordinator(Protocol):
    """Protocol for learning and skill ranking."""

    def record_execution_outcome(
        self, case_id: str, trace_id: str, outcome: Any, duration_ms: int
    ) -> None: ...
    def get_learning_summary(self) -> dict[str, Any]: ...
    def get_ranked_skills(self, limit: int = 10) -> list[Any]: ...


@runtime_checkable
class IExecutor(Protocol):
    """Protocol for task execution."""

    def execute_task(
        self, case_id: str, task: str, agent_role: str = "Executor", reference: Any | None = None
    ) -> Any: ...
    def register_handler(self, task_type: str, handler: Callable) -> None: ...
