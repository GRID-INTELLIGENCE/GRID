"""Personality engine for adaptive agent behavior.

Provides rule pack selection based on mood and consent signals
for personality-aware agent interactions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Mood(Enum):
    """Agent mood states affecting rule selection."""

    FOCUSED = "focused"  # Task-oriented, minimal elaboration
    COLLABORATIVE = "collaborative"  # Open to discussion, helpful
    CAUTIOUS = "cautious"  # Extra validation, conservative
    CREATIVE = "creative"  # More exploratory, flexible
    SUPPORTIVE = "supportive"  # Empathetic, user-centered


class ConsentLevel(Enum):
    """User consent levels for agent autonomy."""

    FULL = "full"  # Agent can act autonomously
    PARTIAL = "partial"  # Agent asks before significant actions
    MINIMAL = "minimal"  # Agent only responds, no proactive actions
    RESTRICTED = "restricted"  # Agent operates in read-only mode


@dataclass(frozen=True, slots=True)
class RulePack:
    """A collection of behavioral rules for agent interactions."""

    id: str
    name: str
    description: str
    rules: tuple[str, ...]
    allowed_actions: frozenset[str]
    forbidden_actions: frozenset[str]
    tone_modifiers: tuple[str, ...]
    autonomy_level: float  # 0.0 = fully restricted, 1.0 = fully autonomous

    def allows_action(self, action: str) -> bool:
        """Check if an action is allowed by this rule pack."""
        if action in self.forbidden_actions:
            return False
        if self.allowed_actions and action not in self.allowed_actions:
            return False
        return True


# Predefined rule packs
_RULE_PACKS: dict[str, RulePack] = {
    "focused_full": RulePack(
        id="focused_full",
        name="Focused Autonomous",
        description="Task-oriented with full autonomy",
        rules=(
            "Prioritize task completion",
            "Minimize elaboration",
            "Execute without confirmation for standard operations",
        ),
        allowed_actions=frozenset(),  # All allowed
        forbidden_actions=frozenset({"destructive_delete", "external_api_call_unverified"}),
        tone_modifiers=("concise", "direct"),
        autonomy_level=0.9,
    ),
    "focused_partial": RulePack(
        id="focused_partial",
        name="Focused Guided",
        description="Task-oriented with guided autonomy",
        rules=(
            "Prioritize task completion",
            "Confirm before multi-step operations",
            "Report progress at checkpoints",
        ),
        allowed_actions=frozenset(),
        forbidden_actions=frozenset({"destructive_delete", "external_api_call_unverified", "batch_modify"}),
        tone_modifiers=("concise", "informative"),
        autonomy_level=0.6,
    ),
    "collaborative_full": RulePack(
        id="collaborative_full",
        name="Collaborative Partner",
        description="Open collaboration with full autonomy",
        rules=(
            "Explain reasoning when asked",
            "Offer alternatives when appropriate",
            "Proactively suggest improvements",
        ),
        allowed_actions=frozenset(),
        forbidden_actions=frozenset({"destructive_delete"}),
        tone_modifiers=("friendly", "explanatory"),
        autonomy_level=0.85,
    ),
    "collaborative_partial": RulePack(
        id="collaborative_partial",
        name="Collaborative Assistant",
        description="Helpful collaboration with confirmation",
        rules=(
            "Explain reasoning for decisions",
            "Ask before significant changes",
            "Provide options rather than single solutions",
        ),
        allowed_actions=frozenset(),
        forbidden_actions=frozenset({"destructive_delete", "external_api_call_unverified"}),
        tone_modifiers=("friendly", "consultative"),
        autonomy_level=0.5,
    ),
    "cautious_minimal": RulePack(
        id="cautious_minimal",
        name="Cautious Observer",
        description="Conservative mode with minimal intervention",
        rules=(
            "Validate all inputs thoroughly",
            "Prefer read operations over write",
            "Request explicit confirmation for all changes",
        ),
        allowed_actions=frozenset({"read", "analyze", "suggest", "explain"}),
        forbidden_actions=frozenset({"write", "delete", "modify", "execute"}),
        tone_modifiers=("careful", "thorough"),
        autonomy_level=0.2,
    ),
    "cautious_restricted": RulePack(
        id="cautious_restricted",
        name="Read-Only Advisor",
        description="Pure advisory mode, no actions",
        rules=(
            "Analyze and advise only",
            "No modifications permitted",
            "Document observations thoroughly",
        ),
        allowed_actions=frozenset({"read", "analyze", "explain"}),
        forbidden_actions=frozenset({"write", "delete", "modify", "execute", "suggest"}),
        tone_modifiers=("observational", "detailed"),
        autonomy_level=0.0,
    ),
    "creative_full": RulePack(
        id="creative_full",
        name="Creative Explorer",
        description="Exploratory mode with full autonomy",
        rules=(
            "Explore alternative approaches",
            "Experiment with novel solutions",
            "Document discoveries",
        ),
        allowed_actions=frozenset(),
        forbidden_actions=frozenset({"destructive_delete"}),
        tone_modifiers=("curious", "innovative"),
        autonomy_level=0.95,
    ),
    "supportive_partial": RulePack(
        id="supportive_partial",
        name="Supportive Guide",
        description="User-centered support with guided autonomy",
        rules=(
            "Prioritize user understanding",
            "Offer step-by-step guidance",
            "Check user comfort before proceeding",
        ),
        allowed_actions=frozenset(),
        forbidden_actions=frozenset({"destructive_delete", "batch_modify"}),
        tone_modifiers=("empathetic", "patient", "encouraging"),
        autonomy_level=0.4,
    ),
}


@dataclass(slots=True)
class PersonalityState:
    """Current personality state of the agent."""

    current_mood: Mood
    consent_level: ConsentLevel
    active_rule_pack: RulePack
    overrides: dict[str, Any] = field(default_factory=dict)
    history: list[str] = field(default_factory=list)

    def record_transition(self, from_pack: str, to_pack: str, reason: str) -> None:
        """Record a rule pack transition."""
        self.history.append(f"{from_pack} -> {to_pack}: {reason}")


class PersonalityEngine:
    """Engine for managing agent personality and rule selection."""

    def __init__(self, *, default_mood: Mood = Mood.COLLABORATIVE) -> None:
        """Initialize the personality engine.

        Args:
            default_mood: Default mood when not explicitly set.
        """
        self.default_mood = default_mood
        self._state: PersonalityState | None = None

    def select_rule_pack(
        self,
        mood: Mood | str,
        consent: ConsentLevel | str,
    ) -> RulePack:
        """Select appropriate rule pack based on mood and consent.

        Args:
            mood: Current agent mood (Mood enum or string).
            consent: User consent level (ConsentLevel enum or string).

        Returns:
            RulePack matching the mood/consent combination.

        Example:
            >>> engine = PersonalityEngine()
            >>> pack = engine.select_rule_pack(Mood.FOCUSED, ConsentLevel.FULL)
            >>> pack.name
            'Focused Autonomous'
        """
        # Normalize inputs
        if isinstance(mood, str):
            mood = Mood(mood.lower())
        if isinstance(consent, str):
            consent = ConsentLevel(consent.lower())

        # Build pack key
        pack_key = self._resolve_pack_key(mood, consent)

        # Get or fallback
        rule_pack = _RULE_PACKS.get(pack_key)
        if not rule_pack:
            # Fallback to closest match
            rule_pack = self._fallback_pack(mood, consent)

        # Update state
        if self._state:
            old_pack_id = self._state.active_rule_pack.id
            self._state.active_rule_pack = rule_pack
            self._state.current_mood = mood
            self._state.consent_level = consent
            self._state.record_transition(old_pack_id, rule_pack.id, "mood/consent change")
        else:
            self._state = PersonalityState(
                current_mood=mood,
                consent_level=consent,
                active_rule_pack=rule_pack,
            )

        return rule_pack

    def _resolve_pack_key(self, mood: Mood, consent: ConsentLevel) -> str:
        """Resolve mood + consent to pack key."""
        # Map consent levels to key suffixes
        consent_map = {
            ConsentLevel.FULL: "full",
            ConsentLevel.PARTIAL: "partial",
            ConsentLevel.MINIMAL: "minimal",
            ConsentLevel.RESTRICTED: "restricted",
        }
        return f"{mood.value}_{consent_map[consent]}"

    def _fallback_pack(self, mood: Mood, consent: ConsentLevel) -> RulePack:
        """Find closest matching pack when exact match unavailable."""
        # Priority: match consent first, then mood
        consent_suffix = consent.value
        for pack_id, pack in _RULE_PACKS.items():
            if consent_suffix in pack_id:
                return pack

        # Ultimate fallback
        return _RULE_PACKS["collaborative_partial"]

    def get_state(self) -> PersonalityState | None:
        """Get current personality state."""
        return self._state

    def get_available_packs(self) -> list[str]:
        """Get list of available rule pack IDs."""
        return list(_RULE_PACKS.keys())

    def get_pack_by_id(self, pack_id: str) -> RulePack | None:
        """Get a specific rule pack by ID."""
        return _RULE_PACKS.get(pack_id)


# Module-level convenience function
def select_rule_pack(mood: Mood | str, consent: ConsentLevel | str) -> RulePack:
    """Select a rule pack based on mood and consent.

    Convenience function using a shared engine instance.

    Args:
        mood: Current agent mood.
        consent: User consent level.

    Returns:
        Appropriate RulePack for the mood/consent combination.
    """
    engine = PersonalityEngine()
    return engine.select_rule_pack(mood, consent)
