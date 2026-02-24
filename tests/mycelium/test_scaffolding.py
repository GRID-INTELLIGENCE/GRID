"""Tests for Mycelium AdaptiveScaffold — dynamic content adaptation.

Grounded in thermodynamic efficiency: scaffolding adjusts output depth
like a heat engine adjusts work output based on temperature differential.

More scaffolding = more support = higher cognitive load reduction.
"""

from __future__ import annotations

import pytest

from mycelium.core import (
    Depth,
    ExpertiseLevel,
    Highlight,
    HighlightPriority,
    PersonaProfile,
    SynthesisResult,
)
from mycelium.scaffolding import AdaptiveScaffold, ScaffoldDepth, Strategy


def _make_result(gist: str = "Energy cannot be created or destroyed.", **kwargs) -> SynthesisResult:
    """Factory for test SynthesisResults."""
    defaults = dict(
        summary="The first law of thermodynamics states that energy is conserved. "
                "Phase transitions require energy input. "
                "Temperature remains constant during phase change.",
        explanation="Energy conservation is fundamental. During melting, 334 J/g is absorbed. "
                    "During boiling, 2260 J/g is absorbed. The energy breaks intermolecular bonds.",
        analogy="Think of energy like water in connected pools — it flows but never disappears.",
        highlights=[
            Highlight(text="energy", priority=HighlightPriority.CRITICAL, category="concept"),
            Highlight(text="thermodynamics", priority=HighlightPriority.HIGH, category="concept"),
            Highlight(text="conservation", priority=HighlightPriority.MEDIUM, category="concept"),
        ],
        source_length=500,
        compression_ratio=0.1,
        depth_used=Depth.AMERICANO,
        patterns_applied=["flow", "repetition"],
    )
    defaults.update(kwargs)
    return SynthesisResult(gist=gist, **defaults)


class TestAutoDepthDetection:
    """Depth auto-detection from persona — like selecting instrument
    resolution based on measurement requirements."""

    def test_child_gets_maximum_scaffolding(self) -> None:
        scaffold = AdaptiveScaffold(PersonaProfile(expertise=ExpertiseLevel.CHILD))
        assert scaffold._auto_detect_depth() == ScaffoldDepth.MAXIMUM

    def test_beginner_gets_full_scaffolding(self) -> None:
        scaffold = AdaptiveScaffold(PersonaProfile(expertise=ExpertiseLevel.BEGINNER))
        assert scaffold._auto_detect_depth() == ScaffoldDepth.FULL

    def test_familiar_gets_moderate_scaffolding(self) -> None:
        scaffold = AdaptiveScaffold(PersonaProfile(expertise=ExpertiseLevel.FAMILIAR))
        assert scaffold._auto_detect_depth() == ScaffoldDepth.MODERATE

    def test_proficient_gets_light_scaffolding(self) -> None:
        scaffold = AdaptiveScaffold(PersonaProfile(expertise=ExpertiseLevel.PROFICIENT))
        assert scaffold._auto_detect_depth() == ScaffoldDepth.LIGHT

    def test_expert_gets_no_scaffolding(self) -> None:
        scaffold = AdaptiveScaffold(PersonaProfile(expertise=ExpertiseLevel.EXPERT))
        assert scaffold._auto_detect_depth() == ScaffoldDepth.NONE

    def test_challenges_override_to_maximum(self) -> None:
        """Any accessibility challenge → maximum scaffolding, like maximum instrument sensitivity."""
        scaffold = AdaptiveScaffold(
            PersonaProfile(expertise=ExpertiseLevel.EXPERT, challenges=["dyslexia"])
        )
        assert scaffold._auto_detect_depth() == ScaffoldDepth.MAXIMUM


