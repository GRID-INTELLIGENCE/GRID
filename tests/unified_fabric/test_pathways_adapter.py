"""
Tests for Unified Fabric - Pathways Integration Adapter
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from unified_fabric.pathways_adapter import (
    PathwaysIntegrationAdapter,
    ResonanceSignal,
    get_pathways_adapter,
    init_pathways_adapter,
)


@pytest.fixture
def mock_safety_bridge():
    bridge = MagicMock()
    report = MagicMock()
    report.should_block = False
    report.violations = []
    bridge.validate = AsyncMock(return_value=report)
    return bridge


@pytest.fixture
def mock_event_bus():
    bus = MagicMock()
    bus.publish = AsyncMock()
    bus.subscribe = MagicMock()
    return bus


@pytest.fixture
def adapter(mock_safety_bridge, mock_event_bus):
    with (
        patch(
            "unified_fabric.pathways_adapter.get_safety_bridge",
            return_value=mock_safety_bridge,
        ),
        patch("unified_fabric.pathways_adapter.get_event_bus", return_value=mock_event_bus),
    ):
        return PathwaysIntegrationAdapter()


def test_resonance_signal_creation():
    signal = ResonanceSignal(
        trigger_content="learning about fractals",
        resonating_content="self-similar patterns in nature",
        connection_strength=0.72,
        semantic_similarity=0.65,
        emotional_amplification=0.3,
    )
    assert signal.connection_strength == 0.72
    assert signal.semantic_similarity == 0.65
    assert signal.signal_id.startswith("res_")


def test_resonance_signal_defaults():
    signal = ResonanceSignal(
        trigger_content="test",
        resonating_content="test2",
        connection_strength=0.5,
    )
    assert signal.semantic_similarity == 0.0
    assert signal.emotional_amplification == 0.0
    assert signal.metadata == {}


@pytest.mark.asyncio
async def test_adapter_initialize(adapter, mock_event_bus):
    await adapter.initialize()
    assert adapter._initialized is True
    # Should subscribe to resonance and knowledge events
    assert mock_event_bus.subscribe.call_count == 2


@pytest.mark.asyncio
async def test_adapter_initialize_idempotent(adapter, mock_event_bus):
    await adapter.initialize()
    await adapter.initialize()
    # Subscribe should only be called once (2 subscriptions on first init)
    assert mock_event_bus.subscribe.call_count == 2


@pytest.mark.asyncio
async def test_process_resonance_success(adapter, mock_event_bus):
    signal = ResonanceSignal(
        trigger_content="quantum mechanics",
        resonating_content="wave-particle duality",
        connection_strength=0.85,
        semantic_similarity=0.78,
    )
    result = await adapter.process_resonance(signal)
    assert result is True
    mock_event_bus.publish.assert_called_once()

    # Check the published event
    event = mock_event_bus.publish.call_args[0][0]
    assert event.event_type == "pathways.resonance.detected"
    assert event.payload["connection_strength"] == 0.85
    assert event.source_domain == "pathways"


@pytest.mark.asyncio
async def test_process_resonance_uses_pathways_system_when_no_trusted_user_id(adapter, mock_safety_bridge):
    """Default: SafetyContext.user_id is pathways-system, never from signal.metadata."""
    signal = ResonanceSignal(
        trigger_content="test",
        resonating_content="test",
        connection_strength=0.5,
        metadata={"user_id": "spoofed-user"},
    )
    await adapter.process_resonance(signal)
    mock_safety_bridge.validate.assert_called_once()
    call_args = mock_safety_bridge.validate.call_args
    ctx = call_args[0][1]
    assert ctx.user_id == "pathways-system"


@pytest.mark.asyncio
async def test_process_resonance_uses_trusted_user_id_when_provided(adapter, mock_safety_bridge):
    """When trusted_user_id is passed by caller, it is used for safety/audit."""
    signal = ResonanceSignal(
        trigger_content="test",
        resonating_content="test",
        connection_strength=0.5,
    )
    await adapter.process_resonance(signal, trusted_user_id="auth-user-123")
    mock_safety_bridge.validate.assert_called_once()
    call_args = mock_safety_bridge.validate.call_args
    ctx = call_args[0][1]
    assert ctx.user_id == "auth-user-123"


@pytest.mark.asyncio
async def test_process_resonance_blocked_by_safety(adapter, mock_safety_bridge):
    mock_safety_bridge.validate.return_value.should_block = True
    signal = ResonanceSignal(
        trigger_content="blocked",
        resonating_content="blocked",
        connection_strength=0.5,
    )
    result = await adapter.process_resonance(signal)
    assert result is False


@pytest.mark.asyncio
async def test_process_resonance_calls_handlers(adapter):
    handler = AsyncMock()
    adapter.register_signal_handler(handler)

    signal = ResonanceSignal(
        trigger_content="test",
        resonating_content="test",
        connection_strength=0.5,
    )
    await adapter.process_resonance(signal)
    handler.assert_called_once_with(signal)


def test_singleton_pattern():
    # Reset singleton for test isolation
    import unified_fabric.pathways_adapter as mod

    mod._pathways_adapter = None
    a1 = get_pathways_adapter()
    a2 = get_pathways_adapter()
    assert a1 is a2
    mod._pathways_adapter = None  # cleanup
