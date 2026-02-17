# grid/knowledge/studio.py
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KnowledgeLink(BaseModel):
    """Represents a reference link in a knowledge entry."""

    label: str
    path: str
    type: str  # e.g., 'code_patch', 'analysis', 'log', 'document'


class KnowledgeArtifact(BaseModel):
    """Structured knowledge artifact representing a system insight or resolution."""

    id: str
    title: str
    summary: str
    links: list[KnowledgeLink]
    timestamp: datetime = Field(default_factory=datetime.now)
    tags: list[str] = []
    metadata: dict[str, Any] = {}


class KnowledgeStudio:
    """The engineering engine that transforms raw task data into persistent knowledge."""

    def __init__(self, storage_dir: str = "data/knowledge_v1"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def synthesize(
        self, task_id: str, title: str, summary_text: str, affected_files: list[str], tags: list[str] | None = None
    ) -> KnowledgeArtifact:
        """Create and persist a structured knowledge artifact."""

        # 1. Map files to structured links with appropriate labels
        links = self._resolve_links(affected_files)

        # 2. Build the structured artifact
        artifact = KnowledgeArtifact(
            id=task_id, title=title, summary=summary_text, links=links, tags=tags or ["automated_capture"]
        )

        # 3. Persist to disk for Windsurf/GRID discovery
        output_file = self.storage_dir / f"{task_id}.json"
        try:
            output_file.write_text(artifact.model_dump_json(indent=2), encoding="utf-8")
            logger.info(f"Persisted knowledge artifact: {task_id} at {output_file}")
        except Exception as e:
            logger.error(f"Failed to persist knowledge artifact {task_id}: {e}")
            raise

        return artifact

    def _resolve_links(self, files: list[str]) -> list[KnowledgeLink]:
        """Maps file paths to human-readable labels based on GRID patterns."""
        links = []
        for f in files:
            path_str = str(f).lower()

            # Pattern matching for labels as shown in the requested screenshot
            if any(p in path_str for p in ["bridge", "dist", "core", "logic"]):
                label = "Code patches"
                link_type = "code_patch"
            elif any(p in path_str for p in ["report", "validate", "verify", "test"]):
                label = "Verification results"
                link_type = "analysis"
            elif any(p in path_str for p in ["cause", "analysis", "audit", "gap", "reception"]):
                label = "Root cause analysis"
                link_type = "analysis"
            elif any(p in path_str for p in ["health", "log", "telemetry", "trace"]):
                label = "Troubleshooting"
                link_type = "log"
            elif any(p in path_str for p in ["docs", "readme", "manual"]):
                label = "Overview"
                link_type = "document"
            else:
                label = Path(f).name
                link_type = "other"

            links.append(KnowledgeLink(label=label, path=f, type=link_type))

        return links
