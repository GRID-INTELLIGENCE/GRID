"""Cross-project context bridge for sharing user context and patterns."""

from .context_service import ContextService
from .profile_sync import ProfileSync
from .pattern_sharing import PatternSharing

__all__ = [
    "ContextService",
    "ProfileSync",
    "PatternSharing",
]
