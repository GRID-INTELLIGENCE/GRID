"""Contextual recognizer for understanding current user context."""

import logging
from datetime import datetime
from typing import Any

from .pattern_recognition import PatternRecognitionService
from .schemas import TimeOfDay
from .user_context_manager import UserContextManager

logger = logging.getLogger(__name__)


class ContextualRecognizer:
    """Recognizes and understands current user context."""

    def __init__(
        self,
        context_manager: UserContextManager,
        pattern_service: PatternRecognitionService,
    ):
        """Initialize contextual recognizer.

        Args:
            context_manager: User context manager
            pattern_service: Pattern recognition service
        """
        self.context_manager = context_manager
        self.pattern_service = pattern_service

    def recognize_current_context(self) -> dict[str, Any]:
        """Recognize and return current user context.

        Returns:
            Dictionary with current context information
        """
        now = datetime.now()
        time_of_day = self.pattern_service.get_time_of_day(now)
        current_project = self.context_manager.get_current_project()
        work_hours = self.pattern_service.detect_work_hours()

        # Determine if within work hours
        is_work_hours = False
        if work_hours:
            start_hour, end_hour = work_hours
            current_hour = now.hour
            is_work_hours = start_hour <= current_hour < end_hour

        # Get predicted next activity
        predicted_activity = self.pattern_service.predict_next_activity()

        # Get frequently accessed files
        frequent_files = self.context_manager.get_frequently_accessed_files(5)

        # Get preferred tools
        preferred_tools = self.context_manager.get_preferred_tools(5)

        return {
            "timestamp": now.isoformat(),
            "time_of_day": time_of_day.value,
            "day_of_week": now.strftime("%A"),
            "current_project": current_project,
            "is_work_hours": is_work_hours,
            "work_hours": {
                "start": work_hours[0] if work_hours else None,
                "end": work_hours[1] if work_hours else None,
            },
            "predicted_activity": predicted_activity,
            "frequent_files": [
                {
                    "path": f.file_path,
                    "access_count": f.access_count,
                }
                for f in frequent_files
            ],
            "preferred_tools": [
                {
                    "tool": t.tool_name,
                    "usage_count": t.usage_count,
                }
                for t in preferred_tools
            ],
        }

    def get_contextual_suggestions(self) -> list[dict[str, Any]]:
        """Get contextual suggestions based on current context."""
        context = self.recognize_current_context()
        suggestions: list[dict[str, Any]] = []

        # Time-based suggestions
        time_of_day = context["time_of_day"]
        if time_of_day == TimeOfDay.MORNING.value:
            suggestions.append(
                {
                    "type": "routine",
                    "message": "Good morning! Starting your typical morning routine?",
                    "priority": "low",
                }
            )
        elif time_of_day == TimeOfDay.EVENING.value:
            suggestions.append(
                {
                    "type": "routine",
                    "message": "Evening session detected. Wrapping up for the day?",
                    "priority": "low",
                }
            )

        # Project-based suggestions
        current_project = context.get("current_project")
        if current_project:
            file_clusters = self.pattern_service.detect_file_access_clusters(5)
            for cluster in file_clusters:
                if cluster["project"] == current_project:
                    suggestions.append(
                        {
                            "type": "file_suggestion",
                            "message": f"Frequently accessed files in {current_project}:",
                            "files": [f["path"] for f in cluster["files"][:3]],
                            "priority": "medium",
                        }
                    )
                    break

        # Activity-based suggestions
        predicted = context.get("predicted_activity")
        if predicted and predicted.get("confidence", 0) > 0.6:
            suggestions.append(
                {
                    "type": "activity_prediction",
                    "message": f"Based on your patterns, you might be working on: {predicted.get('predicted_activity')}",
                    "project": predicted.get("predicted_project"),
                    "priority": "medium",
                }
            )

        # Tool suggestions
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

        return suggestions

    def should_adapt_interface(self) -> dict[str, Any]:
        """Determine if interface should be adapted based on context."""
        context = self.recognize_current_context()
        adaptations = {}

        # Time-based adaptations
        time_of_day = context["time_of_day"]
        if time_of_day in [TimeOfDay.NIGHT.value, TimeOfDay.EARLY_MORNING.value]:
            adaptations["theme"] = "dark"  # Suggest dark theme for night work
            adaptations["notifications"] = "reduced"  # Reduce notifications

        # Work hours adaptations
        if not context.get("is_work_hours", False):
            adaptations["suggestions"] = "minimal"  # Fewer suggestions outside work hours

        # Project-based adaptations
        current_project = context.get("current_project")
        if current_project:
            adaptations["project_focus"] = current_project
            adaptations["file_suggestions"] = "project_aware"

        return adaptations

    def get_context_summary(self) -> dict[str, Any]:
        """Get comprehensive context summary."""
        current_context = self.recognize_current_context()
        suggestions = self.get_contextual_suggestions()
        adaptations = self.should_adapt_interface()
        pattern_summary = self.pattern_service.get_pattern_summary()

        return {
            "current_context": current_context,
            "suggestions": suggestions,
            "interface_adaptations": adaptations,
            "pattern_summary": pattern_summary,
        }
