"""
Authentication and trust-tier resolution for the safety enforcement pipeline.

Trust tiers: anon, user, verified, privileged.
Token validation is pluggable — default uses a shared secret HMAC JWT.
"""

from __future__ import annotations

import hmac
import os
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import jwt
from fastapi import Request
from jwt.exceptions import InvalidTokenError as JWTError

from safety.observability.logging_setup import get_logger

logger = get_logger("api.auth")


class TrustTier(StrEnum):
    ANON = "anon"
    USER = "user"
    VERIFIED = "verified"
    PRIVILEGED = "privileged"


@dataclass(frozen=True, slots=True)
class UserIdentity:
    """Resolved user identity attached to every request."""

    id: str
    trust_tier: TrustTier
    metadata: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Rate-limit defaults per tier (requests per day)
# ---------------------------------------------------------------------------
TIER_RATE_LIMITS: dict[TrustTier, int] = {
    TrustTier.ANON: 20,
    TrustTier.USER: 1_000,
    TrustTier.VERIFIED: 10_000,
    TrustTier.PRIVILEGED: int(os.getenv("PRIVILEGED_RATE_LIMIT", "100000")),
}


# ---------------------------------------------------------------------------
# Token validation
# ---------------------------------------------------------------------------
_JWT_SECRET: str | None = None
_JWT_ALGORITHM = "HS256"

# Mapping from JWT role claim to trust tier
_ROLE_TO_TIER: dict[str, TrustTier] = {
    "anon": TrustTier.ANON,
    "user": TrustTier.USER,
    "verified": TrustTier.VERIFIED,
    "privileged": TrustTier.PRIVILEGED,
    "admin": TrustTier.PRIVILEGED,
}


def _get_jwt_secret() -> str:
    global _JWT_SECRET
    if _JWT_SECRET is None:
        _JWT_SECRET = os.getenv("SAFETY_JWT_SECRET", "")
        if not _JWT_SECRET:
            logger.warning("jwt_secret_not_set", hint="Set SAFETY_JWT_SECRET env var")
    return _JWT_SECRET


def get_user_from_token(request: Request) -> UserIdentity:
    """
    Extract and validate user identity from the request.

    Checks Authorization header (Bearer token) and falls back to
    X-API-Key header, then to anonymous.
    """
    # 1. Try Bearer token
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        return _validate_jwt(token)

    # 2. Try API key
    api_key = request.headers.get("X-API-Key", "")
    if api_key:
        return _validate_api_key(api_key)

    # 3. Anonymous
    client_ip = request.client.host if request.client else "unknown"
    return UserIdentity(
        id=f"anon:{client_ip}",
        trust_tier=TrustTier.ANON,
    )


def _validate_jwt(token: str) -> UserIdentity:
    """Decode and validate a JWT, returning the user identity."""
    secret = _get_jwt_secret()
    if not secret:
        logger.error("jwt_validation_failed", reason="no_secret_configured")
        return UserIdentity(id="anon:no-secret", trust_tier=TrustTier.ANON)
    try:
        payload = jwt.decode(token, secret, algorithms=[_JWT_ALGORITHM])
        user_id = payload.get("sub", "")
        role = payload.get("role", "user")
        tier = _ROLE_TO_TIER.get(role, TrustTier.USER)
        if not user_id:
            raise JWTError("Missing 'sub' claim")
        return UserIdentity(
            id=str(user_id),
            trust_tier=tier,
            metadata={"jwt_claims": payload},
        )
    except JWTError as exc:
        logger.warning("jwt_validation_failed", error=str(exc))
        return UserIdentity(id="anon:bad-jwt", trust_tier=TrustTier.ANON)


def _validate_api_key(key: str) -> UserIdentity:
    """
    Validate an API key. Expected format in env: comma-separated key:tier pairs.
    E.g. SAFETY_API_KEYS="abc123:verified,def456:user"
    """
    keys_raw = os.getenv("SAFETY_API_KEYS", "")
    if not keys_raw:
        logger.warning("api_key_validation_failed", reason="no_keys_configured")
        return UserIdentity(id="anon:no-api-keys", trust_tier=TrustTier.ANON)

    for entry in keys_raw.split(","):
        entry = entry.strip()
        if ":" not in entry:
            continue
        stored_key, tier_name = entry.rsplit(":", 1)
        if hmac.compare_digest(stored_key, key):
            tier = _ROLE_TO_TIER.get(tier_name.strip(), TrustTier.USER)
            return UserIdentity(
                id=f"apikey:{stored_key[:8]}...",
                trust_tier=tier,
            )

    logger.warning("api_key_not_found")
    return UserIdentity(id="anon:invalid-key", trust_tier=TrustTier.ANON)


# ---------------------------------------------------------------------------
# Authorization helpers (used by observation_endpoints)
# ---------------------------------------------------------------------------
class Authorize:
    """FastAPI dependency for trust-tier authorization."""

    def __init__(self, min_tier: TrustTier = TrustTier.USER):
        self.min_tier = min_tier

    async def __call__(self, request: Request) -> UserIdentity:
        user = get_user_from_token(request)
        tier_order = [TrustTier.ANON, TrustTier.USER, TrustTier.VERIFIED, TrustTier.PRIVILEGED]
        if tier_order.index(user.trust_tier) < tier_order.index(self.min_tier):
            from fastapi import HTTPException

            raise HTTPException(status_code=403, detail="Insufficient trust tier")
        return user


def require_permission(min_tier: TrustTier = TrustTier.VERIFIED) -> Authorize:
    """Factory for Authorize dependency with a minimum trust tier."""
    return Authorize(min_tier=min_tier)


async def get_current_user(request: Request) -> UserIdentity:
    """
    FastAPI dependency to get the authenticated user.
    Prefers user from request state (set by middleware),
    otherwise tries to resolve from token.
    """
    # 1. Check if middleware already resolved it
    if hasattr(request.state, "user"):
        return request.state.user

    # 2. Fallback: try to resolve from token directly
    try:
        return get_user_from_token(request)
    except Exception:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=401,
            detail="Valid authentication credentials were not provided",
        )
