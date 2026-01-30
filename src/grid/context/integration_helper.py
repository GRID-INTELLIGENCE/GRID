"""Helper functions for integrating context system with existing projects."""

import logging
from typing import Any

from .pattern_recognition import PatternRecognitionService
from .recognizer import ContextualRecognizer
from .user_context_manager import UserContextManager

logger = logging.getLogger(__name__)


def get_context_manager(user_id: str = "default") -> UserContextManager | None:
    """Get or create user context manager instance.

    Args:
        user_id: User identifier

    Returns:
        UserContextManager instance or None if unavailable
    """
    try:
        return UserContextManager(user_id=user_id)
    except Exception as e:
        logger.warning(f"Failed to initialize context manager: {e}")
        return None


def get_context_services(user_id: str = "default") -> dict[str, Any]:
    """Get all context services as a dictionary.

    Args:
        user_id: User identifier

    Returns:
        Dictionary with context_manager, pattern_service, and recognizer
    """
    context_manager = get_context_manager(user_id)
    if context_manager is None:
        return {}

    try:
        pattern_service = PatternRecognitionService(context_manager)
        recognizer = ContextualRecognizer(context_manager, pattern_service)

        return {
            "context_manager": context_manager,
            "pattern_service": pattern_service,
            "recognizer": recognizer,
        }
    except Exception as e:
        logger.warning(f"Failed to initialize context services: {e}")
        return {}


def track_file_access(file_path: str, project: str | None = None, user_id: str = "default") -> None:
    """Convenience function to track file access.

    Args:
        file_path: Path to file that was accessed
        project: Project identifier (optional, will be inferred)
        user_id: User identifier
    """
    context_manager = get_context_manager(user_id)
    if context_manager:
        try:
            context_manager.track_file_access(file_path, project)
        except Exception as e:
            logger.warning(f"Failed to track file access: {e}")


def track_tool_usage(
    tool_name: str,
    success: bool = True,
    duration_seconds: float | None = None,
    user_id: str = "default",
) -> None:
    """Convenience function to track tool usage.

    Args:
        tool_name: Name of tool used
        success: Whether tool usage was successful
        duration_seconds: Duration of tool usage
        user_id: User identifier
    """
    context_manager = get_context_manager(user_id)
    if context_manager:
        try:
            context_manager.track_tool_usage(tool_name, success, duration_seconds)
        except Exception as e:
            logger.warning(f"Failed to track tool usage: {e}")


def get_contextual_suggestions(user_id: str = "default") -> dict[str, Any]:
    """Get contextual suggestions for current context.

    Args:
        user_id: User identifier

    Returns:
        Dictionary with suggestions and context
    """
    services = get_context_services(user_id)
    if not services:
        return {}

    recognizer = services.get("recognizer")
    if recognizer:
        try:
            return recognizer.get_context_summary()
        except Exception as e:
            logger.warning(f"Failed to get contextual suggestions: {e}")
            return {}

    return {}
