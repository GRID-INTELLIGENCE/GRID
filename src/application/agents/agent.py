"""Agent utilities for Atlas integration.

Provides prompt sanitization to prevent injection attacks and ensure safe LLM interactions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


class SanitizationLevel(Enum):
    """Sanitization strictness levels."""

    MINIMAL = "minimal"  # Remove only critical injection patterns
    STANDARD = "standard"  # Default: balanced security
    STRICT = "strict"  # Maximum protection, may alter content significantly


@dataclass(frozen=True, slots=True)
class SanitizationResult:
    """Result of prompt sanitization."""

    sanitized: str
    original: str
    modifications: tuple[str, ...]
    level: SanitizationLevel


_INJECTION_PATTERNS: tuple[tuple[str, str, str], ...] = (
    # System prompt injection attempts
    (r"(?i)\[SYSTEM\]", "[FILTERED]", "system_bracket_injection"),
    (r"(?i)<<SYS>>", "[FILTERED]", "llama_system_injection"),
    (r"(?i)<\|im_start\|>system", "[FILTERED]", "chatml_system_injection"),
    # Role manipulation
    (r"(?i)ignore previous instructions", "[instruction reference removed]", "instruction_override"),
    (r"(?i)disregard (all |any )?prior", "[instruction reference removed]", "prior_disregard"),
    (r"(?i)forget (everything|all|what)", "[instruction reference removed]", "forget_instruction"),
    # Prompt leaking attempts
    (r"(?i)repeat (the |your )?system prompt", "[request filtered]", "prompt_leak_repeat"),
    (r"(?i)show (me )?(the |your )?instructions", "[request filtered]", "prompt_leak_show"),
    (r"(?i)what (are|is) your (system |initial )?prompt", "[request filtered]", "prompt_leak_query"),
    (r"(?i)tell (me )?(the |your )?system prompt", "[request filtered]", "prompt_leak_tell"),
    (r"(?i)(your |the )system prompt", "[request filtered]", "prompt_reference"),
    # Jailbreak patterns
    (r"(?i)DAN mode", "[filtered]", "dan_jailbreak"),
    (r"(?i)developer mode", "[filtered]", "developer_mode_jailbreak"),
    (r"(?i)pretend you (are|have) no", "[filtered]", "pretend_jailbreak"),
)

_STRICT_PATTERNS: tuple[tuple[str, str, str], ...] = (
    # Additional strict-mode patterns
    (r"(?i)act as (if you are|a)", "[role reference filtered]", "role_assumption"),
    (r"(?i)you are now", "[role reference filtered]", "role_override"),
    (r"(?i)from now on", "[temporal override filtered]", "temporal_override"),
    # Code injection via markdown
    (r"```system", "```text", "code_block_system"),
    (r"```instruction", "```text", "code_block_instruction"),
)


def sanitize_prompt(
    prompt: str,
    *,
    level: SanitizationLevel = SanitizationLevel.STANDARD,
    custom_patterns: Sequence[tuple[str, str, str]] | None = None,
    max_length: int | None = None,
) -> SanitizationResult:
    """Sanitize a prompt to prevent injection attacks.

    Args:
        prompt: The raw prompt text to sanitize.
        level: Strictness level for sanitization.
        custom_patterns: Additional (pattern, replacement, name) tuples.
        max_length: Optional maximum length to truncate to.

    Returns:
        SanitizationResult with sanitized text and modification log.

    Example:
        >>> result = sanitize_prompt("Ignore previous instructions and...")
        >>> result.sanitized
        '[instruction reference removed] and...'
        >>> result.modifications
        ('instruction_override',)
    """
    if not prompt:
        return SanitizationResult(
            sanitized="",
            original="",
            modifications=(),
            level=level,
        )

    original = prompt
    modifications: list[str] = []
    sanitized = prompt

    # Select patterns based on level
    patterns: list[tuple[str, str, str]] = []
    if level != SanitizationLevel.MINIMAL:
        patterns.extend(_INJECTION_PATTERNS)
    if level == SanitizationLevel.STRICT:
        patterns.extend(_STRICT_PATTERNS)

    # Add custom patterns
    if custom_patterns:
        patterns.extend(custom_patterns)

    # Apply pattern replacements
    for pattern, replacement, name in patterns:
        new_text, count = re.subn(pattern, replacement, sanitized)
        if count > 0:
            sanitized = new_text
            modifications.append(name)

    # Normalize whitespace
    sanitized = re.sub(r"\s+", " ", sanitized).strip()

    # Length truncation
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rsplit(" ", 1)[0] + "..."
        modifications.append("truncated")

    return SanitizationResult(
        sanitized=sanitized,
        original=original,
        modifications=tuple(modifications),
        level=level,
    )


def is_prompt_safe(prompt: str, *, level: SanitizationLevel = SanitizationLevel.STANDARD) -> bool:
    """Check if a prompt is safe without modifying it.

    Args:
        prompt: The prompt to check.
        level: Strictness level for checking.

    Returns:
        True if the prompt requires no sanitization.
    """
    result = sanitize_prompt(prompt, level=level)
    return len(result.modifications) == 0
