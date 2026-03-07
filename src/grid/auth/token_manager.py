import logging
import base64
import hashlib
import hmac
import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

try:
    import jwt
    from jwt.exceptions import InvalidTokenError as JWTError
except ImportError:
    jwt = None  # type: ignore[assignment]

    class JWTError(Exception):
        pass

from grid.config.runtime_settings import RuntimeSettings
from grid.infrastructure.cache import CacheFactory

logger = logging.getLogger(__name__)


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(value, datetime):
            normalized[key] = int(value.timestamp())
        else:
            normalized[key] = value
    return normalized


def _encode_jwt(payload: dict[str, Any], secret_key: str, algorithm: str) -> str:
    normalized = _normalize_payload(payload)
    if jwt is not None:
        return jwt.encode(normalized, secret_key, algorithm=algorithm)
    if algorithm != "HS256":
        raise ValueError(f"Unsupported JWT algorithm without PyJWT: {algorithm}")

    header = {"alg": algorithm, "typ": "JWT"}
    header_segment = _base64url_encode(json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    payload_segment = _base64url_encode(json.dumps(normalized, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signing_input = f"{header_segment}.{payload_segment}"
    signature = hmac.new(secret_key.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
    return f"{signing_input}.{_base64url_encode(signature)}"


def _decode_jwt(token: str, secret_key: str, algorithm: str, verify_exp: bool = True) -> dict[str, Any]:
    if jwt is not None:
        return jwt.decode(token, secret_key, algorithms=[algorithm], options={"verify_exp": verify_exp})
    if algorithm != "HS256":
        raise ValueError(f"Unsupported JWT algorithm without PyJWT: {algorithm}")

    try:
        header_segment, payload_segment, signature_segment = token.split(".")
        header = json.loads(_base64url_decode(header_segment).decode("utf-8"))
        if header.get("alg") != algorithm:
            raise JWTError("Algorithm mismatch")

        signing_input = f"{header_segment}.{payload_segment}"
        expected_signature = hmac.new(
            secret_key.encode("utf-8"),
            signing_input.encode("ascii"),
            hashlib.sha256,
        ).digest()
        actual_signature = _base64url_decode(signature_segment)
        if not hmac.compare_digest(expected_signature, actual_signature):
            raise JWTError("Signature verification failed")

        payload = json.loads(_base64url_decode(payload_segment).decode("utf-8"))
        exp = payload.get("exp")
        if verify_exp and exp is not None and float(exp) < datetime.now(UTC).timestamp():
            raise JWTError("Signature has expired")
        return payload
    except ValueError as exc:
        raise JWTError("Malformed token") from exc
    except (TypeError, json.JSONDecodeError) as exc:
        raise JWTError("Invalid token payload") from exc


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

    def create_access_token(self, data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
        """Create a new JWT access token."""
        to_encode: dict[str, Any] = data.copy()
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(minutes=self.access_expiry)

        to_encode.update({"exp": expire, "iat": datetime.now(UTC), "jti": str(uuid.uuid4())})
        encoded_jwt = _encode_jwt(to_encode, self.secret_key, self.algorithm)
        return encoded_jwt

    async def verify_token(self, token: str) -> dict[str, Any]:
        """Verify token signature and check denylist."""
        # Check Denylist first
        is_revoked = await self.cache.get(f"denylist:{token}")
        if is_revoked:
            raise ValueError("Token has been revoked")

        try:
            payload = _decode_jwt(token, self.secret_key, self.algorithm)
            return payload
        except JWTError as e:
            raise ValueError(f"Could not validate credentials: {e}")

    async def revoke_token(self, token: str) -> None:
        """Revoke a token by adding it to the denylist until its expiry."""
        try:
            # Decode without verifying signature first to get expiry,
            # or just verify logic. Verification is safer.
            payload = _decode_jwt(token, self.secret_key, self.algorithm, verify_exp=False)
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
