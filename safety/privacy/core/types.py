from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from safety.privacy.core.masking import CompliancePreset, MaskingEngine

class PrivacyAction(str, Enum):
    """Actions to take when PII is detected."""

    MASK = "mask"  # Auto-mask the PII
    FLAG = "flag"  # Flag for review but don't mask
    BLOCK = "block"  # Block the request entirely
    ASK = "ask"  # Ask user what to do (interactive mode)
    LOG = "log"  # Log only, no action


@dataclass
class PrivacyConfig:
    """Configuration for privacy operations."""

    # Detection settings
    enable_detection: bool = True
    enabled_patterns: list[str] | None = None

    # Action settings
    default_action: PrivacyAction = PrivacyAction.ASK  # Interactive by default
    per_type_actions: dict[str, PrivacyAction] = field(default_factory=dict)

    # Masking settings
    compliance_preset: CompliancePreset | None = None
    masking_engine: MaskingEngine | None = None

    # Caching
    enable_cache: bool = True
    cache_ttl: int = 3600

    # Collaborative settings
    collaborative: bool = False  # Default: singular/personal mode
    context_id: str | None = None  # Workspace/team ID for collaborative


@dataclass
class PrivacyResult:
    """Result of a privacy operation."""

    success: bool
    original_text: str
    processed_text: str | None = None
    detections: list[dict[str, Any]] = field(default_factory=list)
    action_taken: PrivacyAction | None = None
    masked: bool = False
    blocked: bool = False
    requires_user_input: bool = False
    user_choice: str | None = None  # If requires_user_input is True
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "original_text": self.original_text,
            "processed_text": self.processed_text,
            "detections": self.detections,
            "action_taken": self.action_taken.value if self.action_taken else None,
            "masked": self.masked,
            "blocked": self.blocked,
            "requires_user_input": self.requires_user_input,
            "user_choice": self.user_choice,
            "error": self.error,
        }
