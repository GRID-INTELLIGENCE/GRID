"""Skill retriever for finding relevant historical skills."""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SkillRetriever:
    """Retrieves relevant Antigravity skills based on case context."""

    def __init__(self, skill_store_path: Path):
        """Initialize skill retriever.

        Args:
            skill_store_path: Path to the antigravity skill store
        """
        self.skill_store_path = skill_store_path

    def find_relevant_skills(
        self, category: str | None = None, keywords: list[str] | None = None, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Find skills that match the given category or keywords.

        Args:
            category: Case category
            keywords: List of case keywords
            limit: Maximum skills to return

        Returns:
            List of skill metadata and artifact paths
        """
        if not self.skill_store_path.exists():
            return []

        relevant_skills = []

        for skill_dir in self.skill_store_path.iterdir():
            if not skill_dir.is_dir():
                continue

            metadata_path = skill_dir / "metadata.json"
            if not metadata_path.exists():
                continue

            try:
                # Try UTF-8 first
                try:
                    with open(metadata_path, encoding="utf-8") as f:
                        metadata = json.load(f)
                except UnicodeDecodeError:
                    # Fallback to system encoding or UTF-16 if needed
                    with open(metadata_path, encoding="utf-16") as f:
                        metadata = json.load(f)

                # Simple matching logic: check if category or keywords appear in title/summary
                score = 0
                title = metadata.get("title", "").lower()
                summary = metadata.get("summary", "").lower()

                if category and category.lower() in (title + summary):
                    score += 5

                if keywords:
                    for kw in keywords:
                        if kw.lower() in (title + summary):
                            score += 2

                if score > 0:
                    relevant_skills.append(
                        {"id": skill_dir.name, "score": score, "metadata": metadata, "path": str(skill_dir)}
                    )

            except Exception as e:
                logger.warning(f"Error reading skill {skill_dir.name}: {e}")

        # Sort by score descending
        relevant_skills.sort(key=lambda x: x["score"], reverse=True)
        return relevant_skills[:limit]

    def load_skill_artifacts(self, skill_id: str) -> dict[str, str]:
        """Load artifact content for a specific skill.

        Args:
            skill_id: Skill identifier (directory name)

        Returns:
            Dict mapping artifact names to their content
        """
        skill_dir = self.skill_store_path / skill_id
        artifacts_dir = skill_dir / "artifacts"
        artifacts = {}

        if artifacts_dir.exists():
            for artifact_file in artifacts_dir.iterdir():
                if artifact_file.is_file():
                    try:
                        with open(artifact_file, encoding="utf-8") as f:
                            artifacts[artifact_file.name] = f.read()
                    except Exception:
                        pass

        return artifacts
