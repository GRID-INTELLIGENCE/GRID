"""Cognitive-aware request router.

Routes requests to appropriate processing path based on:
- Cognitive load
- Processing mode (System 1 vs System 2)
- User expertise
- Pattern detection
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from cognitive.light_of_the_seven.cognitive_layer.schemas.cognitive_state import (
    CognitiveState,
    ProcessingMode,
)
from cognitive.light_of_the_seven.cognitive_layer.schemas.user_cognitive_profile import (
    ExpertiseLevel,
    UserCognitiveProfile,
)

logger = logging.getLogger(__name__)


class RouteType(str, Enum):
    """Types of processing routes."""

    # Speed-based routes
    FAST = "fast"  # Quick, System 1 processing
    DELIBERATE = "deliberate"  # Slow, System 2 processing

    # Load-based routes
    LIGHT = "light"  # Low cognitive load, full processing
    HEAVY = "heavy"  # High cognitive load, simplified processing

    # Expertise-based routes
    EXPERT = "expert"  # Minimal guidance, assume knowledge
    NOVICE = "novice"  # Maximum guidance, step-by-step

    # Pattern-based routes
    FLOW = "flow"  # Optimal flow state, maintain engagement
    INVESTIGATE = "investigate"  # Deviation detected, investigate
    AUTOMATE = "automate"  # Repetition detected, automation opportunity


@dataclass
class Route:
    """Represents a processing route."""

    route_type: RouteType
    description: str
    adaptations: list[str]
    confidence: float  # 0-1


@dataclass
class Adaptation:
    """Represents a cognitive adaptation to apply."""

    adaptation_type: str
    description: str
    parameters: dict[str, Any]


class CognitiveRouter:
    """Cognitive-aware request router.

    Routes requests to appropriate processing paths based on cognitive state,
    user profile, and detected patterns.
    """

    def __init__(self):
        """Initialize the cognitive router."""
        # Route thresholds
        self.load_heavy_threshold = 7.0
        self.load_light_threshold = 3.0

        # Expertise thresholds
        self.expert_thresholds = {
            ExpertiseLevel.EXPERT: 0.9,
            ExpertiseLevel.ADVANCED: 0.7,
            ExpertiseLevel.INTERMEDIATE: 0.5,
            ExpertiseLevel.BEGINNER: 0.3,
            ExpertiseLevel.NOVICE: 0.1,
        }

        logger.info("CognitiveRouter initialized")

    def route(
        self,
        request: dict[str, Any],
        cognitive_state: CognitiveState,
        profile: UserCognitiveProfile,
        detected_patterns: list[str] | None = None,
    ) -> Route:
        """Route request to appropriate handler based on cognitive context.

        Args:
            request: Request data
            cognitive_state: Current cognitive state
            profile: User cognitive profile
            detected_patterns: Optional list of detected patterns

        Returns:
            Route with routing decision and adaptations
        """
        # Determine primary route based on multiple factors
        route_type, confidence = self._determine_route_type(cognitive_state, profile, detected_patterns)

        # Generate adaptations
        adaptations = self.get_adaptations(cognitive_state, profile)

        # Generate description
        description = self._generate_route_description(route_type, cognitive_state, profile)

        return Route(
            route_type=route_type,
            description=description,
            adaptations=adaptations,
            confidence=confidence,
        )

    def _determine_route_type(
        self,
        cognitive_state: CognitiveState,
        profile: UserCognitiveProfile,
        detected_patterns: list[str] | None = None,
    ) -> tuple[RouteType, float]:
        """Determine the primary route type."""
        detected_patterns = detected_patterns or []
        scores: dict[RouteType, float] = {}

        # 1. Processing mode score
        if cognitive_state.processing_mode == ProcessingMode.SYSTEM_1:
            scores[RouteType.FAST] = cognitive_state.mode_confidence * 0.8
        else:
            scores[RouteType.DELIBERATE] = cognitive_state.mode_confidence * 0.8

        # 2. Cognitive load score
        if cognitive_state.estimated_load > self.load_heavy_threshold:
            scores[RouteType.HEAVY] = (cognitive_state.estimated_load - self.load_heavy_threshold) / 3.0
        elif cognitive_state.estimated_load < self.load_light_threshold:
            scores[RouteType.LIGHT] = (
                self.load_light_threshold - cognitive_state.estimated_load
            ) / self.load_light_threshold

        # 3. Expertise score
        expertise_score = self.expert_thresholds.get(profile.expertise_level, 0.5)
        if expertise_score > 0.7:
            scores[RouteType.EXPERT] = expertise_score
        elif expertise_score < 0.3:
            scores[RouteType.NOVICE] = 1.0 - expertise_score

        # 4. Pattern-based scores
        if "flow" in detected_patterns:
            scores[RouteType.FLOW] = 0.9
        if "deviation" in detected_patterns:
            scores[RouteType.INVESTIGATE] = 0.8
        if "repetition" in detected_patterns:
            scores[RouteType.AUTOMATE] = 0.7

        # Determine highest scoring route
        if not scores:
            return RouteType.LIGHT, 0.5

        best_route = max(scores.items(), key=lambda x: x[1])
        return best_route

    def get_adaptations(
        self,
        cognitive_state: CognitiveState,
        profile: UserCognitiveProfile,
    ) -> list[str]:
        """Get response adaptation based on cognitive state.

        Args:
            cognitive_state: Current cognitive state
            profile: User cognitive profile

        Returns:
            List of adaptation descriptions
        """
        adaptations: list[str] = []

        # Load-based adaptations
        if cognitive_state.estimated_load > 7.0:
            adaptations.append("simplify_response")
            adaptations.append("use_scaffolding")
        elif cognitive_state.estimated_load > 5.0:
            adaptations.append("chunk_information")

        # Processing mode adaptations
        if cognitive_state.processing_mode == ProcessingMode.SYSTEM_1:
            adaptations.append("be_concise")
        else:
            adaptations.append("provide_detail")

        # Expertise adaptations
        if profile.expertise_level == ExpertiseLevel.NOVICE:
            adaptations.extend(["add_examples", "add_explanations", "step_by_step"])
        elif profile.expertise_level == ExpertiseLevel.BEGINNER:
            adaptations.extend(["add_examples", "provide_context"])
        elif profile.expertise_level == ExpertiseLevel.EXPERT:
            adaptations.append("minimal_explanation")

        # Mental model adaptations
        if cognitive_state.mental_model_alignment < 0.5:
            adaptations.append("align_with_expectations")

        return adaptations

    def _generate_route_description(
        self,
        route_type: RouteType,
        cognitive_state: CognitiveState,
        profile: UserCognitiveProfile,
    ) -> str:
        """Generate human-readable route description."""
        parts = [f"Processing via {route_type.value} route"]

        if route_type == RouteType.FAST:
            parts.append("(System 1 - quick, intuitive processing)")
        elif route_type == RouteType.DELIBERATE:
            parts.append("(System 2 - slow, analytical processing)")
        elif route_type == RouteType.HEAVY:
            parts.append(f"(high load: {cognitive_state.estimated_load:.1f}/10)")
        elif route_type == RouteType.LIGHT:
            parts.append(f"(low load: {cognitive_state.estimated_load:.1f}/10)")
        elif route_type == RouteType.EXPERT:
            parts.append(f"(expert user: {profile.expertise_level.value})")
        elif route_type == RouteType.NOVICE:
            parts.append(f"(novice user: {profile.expertise_level.value})")
        elif route_type == RouteType.FLOW:
            parts.append("(optimal flow state)")
        elif route_type == RouteType.INVESTIGATE:
            parts.append("(deviation detected)")
        elif route_type == RouteType.AUTOMATE:
            parts.append("(repetition detected)")

        return " ".join(parts)

    def get_processing_parameters(
        self,
        route: Route,
        request: dict[str, Any],
    ) -> dict[str, Any]:
        """Get processing parameters for a route.

        Args:
            route: Route to get parameters for
            request: Original request

        Returns:
            Dictionary of processing parameters
        """
        params = {
            "route_type": route.route_type.value,
            "adaptations": route.adaptations,
            "confidence": route.confidence,
        }

        # Route-specific parameters
        if route.route_type == RouteType.FAST:
            params.update(
                {
                    "max_tokens": 500,
                    "temperature": 0.7,
                    "detail_level": "minimal",
                }
            )
        elif route.route_type == RouteType.DELIBERATE:
            params.update(
                {
                    "max_tokens": 2000,
                    "temperature": 0.5,
                    "detail_level": "high",
                }
            )
        elif route.route_type == RouteType.HEAVY:
            params.update(
                {
                    "max_tokens": 300,
                    "temperature": 0.6,
                    "detail_level": "minimal",
                    "use_scaffolding": True,
                }
            )
        elif route.route_type == RouteType.LIGHT:
            params.update(
                {
                    "max_tokens": 1500,
                    "temperature": 0.8,
                    "detail_level": "medium",
                }
            )
        elif route.route_type == RouteType.NOVICE:
            params.update(
                {
                    "max_tokens": 1000,
                    "temperature": 0.6,
                    "detail_level": "high",
                    "include_examples": True,
                    "step_by_step": True,
                }
            )
        elif route.route_type == RouteType.EXPERT:
            params.update(
                {
                    "max_tokens": 1000,
                    "temperature": 0.9,
                    "detail_level": "low",
                    "minimal_explanation": True,
                }
            )

        return params

    def should_cache_result(self, route: Route) -> bool:
        """Determine if results should be cached based on route.

        Args:
            route: Route to evaluate

        Returns:
            True if caching is recommended
        """
        # Cache for expert and light routes (likely repeatable)
        return route.route_type in [RouteType.EXPERT, RouteType.LIGHT]

    def get_timeout_seconds(self, route: Route) -> float:
        """Get appropriate timeout for a route.

        Args:
            route: Route to evaluate

        Returns:
            Timeout in seconds
        """
        timeouts = {
            RouteType.FAST: 5.0,
            RouteType.HEAVY: 30.0,
            RouteType.LIGHT: 10.0,
            RouteType.DELIBERATE: 60.0,
            RouteType.EXPERT: 15.0,
            RouteType.NOVICE: 45.0,
            RouteType.FLOW: 20.0,
            RouteType.INVESTIGATE: 120.0,
            RouteType.AUTOMATE: 30.0,
        }
        return timeouts.get(route.route_type, 30.0)


class CognitiveRequestHandler:
    """Base class for cognitive-aware request handlers."""

    def __init__(self, router: CognitiveRouter | None = None):
        """Initialize handler.

        Args:
            router: Optional custom router
        """
        self.router = router or CognitiveRouter()

    async def handle(
        self,
        request: dict[str, Any],
        cognitive_state: CognitiveState,
        profile: UserCognitiveProfile,
        detected_patterns: list[str] | None = None,
    ) -> dict[str, Any]:
        """Handle a request with cognitive awareness.

        Args:
            request: Request data
            cognitive_state: Current cognitive state
            profile: User cognitive profile
            detected_patterns: Optional detected patterns

        Returns:
            Response dictionary
        """
        # Route the request
        route = self.router.route(request, cognitive_state, profile, detected_patterns)

        logger.debug(f"Routing request via {route.route_type.value}: {route.description}")

        # Get processing parameters
        params = self.router.get_processing_parameters(route, request)

        # Process the request (to be implemented by subclasses)
        result = await self._process_request(request, route, params)

        # Add route metadata to result
        result["route"] = {
            "type": route.route_type.value,
            "description": route.description,
            "adaptations": route.adaptations,
            "confidence": route.confidence,
        }

        return result

    async def _process_request(
        self,
        request: dict[str, Any],
        route: Route,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Process the request (to be overridden).

        Args:
            request: Request data
            route: Route information
            params: Processing parameters

        Returns:
            Processing result
        """
        raise NotImplementedError("Subclasses must implement _process_request")


# Global instance for convenience
_cognitive_router: CognitiveRouter | None = None


def get_cognitive_router() -> CognitiveRouter:
    """Get the global cognitive router instance.

    Returns:
        Cognitive router singleton
    """
    global _cognitive_router
    if _cognitive_router is None:
        _cognitive_router = CognitiveRouter()
    return _cognitive_router
