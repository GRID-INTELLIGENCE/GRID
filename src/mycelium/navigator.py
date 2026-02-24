"""
Pattern Navigator — Explore concepts through geometric cognitive lenses.

Mission 3 of Mycelium: assist people with various limitations or challenges
to participate in topics that carry a stigma of being "too complex."

The Navigator maps concepts to GRID's 9 cognitive patterns, offering
multiple "lenses" through which to understand the same idea. If one
lens doesn't click, try another. Like how cave artists used different
symbols for the same animal depending on context.

Each lens provides:
  - An analogy grounded in geometry or nature
  - An ELI5 (explain like I'm 5) version
  - A visual hint (what to picture in your mind)
  - When this lens is most useful

The user gives resonance feedback (SILENT / HUM / RING) and the
Navigator adapts — prioritizing lenses that resonate.

Inspired by:
  - GRID's PatternExplanation (9 patterns with human-readable descriptions)
  - GRID's CoffeeMode (adaptive depth)
  - Mycelium's cave-symbol principle (same meaning, different representation)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from mycelium.core import (
    PersonaProfile,
    ResonanceLevel,
)

logger = logging.getLogger(__name__)


@dataclass
class PatternLens:
    """A way of seeing a concept through a specific cognitive pattern."""

    pattern: str  # flow, spatial, rhythm, color, repetition, deviation, cause, time, combination
    analogy: str  # the geometric/natural analogy
    eli5: str  # explain like I'm 5
    visual_hint: str  # what to picture
    when_useful: str  # when this lens helps most


@dataclass
class NavigationResult:
    """What the Navigator returns when exploring a concept."""

    concept: str
    lens: PatternLens
    alternatives_available: int
    depth_note: str  # brief note about why this lens was chosen


# --- Lens Library ---
# Each concept has multiple lenses. Different people resonate with different ones.

_CONCEPT_LENSES: dict[str, list[PatternLens]] = {
    # --- Data / Computing concepts ---
    "cache": [
        PatternLens(
            pattern="flow",
            analogy="A river with pools — fast water flows past, pools hold what you need nearby.",
            eli5="A shelf next to you with stuff you use a lot. Saves walking to the warehouse.",
            visual_hint="Picture a river. The pools are your cache. Water is data flowing through.",
            when_useful="When you keep asking for the same thing and it's slow to get.",
        ),
        PatternLens(
            pattern="rhythm",
            analogy="A heartbeat — regular pulses of checking and refreshing.",
            eli5="Like checking your fridge. Milk expires, so you check before using it.",
            visual_hint="Picture a clock ticking. Each tick = check if data is still fresh.",
            when_useful="When data changes on a schedule and you need to stay current.",
        ),
        PatternLens(
            pattern="spatial",
            analogy="Two shelves: one arm's reach away (fast), one in the basement (slow).",
            eli5="Your desk vs. a storage room. You keep pens on your desk, not downstairs.",
            visual_hint="Picture two shelves at different distances from where you sit.",
            when_useful="When you need to understand why some data is faster to access.",
        ),
    ],
    "database": [
        PatternLens(
            pattern="spatial",
            analogy="A library with organized shelves — every book has an address.",
            eli5="A big notebook where you write things down so you don't forget.",
            visual_hint="Picture a giant filing cabinet. Each drawer has a label.",
            when_useful="When you need to store and find things reliably.",
        ),
        PatternLens(
            pattern="repetition",
            analogy="A filing system — same structure repeated for every record.",
            eli5="Like filling out the same form for every student in a school.",
            visual_hint="Picture rows of identical boxes, each with a name tag.",
            when_useful="When you have lots of similar things to keep track of.",
        ),
    ],
    "api": [
        PatternLens(
            pattern="cause",
            analogy="A waiter in a restaurant — you tell them what you want, they bring it from the kitchen.",
            eli5="You ask for pizza. The waiter goes to the kitchen and brings it. The waiter is the API.",
            visual_hint="Picture a counter with a window. You speak into the window, food comes out.",
            when_useful="When two systems need to talk to each other.",
        ),
        PatternLens(
            pattern="flow",
            analogy="A pipeline with valves — requests flow in, responses flow out.",
            eli5="A tube. You put a question in one end, an answer comes out the other.",
            visual_hint="Picture a pipe connecting two boxes. Messages travel through it.",
            when_useful="When you need to understand how data moves between systems.",
        ),
    ],
    "encryption": [
        PatternLens(
            pattern="combination",
            analogy="A lockbox with two keys — one to lock, one to unlock.",
            eli5="Writing a secret message in code. Only your friend knows the code.",
            visual_hint="Picture a treasure chest. The lock scrambles what's inside. The key unscrambles it.",
            when_useful="When you need to keep information private during transfer.",
        ),
    ],
    "algorithm": [
        PatternLens(
            pattern="flow",
            analogy="A recipe — step 1, step 2, step 3. Same ingredients, same cake every time.",
            eli5="Instructions for building a LEGO set. Follow them and you always get the same thing.",
            visual_hint="Picture a flowchart. Arrows point from one step to the next.",
            when_useful="When you need to understand a repeatable process.",
        ),
        PatternLens(
            pattern="rhythm",
            analogy="A drumbeat — the same pattern repeating, sometimes with variations.",
            eli5="Like brushing your teeth: wet, paste, brush, rinse. Same every time.",
            visual_hint="Picture a metronome clicking. Each click is a step in the process.",
            when_useful="When the process has a regular, predictable pattern.",
        ),
    ],
    "pubsub": [
        PatternLens(
            pattern="spatial",
            analogy="A town square — shout in the middle, everyone nearby hears.",
            eli5="A group chat. You post once. Everyone in the group sees it.",
            visual_hint="Picture a megaphone in a room. Walls are channels. Rooms are topics.",
            when_useful="When many parts of your app need to react to the same event.",
        ),
        PatternLens(
            pattern="cause",
            analogy="Dominoes — one falls, the next reacts, chain continues.",
            eli5="You flip a switch. The light turns on. That's pub/sub.",
            visual_hint="Picture dominoes falling in a line. Each domino is a subscriber.",
            when_useful="When action A should always trigger reactions B, C, D.",
        ),
    ],
    "rate_limit": [
        PatternLens(
            pattern="rhythm",
            analogy="A metronome — only one beat per interval, no rushing.",
            eli5="A water fountain. It only gives a sip at a time. You can't flood it.",
            visual_hint="Picture a turnstile. One person through per second.",
            when_useful="When too many requests at once would break something.",
        ),
    ],
    "leaderboard": [
        PatternLens(
            pattern="deviation",
            analogy="The tallest tree stands out from the forest canopy.",
            eli5="A race. First place is the one furthest ahead. Simple.",
            visual_hint="Picture trees of different heights. You see the tallest instantly.",
            when_useful="When you need to rank things and show the top ones.",
        ),
    ],
    "time_series": [
        PatternLens(
            pattern="time",
            analogy="Tree rings — each ring records a moment, together they tell a story.",
            eli5="A diary. One entry per day. You can read back and see what happened.",
            visual_hint="Picture tree rings. Wider rings = good years. Narrow = stress.",
            when_useful="When you want to track how something changes over time.",
        ),
    ],
    # --- General / Accessible concepts ---
    "complexity": [
        PatternLens(
            pattern="combination",
            analogy="A tangled ball of yarn — many simple threads, just wound together.",
            eli5="A messy room isn't hard. It's just lots of easy things piled up.",
            visual_hint="Picture untangling one thread at a time from a ball of yarn.",
            when_useful="When something feels overwhelming but is really just many simple parts.",
        ),
        PatternLens(
            pattern="spatial",
            analogy="A map with many roads — each road is simple, the network looks complex.",
            eli5="A city looks confusing from above. But each street is just one path.",
            visual_hint="Picture zooming into a map. Up close, every road is just a line.",
            when_useful="When you need to break a big problem into smaller, walkable pieces.",
        ),
    ],
    "recursion": [
        PatternLens(
            pattern="repetition",
            analogy="Mirrors facing each other — the same image repeating smaller and smaller.",
            eli5="A box inside a box inside a box. Open one, find another. Same shape, smaller.",
            visual_hint="Picture Russian nesting dolls. Each one contains a smaller version of itself.",
            when_useful="When a problem can be solved by solving a smaller version of itself.",
        ),
    ],
    "network": [
        PatternLens(
            pattern="spatial",
            analogy="A spider web — every intersection is a node, every thread is a connection.",
            eli5="Friends of friends. You know someone, they know someone, and so on.",
            visual_hint="Picture a web. Tug one thread, others feel it.",
            when_useful="When things are connected and those connections matter.",
        ),
    ],
    "abstraction": [
        PatternLens(
            pattern="color",
            analogy="Looking at a forest from far away — you see 'green' not individual leaves.",
            eli5="Instead of listing every animal, just say 'pets.' That's abstraction.",
            visual_hint="Picture zooming out on a photo until details blur into shapes.",
            when_useful="When you need to ignore details and focus on the big picture.",
        ),
    ],
    "pattern": [
        PatternLens(
            pattern="rhythm",
            analogy="Music — same notes repeating create a melody you can predict.",
            eli5="Clap, clap, pause. Clap, clap, pause. You know what comes next.",
            visual_hint="Picture a heartbeat on a monitor. The same shape, over and over.",
            when_useful="When you notice something happening the same way more than once.",
        ),
    ],
    "security": [
        PatternLens(
            pattern="deviation",
            analogy="A guard who knows what 'normal' looks like — anything different triggers an alert.",
            eli5="Your house. You know how it looks. If something moves, you notice.",
            visual_hint="Picture a calm lake. A single ripple means something entered the water.",
            when_useful="When you need to detect what doesn't belong.",
        ),
    ],
}


class PatternNavigator:
    """Interactive concept explorer using cognitive pattern lenses.

    The Navigator doesn't teach by dumbing down. It teaches by offering
    the same idea through different geometric/natural metaphors until
    one resonates. Like how different cave paintings of the same animal
    used different styles — the meaning is the same, the representation
    adapts to context.
    """

    def __init__(self, persona: PersonaProfile | None = None) -> None:
        self._persona = persona or PersonaProfile()
        self._exploration_history: list[dict[str, Any]] = []
        # Track which lenses resonated per concept
        self._resonance_map: dict[str, dict[str, ResonanceLevel]] = {}

    @property
    def persona(self) -> PersonaProfile:
        return self._persona

    @persona.setter
    def persona(self, value: PersonaProfile) -> None:
        self._persona = value

    @property
    def available_concepts(self) -> list[str]:
        """List all concepts that have lenses registered."""
        return sorted(_CONCEPT_LENSES.keys())

    def explore(
        self,
        concept: str,
        preferred_pattern: str | None = None,
    ) -> NavigationResult | None:
        """Explore a concept through a pattern lens.

        Args:
            concept: The concept to explore (e.g. "cache", "recursion").
            preferred_pattern: Optional preferred cognitive pattern to use.

        Returns:
            NavigationResult with the best-fit lens, or None if concept unknown.
        """
        concept_key = concept.lower().strip()
        lenses = _CONCEPT_LENSES.get(concept_key)

        if not lenses:
            # Try fuzzy match
            lenses = self._fuzzy_lookup(concept_key)
            if not lenses:
                logger.info("PatternNavigator: unknown concept '%s'", concept)
                return None

        # Pick the best lens for this user
        lens = self._select_lens(concept_key, lenses, preferred_pattern)

        # Record exploration
        self._exploration_history.append(
            {"concept": concept_key, "pattern": lens.pattern}
        )

        depth_note = self._explain_selection(lens, preferred_pattern)

        return NavigationResult(
            concept=concept_key,
            lens=lens,
            alternatives_available=len(lenses) - 1,
            depth_note=depth_note,
        )

    def try_different(
        self,
        concept: str,
        feedback: ResonanceLevel = ResonanceLevel.SILENT,
    ) -> NavigationResult | None:
        """Previous lens didn't click. Try a different one.

        Args:
            concept: The concept to re-explore.
            feedback: How well the previous lens resonated.

        Returns:
            A different NavigationResult, or None if no alternatives.
        """
        concept_key = concept.lower().strip()
        lenses = _CONCEPT_LENSES.get(concept_key)

        if not lenses or len(lenses) <= 1:
            return None

        # Record feedback on the last lens used
        if self._exploration_history:
            last = self._exploration_history[-1]
            if last["concept"] == concept_key:
                self._record_resonance(concept_key, last["pattern"], feedback)
                # Also update persona
                self._persona.record_resonance(
                    concept_key, last["pattern"], feedback
                )

        # Find a lens we haven't tried yet, or the least-tried one
        tried_patterns = self._resonance_map.get(concept_key, {})
        untried = [l for l in lenses if l.pattern not in tried_patterns]

        if untried:
            lens = untried[0]
        else:
            # All tried — pick the one with best resonance, or random
            best_pattern = max(
                tried_patterns,
                key=lambda p: (
                    0 if tried_patterns[p] == ResonanceLevel.SILENT
                    else 1 if tried_patterns[p] == ResonanceLevel.HUM
                    else 2
                ),
                default=None,
            )
            # Pick a different one from the best (to avoid repetition)
            alternatives = [l for l in lenses if l.pattern != best_pattern]
            lens = alternatives[0] if alternatives else lenses[0]

        self._exploration_history.append(
            {"concept": concept_key, "pattern": lens.pattern}
        )

        return NavigationResult(
            concept=concept_key,
            lens=lens,
            alternatives_available=len(lenses) - 1,
            depth_note="Trying a different lens based on your feedback.",
        )

    def simplify(self, concept: str) -> str:
        """Get the absolute simplest explanation. ELI5 mode. Always works."""
        concept_key = concept.lower().strip()
        lenses = _CONCEPT_LENSES.get(concept_key)

        if not lenses:
            lenses = self._fuzzy_lookup(concept_key)
        if not lenses:
            return f"'{concept}' — not in my library yet. Can you describe what it means to you?"

        # Pick the lens with the most resonance for this user, or first
        lens = self._select_lens(concept_key, lenses, preferred_pattern=None)
        return lens.eli5

    def register_concept(self, concept: str, lenses: list[PatternLens]) -> None:
        """Add or extend lenses for a concept. User-extensible."""
        concept_key = concept.lower().strip()
        existing = _CONCEPT_LENSES.get(concept_key, [])
        existing.extend(lenses)
        _CONCEPT_LENSES[concept_key] = existing
        logger.info(
            "PatternNavigator: registered %d lenses for '%s'",
            len(lenses), concept_key,
        )

    def feedback(self, concept: str, pattern: str, level: ResonanceLevel) -> None:
        """Explicit resonance feedback on a lens."""
        concept_key = concept.lower().strip()
        self._record_resonance(concept_key, pattern, level)
        self._persona.record_resonance(concept_key, pattern, level)

    # --- Internal methods ---

    def _select_lens(
        self,
        concept: str,
        lenses: list[PatternLens],
        preferred_pattern: str | None,
    ) -> PatternLens:
        """Pick the best lens for this user and concept."""
        # 1. If user explicitly requested a pattern
        if preferred_pattern:
            for lens in lenses:
                if lens.pattern == preferred_pattern:
                    return lens

        # 2. Check persona's preferred patterns from resonance history
        for pref_pattern in self._persona.preferred_patterns:
            for lens in lenses:
                if lens.pattern == pref_pattern:
                    return lens

        # 3. Match by cognitive style
        style_pattern_map = {
            "visual": ["spatial", "color"],
            "narrative": ["flow", "cause", "time"],
            "analytical": ["deviation", "repetition", "combination"],
            "kinesthetic": ["rhythm", "flow"],
        }
        style_patterns = style_pattern_map.get(
            self._persona.cognitive_style.value, []
        )
        for sp in style_patterns:
            for lens in lenses:
                if lens.pattern == sp:
                    return lens

        # 4. Default: first lens
        return lenses[0]

    def _record_resonance(
        self, concept: str, pattern: str, level: ResonanceLevel
    ) -> None:
        """Record resonance for a concept-pattern pair."""
        if concept not in self._resonance_map:
            self._resonance_map[concept] = {}
        self._resonance_map[concept][pattern] = level

    def _explain_selection(
        self, lens: PatternLens, preferred: str | None
    ) -> str:
        """Brief note explaining why this lens was chosen."""
        if preferred:
            return f"Using '{lens.pattern}' pattern as you requested."
        if lens.pattern in self._persona.preferred_patterns:
            return f"Using '{lens.pattern}' — it resonated with you before."
        return f"Trying '{lens.pattern}' pattern based on your cognitive style."

    def _fuzzy_lookup(self, concept: str) -> list[PatternLens] | None:
        """Try to find lenses for a concept using partial matching."""
        for key in _CONCEPT_LENSES:
            if concept in key or key in concept:
                return _CONCEPT_LENSES[key]
        return None
