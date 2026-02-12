"""Persistent storage layer for user context data."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .schemas import (
    Correction,
    FileAccessPattern,
    LearnedPreference,
    ToolUsagePattern,
    UserProfile,
)

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Raised when a security constraint is violated."""

    pass


# Default storage paths
DEFAULT_CONTEXT_ROOT = Path("E:/user_context")
DEFAULT_PROFILES_DIR = DEFAULT_CONTEXT_ROOT / "profiles"
DEFAULT_PATTERNS_DIR = DEFAULT_CONTEXT_ROOT / "patterns"
DEFAULT_ROUTINES_DIR = DEFAULT_CONTEXT_ROOT / "routines"
DEFAULT_LEARNING_DIR = DEFAULT_CONTEXT_ROOT / "learning"


class ContextStorage:
    """Manages persistent storage of user context data."""

    def __init__(
        self,
        context_root: Path | None = None,
        user_id: str = "default",
    ):
        """Initialize context storage.

        Args:
            context_root: Root directory for context storage (default: E:/user_context)
            user_id: User identifier
        """
        self.context_root = context_root or DEFAULT_CONTEXT_ROOT
        self.user_id = user_id

        # Ensure directories exist
        self.profiles_dir = self.context_root / "profiles"
        self.patterns_dir = self.context_root / "patterns"
        self.routines_dir = self.context_root / "routines"
        self.learning_dir = self.context_root / "learning"

        # Security: Ensure context root is within allowed bounds
        self._validate_context_root()

    def _validate_context_root(self) -> None:
        """Validate that context root is within reasonable bounds."""
        resolved_root = self.context_root.resolve()

        # Restrict to known safe directories
        allowed_roots = [
            Path.home() / ".grid" / "context",
            Path("E:/user_context"),
            Path("/var/grid/context"),
            Path("/tmp/grid/context"),
        ]

        if not any(resolved_root.is_relative_to(allowed_root.resolve()) for allowed_root in allowed_roots):
            logger.warning(f"Context root {resolved_root} may be unsafe")

        # Ensure directories exist
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.patterns_dir.mkdir(parents=True, exist_ok=True)
        self.routines_dir.mkdir(parents=True, exist_ok=True)
        self.learning_dir.mkdir(parents=True, exist_ok=True)

    def _validate_path(self, path: Path) -> Path:
        """Ensure path is within context root."""
        resolved_path = path.resolve()
        if not resolved_path.is_relative_to(self.context_root.resolve()):
            logger.error(f"Access denied: {path} is outside context root")
            raise SecurityError(f"Access denied: {path} is outside context root")
        return resolved_path

    def load_user_profile(self) -> UserProfile | None:
        """Load user profile from storage."""
        profile_path = self.profiles_dir / f"{self.user_id}_profile.json"
        if not profile_path.exists():
            return None

        try:
            validated_path = self._validate_path(profile_path)
            with open(validated_path, encoding="utf-8") as f:
                data = json.load(f)
            return UserProfile(**data)
        except Exception as e:
            logger.error(f"Failed to load user profile: {e}")
            return None

    def save_user_profile(self, profile: UserProfile) -> bool:
        """Save user profile to storage."""
        profile_path = self.profiles_dir / f"{self.user_id}_profile.json"
        profile.updated_at = datetime.now()

        try:
            validated_path = self._validate_path(profile_path)
            with open(validated_path, "w", encoding="utf-8") as f:
                json.dump(profile.model_dump(mode="json"), f, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"Failed to save user profile: {e}")
            return False

    def load_work_patterns(self) -> dict[str, Any]:
        """Load work patterns from storage."""
        patterns_path = self.patterns_dir / "work_patterns.json"
        if not patterns_path.exists():
            return {}

        try:
            validated_path = self._validate_path(patterns_path)
            with open(validated_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load work patterns: {e}")
            return {}

    def save_work_patterns(self, patterns: dict[str, Any]) -> bool:
        """Save work patterns to storage."""
        patterns_path = self.patterns_dir / "work_patterns.json"
        try:
            validated_path = self._validate_path(patterns_path)
            with open(validated_path, "w", encoding="utf-8") as f:
                json.dump(patterns, f, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"Failed to save work patterns: {e}")
            return False

    def load_file_access_patterns(self) -> dict[str, FileAccessPattern]:
        """Load file access patterns from storage."""
        patterns_path = self.patterns_dir / "file_access_patterns.json"
        if not patterns_path.exists():
            return {}

        try:
            validated_path = self._validate_path(patterns_path)
            with open(validated_path, encoding="utf-8") as f:
                data = json.load(f)
                return {path: FileAccessPattern(**pattern_data) for path, pattern_data in data.items()}
        except Exception as e:
            logger.error(f"Failed to load file access patterns: {e}")
            return {}

    def save_file_access_patterns(self, patterns: dict[str, FileAccessPattern]) -> bool:
        """Save file access patterns to storage."""
        patterns_path = self.patterns_dir / "file_access_patterns.json"
        try:
            data = {path: pattern.model_dump(mode="json") for path, pattern in patterns.items()}
            validated_path = self._validate_path(patterns_path)
            with open(validated_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"Failed to save file access patterns: {e}")
            return False

    def load_tool_usage_patterns(self) -> dict[str, ToolUsagePattern]:
        """Load tool usage patterns from storage."""
        patterns_path = self.patterns_dir / "tool_usage_patterns.json"
        if not patterns_path.exists():
            return {}

        try:
            validated_path = self._validate_path(patterns_path)
            with open(validated_path, encoding="utf-8") as f:
                data = json.load(f)
                return {tool: ToolUsagePattern(**pattern_data) for tool, pattern_data in data.items()}
        except Exception as e:
            logger.error(f"Failed to load tool usage patterns: {e}")
            return {}

    def save_tool_usage_patterns(self, patterns: dict[str, ToolUsagePattern]) -> bool:
        """Save tool usage patterns to storage."""
        patterns_path = self.patterns_dir / "tool_usage_patterns.json"
        try:
            data = {tool: pattern.model_dump(mode="json") for tool, pattern in patterns.items()}
            validated_path = self._validate_path(patterns_path)
            with open(validated_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"Failed to save tool usage patterns: {e}")
            return False

    def load_corrections(self) -> list[Correction]:
        """Load user corrections from storage."""
        corrections_path = self.learning_dir / "corrections.json"
        if not corrections_path.exists():
            return []

        try:
            validated_path = self._validate_path(corrections_path)
            with open(validated_path, encoding="utf-8") as f:
                data = json.load(f)
                return [Correction(**correction_data) for correction_data in data]
        except Exception as e:
            logger.error(f"Failed to load corrections: {e}")
            return []

    def save_correction(self, correction: Correction) -> bool:
        """Save a user correction to storage."""
        corrections_path = self.learning_dir / "corrections.json"
        corrections = self.load_corrections()
        corrections.append(correction)

        try:
            validated_path = self._validate_path(corrections_path)
            with open(validated_path, "w", encoding="utf-8") as f:
                json.dump(
                    [c.model_dump(mode="json") for c in corrections],
                    f,
                    indent=2,
                    default=str,
                )
            return True
        except Exception as e:
            logger.error(f"Failed to save correction: {e}")
            return False

    def load_learned_preferences(self) -> dict[str, LearnedPreference]:
        """Load learned preferences from storage."""
        preferences_path = self.learning_dir / "preferences.json"
        if not preferences_path.exists():
            return {}

        try:
            validated_path = self._validate_path(preferences_path)
            with open(validated_path, encoding="utf-8") as f:
                data = json.load(f)
                return {pref_type: LearnedPreference(**pref_data) for pref_type, pref_data in data.items()}
        except Exception as e:
            logger.error(f"Failed to load learned preferences: {e}")
            return {}

    def save_learned_preferences(self, preferences: dict[str, LearnedPreference]) -> bool:
        """Save learned preferences to storage."""
        preferences_path = self.learning_dir / "preferences.json"
        try:
            data = {pref_type: pref.model_dump(mode="json") for pref_type, pref in preferences.items()}
            validated_path = self._validate_path(preferences_path)
            with open(validated_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"Failed to save learned preferences: {e}")
            return False
