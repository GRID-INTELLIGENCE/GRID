"""
Tests for PatternNavigator — discovery fallback via explore_with_discovery().
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from mycelium.navigator import NavigationResult, PatternLens, PatternNavigator


@pytest.fixture
def mock_discovery_engine():
    engine = MagicMock()
    engine.discover_lenses = AsyncMock(
        return_value=[
            PatternLens(
                pattern="flow",
                analogy="Like a river carrying blockchain from source to destination.",
                eli5="blockchain is like water flowing downhill.",
                visual_hint="Picture a stream.",
                when_useful="When you need to understand blockchain as a process.",
            ),
            PatternLens(
                pattern="spatial",
                analogy="Think of blockchain as a building with rooms.",
                eli5="blockchain is like a house.",
                visual_hint="Picture a blueprint.",
                when_useful="When you need to see how parts are organized.",
            ),
        ]
    )
    return engine


@pytest.fixture
def navigator(mock_discovery_engine):
    return PatternNavigator(discovery_engine=mock_discovery_engine)


def test_explore_known_concept_no_discovery(navigator, mock_discovery_engine):
    """Known concepts should not trigger discovery."""
    result = navigator.explore("cache")
    assert result is not None
    assert result.concept == "cache"
    mock_discovery_engine.discover_lenses.assert_not_called()


@pytest.mark.asyncio
async def test_explore_with_discovery_known(navigator, mock_discovery_engine):
    """explore_with_discovery should return immediately for known concepts."""
    result = await navigator.explore_with_discovery("cache")
    assert result is not None
    assert result.concept == "cache"
    mock_discovery_engine.discover_lenses.assert_not_called()


@pytest.mark.asyncio
async def test_explore_with_discovery_unknown(navigator, mock_discovery_engine):
    """explore_with_discovery should auto-discover for unknown concepts."""
    result = await navigator.explore_with_discovery("blockchain")
    assert result is not None
    assert result.concept == "blockchain"
    mock_discovery_engine.discover_lenses.assert_called_once_with("blockchain")


@pytest.mark.asyncio
async def test_explore_with_discovery_registers_concept(navigator, mock_discovery_engine):
    """After discovery, the concept should be registered for future sync explore()."""
    await navigator.explore_with_discovery("blockchain")

    # Now sync explore should work
    result = navigator.explore("blockchain")
    assert result is not None
    assert result.concept == "blockchain"


@pytest.mark.asyncio
async def test_explore_with_discovery_no_engine():
    """Without a discovery engine, unknown concepts return None."""
    nav = PatternNavigator(discovery_engine=None)
    result = await nav.explore_with_discovery("totally_unknown")
    assert result is None


@pytest.mark.asyncio
async def test_explore_with_discovery_empty_results():
    """When discovery finds nothing, return None."""
    engine = MagicMock()
    engine.discover_lenses = AsyncMock(return_value=[])
    nav = PatternNavigator(discovery_engine=engine)

    result = await nav.explore_with_discovery("empty_concept")
    assert result is None


@pytest.mark.asyncio
async def test_explore_with_discovery_error_handling():
    """Discovery errors should be handled gracefully."""
    engine = MagicMock()
    engine.discover_lenses = AsyncMock(side_effect=RuntimeError("network error"))
    nav = PatternNavigator(discovery_engine=engine)

    result = await nav.explore_with_discovery("error_concept")
    assert result is None


@pytest.mark.asyncio
async def test_explore_with_discovery_preferred_pattern(navigator, mock_discovery_engine):
    """Preferred pattern should be respected after discovery."""
    result = await navigator.explore_with_discovery("blockchain", preferred_pattern="spatial")
    assert result is not None
    assert result.lens.pattern == "spatial"
