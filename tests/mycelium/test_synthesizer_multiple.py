"""
Tests for Synthesizer.synthesize_multiple() — cross-corpus synthesis.
"""

import pytest

from mycelium.core import PersonaProfile
from mycelium.synthesizer import Synthesizer


@pytest.fixture
def synthesizer():
    return Synthesizer()


def test_synthesize_multiple_empty(synthesizer):
    result = synthesizer.synthesize_multiple([])
    assert result.gist == "(no content to synthesize)"
    assert result.source_length == 0


def test_synthesize_multiple_single_text(synthesizer):
    result = synthesizer.synthesize_multiple(
        ["The quick brown fox jumps over the lazy dog. This is a simple test sentence."]
    )
    assert result.gist
    assert result.source_length > 0


def test_synthesize_multiple_combines_sources(synthesizer):
    texts = [
        "[GRID] Machine learning is a subset of artificial intelligence. It enables computers to learn from data.",
        "[Pathways] Neural networks are inspired by biological brains. They process information through layers.",
    ]
    result = synthesizer.synthesize_multiple(texts)
    assert result.gist
    assert result.source_length > 0
    # Combined text should be longer than either individual text
    assert result.source_length > len(texts[0])


def test_synthesize_multiple_with_persona(synthesizer):
    """Persona override should be used and then restored."""
    original_persona = synthesizer.persona
    custom_persona = PersonaProfile(expertise="expert")

    texts = ["Complex systems theory describes emergent behavior in interconnected networks."]
    result = synthesizer.synthesize_multiple(texts, persona=custom_persona)

    assert result.gist
    # Original persona should be restored
    assert synthesizer.persona is original_persona


def test_synthesize_multiple_pattern_detection(synthesizer):
    """Patterns that appear across combined texts should be detected."""
    texts = [
        "[GRID] Therefore the system consequently processes data through multiple stages. "
        "Furthermore the architecture enables efficient data flow through the pipeline.",
        "[Pathways] The structure hierarchy organizes components within the framework. "
        "The module system layer connects to the network architecture.",
    ]
    result = synthesizer.synthesize_multiple(texts)
    # With connectives and structural words, we expect flow and/or spatial patterns
    assert result.patterns_applied  # at least some patterns detected
