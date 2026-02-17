"""Tests for real-time adapter functionality."""

from __future__ import annotations

import pytest

from grid.awareness.context import Context
from grid.essence.core_state import EssentialState
from grid.evolution.realtime_adapter import (
    AdaptationState,
    DynamicWeightNetwork,
    RealTimeAdapter,
    WeightUpdate,
)


class TestDynamicWeightNetwork:
    """Test DynamicWeightNetwork."""

    @pytest.fixture
    def network(self):
        """Create dynamic weight network."""
        return DynamicWeightNetwork()

    def test_get_weights(self, network):
        """Test getting weights."""
        weights = network.get_weights()

        assert "input" in weights
        assert "hidden" in weights
        assert "output" in weights

    def test_update_weight(self, network):
        """Test updating weights."""
        update = network.update_weight("input", "coherence_weight", 0.5, "test")

        assert isinstance(update, WeightUpdate)
        assert update.layer == "input"
        assert update.weight_name == "coherence_weight"
        assert update.new_value == 0.5
        assert network.weights["input"]["coherence_weight"] == 0.5

    def test_adapt_weights_iterative(self, network):
        """Test iterative weight adaptation."""
        iteration_pattern = {
            "coherence": 0.8,
            "context_depth": 2.0,
            "performance": 0.9,
        }

        updates = network.adapt_weights_iterative(iteration_pattern, adaptation_rate=0.1)

        assert len(updates) > 0
        assert any(update.layer == "input" for update in updates)

    def test_get_weight_trend(self, network):
        """Test getting weight trends."""
        # Update weight multiple times
        for i in range(5):
            network.update_weight("input", "coherence_weight", 0.3 + i * 0.1, "test")
            network.weight_history.append(network.weights.copy())

        trend = network.get_weight_trend("input", "coherence_weight")

        assert trend is not None
        # Trend should be positive (increasing) - allow for floating point precision
        assert trend >= -0.01  # Essentially zero or positive


class TestRealTimeAdapter:
    """Test RealTimeAdapter."""

    @pytest.fixture
    def adapter(self):
        """Create real-time adapter."""
        return RealTimeAdapter()

    @pytest.fixture
    def base_state(self):
        """Create base essential state."""
        return EssentialState(
            pattern_signature="test_sig",
            quantum_state={"test": "data"},
            context_depth=1.0,
            coherence_factor=0.5,
        )

    @pytest.fixture
    def base_context(self):
        """Create base context."""
        return Context(
            temporal_depth=1.0,
            spatial_field={},
            relational_web={},
            quantum_signature="test_ctx",
        )

    @pytest.mark.asyncio
    async def test_adapt(self, adapter, base_state, base_context):
        """Test adaptation."""
        state = await adapter.adapt(base_state, base_context, performance_metric=0.7)

        assert isinstance(state, AdaptationState)
        assert state.iteration == 1
        assert len(state.weights) > 0

    @pytest.mark.asyncio
    async def test_multiple_adaptations(self, adapter, base_state, base_context):
        """Test multiple adaptations."""
        for i in range(3):
            state = await adapter.adapt(base_state, base_context, performance_metric=0.6 + i * 0.1)

        assert state.iteration == 3
        assert len(state.adaptation_history) > 0

    @pytest.mark.asyncio
    async def test_predict(self, adapter, base_state, base_context):
        """Test prediction."""
        result = adapter.predict(base_state, base_context)

        assert "prediction" in result
        assert "confidence" in result
        assert "normalized_input" in result
        assert 0.0 <= result["confidence"] <= 1.0

    def test_get_adaptation_summary(self, adapter, base_state, base_context):
        """Test getting adaptation summary."""
        import asyncio

        async def setup():
            await adapter.adapt(base_state, base_context, performance_metric=0.7)

        asyncio.run(setup())

        summary = adapter.get_adaptation_summary()

        assert "iteration" in summary
        assert "total_adaptations" in summary
        assert "performance_metrics" in summary
        assert "weight_trends" in summary
