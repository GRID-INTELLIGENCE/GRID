"""Fibonacci-like evolution patterns for dynamic optimization.

This module implements Fibonacci-like evolution mechanisms as both metaphor
and mechanism for the Embedded Agentic Knowledge System.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from grid.awareness.context import Context
from grid.essence.core_state import EssentialState

logger = logging.getLogger(__name__)


class FibonacciSequence:
    """Generates Fibonacci sequences for evolution patterns."""

    def __init__(self) -> None:
        self._cache: dict[int, int] = {0: 0, 1: 1}

    def generate(self, n: int) -> list[int]:
        """Generate Fibonacci sequence up to n terms.

        Args:
            n: Number of terms to generate

        Returns:
            List of Fibonacci numbers
        """
        if n <= 0:
            return []

        if n in self._cache:
            return [self._cache[i] for i in range(min(n, len(self._cache)))]

        sequence = []
        for i in range(n):
            if i in self._cache:
                sequence.append(self._cache[i])
            else:
                if i == 0:
                    fib = 0
                elif i == 1:
                    fib = 1
                else:
                    fib = self._cache.get(i - 1, self._fib(i - 1)) + self._cache.get(i - 2, self._fib(i - 2))
                self._cache[i] = fib
                sequence.append(fib)

        return sequence

    def _fib(self, n: int) -> int:
        """Calculate Fibonacci number recursively (with caching)."""
        if n in self._cache:
            return self._cache[n]
        if n <= 1:
            return n
        result = self._fib(n - 1) + self._fib(n - 2)
        self._cache[n] = result
        return result

    def get_golden_ratio(self) -> float:
        """Get the golden ratio (φ ≈ 1.618)."""
        return (1 + (5**0.5)) / 2

    def get_growth_factor(self, step: int) -> float:
        """Get growth factor based on Fibonacci ratio at step.

        Args:
            step: Evolution step number

        Returns:
            Growth factor based on Fibonacci progression
        """
        if step < 0:
            return 1.0

        # For step 0, use minimal growth
        if step == 0:
            return 1.05  # 5% growth

        # For step 1, use small growth
        if step == 1:
            return 1.1  # 10% growth

        sequence = self.generate(step + 1)
        if len(sequence) < 2:
            return 1.1

        # Calculate ratio of consecutive Fibonacci numbers (approaches golden ratio)
        if step >= len(sequence) or sequence[step] == 0:
            return 1.1

        if step - 1 < 0 or sequence[step - 1] == 0:
            return 1.1

        ratio = sequence[step] / sequence[step - 1]
        # Normalize to reasonable growth range (1.05 to 1.8)
        normalized = 1.0 + (ratio - 1.0) * 0.3
        return min(max(normalized, 1.05), 1.8)  # Cap between 1.05 and 1.8 for stability


@dataclass
class FibonacciEvolutionState:
    """State for Fibonacci-guided evolution."""

    base_state: EssentialState
    context: Context
    evolution_step: int = 0
    growth_pattern: list[int] = field(default_factory=list)
    structural_changes: dict[str, Any] = field(default_factory=dict)
    optimization_metrics: dict[str, float] = field(default_factory=dict)

    def get_growth_factor(self, fibonacci: FibonacciSequence) -> float:
        """Get current growth factor from Fibonacci sequence."""
        return fibonacci.get_growth_factor(self.evolution_step)


class FibonacciEvolutionEngine:
    """Fibonacci-like evolution engine for dynamic optimization.

    Implements Fibonacci patterns as both metaphor (mathematical elegance)
    and mechanism (dynamic optimization with state/control variables).
    """

    def __init__(self) -> None:
        self.fibonacci = FibonacciSequence()
        self.evolution_history: list[FibonacciEvolutionState] = []

    async def evolve_with_fibonacci(
        self,
        state: EssentialState,
        context: Context,
        optimization_target: str | None = None,
    ) -> EssentialState:
        """Evolve state using Fibonacci-like patterns.

        Args:
            state: Current essential state
            context: Current context
            optimization_target: Optional target for optimization (e.g., "coherence", "complexity")

        Returns:
            Evolved essential state
        """
        # Determine evolution step from history
        evolution_step = len(self.evolution_history)

        # Generate growth pattern
        growth_pattern = self.fibonacci.generate(evolution_step + 3)
        growth_factor = self.fibonacci.get_growth_factor(evolution_step)

        # Create evolution state
        evolution_state = FibonacciEvolutionState(
            base_state=state,
            context=context,
            evolution_step=evolution_step,
            growth_pattern=growth_pattern,
            optimization_metrics={},
        )

        # Apply Fibonacci-guided evolution
        evolved_state = await self._apply_fibonacci_evolution(state, context, growth_factor, optimization_target)

        # Track evolution
        evolution_state.structural_changes = {
            "growth_factor": growth_factor,
            "evolution_step": evolution_step,
            "optimization_target": optimization_target,
        }
        self.evolution_history.append(evolution_state)

        logger.info(f"Evolved state with Fibonacci pattern: step={evolution_step}, growth_factor={growth_factor:.3f}")

        return evolved_state

    async def _apply_fibonacci_evolution(
        self,
        state: EssentialState,
        context: Context,
        growth_factor: float,
        optimization_target: str | None,
    ) -> EssentialState:
        """Apply Fibonacci-guided evolution to state.

        Args:
            state: Current state
            context: Current context
            growth_factor: Fibonacci-based growth factor
            optimization_target: Optional optimization target

        Returns:
            Evolved state
        """
        from dataclasses import replace

        # Apply growth to coherence factor (Fibonacci-like progression)
        new_coherence = state.coherence_factor * (1.0 + (growth_factor - 1.0) * 0.1)

        # Apply growth to context depth (temporal evolution)
        new_context_depth = context.temporal_depth * (1.0 + (growth_factor - 1.0) * 0.05)

        # Evolve pattern signature with Fibonacci influence
        fib_marker = f"_fib{int(growth_factor * 100)}"
        new_signature = f"{state.pattern_signature}{fib_marker}"

        # Evolve quantum state with structural growth
        new_quantum_state = state.quantum_state.copy()
        if "evolution_metrics" not in new_quantum_state:
            new_quantum_state["evolution_metrics"] = {}

        new_quantum_state["evolution_metrics"].update(
            {
                "growth_factor": growth_factor,
                "fibonacci_step": len(self.evolution_history),
                "optimization_target": optimization_target,
            }
        )

        # Create evolved state
        evolved = replace(
            state,
            pattern_signature=new_signature,
            coherence_factor=new_coherence,
            context_depth=new_context_depth,
            quantum_state=new_quantum_state,
        )

        return evolved

    def get_evolution_history(self) -> list[FibonacciEvolutionState]:
        """Get evolution history."""
        return self.evolution_history.copy()

    def detect_structural_similarity(self, level1: int, level2: int) -> float:
        """Detect structural similarity across levels (Fibonacci property).

        Args:
            level1: First evolution level
            level2: Second evolution level

        Returns:
            Similarity score (0.0-1.0)
        """
        if level1 >= len(self.evolution_history) or level2 >= len(self.evolution_history):
            return 0.0

        state1 = self.evolution_history[level1]
        state2 = self.evolution_history[level2]

        # Compare growth patterns
        pattern1 = state1.growth_pattern
        pattern2 = state2.growth_pattern

        if not pattern1 or not pattern2:
            return 0.0

        # Calculate similarity based on pattern structure
        min_len = min(len(pattern1), len(pattern2))
        if min_len == 0:
            return 0.0

        # Compare ratios (Fibonacci property: similar ratios at different scales)
        ratios1 = [pattern1[i] / pattern1[i - 1] for i in range(1, min_len) if pattern1[i - 1] > 0]
        ratios2 = [pattern2[i] / pattern2[i - 1] for i in range(1, min_len) if pattern2[i - 1] > 0]

        if not ratios1 or not ratios2:
            return 0.0

        # Calculate average ratio similarity
        avg_ratio1 = sum(ratios1) / len(ratios1)
        avg_ratio2 = sum(ratios2) / len(ratios2)

        # Similarity based on how close ratios are (Fibonacci converges to golden ratio)
        similarity = 1.0 - abs(avg_ratio1 - avg_ratio2) / max(avg_ratio1, avg_ratio2)
        return max(0.0, min(1.0, similarity))

    def get_optimal_evolution_path(self, target_coherence: float, max_steps: int = 10) -> list[int]:
        """Get optimal evolution path using Fibonacci patterns.

        Args:
            target_coherence: Target coherence factor
            max_steps: Maximum evolution steps

        Returns:
            List of evolution step indices for optimal path
        """
        if not self.evolution_history:
            return []

        # Use Fibonacci sequence to determine optimal steps
        fibonacci_steps = self.fibonacci.generate(max_steps)
        optimal_path = []

        current_coherence = self.evolution_history[-1].base_state.coherence_factor

        for step in range(max_steps):
            if step < len(fibonacci_steps):
                growth = self.fibonacci.get_growth_factor(step)
                projected_coherence = current_coherence * (1.0 + (growth - 1.0) * 0.1)

                if projected_coherence >= target_coherence:
                    optimal_path.append(step)
                    break

                if step in fibonacci_steps:
                    optimal_path.append(step)

        return optimal_path
