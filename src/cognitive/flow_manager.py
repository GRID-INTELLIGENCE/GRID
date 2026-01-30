"""Advanced Flow Manager.

Implements flow optimization with:
- Topological sort for task dependency resolution
- Priority weighting for task ordering
- Flow state detection and transitions
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class FlowState(str, Enum):
    """States for cognitive flow."""

    BLOCKED = "blocked"
    ACTIVE = "active"
    COMPLETED = "completed"
    SUSPENDED = "suspended"
    INTERRUPTED = "interrupted"
    STUCK = "stuck"


class TaskPriority(str, Enum):
    """Priority levels for tasks within flow."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class FlowTask:
    """A task within a cognitive flow."""

    task_id: str
    name: str
    priority: TaskPriority
    dependencies: list[str] = field(default_factory=list)
    estimated_duration_seconds: int = 0
    status: FlowState = FlowState.BLOCKED
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FlowMetadata:
    """Metadata about the overall flow."""

    flow_id: str
    name: str
    state: FlowState
    total_tasks: int
    completed_tasks: int
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    current_task: str | None = None
    momentum_score: float = 0.0  # -1.0 to 1.0


@dataclass
class FlowOptimizationResult:
    """Result of flow optimization."""

    original_order: list[str]
    optimized_order: list[str]
    optimization_score: float = 0.0  # Higher is better
    estimated_time_savings_seconds: float = 0.0
    topological_violations: int = 0  # Count of dependency violations


