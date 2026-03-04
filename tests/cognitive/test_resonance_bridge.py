"""
Tests for Cognitive - Resonance Bridge
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cognitive.pattern_manager import AdvancedPatternManager
from cognitive.resonance_bridge import ResonanceBridge
from unified_fabric import Event


@pytest.fixture
def pattern_manager():
    pm = AdvancedPatternManager()
    pm.register_pattern("flow_1", "Flow Pattern", "flow", initial_confidence=0.5)
    pm.register_pattern("spatial_1", "Spatial Pattern", "spatial", initial_confidence=0.4)
    return pm


@pytest.fixture
def mock_event_bus():
    bus = MagicMock()
    bus.subscribe = MagicMock()
    return bus


@pytest.fixture
def bridge(pattern_manager, mock_event_bus):
    with patch("cognitive.resonance_bridge.get_event_bus", return_value=mock_event_bus):
        return ResonanceBridge(pattern_manager)


@pytest.mark.asyncio
async def test_bridge_initialize(bridge, mock_event_bus):
    await bridge.initialize()
    assert bridge._initialized is True
    mock_event_bus.subscribe.assert_called_once()
    call_args = mock_event_bus.subscribe.call_args
    assert call_args[0][0] == "pathways.resonance.*"


@pytest.mark.asyncio
async def test_bridge_initialize_idempotent(bridge, mock_event_bus):
    await bridge.initialize()
    await bridge.initialize()
    assert mock_event_bus.subscribe.call_count == 1


@pytest.mark.asyncio
async def test_on_resonance_event_updates_patterns(bridge, pattern_manager):
    event = Event(
        event_type="pathways.resonance.detected",
        payload={
            "trigger_content": "machine learning",
            "resonating_content": "neural networks",
            "connection_strength": 0.8,
            "semantic_similarity": 0.75,
            "emotional_amplification": 0.2,
        },
        source_domain="pathways",
    )

    initial_flow_confidence = pattern_manager.get_pattern_model("flow_1").confidence
    initial_spatial_confidence = pattern_manager.get_pattern_model("spatial_1").confidence

    await bridge._on_resonance_event(event)

    # Both patterns should have increased confidence
    flow_model = pattern_manager.get_pattern_model("flow_1")
    spatial_model = pattern_manager.get_pattern_model("spatial_1")
    assert flow_model.confidence > initial_flow_confidence
    assert spatial_model.confidence > initial_spatial_confidence
    assert bridge.events_processed == 1


@pytest.mark.asyncio
async def test_on_resonance_event_records_history(bridge, pattern_manager):
    event = Event(
        event_type="pathways.resonance.detected",
        payload={
            "trigger_content": "data structures",
            "resonating_content": "trees and graphs",
            "connection_strength": 0.6,
            "semantic_similarity": 0.5,
            "emotional_amplification": 0.1,
        },
        source_domain="pathways",
    )

    await bridge._on_resonance_event(event)

    flow_model = pattern_manager.get_pattern_model("flow_1")
    assert len(flow_model.resonance_history) == 1
    entry = flow_model.resonance_history[0]
    assert entry["connection_strength"] == 0.6
    assert entry["semantic_similarity"] == 0.5


@pytest.mark.asyncio
async def test_gradient_confidence_proportional(bridge, pattern_manager):
    """Stronger connection_strength should produce larger confidence change."""
    # Weak signal
    weak_event = Event(
        event_type="pathways.resonance.detected",
        payload={
            "trigger_content": "a",
            "resonating_content": "b",
            "connection_strength": 0.2,
            "semantic_similarity": 0.1,
            "emotional_amplification": 0.0,
        },
        source_domain="pathways",
    )

    flow_before = pattern_manager.get_pattern_model("flow_1").confidence
    await bridge._on_resonance_event(weak_event)
    flow_after_weak = pattern_manager.get_pattern_model("flow_1").confidence
    weak_delta = flow_after_weak - flow_before

    # Reset
    pattern_manager.get_pattern_model("flow_1").confidence = flow_before

    # Strong signal
    strong_event = Event(
        event_type="pathways.resonance.detected",
        payload={
            "trigger_content": "a",
            "resonating_content": "b",
            "connection_strength": 0.9,
            "semantic_similarity": 0.8,
            "emotional_amplification": 0.5,
        },
        source_domain="pathways",
    )

    await bridge._on_resonance_event(strong_event)
    flow_after_strong = pattern_manager.get_pattern_model("flow_1").confidence
    strong_delta = flow_after_strong - flow_before

    assert strong_delta > weak_delta


def test_bridge_stats(bridge):
    stats = bridge.get_stats()
    assert stats["initialized"] is False
    assert stats["events_processed"] == 0
    assert stats["pattern_count"] == 2
