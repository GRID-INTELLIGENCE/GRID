"""
API key management router.

Endpoints for creating, listing, and managing API keys.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta, timezone
from typing import List

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies import RequiredAuth, UoW
from ..exceptions import ResourceNotFoundError
from ..models.api_key import APIKey
from ..models.payment import SubscriptionTier
from ..schemas.api_key import (
    APIKeyCreatedResponse,
    APIKeyResponse,
    CreateAPIKeyRequest,
    UpdateAPIKeyRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


def generate_api_key() -> tuple[str, str]:
    """
    Generate a new API key and its hash.

    Returns:
        Tuple of (plaintext_key, hashed_key)
    """
    import uuid

    # Generate key with prefix
    key_prefix = "grid"
    key_suffix = str(uuid.uuid4()).replace("-", "")
    plaintext_key = f"{key_prefix}_{key_suffix}"

    # Hash the key
    hashed_key = bcrypt.hashpw(plaintext_key.encode(), bcrypt.gensalt()).decode()

    return plaintext_key, hashed_key


def verify_api_key(plaintext_key: str, hashed_key: str) -> bool:
    """
    Verify an API key against its hash.

    Args:
        plaintext_key: Plaintext API key
        hashed_key: Hashed API key

    Returns:
        True if key matches
    """
    try:
        return bcrypt.checkpw(plaintext_key.encode(), hashed_key.encode())
    except Exception:
        return False


@router.post("/", response_model=APIKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: CreateAPIKeyRequest,
    auth: RequiredAuth,
    uow: UoW,
) -> APIKeyCreatedResponse:
    """
    Create a new API key.

    The plaintext key is only shown once - make sure to store it securely.
    """
    user_id = auth.get("user_id", "unknown")

    # Generate key
    plaintext_key, hashed_key = generate_api_key()

    # Calculate expiration
    expires_at = None
    if request.expires_in_days:
        expires_at = datetime.now(UTC) + timedelta(days=request.expires_in_days)

    # Get user's subscription tier (default to FREE for now)
    # TODO: Integrate with subscription repository in Phase 1.2
    tier = SubscriptionTier.FREE

    # Create API key record
    api_key = APIKey(
        user_id=user_id,
        key_hash=hashed_key,
        key_prefix=plaintext_key[:8],
        tier=tier,
        name=request.name,
        expires_at=expires_at,
    )

    async with uow.transaction():
        await uow.api_keys.add(api_key)

    return APIKeyCreatedResponse(
        api_key=APIKeyResponse(**api_key.to_dict()),
        key=plaintext_key,
    )


@router.get("/", response_model=list[APIKeyResponse])
async def list_api_keys(
    auth: RequiredAuth,
    uow: UoW,
):
    """List all API keys for the current user."""
    user_id = auth.get("user_id", "unknown")
    api_keys = await uow.api_keys.get_by_user(user_id)
    return [APIKeyResponse(**key.to_dict()) for key in api_keys]


@router.get("/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: str,
    auth: RequiredAuth,
    uow: UoW,
):
    """Get API key details."""
    api_key = await uow.api_keys.get(key_id)
    if not api_key:
        raise ResourceNotFoundError("api_key", key_id)

    user_id = auth.get("user_id", "unknown")
    if api_key.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return APIKeyResponse(**api_key.to_dict())


@router.patch("/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: str,
    request: UpdateAPIKeyRequest,
    auth: RequiredAuth,
    uow: UoW,
):
    """Update an API key (name or active status)."""
    api_key = await uow.api_keys.get(key_id)
    if not api_key:
        raise ResourceNotFoundError("api_key", key_id)

    user_id = auth.get("user_id", "unknown")
    if api_key.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    if request.name is not None:
        api_key.name = request.name
    if request.is_active is not None:
        api_key.is_active = request.is_active

    async with uow.transaction():
        await uow.api_keys.update(api_key)

    return APIKeyResponse(**api_key.to_dict())


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: str,
    auth: RequiredAuth,
    uow: UoW,
):
    """Delete an API key."""
    api_key = await uow.api_keys.get(key_id)
    if not api_key:
        raise ResourceNotFoundError("api_key", key_id)

    user_id = auth.get("user_id", "unknown")
    if api_key.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    async with uow.transaction():
        await uow.api_keys.delete(key_id)
