"""
Cognitive Router Integration - Apps Router Adapter.

Bridges the cognitive engine with the @apps routing system:
- Enhances activities with cognitive insights
- Integrates pattern recognition
- Applies temporal context
- Provides cognitive-aware routing
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from cognition.core.processor import CognitiveProcessor, get_cognitive_processor
from cognition.learning.adaptive import LearningOutcome, LearningSignal, OutcomeType, get_adaptive_learner
from cognition.patterns.enhanced import get_enhanced_pattern_manager

logger = logging.getLogger(__name__)


@dataclass
class EnhancedActivity:
    """Activity enhanced with cognitive insights."""

    original_id: str
    cognitive_context: dict[str, Any]
    pattern_matches: list[str]
    priority_boost: bool
    boost_reason: str | None
    recommendations: list[str]
    processing_time_ms: float
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "original_id": self.original_id,
            "cognitive_context": self.cognitive_context,
            "pattern_matches": self.pattern_matches,
            "priority_boost": self.priority_boost,
            "boost_reason": self.boost_reason,
            "recommendations": self.recommendations,
            "processing_time_ms": self.processing_time_ms,
            "timestamp": self.timestamp.isoformat(),
        }


class CognitiveRouterAdapter:
    """
    Adapter that integrates cognitive processing with @apps routing.

    Enhances routing decisions with:
    - Pattern-based insights
    - Temporal context awareness
    - Cognitive load consideration
    - Adaptive learning from outcomes
    """

    def __init__(self, processor: CognitiveProcessor | None = None):
        self._processor = processor or get_cognitive_processor()
        self._pattern_manager = get_enhanced_pattern_manager()
        self._learner = get_adaptive_learner()
        self._enhancement_history: list[EnhancedActivity] = []
        self._stats = {
            "activities_enhanced": 0,
            "priority_boosts": 0,
            "patterns_detected": 0,
        }

    async def enhance_routing(self, activity: Any) -> EnhancedActivity:
        """
        Enhance an activity with cognitive insights for routing.

        Args:
            activity: Activity object (with context, payload, etc.)

        Returns:
            EnhancedActivity with cognitive enhancements
        """
        start_time = datetime.now()

        # Extract activity data
        activity_id = str(getattr(activity, "id", "unknown"))
        payload = getattr(activity, "payload", {})
        context_meta = getattr(getattr(activity, "context", None), "meta", {})

        # 1. Process through cognitive engine
        await self._processor.process_input(payload)

        # 2. Pattern matching
        pattern_matches = self._pattern_manager.find_matches_enhanced({"payload": payload, "context": context_meta})
        pattern_names = [m.pattern_name for m in pattern_matches]

        # 3. Analyze routing context
        cognitive_context = await self._analyze_context(activity, pattern_matches)

        # 4. Determine priority boost
        priority_boost, boost_reason = await self._should_boost_priority(activity, pattern_names, cognitive_context)

        # 5. Generate recommendations
        recommendations = await self._generate_routing_recommendations(activity, pattern_names, cognitive_context)

        # 6. Inject insights into activity
        if hasattr(activity, "context") and hasattr(activity.context, "meta"):
            activity.context.meta["cognitive_insights"] = {
                "patterns": pattern_names,
                "context": cognitive_context,
                "boost": priority_boost,
                "boost_reason": boost_reason,
                "recommendations": recommendations,
            }

        # Build enhanced activity
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        enhanced = EnhancedActivity(
            original_id=activity_id,
            cognitive_context=cognitive_context,
            pattern_matches=pattern_names,
            priority_boost=priority_boost,
            boost_reason=boost_reason,
            recommendations=recommendations,
            processing_time_ms=processing_time,
        )

        # Update stats
        self._stats["activities_enhanced"] += 1
        self._stats["patterns_detected"] += len(pattern_names)
        if priority_boost:
            self._stats["priority_boosts"] += 1

        self._enhancement_history.append(enhanced)

        return enhanced

    async def _analyze_context(self, activity: Any, pattern_matches: list) -> dict[str, Any]:
        """Analyze cognitive context for routing."""
        processor_context = self._processor.context

        return {
            "state": processor_context.state.value,
            "processing_mode": processor_context.processing_mode.value,
            "coffee_mode": processor_context.coffee_mode.value,
            "cognitive_load": processor_context.metrics.cognitive_load,
            "attention_level": processor_context.metrics.attention_level,
            "pattern_count": len(pattern_matches),
            "is_optimal": processor_context.metrics.is_optimal(),
            "is_overloaded": processor_context.metrics.is_overloaded(),
        }

    async def _should_boost_priority(
        self,
        activity: Any,
        pattern_names: list[str],
        cognitive_context: dict[str, Any],
    ) -> tuple[bool, str | None]:
        """Determine if activity priority should be boosted."""
        # Security patterns always boost
        if "SECURITY_INCIDENT_PATTERN" in pattern_names:
            return True, "security_incident"

        # Critical patterns boost
        if "CRITICAL_PATTERN" in pattern_names:
            return True, "critical_pattern"

        # Error patterns during business hours
        if "ERROR_PATTERN" in pattern_names and cognitive_context.get("is_optimal"):
            return True, "error_during_optimal"

        # Urgent patterns when not overloaded
        if "URGENT_PATTERN" in pattern_names and not cognitive_context.get("is_overloaded"):
            return True, "urgent_request"

        return False, None

    async def _generate_routing_recommendations(
        self,
        activity: Any,
        pattern_names: list[str],
        cognitive_context: dict[str, Any],
    ) -> list[str]:
        """Generate routing recommendations based on analysis."""
        recommendations = []

        # Based on patterns
        if pattern_names:
            recommendations.append(f"Activity matches {len(pattern_names)} pattern(s) - consider priority routing")

        # Based on cognitive state
        if cognitive_context.get("is_overloaded"):
            recommendations.append(
                "System experiencing high cognitive load - consider deferring non-critical activities"
            )

        if cognitive_context.get("is_optimal"):
            recommendations.append("Optimal cognitive state - suitable for complex analysis tasks")

        # Based on coffee mode
        coffee_mode = cognitive_context.get("coffee_mode")
        if coffee_mode == "cold_brew":
            recommendations.append("Deep analysis mode active - ideal for comprehensive processing")
        elif coffee_mode == "espresso":
            recommendations.append("Quick processing mode - focus on rapid decisions")

        return recommendations

    def record_routing_outcome(
        self,
        activity_id: str,
        route_taken: str,
        was_successful: bool,
        details: str | None = None,
    ) -> None:
        """
        Record the outcome of a routing decision for learning.

        Args:
            activity_id: The activity that was routed
            route_taken: The route that was chosen
            was_successful: Whether the routing was successful
            details: Optional details about the outcome
        """
        # Find the enhancement for this activity
        enhancement = next((e for e in self._enhancement_history if e.original_id == activity_id), None)

        if enhancement:
            outcome = LearningOutcome(
                outcome_id=f"route_{activity_id}",
                outcome_type=OutcomeType.SUCCESS if was_successful else OutcomeType.FAILURE,
                signal=LearningSignal.POSITIVE if was_successful else LearningSignal.NEGATIVE,
                input_features={
                    "patterns": enhancement.pattern_matches,
                    "priority_boost": enhancement.priority_boost,
                    "cognitive_context": enhancement.cognitive_context,
                },
                predicted_output=route_taken,
                actual_output="success" if was_successful else "failure",
                confidence=0.8 if enhancement.priority_boost else 0.6,
                metadata={"details": details},
            )

            self._learner.learn_from_outcome(enhancement.to_dict(), outcome)

    def get_stats(self) -> dict[str, Any]:
        """Get adapter statistics."""
        return {
            **self._stats,
            "processor_stats": self._processor.get_stats(),
            "pattern_stats": self._pattern_manager.get_stats(),
            "learner_stats": self._learner.get_stats(),
        }

    def get_recent_enhancements(self, count: int = 20) -> list[dict[str, Any]]:
        """Get recent activity enhancements."""
        return [e.to_dict() for e in self._enhancement_history[-count:]]


# Factory function
def create_router_adapter(processor: CognitiveProcessor | None = None) -> CognitiveRouterAdapter:
    """Create a new CognitiveRouterAdapter instance."""
    return CognitiveRouterAdapter(processor)
