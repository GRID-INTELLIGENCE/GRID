"""Workflow orchestrator for coordinating tasks across projects."""

import logging
from datetime import datetime
from typing import Any

from ..context.pattern_recognition import PatternRecognitionService
from ..context.recognizer import ContextualRecognizer
from ..context.user_context_manager import UserContextManager

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """Orchestrates workflows across projects using user context."""

    def __init__(
        self,
        context_manager: UserContextManager,
        pattern_service: PatternRecognitionService,
        recognizer: ContextualRecognizer,
    ):
        """Initialize workflow orchestrator.

        Args:
            context_manager: User context manager
            pattern_service: Pattern recognition service
            recognizer: Contextual recognizer
        """
        self.context_manager = context_manager
        self.pattern_service = pattern_service
        self.recognizer = recognizer

    async def coordinate_task(
        self,
        task_type: str,
        task_data: dict[str, Any],
        project: str | None = None,
    ) -> dict[str, Any]:
        """Coordinate a task across projects using user context.

        Args:
            task_type: Type of task to coordinate
            task_data: Task-specific data
            project: Target project (if None, inferred from context)

        Returns:
            Task coordination result
        """
        # Get current context
        context = self.recognizer.recognize_current_context()

        # Infer project if not provided
        if project is None:
            project = context.get("current_project")

        # Determine optimal execution strategy based on patterns
        strategy = self._determine_strategy(task_type, project, context)

        # Track task start
        task_start = datetime.now()

        try:
            # Execute task based on strategy
            result = await self._execute_task(task_type, task_data, strategy, project)

            # Track successful completion
            duration = (datetime.now() - task_start).total_seconds() / 60
            self.context_manager.track_task_pattern(
                task_type=task_type,
                sequence=strategy.get("steps", []),
                duration_minutes=duration,
                success=True,
            )

            return {
                "status": "success",
                "result": result,
                "strategy": strategy,
                "duration_minutes": duration,
            }

        except Exception as e:
            # Track failure
            duration = (datetime.now() - task_start).total_seconds() / 60
            self.context_manager.track_task_pattern(
                task_type=task_type,
                sequence=strategy.get("steps", []),
                duration_minutes=duration,
                success=False,
            )

            logger.error(f"Task coordination failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "duration_minutes": duration,
            }

    def _determine_strategy(
        self,
        task_type: str,
        project: str | None,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Determine optimal execution strategy based on patterns."""
        # Check for existing task patterns
        if self.context_manager.profile:
            task_patterns = self.context_manager.profile.task_patterns
            if task_type in task_patterns:
                pattern = task_patterns[task_type]
                return {
                    "steps": pattern.sequence,
                    "expected_duration_minutes": pattern.average_duration_minutes,
                    "confidence": pattern.success_rate,
                }

        # Default strategy
        return {
            "steps": ["prepare", "execute", "validate"],
            "expected_duration_minutes": None,
            "confidence": 0.5,
        }

    async def _execute_task(
        self,
        task_type: str,
        task_data: dict[str, Any],
        strategy: dict[str, Any],
        project: str | None,
    ) -> Any:
        """Execute task using determined strategy."""
        # This is a placeholder - actual implementation would coordinate
        # with agentic system, EUFLE, Apps, etc.

        steps = strategy.get("steps", [])
        results = {}

        for step in steps:
            logger.info(f"Executing step: {step} for task: {task_type}")
            # Placeholder: actual step execution would be implemented here
            results[step] = {"status": "completed"}

        return results

    def get_workflow_suggestions(self) -> list[dict[str, Any]]:
        """Get workflow optimization suggestions based on patterns."""
        suggestions: list[dict[str, Any]] = []

        if self.context_manager.profile is None:
            return suggestions

        # Analyze task patterns for optimization opportunities
        task_patterns = self.context_manager.profile.task_patterns

        for task_type, pattern in task_patterns.items():
            if pattern.frequency >= 5:
                # Suggest automation for frequently repeated tasks
                if pattern.success_rate > 0.9:
                    suggestions.append(
                        {
                            "type": "automation",
                            "task": task_type,
                            "message": f"Consider automating '{task_type}' - high success rate ({pattern.success_rate:.0%})",
                            "priority": "medium",
                        }
                    )

                # Suggest optimization for slow tasks
                if pattern.average_duration_minutes and pattern.average_duration_minutes > 30:
                    suggestions.append(
                        {
                            "type": "optimization",
                            "task": task_type,
                            "message": f"'{task_type}' takes {pattern.average_duration_minutes:.1f} minutes on average - consider optimization",
                            "priority": "low",
                        }
                    )

        return suggestions
