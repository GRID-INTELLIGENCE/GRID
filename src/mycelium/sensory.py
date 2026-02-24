"""
Sensory Mode — Adaptive output formatting for accessibility needs.

Adapts how Mycelium presents information based on sensory, motor,
and cognitive profiles. This isn't about changing what is said —
it's about changing the delivery channel and format.

Like how mycelium networks use different chemical signals for
different purposes (nutrients, defense, growth), Sensory Mode
uses different output formats for different user needs.

Inspired by:
  - GRID's CognitiveRouter (load-based route selection)
  - WCAG 2.2 AA guidelines (perceivable, operable, understandable)
  - Mycelium's Mother Tree principle (stressed nodes get priority support)
"""

from __future__ import annotations

import logging
import re
import textwrap
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class SensoryProfile(StrEnum):
    """Predefined sensory profiles. User picks one, or system suggests."""

    DEFAULT = "default"  # standard output
    LOW_VISION = "low_vision"  # large text markers, no visual-only info
    SCREEN_READER = "screen_reader"  # optimized for TTS, no visual formatting
    COGNITIVE = "cognitive"  # reduced complexity, shorter chunks, slower pace
    FOCUS = "focus"  # minimal output, single key point at a time
    CALM = "calm"  # soft language, no urgency markers, gentle tone


@dataclass
class SensoryAdaptation:
    """A single adaptation applied to output."""

    what: str  # e.g. "wrap_lines_at_60"
    why: str  # e.g. "Low vision profile: shorter lines easier to track"
    reversible: bool = True


@dataclass
class SensoryState:
    """Current sensory configuration."""

    profile: SensoryProfile = SensoryProfile.DEFAULT
    adaptations: list[SensoryAdaptation] = field(default_factory=list)
    line_width: int = 80  # characters per line
    uppercase_headings: bool = False  # for screen readers
    strip_formatting: bool = False  # remove markdown/symbols
    simplify_punctuation: bool = False  # reduce complex punctuation
    chunk_size: int = 3  # sentences per chunk (for cognitive profile)
    urgency_level: str = "normal"  # normal, gentle, none


