"""
API key domain models.

Models for API key management and authentication.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .payment import SubscriptionTier


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID with optional prefix."""
    import uuid

    id_str = str(uuid.uuid4()).replace("-", "")
    return f"{prefix}_{id_str}" if prefix else id_str


def utc_now() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc)


@dataclass
class APIKey:
    """Represents an API key for programmatic access."""

    id: str = field(default_factory=lambda: generate_id("key"))
    user_id: str = ""
    key_hash: str = ""  # Hashed version of the key (never store plaintext)
    key_prefix: str = "grid"  # First 8 chars for identification
    tier: SubscriptionTier = SubscriptionTier.FREE
    name: str = ""  # User-friendly name for the key
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def is_expired(self) -> bool:
        """Check if API key has expired."""
        if self.expires_at is None:
            return False
        return utc_now() > self.expires_at

    def is_valid(self) -> bool:
        """Check if API key is valid (active and not expired)."""
        return self.is_active and not self.is_expired()

    def touch(self) -> None:
        """Update last used timestamp."""
        self.last_used_at = utc_now()
        self.updated_at = utc_now()

    def to_dict(self, include_hash: bool = False) -> Dict[str, Any]:
        """Serialize to dictionary."""
        result = {
            "id": self.id,
            "user_id": self.user_id,
            "key_prefix": self.key_prefix,
            "tier": self.tier.value,
            "name": self.name,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_hash:
            result["key_hash"] = self.key_hash
        return result
