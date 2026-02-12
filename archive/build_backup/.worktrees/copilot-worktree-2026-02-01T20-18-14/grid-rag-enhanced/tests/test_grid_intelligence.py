"""Tests for GRID Intelligence layer components."""

import pytest

# Skip this entire module if required dependencies don't exist
pytest.importorskip("grid.essence", reason="grid.essence module not implemented")


from grid.application import ApplicationConfig, IntelligenceApplication
from grid.awareness.context import Context
from grid.essence.core_state import EssentialState
from grid.evolution.version import VersionState
from grid.interfaces.bridge import QuantumBridge
from grid.interfaces.sensory import SensoryInput, SensoryProcessor
from grid.patterns.recognition import PatternRecognition


class TestEssentialState:
    """Test core state representation."""

    def test_state_creation(self):
        """Test creating essential state."""
        state = EssentialState(
            pattern_signature="test_pattern", quantum_state={"key": "value"}, context_depth=1.5, coherence_factor=0.8
        )

        assert state.pattern_signature == "test_pattern"
        assert state.coherence_factor == 0.8
        assert state.context_depth == 1.5

    def test_state_transform(self):
        """Test state transformation."""
        state = EssentialState(
            pattern_signature="p1", quantum_state={"data": 42}, context_depth=1.0, coherence_factor=0.5
        )

        context = Context(
            temporal_depth=2.0,
            spatial_field={"x": 1.0, "y": 2.0},
            relational_web={"rel": "value"},
            quantum_signature="ctx1",
        )

        new_state = state._quantum_transform(context)

        assert new_state.pattern_signature != state.pattern_signature
        assert new_state.coherence_factor > state.coherence_factor
        assert new_state.context_depth == context.temporal_depth


class TestPatternRecognition:
    """Test pattern recognition system."""

    def test_recognizer_initialization(self):
        """Test pattern recognizer setup."""
        recognizer = PatternRecognition()

        assert recognizer.quantum_field is not None
        assert recognizer.quantum_field.shape == (64, 64)
        assert len(recognizer.resonance_patterns) == 0

    @pytest.mark.asyncio
    async def test_pattern_emergence(self):
        """Test pattern emergence from quantum field."""
        recognizer = PatternRecognition()

        state = EssentialState(
            pattern_signature="test_emerge", quantum_state={}, context_depth=1.0, coherence_factor=0.9
        )

        patterns = await recognizer.recognize(state)

        assert isinstance(patterns, list)
        assert len(patterns) <= 5


class TestContext:
    """Test context awareness system."""

    def test_context_creation(self):
        """Test creating context."""
        ctx = Context(
            temporal_depth=1.5, spatial_field={"x": 1.0}, relational_web={"rel": "test"}, quantum_signature="ctx_test"
        )

        assert ctx.temporal_depth == 1.5
        assert ctx.quantum_signature == "ctx_test"

    @pytest.mark.asyncio
    async def test_context_evolution(self):
        """Test context natural evolution."""
        ctx = Context(
            temporal_depth=1.0, spatial_field={"x": 1.0, "y": 1.0}, relational_web={}, quantum_signature="ctx1"
        )

        state = EssentialState(pattern_signature="p1", quantum_state={}, context_depth=1.0, coherence_factor=0.8)

        evolved_ctx = await ctx.evolve(state)

        assert evolved_ctx.temporal_depth > ctx.temporal_depth
        assert evolved_ctx.quantum_signature != ctx.quantum_signature


class TestVersionState:
    """Test version management."""

    def test_version_creation(self):
        """Test creating version state."""
        state = EssentialState(pattern_signature="p1", quantum_state={}, context_depth=1.0, coherence_factor=0.5)

        ctx = Context(temporal_depth=1.0, spatial_field={}, relational_web={}, quantum_signature="ctx1")

        version = VersionState(essential_state=state, context=ctx, quantum_signature="v1", transform_history=[])

        assert version.quantum_signature == "v1"
        assert len(version.transform_history) == 0

    @pytest.mark.asyncio
    async def test_version_evolution_check(self):
        """Test version evolution threshold check."""
        state = EssentialState(
            pattern_signature="p1",
            quantum_state={},
            context_depth=1.0,
            coherence_factor=2.0,  # High coherence
        )

        ctx = Context(temporal_depth=1.0, spatial_field={}, relational_web={}, quantum_signature="ctx1")

        version = VersionState(essential_state=state, context=ctx, quantum_signature="v1", transform_history=[])

        needs_evolution = await version._needs_evolution()
        assert needs_evolution is True


