"""
Input Sanitization Module for GRID Security Stack.

Provides multi-layer input sanitization with XSS, injection, and
path traversal protection. Implements defense-in-depth approach
for securing all input sources in the GRID event-driven architecture.

Features:
- HTML entity encoding for XSS prevention
- Code injection pattern detection and removal
- SQL injection pattern blocking
- Command injection protection
- Path traversal prevention
- JSON structure validation with depth limits
- Length limits and truncation
- Configurable severity levels

Security Standards:
- OWASP Top 10 compliance
- Input validation best practices
- Defense in depth approach

Example:
    >>> from grid.security.input_sanitizer import InputSanitizer
    >>> sanitizer = InputSanitizer()
    >>> safe_text = sanitizer.sanitize_text("<script>alert('xss')</script>")
    >>> print(safe_text)
    &lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;
"""

from __future__ import annotations

import html
import logging
import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ThreatSeverity(str, Enum):
    """Severity levels for detected threats."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(str, Enum):
    """Types of security threats."""

    XSS = "xss"
    SQL_INJECTION = "sql_injection"
    COMMAND_INJECTION = "command_injection"
    CODE_INJECTION = "code_injection"
    PATH_TRAVERSAL = "path_traversal"
    OVERSIZED_INPUT = "oversized_input"
    DEEP_NESTING = "deep_nesting"
    INVALID_ENCODING = "invalid_encoding"
    SUSPICIOUS_PATTERN = "suspicious_pattern"


@dataclass
class SanitizationResult:
    """Result of input sanitization."""

    original_length: int
    sanitized_length: int
    sanitized_content: str | dict[str, Any] | list[Any]
    threats_detected: list[dict[str, Any]] = field(default_factory=list)
    modifications_made: list[str] = field(default_factory=list)
    severity: ThreatSeverity = ThreatSeverity.NONE
    is_safe: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "original_length": self.original_length,
            "sanitized_length": self.sanitized_length,
            "threats_detected": self.threats_detected,
            "modifications_made": self.modifications_made,
            "severity": self.severity.value,
            "is_safe": self.is_safe,
        }


@dataclass
class SanitizationConfig:
    """Configuration for input sanitization."""

    # Length limits
    max_text_length: int = 100000
    max_json_depth: int = 10
    max_dict_keys: int = 100
    max_list_items: int = 1000

    # Feature flags
    encode_html: bool = True
    remove_scripts: bool = True
    block_sql_injection: bool = True
    block_command_injection: bool = True
    block_code_injection: bool = True
    block_path_traversal: bool = True
    normalize_unicode: bool = True

    # Behavior
    truncate_oversized: bool = True
    log_threats: bool = True
    strict_mode: bool = False  # If True, reject any suspicious input


class InputSanitizer:
    """
    Multi-layer input sanitization with threat detection.

    Provides comprehensive protection against common attack vectors
    including XSS, SQL injection, command injection, and path traversal.

    Attributes:
        config: Sanitization configuration
        threat_patterns: Compiled threat detection patterns
    """

    # Dangerous patterns to detect and remove
    DANGEROUS_PATTERNS: list[tuple[str, ThreatType, ThreatSeverity]] = [
        # XSS patterns
        (r"<script[^>]*>.*?</script>", ThreatType.XSS, ThreatSeverity.CRITICAL),
        (r"<script[^>]*>", ThreatType.XSS, ThreatSeverity.CRITICAL),
        (r"javascript\s*:", ThreatType.XSS, ThreatSeverity.HIGH),
        (r"vbscript\s*:", ThreatType.XSS, ThreatSeverity.HIGH),
        (r"data\s*:\s*text/html", ThreatType.XSS, ThreatSeverity.HIGH),
        (r"on\w+\s*=", ThreatType.XSS, ThreatSeverity.HIGH),
        (r"<iframe[^>]*>", ThreatType.XSS, ThreatSeverity.HIGH),
        (r"<object[^>]*>", ThreatType.XSS, ThreatSeverity.MEDIUM),
        (r"<embed[^>]*>", ThreatType.XSS, ThreatSeverity.MEDIUM),
        (r"<link[^>]*>", ThreatType.XSS, ThreatSeverity.LOW),
        (r"<meta[^>]*http-equiv", ThreatType.XSS, ThreatSeverity.MEDIUM),
        # SQL injection patterns
        (r"\b(union\s+select|union\s+all\s+select)\b", ThreatType.SQL_INJECTION, ThreatSeverity.CRITICAL),
        (r"\b(select\s+.*\s+from\s+.*\s+where)\b", ThreatType.SQL_INJECTION, ThreatSeverity.HIGH),
        (r"\b(insert\s+into|update\s+.*\s+set|delete\s+from)\b", ThreatType.SQL_INJECTION, ThreatSeverity.HIGH),
        (r"\b(drop\s+table|drop\s+database|truncate\s+table)\b", ThreatType.SQL_INJECTION, ThreatSeverity.CRITICAL),
        (r"\b(alter\s+table|create\s+table)\b", ThreatType.SQL_INJECTION, ThreatSeverity.HIGH),
        (r"('\s*or\s+'?\d+'?\s*=\s*'?\d+'?)", ThreatType.SQL_INJECTION, ThreatSeverity.HIGH),
        (r"(--\s*$|;\s*--)", ThreatType.SQL_INJECTION, ThreatSeverity.MEDIUM),
        (r"\b(exec\s*\(|execute\s*\()\b", ThreatType.SQL_INJECTION, ThreatSeverity.HIGH),
        (r"\b(xp_cmdshell|sp_executesql)\b", ThreatType.SQL_INJECTION, ThreatSeverity.CRITICAL),
        # Command injection patterns
        (r";\s*(rm|del|format|fdisk|mkfs)\s", ThreatType.COMMAND_INJECTION, ThreatSeverity.CRITICAL),
        (r"\|\s*(nc|netcat|telnet|ssh|bash|sh|cmd)\s", ThreatType.COMMAND_INJECTION, ThreatSeverity.CRITICAL),
        (r"&&\s*(wget|curl|fetch|powershell)\s", ThreatType.COMMAND_INJECTION, ThreatSeverity.HIGH),
        (r"\$\([^)]+\)", ThreatType.COMMAND_INJECTION, ThreatSeverity.MEDIUM),
        (r"`[^`]+`", ThreatType.COMMAND_INJECTION, ThreatSeverity.MEDIUM),
        (r">\s*/dev/null", ThreatType.COMMAND_INJECTION, ThreatSeverity.LOW),
        (r">\s*&\d", ThreatType.COMMAND_INJECTION, ThreatSeverity.MEDIUM),
        # Python code injection patterns
        (r"\beval\s*\(", ThreatType.CODE_INJECTION, ThreatSeverity.CRITICAL),
        (r"\bexec\s*\(", ThreatType.CODE_INJECTION, ThreatSeverity.CRITICAL),
        (r"\bcompile\s*\(", ThreatType.CODE_INJECTION, ThreatSeverity.HIGH),
        (r"\b__import__\s*\(", ThreatType.CODE_INJECTION, ThreatSeverity.CRITICAL),
        (r"\bgetattr\s*\(", ThreatType.CODE_INJECTION, ThreatSeverity.MEDIUM),
        (r"\bsetattr\s*\(", ThreatType.CODE_INJECTION, ThreatSeverity.MEDIUM),
        (r"\bdelattr\s*\(", ThreatType.CODE_INJECTION, ThreatSeverity.MEDIUM),
        (r"\bglobals\s*\(\s*\)", ThreatType.CODE_INJECTION, ThreatSeverity.HIGH),
        (r"\blocals\s*\(\s*\)", ThreatType.CODE_INJECTION, ThreatSeverity.MEDIUM),
        (r"\bvars\s*\(\s*\)", ThreatType.CODE_INJECTION, ThreatSeverity.MEDIUM),
        (r'\bopen\s*\([^)]*,\s*["\']w', ThreatType.CODE_INJECTION, ThreatSeverity.HIGH),
        (r"\bos\.system\s*\(", ThreatType.CODE_INJECTION, ThreatSeverity.CRITICAL),
        (r"\bsubprocess\s*\.", ThreatType.CODE_INJECTION, ThreatSeverity.CRITICAL),
        (r"\bimport\s+os\b", ThreatType.CODE_INJECTION, ThreatSeverity.MEDIUM),
        (r"\bimport\s+subprocess\b", ThreatType.CODE_INJECTION, ThreatSeverity.HIGH),
        (r"\bimport\s+pickle\b", ThreatType.CODE_INJECTION, ThreatSeverity.HIGH),
        # Path traversal patterns
        (r"\.\./", ThreatType.PATH_TRAVERSAL, ThreatSeverity.HIGH),
        (r"\.\.\\", ThreatType.PATH_TRAVERSAL, ThreatSeverity.HIGH),
        (r"%2e%2e%2f", ThreatType.PATH_TRAVERSAL, ThreatSeverity.HIGH),
        (r"%2e%2e%5c", ThreatType.PATH_TRAVERSAL, ThreatSeverity.HIGH),
        (r"%252e%252e%252f", ThreatType.PATH_TRAVERSAL, ThreatSeverity.HIGH),
        (r"/etc/passwd", ThreatType.PATH_TRAVERSAL, ThreatSeverity.HIGH),
        (r"/etc/shadow", ThreatType.PATH_TRAVERSAL, ThreatSeverity.CRITICAL),
        (r"c:\\windows\\system32", ThreatType.PATH_TRAVERSAL, ThreatSeverity.HIGH),
    ]

    # Characters that are always safe
    SAFE_CHARS: set[str] = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?-_")

    def __init__(self, config: SanitizationConfig | None = None) -> None:
        """
        Initialize input sanitizer.

        Args:
            config: Sanitization configuration
        """
        self.config = config or SanitizationConfig()
        self._compiled_patterns: list[tuple[re.Pattern, ThreatType, ThreatSeverity]] = []
        self._compile_patterns()

        logger.debug("InputSanitizer initialized with config: %s", self.config)

    def _compile_patterns(self) -> None:
        """Compile regex patterns for efficient matching."""
        for pattern, threat_type, severity in self.DANGEROUS_PATTERNS:
            try:
                compiled = re.compile(pattern, re.IGNORECASE | re.DOTALL)
                self._compiled_patterns.append((compiled, threat_type, severity))
            except re.error as e:
                logger.error("Failed to compile pattern '%s': %s", pattern, e)

    def sanitize_text(self, text: str) -> str:
        """
        Sanitize text input with full protection.

        Args:
            text: Input text to sanitize

        Returns:
            Sanitized text
        """
        result = self.sanitize_text_full(text)
        return str(result.sanitized_content)

    def sanitize_text_full(self, text: str) -> SanitizationResult:
        """
        Sanitize text input with detailed result.

        Args:
            text: Input text to sanitize

        Returns:
            SanitizationResult with details
        """
        if not isinstance(text, str):
            text = str(text)

        original_length = len(text)
        threats: list[dict[str, Any]] = []
        modifications: list[str] = []
        max_severity = ThreatSeverity.NONE

        # Step 1: Normalize unicode
        if self.config.normalize_unicode:
            normalized = unicodedata.normalize("NFC", text)
            if normalized != text:
                modifications.append("unicode_normalized")
                text = normalized

        # Step 2: Check and enforce length limits
        if len(text) > self.config.max_text_length:
            threats.append(
                {
                    "type": ThreatType.OVERSIZED_INPUT.value,
                    "severity": ThreatSeverity.MEDIUM.value,
                    "details": f"Input length {len(text)} exceeds limit {self.config.max_text_length}",
                }
            )
            max_severity = max(max_severity, ThreatSeverity.MEDIUM, key=lambda x: list(ThreatSeverity).index(x))

            if self.config.truncate_oversized:
                text = text[: self.config.max_text_length] + "... [truncated]"
                modifications.append("truncated")

        # Step 3: Detect dangerous patterns
        for compiled_pattern, threat_type, severity in self._compiled_patterns:
            # Check if this pattern type should be blocked
            should_check = (
                (threat_type == ThreatType.XSS and self.config.remove_scripts)
                or (threat_type == ThreatType.SQL_INJECTION and self.config.block_sql_injection)
                or (threat_type == ThreatType.COMMAND_INJECTION and self.config.block_command_injection)
                or (threat_type == ThreatType.CODE_INJECTION and self.config.block_code_injection)
                or (threat_type == ThreatType.PATH_TRAVERSAL and self.config.block_path_traversal)
            )

            if not should_check:
                continue

            matches = compiled_pattern.findall(text)
            if matches:
                threats.append(
                    {
                        "type": threat_type.value,
                        "severity": severity.value,
                        "matches": matches[:5],  # Limit logged matches
                        "match_count": len(matches),
                    }
                )
                max_severity = max(max_severity, severity, key=lambda x: list(ThreatSeverity).index(x))

                # Remove dangerous patterns
                text = compiled_pattern.sub("", text)
                modifications.append(f"removed_{threat_type.value}")

        # Step 4: HTML entity encoding
        if self.config.encode_html:
            encoded = html.escape(text, quote=True)
            if encoded != text:
                modifications.append("html_encoded")
                text = encoded

        # Log threats if configured
        if threats and self.config.log_threats:
            logger.warning(
                "Threats detected in input: %d threats, max severity: %s",
                len(threats),
                max_severity.value,
            )

        # Determine if input is safe
        is_safe = max_severity in [ThreatSeverity.NONE, ThreatSeverity.LOW]
        if self.config.strict_mode:
            is_safe = max_severity == ThreatSeverity.NONE and not modifications

        return SanitizationResult(
            original_length=original_length,
            sanitized_length=len(text),
            sanitized_content=text,
            threats_detected=threats,
            modifications_made=modifications,
            severity=max_severity,
            is_safe=is_safe,
        )

    def sanitize_json(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Sanitize JSON/dictionary input.

        Args:
            data: Dictionary to sanitize

        Returns:
            Sanitized dictionary
        """
        result = self.sanitize_json_full(data)
        return result.sanitized_content  # type: ignore

    def sanitize_json_full(self, data: dict[str, Any]) -> SanitizationResult:
        """
        Sanitize JSON/dictionary input with detailed result.

        Args:
            data: Dictionary to sanitize

        Returns:
            SanitizationResult with details
        """
        if not isinstance(data, dict):
            raise ValueError("Input must be a dictionary")

        threats: list[dict[str, Any]] = []
        modifications: list[str] = []
        max_severity = ThreatSeverity.NONE

        # Validate and sanitize structure
        try:
            sanitized, structure_threats, structure_mods = self._sanitize_structure(
                data,
                current_depth=0,
            )
            threats.extend(structure_threats)
            modifications.extend(structure_mods)

            # Update max severity
            for threat in structure_threats:
                threat_severity = ThreatSeverity(threat.get("severity", "none"))
                max_severity = max(max_severity, threat_severity, key=lambda x: list(ThreatSeverity).index(x))

        except RecursionError:
            threats.append(
                {
                    "type": ThreatType.DEEP_NESTING.value,
                    "severity": ThreatSeverity.HIGH.value,
                    "details": "Input structure too deeply nested",
                }
            )
            max_severity = ThreatSeverity.HIGH
            sanitized = {"error": "Input too complex"}

        is_safe = max_severity in [ThreatSeverity.NONE, ThreatSeverity.LOW]
        if self.config.strict_mode:
            is_safe = max_severity == ThreatSeverity.NONE

        return SanitizationResult(
            original_length=len(str(data)),
            sanitized_length=len(str(sanitized)),
            sanitized_content=sanitized,
            threats_detected=threats,
            modifications_made=modifications,
            severity=max_severity,
            is_safe=is_safe,
        )

    def _sanitize_structure(
        self,
        obj: Any,
        current_depth: int,
    ) -> tuple[Any, list[dict[str, Any]], list[str]]:
        """
        Recursively sanitize data structure.

        Args:
            obj: Object to sanitize
            current_depth: Current nesting depth

        Returns:
            Tuple of (sanitized object, threats, modifications)
        """
        threats: list[dict[str, Any]] = []
        modifications: list[str] = []

        # Check depth
        if current_depth >= self.config.max_json_depth:
            threats.append(
                {
                    "type": ThreatType.DEEP_NESTING.value,
                    "severity": ThreatSeverity.MEDIUM.value,
                    "details": f"Depth {current_depth} exceeds limit {self.config.max_json_depth}",
                }
            )
            modifications.append("depth_truncated")
            return str(obj)[:100], threats, modifications

        if isinstance(obj, dict):
            # Check key count
            if len(obj) > self.config.max_dict_keys:
                threats.append(
                    {
                        "type": ThreatType.OVERSIZED_INPUT.value,
                        "severity": ThreatSeverity.LOW.value,
                        "details": f"Dict has {len(obj)} keys, limiting to {self.config.max_dict_keys}",
                    }
                )
                modifications.append("keys_limited")
                obj = dict(list(obj.items())[: self.config.max_dict_keys])

            sanitized_dict = {}
            for key, value in obj.items():
                # Sanitize key
                if isinstance(key, str):
                    key_result = self.sanitize_text_full(key)
                    if key_result.threats_detected:
                        threats.extend(key_result.threats_detected)
                        modifications.extend(key_result.modifications_made)
                    key = str(key_result.sanitized_content)

                # Sanitize value recursively
                sanitized_value, value_threats, value_mods = self._sanitize_structure(
                    value,
                    current_depth + 1,
                )
                threats.extend(value_threats)
                modifications.extend(value_mods)

                sanitized_dict[key] = sanitized_value

            return sanitized_dict, threats, modifications

        elif isinstance(obj, list):
            # Check list size
            if len(obj) > self.config.max_list_items:
                threats.append(
                    {
                        "type": ThreatType.OVERSIZED_INPUT.value,
                        "severity": ThreatSeverity.LOW.value,
                        "details": f"List has {len(obj)} items, limiting to {self.config.max_list_items}",
                    }
                )
                modifications.append("list_limited")
                obj = obj[: self.config.max_list_items]

            sanitized_list = []
            for item in obj:
                sanitized_item, item_threats, item_mods = self._sanitize_structure(
                    item,
                    current_depth + 1,
                )
                threats.extend(item_threats)
                modifications.extend(item_mods)
                sanitized_list.append(sanitized_item)

            return sanitized_list, threats, modifications

        elif isinstance(obj, str):
            result = self.sanitize_text_full(obj)
            return result.sanitized_content, result.threats_detected, result.modifications_made

        elif isinstance(obj, (int, float, bool, type(None))):
            # Primitive types are safe
            return obj, threats, modifications

        else:
            # Unknown type - convert to string and sanitize
            str_result = self.sanitize_text_full(str(obj))
            modifications.append("type_converted")
            return str_result.sanitized_content, str_result.threats_detected, str_result.modifications_made

    def is_safe(self, text: str) -> bool:
        """
        Quick check if text is safe.

        Args:
            text: Text to check

        Returns:
            True if text appears safe
        """
        result = self.sanitize_text_full(text)
        return result.is_safe

    def detect_threats(self, text: str) -> list[dict[str, Any]]:
        """
        Detect threats without modifying input.

        Args:
            text: Text to analyze

        Returns:
            List of detected threats
        """
        threats: list[dict[str, Any]] = []

        for compiled_pattern, threat_type, severity in self._compiled_patterns:
            matches = compiled_pattern.findall(text)
            if matches:
                threats.append(
                    {
                        "type": threat_type.value,
                        "severity": severity.value,
                        "pattern": compiled_pattern.pattern,
                        "matches": matches[:5],
                        "match_count": len(matches),
                    }
                )

        return threats

    def get_max_severity(self, threats: list[dict[str, Any]]) -> ThreatSeverity:
        """
        Get maximum severity from list of threats.

        Args:
            threats: List of threat dictionaries

        Returns:
            Maximum ThreatSeverity
        """
        if not threats:
            return ThreatSeverity.NONE

        max_sev = ThreatSeverity.NONE
        for threat in threats:
            try:
                severity = ThreatSeverity(threat.get("severity", "none"))
                max_sev = max(max_sev, severity, key=lambda x: list(ThreatSeverity).index(x))
            except ValueError:
                pass

        return max_sev

    @staticmethod
    def escape_for_shell(text: str) -> str:
        """
        Escape text for safe shell use.

        Args:
            text: Text to escape

        Returns:
            Shell-escaped text
        """
        # Remove any shell special characters
        dangerous_chars = set(";&|`$(){}[]<>\\'\"!*?~")
        escaped = "".join(c if c not in dangerous_chars else "" for c in text)
        return escaped

    @staticmethod
    def escape_for_sql(text: str) -> str:
        """
        Escape text for safe SQL use (basic escaping, prefer parameterized queries).

        Args:
            text: Text to escape

        Returns:
            SQL-escaped text
        """
        # Basic escaping - always use parameterized queries in production
        return text.replace("'", "''").replace("\\", "\\\\")


# ─────────────────────────────────────────────────────────────
# Factory Functions
# ─────────────────────────────────────────────────────────────

_default_sanitizer: InputSanitizer | None = None


def get_sanitizer(config: SanitizationConfig | None = None) -> InputSanitizer:
    """
    Get the default input sanitizer instance.

    Args:
        config: Optional configuration

    Returns:
        Shared InputSanitizer instance
    """
    global _default_sanitizer
    if _default_sanitizer is None:
        _default_sanitizer = InputSanitizer(config)
    return _default_sanitizer


def sanitize_text(text: str) -> str:
    """
    Sanitize text using default sanitizer.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text
    """
    return get_sanitizer().sanitize_text(text)


def sanitize_json(data: dict[str, Any]) -> dict[str, Any]:
    """
    Sanitize JSON using default sanitizer.

    Args:
        data: Dictionary to sanitize

    Returns:
        Sanitized dictionary
    """
    return get_sanitizer().sanitize_json(data)


def is_safe(text: str) -> bool:
    """
    Check if text is safe using default sanitizer.

    Args:
        text: Text to check

    Returns:
        True if text appears safe
    """
    return get_sanitizer().is_safe(text)
