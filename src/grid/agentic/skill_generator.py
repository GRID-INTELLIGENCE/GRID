"""Skill generator for automated persistence of successful cases."""

import asyncio
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiofiles

from .event_bus import get_event_bus

logger = logging.getLogger(__name__)


class SkillGenerator:
    """Generates Antigravity-style skills from successful cases."""

    def __init__(self, skill_store_path: Path):
        """Initialize skill generator.

        Args:
            skill_store_path: Path to the antigravity skill store
        """
        self.skill_store_path = skill_store_path
        self.skill_store_path.mkdir(parents=True, exist_ok=True)

    async def handle_case_completed(self, event: dict[str, Any]) -> None:
        """Handle case.completed events and generate skills if successful.

        Args:
            event: CaseCompletedEvent dictionary
        """
        if event.get("outcome") != "success":
            return

        case_id = event.get("case_id")
        solution = event.get("solution")
        experience = event.get("agent_experience", {})

        skill_id = f"case_{case_id}"
        skill_dir = self.skill_store_path / skill_id
        await asyncio.to_thread(skill_dir.mkdir, parents=True, exist_ok=True)

        await asyncio.to_thread((skill_dir / "artifacts").mkdir, exist_ok=True)

        # Generate metadata.json
        metadata = {
            "title": f"Skill: {case_id}",
            "summary": f"Automated skill generated from successful execution of case {case_id}.",
            "references": [{"type": "case_id", "value": case_id}],
            "generated_at": datetime.now(UTC).isoformat(),
        }

        async with aiofiles.open(skill_dir / "metadata.json", "w") as f:
            await f.write(json.dumps(metadata, indent=4))

        # Generate overview.md
        overview = f"""# Skill: {case_id}

## Solution
{solution}

## Agent Experience
- Role: {experience.get("agent_role", "N/A")}
- Task: {experience.get("task", "N/A")}
- Execution Time: {experience.get("execution_time_seconds", "N/A")}s
"""
        async with aiofiles.open(skill_dir / "artifacts" / "overview.md", "w") as f:
            await f.write(overview)

        logger.info(f"Generated skill for case {case_id} at {skill_dir}")


def setup_skill_generator(skill_store_path: str) -> SkillGenerator:
    """Set up and subscribe skill generator to event bus."""
    generator = SkillGenerator(Path(skill_store_path))
    bus = get_event_bus()

    # In a real system, we'd use a more robust event type string
    async def sub_handler(event):
        if event.get("event_type") == "case.completed":
            await generator.handle_case_completed(event)

    bus.handlers["case.completed"].append(sub_handler)
    return generator
