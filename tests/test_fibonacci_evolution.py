"""Tests for Fibonacci evolution functionality."""

from __future__ import annotations

import pytest

from grid.awareness.context import Context
from grid.essence.core_state import EssentialState
from grid.evolution.fibonacci_evolution import (
    FibonacciEvolutionEngine,
    FibonacciEvolutionState,
    FibonacciSequence,
)


class TestFibonacciSequence:
    """Test FibonacciSequence."""

    def test_generate_sequence(self):
        """Test generating Fibonacci sequence."""
        fib = FibonacciSequence()
        sequence = fib.generate(10)

        assert len(sequence) == 10
        assert sequence[0] == 0
        assert sequence[1] == 1
        assert sequence[2] == 1
        assert sequence[3] == 2
        assert sequence[4] == 3
        assert sequence[5] == 5
        assert sequence[6] == 8

    def test_golden_ratio(self):
        """Test golden ratio calculation."""
        fib = FibonacciSequence()
        phi = fib.get_golden_ratio()

        # Golden ratio is approximately 1.618
        assert abs(phi - 1.618) < 0.01

    def test_growth_factor(self):
        """Test growth factor calculation."""
        fib = FibonacciSequence()

        # Early steps should have lower growth
        factor1 = fib.get_growth_factor(2)
        assert factor1 > 0

        # Later steps should approach golden ratio
        factor10 = fib.get_growth_factor(10)
        assert factor10 > factor1
        assert factor10 <= 2.0  # Capped at 2.0


class TestFibonacciEvolutionEngine:
    """Test FibonacciEvolutionEngine."""

    @pytest.fixture
    def engine(self):
        """Create Fibonacci evolution engine."""
        return FibonacciEvolutionEngine()

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
    async def test_evolve_with_fibonacci(self, engine, base_state, base_context):
        """Test evolving state with Fibonacci patterns."""
        evolved = await engine.evolve_with_fibonacci(base_state, base_context, optimization_target="coherence")

        assert evolved.pattern_signature != base_state.pattern_signature
        assert "fib" in evolved.pattern_signature
        assert evolved.coherence_factor > base_state.coherence_factor
        assert "evolution_metrics" in evolved.quantum_state

    @pytest.mark.asyncio
    async def test_multiple_evolutions(self, engine, base_state, base_context):
        """Test multiple evolution steps."""
        state = base_state

        for _i in range(3):
            state = await engine.evolve_with_fibonacci(state, base_context, optimization_target="coherence")

        # Should have evolution history
        assert len(engine.evolution_history) == 3

        # Coherence should increase
        assert state.coherence_factor > base_state.coherence_factor

    @pytest.mark.asyncio
    async def test_evolution_history(self, engine, base_state, base_context):
        """Test evolution history tracking."""
        await engine.evolve_with_fibonacci(base_state, base_context)

        history = engine.get_evolution_history()
        assert len(history) == 1
        assert history[0].evolution_step == 0
        assert len(history[0].growth_pattern) > 0

    def test_detect_structural_similarity(self, engine, base_state, base_context):
        """Test structural similarity detection."""
        # Need to evolve first to have history
        import asyncio

        async def setup():
            await engine.evolve_with_fibonacci(base_state, base_context)
            await engine.evolve_with_fibonacci(base_state, base_context)

        asyncio.run(setup())

        similarity = engine.detect_structural_similarity(0, 1)
        assert 0.0 <= similarity <= 1.0

    def test_get_optimal_evolution_path(self, engine, base_state, base_context):
        """Test optimal evolution path calculation."""
        import asyncio

        async def setup():
            await engine.evolve_with_fibonacci(base_state, base_context)

        asyncio.run(setup())

        path = engine.get_optimal_evolution_path(target_coherence=1.0, max_steps=10)
        assert isinstance(path, list)
        # Path should contain step indices
        assert all(isinstance(step, int) for step in path)


class TestFibonacciEvolutionState:
    """Test FibonacciEvolutionState."""

    def test_evolution_state_creation(self):
        """Test creating evolution state."""
        state = EssentialState(
            pattern_signature="test",
            quantum_state={},
            context_depth=1.0,
            coherence_factor=0.5,
        )
        context = Context(
            temporal_depth=1.0,
            spatial_field={},
            relational_web={},
            quantum_signature="test",
        )

        fib = FibonacciSequence()
        evolution_state = FibonacciEvolutionState(
            base_state=state,
            context=context,
            evolution_step=0,
            growth_pattern=[0, 1, 1, 2],
        )

        assert evolution_state.evolution_step == 0
        assert len(evolution_state.growth_pattern) == 4

        growth_factor = evolution_state.get_growth_factor(fib)
        assert growth_factor > 0
