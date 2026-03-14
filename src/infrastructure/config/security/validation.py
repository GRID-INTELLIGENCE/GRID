"""
Secret Strength Validation.

Validates secret/key strength based on:
- Length requirements
- Entropy estimation
- Character variety
- Common weak patterns

Environment-aware: Stricter in production, lenient in development.

Extracted from Mothership's secret_validation module.
"""

from __future__ import annotations

import hashlib
import logging
import math
import secrets
import string
from enum import Enum

logger = logging.getLogger(__name__)


class SecretStrength(Enum):
    """Secret strength levels."""

    WEAK = "weak"
    ACCEPTABLE = "acceptable"
    STRONG = "strong"


class SecretValidationError(ValueError):
    """Raised when secret validation fails in fail-fast mode."""

    pass


# Minimum lengths by environment
MIN_LENGTHS = {
    "development": 16,
    "test": 16,
    "testing": 16,
    "staging": 32,
    "production": 64,
}

# Common weak patterns to reject
WEAK_PATTERNS = [
    "password",
    "secret",
    "admin",
    "root",
    "test",
    "demo",
    "example",
    "123456",
    "qwerty",
    "abc123",
]


def validate_secret_strength(
    secret: str,
    environment: str = "development",
    *,
    min_length: int | None = None,
) -> SecretStrength:
    """
    Validate secret strength.

    Args:
        secret: Secret string to validate
        environment: Environment name for context-aware validation
        min_length: Override minimum length requirement

    Returns:
        SecretStrength level

    Raises:
        SecretValidationError: If secret is empty or too short for environment
    """
    if not secret:
        raise SecretValidationError("Secret is empty")

    secret = secret.strip()

    # Get minimum length for environment
    required_length = min_length or MIN_LENGTHS.get(environment.lower(), 32)

    # Check minimum length
    if len(secret) < required_length:
        if environment.lower() == "production":
            raise SecretValidationError(
                f"Secret too short for production: {len(secret)} chars "
                f"(minimum: {required_length}). Use generate_secure_secret()."
            )
        return SecretStrength.WEAK

    # Check for weak patterns
    secret_lower = secret.lower()
    for pattern in WEAK_PATTERNS:
        if pattern in secret_lower:
            logger.warning(f"Secret contains weak pattern: '{pattern}'")
            return SecretStrength.WEAK

    # Calculate entropy
    entropy = _calculate_entropy(secret)

    # Determine strength
    if len(secret) >= 64 and entropy > 4.0:
        return SecretStrength.STRONG
    elif len(secret) >= 32 and entropy > 3.0:
        return SecretStrength.ACCEPTABLE
    else:
        return SecretStrength.WEAK


def _calculate_entropy(secret: str) -> float:
    """
    Calculate Shannon entropy of secret.

    Higher entropy = more random = stronger secret.

    Args:
        secret: Secret string

    Returns:
        Entropy in bits per character
    """
    if not secret:
        return 0.0

    # Count character frequencies
    freq: dict[str, int] = {}
    for char in secret:
        freq[char] = freq.get(char, 0) + 1

    # Calculate entropy
    length = len(secret)
    entropy = 0.0

    for count in freq.values():
        probability = count / length
        if probability > 0:
            entropy -= probability * math.log2(probability)

    return entropy


def generate_secure_secret(length: int = 64, *, url_safe: bool = True) -> str:
    """
    Generate a cryptographically secure secret.

    Args:
        length: Length of secret to generate
        url_safe: If True, use URL-safe characters only

    Returns:
        Secure random secret string

    Examples:
        >>> secret = generate_secure_secret(32)
        >>> len(secret)
        32
    """
    if url_safe:
        # Use URL-safe base64 alphabet
        alphabet = string.ascii_letters + string.digits + "-_"
    else:
        alphabet = string.ascii_letters + string.digits + string.punctuation

    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_token(prefix: str = "", length: int = 32) -> str:
    """
    Generate a token with optional prefix.

    Args:
        prefix: Optional prefix (e.g., "dapi" for Databricks)
        length: Length of random portion

    Returns:
        Token string

    Examples:
        >>> token = generate_token("dapi", 32)
        >>> token.startswith("dapi")
        True
    """
    random_part = secrets.token_hex(length)
    return f"{prefix}{random_part}" if prefix else random_part


