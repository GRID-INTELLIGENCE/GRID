"""
Secret validation and management utilities.

Implements industry best practices for secret management following
OWASP guidelines and community standards for AI safety and security.
"""

from __future__ import annotations

import hashlib
import logging
import os
import secrets
import string
from enum import StrEnum

logger = logging.getLogger(__name__)

# Minimum secret requirements following OWASP guidelines
MIN_SECRET_LENGTH = 32  # Minimum 32 characters for HS256
RECOMMENDED_SECRET_LENGTH = 64  # Recommended 64+ characters
MAX_SECRET_LENGTH = 512  # Reasonable maximum


class SecretValidationError(Exception):
    """Raised when secret validation fails."""

    pass


class SecretStrength(StrEnum):
    """Secret strength classification."""

    WEAK = "weak"
    ACCEPTABLE = "acceptable"
    STRONG = "strong"


def generate_secure_secret(length: int = RECOMMENDED_SECRET_LENGTH) -> str:
    """
    Generate a cryptographically secure secret key.

    Uses secrets module (cryptographically secure random) following
    Python security best practices and OWASP recommendations.

    Args:
        length: Desired secret length (default: 64)

    Returns:
        Cryptographically secure random secret string

    Raises:
        ValueError: If length is less than MIN_SECRET_LENGTH
    """
    if length < MIN_SECRET_LENGTH:
        raise ValueError(f"Secret length must be at least {MIN_SECRET_LENGTH} characters")

    # Use URL-safe base64 encoding for better entropy per character
    # This provides better security than hex encoding
    alphabet = string.ascii_letters + string.digits + "-_"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def validate_secret_strength(secret: str, environment: str = "production") -> SecretStrength:
    """
    Validate secret strength following OWASP guidelines.

    Args:
        secret: Secret string to validate
        environment: Environment (production, development, testing)

    Returns:
        SecretStrength classification

    Raises:
        SecretValidationError: If secret is too weak for the environment
    """
    if not secret:
        raise SecretValidationError("Secret key cannot be empty")

    length = len(secret)

    # Check minimum length (enforce strictly in production)
    if length < MIN_SECRET_LENGTH:
        msg = (
            f"Secret key must be at least {MIN_SECRET_LENGTH} characters "
            f"(current: {length}). Use generate_secure_secret() to create a secure key."
        )
        if environment.lower() == "production":
            raise SecretValidationError(msg)
        logger.warning(f"SECURITY WARNING: {msg}")

    # Check entropy (character diversity)
    unique_chars = len(set(secret))
    entropy_ratio = unique_chars / max(length, 1)

    # Classify strength
    if length >= RECOMMENDED_SECRET_LENGTH and entropy_ratio >= 0.5:
        strength = SecretStrength.STRONG
    elif length >= MIN_SECRET_LENGTH and entropy_ratio >= 0.3:
        strength = SecretStrength.ACCEPTABLE
    else:
        strength = SecretStrength.WEAK

    # In production, reject weak secrets
    if environment.lower() == "production" and strength == SecretStrength.WEAK:
        raise SecretValidationError(
            f"Secret key is too weak for production. "
            f"Length: {length}, Entropy ratio: {entropy_ratio:.2f}. "
            f"Generate a secure key with generate_secure_secret()."
        )

    # Check for common weak patterns
    weak_patterns = [
        "password",
        "secret",
        "key",
        "123456",
        "admin",
        "test",
        "default",
        "insecure",
        "change-in-production",
    ]

    secret_lower = secret.lower()
    for pattern in weak_patterns:
        if pattern in secret_lower:
            if environment.lower() == "production":
                raise SecretValidationError(
                    f"Secret key contains weak pattern '{pattern}' which is not allowed in production"
                )
            logger.warning(f"Secret key contains weak pattern '{pattern}' - not recommended")

    return strength


def get_secret_from_env(
    env_var: str,
    required: bool = True,
    environment: str = "production",
    default: str | None = None,
) -> str:
    """
    Get secret from environment variable with validation.

    Follows industry best practices:
    - Fails fast if required secret is missing
    - Validates secret strength
    - Provides helpful error messages
    - Never uses insecure defaults in production

    Args:
        env_var: Environment variable name
        required: Whether secret is required
        environment: Current environment (production, development, testing)
        default: Optional default value (only used if not required)

    Returns:
        Validated secret string

    Raises:
        SecretValidationError: If secret is missing (when required) or too weak
    """
    secret = os.getenv(env_var)

    # Handle missing secret
    if not secret or not secret.strip():
        if required:
            if environment.lower() == "production":
                raise SecretValidationError(
                    f"Required secret environment variable '{env_var}' is not set. "
                    f"This is a CRITICAL security issue in production. "
                    f"Set {env_var} to a secure value (use generate_secure_secret() to create one)."
                )
            else:
                # In development/testing, allow default but warn
                if default:
                    logger.warning(
                        f"Secret environment variable '{env_var}' not set, using provided default. "
                        f"This is INSECURE and must be fixed before production."
                    )
                    secret = default
                else:
                    raise SecretValidationError(
                        f"Required secret environment variable '{env_var}' is not set. "
                        f"Set {env_var} in your environment or .env file."
                    )
        else:
            # Not required, return default or empty string
            return default or ""

    secret = secret.strip()

    # Validate strength
    try:
        strength = validate_secret_strength(secret, environment)
        if strength == SecretStrength.WEAK and environment.lower() == "production":
            raise SecretValidationError(
                f"Secret in '{env_var}' is too weak for production. "
                f"Generate a secure secret with generate_secure_secret()."
            )
    except SecretValidationError:
        raise  # Re-raise validation errors
    except Exception as e:
        logger.warning(f"Secret validation warning for '{env_var}': {e}")

    # Security audit log (without exposing the secret)
    secret_hash = hashlib.sha256(secret.encode()).hexdigest()[:16]
    logger.info(f"Secret loaded from '{env_var}' (length={len(secret)}, strength={strength.value}, hash={secret_hash})")

    return secret


def mask_secret(secret: str, visible_chars: int = 4) -> str:
    """
    Mask secret for logging/display purposes.

    Args:
        secret: Secret to mask
        visible_chars: Number of visible characters at start and end

    Returns:
        Masked secret string (e.g., "abcd...xyz")
    """
    if not secret or len(secret) <= visible_chars * 2:
        return "***"
    return f"{secret[:visible_chars]}...{secret[-visible_chars:]}"


__all__ = [
    "SecretValidationError",
    "SecretStrength",
    "generate_secure_secret",
    "validate_secret_strength",
    "get_secret_from_env",
    "mask_secret",
    "MIN_SECRET_LENGTH",
    "RECOMMENDED_SECRET_LENGTH",
]
