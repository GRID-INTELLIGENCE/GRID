"""User context manager for agentic development workflow."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .schemas import (
    FileAccessPattern,
    TaskPattern,
    TimeOfDay,
    ToolUsagePattern,
    UserPreferences,
    UserProfile,
    WorkPattern,
)
from .storage import ContextStorage

logger = logging.getLogger(__name__)


class UserContextManager:
    """Manages user context, preferences, and patterns."""

    def __init__(
        self,
        context_root: Path | None = None,
        user_id: str = "default",
    ):
        """Initialize user context manager.

        Args:
            context_root: Root directory for context storage
            user_id: User identifier
        """
        self.storage = ContextStorage(context_root, user_id)
        self.user_id = user_id
        self.profile: UserProfile | None = None
        self._load_profile()

    def _load_profile(self) -> None:
        """Load user profile from storage."""
        self.profile = self.storage.load_user_profile()
        if self.profile is None:
            # Create default profile
            self.profile = UserProfile(
                user_id=self.user_id,
                preferences=UserPreferences(),
            )
            self.save_profile()

    def _require_profile(self) -> UserProfile:
        """Return a loaded user profile or raise if unavailable."""
        if self.profile is None:
            self._load_profile()
        if self.profile is None:
            raise RuntimeError("User profile could not be loaded")
        return self.profile

    def save_profile(self) -> bool:
        """Save user profile to storage."""
        if self.profile is None:
            return False
        result: bool = self.storage.save_user_profile(self.profile)
        return result

    def get_preferences(self) -> UserPreferences:
        """Get user preferences."""
        profile = self._require_profile()
        return profile.preferences

    def update_preference(self, key: str, value: Any) -> None:
        """Update a user preference."""
        profile = self._require_profile()

        if hasattr(profile.preferences, key):
            setattr(profile.preferences, key, value)
        else:
            # Store in metadata for unknown preferences
            profile.metadata[f"preference_{key}"] = value

        self.save_profile()

    def track_file_access(self, file_path: str, project: str | None = None) -> None:
        """Track file access for pattern recognition."""
        profile = self._require_profile()

        # Normalize path
        normalized_path = str(Path(file_path).resolve())

        if normalized_path not in profile.file_access_patterns:
            file_type = Path(file_path).suffix.lower()
            profile.file_access_patterns[normalized_path] = FileAccessPattern(
                file_path=normalized_path,
                project=project,
                file_type=file_type,
            )

        pattern = profile.file_access_patterns[normalized_path]
        pattern.access_count += 1
        pattern.last_accessed = datetime.now()

        self.save_profile()

    def track_tool_usage(
        self,
        tool_name: str,
        success: bool = True,
        duration_seconds: float | None = None,
    ) -> None:
        """Track tool usage for pattern recognition."""
        profile = self._require_profile()

        if tool_name not in profile.tool_usage_patterns:
            profile.tool_usage_patterns[tool_name] = ToolUsagePattern(
                tool_name=tool_name,
            )

        pattern = profile.tool_usage_patterns[tool_name]
        pattern.usage_count += 1
        pattern.last_used = datetime.now()

        # Update success rate
        if pattern.usage_count == 1:
            pattern.success_rate = 1.0 if success else 0.0
        else:
            # Moving average
            pattern.success_rate = (
                pattern.success_rate * (pattern.usage_count - 1) + (1.0 if success else 0.0)
            ) / pattern.usage_count

        # Update average duration
        if duration_seconds is not None:
            if pattern.average_duration_seconds is None:
                pattern.average_duration_seconds = duration_seconds
            else:
                pattern.average_duration_seconds = (
                    pattern.average_duration_seconds * (pattern.usage_count - 1) + duration_seconds
                ) / pattern.usage_count

        self.save_profile()

    def track_work_pattern(
        self,
        time_of_day: TimeOfDay,
        day_of_week: int,
        activity_type: str,
        duration_minutes: float,
        project_focus: str | None = None,
    ) -> None:
        """Track work pattern for routine recognition."""
        profile = self._require_profile()

        pattern = WorkPattern(
            time_of_day=time_of_day,
            day_of_week=day_of_week,
            activity_type=activity_type,
            duration_minutes=duration_minutes,
            project_focus=project_focus,
        )

        profile.work_patterns.append(pattern)

        # Keep only last 1000 patterns to avoid unbounded growth
        if len(profile.work_patterns) > 1000:
            profile.work_patterns = profile.work_patterns[-1000:]

        self.save_profile()

    def track_task_pattern(
        self,
        task_type: str,
        sequence: list[str],
        duration_minutes: float | None = None,
        success: bool = True,
    ) -> None:
        """Track task completion pattern."""
        profile = self._require_profile()

        if task_type not in profile.task_patterns:
            profile.task_patterns[task_type] = TaskPattern(
                task_type=task_type,
            )

        pattern = profile.task_patterns[task_type]
        pattern.frequency += 1
        pattern.sequence = sequence

        # Update success rate
        if pattern.frequency == 1:
            pattern.success_rate = 1.0 if success else 0.0
        else:
            pattern.success_rate = (
                pattern.success_rate * (pattern.frequency - 1) + (1.0 if success else 0.0)
            ) / pattern.frequency

        # Update average duration
        if duration_minutes is not None:
            if pattern.average_duration_minutes is None:
                pattern.average_duration_minutes = duration_minutes
            else:
                pattern.average_duration_minutes = (
                    pattern.average_duration_minutes * (pattern.frequency - 1) + duration_minutes
                ) / pattern.frequency

        self.save_profile()

    def get_frequently_accessed_files(self, limit: int = 10) -> list[FileAccessPattern]:
        """Get most frequently accessed files."""
        if self.profile is None:
            return []

        patterns = list(self.profile.file_access_patterns.values())
        patterns.sort(key=lambda p: p.access_count, reverse=True)
        return patterns[:limit]

    def get_preferred_tools(self, limit: int = 10) -> list[ToolUsagePattern]:
        """Get most preferred tools based on usage and success rate."""
        if self.profile is None:
            return []

        patterns = list(self.profile.tool_usage_patterns.values())
        # Sort by usage count and success rate
        patterns.sort(
            key=lambda p: p.usage_count * p.success_rate,
            reverse=True,
        )
        return patterns[:limit]

    def get_current_project(self) -> str | None:
        """Infer current project from recent file accesses."""
        if self.profile is None:
            return None

        recent_files = [
            p
            for p in self.profile.file_access_patterns.values()
            if p.last_accessed and (datetime.now() - p.last_accessed).total_seconds() < 3600
        ]

        if not recent_files:
            return None

        # Get most common project from recent files
        projects = [f.project for f in recent_files if f.project]
        if not projects:
            return None

        from collections import Counter

        project_counts = Counter(projects)
        most_common_project: str = project_counts.most_common(1)[0][0]
        return most_common_project

    def get_context_summary(self) -> dict[str, Any]:
        """Get summary of current user context."""
        if self.profile is None:
            return {}

        return {
            "user_id": self.user_id,
            "current_project": self.get_current_project(),
            "frequent_files": [
                {
                    "path": p.file_path,
                    "access_count": p.access_count,
                }
                for p in self.get_frequently_accessed_files(5)
            ],
            "preferred_tools": [
                {
                    "tool": p.tool_name,
                    "usage_count": p.usage_count,
                    "success_rate": p.success_rate,
                }
                for p in self.get_preferred_tools(5)
            ],
            "preferences": self.profile.preferences.model_dump(),
        }
