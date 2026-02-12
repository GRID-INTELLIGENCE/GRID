"""Pattern recognition service for user work patterns and routines."""

import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any

from .schemas import TimeOfDay
from .user_context_manager import UserContextManager

logger = logging.getLogger(__name__)


class PatternRecognitionService:
    """Recognizes patterns in user behavior and work routines."""

    def __init__(
        self,
        context_manager: UserContextManager,
    ):
        """Initialize pattern recognition service.

        Args:
            context_manager: User context manager instance
        """
        self.context_manager = context_manager
        self.storage = context_manager.storage

    def get_time_of_day(self, timestamp: datetime | None = None) -> TimeOfDay:
        """Determine time of day category from timestamp."""
        if timestamp is None:
            timestamp = datetime.now()

        hour = timestamp.hour

        if 5 <= hour < 8:
            return TimeOfDay.EARLY_MORNING
        elif 8 <= hour < 12:
            return TimeOfDay.MORNING
        elif 12 <= hour < 17:
            return TimeOfDay.AFTERNOON
        elif 17 <= hour < 21:
            return TimeOfDay.EVENING
        else:
            return TimeOfDay.NIGHT

    def detect_work_hours(self, days_back: int = 30) -> tuple[int, int] | None:
        """Detect user's typical work hours from patterns.

        Returns:
            Tuple of (start_hour, end_hour) or None if insufficient data
        """
        if self.context_manager.profile is None:
            return None

        patterns = self.context_manager.profile.work_patterns
        if len(patterns) < 10:
            return None

        # Get recent patterns
        cutoff = datetime.now() - timedelta(days=days_back)
        recent_patterns = [
            p for p in patterns if p.timestamp >= cutoff and p.activity_type in ["coding", "review", "meeting"]
        ]

        if len(recent_patterns) < 5:
            return None

        # Extract hours from timestamps
        hours = [p.timestamp.hour for p in recent_patterns]

        # Find most common work hours
        hour_counts = Counter(hours)
        if not hour_counts:
            return None

        # Get range covering 80% of work hours
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        total_activities = sum(hour_counts.values())
        threshold = total_activities * 0.8

        work_hours = []
        cumulative = 0
        for hour, count in sorted_hours:
            work_hours.append(hour)
            cumulative += count
            if cumulative >= threshold:
                break

        if not work_hours:
            return None

        start_hour = min(work_hours)
        end_hour = max(work_hours) + 1  # Add 1 to include the last hour

        return (start_hour, end_hour)

    def detect_daily_routine(self, days_back: int = 14) -> dict[str, Any]:
        """Detect daily routine patterns.

        Returns:
            Dictionary with routine patterns
        """
        if self.context_manager.profile is None:
            return {}

        patterns = self.context_manager.profile.work_patterns
        if len(patterns) < 20:
            return {}

        cutoff = datetime.now() - timedelta(days=days_back)
        recent_patterns = [p for p in patterns if p.timestamp >= cutoff]

        if not recent_patterns:
            return {}

        # Group by day of week
        by_day = defaultdict(list)
        for pattern in recent_patterns:
            by_day[pattern.day_of_week].append(pattern)

        # Analyze patterns per day
        routine = {}
        for day, day_patterns in by_day.items():
            day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][day]

            # Most common activity type
            activity_types = Counter(p.activity_type for p in day_patterns)
            most_common_activity = activity_types.most_common(1)[0][0] if activity_types else None

            # Average duration
            avg_duration = sum(p.duration_minutes for p in day_patterns) / len(day_patterns) if day_patterns else 0

            # Most common project
            projects = [p.project_focus for p in day_patterns if p.project_focus]
            most_common_project = Counter(projects).most_common(1)[0][0] if projects else None

            routine[day_name] = {
                "most_common_activity": most_common_activity,
                "average_duration_minutes": avg_duration,
                "most_common_project": most_common_project,
                "activity_count": len(day_patterns),
            }

        return routine

    def detect_project_switching_patterns(self, days_back: int = 7) -> dict[str, Any]:
        """Detect patterns in project switching behavior."""
        if self.context_manager.profile is None:
            return {}

        patterns = self.context_manager.profile.work_patterns
        cutoff = datetime.now() - timedelta(days=days_back)
        recent_patterns = [p for p in patterns if p.timestamp >= cutoff and p.project_focus]

        if len(recent_patterns) < 5:
            return {}

        # Track project switches
        project_sequence = []
        last_project = None

        for pattern in sorted(recent_patterns, key=lambda p: p.timestamp):
            if pattern.project_focus != last_project:
                if last_project is not None:
                    project_sequence.append((last_project, pattern.project_focus))
                last_project = pattern.project_focus

        # Analyze switch patterns
        switch_counts = Counter(project_sequence)
        most_common_switches = switch_counts.most_common(5)

        # Calculate average time per project
        project_durations = defaultdict(list)
        current_project = None
        project_start = None

        for pattern in sorted(recent_patterns, key=lambda p: p.timestamp):
            if pattern.project_focus != current_project:
                if current_project and project_start:
                    duration = (pattern.timestamp - project_start).total_seconds() / 60
                    project_durations[current_project].append(duration)
                current_project = pattern.project_focus
                project_start = pattern.timestamp

        avg_durations = {project: sum(durations) / len(durations) for project, durations in project_durations.items()}

        return {
            "most_common_switches": [{"from": f[0], "to": f[1], "count": count} for f, count in most_common_switches],
            "average_duration_per_project_minutes": avg_durations,
            "total_switches": len(project_sequence),
        }

    def detect_file_access_clusters(self, limit: int = 10) -> list[dict[str, Any]]:
        """Detect clusters of frequently accessed files (likely related work)."""
        frequent_files = self.context_manager.get_frequently_accessed_files(limit * 2)

        # Group by project
        by_project = defaultdict(list)
        for file_pattern in frequent_files:
            if file_pattern.project:
                by_project[file_pattern.project].append(file_pattern)

        clusters = []
        for project, files in by_project.items():
            if len(files) >= 3:  # Only clusters with 3+ files
                clusters.append(
                    {
                        "project": project,
                        "files": [
                            {
                                "path": f.file_path,
                                "access_count": f.access_count,
                                "file_type": f.file_type,
                            }
                            for f in sorted(files, key=lambda x: x.access_count, reverse=True)[:limit]
                        ],
                        "total_accesses": sum(f.access_count for f in files),
                    }
                )

        return sorted(clusters, key=lambda x: x["total_accesses"], reverse=True)

    def predict_next_activity(self) -> dict[str, Any] | None:
        """Predict user's next likely activity based on patterns."""
        if self.context_manager.profile is None:
            return None

        now = datetime.now()
        current_time_of_day = self.get_time_of_day(now)
        current_day = now.weekday()

        # Get patterns for similar time/day
        patterns = self.context_manager.profile.work_patterns
        similar_patterns = [
            p for p in patterns if p.day_of_week == current_day and p.time_of_day == current_time_of_day.value
        ]

        if not similar_patterns:
            # Fall back to same day, any time
            similar_patterns = [p for p in patterns if p.day_of_week == current_day]

        if not similar_patterns:
            return None

        # Most common activity at this time
        activity_counts = Counter(p.activity_type for p in similar_patterns)
        most_likely_activity = activity_counts.most_common(1)[0][0] if activity_counts else None

        # Most common project
        projects = [p.project_focus for p in similar_patterns if p.project_focus]
        most_likely_project = Counter(projects).most_common(1)[0][0] if projects else None

        # Average duration
        avg_duration = (
            sum(p.duration_minutes for p in similar_patterns) / len(similar_patterns) if similar_patterns else 0
        )

        return {
            "predicted_activity": most_likely_activity,
            "predicted_project": most_likely_project,
            "expected_duration_minutes": avg_duration,
            "confidence": min(len(similar_patterns) / 10.0, 1.0),  # Higher confidence with more data
        }

    def get_pattern_summary(self) -> dict[str, Any]:
        """Get comprehensive pattern summary."""
        work_hours = self.detect_work_hours()
        daily_routine = self.detect_daily_routine()
        project_switches = self.detect_project_switching_patterns()
        file_clusters = self.detect_file_access_clusters()
        next_activity = self.predict_next_activity()

        return {
            "work_hours": {
                "start": work_hours[0] if work_hours else None,
                "end": work_hours[1] if work_hours else None,
            },
            "daily_routine": daily_routine,
            "project_switching": project_switches,
            "file_clusters": file_clusters,
            "predicted_next_activity": next_activity,
        }