class AdvancedFlowManager:
    """Advanced flow manager with topological sort and priority weighting.

    Features:
    - Topological sort for task dependency resolution
    - Priority weighting for task ordering
    - Flow state detection and transitions
    - Bottleneck identification
    - Critical path analysis
    """

    def __init__(self):
        self._tasks: dict[str, FlowTask] = {}
        self._flows: dict[str, FlowMetadata] = {}
        self._dependency_graph: dict[str, list[str]] = defaultdict(list)
        self._momentum_scores: dict[str, float] = defaultdict(float)
        self._last_optimization = datetime.now(UTC)

    def add_task(
        self,
        task_id: str,
        name: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        dependencies: list[str] | None = None,
        estimated_duration_seconds: int = 60,
    ) -> None:
        """Add a task to the current flow.

        Args:
            task_id: Unique task identifier
            name: Task name
            priority: Task priority level
            dependencies: Task IDs this task depends on
            estimated_duration_seconds: Estimated duration in seconds
        """
        task = FlowTask(
            task_id=task_id,
            name=name,
            priority=priority,
            dependencies=dependencies or [],
            estimated_duration_seconds=estimated_duration_seconds,
        )

        self._tasks[task_id] = task
        logger.info(f"Added task: {task_id} ({name}, priority={priority.value})")

    def add_dependency(self, task_id: str, depends_on: str) -> None:
        """Add a dependency relationship between tasks.

        Args:
            task_id: Task ID that depends on another task
            depends_on: Task ID that must complete first
        """
        if task_id not in self._tasks:
            logger.warning(f"Task {task_id} not found when adding dependency")
            return None

        if depends_on not in self._tasks:
            logger.warning(f"Task {depends_on} not found when adding dependency")
            return None

        self._dependency_graph[depends_on].append(task_id)
        logger.debug(f"Added dependency: {task_id} -> {depends_on}")

    def complete_task(self, task_id: str) -> None:
        """Mark a task as completed.

        Args:
            task_id: Task ID to complete
        """
        if task_id not in self._tasks:
            logger.warning(f"Task {task_id} not found")
            return None

        task = self._tasks[task_id]
        task.status = FlowState.COMPLETED
        task.completed_at = datetime.now(UTC)

        # Update momentum for future tasks
        task_priority = task.priority
        if task_priority == TaskPriority.CRITICAL:
            self._momentum_scores["critical"] += 0.2
        elif task_priority == TaskPriority.HIGH:
            self._momentum_scores["high"] += 0.1
        elif task_priority == TaskPriority.MEDIUM:
            self._momentum_scores["medium"] += 0.05

        logger.info(f"Completed task: {task_id} ({task.name})")

    def optimize_flow_order(self) -> FlowOptimizationResult:
        """Optimize task order using topological sort and priority weighting.

        Returns:
            Optimization result with optimal task ordering
        """
        if not self._tasks:
            return FlowOptimizationResult(
                original_order=[],
                optimized_order=[],
                optimization_score=0.0,
            )

        # Kahn's algorithm for topological sort
        in_degree = {task_id: len(self._dependency_graph[task_id]) for task_id in self._tasks}
        topological_order = []

        while in_degree:
            # Find task with no dependencies (in_degree = 0)
            ready_tasks = [tid for tid, deg in in_degree.items() if deg == 0]

            if not ready_tasks:
                logger.warning("Circular dependency detected in flow graph")
                return FlowOptimizationResult(
                    original_order=list(self._tasks.keys()),
                    optimized_order=list(self._tasks.keys()),
                    optimization_score=0.0,
                    topological_violations=len(self._tasks),
                )

            # Select first available task
            task = self._tasks[ready_tasks[0]]
            topological_order.append(task.task_id)

            # Remove completed dependencies
            for dep_id in list(task.dependencies):
                if dep_id in in_degree:
                    in_degree[dep_id] -= 1

        # Apply priority weighting to available tasks
        weighted_scores = {}
        for tid, task in self._tasks.items():
            if tid not in topological_order:
                # Task already processed
                continue

            priority_weight = {
                TaskPriority.CRITICAL: 3.0,
                TaskPriority.HIGH: 2.0,
                TaskPriority.MEDIUM: 1.0,
                TaskPriority.LOW: 0.5,
            }[task.priority]
            momentum_score = self._momentum_scores.get(task.priority.value, 1.0)

            weighted_score = priority_weight + (momentum_score * 0.1)
            weighted_scores[tid] = weighted_score

        # Reorder by weighted score
        remaining_tasks = [
            tid for tid in topological_order if tid not in weighted_scores
        ]
        remaining_tasks_sorted = sorted(remaining_tasks, key=lambda tid: weighted_scores[tid], reverse=True)

        optimized_order = topological_order + remaining_tasks_sorted

        # Calculate optimization score
        # Higher score is better - measures how many high priority tasks are ready
        ready_critical = sum(1 for tid, task in self._tasks.items()
                               if task.status == FlowState.COMPLETED and task.priority == TaskPriority.CRITICAL)
        ready_high = sum(1 for tid, task in self._tasks.items()
                            if task.status == FlowState.COMPLETED and task.priority == TaskPriority.HIGH)

        optimization_score = (ready_critical + ready_high) / len(self._tasks)

        logger.info(
            f"Flow optimized: {len(self._tasks)} tasks, "
            f"score={optimization_score:.2f}, violations={len(in_degree) - len(topological_order)}"
        )

        return FlowOptimizationResult(
            original_order=list(self._tasks.keys()),
            optimized_order=optimized_order,
            optimization_score=optimization_score,
            topological_violations=len(in_degree) - len(topological_order),
        )

    def get_flow_state(self, flow_id: str) -> FlowMetadata:
        """Get the current state of a flow.

        Args:
            flow_id: Flow identifier

        Returns:
            Flow metadata with current state
        """
        if flow_id not in self._flows:
            logger.warning(f"Flow {flow_id} not found")
            return None

        flow = self._flows[flow_id]

        # Count tasks by state
        state_counts = defaultdict(int)
        for task in self._tasks.values():
            state_counts[task.status.value] += 1

        # Calculate momentum score
        active_tasks = [t for t in self._tasks.values() if t.status == FlowState.ACTIVE]
        current_momentum = self._calculate_flow_momentum(active_tasks, self._tasks)

        # Determine overall state
        if any(t.status == FlowState.BLOCKED for t in self._tasks.values()):
            state = FlowState.BLOCKED
        elif any(t.status == FlowState.SUSPENDED for t in self._tasks.values()):
            state = FlowState.SUSPENDED
        elif any(t.status == FlowState.STUCK for t in self._tasks.values()):
            state = FlowState.STUCK
        elif state_counts[FlowState.COMPLETED] == len(self._tasks):
            state = FlowState.COMPLETED
        elif state_counts[FlowState.ACTIVE] > 0:
            state = FlowState.ACTIVE
        else:
            state = FlowState.INTERRUPTED

        return FlowMetadata(
            flow_id=flow_id,
            name=flow.name,
            state=state,
            total_tasks=len(self._tasks),
            completed_tasks=state_counts[FlowState.COMPLETED],
            momentum_score=current_momentum,
        )

    def _calculate_flow_momentum(self, active_tasks: list[FlowTask], all_tasks: dict[str, FlowTask]) -> float:
        """Calculate momentum score for flow based on task completion.

        Args:
            active_tasks: Currently active tasks
            all_tasks: All tasks in the flow

        Returns:
            Momentum score (-1.0 to 1.0)
        """
        if not active_tasks:
            return 0.0

        momentum_score = 0.0

        # Base momentum
        completed_ratio = sum(1 for t in all_tasks.values() if t.status == FlowState.COMPLETED) / len(all_tasks)
        momentum_score += completed_ratio * 0.5

        # Bonus for having active tasks (prevents stalling)
        active_ratio = len(active_tasks) / len(all_tasks)
        momentum_score += active_ratio * 0.3

        # Penalty for too many blocked tasks
        blocked_ratio = sum(1 for t in all_tasks.values() if t.status == FlowState.BLOCKED) / len(all_tasks)
        momentum_score -= blocked_ratio * 0.4

        return min(1.0, max(-1.0, momentum_score))

    def detect_flow_bottleneck(self, flow_id: str) -> list[str] | None:
        """Detect bottlenecks in the flow.

        Args:
            flow_id: Flow identifier

        Returns:
            List of task IDs that are blocking progress
        """
        flow = self._flows.get(flow_id)
        if not flow:
            return None

        active_tasks = [tid for tid, task in self._tasks.items() if task.status == FlowState.ACTIVE]

        # Check for tasks that active tasks are waiting on
        blocking_tasks = []
        for task in active_tasks:
            # Find dependencies that are not completed
            for dep_id in task.dependencies:
                dep_task = self._tasks.get(dep_id)
                if dep_task and dep_task.status != FlowState.COMPLETED:
                    blocking_tasks.append(task.task_id)

        return blocking_tasks if blocking_tasks else None
