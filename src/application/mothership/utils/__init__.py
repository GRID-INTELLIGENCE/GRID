"""
Mothership Cockpit Utilities Package.

Common utility functions and validators for the Mothership Cockpit
application including data validation, formatting, and helper functions.
"""

from __future__ import annotations

import hashlib
import re
import secrets
import string
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timezone
from typing import Any

# =============================================================================
# DateTime Utilities
# =============================================================================


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(UTC)


def utc_timestamp() -> float:
    """Get current UTC timestamp in seconds."""
    return utc_now().timestamp()


def utc_timestamp_ms() -> int:
    """Get current UTC timestamp in milliseconds."""
    return int(utc_now().timestamp() * 1000)


def parse_datetime(value: str | datetime | None) -> datetime | None:
    """
    Parse a datetime from string or return as-is if already datetime.

    Supports ISO 8601 format strings.

    Args:
        value: String, datetime, or None

    Returns:
        Parsed datetime or None
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        # Try ISO format first
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def format_datetime(dt: datetime | None, fmt: str = "iso") -> str | None:
    """
    Format datetime to string.

    Args:
        dt: Datetime to format
        fmt: Format type ('iso', 'human', 'compact')

    Returns:
        Formatted string or None
    """
    if dt is None:
        return None

    if fmt == "iso":
        return dt.isoformat()
    elif fmt == "human":
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    elif fmt == "compact":
        return dt.strftime("%Y%m%d%H%M%S")
    return dt.isoformat()


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Human-readable duration string
    """
    if seconds < 0:
        return "0s"

    days, remainder = divmod(int(seconds), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")

    return " ".join(parts)


def time_ago(dt: datetime) -> str:
    """
    Get human-readable time ago string.

    Args:
        dt: Datetime to compare against now

    Returns:
        Human-readable "time ago" string
    """
    now = utc_now()
    diff = now - dt

    seconds = diff.total_seconds()
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"


# =============================================================================
# ID Generation
# =============================================================================


def generate_id(prefix: str = "", length: int = 12) -> str:
    """
    Generate a unique identifier with optional prefix.

    Args:
        prefix: Optional prefix for the ID
        length: Length of the random part (default 12)

    Returns:
        Unique identifier string
    """
    random_part = uuid.uuid4().hex[:length]
    return f"{prefix}_{random_part}" if prefix else random_part


def generate_uuid() -> str:
    """Generate a full UUID4 string."""
    return str(uuid.uuid4())


def generate_short_id(length: int = 8) -> str:
    """
    Generate a short alphanumeric ID.

    Args:
        length: Length of the ID

    Returns:
        Short alphanumeric string
    """
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_token(length: int = 32) -> str:
    """
    Generate a secure random token.

    Args:
        length: Length of the token in bytes

    Returns:
        Hex-encoded token string
    """
    return secrets.token_hex(length)


def generate_api_key() -> str:
    """
    Generate an API key in standard format.

    Returns:
        API key in format: 'mk_xxxx_xxxx_xxxx_xxxx'
    """
    parts = [secrets.token_hex(4) for _ in range(4)]
    return f"mk_{parts[0]}_{parts[1]}_{parts[2]}_{parts[3]}"


# =============================================================================
# String Utilities
# =============================================================================


def slugify(text: str, separator: str = "-") -> str:
    """
    Convert text to URL-friendly slug.

    Args:
        text: Text to slugify
        separator: Separator character (default '-')

    Returns:
        Slugified string
    """
    # Convert to lowercase
    text = text.lower()
    # Replace spaces and underscores with separator
    text = re.sub(r"[\s_]+", separator, text)
    # Remove non-alphanumeric characters (except separator)
    text = re.sub(rf"[^a-z0-9{re.escape(separator)}]", "", text)
    # Remove duplicate separators
    text = re.sub(rf"{re.escape(separator)}+", separator, text)
    # Strip separators from ends
    return text.strip(separator)


def truncate(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length with suffix.

    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add when truncated

    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def mask_sensitive(value: str, visible_chars: int = 4) -> str:
    """
    Mask sensitive string showing only first few characters.

    Args:
        value: String to mask
        visible_chars: Number of characters to show

    Returns:
        Masked string
    """
    if not value:
        return ""
    if len(value) <= visible_chars:
        return "*" * len(value)
    return value[:visible_chars] + "*" * (len(value) - visible_chars)


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize a string by removing control characters and limiting length.

    Args:
        value: String to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string
    """
    # Remove control characters except newlines and tabs
    sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", value)
    # Limit length
    return sanitized[:max_length]


# =============================================================================
# Validators
# =============================================================================


class ValidationError(ValueError):
    """Validation error with field information."""

    def __init__(self, message: str, field: str | None = None):
        self.message = message
        self.field = field
        super().__init__(message)


def validate_email(email: str) -> bool:
    """
    Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        True if valid
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_uuid(value: str) -> bool:
    """
    Validate UUID format.

    Args:
        value: String to validate

    Returns:
        True if valid UUID
    """
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


def validate_url(url: str, require_https: bool = False) -> bool:
    """
    Validate URL format.

    Args:
        url: URL to validate
        require_https: Require HTTPS scheme

    Returns:
        True if valid
    """
    pattern = r"^https?://" if not require_https else r"^https://"
    pattern += r"[a-zA-Z0-9][-a-zA-Z0-9]*(\.[a-zA-Z0-9][-a-zA-Z0-9]*)+(/.*)?$"
    return bool(re.match(pattern, url))


def validate_ip_address(ip: str) -> bool:
    """
    Validate IPv4 or IPv6 address.

    Args:
        ip: IP address to validate

    Returns:
        True if valid
    """
    # IPv4
    ipv4_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
    if re.match(ipv4_pattern, ip):
        parts = ip.split(".")
        return all(0 <= int(p) <= 255 for p in parts)

    # IPv6 (simplified)
    ipv6_pattern = r"^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$"
    return bool(re.match(ipv6_pattern, ip))


def validate_identifier(
    value: str,
    min_length: int = 1,
    max_length: int = 64,
    allow_dots: bool = False,
) -> bool:
    """
    Validate an identifier (alphanumeric with underscores/dashes).

    Args:
        value: Value to validate
        min_length: Minimum length
        max_length: Maximum length
        allow_dots: Allow dots in identifier

    Returns:
        True if valid
    """
    if not value or len(value) < min_length or len(value) > max_length:
        return False

    pattern = r"^[a-zA-Z][a-zA-Z0-9_-]*$"
    if allow_dots:
        pattern = r"^[a-zA-Z][a-zA-Z0-9_.-]*$"

    return bool(re.match(pattern, value))


def validate_semver(version: str) -> bool:
    """
    Validate semantic version string.

    Args:
        version: Version string to validate

    Returns:
        True if valid semver
    """
    pattern = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(-[a-zA-Z0-9-]+)?(\+[a-zA-Z0-9-]+)?$"
    return bool(re.match(pattern, version))


# =============================================================================
# Data Utilities
# =============================================================================


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """
    Deep merge two dictionaries.

    Args:
        base: Base dictionary
        override: Dictionary with values to override

    Returns:
        Merged dictionary
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def flatten_dict(
    data: dict[str, Any],
    separator: str = ".",
    prefix: str = "",
) -> dict[str, Any]:
    """
    Flatten a nested dictionary.

    Args:
        data: Dictionary to flatten
        separator: Key separator
        prefix: Key prefix

    Returns:
        Flattened dictionary
    """
    items: dict[str, Any] = {}
    for key, value in data.items():
        new_key = f"{prefix}{separator}{key}" if prefix else key
        if isinstance(value, dict):
            items.update(flatten_dict(value, separator, new_key))
        else:
            items[new_key] = value
    return items


def safe_get(data: dict[str, Any], path: str, default: Any = None) -> Any:
    """
    Safely get a nested value from a dictionary.

    Args:
        data: Dictionary to search
        path: Dot-separated path to value
        default: Default value if not found

    Returns:
        Value at path or default
    """
    keys = path.split(".")
    result = data
    for key in keys:
        if isinstance(result, dict) and key in result:
            result = result[key]
        else:
            return default
    return result


def chunk_list[T](items: list[T], chunk_size: int) -> list[list[T]]:
    """
    Split a list into chunks of specified size.

    Args:
        items: List to chunk
        chunk_size: Size of each chunk

    Returns:
        List of chunks
    """
    return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]


def deduplicate[T](items: list[T], key: Callable[[T], Any] | None = None) -> list[T]:
    """
    Remove duplicates from a list while preserving order.

    Args:
        items: List to deduplicate
        key: Optional key function for comparison

    Returns:
        Deduplicated list
    """
    seen = set()
    result = []
    for item in items:
        k = key(item) if key else item
        if k not in seen:
            seen.add(k)
            result.append(item)
    return result


# =============================================================================
# Hash Utilities
# =============================================================================


def hash_string(value: str, algorithm: str = "sha256") -> str:
    """
    Hash a string using specified algorithm.

    Args:
        value: String to hash
        algorithm: Hash algorithm (sha256, sha512, md5)

    Returns:
        Hex-encoded hash
    """
    hasher = hashlib.new(algorithm)
    hasher.update(value.encode("utf-8"))
    return hasher.hexdigest()


def hash_dict(data: dict[str, Any]) -> str:
    """
    Create a hash of a dictionary for comparison.

    Args:
        data: Dictionary to hash

    Returns:
        Hex-encoded hash
    """
    import json

    serialized = json.dumps(data, sort_keys=True, default=str)
    return hash_string(serialized)


# =============================================================================
# Ghost Configuration & Resonance Traps
# =============================================================================


def ghost_config_trap(component_name: str, accessed_key: str) -> str:
    """
    Identifies and handles access to decommissioned/ghost configurations.
    Implements a hyper-terminal garbage transfer (log dump) for diagnostic tracking.

    Args:
        component_name: Name of the decommissioned component (e.g., 'bkash')
        accessed_key: The configuration key that was accessed

    Returns:
        A terminal garbage signature to identify the leak
    """
    import inspect
    import logging

    logger = logging.getLogger("mothership.ghost_trap")

    # Analyze caller context for pattern analysis
    frame = inspect.currentframe().f_back
    caller_info = {
        "function": frame.f_code.co_name if frame else "unknown",
        "filename": frame.f_code.co_filename if frame else "unknown",
        "lineno": frame.f_lineno if frame else 0,
    }

    # Generate hyper-terminal garbage signature
    trap_payload = f"{component_name}://{accessed_key}@{caller_info['filename']}:{caller_info['lineno']}"
    garbage_sig = hashlib.sha256(trap_payload.encode()).hexdigest()[:24]

    # INTELLIGENT IDENTIFICATION: Log the divergence pattern
    logger.critical(
        f"RESONANCE_DIVERGENCE_TRAP: {garbage_sig} | "
        f"DISAPPEARING_CONFIG_ACCESSED: [{component_name}.{accessed_key}] | "
        f"SOURCE: {caller_info['filename']}:{caller_info['lineno']} | "
        f"ACTION: Grounding execution to hyper-terminal garbage transfer."
    )

    # HYPER-TERMINAL GARBAGE TRANSFER:
    # Emit a high-density, non-destructive but overwhelming diagnostic blob
    # to identify the source of the ghost access in terminal/logs.
    garbage_blob = "\n".join(
        [
            f"!!! GHOST_RESONANCE_DIVERGENCE_DETECTED [{garbage_sig}] !!!",
            "TRAP_PAYLOAD_MAP: " + hashlib.sha256(trap_payload.encode()).hexdigest(),
            "MEM_RESONANCE_STATE: HIGH_TENSION_LOCKED",
            "REASONING: Unauthorized access to decommissioned configuration context.",
            "DIVERGENCE_INDEX: " + (secrets.token_hex(32) + secrets.token_hex(32)),
            "!!!" * 20,
        ]
    )
    print(garbage_blob)

    return f"ERR_GHOST_CONFIG_RESONANCE_DIVERGENCE_{garbage_sig.upper()}"


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # DateTime
    "utc_now",
    "utc_timestamp",
    "utc_timestamp_ms",
    "parse_datetime",
    "format_datetime",
    "format_duration",
    "time_ago",
    # ID Generation
    "generate_id",
    "generate_uuid",
    "generate_short_id",
    "generate_token",
    "generate_api_key",
    # String Utilities
    "slugify",
    "truncate",
    "mask_sensitive",
    "sanitize_string",
    # Validators
    "ValidationError",
    "validate_email",
    "validate_uuid",
    "validate_url",
    "validate_ip_address",
    "validate_identifier",
    "validate_semver",
    # Data Utilities
    "deep_merge",
    "flatten_dict",
    "safe_get",
    "chunk_list",
    "deduplicate",
    # Hash Utilities
    "hash_string",
    "hash_dict",
    # Ghost Traps
    "ghost_config_trap",
    # CPU Executor
    "run_cpu_bound",
    "run_blocking_io",
    "shutdown_executor",
]

# Import CPU executor functions
from .cpu_executor import run_blocking_io, run_cpu_bound, shutdown_executor


def seed_resonance_traps() -> None:
    """
    Seeds resonance traps across the system environment to identify
    leaks of disappearing configurations.
    """
    import os

    ghost_keys = ["BKASH_APP_KEY", "BKASH_APP_SECRET", "BKASH_ENABLED", "BKASH_USERNAME", "BKASH_PASSWORD"]
    for key in ghost_keys:
        if os.environ.get(key):
            ghost_config_trap("env_leak", key)


# Auto-seed traps on utilities import to identify patterns immediately
seed_resonance_traps()
