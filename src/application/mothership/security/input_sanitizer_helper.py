"""
Helper to apply InputSanitizer at RAG, agentic, and other LLM-facing entry points.

Use before passing user-supplied text to LLM, search, or subprocess.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException, status

from .api_sentinels import InputSanitizer

logger = logging.getLogger(__name__)

# Shared instance for request-scoped use
_llm_sanitizer: InputSanitizer | None = None


def get_llm_sanitizer() -> InputSanitizer:
    """Return shared InputSanitizer for LLM/agent entry points (strict mode, reject on threat)."""
    global _llm_sanitizer
    if _llm_sanitizer is None:
        _llm_sanitizer = InputSanitizer(max_input_length=100_000, strict_mode=True)
    return _llm_sanitizer


def sanitize_text_for_llm(text: str, field_name: str = "input") -> str:
    """
    Sanitize user text before passing to LLM/RAG/agent. Raises 400 if threats detected.

    Args:
        text: Raw user input
        field_name: Name for error messages

    Returns:
        Sanitized string (or original if safe)

    Raises:
        HTTPException: 400 if input is not safe
    """
    if not text or not isinstance(text, str):
        return text or ""
    sanitizer = get_llm_sanitizer()
    result = sanitizer.sanitize_string(text)
    if not result.is_safe:
        logger.warning(
            "Input sanitization rejected %s: threats=%s",
            field_name,
            [t.get("category") for t in (result.threats_detected or [])],
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid or unsafe {field_name}; request rejected by security policy",
        )
    return result.sanitized_value if result.sanitized_value else text


def sanitize_dict_for_llm(data: dict[str, Any], text_keys: list[str]) -> dict[str, Any]:
    """
    Sanitize specific string values in a dict. Modifies a copy; returns it.
    Raises 400 if any of the listed keys contain unsafe content.
    """
    out = dict(data)
    for key in text_keys:
        if key not in out:
            continue
        val = out[key]
        if isinstance(val, str):
            out[key] = sanitize_text_for_llm(val, field_name=key)
        elif isinstance(val, list) and val and isinstance(val[0], str):
            out[key] = [sanitize_text_for_llm(v, field_name=f"{key}[]") for v in val]
    return out
