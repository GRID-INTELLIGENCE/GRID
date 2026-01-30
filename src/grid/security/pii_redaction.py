"""
PII Redaction Engine for Secure Logging.

Redacts Personally Identifiable Information (PII) from logs
before writing to console, files, or audit systems.
"""

import hashlib
import logging
import re
from dataclasses import dataclass
from enum import Enum
from re import Pattern

logger = logging.getLogger(__name__)


class RedactionMode(Enum):
    """Redaction modes."""

    FULL = "full"
    PARTIAL = "partial"
    AUDIT = "audit"


@dataclass
class PIIPattern:
    """PII pattern configuration."""

    name: str
    pattern: Pattern
    replacement: str
    description: str


class PIIRedactor:
    """
    Redact PII from log messages and error reports.

    Supports: emails, phone numbers, SSN, credit cards, names, addresses.
    """

    # Predefined PII patterns
    PATTERNS: list[PIIPattern] = [
        PIIPattern(
            name="email",
            pattern=re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
            replacement="[EMAIL_REDACTED]",
            description="Email address",
        ),
        PIIPattern(
            name="phone_us",
            pattern=re.compile(r"\+?1?\s*\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}"),
            replacement="[PHONE_REDACTED]",
            description="US phone number",
        ),
        PIIPattern(
            name="phone_intl",
            pattern=re.compile(r"\+\d{1,3}\s?\(?\d{1,4}\)?[\s.-]?\d{1,4}[\s.-]?\d{1,9}"),
            replacement="[PHONE_REDACTED]",
            description="International phone number",
        ),
        PIIPattern(
            name="ssn",
            pattern=re.compile(r"\d{3}-\d{2}-\d{4}|\d{3}\s\d{2}\s\d{4}"),
            replacement="[SSN_REDACTED]",
            description="Social Security Number",
        ),
        PIIPattern(
            name="credit_card",
            pattern=re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
            replacement="[CARD_REDACTED]",
            description="Credit card number",
        ),
        PIIPattern(
            name="full_name",
            pattern=re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+(?: [A-Z][a-z]+)?\b"),
            replacement="[NAME_REDACTED]",
            description="Full name",
        ),
        PIIPattern(
            name="ipv4",
            pattern=re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
            replacement="[IP_REDACTED]",
            description="IPv4 address",
        ),
        PIIPattern(
            name="api_key",
            pattern=re.compile(r"[A-Za-z0-9_-]{20,}"),
            replacement="[KEY_REDACTED]",
            description="API key",
        ),
        PIIPattern(
            name="jwt_token",
            pattern=re.compile(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"),
            replacement="[JWT_REDACTED]",
            description="JWT token",
        ),
        PIIPattern(
            name="google_client_id",
            pattern=re.compile(r"[0-9]+-[a-zA-Z0-9_]+\.apps\.googleusercontent\.com"),
            replacement="[GOOGLE_CLIENT_ID_REDACTED]",
            description="Google OAuth client ID",
        ),
    ]

    def __init__(self, custom_patterns: list[PIIPattern] | None = None):
        """
        Initialize PII redactor.

        Args:
            custom_patterns: Additional PII patterns to redact
        """
        self.patterns = self.PATTERNS.copy()
        if custom_patterns:
            self.patterns.extend(custom_patterns)

    def redact(self, message: str, mask_mode: RedactionMode = RedactionMode.FULL) -> str:
        """
        Redact PII from message.

        Args:
            message: Original message
            mask_mode: Redaction mode (full, partial, audit)
                - full: Complete redaction "[REDACTED]"
                - partial: Partial masking "user@***.com"
                - audit: Hash-based anonymization "[HASH:abc123]"

        Returns:
            Redacted message
        """
        redacted = message

        for pii_pattern in self.patterns:
            if mask_mode == RedactionMode.FULL:
                redacted = pii_pattern.pattern.sub(pii_pattern.replacement, redacted)
            elif mask_mode == RedactionMode.PARTIAL:
                # Partial masking - show first and last chars
                redacted = self._partial_mask(redacted, pii_pattern)
            elif mask_mode == RedactionMode.AUDIT:
                # Audit mode - hash-based anonymization
                redacted = self._audit_mask(redacted, pii_pattern)

        return redacted

    def _partial_mask(self, message: str, pattern: PIIPattern) -> str:
        """
        Apply partial masking (show first 2 and last 2 chars).
        """

        def mask_match(match):
            matched = match.group()
            if len(matched) <= 4:
                return pattern.replacement
            return matched[:2] + "***" + matched[-2:]

        return pattern.pattern.sub(mask_match, message)

    def _audit_mask(self, message: str, pattern: PIIPattern) -> str:
        """
        Apply audit-mode masking (hash-based anonymization).
        """

        def mask_match(match):
            matched = match.group()
            # Use SHA256 hash for consistency
            hashed = hashlib.sha256(matched.encode()).hexdigest()[:8]
            return f"[HASH:{hashed}]"

        return pattern.pattern.sub(mask_match, message)

    def add_custom_pattern(self, name: str, pattern: str, replacement: str) -> None:
        """
        Add custom PII pattern.

        Args:
            name: Pattern name
            pattern: Regular expression pattern
            replacement: Replacement string
        """
        self.patterns.append(
            PIIPattern(
                name=name, pattern=re.compile(pattern), replacement=replacement, description=f"Custom pattern: {name}"
            )
        )


# Global redactor instance
_redactor: PIIRedactor | None = None


def get_redactor() -> PIIRedactor:
    """Get global PII redactor instance."""
    global _redactor
    if _redactor is None:
        _redactor = PIIRedactor()
    return _redactor


def redact_log_message(message: str, mask_mode: RedactionMode = RedactionMode.FULL) -> str:
    """
    Convenience function to redact PII from log message.

    Args:
        message: Log message
        mask_mode: Redaction mode (full, partial, audit)

    Returns:
        Redacted message
    """
    redactor = get_redactor()
    return redactor.redact(message, mask_mode)


def setup_logging_with_redaction():
    """
    Configure Python logging to automatically redact PII.

    This should be called during application initialization.
    """

    class RedactingFormatter(logging.Formatter):
        """Log formatter with automatic PII redaction."""

        def format(self, record):
            # Format the message first
            formatted = super().format(record)
            # Redact PII
            return redact_log_message(formatted, RedactionMode.FULL)

    # Apply to all handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.setFormatter(RedactingFormatter(handler.formatter._fmt if hasattr(handler.formatter, "_fmt") else None))

    logger.info("PII redaction enabled for all logging")


# Wealth management specific redactions
def redact_wealth_data(data: dict) -> dict:
    """
    Redact PII from wealth management data.

    Args:
        data: Dictionary containing potentially sensitive data

    Returns:
        Redacted dictionary
    """
    redacted = data.copy()

    # Redact specific wealth management fields
    if "client_name" in redacted:
        redacted["client_name"] = "[REDACTED - PERSONAL_DATA]"

    if "client_info" in redacted:
        if isinstance(redacted["client_info"], dict):
            redacted["client_info"]["name"] = "[REDACTED]"
            redacted["client_info"]["email"] = "[EMAIL_REDACTED]"
            redacted["client_info"]["phone"] = "[PHONE_REDACTED]"

    return redacted
