"""
Subscription and usage tracking models.

Note: This file contains subscription-related models that complement payment.py.
Subscription model is in payment.py, but usage tracking is here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


def utc_now() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(UTC)


@dataclass
class UsageRecord:
    """Represents a single API usage record."""

    id: str
    user_id: str
    api_key_id: str | None = None
    endpoint: str = ""
    cost_units: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        """Ensure ID is set if not provided."""
        if not self.id:
            import uuid

            self.id = str(uuid.uuid4())

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "api_key_id": self.api_key_id,
            "endpoint": self.endpoint,
            "cost_units": self.cost_units,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }
