"""
Persona Engine — Understand the user, adapt to them.

Mission 1 of Mycelium: understand the end user and their personality.

This module detects user characteristics from interaction signals
and builds a PersonaProfile that the rest of the system uses to adapt.

Detection is heuristic and local-only. No data leaves the device.
The user can always override any detected trait explicitly.

Inspired by:
  - GRID's CognitiveRouter (expertise-based routing)
  - GRID's ScaffoldingEngine (load-based adaptation)
  - Mycelium's Mother Tree principle (adapt to what the node needs)
"""

from __future__ import annotations

import logging
import re
import statistics
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from mycelium.core import (
    CognitiveStyle,
    Depth,
    EngagementTone,
    ExpertiseLevel,
    PersonaProfile,
    ResonanceLevel,
)

logger = logging.getLogger(__name__)

# Memory caps — prevent unbounded growth (Safety Rule 5.6)
_MAX_SIGNALS: int = 500
_MAX_WORD_HISTORY: int = 2_000
_MAX_FEEDBACK_HISTORY: int = 200
_MAX_RESPONSE_TIMES: int = 200
_MAX_RESONANCE_HISTORY: int = 500
_MAX_PREFERRED_PATTERNS: int = 50


@dataclass
class InteractionSignal:
    """A single observation from user interaction."""

    signal_type: str  # "query", "feedback", "preference", "behavior"
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class PersonaSnapshot:
    """Point-in-time snapshot of detected persona traits with confidence."""

    profile: PersonaProfile
    confidence: float  # 0.0–1.0 overall confidence in detection
    trait_confidences: dict[str, float] = field(default_factory=dict)
    signals_analyzed: int = 0


