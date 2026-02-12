"""Runtime behavior tracer for agent execution tracking."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import uuid4


class ExecutionOutcome(Enum):
    """Possible execution outcomes."""

    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    ERROR = "error"


class DecisionType(Enum):
    """Types of routing decisions."""

    ROUTE = "route"
    RETRY = "retry"
    FALLBACK = "fallback"
    ADAPT = "adapt"


@dataclass
class DecisionPoint:
    """A decision point during execution."""

    decision_type: DecisionType
    rationale: str
    confidence: float
    alternatives: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ExecutionBehavior:
    """Execution behavior trace for a single task."""

    trace_id: str = field(default_factory=lambda: str(uuid4()))
    case_id: str = ""
    agent_role: str = ""
    task_type: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    decisions: list[DecisionPoint] = field(default_factory=list)
    llm_calls: int = 0
    tokens_used: int = 0
    skills_retrieved: int = 0
    outcome: ExecutionOutcome | None = None

    @property
    def duration_ms(self) -> int:
        """Get duration in milliseconds."""
        if self.end_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() * 1000)
        return 0

    def add_decision(
        self,
        decision_type: DecisionType,
        rationale: str,
        confidence: float = 1.0,
        alternatives: list[str] | None = None,
    ) -> None:
        """Add a decision point to the trace."""
        self.decisions.append(
            DecisionPoint(
                decision_type=decision_type,
                rationale=rationale,
                confidence=confidence,
                alternatives=alternatives or [],
            )
        )


class RuntimeBehaviorTracer:
    """Traces runtime behavior for agent executions."""

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.traces: dict[str, ExecutionBehavior] = {}
        self.history: list[ExecutionBehavior] = []

    def start_trace(
        self, case_id: str, agent_role: str = "", task_type: str = ""
    ) -> ExecutionBehavior:
        """Start a new execution trace."""
        trace = ExecutionBehavior(case_id=case_id, agent_role=agent_role, task_type=task_type)
        self.traces[trace.trace_id] = trace
        return trace

    def end_trace(self, trace_id: str, outcome: ExecutionOutcome) -> ExecutionBehavior | None:
        """Finalize a trace with its outcome."""
        trace = self.traces.get(trace_id)
        if trace:
            trace.end_time = datetime.now()
            trace.outcome = outcome
            self.history.append(trace)
            if len(self.history) > self.max_history:
                self.history.pop(0)
            del self.traces[trace_id]
        return trace

    def get_trace(self, trace_id: str) -> ExecutionBehavior | None:
        """Get a trace by ID."""
        return self.traces.get(trace_id)

    def get_performance_stats(self) -> dict:
        """Get performance statistics from history."""
        if not self.history:
            return {}

        durations = [t.duration_ms for t in self.history if t.duration_ms > 0]
        success_count = sum(1 for t in self.history if t.outcome == ExecutionOutcome.SUCCESS)

        return {
            "total_executions": len(self.history),
            "success_rate": success_count / len(self.history) if self.history else 0,
            "p50_latency_ms": sorted(durations)[len(durations) // 2] if durations else 0,
            "p95_latency_ms": sorted(durations)[int(len(durations) * 0.95)] if durations else 0,
            "avg_llm_calls": sum(t.llm_calls for t in self.history) / len(self.history),
            "avg_tokens_used": sum(t.tokens_used for t in self.history) / len(self.history),
        }
