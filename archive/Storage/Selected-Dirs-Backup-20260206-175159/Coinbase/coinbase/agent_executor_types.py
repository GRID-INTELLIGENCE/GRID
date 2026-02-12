"""Types for AgentExecutor."""

from dataclasses import dataclass
from typing import Any


@dataclass
class ExecutionResult:
    """Result of a task execution."""

    success: bool
    result: Any
    error: str | None = None
    duration_ms: int = 0
