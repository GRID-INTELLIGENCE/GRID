"""Main agentic system orchestrator."""

from dataclasses import dataclass
from typing import Any

from .agent_executor import AgentExecutor, ExecutionResult
from .core.interfaces import IEventBus, ILearningCoordinator, ITracer
from .events import CaseCompletedEvent, CaseExecutedEvent, EventBus
from .learning_coordinator import LearningCoordinator
from .skill_generator import SkillGenerator
from .tracer import RuntimeBehaviorTracer


@dataclass
class SystemConfig:
    """Configuration for the agentic system."""

    skill_store_path: str | None = None
    max_traces: int = 1000
    max_retry_attempts: int = 3


class AgenticSystem:
    """Main agentic system orchestrator for GRID execution."""

    def __init__(
        self,
        config: SystemConfig | None = None,
        tracer: ITracer | None = None,
        event_bus: IEventBus | None = None,
        executor: AgentExecutor | None = None,
        skill_generator: SkillGenerator | None = None,
        learning_coordinator: ILearningCoordinator | None = None,
    ):
        self.config = config or SystemConfig()

        # Core components with Dependency Injection
        self.tracer = tracer or RuntimeBehaviorTracer(max_history=self.config.max_traces)
        self.event_bus = event_bus or EventBus()
        self.learning_coordinator = learning_coordinator or LearningCoordinator()

        self.executor = executor or AgentExecutor(
            tracer=self.tracer if isinstance(self.tracer, ITracer) else None,
            event_bus=self.event_bus if isinstance(self.event_bus, IEventBus) else None,
            learning_coordinator=self.learning_coordinator,
        )

        self.skill_generator = skill_generator or SkillGenerator(
            event_bus=self.event_bus if isinstance(self.event_bus, IEventBus) else self.event_bus,  # type: ignore
            skill_store_path=Path(self.config.skill_store_path) if self.config.skill_store_path else None,  # type: ignore
        )

        # Wire up event subscriptions for decoupled modules
        if hasattr(self.learning_coordinator, "handle_execution_completed"):
            self.event_bus.subscribe(
                "execution_completed", self.learning_coordinator.handle_execution_completed
            )

        # Subscribe to orchestration events
        self.event_bus.subscribe("case_executed", self._handle_case_executed)
        self.event_bus.subscribe("case_completed", self._handle_case_completed)

    def execute_case(
        self, case_id: str, task: str, agent_role: str = "Executor", reference: Any | None = None
    ) -> dict[str, Any]:
        """Execute a case with full orchestration and tracking."""
        start_time = __import__("datetime").datetime.now()

        # Execute task
        result: ExecutionResult = self.executor.execute_task(
            case_id=case_id, task=task, agent_role=agent_role, reference=reference
        )

        execution_time = (__import__("datetime").datetime.now() - start_time).total_seconds()

        # Publish execution event
        executed_event = CaseExecutedEvent(case_id=case_id, agent_role=agent_role, task=task)
        self.event_bus.publish({"type": "case_executed", **executed_event.__dict__})

        # Publish completion event
        completed_event = CaseCompletedEvent(
            case_id=case_id,
            outcome="success" if result.success else "failure",
            solution=str(result.result) if result.result else "",
            agent_experience={
                "execution_time_seconds": execution_time,
                "agent_role": agent_role,
                "task": task,
            },
            execution_time_seconds=execution_time,
        )
        self.event_bus.publish({"type": "case_completed", **completed_event.__dict__})

        return {
            "case_id": case_id,
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "duration_ms": result.duration_ms,
            "execution_time_seconds": execution_time,
        }

    def _handle_case_executed(self, event: dict[str, Any]) -> None:
        """Handle case executed event."""
        print(f"[AgenticSystem] Case executed: {event.get('case_id')}")

    def _handle_case_completed(self, event: dict[str, Any]) -> None:
        """Handle case completed event."""
        outcome = event.get("outcome")
        case_id = event.get("case_id")
        print(f"[AgenticSystem] Case completed: {case_id} - {outcome}")

    def register_handler(self, task_type: str, handler: Any) -> None:
        """Register a task handler."""
        self.executor.register_handler(task_type, handler)

    def get_performance_stats(self) -> dict[str, Any]:
        """Get system performance statistics."""
        return self.tracer.get_performance_stats()

    def get_learning_summary(self) -> dict[str, Any]:
        """Get learning coordinator summary."""
        return self.learning_coordinator.get_learning_summary()
