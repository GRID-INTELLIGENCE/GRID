"""Projectable Protocol - Interface for future projection capabilities.

Defines the contract for entities that can project future context needs
based on current trajectory and historical patterns.

Projection enables VECTION's anticipatory capabilities - predicting
what context will be needed before it's explicitly requested.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Projectable(Protocol):
    """Protocol for entities that can project future states.

    Implementers can forecast future context needs based on
    current trajectory, velocity, and historical patterns.

    This is the foundation for VECTION's anticipatory intelligence -
    knowing what you'll need before you need it.
    """

    def project(self, steps: int = 3) -> list[str]:
        """Project future context needs.

        Args:
            steps: Number of steps into the future to project.
                   Each step represents a potential future interaction.

        Returns:
            List of projected context need descriptions.
            These describe what context/information will likely be needed.

        Example:
            >>> projectable.project(steps=3)
            ["broader_context_needed", "related_topics_retrieval", "discovery_support"]
        """
        ...

    def get_projection_confidence(self) -> float:
        """Get confidence level for projections.

        Returns:
            Confidence score (0.0 - 1.0) indicating how reliable
            the current projections are. Lower values indicate
            insufficient data or unstable trajectory.
        """
        ...


@runtime_checkable
class DetailedProjectable(Projectable, Protocol):
    """Extended projection protocol with detailed forecasting.

    Provides richer projection capabilities including probability
    distributions, time estimates, and conditional projections.
    """

    def project_detailed(
        self,
        steps: int = 3,
        include_probabilities: bool = True,
    ) -> list[dict[str, Any]]:
        """Project future context needs with detailed information.

        Args:
            steps: Number of steps to project.
            include_probabilities: Whether to include probability estimates.

        Returns:
            List of detailed projection dictionaries with structure:
            {
                "step": int,
                "description": str,
                "probability": float,  # If include_probabilities
                "category": str,
                "prerequisites": list[str],
                "metadata": dict
            }
        """
        ...

    def project_conditional(
        self,
        condition: str,
        steps: int = 3,
    ) -> list[str]:
        """Project future needs given a condition.

        Answers: "If X happens, what will be needed?"

        Args:
            condition: A condition string describing a potential action.
            steps: Number of steps to project.

        Returns:
            List of projected context needs assuming the condition.
        """
        ...

    def get_projection_horizon(self) -> int:
        """Get the maximum reliable projection horizon.

        Returns:
            Maximum number of steps for which projections are
            considered reliable (confidence > 0.5).
        """
        ...


@runtime_checkable
class ProjectionSource(Protocol):
    """Protocol for entities that can provide projection data.

    Used by projection aggregators to collect projection inputs
    from multiple sources.
    """

    def get_projection_data(self) -> dict[str, Any]:
        """Get data used for projection calculations.

        Returns:
            Dictionary containing:
            {
                "direction": str,
                "velocity": float,
                "momentum": float,
                "history": list[str],
                "patterns": list[str],
            }
        """
        ...

    def get_projection_weights(self) -> dict[str, float]:
        """Get weights for different projection factors.

        Returns:
            Dictionary mapping factor names to their weights.
            Weights should sum to 1.0.
        """
        ...


class ProjectionResult:
    """Result of a projection operation.

    Encapsulates the projected needs along with confidence
    and supporting evidence.
    """

    def __init__(
        self,
        projections: list[str],
        confidence: float,
        horizon: int,
        source: str = "unknown",
        evidence: list[str] | None = None,
    ) -> None:
        """Initialize projection result.

        Args:
            projections: List of projected context needs.
            confidence: Overall confidence (0.0 - 1.0).
            horizon: Number of steps projected.
            source: Source of the projection.
            evidence: Supporting evidence for projections.
        """
        self.projections = projections
        self.confidence = max(0.0, min(1.0, confidence))
        self.horizon = horizon
        self.source = source
        self.evidence = evidence or []

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ProjectionResult(projections={self.projections[:3]}..., "
            f"confidence={self.confidence:.2f}, horizon={self.horizon})"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "projections": self.projections,
            "confidence": round(self.confidence, 3),
            "horizon": self.horizon,
            "source": self.source,
            "evidence": self.evidence,
        }

    def is_reliable(self, threshold: float = 0.5) -> bool:
        """Check if projection meets reliability threshold.

        Args:
            threshold: Minimum confidence for reliability.

        Returns:
            True if confidence meets or exceeds threshold.
        """
        return self.confidence >= threshold

    def get_primary(self) -> str | None:
        """Get primary (first) projection.

        Returns:
            Primary projection or None if empty.
        """
        return self.projections[0] if self.projections else None

    def filter_by_keyword(self, keyword: str) -> list[str]:
        """Filter projections by keyword.

        Args:
            keyword: Keyword to search for.

        Returns:
            Projections containing the keyword.
        """
        keyword_lower = keyword.lower()
        return [p for p in self.projections if keyword_lower in p.lower()]
