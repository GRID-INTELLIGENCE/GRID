"""Profile synchronization across projects."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from .context_service import ContextService

logger = logging.getLogger(__name__)


class ProfileSync:
    """Synchronizes user profile across projects."""

    def __init__(self, context_service: Optional[ContextService] = None):
        """Initialize profile sync.

        Args:
            context_service: Context service instance
        """
        self.context_service = context_service or ContextService()

    def sync_profile_to_project(self, project: str, user_id: str = "default") -> bool:
        """Sync user profile to a specific project.

        Args:
            project: Project identifier
            user_id: User identifier

        Returns:
            True if sync was successful
        """
        profile_path = self.context_service.get_user_profile_path(user_id)
        if not profile_path.exists():
            logger.warning(f"User profile not found: {profile_path}")
            return False

        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                profile_data = json.load(f)

            # Set as shared context for the project
            return self.context_service.set_shared_context(project, {
                "user_profile": profile_data,
                "synced_at": str(Path(__file__).stat().st_mtime),  # Simple timestamp
            })

        except Exception as e:
            logger.error(f"Failed to sync profile to {project}: {e}")
            return False

    def sync_all_projects(self, user_id: str = "default") -> Dict[str, bool]:
        """Sync user profile to all known projects.

        Args:
            user_id: User identifier

        Returns:
            Dictionary mapping project names to sync success status
        """
        projects = ["grid", "EUFLE", "Apps", "pipeline", "workspace_utils"]
        results = {}

        for project in projects:
            results[project] = self.sync_profile_to_project(project, user_id)

        return results

    def get_project_profile(self, project: str) -> Optional[Dict[str, Any]]:
        """Get user profile for a specific project.

        Args:
            project: Project identifier

        Returns:
            User profile data or None
        """
        context = self.context_service.get_shared_context(project)
        return context.get("user_profile")
