"""Predictive task suggestions based on user patterns."""

import logging
from pathlib import Path
from typing import Any

from ..context.pattern_recognition import PatternRecognitionService
from ..context.recognizer import ContextualRecognizer
from ..context.user_context_manager import UserContextManager

logger = logging.getLogger(__name__)


class PredictiveSuggestions:
    """Provides predictive task suggestions based on user patterns."""

    def __init__(
        self,
        context_manager: UserContextManager,
        pattern_service: PatternRecognitionService,
        recognizer: ContextualRecognizer,
    ):
        """Initialize predictive suggestions.

        Args:
            context_manager: User context manager
            pattern_service: Pattern recognition service
            recognizer: Contextual recognizer
        """
        self.context_manager = context_manager
        self.pattern_service = pattern_service
        self.recognizer = recognizer

    def get_task_suggestions(self, limit: int = 5) -> list[dict[str, Any]]:
        """Get predictive task suggestions based on patterns.

        Args:
            limit: Maximum number of suggestions to return

        Returns:
            List of task suggestions
        """
        suggestions = []

        # Get predicted next activity
        predicted = self.pattern_service.predict_next_activity()
        if predicted and predicted.get("confidence", 0) > 0.5:
            suggestions.append(
                {
                    "type": "predicted_activity",
                    "task": predicted.get("predicted_activity"),
                    "project": predicted.get("predicted_project"),
                    "confidence": predicted.get("confidence", 0),
                    "reason": "Based on your typical patterns at this time",
                    "priority": "high" if predicted.get("confidence", 0) > 0.7 else "medium",
                }
            )

        # Get context-based suggestions
        context = self.recognizer.recognize_current_context()

        # File-based suggestions
        frequent_files = context.get("frequent_files", [])
        if frequent_files:
            current_project = context.get("current_project")
            project_files = [f for f in frequent_files if current_project and current_project in f.get("path", "")]

            if project_files:
                suggestions.append(
                    {
                        "type": "file_suggestion",
                        "message": "Files you frequently access in current project",
                        "files": [f["path"] for f in project_files[:3]],
                        "priority": "medium",
                    }
                )

        # Tool-based suggestions
        preferred_tools = context.get("preferred_tools", [])
        if preferred_tools:
            top_tool = preferred_tools[0]
            suggestions.append(
                {
                    "type": "tool_suggestion",
                    "message": f"Your most-used tool: {top_tool['tool']}",
                    "tool": top_tool["tool"],
                    "priority": "low",
                }
            )

        # Time-based suggestions
        time_of_day = context.get("time_of_day")
        if time_of_day == "morning":
            suggestions.append(
                {
                    "type": "routine",
                    "message": "Morning routine: Check overnight builds, review PRs, plan day",
                    "priority": "low",
                }
            )
        elif time_of_day == "evening":
            suggestions.append(
                {
                    "type": "routine",
                    "message": "Evening routine: Commit changes, update documentation, plan tomorrow",
                    "priority": "low",
                }
            )

        # Task pattern suggestions
        if self.context_manager.profile:
            task_patterns = self.context_manager.profile.task_patterns
            for task_type, pattern in task_patterns.items():
                if pattern.frequency >= 3:
                    # Suggest tasks that are typically done around this time
                    suggestions.append(
                        {
                            "type": "pattern_based",
                            "task": task_type,
                            "message": f"You often do '{task_type}' - consider doing it now?",
                            "frequency": pattern.frequency,
                            "priority": "medium",
                        }
                    )

        # Sort by priority and limit
        priority_order = {"high": 0, "medium": 1, "low": 2}
        suggestions.sort(key=lambda s: priority_order.get(s.get("priority", "low"), 2))

        return suggestions[:limit]

    def get_file_suggestions(self, current_file: str | None = None, limit: int = 5) -> list[str]:
        """Get file suggestions based on access patterns.

        Args:
            current_file: Currently open file (for related file suggestions)
            limit: Maximum number of suggestions

        Returns:
            List of suggested file paths
        """
        frequent_files = self.context_manager.get_frequently_accessed_files(limit * 2)

        if current_file:
            # Find related files
            current_path = Path(current_file) if current_file else None
            if current_path and self.context_manager.profile:
                # Get files from same project/directory
                current_dir = current_path.parent
                related = [f for f in frequent_files if Path(f.file_path).parent == current_dir]
                if related:
                    return [f.file_path for f in related[:limit]]

        # Return most frequently accessed
        return [f.file_path for f in frequent_files[:limit]]

    def get_tool_suggestions(self, context: str | None = None, limit: int = 3) -> list[dict[str, Any]]:
        """Get tool suggestions based on usage patterns and context.

        Args:
            context: Current context (e.g., "coding", "debugging", "testing")
            limit: Maximum number of suggestions

        Returns:
            List of tool suggestions
        """
        preferred_tools = self.context_manager.get_preferred_tools(limit * 2)

        # Filter by context if provided
        if context:
            # This would be enhanced with context-aware tool mapping
            pass

        return [
            {
                "tool": t.tool_name,
                "usage_count": t.usage_count,
                "success_rate": t.success_rate,
                "reason": "Frequently used with high success rate",
            }
            for t in preferred_tools[:limit]
        ]

    def get_workflow_suggestions(self) -> list[dict[str, Any]]:
        """Get workflow optimization suggestions."""
        suggestions = []

        if self.context_manager.profile is None:
            return suggestions

        # Analyze patterns for optimization opportunities
        task_patterns = self.context_manager.profile.task_patterns

        for task_type, pattern in task_patterns.items():
            # Suggest automation for repetitive tasks
            if pattern.frequency >= 5 and pattern.success_rate > 0.9:
                suggestions.append(
                    {
                        "type": "automation",
                        "task": task_type,
                        "message": f"Consider automating '{task_type}' - performed {pattern.frequency} times with {pattern.success_rate:.0%} success rate",
                        "priority": "medium",
                    }
                )

            # Suggest optimization for slow tasks
            if pattern.average_duration_minutes and pattern.average_duration_minutes > 20:
                suggestions.append(
                    {
                        "type": "optimization",
                        "task": task_type,
                        "message": f"'{task_type}' takes {pattern.average_duration_minutes:.1f} minutes - consider optimization",
                        "priority": "low",
                    }
                )

        return suggestions
