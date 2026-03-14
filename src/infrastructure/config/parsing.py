"""
Environment Variable Parsing Utilities.

Provides robust parsing for common environment variable types:
- Boolean (multiple formats: true/1/yes/on)
- Integer (with validation)
- Float (with validation)
- List (comma-separated)
- JSON (structured data)

Extracted from Mothership's _parse_bool and _parse_list patterns.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# Boolean truth values (case-insensitive)
TRUE_VALUES = {"true", "1", "yes", "y", "on", "enabled"}
FALSE_VALUES = {"false", "0", "no", "n", "off", "disabled", ""}


def parse_bool(value: str | None, default: bool = False) -> bool:
    """
    Parse boolean from environment variable string.

    Accepts multiple formats:
    - True: "true", "1", "yes", "y", "on", "enabled"
    - False: "false", "0", "no", "n", "off", "disabled", ""

    Args:
        value: String value to parse (typically from os.getenv)
        default: Default value if None or empty

    Returns:
        Parsed boolean value

    Examples:
        >>> parse_bool("true")
        True
        >>> parse_bool("0")
        False
        >>> parse_bool(None, default=True)
        True
    """
    if value is None:
        return default

    normalized = value.strip().lower()

    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False

    # Unknown value - log warning and return default
    logger.warning(f"Unknown boolean value '{value}', using default={default}")
    return default


def parse_int(
    value: str | None,
    default: int = 0,
    *,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int:
    """
    Parse integer from environment variable string with optional bounds.

    Args:
        value: String value to parse
        default: Default value if None or invalid
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)

    Returns:
        Parsed integer value

    Examples:
        >>> parse_int("42")
        42
        >>> parse_int("invalid", default=10)
        10
        >>> parse_int("5", min_value=1, max_value=10)
        5
        >>> parse_int("15", min_value=1, max_value=10)
        10  # Clamped to max
    """
    if value is None or not value.strip():
        return default

    try:
        result = int(value.strip())

        # Apply bounds
        if min_value is not None and result < min_value:
            logger.warning(f"Value {result} below minimum {min_value}, clamping")
            result = min_value
        if max_value is not None and result > max_value:
            logger.warning(f"Value {result} above maximum {max_value}, clamping")
            result = max_value

        return result

    except ValueError:
        logger.warning(f"Invalid integer value '{value}', using default={default}")
        return default


def parse_float(
    value: str | None,
    default: float = 0.0,
    *,
    min_value: float | None = None,
    max_value: float | None = None,
) -> float:
    """
    Parse float from environment variable string with optional bounds.

    Args:
        value: String value to parse
        default: Default value if None or invalid
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)

    Returns:
        Parsed float value

    Examples:
        >>> parse_float("3.14")
        3.14
        >>> parse_float("invalid", default=1.0)
        1.0
        >>> parse_float("0.5", min_value=0.0, max_value=1.0)
        0.5
    """
    if value is None or not value.strip():
        return default

    try:
        result = float(value.strip())

        # Apply bounds
        if min_value is not None and result < min_value:
            logger.warning(f"Value {result} below minimum {min_value}, clamping")
            result = min_value
        if max_value is not None and result > max_value:
            logger.warning(f"Value {result} above maximum {max_value}, clamping")
            result = max_value

        return result

    except ValueError:
        logger.warning(f"Invalid float value '{value}', using default={default}")
        return default


def parse_list(value: str | None, separator: str = ",", strip: bool = True) -> list[str]:
    """
    Parse comma-separated list from environment variable.

    Args:
        value: String value to parse
        separator: Separator character (default: comma)
        strip: Whether to strip whitespace from items

    Returns:
        List of string items (empty list if value is None/empty)

    Examples:
        >>> parse_list("a,b,c")
        ['a', 'b', 'c']
        >>> parse_list("  a , b , c  ")
        ['a', 'b', 'c']
        >>> parse_list(None)
        []
        >>> parse_list("a|b|c", separator="|")
        ['a', 'b', 'c']
    """
    if not value or not value.strip():
        return []

    items = value.split(separator)

    if strip:
        items = [item.strip() for item in items]

    # Filter empty strings
    return [item for item in items if item]


def parse_json(value: str | None, default: Any = None) -> Any:
    """
    Parse JSON from environment variable string.

    Args:
        value: String value to parse
        default: Default value if None or invalid

    Returns:
        Parsed JSON value (dict, list, or primitive)

    Examples:
        >>> parse_json('{"key": "value"}')
        {'key': 'value'}
        >>> parse_json('[1, 2, 3]')
        [1, 2, 3]
        >>> parse_json(None, default={})
        {}
    """
    if value is None or not value.strip():
        return default

    try:
        return json.loads(value.strip())
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON value '{value}': {e}, using default")
        return default


def parse_url(value: str | None, default: str = "", require_scheme: bool = False) -> str:
    """
    Parse URL from environment variable with optional validation.

    Args:
        value: String value to parse
        default: Default value if None or empty
        require_scheme: If True, require http:// or https:// scheme

    Returns:
        URL string (stripped of whitespace)

    Examples:
        >>> parse_url("  https://example.com  ")
        'https://example.com'
        >>> parse_url(None, default="http://localhost")
        'http://localhost'
    """
    if value is None or not value.strip():
        return default

    url = value.strip()

    if require_scheme and not url.startswith(("http://", "https://")):
        logger.warning(f"URL '{url}' missing required scheme, using default")
        return default

    return url


def parse_path(value: str | None, default: str = "", must_exist: bool = False) -> str:
    """
    Parse file path from environment variable with optional validation.

    Args:
        value: String value to parse
        default: Default value if None or empty
        must_exist: If True, validate path exists

    Returns:
        Path string (stripped of whitespace)

    Examples:
        >>> parse_path("/home/user/config")
        '/home/user/config'
        >>> parse_path(None, default="./config")
        './config'
    """
    from pathlib import Path

    if value is None or not value.strip():
        return default

    path_str = value.strip()

    if must_exist:
        try:
            if not Path(path_str).expanduser().exists():
                logger.warning(f"Path '{path_str}' does not exist, using default")
                return default
        except (OSError, ValueError):
            logger.warning(f"Path '{path_str}' is invalid, using default")
            return default

    return path_str


class EnvParser:
    """
    Convenience class for parsing environment variables with a prefix.

    Usage:
        parser = EnvParser("MOTHERSHIP_")
        port = parser.int("PORT", default=8080)
        debug = parser.bool("DEBUG", default=False)
        origins = parser.list("CORS_ORIGINS")
    """

    def __init__(self, prefix: str = "", env: dict[str, str] | None = None):
        """
        Initialize parser with optional prefix.

        Args:
            prefix: Prefix to prepend to variable names
            env: Environment dict (defaults to os.environ)
        """
        self._prefix = prefix
        self._env = env if env is not None else os.environ

    def _get(self, name: str) -> str | None:
        """Get environment variable with prefix applied."""
        full_name = f"{self._prefix}{name}" if self._prefix else name
        return self._env.get(full_name)

    def bool(self, name: str, default: bool = False) -> bool:
        """Parse boolean environment variable."""
        return parse_bool(self._get(name), default)

    def int(
        self,
        name: str,
        default: int = 0,
        *,
        min_value: int | None = None,
        max_value: int | None = None,
    ) -> int:
        """Parse integer environment variable."""
        return parse_int(self._get(name), default, min_value=min_value, max_value=max_value)

    def float(
        self,
        name: str,
        default: float = 0.0,
        *,
        min_value: float | None = None,
        max_value: float | None = None,
    ) -> float:
        """Parse float environment variable."""
        return parse_float(self._get(name), default, min_value=min_value, max_value=max_value)

    def list(self, name: str, separator: str = ",") -> list[str]:
        """Parse list environment variable."""
        return parse_list(self._get(name), separator)

    def json(self, name: str, default: Any = None) -> Any:
        """Parse JSON environment variable."""
        return parse_json(self._get(name), default)

    def str(self, name: str, default: str = "") -> str:
        """Get string environment variable."""
        value = self._get(name)
        return value.strip() if value else default

    def url(self, name: str, default: str = "", require_scheme: bool = False) -> str:
        """Parse URL environment variable."""
        return parse_url(self._get(name), default, require_scheme)

    def path(self, name: str, default: str = "", must_exist: bool = False) -> str:
        """Parse path environment variable."""
        return parse_path(self._get(name), default, must_exist)
