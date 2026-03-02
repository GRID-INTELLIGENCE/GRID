"""Signature-based authentication for guardrail profile access."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass, field
from typing import Any

from .models import GuardrailProfile


@dataclass
class AuthSignature:
    """Signature for profile authentication."""
    profile_name: str
    signature: str
    timestamp: int
    nonce: str = field(default_factory=lambda: secrets.token_urlsafe(16))
    metadata: dict[str, Any] = field(default_factory=dict)


class GuardrailAuth:
    """Signature-based authentication for guardrail profiles."""

    def __init__(self, secret_key: str | None = None):
        """Initialize with secret key for signature validation."""
        self.secret_key = secret_key or secrets.token_hex(32)

    def generate_profile_signature(
        self,
        profile: GuardrailProfile,
        user_id: str,
        timestamp: int,
        nonce: str | None = None,
        extra_data: dict[str, Any] | None = None
    ) -> AuthSignature:
        """Generate authenticated signature for profile access."""
        if nonce is None:
            nonce = secrets.token_urlsafe(16)

        # Create signature payload
        payload = f"{profile.name}:{user_id}:{timestamp}:{nonce}"

        if extra_data:
            # Sort keys for consistent hashing
            sorted_extra = sorted(extra_data.items())
            extra_str = ":".join(f"{k}={v}" for k, v in sorted_extra)
            payload += f":{extra_str}"

        # Generate HMAC signature
        signature = hmac.new(
            self.secret_key.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        return AuthSignature(
            profile_name=profile.name,
            signature=signature,
            timestamp=timestamp,
            nonce=nonce,
            metadata={
                "user_id": user_id,
                "extra_data": extra_data or {},
                "payload_hash": hashlib.sha256(payload.encode()).hexdigest()
            }
        )

    def validate_profile_signature(
        self,
        profile: GuardrailProfile,
        auth_sig: AuthSignature,
        user_id: str,
        max_age_seconds: int = 300  # 5 minutes default
    ) -> bool:
        """Validate signature for profile access."""
        import time
        current_time = int(time.time())

        # Check timestamp freshness
        if current_time - auth_sig.timestamp > max_age_seconds:
            return False

        # Regenerate signature for comparison
        expected_sig = self.generate_profile_signature(
            profile=profile,
            user_id=user_id,
            timestamp=auth_sig.timestamp,
            nonce=auth_sig.nonce,
            extra_data=auth_sig.metadata.get("extra_data")
        )

        # Use constant-time comparison
        return hmac.compare_digest(auth_sig.signature, expected_sig.signature)

    def narrow_access_scope(
        self,
        requested_profile: str,
        user_permissions: set[str],
        user_role: str
    ) -> str | None:
        """Narrow accessibility scope based on user permissions and role.

        Returns the requested profile if allowed, otherwise None (deny access).
        """
        # Define role-based access mappings
        role_mappings = {
            "developer": {"developer", "basic"},
            "designer": {"designer", "basic"},
            "manager": {"manager", "designer", "developer", "basic"},
            "admin": {"admin", "manager", "designer", "developer", "basic"}
        }

        # Get allowed profiles for this role
        allowed_profiles = role_mappings.get(user_role, {"basic"})

        # Check if user has explicit permission or role allows access
        if requested_profile in user_permissions or requested_profile in allowed_profiles:
            return requested_profile

        # Deny access - scope is narrowed, no fallback to lower privilege
        return None

    def hash_user_signature(self, user_id: str, profile_name: str) -> str:
        """Generate signature-based hash for user-profile combination."""
        combined = f"{user_id}:{profile_name}:{self.secret_key}"
        return hashlib.sha256(combined.encode()).hexdigest()


# Global auth instance for the guardrail system
_default_auth = GuardrailAuth()


def get_default_auth() -> GuardrailAuth:
    """Get the default guardrail authentication instance."""
    return _default_auth


def create_auth_signature(
    profile: GuardrailProfile,
    user_id: str,
    timestamp: int | None = None,
    auth: GuardrailAuth | None = None
) -> AuthSignature:
    """Convenience function to create auth signature."""
    if timestamp is None:
        import time
        timestamp = int(time.time())

    auth = auth or get_default_auth()
    return auth.generate_profile_signature(profile, user_id, timestamp)


def validate_auth_signature(
    profile: GuardrailProfile,
    auth_sig: AuthSignature,
    user_id: str,
    auth: GuardrailAuth | None = None
) -> bool:
    """Convenience function to validate auth signature."""
    auth = auth or get_default_auth()
    return auth.validate_profile_signature(profile, auth_sig, user_id)
