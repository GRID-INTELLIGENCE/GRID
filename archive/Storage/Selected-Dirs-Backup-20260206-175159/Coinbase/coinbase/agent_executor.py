from collections.abc import Callable
from typing import Any

from .agent_executor_types import ExecutionResult
from .core.interfaces import IEventBus, ILearningCoordinator, IRecoveryEngine, ITracer
from .error_recovery import RecoveryEngine
from .learning_coordinator import LearningCoordinator
from .tracer import (
    DecisionType,
    ExecutionOutcome,
    RuntimeBehaviorTracer,
)


class AgentExecutor:
    """Executes agent tasks with comprehensive behavior tracking."""

    def __init__(
        self,
        tracer: ITracer | None = None,
        event_bus: IEventBus | None = None,
        recovery_engine: IRecoveryEngine | None = None,
        learning_coordinator: ILearningCoordinator | None = None,
    ) -> None:
        self.tracer = tracer or RuntimeBehaviorTracer()
        self.event_bus = event_bus  # Optional event bus for broadcasting results
        self.recovery_engine = recovery_engine or RecoveryEngine()
        self.learning_coordinator = learning_coordinator or LearningCoordinator()
        self.handlers: dict[str, Callable] = {}

    def register_handler(self, task_type: str, handler: Callable) -> None:
        """Register a handler for a specific task type."""
        self.handlers[task_type] = handler

    def execute_task(
        self, case_id: str, task: str, agent_role: str = "Executor", reference: Any | None = None
    ) -> ExecutionResult:
        """Execute a task with full behavior tracking and recovery."""
        # Start execution trace
        trace = self.tracer.start_trace(case_id=case_id, agent_role=agent_role, task_type=task)

        # Log routing decision
        handler = self.handlers.get(task)
        if handler:
            trace.add_decision(
                decision_type=DecisionType.ROUTE,
                rationale=f"Routing {task} to {handler.__name__}",
                confidence=1.0,
            )

        try:
            # Execute with recovery
            result = self.recovery_engine.execute_with_recovery(
                self._execute_task_by_type,
                case_id=case_id,
                task=task,
                reference=reference,
                agent_role=agent_role,
                trace=trace,
            )

            # Record outcome
            self.tracer.end_trace(trace.trace_id, ExecutionOutcome.SUCCESS)

            # Publish completion event if bus is available
            if self.event_bus:
                self.event_bus.publish(
                    {
                        "type": "execution_completed",
                        "case_id": case_id,
                        "trace_id": trace.trace_id,
                        "outcome": ExecutionOutcome.SUCCESS,
                        "duration_ms": trace.duration_ms,
                    }
                )
            else:
                # Fallback to direct call if no event bus (backward compatibility)
                self.learning_coordinator.record_execution_outcome(
                    case_id=case_id,
                    trace_id=trace.trace_id,
                    outcome=ExecutionOutcome.SUCCESS,
                    duration_ms=trace.duration_ms,
                )

            return ExecutionResult(success=True, result=result, duration_ms=trace.duration_ms)

        except Exception as e:
            # Record failure
            self.tracer.end_trace(trace.trace_id, ExecutionOutcome.FAILURE)

            if self.event_bus:
                self.event_bus.publish(
                    {
                        "type": "execution_completed",
                        "case_id": case_id,
                        "trace_id": trace.trace_id,
                        "outcome": ExecutionOutcome.FAILURE,
                        "duration_ms": trace.duration_ms,
                    }
                )
            else:
                self.learning_coordinator.record_execution_outcome(
                    case_id=case_id,
                    trace_id=trace.trace_id,
                    outcome=ExecutionOutcome.FAILURE,
                    duration_ms=trace.duration_ms,
                )

            return ExecutionResult(
                success=False, result=None, error=str(e), duration_ms=trace.duration_ms
            )

    def _execute_task_by_type(
        self,
        case_id: str,
        task: str,
        reference: Any | None,
        agent_role: str,
        trace: Any,  # ExecutionBehavior
    ) -> Any:
        """Execute task by type with handler dispatch."""
        handler = self.handlers.get(task)

        if handler is None:
            raise ValueError(f"No handler registered for task type: {task}")

        # Update trace with resource usage if it has these attributes
        if hasattr(trace, "llm_calls"):
            trace.llm_calls += 1
        if hasattr(trace, "tokens_used"):
            trace.tokens_used += 100  # Placeholder

        return handler(case_id, reference, agent_role)
