"""Runtime Behavior Tracer for GRID Agentic System.

Tracks comprehensive execution behavior patterns, decision intelligence,
resource usage, and outcomes to enable adaptive learning and observability.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ExecutionOutcome(str, Enum):
    """Possible outcomes of an execution task."""

    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"
    PARTIAL = "partial"


@dataclass
class DecisionPoint:
    """A specific decision point within an agent's execution flow."""

    timestamp: float = field(default_factory=time.time)
    decision_type: str = "route"  # "route", "retry", "fallback", "adapt", "skill_select"
    context: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    rationale: str = ""
    alternatives_considered: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "decision_type": self.decision_type,
            "context": self.context,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "alternatives_considered": self.alternatives_considered,
        }


@dataclass
class ExecutionBehavior:
    """Comprehensive trace of an agent's execution behavior for a single task."""

    case_id: str
    agent_role: str
    task_type: str
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None

    # Decision Intelligence
    decisions: list[DecisionPoint] = field(default_factory=list)
    confidence: float = 1.0
    fallback_used: bool = False

    # Resource Usage
    llm_calls: int = 0
    total_tokens: int = 0
    skills_retrieved: int = 0
    skills_used: int = 0

    # Outcomes
    outcome: ExecutionOutcome = ExecutionOutcome.SUCCESS
    error_category: str | None = None
    recovery_strategy: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    def finalize(self, outcome: ExecutionOutcome = ExecutionOutcome.SUCCESS) -> None:
        """Finalize the trace with end time and outcome."""
        self.end_time = time.time()
        self.outcome = outcome

    @property
    def duration_ms(self) -> float:
        """Calculate duration in milliseconds."""
        if not self.end_time:
            return (time.time() - self.start_time) * 1000
        return (self.end_time - self.start_time) * 1000

    def add_decision(self, **kwargs: Any) -> None:
        """Add a decision point to the trace."""
        decision = DecisionPoint(**kwargs)
        self.decisions.append(decision)
        # Update overall confidence as a product of decision confidences (simple heuristic)
        self.confidence *= decision.confidence

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "case_id": self.case_id,
            "agent_role": self.agent_role,
            "task_type": self.task_type,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "decisions": [d.to_dict() for d in self.decisions],
            "confidence": self.confidence,
            "fallback_used": self.fallback_used,
            "llm_calls": self.llm_calls,
            "total_tokens": self.total_tokens,
            "skills_retrieved": self.skills_retrieved,
            "skills_used": self.skills_used,
            "outcome": self.outcome.value,
            "error_category": self.error_category,
            "recovery_strategy": self.recovery_strategy,
            "metadata": self.metadata,
        }


class RuntimeBehaviorTracer:
    """Manager for recording and collecting execution behavior traces."""

    def __init__(self):
        self._active_traces: dict[str, ExecutionBehavior] = {}
        self._history: list[ExecutionBehavior] = []
        self._max_history = 1000

    def start_trace(self, case_id: str, agent_role: str, task_type: str) -> ExecutionBehavior:
        """Start a new behavior trace."""
        trace = ExecutionBehavior(case_id=case_id, agent_role=agent_role, task_type=task_type)
        self._active_traces[trace.trace_id] = trace
        return trace

    def get_trace(self, trace_id: str) -> ExecutionBehavior | None:
        """Retrieve an active trace by ID."""
        return self._active_traces.get(trace_id)

    def end_trace(
        self, trace_id: str, outcome: ExecutionOutcome = ExecutionOutcome.SUCCESS
    ) -> ExecutionBehavior | None:
        """Finalize and archive an active trace."""
        trace = self._active_traces.pop(trace_id, None)
        if trace:
            trace.finalize(outcome)
            self._history.append(trace)
            if len(self._history) > self._max_history:
                self._history.pop(0)

            logger.info(
                f"📊 Behavior Trace Completed: {trace.agent_role}:{trace.task_type} "
                f"outcome={trace.outcome.value} duration={trace.duration_ms:.2f}ms"
            )
        return trace

    def get_history(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get history of completed traces."""
        return [t.to_dict() for t in self._history[-limit:]]
