"""Cognitive load estimator for assessing mental effort requirements."""

from enum import Enum
from typing import Any

from ..schemas.cognitive_state import CognitiveLoadType, CognitiveState
from ..schemas.user_cognitive_profile import UserCognitiveProfile


class LoadFactor(str, Enum):
    """Factors that contribute to cognitive load."""

    INFORMATION_DENSITY = "information_density"
    NOVELTY = "novelty"
    COMPLEXITY = "complexity"
    TIME_PRESSURE = "time_pressure"
    SPLIT_ATTENTION = "split_attention"
    ELEMENT_INTERACTIVITY = "element_interactivity"


class CognitiveLoadEstimator:
    """Estimates cognitive load of operations and information.

    Considers:
    - Information density
    - Novelty
    - Complexity
    - Time pressure
    """

    def __init__(self):
        """Initialize the cognitive load estimator."""
        self.factor_weights = {
            LoadFactor.INFORMATION_DENSITY: 0.25,
            LoadFactor.NOVELTY: 0.20,
            LoadFactor.COMPLEXITY: 0.25,
            LoadFactor.TIME_PRESSURE: 0.15,
            LoadFactor.SPLIT_ATTENTION: 0.10,
            LoadFactor.ELEMENT_INTERACTIVITY: 0.05,
        }

    def estimate_load(self, operation: dict[str, Any], user_profile: UserCognitiveProfile | None = None) -> float:
        """Estimate cognitive load of an operation.

        Args:
            operation: Operation description with load factors
            user_profile: Optional user cognitive profile

        Returns:
            Estimated cognitive load (0-10 scale)
        """
        # Extract load factors
        information_density = operation.get("information_density", 0.5)
        novelty = operation.get("novelty", 0.5)
        complexity = operation.get("complexity", 0.5)
        time_pressure = operation.get("time_pressure", 0.0)
        split_attention = operation.get("split_attention", 0.0)
        element_interactivity = operation.get("element_interactivity", 0.5)

        # Calculate weighted load
        load = (
            information_density * self.factor_weights[LoadFactor.INFORMATION_DENSITY]
            + novelty * self.factor_weights[LoadFactor.NOVELTY]
            + complexity * self.factor_weights[LoadFactor.COMPLEXITY]
            + time_pressure * self.factor_weights[LoadFactor.TIME_PRESSURE]
            + split_attention * self.factor_weights[LoadFactor.SPLIT_ATTENTION]
            + element_interactivity * self.factor_weights[LoadFactor.ELEMENT_INTERACTIVITY]
        ) * 10.0  # Scale to 0-10

        # Adjust based on user profile
        if user_profile:
            # Experts can handle more load
            if user_profile.expertise_level in ["advanced", "expert"]:
                load *= 0.8  # Reduce perceived load for experts
            # Adjust for cognitive capacity
            capacity_factor = user_profile.working_memory_capacity
            load *= 2.0 - capacity_factor  # Higher capacity = lower effective load

        return min(10.0, max(0.0, load))

    def estimate_load_type(self, operation: dict[str, Any]) -> CognitiveLoadType:
        """Estimate the type of cognitive load.

        Args:
            operation: Operation description

        Returns:
            Type of cognitive load
        """
        # High element interactivity suggests intrinsic load
        if operation.get("element_interactivity", 0.0) > 0.7:
            return CognitiveLoadType.INTRINSIC

        # Split attention suggests extraneous load
        if operation.get("split_attention", 0.0) > 0.5:
            return CognitiveLoadType.EXTRINSIC

        # High novelty with low complexity suggests germane load
        if operation.get("novelty", 0.0) > 0.6 and operation.get("complexity", 1.0) < 0.5:
            return CognitiveLoadType.GERMANE

        # Default to intrinsic
        return CognitiveLoadType.INTRINSIC

    def estimate_working_memory_usage(
        self, information: dict[str, Any], user_profile: UserCognitiveProfile | None = None
    ) -> float:
        """Estimate working memory usage.

        Args:
            information: Information to be processed
            user_profile: Optional user cognitive profile

        Returns:
            Estimated working memory usage (0-1, where 1 = capacity)
        """
        # Count information chunks (Miller's 7±2)
        chunk_count = information.get("chunk_count", 0)
        if chunk_count == 0:
            # Estimate from other factors
            item_count = information.get("item_count", 0)
            chunk_count = max(1, item_count // 3)  # Rough estimate: 3 items per chunk

        # Calculate usage
        base_capacity = 7.0  # Miller's magic number
        usage = min(1.0, chunk_count / base_capacity)

        # Adjust for user capacity
        if user_profile:
            user_capacity = user_profile.working_memory_capacity * 7.0
            usage = min(1.0, chunk_count / user_capacity)

        return usage

    def create_cognitive_state(
        self, operation: dict[str, Any], user_profile: UserCognitiveProfile | None = None
    ) -> CognitiveState:
        """Create a cognitive state from operation analysis.

        Args:
            operation: Operation description
            user_profile: Optional user cognitive profile

        Returns:
            Cognitive state with estimated load
        """
        estimated_load = self.estimate_load(operation, user_profile)
        load_type = self.estimate_load_type(operation)

        # Estimate working memory usage
        working_memory_usage = self.estimate_working_memory_usage(operation, user_profile)

        return CognitiveState(
            estimated_load=estimated_load,
            load_type=load_type,
            working_memory_usage=working_memory_usage,
            decision_complexity=operation.get("complexity", 0.5),
            time_pressure=operation.get("time_pressure", 0.0),
            context=operation,
        )

    def is_load_acceptable(self, estimated_load: float, user_profile: UserCognitiveProfile | None = None) -> bool:
        """Check if estimated load is acceptable for the user.

        Args:
            estimated_load: Estimated cognitive load (0-10)
            user_profile: Optional user cognitive profile

        Returns:
            True if load is acceptable
        """
        if user_profile:
            tolerance = user_profile.cognitive_load_tolerance * 10.0
            return estimated_load <= tolerance

        # Default threshold: 7.0 (high load)
        return estimated_load <= 7.0

    def suggest_reduction(self, operation: dict[str, Any], estimated_load: float) -> dict[str, Any]:
        """Suggest ways to reduce cognitive load.

        Args:
            operation: Operation description
            estimated_load: Estimated cognitive load

        Returns:
            Dictionary with reduction suggestions
        """
        suggestions = []

        if operation.get("split_attention", 0.0) > 0.5:
            suggestions.append(
                {
                    "factor": "split_attention",
                    "suggestion": "Integrate related information to reduce split attention",
                }
            )

        if operation.get("information_density", 0.0) > 0.7:
            suggestions.append(
                {
                    "factor": "information_density",
                    "suggestion": "Reduce information density by chunking or progressive disclosure",
                }
            )

        if operation.get("element_interactivity", 0.0) > 0.7:
            suggestions.append(
                {
                    "factor": "element_interactivity",
                    "suggestion": "Break down into smaller, independent elements",
                }
            )

        if operation.get("time_pressure", 0.0) > 0.6:
            suggestions.append(
                {
                    "factor": "time_pressure",
                    "suggestion": "Reduce time pressure or provide more time",
                }
            )

        return {
            "estimated_load": estimated_load,
            "suggestions": suggestions,
            "priority": "high" if estimated_load > 7.0 else "medium" if estimated_load > 4.0 else "low",
        }