class TestStrategyApplication:
    """Strategy application — like signal processing pipeline stages."""

    def test_none_depth_applies_no_strategies(self) -> None:
        scaffold = AdaptiveScaffold(PersonaProfile(expertise=ExpertiseLevel.EXPERT))
        result = _make_result()
        output = scaffold.scaffold(result, depth=ScaffoldDepth.NONE)
        assert len(output.strategies_used) == 0

    def test_light_depth_applies_highlighting_and_summary_first(self) -> None:
        scaffold = AdaptiveScaffold()
        result = _make_result()
        output = scaffold.scaffold(result, depth=ScaffoldDepth.LIGHT)
        assert Strategy.HIGHLIGHTING in output.strategies_used
        assert Strategy.SUMMARY_FIRST in output.strategies_used

    def test_moderate_depth_adds_chunking_and_examples(self) -> None:
        scaffold = AdaptiveScaffold()
        result = _make_result()
        output = scaffold.scaffold(result, depth=ScaffoldDepth.MODERATE)
        assert Strategy.CHUNKING in output.strategies_used
        assert Strategy.EXAMPLES in output.strategies_used

    def test_full_depth_adds_step_by_step_and_analogy(self) -> None:
        scaffold = AdaptiveScaffold()
        result = _make_result()
        output = scaffold.scaffold(result, depth=ScaffoldDepth.FULL)
        assert Strategy.STEP_BY_STEP in output.strategies_used
        assert Strategy.ANALOGY in output.strategies_used

    def test_maximum_depth_adds_simplification_and_progressive(self) -> None:
        scaffold = AdaptiveScaffold()
        result = _make_result()
        output = scaffold.scaffold(result, depth=ScaffoldDepth.MAXIMUM)
        assert Strategy.SIMPLIFICATION in output.strategies_used
        assert Strategy.PROGRESSIVE in output.strategies_used

    def test_more_strategies_means_more_cognitive_reduction(self) -> None:
        """More strategies → higher load reduction — like more insulation → less heat loss."""
        scaffold = AdaptiveScaffold()
        result = _make_result()
        light = scaffold.scaffold(result, depth=ScaffoldDepth.LIGHT)
        maximum = scaffold.scaffold(result, depth=ScaffoldDepth.MAXIMUM)
        assert maximum.cognitive_reduction > light.cognitive_reduction


class TestOutputContent:
    """Output content verification — ensuring scaffolded output carries
    the essential information, like conservation laws in physics."""

    def test_summary_first_puts_gist_at_top(self) -> None:
        scaffold = AdaptiveScaffold()
        result = _make_result(gist="Energy is conserved.")
        output = scaffold.scaffold(result, depth=ScaffoldDepth.LIGHT)
        assert output.content.startswith("IN BRIEF: Energy is conserved.")

    def test_highlights_section_contains_keywords(self) -> None:
        scaffold = AdaptiveScaffold()
        result = _make_result()
        output = scaffold.scaffold(result, depth=ScaffoldDepth.MODERATE)
        assert "energy" in output.content.lower()

    def test_analogy_section_present_at_full_depth(self) -> None:
        scaffold = AdaptiveScaffold()
        result = _make_result()
        output = scaffold.scaffold(result, depth=ScaffoldDepth.FULL)
        assert "THINK OF IT LIKE" in output.content

    def test_step_by_step_has_numbered_steps(self) -> None:
        scaffold = AdaptiveScaffold()
        result = _make_result()
        output = scaffold.scaffold(result, depth=ScaffoldDepth.FULL)
        assert "1." in output.content
        assert "2." in output.content

    def test_simplification_replaces_complex_words(self) -> None:
        scaffold = AdaptiveScaffold()
        result = _make_result(
            explanation="We must utilize this methodology to facilitate comprehensive optimization."
        )
        output = scaffold.scaffold(result, depth=ScaffoldDepth.MAXIMUM)
        lower = output.content.lower()
        # "utilize" → "use", "methodology" → "method", "facilitate" → "help"
        assert "utilize" not in lower
        assert "methodology" not in lower

    def test_sections_list_populated(self) -> None:
        scaffold = AdaptiveScaffold()
        result = _make_result()
        output = scaffold.scaffold(result, depth=ScaffoldDepth.FULL)
        assert len(output.sections) >= 3  # at least gist, highlights, step-by-step


class TestFeedbackLoop:
    """Feedback loop — like a control system adjusting gain."""

    def test_too_complex_increases_depth(self, scaffold: AdaptiveScaffold) -> None:
        scaffold._depth_override = ScaffoldDepth.LIGHT
        new_depth = scaffold.feedback(too_complex=True)
        assert new_depth == ScaffoldDepth.MODERATE

    def test_too_simple_decreases_depth(self, scaffold: AdaptiveScaffold) -> None:
        scaffold._depth_override = ScaffoldDepth.MODERATE
        new_depth = scaffold.feedback(too_simple=True)
        assert new_depth == ScaffoldDepth.LIGHT

    def test_maximum_depth_cannot_increase_further(self, scaffold: AdaptiveScaffold) -> None:
        """Upper bound — like maximum entropy."""
        scaffold._depth_override = ScaffoldDepth.MAXIMUM
        new_depth = scaffold.feedback(too_complex=True)
        assert new_depth == ScaffoldDepth.MAXIMUM

    def test_none_depth_cannot_decrease_further(self, scaffold: AdaptiveScaffold) -> None:
        """Lower bound — like ground state energy."""
        scaffold._depth_override = ScaffoldDepth.NONE
        new_depth = scaffold.feedback(too_simple=True)
        assert new_depth == ScaffoldDepth.NONE

    def test_reset_clears_override(self, scaffold: AdaptiveScaffold) -> None:
        scaffold._depth_override = ScaffoldDepth.MAXIMUM
        scaffold.reset_depth()
        assert scaffold._depth_override is None
