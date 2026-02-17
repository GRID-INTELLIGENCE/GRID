"""
Slash Commands Package
Provides command-line interface for common workflows and system operations
"""

from .base import BaseCommand, KnowledgeCommand, PipelineCommand, ReviewCommand
from .ci import CICommand
from .sync import SyncCommand

# Command registry for automatic discovery
COMMAND_REGISTRY = {
    "/ci": CICommand,
    "/sync": SyncCommand,
}


def get_command(command_name: str):
    """Get command instance by name"""
    if command_name not in COMMAND_REGISTRY:
        raise ValueError(f"Unknown command: {command_name}")

    return COMMAND_REGISTRY[command_name]()


def list_commands():
    """List all available commands"""
    return list(COMMAND_REGISTRY.keys())


__all__ = [
    "BaseCommand",
    "PipelineCommand",
    "KnowledgeCommand",
    "ReviewCommand",
    "CICommand",
    "SyncCommand",
    "get_command",
    "list_commands",
    "COMMAND_REGISTRY",
]
