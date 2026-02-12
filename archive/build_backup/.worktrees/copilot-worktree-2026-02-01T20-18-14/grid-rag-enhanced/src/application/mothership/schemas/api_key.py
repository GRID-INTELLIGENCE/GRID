"""
API key schemas.

Pydantic schemas for API key management requests and responses.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import Field

from ..schemas import BaseSchema


class CreateAPIKeyRequest(BaseSchema):
    """Request to create an API key."""

    name: str = Field(..., description="User-friendly name for the API key", min_length=1, max_length=100)
    expires_in_days: Optional[int] = Field(
        None, description="Number of days until expiration (None for no expiration)", gt=0
    )


class APIKeyResponse(BaseSchema):
    """API key response (without sensitive hash)."""

    id: str
    user_id: str
    key_prefix: str
    name: str
    tier: str
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class APIKeyCreatedResponse(BaseSchema):
    """Response after creating an API key (includes the key itself - only shown once)."""

    api_key: APIKeyResponse
    key: str = Field(..., description="The actual API key (only shown once, store securely)")


class UpdateAPIKeyRequest(BaseSchema):
    """Request to update an API key."""

    name: Optional[str] = Field(None, description="Update the name", min_length=1, max_length=100)
    is_active: Optional[bool] = Field(None, description="Activate or deactivate the key")
