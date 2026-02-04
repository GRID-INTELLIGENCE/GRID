import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from grid.config.runtime_settings import RuntimeSettings
from grid.infrastructure.cache import CacheFactory

logger = logging.getLogger(__name__)


class TokenManager:
    """
    Manages JWT tokens (Issue, Verify, Revoke).
    Uses Cache backend for Denylist (Revocation).
    """

    def __init__(self, settings: RuntimeSettings | None = None):
        runtime = settings or RuntimeSettings.from_env()
        if not runtime.security.secret_key:
            logger.critical("Missing MOTHERSHIP_SECRET_KEY; refusing to start without a valid secret.")
            raise ValueError("MOTHERSHIP_SECRET_KEY is required")

        self.secret_key = runtime.security.secret_key
        self.algorithm = runtime.security.algorithm
        self.access_expiry = runtime.security.access_token_expire_minutes
        self.cache = CacheFactory.create(runtime.cache.backend)

    def create_access_token(self, data: dict, expires_delta: timedelta | None = None) -> str:
        """Create a new JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(minutes=self.access_expiry)

        to_encode.update({"exp": expire, "iat": datetime.now(UTC), "jti": str(uuid.uuid4())})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    async def verify_token(self, token: str) -> dict[str, Any]:
        """Verify token signature and check denylist."""
        # Check Denylist first
        is_revoked = await self.cache.get(f"denylist:{token}")
        if is_revoked:
            raise ValueError("Token has been revoked")

        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            raise ValueError(f"Could not validate credentials: {e}")

    async def revoke_token(self, token: str) -> None:
        """Revoke a token by adding it to the denylist until its expiry."""
        try:
            # Decode without verifying signature first to get expiry,
            # or just verify logic. Verification is safer.
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm], options={"verify_exp": False})
            exp = payload.get("exp")
            if exp:
                now = datetime.now(UTC).timestamp()
                ttl = int(exp - now)
                if ttl > 0:
                    await self.cache.set(f"denylist:{token}", "revoked", ttl=ttl)
                    logger.info(f"Token revoked. Denylisted for {ttl}s")
                else:
                    logger.info("Token already expired, no need to denylist.")
        except JWTError:
            logger.warning("Attempted to revoke invalid token")
