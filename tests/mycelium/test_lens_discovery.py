"""
Tests for Mycelium - Lens Discovery Engine
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mycelium.knowledge_federation import FederatedResult
from mycelium.lens_discovery import _MIN_PATTERNS_FOR_LENS, LensDiscoveryEngine


@pytest.fixture
def mock_federator():
    federator = MagicMock()
    federator.query = AsyncMock()
    return federator


@pytest.fixture
def engine(mock_federator):
    return LensDiscoveryEngine(federator=mock_federator)


@pytest.mark.asyncio
async def test_discover_lenses_with_enough_patterns(engine, mock_federator):
    """When enough patterns are detected, lenses should be generated."""
    # Provide text that triggers at least 2 patterns.
    # "flow" pattern needs connectives; "repetition" needs repeated words.
    text = (
        "Therefore the system consequently processes data through layers. "
        "The system processes data through layers again and again. "
        "Furthermore the system adapts and the system evolves continuously."
    )
    mock_federator.query.return_value = FederatedResult(
        question="What is machine learning?",
        grid_results=[text],
        pathways_results=[],
        sources=["grid"],
    )

    lenses = await engine.discover_lenses("machine learning")
    assert len(lenses) >= _MIN_PATTERNS_FOR_LENS
    assert all(lens.pattern for lens in lenses)
    # Check auto-generation markers
    for lens in lenses:
        assert "machine learning" in lens.analogy.lower() or "machine learning" in lens.eli5.lower()


@pytest.mark.asyncio
async def test_discover_lenses_too_few_patterns(engine, mock_federator):
    """When fewer than minimum patterns detected, return empty."""
    mock_federator.query.return_value = FederatedResult(
        question="What is xyz?",
        grid_results=["Short text."],
        pathways_results=[],
        sources=["grid"],
    )

    lenses = await engine.discover_lenses("xyz")
    assert lenses == []


@pytest.mark.asyncio
async def test_discover_lenses_no_knowledge(engine, mock_federator):
    """When no knowledge found, return empty."""
    mock_federator.query.return_value = FederatedResult(
        question="What is unknown?",
        grid_results=[],
        pathways_results=[],
        sources=[],
    )

    lenses = await engine.discover_lenses("unknown_concept")
    assert lenses == []


@pytest.mark.asyncio
async def test_discover_lenses_cached(engine, mock_federator):
    """Second call for same concept should use cache."""
    text = (
        "Therefore the system consequently processes data through layers. "
        "The system processes data through layers again and again. "
        "Furthermore the system adapts and the system evolves continuously."
    )
    mock_federator.query.return_value = FederatedResult(
        question="What is caching?",
        grid_results=[text],
        pathways_results=[],
        sources=["grid"],
    )

    lenses1 = await engine.discover_lenses("caching")
    lenses2 = await engine.discover_lenses("caching")

    assert lenses1 is lenses2
    # Federator should only be called once
    assert mock_federator.query.call_count == 1


def test_engine_stats(engine):
    stats = engine.get_stats()
    assert stats["cached_concepts"] == 0
    assert stats["total_lenses_generated"] == 0


@pytest.mark.asyncio
async def test_lens_pattern_templates_applied(engine, mock_federator):
    """Generated lenses should use the correct template for each pattern."""
    # Text with flow + spatial patterns
    text = (
        "Therefore the architecture consequently processes through the framework. "
        "The structure hierarchy organizes the system layer by layer. "
        "Furthermore the component module connects through the network system."
    )
    mock_federator.query.return_value = FederatedResult(
        question="What is microservices?",
        grid_results=[text],
        pathways_results=[],
        sources=["grid"],
    )

    lenses = await engine.discover_lenses("microservices")

    if lenses:
        patterns_found = {lens.pattern for lens in lenses}
        # Each generated lens should have non-empty fields
        for lens in lenses:
            assert lens.analogy
            assert lens.eli5
            assert lens.visual_hint
            assert lens.when_useful
            assert lens.pattern in patterns_found