class PersonaEngine:
    """Detects and adapts to user personality from interaction signals.

    The engine observes how the user interacts — what they ask, how they
    phrase things, what feedback they give — and builds a profile that
    helps the rest of Mycelium adapt its output.

    Not a classifier. Not a label. A living, updatable understanding.
    """

    # Vocabulary indicators for expertise detection
    _JARGON_PATTERNS: dict[str, list[str]] = {
        "tech": [
            "api", "backend", "frontend", "database", "server", "deploy",
            "cache", "endpoint", "middleware", "async", "latency", "throughput",
            "microservice", "container", "kubernetes", "docker", "redis",
        ],
        "science": [
            "hypothesis", "variable", "correlation", "methodology", "empirical",
            "quantitative", "qualitative", "peer-reviewed", "statistical",
        ],
        "legal": [
            "jurisdiction", "plaintiff", "defendant", "statute", "compliance",
            "liability", "precedent", "arbitration", "indemnity",
        ],
        "medical": [
            "diagnosis", "prognosis", "pathology", "etiology", "contraindication",
            "pharmacological", "symptomatic", "chronic", "acute",
        ],
        "finance": [
            "portfolio", "derivative", "amortization", "equity", "liquidity",
            "hedge", "arbitrage", "yield", "dividend", "collateral",
        ],
    }

    # Simple sentence patterns indicating cognitive style
    _STYLE_INDICATORS: dict[CognitiveStyle, list[str]] = {
        CognitiveStyle.VISUAL: [
            "show me", "picture", "diagram", "looks like", "visualize",
            "graph", "chart", "map", "color", "layout",
        ],
        CognitiveStyle.NARRATIVE: [
            "tell me", "story", "example", "like when", "imagine",
            "analogy", "metaphor", "scenario", "walk me through",
        ],
        CognitiveStyle.ANALYTICAL: [
            "compare", "data", "statistics", "versus", "trade-off",
            "pros and cons", "benchmark", "measure", "quantify",
        ],
        CognitiveStyle.KINESTHETIC: [
            "try it", "hands-on", "practice", "exercise", "build",
            "experiment", "interactive", "step by step", "do it",
        ],
    }

    def __init__(self) -> None:
        self._signals: list[InteractionSignal] = []
        self._current_profile = PersonaProfile()
        self._word_history: list[str] = []
        self._feedback_history: list[dict[str, Any]] = []
        self._response_times: list[float] = []
        self._total_signals_received: int = 0

    @property
    def profile(self) -> PersonaProfile:
        """Current detected profile."""
        return self._current_profile

    def observe(self, signal: InteractionSignal) -> PersonaSnapshot:
        """Feed an interaction signal into the engine and update the profile.

        Args:
            signal: An observation from user interaction.

        Returns:
            Updated persona snapshot with confidence scores.
        """
        self._signals.append(signal)
        self._total_signals_received += 1

        if signal.signal_type == "query":
            self._analyze_query(signal.content)
        elif signal.signal_type == "feedback":
            self._analyze_feedback(signal)
        elif signal.signal_type == "preference":
            self._apply_explicit_preference(signal)
        elif signal.signal_type == "behavior":
            self._analyze_behavior(signal)

        self._enforce_caps()
        return self._build_snapshot()

    def set_explicit(self, **traits: Any) -> PersonaProfile:
        """User explicitly sets traits. Always overrides detection.

        Example:
            engine.set_explicit(expertise="expert", tone="direct")
        """
        for trait_name, trait_value in traits.items():
            if trait_name == "expertise" and isinstance(trait_value, str):
                self._current_profile.expertise = ExpertiseLevel(trait_value)
            elif trait_name == "cognitive_style" and isinstance(trait_value, str):
                self._current_profile.cognitive_style = CognitiveStyle(trait_value)
            elif trait_name == "tone" and isinstance(trait_value, str):
                self._current_profile.tone = EngagementTone(trait_value)
            elif trait_name == "depth" and isinstance(trait_value, str):
                self._current_profile.depth = Depth(trait_value)
            elif trait_name == "attention_span" and isinstance(trait_value, str):
                self._current_profile.attention_span = trait_value
            elif trait_name == "age_group" and isinstance(trait_value, str):
                self._current_profile.age_group = trait_value
            elif trait_name == "challenges" and isinstance(trait_value, list):
                self._current_profile.challenges = trait_value
            elif trait_name == "interests" and isinstance(trait_value, list):
                self._current_profile.interests = trait_value
            elif trait_name == "language" and isinstance(trait_value, str):
                self._current_profile.language = trait_value

        logger.info("PersonaEngine: explicit traits set: %s", list(traits.keys()))
        return self._current_profile

    def record_resonance(
        self, concept: str, pattern: str, level: ResonanceLevel
    ) -> None:
        """Record whether an explanation resonated. Feeds back into profile."""
        self._current_profile.record_resonance(concept, pattern, level)
        self._feedback_history.append(
            {
                "concept": concept,
                "pattern": pattern,
                "level": level.value,
                "timestamp": time.time(),
            }
        )
        self._enforce_caps()

    def reset(self) -> None:
        """Clear all detected traits and history. Start fresh."""
        self._signals.clear()
        self._word_history.clear()
        self._feedback_history.clear()
        self._response_times.clear()
        self._current_profile = PersonaProfile()
        self._total_signals_received = 0
        logger.info("PersonaEngine: reset to defaults")

    def _enforce_caps(self) -> None:
        """Enforce memory caps on all history lists. Trims oldest entries."""
        if len(self._signals) > _MAX_SIGNALS:
            self._signals = self._signals[-_MAX_SIGNALS:]
        if len(self._word_history) > _MAX_WORD_HISTORY:
            self._word_history = self._word_history[-_MAX_WORD_HISTORY:]
        if len(self._feedback_history) > _MAX_FEEDBACK_HISTORY:
            self._feedback_history = self._feedback_history[-_MAX_FEEDBACK_HISTORY:]
        if len(self._response_times) > _MAX_RESPONSE_TIMES:
            self._response_times = self._response_times[-_MAX_RESPONSE_TIMES:]
        if len(self._current_profile.resonance_history) > _MAX_RESONANCE_HISTORY:
            self._current_profile.resonance_history = (
                self._current_profile.resonance_history[-_MAX_RESONANCE_HISTORY:]
            )
        if len(self._current_profile.preferred_patterns) > _MAX_PREFERRED_PATTERNS:
            self._current_profile.preferred_patterns = (
                self._current_profile.preferred_patterns[-_MAX_PREFERRED_PATTERNS:]
            )

    # --- Internal analysis methods ---

    def _analyze_query(self, text: str) -> None:
        """Extract signals from a user query."""
        words = self._tokenize(text)
        self._word_history.extend(words)

        # Detect expertise from vocabulary
        self._detect_expertise(words)

        # Detect cognitive style from phrasing
        self._detect_cognitive_style(text.lower())

        # Detect attention span from query length
        self._detect_attention_span(text)

    def _analyze_feedback(self, signal: InteractionSignal) -> None:
        """Process explicit feedback signals."""
        content = signal.content.lower()
        meta = signal.metadata

        # "Too complex" / "too simple" → adjust depth
        if any(w in content for w in ["complex", "hard", "confusing", "lost"]):
            self._shift_depth_down()
        elif any(w in content for w in ["simple", "basic", "obvious", "know this"]):
            self._shift_depth_up()

        # "Didn't help" / "perfect" → adjust tone
        if any(w in content for w in ["boring", "dry", "dull"]):
            self._current_profile.tone = EngagementTone.PLAYFUL
        elif any(w in content for w in ["too casual", "serious", "professional"]):
            self._current_profile.tone = EngagementTone.DIRECT

        # Resonance level from metadata
        if "resonance" in meta:
            level = ResonanceLevel(meta["resonance"])
            pattern = meta.get("pattern", "unknown")
            concept = meta.get("concept", "unknown")
            self.record_resonance(concept, pattern, level)

    def _analyze_behavior(self, signal: InteractionSignal) -> None:
        """Process behavioral signals (time spent, scroll depth, etc.)."""
        meta = signal.metadata

        if "response_time_ms" in meta:
            self._response_times.append(meta["response_time_ms"])

        if "scroll_depth" in meta:
            depth = meta["scroll_depth"]
            if depth < 0.3:
                self._current_profile.attention_span = "short"
            elif depth > 0.7:
                self._current_profile.attention_span = "long"

    def _apply_explicit_preference(self, signal: InteractionSignal) -> None:
        """Process an explicit preference declaration."""
        meta = signal.metadata
        for key, value in meta.items():
            self.set_explicit(**{key: value})

    def _detect_expertise(self, words: list[str]) -> None:
        """Infer expertise from vocabulary density."""
        if len(self._word_history) < 10:
            return  # not enough data yet

        recent_words = set(self._word_history[-100:])
        domain_scores: dict[str, int] = {}

        for domain, jargon_list in self._JARGON_PATTERNS.items():
            overlap = recent_words.intersection(jargon_list)
            domain_scores[domain] = len(overlap)

        max_score = max(domain_scores.values()) if domain_scores else 0

        if max_score >= 5:
            self._current_profile.expertise = ExpertiseLevel.EXPERT
        elif max_score >= 3:
            self._current_profile.expertise = ExpertiseLevel.PROFICIENT
        elif max_score >= 1:
            self._current_profile.expertise = ExpertiseLevel.FAMILIAR
        # If 0, keep current (don't downgrade on sparse data)

        # Track domain as interest
        if max_score > 0:
            top_domain = max(domain_scores, key=domain_scores.get)  # type: ignore[arg-type]
            if top_domain not in self._current_profile.interests:
                self._current_profile.interests.append(top_domain)

    def _detect_cognitive_style(self, text: str) -> None:
        """Infer cognitive style from phrasing patterns."""
        scores: dict[CognitiveStyle, int] = {style: 0 for style in CognitiveStyle}

        for style, indicators in self._STYLE_INDICATORS.items():
            for phrase in indicators:
                if phrase in text:
                    scores[style] += 1

        top_style = max(scores, key=scores.get)  # type: ignore[arg-type]
        if scores[top_style] > 0:
            self._current_profile.cognitive_style = top_style

    def _detect_attention_span(self, text: str) -> None:
        """Infer attention span from query length patterns."""
        word_count = len(text.split())

        if word_count <= 5:
            self._current_profile.attention_span = "short"
        elif word_count >= 30:
            self._current_profile.attention_span = "long"

    def _shift_depth_down(self) -> None:
        """Make output simpler."""
        match self._current_profile.depth:
            case Depth.COLD_BREW:
                self._current_profile.depth = Depth.AMERICANO
            case Depth.AMERICANO:
                self._current_profile.depth = Depth.ESPRESSO
            case Depth.ESPRESSO:
                pass  # already at simplest

    def _shift_depth_up(self) -> None:
        """Make output more detailed."""
        match self._current_profile.depth:
            case Depth.ESPRESSO:
                self._current_profile.depth = Depth.AMERICANO
            case Depth.AMERICANO:
                self._current_profile.depth = Depth.COLD_BREW
            case Depth.COLD_BREW:
                pass  # already at deepest

    def _build_snapshot(self) -> PersonaSnapshot:
        """Build a confidence-scored snapshot of the current profile."""
        signal_count = len(self._signals)

        # Confidence grows with more signals, caps at 0.95
        base_confidence = min(signal_count / 20, 0.95)

        # Trait-level confidence
        trait_conf: dict[str, float] = {
            "expertise": min(len(self._word_history) / 50, 0.9),
            "cognitive_style": min(
                sum(1 for s in self._signals if s.signal_type == "query") / 10, 0.8
            ),
            "tone": min(len(self._feedback_history) / 5, 0.85),
            "depth": min(
                (len(self._feedback_history) + len(self._response_times)) / 10, 0.9
            ),
        }

        return PersonaSnapshot(
            profile=self._current_profile,
            confidence=base_confidence,
            trait_confidences=trait_conf,
            signals_analyzed=signal_count,
        )

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Simple word tokenizer. No external dependencies."""
        return [w.lower() for w in re.findall(r"[a-zA-Z]+", text) if len(w) > 2]