def hash_secret(secret: str, algorithm: str = "sha256") -> str:
    """
    Hash a secret for storage/comparison.

    Args:
        secret: Secret to hash
        algorithm: Hash algorithm (sha256, sha512, blake2b)

    Returns:
        Hex-encoded hash string
    """
    if algorithm == "sha256":
        return hashlib.sha256(secret.encode()).hexdigest()
    elif algorithm == "sha512":
        return hashlib.sha512(secret.encode()).hexdigest()
    elif algorithm == "blake2b":
        return hashlib.blake2b(secret.encode()).hexdigest()
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")


def compare_secrets(secret: str, hashed: str, algorithm: str = "sha256") -> bool:
    """
    Compare secret against hash in constant time.

    Uses secrets.compare_digest to prevent timing attacks.

    Args:
        secret: Secret to compare
        hashed: Hashed secret to compare against
        algorithm: Hash algorithm used

    Returns:
        True if secret matches hash
    """
    secret_hash = hash_secret(secret, algorithm)
    return secrets.compare_digest(secret_hash, hashed)


class SecretValidator:
    """
    Configurable secret validator.

    Usage:
        validator = SecretValidator(
            min_length=32,
            require_uppercase=True,
            require_lowercase=True,
            require_digits=True,
            require_symbols=True,
        )

        strength = validator.validate("MySecret123!")
    """

    def __init__(
        self,
        *,
        min_length: int = 32,
        require_uppercase: bool = False,
        require_lowercase: bool = False,
        require_digits: bool = False,
        require_symbols: bool = False,
        forbidden_patterns: list[str] | None = None,
    ):
        """
        Initialize validator.

        Args:
            min_length: Minimum length requirement
            require_uppercase: Require uppercase letters
            require_lowercase: Require lowercase letters
            require_digits: Require digits
            require_symbols: Require symbols
            forbidden_patterns: Additional patterns to forbid
        """
        self._min_length = min_length
        self._require_uppercase = require_uppercase
        self._require_lowercase = require_lowercase
        self._require_digits = require_digits
        self._require_symbols = require_symbols
        self._forbidden_patterns = forbidden_patterns or []

    def validate(self, secret: str, *, fail_fast: bool = False) -> tuple[SecretStrength, list[str]]:
        """
        Validate secret and return strength and issues.

        Args:
            secret: Secret to validate
            fail_fast: If True, raise on first issue

        Returns:
            Tuple of (strength, list of issues)

        Raises:
            SecretValidationError: If fail_fast and validation fails
        """
        issues: list[str] = []

        if not secret:
            if fail_fast:
                raise SecretValidationError("Secret is empty")
            return SecretStrength.WEAK, ["Secret is empty"]

        # Check length
        if len(secret) < self._min_length:
            issues.append(f"Secret must be at least {self._min_length} characters (got {len(secret)})")

        # Check character requirements
        if self._require_uppercase and not any(c.isupper() for c in secret):
            issues.append("Secret must contain uppercase letters")

        if self._require_lowercase and not any(c.islower() for c in secret):
            issues.append("Secret must contain lowercase letters")

        if self._require_digits and not any(c.isdigit() for c in secret):
            issues.append("Secret must contain digits")

        if self._require_symbols and not any(c in string.punctuation for c in secret):
            issues.append("Secret must contain symbols")

        # Check forbidden patterns
        secret_lower = secret.lower()
        forbidden_found = [
            f"Secret contains forbidden pattern: '{pattern}'"
            for pattern in WEAK_PATTERNS + self._forbidden_patterns
            if pattern.lower() in secret_lower
        ]
        issues.extend(forbidden_found)

        if issues and fail_fast:
            raise SecretValidationError("; ".join(issues))

        if issues:
            return SecretStrength.WEAK, issues

        # Calculate strength
        entropy = _calculate_entropy(secret)
        if len(secret) >= 64 and entropy > 4.0:
            return SecretStrength.STRONG, []
        elif len(secret) >= 32 and entropy > 3.0:
            return SecretStrength.ACCEPTABLE, []
        else:
            return SecretStrength.WEAK, ["Secret has low entropy"]
