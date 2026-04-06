"""
Comprehensive test suite for RAG Evolution Layer.

Tests the core state management and persistence components including:
- FibonacciSequence / FibonacciEvolutionEngine: Dynamic optimization patterns
- VersionState: Version management and evolution tracking
- LandscapeDetector analyzers: State change detection
- DynamicWeightNetwork / RealTimeAdapter: Adaptation mechanisms
"""

from datetime import datetime

import pytest

from grid.awareness.context import Context
from grid.essence.core_state import EssentialState
from grid.evolution import (
    AdaptationState,
    DynamicWeightNetwork,
    FibonacciEvolutionEngine,
    FibonacciEvolutionState,
    LandscapeShift,
    LandscapeSnapshot,
    RealTimeAdapter,
    VersionState,
    WeightUpdate,
)
from grid.evolution.fibonacci_evolution import FibonacciSequence
from grid.evolution.landscape_detector import StatisticalLandscapeAnalyzer

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def essential_state():
    """Minimal EssentialState for evolution tests."""
    return EssentialState(
        pattern_signature="test_sig",
        quantum_state={"patterns": ["alpha"]},
        context_depth=1.0,
        coherence_factor=0.5,
    )


@pytest.fixture
def context():
    """Minimal Context for evolution tests."""
    return Context(
        temporal_depth=1.0,
        spatial_field={"origin": "test"},
        relational_web={},
        quantum_signature="ctx_test",
    )


# ---------------------------------------------------------------------------
# FibonacciSequence
# ---------------------------------------------------------------------------


class TestFibonacciSequence:
    """Test the standalone FibonacciSequence generator."""

    def test_generate_returns_correct_length(self):
        seq = FibonacciSequence()
        result = seq.generate(8)
        assert len(result) == 8

    def test_generate_known_values(self):
        seq = FibonacciSequence()
        result = seq.generate(8)
        assert result == [0, 1, 1, 2, 3, 5, 8, 13]

    def test_generate_zero_returns_empty(self):
        assert FibonacciSequence().generate(0) == []

    def test_golden_ratio(self):
        phi = FibonacciSequence().get_golden_ratio()
        assert abs(phi - 1.618) < 0.001

    def test_growth_factor_within_bounds(self):
        seq = FibonacciSequence()
        for step in range(10):
            gf = seq.get_growth_factor(step)
            assert 1.05 <= gf <= 1.8


# ---------------------------------------------------------------------------
# FibonacciEvolutionEngine
# ---------------------------------------------------------------------------


class TestFibonacciEvolution:
    """Test Fibonacci evolution engine using the real async API."""

    @pytest.fixture
    def engine(self):
        return FibonacciEvolutionEngine()

    @pytest.mark.asyncio
    async def test_evolve_with_fibonacci_changes_state(self, engine, essential_state, context):
        """evolve_with_fibonacci returns an evolved EssentialState."""
        evolved = await engine.evolve_with_fibonacci(essential_state, context)
        assert isinstance(evolved, EssentialState)
        assert evolved.pattern_signature != essential_state.pattern_signature
        assert "_fib" in evolved.pattern_signature

    @pytest.mark.asyncio
    async def test_evolution_history_grows(self, engine, essential_state, context):
        """Each call appends to evolution_history."""
        assert len(engine.get_evolution_history()) == 0
        await engine.evolve_with_fibonacci(essential_state, context)
        assert len(engine.get_evolution_history()) == 1
        await engine.evolve_with_fibonacci(essential_state, context)
        assert len(engine.get_evolution_history()) == 2

    @pytest.mark.asyncio
    async def test_evolution_state_records_growth_factor(self, engine, essential_state, context):
        """History entries store structural_changes with growth_factor."""
        await engine.evolve_with_fibonacci(essential_state, context)
        history = engine.get_evolution_history()
        assert "growth_factor" in history[0].structural_changes

    def test_fibonacci_evolution_state_dataclass(self, essential_state, context):
        """FibonacciEvolutionState can be created with base_state + context."""
        state = FibonacciEvolutionState(base_state=essential_state, context=context)
        assert state.evolution_step == 0
        assert state.growth_pattern == []

    def test_detect_structural_similarity(self):
        """detect_structural_similarity returns a float in [0, 1]."""
        engine = FibonacciEvolutionEngine()
        sim = engine.detect_structural_similarity(3, 5)
        assert 0.0 <= sim <= 1.0


# ---------------------------------------------------------------------------
# VersionState
# ---------------------------------------------------------------------------


class TestVersionState:
    """Test VersionState dataclass and its needs_evolution logic."""

    def test_version_state_creation(self, essential_state, context):
        vs = VersionState(
            essential_state=essential_state,
            context=context,
            quantum_signature="vs_test",
        )
        assert vs.transform_history == []
        assert vs.quantum_signature == "vs_test"

    @pytest.mark.asyncio
    async def test_needs_evolution_low_coherence(self, context):
        """With coherence_factor <= 1.5, no evolution needed."""
        state = EssentialState(
            pattern_signature="s",
            quantum_state={},
            context_depth=1.0,
            coherence_factor=0.5,
        )
        vs = VersionState(essential_state=state, context=context, quantum_signature="q")
        assert await vs._needs_evolution() is False

    @pytest.mark.asyncio
    async def test_needs_evolution_high_coherence(self, context):
        """With coherence_factor > 1.5, evolution is needed."""
        state = EssentialState(
            pattern_signature="s",
            quantum_state={},
            context_depth=1.0,
            coherence_factor=2.0,
        )
        vs = VersionState(essential_state=state, context=context, quantum_signature="q")
        assert await vs._needs_evolution() is True


