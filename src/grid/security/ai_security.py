"""
AI-specific security primitives for the GRID infrastructure layer.

Owns: prompt injection detection, AI input validation, AI output sanitisation.
Layer: grid.security (infrastructure) — MUST NOT import from application.*.

Consumed by:
  - tests/security/test_security_suite.py::TestAISecurity
  - safety pipeline middleware (future wiring)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class AISecurityConfig:
    """Tuneable parameters for AI input/output security checks."""

    max_input_length: int = 10_000
    max_output_length: int = 50_000
    # Risk score at or above which an input is considered unsafe (0–1 scale).
    # N8: aligned with minimum _INPUT_THREAT_PATTERNS risk (0.7); below this,
    # a single pattern match would always exceed threshold, making it a no-op gate.
    risk_threshold: float = 0.7
    # N7: when False, validate_input() still scores risk but never returns False
    # on pattern matches (useful for observe-only / audit modes).
    block_prompt_injections: bool = True
    # Patterns added at runtime (e.g. per-deployment policy)
    extra_input_patterns: list[str] = field(default_factory=list)
    extra_output_patterns: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Threat pattern tables
# ---------------------------------------------------------------------------

# Each entry: (compiled_pattern, risk_score, human_readable_reason)
_INPUT_THREAT_PATTERNS: list[tuple[re.Pattern, float, str]] = [
    (
        re.compile(
            r"\bignore\b.{0,80}\b(?:previous|all)\b.{0,80}"
            r"\b(?:instructions|rules|constraints|guidelines)\b",
            re.I | re.S,
        ),
        0.9,
        "Instruction-override attempt",
    ),
    (
        re.compile(
            r"\b(?:you are now|you're now|now you are)\b.{0,100}"
            r"\b(?:developer|dev|uncensored|jailbreak|god|DAN)\b",
            re.I | re.S,
        ),
        0.85,
        "Persona-jailbreak attempt",
    ),
    (
        re.compile(r"^(?:SYSTEM|USER|ASSISTANT)\s*:", re.I | re.M),
        0.8,
        "Role-marker injection",
    ),
    (
        re.compile(
            r"\bforget\b.{0,100}"
            r"\b(?:safety|instructions|guidelines|rules|constraints)\b",
            re.I | re.S,
        ),
        0.9,
        "Safety-bypass attempt",
    ),
    (
        re.compile(
            r"\b(?:reveal|expose|show|leak)\b.{0,80}"
            r"\b(?:all user|internal|system prompt|password|secret)\b",
            re.I | re.S,
        ),
        0.75,
        "Data-exfiltration attempt",
    ),
    (
        re.compile(
            r"\b(?:break character|drop character|act as|pretend you are)\b",
            re.I,
        ),
        0.7,
        "Character-manipulation attempt",
    ),
    (
        re.compile(
            r"\b(?:developer mode|god mode|DAN mode|jailbreak mode)\b",
            re.I,
        ),
        0.85,
        "Mode-manipulation attempt",
    ),
]

# Each entry: (compiled_pattern, replacement_token, filter_label)
_OUTPUT_FILTER_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    (
        re.compile(r"(?i)\bsystem\s*prompt\b[^\n.]*"),
        "FILTERED_SYSTEM_PROMPT",
        "system_prompt_exposure",
    ),
    (
        re.compile(r"(?i)\binternal\s*data\b[^\n.]*"),
        "FILTERED_INTERNAL_DATA",
        "internal_data_exposure",
    ),
    (
        # Credential field assignments: password:val, api_key:val, secret:val, token:val
        # Anchored to known credential field names to avoid matching URLs, timestamps, etc.
        re.compile(
            r"\b(?:password|passwd|api[_-]?key|secret|token|auth[_-]?key|private[_-]?key)"
            r"\s*[:=]\s*[^\s,;\"']{4,}",
            re.IGNORECASE,
        ),
        "FILTERED_CREDENTIALS",
        "potential_credentials",
    ),
]

# Prompt injection signals scanned by PromptInjectionDetector
_INJECTION_SIGNALS: list[tuple[re.Pattern, str]] = [
    (
        re.compile(r"\b(?:SYSTEM|ASSISTANT|USER)\s*:", re.I),
        "role_marker",
    ),
    (
        re.compile(
            r"\b(?:ignore safety|break character|reveal secrets|"
            r"uncensored|jailbreak|bypass|override instructions?)\b",
            re.I,
        ),
        "injection_keyword",
    ),
    (
        re.compile(
            r"\bignore\b.{0,50}\b(?:safety|instructions|guidelines|rules)\b",
            re.I | re.S,
        ),
        "instruction_override",
    ),
    (
        re.compile(
            r"\b(?:now you are|you are now)\b.{0,80}"
            r"\b(?:uncensored|unrestricted|free|without limits)\b",
            re.I | re.S,
        ),
        "persona_override",
    ),
]


# ---------------------------------------------------------------------------
# InputValidator
# ---------------------------------------------------------------------------


class InputValidator:
    """
    Validates raw user input before it reaches an AI model.

    Returns a 3-tuple: (is_safe: bool, reason: str, risk_score: float).
    risk_score is on a 0–1 scale; 0.0 means no threat detected.
    """

    def __init__(self, config: AISecurityConfig | None = None) -> None:
        self.config = config or AISecurityConfig()
        # Compile any runtime-added patterns
        self._extra: list[tuple[re.Pattern, float, str]] = [
            (re.compile(p, re.I | re.S), 0.8, "custom_policy") for p in self.config.extra_input_patterns
        ]

    def validate_input(self, text: str) -> tuple[bool, str, float]:
        """
        Check *text* for prompt-injection and jailbreak patterns.

        Returns:
            (True, "", 0.0)                   – safe input
            (False, <reason>, <risk_score>)   – unsafe input
        """
        if len(text) > self.config.max_input_length:
            return False, "Input exceeds maximum allowed length", 1.0

        highest_risk = 0.0
        worst_reason = ""

        for pattern, risk, reason in _INPUT_THREAT_PATTERNS + self._extra:
            if pattern.search(text):
                if risk > highest_risk:
                    highest_risk = risk
                    worst_reason = reason

        if highest_risk >= self.config.risk_threshold:
            # N7: honour observe-only mode — still report risk but don't block.
            if not self.config.block_prompt_injections:
                return True, worst_reason, highest_risk
            return False, worst_reason, highest_risk

        return True, "", highest_risk


# ---------------------------------------------------------------------------
# OutputSanitizer
# ---------------------------------------------------------------------------


class OutputSanitizer:
    """
    Scrubs AI-generated output before it reaches the client.

    Returns a 2-tuple: (sanitized_text: str, filters_applied: list[str]).
    If no filters fired, filters_applied is an empty list and the text is
    returned unchanged.
    """

    def __init__(self, config: AISecurityConfig | None = None) -> None:
        self.config = config or AISecurityConfig()
        # N9: parameterize the replacement token with the pattern index so callers
        # can distinguish which custom pattern fired when multiple are registered.
        self._extra: list[tuple[re.Pattern, str, str]] = [
            (re.compile(p, re.I | re.S), f"[FILTERED_CUSTOM_{i}]", f"custom_policy_{i}")
            for i, p in enumerate(self.config.extra_output_patterns)
        ]

    def sanitize_output(self, text: str) -> tuple[str, list[str]]:
        """
        Apply output filters to *text*.

        Returns:
            (original_text, [])                        – no threats found
            (filtered_text, [<filter_label>, …])       – one or more filters fired
        """
        result = text
        applied: list[str] = []

        for pattern, replacement, label in _OUTPUT_FILTER_PATTERNS + self._extra:
            new, count = pattern.subn(replacement, result)
            if count:
                result = new
                applied.append(label)

        return result, applied


# ---------------------------------------------------------------------------
# PromptInjectionDetector
# ---------------------------------------------------------------------------


class PromptInjectionDetector:
    """
    Scans text for structural prompt-injection signals.

    Unlike InputValidator (which scores risk), this detector returns a list
    of discrete detection objects so callers can inspect *what* was found.
    Each detection is a dict: {"signal": str, "match": str}.
    """

    def detect_injection(self, text: str) -> list[dict[str, str]]:
        """
        Return a list of detections found in *text*.
        An empty list means no injection signals were detected.
        """
        detections: list[dict[str, str]] = []
        seen_signals: set[str] = set()

        for pattern, signal in _INJECTION_SIGNALS:
            for match in pattern.finditer(text):
                # Deduplicate by signal type to keep the list concise
                if signal not in seen_signals:
                    detections.append({"signal": signal, "match": match.group(0)})
                    seen_signals.add(signal)

        return detections


# ---------------------------------------------------------------------------
# AISecurityWrapper
# ---------------------------------------------------------------------------


class AISecurityWrapper:
    """
    Wraps an AI inference callable with pre- and post-execution security checks.

    Usage::

        wrapper = AISecurityWrapper()
        response, info = await wrapper.secure_inference(user_text, my_model_fn)
        if not info["input_safe"]:
            # handle blocked input
            ...

    *info* keys guaranteed to be present:
        input_validated (bool) – True when the input was inspected
        input_safe      (bool) – False if a threat was detected
        risk_score      (float) – 0–1 risk score from InputValidator
        output_filtered (bool) – True when OutputSanitizer made substitutions
        filters_applied (list)  – labels of filters that fired on the output
    """

    def __init__(self, config: AISecurityConfig | None = None) -> None:
        self.config = config or AISecurityConfig()
        self._input_validator = InputValidator(self.config)
        self._output_sanitizer = OutputSanitizer(self.config)

    async def secure_inference(
        self,
        text: str,
        inference_fn,
    ) -> tuple[str, dict]:
        """
        Run *inference_fn(text)* with input validation and output sanitisation.

        *inference_fn* may be a plain callable or a coroutine function; both
        are handled transparently.

        Returns:
            (response_text, info_dict)
        """
        import asyncio

        is_safe, reason, risk = self._input_validator.validate_input(text)
        info: dict = {
            "input_validated": True,
            "input_safe": is_safe,
            "risk_score": risk,
            "output_filtered": False,
            "filters_applied": [],
        }

        if not is_safe:
            blocked_msg = f"[Blocked: {reason}]"
            return blocked_msg, info

        # Invoke the inference function — supports both sync and async
        if asyncio.iscoroutinefunction(inference_fn):
            raw_response = await inference_fn(text)
        else:
            raw_response = inference_fn(text)

        sanitized, filters = self._output_sanitizer.sanitize_output(str(raw_response))
        info["output_filtered"] = len(filters) > 0
        info["filters_applied"] = filters

        return sanitized, info
