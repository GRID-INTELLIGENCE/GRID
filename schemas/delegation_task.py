import dataclasses
from typing import Any, Literal


@dataclasses.dataclass
class DelegationTask:
    """
    Schema for a delegatable task, designed to be machine-readable.
    """

    id: str
    title: str
    description: str
    status: Literal["not-started", "in-progress", "completed", "blocked"]
    assignee: str | None = None
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    context_files: list[str] = dataclasses.field(default_factory=list)
    command_to_execute: str | None = None
    expected_output_format: str | None = None
    metadata: dict[str, Any] = dataclasses.field(default_factory=dict)