# ---------------------------------------------------------------------------
# Landscape analyzers
# ---------------------------------------------------------------------------


class TestLandscapeAnalyzers:
    """Test StatisticalLandscapeAnalyzer and LandscapeSnapshot / LandscapeShift."""

    def test_snapshot_creation(self):
        snap = LandscapeSnapshot(
            timestamp=datetime.now(),
            patterns=["p1", "p2"],
            structural_features={"depth": 3},
            domain_metrics={"coherence": 0.9},
        )
        assert len(snap.patterns) == 2

    def test_shift_to_dict(self):
        shift = LandscapeShift(
            shift_type="structural",
            magnitude=0.6,
            affected_domains=["domain_a"],
            detected_patterns=["pattern_x"],
        )
        d = shift.to_dict()
        assert d["shift_type"] == "structural"
        assert d["magnitude"] == 0.6

    def test_statistical_analyzer_needs_window(self):
        """With fewer snapshots than window_size, no shifts are detected."""
        analyzer = StatisticalLandscapeAnalyzer(window_size=5)
        snap = LandscapeSnapshot(
            timestamp=datetime.now(),
            patterns=["p1"],
            structural_features={},
            domain_metrics={},
        )
        analyzer.add_snapshot(snap)
        assert analyzer.detect_statistical_shifts() == []

    def test_statistical_analyzer_detects_shift(self):
        """Feeding divergent pattern sets across the window triggers a shift."""
        analyzer = StatisticalLandscapeAnalyzer(window_size=3)
        # First window — patterns A
        for _ in range(6):
            analyzer.add_snapshot(
                LandscapeSnapshot(
                    timestamp=datetime.now(),
                    patterns=["a"],
                    structural_features={},
                    domain_metrics={"coherence": 0.5},
                )
            )
        # Replace recent window with entirely different patterns
        analyzer.snapshots[-3:] = [
            LandscapeSnapshot(
                timestamp=datetime.now(),
                patterns=["z", "y"],
                structural_features={},
                domain_metrics={"coherence": 0.8},
            )
            for _ in range(3)
        ]
        shifts = analyzer.detect_statistical_shifts(threshold=0.1)
        assert len(shifts) >= 1
        assert all(isinstance(s, LandscapeShift) for s in shifts)


# ---------------------------------------------------------------------------
# DynamicWeightNetwork
# ---------------------------------------------------------------------------


class TestDynamicWeightNetwork:
    """Test DynamicWeightNetwork weight management."""

    def test_default_weights(self):
        net = DynamicWeightNetwork()
        w = net.get_weights()
        assert "input" in w
        assert "hidden" in w
        assert "output" in w

    def test_custom_initial_weights(self):
        custom = {"layer1": {"w1": 0.7, "w2": 0.3}}
        net = DynamicWeightNetwork(initial_weights=custom)
        assert net.get_weights()["layer1"]["w1"] == 0.7

    def test_update_weight_returns_record(self):
        net = DynamicWeightNetwork()
        update = net.update_weight("input", "coherence_weight", 0.5, reason="test")
        assert isinstance(update, WeightUpdate)
        assert update.layer == "input"
        assert update.new_value == 0.5

    def test_update_weight_changes_value(self):
        net = DynamicWeightNetwork()
        net.update_weight("input", "coherence_weight", 0.9)
        assert net.get_weights()["input"]["coherence_weight"] == 0.9

    def test_adapt_weights_iterative(self):
        net = DynamicWeightNetwork()
        pattern = {"coherence": 0.8, "context_depth": 2.0, "pattern_count": 5}
        updates = net.adapt_weights_iterative(pattern, adaptation_rate=0.1)
        assert isinstance(updates, list)
        assert all(isinstance(u, WeightUpdate) for u in updates)


# ---------------------------------------------------------------------------
# RealTimeAdapter
# ---------------------------------------------------------------------------


class TestRealTimeAdaptation:
    """Test RealTimeAdapter async adaptation loop."""

    @pytest.fixture
    def adapter(self):
        return RealTimeAdapter()

    def test_initial_state(self, adapter):
        assert adapter.adaptation_state.iteration == 0
        assert adapter.performance_history == []

    @pytest.mark.asyncio
    async def test_adapt_increments_iteration(self, adapter, essential_state, context):
        result = await adapter.adapt(essential_state, context)
        assert isinstance(result, AdaptationState)
        assert result.iteration == 1

    @pytest.mark.asyncio
    async def test_adapt_records_performance(self, adapter, essential_state, context):
        await adapter.adapt(essential_state, context, performance_metric=0.75)
        assert len(adapter.performance_history) == 1
        assert adapter.adaptation_state.performance_metrics["current"] == 0.75

    @pytest.mark.asyncio
    async def test_multiple_adaptations(self, adapter, essential_state, context):
        for i in range(5):
            await adapter.adapt(essential_state, context, performance_metric=0.5 + i * 0.05)
        assert adapter.adaptation_state.iteration == 5
        assert len(adapter.performance_history) == 5

    def test_predict_returns_dict(self, adapter, essential_state, context):
        result = adapter.predict(essential_state, context)
        assert "prediction" in result
        assert "confidence" in result

    def test_get_adaptation_summary(self, adapter):
        summary = adapter.get_adaptation_summary()
        assert "iteration" in summary
        assert summary["iteration"] == 0
