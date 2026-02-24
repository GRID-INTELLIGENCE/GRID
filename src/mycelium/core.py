"""
MYCELIUM Core — Foundation types for pattern recognition and synthesis.

Every type here is designed around the cave-symbol principle:
  rich meaning in simple structures.

A Spore carries data + context + metadata — richer than a plain key-value pair.
A PersonaProfile captures who the user is — not to judge, but to adapt.
A SynthesisResult is what comes out — simplified, highlighted, accessible.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import IntEnum, StrEnum
from typing import Any


class Depth(StrEnum):
    """How deep to go. Inspired by GRID's CoffeeMode."""

    ESPRESSO = "espresso"  # fast, minimal, gist only
    AMERICANO = "americano"  # balanced, standard detail
    COLD_BREW = "cold_brew"  # full depth, all context


class SignalType(StrEnum):
    """What kind of data. Like mycelium's chemical signal types."""

    NUTRIENT = "nutrient"  # regular data (documents, text, config)
    DEFENSE = "defense"  # alerts, warnings, limits
    GROWTH = "growth"  # analytics, learning progress, feedback


class ResonanceLevel(StrEnum):
    """How well an explanation 'clicks' with the user."""

    SILENT = "silent"  # didn't land — try a different approach
    HUM = "hum"  # partially resonated — refine
    RING = "ring"  # clear resonance — this works


class ExpertiseLevel(StrEnum):
    """User's familiarity with the subject."""

    CHILD = "child"  # ages ~5-10, concrete thinking, short attention
    BEGINNER = "beginner"  # no domain knowledge, needs full context
    FAMILIAR = "familiar"  # knows basics, can handle some jargon
    PROFICIENT = "proficient"  # solid understanding, wants efficiency
    EXPERT = "expert"  # deep knowledge, wants precision and nuance


class CognitiveStyle(StrEnum):
    """How the user best absorbs information."""

    VISUAL = "visual"  # diagrams, spatial layouts, color coding
    NARRATIVE = "narrative"  # stories, analogies, step-by-step
    ANALYTICAL = "analytical"  # data, logic, structure, comparisons
    KINESTHETIC = "kinesthetic"  # hands-on, interactive, examples first


class EngagementTone(StrEnum):
    """Communication register. Not about 'dumbing down' — about resonating."""

    PLAYFUL = "playful"  # curious, exploratory, uses metaphors
    WARM = "warm"  # supportive, encouraging, patient
    DIRECT = "direct"  # concise, factual, no frills
    ACADEMIC = "academic"  # precise, structured, with citations


class HighlightPriority(IntEnum):
    """How important a keyword or highlight is."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Spore:
    """A unit of data flowing through Mycelium. Richer than key-value."""

    key: str
    value: Any
    signal_type: SignalType = SignalType.NUTRIENT
    ttl: int | None = None
    priority: int = 1
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    access_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def fingerprint(self) -> str:
        """Short hash identifying this spore's content."""
        data = f"{self.key}:{self.value}:{self.signal_type}"
        return hashlib.md5(data.encode()).hexdigest()[:12]  # noqa: S324

    def is_expired(self) -> bool:
        """Check if TTL has passed."""
        if self.ttl is None:
            return False
        age = (datetime.now(UTC) - self.created_at).total_seconds()
        return age > self.ttl

    def touch(self) -> None:
        """Record an access. Hub detection uses this."""
        self.access_count += 1


@dataclass
class PersonaProfile:
    """Who the user is. Not to judge — to adapt.

    Built from interaction signals, explicit preferences, or both.
    Everything here is local-only. Nothing leaves the device.
    """

    expertise: ExpertiseLevel = ExpertiseLevel.BEGINNER
    cognitive_style: CognitiveStyle = CognitiveStyle.NARRATIVE
    tone: EngagementTone = EngagementTone.WARM
    depth: Depth = Depth.AMERICANO
    attention_span: str = "medium"  # short, medium, long
    interests: list[str] = field(default_factory=list)
    challenges: list[str] = field(default_factory=list)  # e.g. ["dyslexia", "low_vision"]
    language: str = "en"
    age_group: str = "adult"  # child, teen, adult, elder

    # Resonance tracking — what explanations worked before
    preferred_patterns: list[str] = field(default_factory=list)
    resonance_history: list[dict[str, Any]] = field(default_factory=list)

    def effective_depth(self) -> Depth:
        """Resolve depth from expertise if not explicitly set."""
        match self.expertise:
            case ExpertiseLevel.CHILD | ExpertiseLevel.BEGINNER:
                return Depth.ESPRESSO
            case ExpertiseLevel.FAMILIAR:
                return Depth.AMERICANO
            case ExpertiseLevel.PROFICIENT | ExpertiseLevel.EXPERT:
                return Depth.COLD_BREW

    def record_resonance(self, concept: str, pattern: str, level: ResonanceLevel) -> None:
        """Track what explanation styles resonate with this user."""
        self.resonance_history.append(
            {
                "concept": concept,
                "pattern": pattern,
                "level": level.value,
                "timestamp": time.time(),
            }
        )
        if level == ResonanceLevel.RING and pattern not in self.preferred_patterns:
            self.preferred_patterns.append(pattern)


@dataclass
class Highlight:
    """A keyword or point worth highlighting within a body of text."""

    text: str
    priority: HighlightPriority = HighlightPriority.MEDIUM
    context: str = ""  # surrounding sentence or phrase
    category: str = ""  # e.g. "definition", "action", "concept", "name"
    position: int = 0  # character offset in source


@dataclass
class SynthesisResult:
    """The output of synthesis — complexity made simple."""

    # The gist — always present, always short
    gist: str

    # Highlights — the key points extracted
    highlights: list[Highlight] = field(default_factory=list)

    # Layered detail — progressively deeper
    summary: str = ""  # 2-3 sentence summary
    explanation: str = ""  # full accessible explanation
    analogy: str = ""  # geometric/natural analogy if available

    # Metadata
    source_length: int = 0  # original content length (chars)
    compression_ratio: float = 0.0  # gist_length / source_length
    depth_used: Depth = Depth.AMERICANO
    patterns_applied: list[str] = field(default_factory=list)
    scaffolding_applied: list[str] = field(default_factory=list)

    # Feedback hook
    resonance: ResonanceLevel = ResonanceLevel.HUM

    def as_dict(self) -> dict[str, Any]:
        """Serialize for storage or transmission."""
        return {
            "gist": self.gist,
            "highlights": [
                {"text": h.text, "priority": h.priority.value, "category": h.category}
                for h in self.highlights
            ],
            "summary": self.summary,
            "explanation": self.explanation,
            "analogy": self.analogy,
            "compression_ratio": round(self.compression_ratio, 3),
            "depth": self.depth_used.value,
            "patterns": self.patterns_applied,
        }
