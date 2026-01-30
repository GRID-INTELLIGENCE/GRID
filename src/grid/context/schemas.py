"""Pydantic schemas for user context data structures."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TimeOfDay(str, Enum):
    """Time of day categories."""

    EARLY_MORNING = "early_morning"  # 5-8 AM
    MORNING = "morning"  # 8-12 PM
    AFTERNOON = "afternoon"  # 12-5 PM
    EVENING = "evening"  # 5-9 PM
    NIGHT = "night"  # 9 PM-5 AM


class WorkPattern(BaseModel):
    """User work pattern data."""

    time_of_day: TimeOfDay
    day_of_week: int  # 0=Monday, 6=Sunday
    project_focus: str | None = None
    activity_type: str  # "coding", "review", "meeting", "break"
    duration_minutes: float
    timestamp: datetime = Field(default_factory=datetime.now)


class FileAccessPattern(BaseModel):
    """File access pattern data."""

    file_path: str
    access_count: int = 0
    last_accessed: datetime | None = None
    project: str | None = None
    file_type: str | None = None
    related_files: list[str] = Field(default_factory=list)


class ToolUsagePattern(BaseModel):
    """Tool usage pattern data."""

    tool_name: str
    usage_count: int = 0
    last_used: datetime | None = None
    success_rate: float = 1.0
    average_duration_seconds: float | None = None


class TaskPattern(BaseModel):
    """Task completion pattern data."""

    task_type: str
    sequence: list[str] = Field(default_factory=list)
    average_duration_minutes: float | None = None
    success_rate: float = 1.0
    frequency: int = 0


class UserPreferences(BaseModel):
    """User preferences and settings."""

    code_style: dict[str, Any] = Field(default_factory=dict)
    preferred_tools: list[str] = Field(default_factory=list)
    work_hours_start: int | None = None  # Hour of day (0-23)
    work_hours_end: int | None = None
    preferred_languages: list[str] = Field(default_factory=list)
    notification_preferences: dict[str, bool] = Field(default_factory=dict)


class UserProfile(BaseModel):
    """Complete user profile."""

    user_id: str = "default"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    work_patterns: list[WorkPattern] = Field(default_factory=list)
    file_access_patterns: dict[str, FileAccessPattern] = Field(default_factory=dict)
    tool_usage_patterns: dict[str, ToolUsagePattern] = Field(default_factory=dict)
    task_patterns: dict[str, TaskPattern] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Correction(BaseModel):
    """User correction/feedback data."""

    timestamp: datetime = Field(default_factory=datetime.now)
    context: str  # What was being done
    correction_type: str  # "code_style", "tool_usage", "suggestion", etc.
    original: Any
    corrected: Any
    reason: str | None = None


class LearnedPreference(BaseModel):
    """Learned preference from user interactions."""

    preference_type: str
    value: Any
    confidence: float = 0.5  # 0.0 to 1.0
    source: str  # "explicit", "correction", "pattern", "inference"
    learned_at: datetime = Field(default_factory=datetime.now)
    usage_count: int = 0