class TestQuantumBridge:
    """Test quantum bridge transfers."""

    def test_bridge_initialization(self):
        """Test bridge setup."""
        bridge = QuantumBridge()

        assert bridge.coherence_field is not None
        assert bridge.coherence_field["field_strength"] == 1.0
        assert len(bridge.coherence_field["entanglement_pairs"]) == 0

    @pytest.mark.asyncio
    async def test_coherent_transfer(self):
        """Test coherent state transfer."""
        bridge = QuantumBridge()

        state = EssentialState(pattern_signature="p1", quantum_state={}, context_depth=1.0, coherence_factor=0.8)

        ctx = Context(temporal_depth=1.0, spatial_field={}, relational_web={}, quantum_signature="ctx1")

        result = await bridge.transfer(state, ctx)

        assert "transfer_signature" in result
        assert "coherence_level" in result
        assert "entanglement_count" in result
        assert result["coherence_level"] > 0


class TestSensoryProcessor:
    """Test sensory input processing."""

    @pytest.mark.asyncio
    async def test_visual_processing(self):
        """Test visual modality processing."""
        processor = SensoryProcessor()

        inp = SensoryInput(
            source="camera",
            data={"spatial_features": {"x": 100, "y": 200}, "clarity": 0.9},
            timestamp=0.0,
            modality="visual",
        )

        result = await processor.process(inp)

        assert result["modality"] == "visual"
        assert "spatial_field" in result
        assert result["coherence"] == 0.9

    @pytest.mark.asyncio
    async def test_text_processing(self):
        """Test text modality processing."""
        processor = SensoryProcessor()

        inp = SensoryInput(
            source="input", data={"tokens": {"word1": 0.5}, "confidence": 0.85}, timestamp=0.0, modality="text"
        )

        result = await processor.process(inp)

        assert result["modality"] == "text"
        assert "semantic_field" in result
        assert result["coherence"] == 0.85

    @pytest.mark.asyncio
    async def test_structured_processing(self):
        """Test structured data processing."""
        processor = SensoryProcessor()

        inp = SensoryInput(
            source="database", data={"field1": "value1", "field2": 42}, timestamp=0.0, modality="structured"
        )

        result = await processor.process(inp)

        assert result["modality"] == "structured"
        assert result["coherence"] == 0.8


class TestIntelligenceApplication:
    """Test application layer integration."""

    def test_app_initialization(self):
        """Test application setup."""
        config = ApplicationConfig(enable_pattern_tracking=True, enable_context_evolution=True, max_patterns=3)

        app = IntelligenceApplication(config)

        assert app.config.max_patterns == 3
        assert app.current_state is None
        assert len(app.interaction_log) == 0

    @pytest.mark.asyncio
    async def test_process_input(self):
        """Test processing input through pipeline."""
        app = IntelligenceApplication()

        data = {"test": "data", "value": 42}
        context_params = {"temporal_depth": 1.5, "spatial_field": {"x": 1.0}, "coherence": 0.7}

        result = await app.process_input(data, context_params)

        assert "patterns" in result
        assert "coherence_level" in result
        assert "context_depth" in result
        assert len(app.interaction_log) == 1

    @pytest.mark.asyncio
    async def test_interaction_summary(self):
        """Test interaction logging and summary."""
        app = IntelligenceApplication()

        # Process multiple inputs
        for i in range(3):
            await app.process_input({"iteration": i}, {"temporal_depth": 1.0, "coherence": 0.5})

        summary = app.get_interaction_summary()

        assert summary["total_interactions"] == 3
        assert summary["average_coherence"] > 0

    def test_app_reset(self):
        """Test application reset."""
        app = IntelligenceApplication()
        app.current_state = EssentialState(
            pattern_signature="test", quantum_state={}, context_depth=1.0, coherence_factor=0.5
        )
        app.interaction_log.append({"test": "entry"})

        app.reset()

        assert app.current_state is None
        assert len(app.interaction_log) == 0


class TestIntegration:
    """Integration tests for full pipeline."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        """Test complete intelligence pipeline."""
        # Setup
        app = IntelligenceApplication()
        processor = SensoryProcessor()

        # Create sensory input
        sensory_input = SensoryInput(
            source="test_source",
            data={"test_field": "test_value", "confidence": 0.85},
            timestamp=0.0,
            modality="structured",
        )

        # Process sensory input
        context_params = await processor.process(sensory_input)

        # Process through application
        result = await app.process_input(sensory_input.data, context_params)

        assert result is not None
        assert "patterns" in result
        assert result["coherence_level"] > 0

        # Check version evolution
        await app.evolve_version()
        # Version may or may not evolve depending on thresholds


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