class SensoryMode:
    """Manages sensory adaptations for Mycelium output.

    All processing is local. No data collected. No tracking.
    User controls everything.
    """

    # Profile → adaptations mapping
    _PROFILE_CONFIGS: dict[SensoryProfile, dict[str, Any]] = {
        SensoryProfile.DEFAULT: {
            "line_width": 80,
            "uppercase_headings": False,
            "strip_formatting": False,
            "simplify_punctuation": False,
            "chunk_size": 5,
            "urgency_level": "normal",
        },
        SensoryProfile.LOW_VISION: {
            "line_width": 60,
            "uppercase_headings": True,
            "strip_formatting": False,
            "simplify_punctuation": False,
            "chunk_size": 3,
            "urgency_level": "normal",
        },
        SensoryProfile.SCREEN_READER: {
            "line_width": 120,
            "uppercase_headings": True,
            "strip_formatting": True,
            "simplify_punctuation": True,
            "chunk_size": 3,
            "urgency_level": "normal",
        },
        SensoryProfile.COGNITIVE: {
            "line_width": 60,
            "uppercase_headings": False,
            "strip_formatting": True,
            "simplify_punctuation": True,
            "chunk_size": 2,
            "urgency_level": "gentle",
        },
        SensoryProfile.FOCUS: {
            "line_width": 50,
            "uppercase_headings": False,
            "strip_formatting": True,
            "simplify_punctuation": True,
            "chunk_size": 1,
            "urgency_level": "none",
        },
        SensoryProfile.CALM: {
            "line_width": 70,
            "uppercase_headings": False,
            "strip_formatting": False,
            "simplify_punctuation": False,
            "chunk_size": 3,
            "urgency_level": "none",
        },
    }

    def __init__(self, profile: SensoryProfile = SensoryProfile.DEFAULT) -> None:
        self._state = self._build_state(profile)

    @property
    def state(self) -> SensoryState:
        """Current sensory state."""
        return self._state

    @property
    def profile(self) -> SensoryProfile:
        """Current active profile."""
        return self._state.profile

    def apply_profile(self, profile: SensoryProfile) -> SensoryState:
        """Switch to a predefined sensory profile."""
        self._state = self._build_state(profile)
        logger.info("SensoryMode: switched to profile '%s'", profile.value)
        return self._state

    def adjust(self, **overrides: Any) -> SensoryState:
        """Fine-tune individual settings. User has full control."""
        for key, value in overrides.items():
            if hasattr(self._state, key):
                setattr(self._state, key, value)
                self._state.adaptations.append(
                    SensoryAdaptation(
                        what=f"set_{key}={value}",
                        why="User override",
                    )
                )
        return self._state

    def format_output(self, text: str) -> str:
        """Apply all active sensory adaptations to output text.

        This is the main formatting pipeline. Takes raw text from
        the scaffolding layer and formats it for the user's sensory needs.
        """
        result = text

        # 1. Strip visual formatting if needed (markdown symbols, etc.)
        if self._state.strip_formatting:
            result = self._strip_formatting(result)

        # 2. Simplify punctuation
        if self._state.simplify_punctuation:
            result = self._simplify_punctuation(result)

        # 3. Uppercase headings for screen readers
        if self._state.uppercase_headings:
            result = self._uppercase_headings(result)

        # 4. Wrap lines to configured width
        result = self._wrap_lines(result, self._state.line_width)

        # 5. Apply urgency level
        if self._state.urgency_level == "gentle":
            result = self._soften_tone(result)
        elif self._state.urgency_level == "none":
            result = self._remove_urgency(result)

        return result

    def explain_current(self) -> str:
        """Plain-language description of active adaptations."""
        profile = self._state.profile
        parts: list[str] = [f"Active profile: {profile.value}"]

        if self._state.strip_formatting:
            parts.append("Visual formatting removed (plain text only).")
        if self._state.uppercase_headings:
            parts.append("Headings are in UPPERCASE for easier detection.")
        if self._state.simplify_punctuation:
            parts.append("Punctuation simplified (fewer symbols).")
        if self._state.line_width < 80:
            parts.append(f"Lines wrap at {self._state.line_width} characters.")
        if self._state.urgency_level != "normal":
            parts.append(f"Tone: {self._state.urgency_level}.")

        if self._state.adaptations:
            parts.append(
                f"{len(self._state.adaptations)} custom adjustment(s) active."
            )

        return " ".join(parts)

    # --- Formatting implementations ---

    @staticmethod
    def _strip_formatting(text: str) -> str:
        """Remove markdown and visual-only formatting."""
        # Remove markdown bold/italic
        text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
        # Remove markdown headers
        text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
        # Remove markdown links, keep text
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        # Remove backticks
        text = re.sub(r"`([^`]+)`", r"\1", text)
        # Remove bullet points
        text = re.sub(r"^[\s]*[-*+]\s+", "  ", text, flags=re.MULTILINE)
        return text

    @staticmethod
    def _simplify_punctuation(text: str) -> str:
        """Reduce complex punctuation for cognitive accessibility."""
        # Replace em-dashes with commas
        text = text.replace("—", ", ")
        text = text.replace("–", ", ")
        # Replace semicolons with periods
        text = text.replace(";", ".")
        # Remove parenthetical asides (can be confusing)
        text = re.sub(r"\s*\([^)]{0,50}\)\s*", " ", text)
        # Collapse multiple spaces
        text = re.sub(r"  +", " ", text)
        return text

    @staticmethod
    def _uppercase_headings(text: str) -> str:
        """Make headings uppercase for screen reader emphasis."""
        lines = text.split("\n")
        result: list[str] = []
        for line in lines:
            stripped = line.strip()
            # Detect heading-like lines (short, ending without period, ALL CAPS already or title-like)
            if (
                stripped
                and len(stripped) < 60
                and not stripped.endswith(".")
                and stripped.endswith(":")
            ):
                result.append(stripped.upper())
            elif stripped.startswith(("IN BRIEF", "KEY POINTS", "SUMMARY", "STEP BY STEP", "EXAMPLE", "DETAILS", "THINK OF IT LIKE")):
                result.append(stripped.upper())
            else:
                result.append(line)
        return "\n".join(result)

    @staticmethod
    def _wrap_lines(text: str, width: int) -> str:
        """Wrap lines to specified width, preserving paragraph breaks."""
        paragraphs = text.split("\n\n")
        wrapped: list[str] = []
        for para in paragraphs:
            lines = para.split("\n")
            wrapped_lines: list[str] = []
            for line in lines:
                if len(line) <= width:
                    wrapped_lines.append(line)
                else:
                    wrapped_lines.append(textwrap.fill(line, width=width))
            wrapped.append("\n".join(wrapped_lines))
        return "\n\n".join(wrapped)

    @staticmethod
    def _soften_tone(text: str) -> str:
        """Replace urgent/harsh language with gentler alternatives."""
        replacements = {
            "ERROR": "Note",
            "WARNING": "Heads up",
            "CRITICAL": "Important",
            "FAIL": "Didn't work",
            "MUST": "Should",
            "NEVER": "Best to avoid",
            "WRONG": "Not quite right",
            "IMMEDIATELY": "When you can",
        }
        result = text
        for harsh, gentle in replacements.items():
            result = result.replace(harsh, gentle)
            result = result.replace(harsh.lower(), gentle.lower())
            result = result.replace(harsh.capitalize(), gentle)
        return result

    @staticmethod
    def _remove_urgency(text: str) -> str:
        """Remove all urgency markers entirely."""
        # Remove exclamation marks (replace with periods)
        text = text.replace("!", ".")
        # Remove ALL CAPS words (lowercase them)
        text = re.sub(
            r"\b[A-Z]{3,}\b",
            lambda m: m.group(0).capitalize(),
            text,
        )
        return text

    # --- Internal ---

    def _build_state(self, profile: SensoryProfile) -> SensoryState:
        """Build a SensoryState from a profile config."""
        config = self._PROFILE_CONFIGS.get(profile, self._PROFILE_CONFIGS[SensoryProfile.DEFAULT])
        adaptations: list[SensoryAdaptation] = []

        if config.get("strip_formatting"):
            adaptations.append(
                SensoryAdaptation(
                    what="strip_formatting",
                    why=f"{profile.value} profile: plain text for accessibility",
                )
            )
        if config.get("uppercase_headings"):
            adaptations.append(
                SensoryAdaptation(
                    what="uppercase_headings",
                    why=f"{profile.value} profile: headings in caps for detection",
                )
            )

        return SensoryState(
            profile=profile,
            adaptations=adaptations,
            line_width=config.get("line_width", 80),
            uppercase_headings=config.get("uppercase_headings", False),
            strip_formatting=config.get("strip_formatting", False),
            simplify_punctuation=config.get("simplify_punctuation", False),
            chunk_size=config.get("chunk_size", 3),
            urgency_level=config.get("urgency_level", "normal"),
        )
