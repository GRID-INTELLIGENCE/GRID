"""Real-time adapter with dynamic weight adjustment.

This module implements neural networks with dynamic weights that change
repeatedly based on iteration patterns for real-time adaptation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np

from grid.awareness.context import Context
from grid.essence.core_state import EssentialState

logger = logging.getLogger(__name__)


@dataclass
class WeightUpdate:
    """Represents a weight update in the neural network."""

    layer: str
    weight_name: str
    old_value: float
    new_value: float
    update_reason: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AdaptationState:
    """State of the real-time adapter."""

    iteration: int
    weights: dict[str, dict[str, float]]
    adaptation_history: list[WeightUpdate] = field(default_factory=list)
    performance_metrics: dict[str, float] = field(default_factory=dict)


class DynamicWeightNetwork:
    """Neural network with dynamically adjustable weights."""

    def __init__(self, initial_weights: dict[str, dict[str, float]] | None = None) -> None:
        """Initialize dynamic weight network.

        Args:
            initial_weights: Optional initial weights structure
        """
        if initial_weights:
            self.weights = initial_weights.copy()
        else:
            # Default weight structure
            self.weights = {
                "input": {
                    "coherence_weight": 0.3,
                    "context_weight": 0.3,
                    "pattern_weight": 0.4,
                },
                "hidden": {
                    "adaptation_rate": 0.1,
                    "learning_rate": 0.05,
                    "momentum": 0.9,
                },
                "output": {
                    "prediction_weight": 0.5,
                    "confidence_weight": 0.5,
                },
            }

        self.weight_history: list[dict[str, dict[str, float]]] = []
        self.adaptation_count = 0

    def get_weights(self) -> dict[str, dict[str, float]]:
        """Get current weights."""
        return self.weights.copy()

    def update_weight(
        self,
        layer: str,
        weight_name: str,
        new_value: float,
        reason: str = "adaptive_update",
    ) -> WeightUpdate:
        """Update a specific weight.

        Args:
            layer: Layer name
            weight_name: Weight name
            new_value: New weight value
            reason: Reason for update

        Returns:
            WeightUpdate record
        """
        if layer not in self.weights:
            self.weights[layer] = {}

        old_value = self.weights[layer].get(weight_name, 0.0)
        self.weights[layer][weight_name] = new_value

        update = WeightUpdate(
            layer=layer,
            weight_name=weight_name,
            old_value=old_value,
            new_value=new_value,
            update_reason=reason,
        )

        self.adaptation_count += 1

        logger.debug(f"Updated weight {layer}.{weight_name}: {old_value:.3f} -> {new_value:.3f} " f"({reason})")

        return update

    def adapt_weights_iterative(
        self,
        iteration_pattern: dict[str, Any],
        adaptation_rate: float = 0.1,
    ) -> list[WeightUpdate]:
        """Adapt weights based on iteration patterns.

        Args:
            iteration_pattern: Pattern from current iteration
            adaptation_rate: Rate of adaptation (0.0-1.0)

        Returns:
            List of weight updates
        """
        updates = []

        # Adapt based on coherence
        if "coherence" in iteration_pattern:
            coherence = iteration_pattern["coherence"]
            # Increase pattern weight if coherence is high
            if coherence > 0.7:
                new_pattern_weight = min(self.weights["input"]["pattern_weight"] + adaptation_rate * 0.1, 1.0)
                updates.append(
                    self.update_weight(
                        "input",
                        "pattern_weight",
                        new_pattern_weight,
                        "high_coherence",
                    )
                )

        # Adapt based on context depth
        if "context_depth" in iteration_pattern:
            context_depth = iteration_pattern["context_depth"]
            # Adjust context weight based on depth
            context_weight = 0.3 + (context_depth / 10.0) * 0.2
            context_weight = max(0.1, min(0.5, context_weight))
            updates.append(
                self.update_weight(
                    "input",
                    "context_weight",
                    context_weight,
                    "context_depth_adaptation",
                )
            )

        # Adapt learning rate based on performance
        if "performance" in iteration_pattern:
            performance = iteration_pattern["performance"]
            # Increase learning rate if performance is improving
            if performance > 0.8:
                new_lr = min(self.weights["hidden"]["learning_rate"] + adaptation_rate * 0.01, 0.2)
                updates.append(
                    self.update_weight(
                        "hidden",
                        "learning_rate",
                        new_lr,
                        "performance_improvement",
                    )
                )

        # Save weight snapshot
        self.weight_history.append(self.weights.copy())
        if len(self.weight_history) > 100:
            self.weight_history = self.weight_history[-100:]

        return updates

    def get_weight_trend(self, layer: str, weight_name: str) -> float | None:
        """Get trend of a weight over time.

        Args:
            layer: Layer name
            weight_name: Weight name

        Returns:
            Trend value (positive = increasing, negative = decreasing) or None
        """
        if len(self.weight_history) < 2:
            return None

        values = []
        for snapshot in self.weight_history:
            if layer in snapshot and weight_name in snapshot[layer]:
                values.append(snapshot[layer][weight_name])

        if len(values) < 2:
            return None

        # Calculate trend (slope)
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]

        return slope


class RealTimeAdapter:
    """Real-time adapter with dynamic weight adjustment."""

    def __init__(self) -> None:
        self.network = DynamicWeightNetwork()
        self.adaptation_state = AdaptationState(iteration=0, weights=self.network.get_weights())
        self.performance_history: list[float] = []

    async def adapt(
        self,
        state: EssentialState,
        context: Context,
        performance_metric: float | None = None,
    ) -> AdaptationState:
        """Adapt network weights based on current state and context.

        Args:
            state: Current essential state
            context: Current context
            performance_metric: Optional performance metric

        Returns:
            Updated adaptation state
        """
        # Build iteration pattern
        iteration_pattern = {
            "coherence": state.coherence_factor,
            "context_depth": context.temporal_depth,
            "pattern_count": len(state.quantum_state) if isinstance(state.quantum_state, dict) else 0,
        }

        if performance_metric is not None:
            iteration_pattern["performance"] = performance_metric
            self.performance_history.append(performance_metric)
            if len(self.performance_history) > 50:
                self.performance_history = self.performance_history[-50:]

        # Calculate adaptation rate based on recent performance
        adaptation_rate = self._calculate_adaptation_rate()

        # Adapt weights
        updates = self.network.adapt_weights_iterative(iteration_pattern, adaptation_rate)

        # Update adaptation state
        self.adaptation_state.iteration += 1
        self.adaptation_state.weights = self.network.get_weights()
        self.adaptation_state.adaptation_history.extend(updates)
        if len(self.adaptation_state.adaptation_history) > 200:
            self.adaptation_state.adaptation_history = self.adaptation_state.adaptation_history[-200:]

        # Update performance metrics
        if self.performance_history:
            self.adaptation_state.performance_metrics = {
                "current": self.performance_history[-1],
                "average": sum(self.performance_history) / len(self.performance_history),
                "trend": self._calculate_performance_trend(),
            }

        logger.info(
            f"Adapted network (iteration {self.adaptation_state.iteration}): "
            f"{len(updates)} weight updates, adaptation_rate={adaptation_rate:.3f}"
        )

        return self.adaptation_state

    def _calculate_adaptation_rate(self) -> float:
        """Calculate adaptation rate based on performance history."""
        if len(self.performance_history) < 3:
            return 0.1  # Default rate

        # If performance is improving, increase adaptation rate
        recent = self.performance_history[-3:]
        if recent[-1] > recent[0]:
            return min(0.2, 0.1 + (recent[-1] - recent[0]) * 0.5)
        # If performance is declining, decrease adaptation rate
        elif recent[-1] < recent[0]:
            return max(0.05, 0.1 - (recent[0] - recent[-1]) * 0.5)

        return 0.1  # Stable

    def _calculate_performance_trend(self) -> float:
        """Calculate performance trend."""
        if len(self.performance_history) < 2:
            return 0.0

        x = np.arange(len(self.performance_history))
        slope = np.polyfit(x, self.performance_history, 1)[0]

        return slope

    def predict(self, state: EssentialState, context: Context) -> dict[str, float]:
        """Make prediction using current weights.

        Args:
            state: Current essential state
            context: Current context

        Returns:
            Prediction results
        """
        weights = self.network.get_weights()

        # Weighted combination of inputs
        input_weights = weights["input"]
        coherence_input = state.coherence_factor * input_weights["coherence_weight"]
        context_input = context.temporal_depth * input_weights["context_weight"]
        pattern_input = (len(state.quantum_state) if isinstance(state.quantum_state, dict) else 0) * input_weights[
            "pattern_weight"
        ]

        # Normalize
        total_input = coherence_input + context_input + pattern_input
        if total_input > 0:
            normalized_input = total_input / (
                input_weights["coherence_weight"] + input_weights["context_weight"] + input_weights["pattern_weight"]
            )
        else:
            normalized_input = 0.0

        # Apply hidden layer processing
        hidden_weights = weights["hidden"]
        processed = normalized_input * (1.0 + hidden_weights["learning_rate"])

        # Output layer
        output_weights = weights["output"]
        prediction = processed * output_weights["prediction_weight"]
        confidence = min(1.0, processed * output_weights["confidence_weight"])

        return {
            "prediction": prediction,
            "confidence": confidence,
            "normalized_input": normalized_input,
        }

    def get_adaptation_summary(self) -> dict[str, Any]:
        """Get summary of adaptation state."""
        return {
            "iteration": self.adaptation_state.iteration,
            "total_adaptations": len(self.adaptation_state.adaptation_history),
            "performance_metrics": self.adaptation_state.performance_metrics,
            "weight_trends": {
                layer: {
                    weight_name: self.network.get_weight_trend(layer, weight_name)
                    for weight_name in layer_weights.keys()
                }
                for layer, layer_weights in self.adaptation_state.weights.items()
            },
        }
