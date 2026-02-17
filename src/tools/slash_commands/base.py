"""
Base classes and interfaces for slash command implementations
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CommandResult:
    """Standard result format for all slash commands"""

    success: bool
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    error_details: str | None = None


@dataclass
class CommandContext:
    """Context information for command execution"""

    user_id: str | None = None
    workspace_path: str = ""
    environment: str = "development"
    permissions: list[str] = field(default_factory=list)
    session_id: str | None = None


class BaseCommand(ABC):
    """Base class for all slash commands"""

    def __init__(self):
        self.name = self.__class__.__name__.lower().replace("command", "")
        self.logger = logging.getLogger(f"commands.{self.name}")

    @abstractmethod
    async def execute(self, args: list[str], kwargs: dict[str, Any], context: CommandContext) -> CommandResult:
        """Execute the command with given arguments and context"""
        pass

    @abstractmethod
    def get_help(self) -> str:
        """Return help text for the command"""
        pass

    def validate_args(self, args: list[str], kwargs: dict[str, Any]) -> bool:
        """Validate command arguments"""
        return True

    def get_required_permissions(self) -> list[str]:
        """Return list of required permissions for this command"""
        return []

    def check_permissions(self, context: CommandContext) -> bool:
        """Check if context has required permissions"""
        required = self.get_required_permissions()
        return all(perm in context.permissions for perm in required)

    async def pre_execute(self, args: list[str], kwargs: dict[str, Any], context: CommandContext) -> bool:
        """Pre-execution hook, return False to abort"""
        if not self.validate_args(args, kwargs):
            raise ValueError("Invalid arguments")

        if not self.check_permissions(context):
            raise PermissionError("Insufficient permissions")

        return True

    async def post_execute(self, result: CommandResult, context: CommandContext) -> CommandResult:
        """Post-execution hook for result processing"""
        # Log execution
        self.logger.info(f"Command {self.name} executed: {result.success}")

        # Add timestamp if not present
        if result.timestamp is None:
            result.timestamp = datetime.now(timezone.utc)

        return result


class PipelineCommand(BaseCommand):
    """Base class for pipeline-style commands"""

    def __init__(self):
        super().__init__()
        self.steps = []

    def add_step(self, name: str, func, required: bool = True):
        """Add a step to the pipeline"""
        self.steps.append({"name": name, "func": func, "required": required, "result": None})

    async def execute_pipeline(self, context: CommandContext) -> dict[str, Any]:
        """Execute all pipeline steps"""
        results = {}

        for step in self.steps:
            try:
                self.logger.info(f"Executing step: {step['name']}")
                step_result = await step["func"](context)
                step["result"] = step_result
                results[step["name"]] = step_result

                if step["required"] and not step_result.get("success", True):
                    self.logger.error(f"Required step failed: {step['name']}")
                    break

            except Exception as e:
                self.logger.error(f"Step {step['name']} failed: {e}")
                step["result"] = {"success": False, "error": str(e)}
                results[step["name"]] = step["result"]

                if step["required"]:
                    break

        return results


class KnowledgeCommand(BaseCommand):
    """Base class for knowledge-related commands"""

    def __init__(self):
        super().__init__()
        self.knowledge_base = None

    async def initialize_knowledge_base(self):
        """Initialize connection to knowledge base"""
        # This would be implemented based on your knowledge system
        pass

    async def update_knowledge_graph(self, updates: dict[str, Any]):
        """Update knowledge graph with new information"""
        # Implementation depends on your graph system
        pass


class ReviewCommand(BaseCommand):
    """Base class for review/audit commands"""

    def __init__(self):
        super().__init__()
        self.review_criteria = {}

    def add_review_criterion(self, name: str, weight: float, check_func):
        """Add a review criterion"""
        self.review_criteria[name] = {"weight": weight, "check": check_func, "result": None}

    async def run_review(self, context: CommandContext) -> dict[str, Any]:
        """Run all review criteria"""
        results = {}
        total_score = 0.0
        total_weight = 0.0

        for name, criterion in self.review_criteria.items():
            try:
                result = await criterion["check"](context)
                criterion["result"] = result
                results[name] = result

                if result.get("success", True):
                    score = result.get("score", 0.0)
                    total_score += score * criterion["weight"]
                    total_weight += criterion["weight"]

            except Exception as e:
                self.logger.error(f"Review criterion {name} failed: {e}")
                results[name] = {"success": False, "error": str(e)}

        # Calculate overall score
        overall_score = total_score / total_weight if total_weight > 0 else 0.0
        results["overall_score"] = overall_score
        results["total_weight"] = total_weight

        return results


# Utility functions for command implementations
def format_duration(seconds: float) -> str:
    """Format duration in human-readable format"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def truncate_string(text: str, max_length: int = 100) -> str:
    """Truncate string to specified length"""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def safe_execute(func, *args, **kwargs):
    """Safely execute function with error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Safe execution failed: {e}")
        return None
