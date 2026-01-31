"""Token revocation list (blacklist) implementation.

Provides JWT token invalidation with:
- JTI (JWT ID) storage in Redis/database
- Token validation checks against revocation list
- Periodic cleanup of expired revocations
- Automatic expiration based on token expiry
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from grid.integration.domain_gateway import DomainGateway

logger = logging.getLogger(__name__)


class TokenRevocationList:
    """Token revocation list for JWT blacklisting.

    Stores revoked token JTIs (JWT IDs) with automatic expiration.
    Uses the domain gateway's persistence layer for storage.
    """

    def __init__(self, key_prefix: str = "revoked_token:"):
        """Initialize the revocation list.

        Args:
            key_prefix: Prefix for revocation keys in storage
        """
        self._key_prefix = key_prefix
        self._gateway = DomainGateway()

    def _make_key(self, jti: str) -> str:
        """Create storage key for a JTI."""
        return f"{self._key_prefix}{jti}"

    async def revoke_token(
        self,
        jti: str,
        expires_at: datetime | None = None,
        reason: str | None = None
    ) -> bool:
        """Revoke a token by its JTI.

        Args:
            jti: JWT ID to revoke
            expires_at: When the token naturally expires (for TTL)
            reason: Optional reason for revocation

        Returns:
            True if revocation was stored successfully
        """
        key = self._make_key(jti)

        # Calculate TTL if expiration provided
        ttl = None
        if expires_at:
            ttl_seconds = int((expires_at - datetime.now(UTC)).total_seconds())
            if ttl_seconds > 0:
                ttl = ttl_seconds
            else:
                # Token already expired, no need to store
                return True

        # Store revocation with metadata
        revocation_data = {
            "jti": jti,
            "revoked_at": datetime.now(UTC).isoformat(),
            "reason": reason or "logout",
            "expires_at": expires_at.isoformat() if expires_at else None,
        }

        try:
            result = await self._gateway.persistence.store(key, revocation_data, ttl=ttl)
            if result:
                logger.info(f"Token revoked: {jti}, reason: {reason}")
            return result
        except Exception as e:
            logger.error(f"Failed to revoke token {jti}: {e}")
            return False

    async def is_revoked(self, jti: str) -> bool:
        """Check if a token JTI is revoked.

        Args:
            jti: JWT ID to check

        Returns:
            True if token is revoked, False otherwise
        """
        key = self._make_key(jti)

        try:
            data = await self._gateway.persistence.retrieve(key)
            return data is not None
        except Exception as e:
            logger.error(f"Error checking revocation status for {jti}: {e}")
            return False

    async def cleanup_expired(self) -> int:
        """Clean up expired revocations.

        Note: If using TTL in storage backend, this may not be necessary
        as expired entries are automatically removed.

        Returns:
            Number of entries cleaned up
        """
        # This is a placeholder - in practice, Redis and similar backends
        # handle TTL expiration automatically
        logger.debug("Cleanup requested - using TTL-based expiration")
        return 0

    async def get_revocation_info(self, jti: str) -> dict[str, Any] | None:
        """Get detailed revocation information for a JTI.

        Args:
            jti: JWT ID to lookup

        Returns:
            Revocation metadata if found, None otherwise
        """
        key = self._make_key(jti)

        try:
            return await self._gateway.persistence.retrieve(key)
        except Exception as e:
            logger.error(f"Error retrieving revocation info for {jti}: {e}")
            return None


class TokenValidator:
    """Enhanced JWT validator with revocation checking."""

    def __init__(self, revocation_list: TokenRevocationList | None = None):
        """Initialize the validator.

        Args:
            revocation_list: Revocation list instance (creates default if None)
        """
        self._revocation_list = revocation_list or TokenRevocationList()

    async def validate_token(
        self,
        token_payload: dict[str, Any],
        verify_exp: bool = True
    ) -> tuple[bool, str | None]:
        """Validate a token including revocation check.

        Args:
            token_payload: Decoded JWT payload
            verify_exp: Whether to verify expiration

        Returns:
            Tuple of (is_valid, error_message)
        """
        jti = token_payload.get("jti")

        # Check if token has JTI
        if not jti:
            return False, "Token missing JTI claim"

        # Check if token is revoked
        if await self._revocation_list.is_revoked(jti):
            return False, "Token has been revoked"

        # Check expiration if requested
        if verify_exp:
            exp = token_payload.get("exp")
            if exp:
                from datetime import datetime
                if datetime.now(UTC).timestamp() > exp:
                    return False, "Token has expired"

        return True, None

    async def revoke_token(
        self,
        token_payload: dict[str, Any],
        reason: str | None = None
    ) -> bool:
        """Revoke a token by its payload.

        Args:
            token_payload: Decoded JWT payload
            reason: Optional reason for revocation

        Returns:
            True if successfully revoked
        """
        jti = token_payload.get("jti")
        if not jti:
            logger.warning("Cannot revoke token without JTI")
            return False

        exp_timestamp = token_payload.get("exp")
        expires_at = None
        if exp_timestamp:
            expires_at = datetime.fromtimestamp(exp_timestamp, tz=UTC)

        return await self._revocation_list.revoke_token(jti, expires_at, reason)


# Global instances for convenience
_revocation_list: TokenRevocationList | None = None
_token_validator: TokenValidator | None = None


def get_revocation_list() -> TokenRevocationList:
    """Get or create the global revocation list."""
    global _revocation_list
    if _revocation_list is None:
        _revocation_list = TokenRevocationList()
    return _revocation_list


def get_token_validator() -> TokenValidator:
    """Get or create the global token validator."""
    global _token_validator
    if _token_validator is None:
        _token_validator = TokenValidator(get_revocation_list())
    return _token_validator


async def revoke_token_by_jti(jti: str, expires_at: datetime | None = None, reason: str | None = None) -> bool:
    """Convenience function to revoke a token by JTI.

    Args:
        jti: JWT ID to revoke
        expires_at: Token expiration time
        reason: Revocation reason

    Returns:
        True if successfully revoked
    """
    revocation_list = get_revocation_list()
    return await revocation_list.revoke_token(jti, expires_at, reason)


async def is_token_revoked(jti: str) -> bool:
    """Convenience function to check if a token is revoked.

    Args:
        jti: JWT ID to check

    Returns:
        True if revoked
    """
    revocation_list = get_revocation_list()
    return await revocation_list.is_revoked(jti)
