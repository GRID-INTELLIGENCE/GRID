"""Shared context service for cross-project communication."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Shared context root
DEFAULT_CONTEXT_ROOT = Path("E:/user_context")
DEFAULT_BRIDGE_ROOT = Path("E:/context_bridge")


class ContextService:
    """Shared context service for cross-project communication."""

    def __init__(
        self,
        context_root: Optional[Path] = None,
        bridge_root: Optional[Path] = None,
    ):
        """Initialize context service.

        Args:
            context_root: Root directory for user context
            bridge_root: Root directory for bridge data
        """
        self.context_root = context_root or DEFAULT_CONTEXT_ROOT
        self.bridge_root = bridge_root or DEFAULT_BRIDGE_ROOT
        self.bridge_root.mkdir(parents=True, exist_ok=True)

    def get_user_profile_path(self, user_id: str = "default") -> Path:
        """Get path to user profile."""
        return self.context_root / "profiles" / f"{user_id}_profile.json"

    def get_shared_context(self, project: str) -> Dict[str, Any]:
        """Get shared context for a specific project.

        Args:
            project: Project identifier (e.g., "grid", "EUFLE", "Apps")

        Returns:
            Shared context dictionary
        """
        context_file = self.bridge_root / f"{project}_context.json"
        if not context_file.exists():
            return {}

        try:
            with open(context_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load shared context for {project}: {e}")
            return {}

    def set_shared_context(self, project: str, context: Dict[str, Any]) -> bool:
        """Set shared context for a specific project.

        Args:
            project: Project identifier
            context: Context data to share

        Returns:
            True if context was saved successfully
        """
        context_file = self.bridge_root / f"{project}_context.json"
        try:
            with open(context_file, "w", encoding="utf-8") as f:
                json.dump(context, f, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"Failed to save shared context for {project}: {e}")
            return False

    def get_cross_project_patterns(self) -> Dict[str, Any]:
        """Get patterns shared across projects."""
        patterns_file = self.bridge_root / "cross_project_patterns.json"
        if not patterns_file.exists():
            return {}

        try:
            with open(patterns_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load cross-project patterns: {e}")
            return {}

    def share_pattern(self, pattern_type: str, pattern_data: Dict[str, Any]) -> bool:
        """Share a pattern across projects.

        Args:
            pattern_type: Type of pattern
            pattern_data: Pattern data

        Returns:
            True if pattern was shared successfully
        """
        patterns = self.get_cross_project_patterns()
        patterns[pattern_type] = pattern_data

        patterns_file = self.bridge_root / "cross_project_patterns.json"
        try:
            with open(patterns_file, "w", encoding="utf-8") as f:
                json.dump(patterns, f, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"Failed to share pattern: {e}")
            return False

    def get_unified_context(self, user_id: str = "default") -> Dict[str, Any]:
        """Get unified context across all projects.

        Args:
            user_id: User identifier

        Returns:
            Unified context dictionary
        """
        # Load user profile
        profile_path = self.get_user_profile_path(user_id)
        user_profile = {}
        if profile_path.exists():
            try:
                with open(profile_path, "r", encoding="utf-8") as f:
                    user_profile = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load user profile: {e}")

        # Get cross-project patterns
        patterns = self.get_cross_project_patterns()

        # Get project-specific contexts
        project_contexts = {}
        for project_file in self.bridge_root.glob("*_context.json"):
            project = project_file.stem.replace("_context", "")
            project_contexts[project] = self.get_shared_context(project)

        return {
            "user_profile": user_profile,
            "cross_project_patterns": patterns,
            "project_contexts": project_contexts,
        }
