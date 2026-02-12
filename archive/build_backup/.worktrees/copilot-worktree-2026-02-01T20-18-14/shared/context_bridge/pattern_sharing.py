"""Pattern sharing across projects."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .context_service import ContextService

logger = logging.getLogger(__name__)


class PatternSharing:
    """Shares patterns across projects."""

    def __init__(self, context_service: Optional[ContextService] = None):
        """Initialize pattern sharing.

        Args:
            context_service: Context service instance
        """
        self.context_service = context_service or ContextService()

    def share_work_pattern(
        self,
        pattern_data: Dict[str, Any],
        project: Optional[str] = None,
    ) -> bool:
        """Share work pattern across projects.

        Args:
            pattern_data: Work pattern data
            project: Source project (optional)

        Returns:
            True if pattern was shared successfully
        """
        pattern_type = "work_pattern"
        if project:
            pattern_type = f"{pattern_type}_{project}"

        return self.context_service.share_pattern(pattern_type, pattern_data)

    def share_file_access_pattern(
        self,
        file_path: str,
        access_count: int,
        project: Optional[str] = None,
    ) -> bool:
        """Share file access pattern.

        Args:
            file_path: File path
            access_count: Access count
            project: Source project

        Returns:
            True if pattern was shared successfully
        """
        pattern_data = {
            "file_path": file_path,
            "access_count": access_count,
            "project": project,
        }

        pattern_type = "file_access"
        if project:
            pattern_type = f"{pattern_type}_{project}"

        return self.context_service.share_pattern(pattern_type, pattern_data)

    def get_shared_patterns(self, pattern_type: Optional[str] = None) -> Dict[str, Any]:
        """Get shared patterns.

        Args:
            pattern_type: Specific pattern type to retrieve (None for all)

        Returns:
            Shared patterns dictionary
        """
        all_patterns = self.context_service.get_cross_project_patterns()

        if pattern_type:
            return {pattern_type: all_patterns.get(pattern_type, {})}

        return all_patterns

    def get_cross_project_file_patterns(self) -> Dict[str, Any]:
        """Get file access patterns shared across projects."""
        patterns = self.get_shared_patterns()
        file_patterns = {}

        for pattern_type, pattern_data in patterns.items():
            if pattern_type.startswith("file_access"):
                if isinstance(pattern_data, dict) and "file_path" in pattern_data:
                    file_path = pattern_data["file_path"]
                    if file_path not in file_patterns:
                        file_patterns[file_path] = {
                            "access_count": 0,
                            "projects": [],
                        }
                    file_patterns[file_path]["access_count"] += pattern_data.get("access_count", 0)
                    if pattern_data.get("project"):
                        file_patterns[file_path]["projects"].append(pattern_data["project"])

        return file_patterns
