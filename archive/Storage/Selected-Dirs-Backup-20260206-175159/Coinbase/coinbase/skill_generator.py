"""Skill generation from successful case executions."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .core.interfaces import IEventBus


@dataclass
class SkillMetadata:
    """Metadata for a generated skill."""

    title: str
    summary: str
    references: list[dict[str, str]]
    generated_at: str
    skill_id: str = field(default_factory=lambda: str(uuid4()))


class SkillGenerator:
    """Generates persistent skills from successful case executions."""

    def __init__(self, event_bus: IEventBus, skill_store_path: Path | None = None):
        self.event_bus = event_bus
        self.skill_store_path = skill_store_path or Path.home() / ".grid" / "knowledge"
        self.skill_store_path.mkdir(parents=True, exist_ok=True)

        # Subscribe to completion events
        self.event_bus.subscribe("case_completed", self.handle_case_completed)  # type: ignore

    def handle_case_completed(self, event: dict[str, Any]) -> SkillMetadata | None:
        """Handle case completion event and generate skill if successful."""
        if event.get("outcome") != "success":
            return None

        case_id = event.get("case_id", "unknown")
        solution = event.get("solution", "")
        agent_experience = event.get("agent_experience", {})

        # Create skill metadata
        metadata = SkillMetadata(
            title=f"Skill: {case_id}",
            summary=f"Automated skill generated from successful execution of case {case_id}.",
            references=[
                {"type": "case_id", "value": case_id},
                {"type": "agent_role", "value": agent_experience.get("agent_role", "unknown")},
            ],
            generated_at=datetime.now().isoformat(),
        )

        # Create skill directory
        skill_dir = self.skill_store_path / metadata.skill_id
        skill_dir.mkdir(parents=True, exist_ok=True)

        # Save metadata
        with open(skill_dir / "metadata.json", "w") as f:
            json.dump(
                {
                    "title": metadata.title,
                    "summary": metadata.summary,
                    "references": metadata.references,
                    "generated_at": metadata.generated_at,
                    "skill_id": metadata.skill_id,
                },
                f,
                indent=4,
            )

        # Create overview documentation
        overview = f"""# {metadata.title}

## Summary
{metadata.summary}

## Execution Details
- **Case ID**: {case_id}
- **Agent Role**: {agent_experience.get('agent_role', 'unknown')}
- **Task**: {agent_experience.get('task', 'unknown')}
- **Execution Time**: {event.get('execution_time_seconds', 0):.2f}s
- **Generated At**: {metadata.generated_at}

## Solution
```
{solution}
```

## References
{chr(10).join(f"- {ref['type']}: {ref['value']}" for ref in metadata.references)}
"""

        artifacts_dir = skill_dir / "artifacts"
        artifacts_dir.mkdir(exist_ok=True)

        with open(artifacts_dir / "overview.md", "w") as f:
            f.write(overview)

        print(f"[SkillGenerator] Generated skill: {metadata.skill_id} for case {case_id}")
        return metadata
