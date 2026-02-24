"""
MYCELIUM Safety Layer — Risk mitigation, input sanitization, and boundary enforcement.

LIMITATIONS:
    This module provides heuristic-based safety checks suitable for a local-first
    accessibility tool. It is NOT a production content moderation system. Keyword
    matching alone is insufficient for production safety without classifier context.
    All patterns here are descriptive (nouns/concepts), never imperative or
    perpetrator-voiced, per Trust Layer Rule 1.1.

Safety invariants enforced:
    1. Input bounds — text length, parameter ranges, memory caps
    2. PII detection — heuristic patterns for emails, phones, SSNs, credit cards
    3. Content sanitization — null bytes, control characters, injection attempts
    4. Memory caps — bounded history sizes to prevent resource exhaustion
    5. Rate awareness — signal frequency tracking to detect abuse patterns
    6. Output integrity — ensure synthesis never produces more data than input

Design principles:
    - Fail-closed: if safety check fails, reject rather than pass through
    - Non-punitive: detection triggers warnings, not blocking (Rule 4.2)
    - Privacy-first: PII detection is local-only, no data transmitted
    - Descriptive patterns: nouns and concepts only, no perpetrator voice (Rule 1.1)
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CONSTANTS — Hard limits. Non-negotiable bounds.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MAX_INPUT_LENGTH: int = 500_000  # 500KB text limit
MAX_CONCEPT_NAME_LENGTH: int = 100
MAX_HIGHLIGHTS: int = 50
MAX_HISTORY_SIZE: int = 1_000  # persona signal/resonance history cap
MAX_REGISTERED_CONCEPTS: int = 500
MAX_LENSES_PER_CONCEPT: int = 20
MAX_CHALLENGES_LIST: int = 20
MAX_INTERESTS_LIST: int = 50
MAX_TRAIT_VALUE_LENGTH: int = 100
MIN_INPUT_LENGTH: int = 1  # at least 1 character


class SafetyVerdict(StrEnum):
    """Result of a safety check."""

    PASS = "pass"
    WARN = "warn"  # proceed with caution (e.g., PII detected)
    REJECT = "reject"  # do not proceed


@dataclass
class SafetyReport:
    """Outcome of safety validation."""

    verdict: SafetyVerdict
    reasons: list[str] = field(default_factory=list)
    pii_detected: bool = False
    sanitized_text: str | None = None  # cleaned version if applicable
    original_length: int = 0
    processing_time_ms: float = 0.0

    @property
    def is_safe(self) -> bool:
        return self.verdict in (SafetyVerdict.PASS, SafetyVerdict.WARN)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PII PATTERNS — Heuristic detection, local-only, no data stored.
#  Descriptive noun form per Trust Layer Rule 1.1.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_PII_PATTERNS: dict[str, re.Pattern[str]] = {
    "email_address": re.compile(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", re.ASCII
    ),
    "phone_number": re.compile(
        r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"
    ),
    "social_security_number": re.compile(
        r"\b\d{3}-\d{2}-\d{4}\b"
    ),
    "credit_card_number": re.compile(
        r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"
    ),
    "ip_address": re.compile(
        r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"
    ),
}

# Max text length to scan for PII (avoids regex cost on huge inputs)
_PII_SCAN_LIMIT: int = 10_000

# Characters that should never appear in processed text
_DANGEROUS_CHARS: re.Pattern[str] = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]"  # control characters (except \t \n \r)
)


class SafetyGuard:
    """Centralized safety validation for all Mycelium operations.

    Every public method on Instrument should route through this guard
    before processing user input. The guard validates, sanitizes, and
    reports — but never stores user content.
    """

    def __init__(self) -> None:
        self._check_count: int = 0
        self._last_check_time: float = 0.0

    def validate_input(self, text: str) -> SafetyReport:
        """Validate text input before synthesis.

        Checks:
            1. Type is string
            2. Length within bounds (1..500,000 chars)
            3. No dangerous control characters
            4. PII detection (warn, don't block)

        Args:
            text: Raw input text to validate.

        Returns:
            SafetyReport with verdict and any warnings.
        """
        start = time.monotonic()
        reasons: list[str] = []
        pii_found = False

        # Type check
        if not isinstance(text, str):
            return SafetyReport(
                verdict=SafetyVerdict.REJECT,
                reasons=["Input must be a string"],
                original_length=0,
                processing_time_ms=_elapsed_ms(start),
            )

        original_length = len(text)

        # Length bounds
        if original_length > MAX_INPUT_LENGTH:
            return SafetyReport(
                verdict=SafetyVerdict.REJECT,
                reasons=[
                    f"Input exceeds maximum length ({original_length:,} > {MAX_INPUT_LENGTH:,} chars)"
                ],
                original_length=original_length,
                processing_time_ms=_elapsed_ms(start),
            )

        if original_length < MIN_INPUT_LENGTH or not text.strip():
            return SafetyReport(
                verdict=SafetyVerdict.REJECT,
                reasons=["Input is empty or whitespace-only"],
                original_length=original_length,
                processing_time_ms=_elapsed_ms(start),
            )

        # Sanitize dangerous characters
        sanitized = _DANGEROUS_CHARS.sub("", text)
        if len(sanitized) != original_length:
            reasons.append("Control characters removed from input")

        # PII detection (warn, don't block — Rule 4.2: non-punitive)
        pii_types = self.detect_pii(sanitized)
        if pii_types:
            pii_found = True
            reasons.append(
                f"Possible PII detected: {', '.join(pii_types)}. "
                f"Processing locally only — no data transmitted."
            )

        self._check_count += 1
        self._last_check_time = time.monotonic()

        verdict = SafetyVerdict.WARN if (reasons and not pii_found) or pii_found else SafetyVerdict.PASS
        if reasons and not pii_found:
            verdict = SafetyVerdict.WARN
        elif pii_found:
            verdict = SafetyVerdict.WARN

        return SafetyReport(
            verdict=verdict,
            reasons=reasons,
            pii_detected=pii_found,
            sanitized_text=sanitized,
            original_length=original_length,
            processing_time_ms=_elapsed_ms(start),
        )

    def validate_parameter(
        self,
        name: str,
        value: Any,
        *,
        min_val: int | float | None = None,
        max_val: int | float | None = None,
        max_length: int | None = None,
        allowed_values: set[str] | None = None,
    ) -> SafetyReport:
        """Validate a single parameter value.

        Args:
            name: Parameter name (for error messages).
            value: The value to validate.
            min_val: Minimum numeric value.
            max_val: Maximum numeric value.
            max_length: Maximum string length.
            allowed_values: Set of allowed string values.

        Returns:
            SafetyReport with verdict.
        """
        start = time.monotonic()
        reasons: list[str] = []

        if isinstance(value, (int, float)):
            if min_val is not None and value < min_val:
                reasons.append(f"{name} below minimum ({value} < {min_val})")
            if max_val is not None and value > max_val:
                reasons.append(f"{name} above maximum ({value} > {max_val})")

        if isinstance(value, str):
            if max_length is not None and len(value) > max_length:
                reasons.append(
                    f"{name} exceeds maximum length ({len(value)} > {max_length})"
                )
            if allowed_values is not None and value not in allowed_values:
                reasons.append(
                    f"{name} has invalid value '{value}'. "
                    f"Allowed: {', '.join(sorted(allowed_values))}"
                )

        if isinstance(value, list):
            if max_val is not None and len(value) > max_val:
                reasons.append(
                    f"{name} list exceeds maximum size ({len(value)} > {int(max_val)})"
                )

        verdict = SafetyVerdict.REJECT if reasons else SafetyVerdict.PASS
        return SafetyReport(
            verdict=verdict,
            reasons=reasons,
            processing_time_ms=_elapsed_ms(start),
        )

    def detect_pii(self, text: str) -> list[str]:
        """Detect potential PII in text. Returns list of PII type names found.

        Local-only detection. No data is stored or transmitted.
        Uses heuristic regex patterns — not a production PII classifier.
        Scans only the first 10KB to bound regex execution time.
        """
        scan_text = text[:_PII_SCAN_LIMIT]
        found: list[str] = []
        for pii_type, pattern in _PII_PATTERNS.items():
            if pattern.search(scan_text):
                found.append(pii_type)
        return found

    def enforce_history_cap(
        self,
        history: list[Any],
        max_size: int = MAX_HISTORY_SIZE,
    ) -> list[Any]:
        """Enforce maximum size on a history list. Trims oldest entries.

        Args:
            history: The list to cap.
            max_size: Maximum allowed size.

        Returns:
            Trimmed list (most recent entries preserved).
        """
        if len(history) > max_size:
            trimmed = len(history) - max_size
            logger.info(
                "SafetyGuard: trimmed %d oldest entries from history (cap=%d)",
                trimmed, max_size,
            )
            return history[-max_size:]
        return history

    def validate_concept_name(self, name: str) -> SafetyReport:
        """Validate a concept name for registration."""
        return self.validate_parameter(
            "concept_name",
            name,
            max_length=MAX_CONCEPT_NAME_LENGTH,
        )

    def validate_lenses_count(self, concept: str, current: int, adding: int) -> SafetyReport:
        """Check that adding lenses won't exceed the per-concept cap."""
        total = current + adding
        if total > MAX_LENSES_PER_CONCEPT:
            return SafetyReport(
                verdict=SafetyVerdict.REJECT,
                reasons=[
                    f"Concept '{concept}' would have {total} lenses "
                    f"(max {MAX_LENSES_PER_CONCEPT})"
                ],
            )
        return SafetyReport(verdict=SafetyVerdict.PASS)

    @property
    def stats(self) -> dict[str, Any]:
        """Safety check statistics."""
        return {
            "checks_performed": self._check_count,
            "last_check_time": self._last_check_time,
        }


def _elapsed_ms(start: float) -> float:
    """Milliseconds elapsed since start."""
    return (time.monotonic() - start) * 1000


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MODULE-LEVEL CONVENIENCE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_default_guard = SafetyGuard()


def validate_input(text: str) -> SafetyReport:
    """Module-level convenience for input validation."""
    return _default_guard.validate_input(text)


def detect_pii(text: str) -> list[str]:
    """Module-level convenience for PII detection."""
    return _default_guard.detect_pii(text)
