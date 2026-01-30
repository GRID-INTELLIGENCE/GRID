"""Workflow automation for routine tasks."""

import logging
from datetime import datetime
from typing import Any

from ..context.pattern_recognition import PatternRecognitionService
from ..context.recognizer import ContextualRecognizer
from ..context.user_context_manager import UserContextManager

logger = logging.getLogger(__name__)


class WorkflowAutomation:
    """Automates routine workflows based on user patterns."""

    def __init__(
        self,
        context_manager: UserContextManager,
        pattern_service: PatternRecognitionService,
        recognizer: ContextualRecognizer,
    ):
        """Initialize workflow automation.

        Args:
            context_manager: User context manager
            pattern_service: Pattern recognition service
            recognizer: Contextual recognizer
        """
        self.context_manager = context_manager
        self.pattern_service = pattern_service
        self.recognizer = recognizer
        self.automated_routines: dict[str, dict[str, Any]] = {}

    def register_routine(
        self,
        routine_id: str,
        trigger: dict[str, Any],
        actions: list[dict[str, Any]],
        enabled: bool = True,
    ) -> bool:
        """Register an automated routine.

        Args:
            routine_id: Unique routine identifier
            trigger: Trigger conditions (time, pattern, event)
            actions: List of actions to execute
            enabled: Whether routine is enabled

        Returns:
            True if routine was registered successfully
        """
        self.automated_routines[routine_id] = {
            "trigger": trigger,
            "actions": actions,
            "enabled": enabled,
            "created_at": datetime.now().isoformat(),
        }
        return True

    def check_routine_triggers(self) -> list[str]:
        """Check which routines should be triggered based on current context."""
        triggered = []

        context = self.recognizer.recognize_current_context()
        now = datetime.now()

        for routine_id, routine in self.automated_routines.items():
            if not routine.get("enabled", True):
                continue

            trigger = routine.get("trigger", {})

            # Time-based trigger
            if "time" in trigger:
                trigger_time = trigger["time"]
                if isinstance(trigger_time, str):
                    # Parse time string (e.g., "09:00")
                    hour, minute = map(int, trigger_time.split(":"))
                    if now.hour == hour and now.minute == minute:
                        triggered.append(routine_id)

            # Pattern-based trigger
            if "pattern" in trigger:
                pattern_type = trigger["pattern"].get("type")
                if pattern_type == "work_hours_start":
                    work_hours = self.pattern_service.detect_work_hours()
                    if work_hours and now.hour == work_hours[0]:
                        triggered.append(routine_id)

            # Context-based trigger
            if "context" in trigger:
                context_conditions = trigger["context"]
                matches = True
                for key, value in context_conditions.items():
                    if context.get(key) != value:
                        matches = False
                        break
                if matches:
                    triggered.append(routine_id)

        return triggered

    async def execute_routine(self, routine_id: str) -> dict[str, Any]:
        """Execute an automated routine.

        Args:
            routine_id: Routine identifier

        Returns:
            Execution result
        """
        if routine_id not in self.automated_routines:
            return {"status": "error", "message": f"Routine '{routine_id}' not found"}

        routine = self.automated_routines[routine_id]
        if not routine.get("enabled", True):
            return {"status": "skipped", "message": "Routine is disabled"}

        actions = routine.get("actions", [])
        results = []

        for action in actions:
            action_type = action.get("type")
            action_data = action.get("data", {})

            try:
                if action_type == "track_activity":
                    # Track work pattern
                    time_of_day = self.pattern_service.get_time_of_day()
                    self.context_manager.track_work_pattern(
                        time_of_day=time_of_day.value,
                        day_of_week=datetime.now().weekday(),
                        activity_type=action_data.get("activity_type", "automated"),
                        duration_minutes=0,
                        project_focus=action_data.get("project"),
                    )

                elif action_type == "suggest_files":
                    # Suggest frequently accessed files
                    frequent_files = self.context_manager.get_frequently_accessed_files(5)
                    results.append(
                        {
                            "type": "file_suggestions",
                            "files": [f.file_path for f in frequent_files],
                        }
                    )

                elif action_type == "custom":
                    # Custom action (placeholder for extensibility)
                    logger.info(f"Executing custom action: {action_data}")

                results.append(
                    {
                        "action": action_type,
                        "status": "completed",
                    }
                )

            except Exception as e:
                logger.error(f"Failed to execute action {action_type}: {e}")
                results.append(
                    {
                        "action": action_type,
                        "status": "error",
                        "error": str(e),
                    }
                )

        return {
            "status": "completed",
            "routine_id": routine_id,
            "actions_executed": len(actions),
            "results": results,
        }

    async def run_scheduled_routines(self) -> list[dict[str, Any]]:
        """Run all triggered routines."""
        triggered = self.check_routine_triggers()
        results = []

        for routine_id in triggered:
            result = await self.execute_routine(routine_id)
            results.append(
                {
                    "routine_id": routine_id,
                    **result,
                }
            )

        return results

    def get_routine_suggestions(self) -> list[dict[str, Any]]:
        """Suggest routines based on detected patterns."""
        suggestions = []

        if self.context_manager.profile is None:
            return suggestions

        # Analyze work patterns for routine opportunities
        daily_routine = self.pattern_service.detect_daily_routine()

        for day_name, day_data in daily_routine.items():
            if day_data.get("activity_count", 0) >= 5:
                # Suggest routine for consistent daily patterns
                suggestions.append(
                    {
                        "type": "daily_routine",
                        "day": day_name,
                        "message": f"Detected consistent pattern on {day_name} - consider automating",
                        "activity": day_data.get("most_common_activity"),
                        "priority": "medium",
                    }
                )

        # Analyze task patterns
        task_patterns = self.context_manager.profile.task_patterns
        for task_type, pattern in task_patterns.items():
            if pattern.frequency >= 10 and pattern.success_rate > 0.95:
                # Suggest automation for highly successful, frequent tasks
                suggestions.append(
                    {
                        "type": "task_automation",
                        "task": task_type,
                        "message": f"'{task_type}' is performed frequently with high success - good candidate for automation",
                        "frequency": pattern.frequency,
                        "success_rate": pattern.success_rate,
                        "priority": "high",
                    }
                )

        return suggestions
