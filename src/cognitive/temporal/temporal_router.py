from datetime import UTC, datetime, timedelta

from cognitive.light_of_the_seven.cognitive_layer.schemas.cognitive_state import CognitiveState
from cognitive.light_of_the_seven.cognitive_layer.schemas.user_cognitive_profile import UserCognitiveProfile


class TemporalRouter:
    """
    Time-aware routing system that integrates temporal patterns with cognitive state.
    Implements logical time-based routing using Coffee House temporal concepts.
    """

    def __init__(self):
        self.temporal_patterns = {"urgent": self._is_urgent, "cyclic": self._is_cyclic, "long_term": self._is_long_term}

    def route(self, cognitive_state: CognitiveState, profile: UserCognitiveProfile, temporal_context: dict) -> dict:
        """
        Route request based on temporal context and cognitive state.

        Args:
            cognitive_state: Current cognitive state
            profile: User cognitive profile
            temporal_context: {
                "deadline": Optional[datetime],
                "pattern": str,  # urgent, cyclic, long_term
                "time_sensitivity": float  # 0-1
            }

        Returns:
            Routing decision with metadata
        """
        # Determine temporal pattern
        pattern = temporal_context.get("pattern", "")
        pattern_detector = self.temporal_patterns.get(pattern, self._default_pattern)

        # Get coffee mode based on cognitive load
        coffee_mode = self._get_coffee_mode(cognitive_state.estimated_load)

        # Apply temporal routing logic
        route_decision = {
            "route_type": "standard",
            "priority": "medium",
            "coffee_mode": coffee_mode,
            "chunk_size": coffee_mode["chunk_size"],
            "processing_mode": coffee_mode["processing_mode"],
            "temporal_adaptations": [],
        }

        # Apply pattern-specific routing
        pattern_detector(cognitive_state, profile, temporal_context, route_decision)

        # Apply time sensitivity adjustments
        sensitivity = temporal_context.get("time_sensitivity", 0.5)
        if sensitivity > 0.7:
            route_decision["priority"] = "high"
            route_decision["temporal_adaptations"].append("time_compression")
        elif sensitivity < 0.3:
            route_decision["priority"] = "low"
            route_decision["temporal_adaptations"].append("time_expansion")

        return route_decision

    def _get_coffee_mode(self, cognitive_load: float) -> dict:
        """Map cognitive load to coffee preparation modes (Coffee House concept)."""
        if cognitive_load < 3.0:
            return {"name": "Espresso", "chunk_size": 32, "processing_mode": "precision"}
        elif cognitive_load < 7.0:
            return {"name": "Americano", "chunk_size": 64, "processing_mode": "balanced"}
        else:
            return {"name": "Cold Brew", "chunk_size": 128, "processing_mode": "comprehensive"}

    def _is_urgent(self, state: CognitiveState, profile: UserCognitiveProfile, context: dict, decision: dict):
        """Urgent temporal pattern routing."""
        deadline = context.get("deadline")
        if deadline and deadline - datetime.now(UTC) < timedelta(hours=24):
            decision["route_type"] = "expedited"
            decision["priority"] = "critical"
            decision["temporal_adaptations"].append("deadline_aware")

            # Reduce processing depth for urgent items
            if state.processing_mode == "System_2":
                decision["processing_mode"] = "System_1"
                decision["chunk_size"] = max(32, decision["chunk_size"] // 2)

    def _is_cyclic(self, state: CognitiveState, profile: UserCognitiveProfile, context: dict, decision: dict):
        """Cyclic temporal pattern routing."""
        decision["route_type"] = "recurring"
        decision["temporal_adaptations"].extend(["pattern_recognition", "predictive_caching"])

        # Increase processing depth for pattern analysis
        if state.estimated_load < 5.0:
            decision["processing_mode"] = "System_2"
            decision["chunk_size"] = min(128, decision["chunk_size"] * 2)

    def _is_long_term(self, state: CognitiveState, profile: UserCognitiveProfile, context: dict, decision: dict):
        """Long-term temporal pattern routing."""
        decision["route_type"] = "strategic"
        decision["temporal_adaptations"].extend(["horizon_scanning", "trend_analysis"])

        # Enable deep processing
        decision["processing_mode"] = "System_2"
        decision["chunk_size"] = 128

    def _default_pattern(self, state: CognitiveState, profile: UserCognitiveProfile, context: dict, decision: dict):
        """Default temporal pattern routing."""
        decision["temporal_adaptations"].append("time_neutral")
