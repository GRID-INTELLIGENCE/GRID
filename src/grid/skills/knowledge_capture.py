# grid/skills/knowledge_capture.py
from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from ..knowledge.studio import KnowledgeStudio
from .base import SimpleSkill

logger = logging.getLogger(__name__)


def _capture_knowledge(args: Mapping[str, Any]) -> dict[str, Any]:
    """
    Skill: knowledge.capture

    Transforms raw task results, logs, and affected files into
    the structured Knowledge format used by GRID and Windsurf.
    """
    studio = KnowledgeStudio()

    task_id = args.get("task_id")
    if not task_id:
        return {"skill": "knowledge.capture", "status": "error", "error": "Missing required parameter: 'task_id'"}

    title = args.get("title", f"System Insight: {task_id}")
    summary = args.get("summary")
    files = args.get("affected_files", [])
    tags = args.get("tags", [])

    if not summary:
        # If no summary is provided, we can't create a quality knowledge entry
        return {
            "skill": "knowledge.capture",
            "status": "error",
            "error": "Missing required parameter: 'summary'. Use 'compress.articulate' first if needed.",
        }

    try:
        artifact = studio.synthesize(
            task_id=task_id, title=title, summary_text=summary, affected_files=files, tags=tags
        )

        return {
            "skill": "knowledge.capture",
            "status": "success",
            "case_id": artifact.id,
            "title": artifact.title,
            "summary_preview": artifact.summary[:100] + "...",
            "links_count": len(artifact.links),
        }
    except Exception as e:
        logger.error(f"Error in knowledge.capture skill: {e}", exc_info=True)
        return {"skill": "knowledge.capture", "status": "error", "error": str(e)}


# Register skill
knowledge_capture = SimpleSkill(
    id="knowledge.capture",
    name="Capture Knowledge Artifact",
    description="Transforms task logs into a structured Knowledge entry with file mappings",
    handler=_capture_knowledge,
)
