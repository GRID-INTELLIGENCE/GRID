"""
Secret Redaction Utilities.

Provides safe logging of secrets by masking sensitive values:
- Token redaction (dapi***xxxx format)
- URL secret masking
- Dictionary secret masking

Extracted from Mothership's _redact_token and mask_secret patterns.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def redact_token(token: str, visible_chars: int = 4) -> str:
    """
    Redact token for safe logging.

    Shows first and last N characters, masks the rest.

    Args:
        token: Token string to redact
        visible_chars: Number of characters to show at start/end

    Returns:
        Redacted token string

    Examples:
        >>> redact_token("dapi1234567890abcdef")
        'dapi***cdef'
        >>> redact_token("short")
        '***'
    """
    if not token:
        return "***"

    token = token.strip()

    # Too short to show partial
    if len(token) < visible_chars * 2:
        return "***"

    return f"{token[:visible_chars]}***{token[-visible_chars:]}"


def mask_secret(secret: str, visible_prefix: int = 4, visible_suffix: int = 4) -> str:
    """
    Mask secret for logging with configurable visibility.

    Args:
        secret: Secret string to mask
        visible_prefix: Characters to show at start
        visible_suffix: Characters to show at end

    Returns:
        Masked secret string

    Examples:
        >>> mask_secret("my-super-secret-key-12345")
        'my-s***2345'
    """
    if not secret:
        return "***"

    secret = secret.strip()

    min_length = visible_prefix + visible_suffix + 3  # +3 for "***"
    if len(secret) < min_length:
        return "***"

    return f"{secret[:visible_prefix]}***{secret[-visible_suffix:]}"


def mask_url_secrets(url: str, mask: str = "***") -> str:
    """
    Mask secrets in URL for logging.

    Handles:
    - Password in userinfo (user:pass@host)
    - Token in databricks URLs (token:xxx@host)
    - Query params with secret names

    Args:
        url: URL string to mask
        mask: Mask string to use

    Returns:
        URL with secrets masked

    Examples:
        >>> mask_url_secrets("postgresql://user:secret@localhost/db")
        'postgresql://user:***@localhost/db'
        >>> mask_url_secrets("https://api.example.com?key=secret123")
        'https://api.example.com?key=***'
    """
    if not url:
        return url

    url = url.strip()

    # Mask password in userinfo
    # Matches: ://user:password@ or ://token:password@
    pattern = r"(://[^:]+:)([^@]+)(@)"
    masked = re.sub(pattern, rf"\1{mask}\3", url)

    # Mask sensitive query parameters
    sensitive_params = {
        "key",
        "api_key",
        "apikey",
        "token",
        "access_token",
        "secret",
        "password",
        "credential",
        "auth",
    }

    # Pattern: ?param=value or &param=value
    for param in sensitive_params:
        # Match param=value, replace value with mask
        pattern = rf"([?&]{param}=)([^&]+)"
        masked = re.sub(pattern, rf"\1{mask}", masked, flags=re.IGNORECASE)

    return masked


def mask_dict_secrets(
    data: dict[str, Any],
    *,
    secret_keys: set[str] | None = None,
    mask: str = "***",
    recursive: bool = True,
) -> dict[str, Any]:
    """
    Mask secrets in dictionary for logging/serialization.

    Args:
        data: Dictionary to mask
        secret_keys: Set of key names to mask (default: common secret patterns)
        mask: Mask string to use
        recursive: If True, recursively mask nested dicts

    Returns:
        Dictionary with secrets masked

    Examples:
        >>> mask_dict_secrets({"api_key": "secret123", "name": "app"})
        {'api_key': '***', 'name': 'app'}
    """
    if secret_keys is None:
        secret_keys = {
            "secret",
            "key",
            "token",
            "password",
            "credential",
            "api_key",
            "apikey",
            "access_token",
            "auth",
            "private_key",
        }

    result: dict[str, Any] = {}

    for key, value in data.items():
        key_lower = key.lower()

        # Check if this key should be masked
        is_secret = any(pattern in key_lower for pattern in secret_keys)

        if is_secret and isinstance(value, str) and value:
            result[key] = mask

        elif recursive and isinstance(value, dict):
            result[key] = mask_dict_secrets(value, secret_keys=secret_keys, mask=mask, recursive=True)

        elif recursive and isinstance(value, list):
            result[key] = [
                mask_dict_secrets(item, secret_keys=secret_keys, mask=mask, recursive=True)
                if isinstance(item, dict)
                else item
                for item in value
            ]

        else:
            result[key] = value

    return result


def mask_connection_string(conn_str: str, mask: str = "***") -> str:
    """
    Mask secrets in database connection string.

    Handles various formats:
    - postgresql://user:pass@host/db
    - mysql://user:pass@host/db
    - mongodb://user:pass@host/db
    - redis://:pass@host
    - databricks://token:xxx@host

    Args:
        conn_str: Connection string to mask
        mask: Mask string to use

    Returns:
        Connection string with secrets masked
    """
    return mask_url_secrets(conn_str, mask)


class SecretMasker:
    """
    Configurable secret masker for consistent masking across application.

    Usage:
        masker = SecretMasker(
            secret_keys={"api_key", "token", "password"},
            visible_chars=4,
        )

        # Mask various types
        masked_token = masker.mask_token("dapi1234567890")
        masked_url = masker.mask_url("postgresql://user:secret@localhost/db")
        masked_dict = masker.mask_dict({"api_key": "secret", "name": "app"})
    """

    def __init__(
        self,
        *,
        secret_keys: set[str] | None = None,
        visible_chars: int = 4,
        mask: str = "***",
    ):
        """
        Initialize masker.

        Args:
            secret_keys: Set of key names to consider secrets
            visible_chars: Characters to show at start/end of secrets
            mask: Mask string to use
        """
        self._secret_keys = secret_keys or {
            "secret",
            "key",
            "token",
            "password",
            "credential",
            "api_key",
            "apikey",
            "access_token",
        }
        self._visible_chars = visible_chars
        self._mask = mask

    def mask_token(self, token: str) -> str:
        """Mask a token string."""
        return redact_token(token, self._visible_chars)

    def mask_secret(self, secret: str) -> str:
        """Mask a secret string."""
        return mask_secret(secret, self._visible_chars, self._visible_chars)

    def mask_url(self, url: str) -> str:
        """Mask secrets in URL."""
        return mask_url_secrets(url, self._mask)

    def mask_dict(self, data: dict[str, Any], *, recursive: bool = True) -> dict[str, Any]:
        """Mask secrets in dictionary."""
        return mask_dict_secrets(
            data,
            secret_keys=self._secret_keys,
            mask=self._mask,
            recursive=recursive,
        )

    def should_mask_key(self, key: str) -> bool:
        """Check if a key should be masked."""
        key_lower = key.lower()
        return any(pattern in key_lower for pattern in self._secret_keys)
