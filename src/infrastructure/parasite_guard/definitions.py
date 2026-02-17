"""
Parasite Guard Data Definitions.

Contains data structures and types for the Parasite Guard system.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class ParasiteRisk(str, Enum):
    """Risk levels for detected parasites."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ParasiteAction(str, Enum):
    """Actions to take on detected parasites."""

    DETECT_ONLY = "detect_only"
    BLOCK = "block"
    SANITIZE = "sanitize"


@dataclass
class SourceMap:
    """Represents the source of a request."""

    ip: str
    user_agent: str
    user_id: str | None = None
    session_id: str | None = None
    trace_id: str | None = None


@dataclass
class ParasiteContext:
    """
    Context for a detected parasite.

    Attributes:
        id: Unique identifier for this detection event.
        component: The component reporting the parasite (e.g., "websocket").
        rule: The specific rule violated (e.g., "no_ack").
        risk: The risk severity.
        action: The action taken (or calculated/simulated).
        source: Information about the request source.
        start_ts: Timestamp of detection.
        subscription_id: Optional ID of a created subscription (for EventBus sanitization).
        meta: Additional context (e.g., connection metrics).
    """

    component: str
    rule: str
    risk: ParasiteRisk
    action: ParasiteAction
    source: SourceMap | None = None
    id: UUID = field(default_factory=uuid4)
    start_ts: datetime = field(default_factory=datetime.now(timezone.utc))
    subscription_id: UUID | None = None  # To be used for EventBus/Subscription tracking
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for logging."""
        return {
            "id": str(self.id),
            "component": self.component,
            "rule": self.rule,
            "risk": self.risk.value,
            "action": self.action.value,
            "timestamp": self.start_ts.isoformat(),
            "source": (
                {
                    "ip": self.source.ip,
                    "user_id": self.source.user_id,
                    "session_id": self.source.session_id,
                }
                if self.source
                else None
            ),
            "meta": self.meta,
        }
