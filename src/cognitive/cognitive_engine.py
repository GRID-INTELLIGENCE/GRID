"""Cognitive Engine: Orchestrates all cognitive components.

The Cognitive Engine is the central orchestrator for GRID's cognitive architecture.
It manages:
- Cognitive state tracking and evolution
- Load estimation and adaptation
- Processing mode switching (System 1 <-> System 2)
- Mental model management
- Pattern-driven recommendations
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import Mock

from cognitive.light_of_the_seven.cognitive_layer.cognitive_load.load_estimator import CognitiveLoadEstimator
from cognitive.light_of_the_seven.cognitive_layer.cognitive_load.scaffolding import ScaffoldingManager
from cognitive.light_of_the_seven.cognitive_layer.schemas.cognitive_state import (
    CognitiveLoadType,
    CognitiveState,
    ProcessingMode,
)
from cognitive.light_of_the_seven.cognitive_layer.schemas.decision_context import DecisionContext
from cognitive.light_of_the_seven.cognitive_layer.schemas.user_cognitive_profile import UserCognitiveProfile
from cognitive.temporal.temporal_router import TemporalRouter  # Added
from cognitive.xai.explanation_generator import ExplanationGenerator  # Added

from .context.DEFINITION import ActivityDomain

logger = logging.getLogger(__name__)


class InteractionEvent:
    """Represents a user interaction event for tracking."""

    def __init__(
        self,
        user_id: str,
        action: str,
        timestamp: datetime | None = None,
        case_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Initialize an interaction event.

        Args:
            user_id: User identifier
            action: Action performed (e.g., "case_start", "query", "choice")
            timestamp: Event timestamp (defaults to now)
            case_id: Optional associated case ID
            metadata: Additional event metadata
        """
        self.user_id = user_id
        self.action = action
        self.timestamp = timestamp or datetime.now()
        self.case_id = case_id
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "action": self.action,
            "timestamp": self.timestamp.isoformat(),
            "case_id": self.case_id,
            "metadata": self.metadata,
        }


class Adaptation:
    """Represents a cognitive adaptation recommendation."""

    def __init__(
        self,
        adaptation_type: str,
        description: str,
        priority: str,
        parameters: dict[str, Any] | None = None,
    ):
        """Initialize adaptation.

        Args:
            adaptation_type: Type of adaptation (e.g., "simplify", "expand", "scaffold")
            description: Human-readable description
            priority: Priority level (low, medium, high)
            parameters: Adaptation-specific parameters
        """
        self.adaptation_type = adaptation_type
        self.description = description
        self.priority = priority
        self.parameters = parameters or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "adaptation_type": self.adaptation_type,
            "description": self.description,
            "priority": self.priority,
            "parameters": self.parameters,
        }


class ScaffoldingAction:
    """Represents a scaffolding action for high load situations."""

    def __init__(
        self,
        action_type: str,
        content: str,
        position: str = "prepend",
    ):
        """Initialize scaffolding action.

        Args:
            action_type: Type of action (e.g., "hint", "example", "step_by_step")
            content: Content to add
            position: Where to place content (prepend, append, insert)
        """
        self.action_type = action_type
        self.content = content
        self.position = position

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "action_type": self.action_type,
            "content": self.content,
            "position": self.position,
        }


class CognitiveEngine:
    """Orchestrates all cognitive components for GRID.

    The Cognitive Engine integrates cognitive state tracking, load estimation,
    processing mode detection, mental model management, and pattern-driven
    recommendations to create a cognitively-aware intelligence system.
    """

    def __init__(
        self,
        profile_store: Any | None = None,
        pattern_matcher: Any | None = None,
    ):
        """Initialize the cognitive engine.

        Args:
            profile_store: Optional profile store for user profiles
            pattern_matcher: Optional pattern matcher for cognition patterns
        """
        self.load_estimator = CognitiveLoadEstimator()
        self.scaffolding_manager = ScaffoldingManager()
        self.profile_store = profile_store
        self.pattern_matcher = pattern_matcher

        # Get metrics collector
        self.metrics_collector = Mock()  # Placeholder for metrics collector

        # In-memory cognitive state cache
        self._state_cache: dict[str, tuple[CognitiveState, datetime]] = {}

        # Processing mode history for mode detection
        self._mode_history: dict[str, list[tuple[ProcessingMode, datetime]]] = {}

        # Recent interactions for pattern detection (last 100 per user)
        self._interaction_history: dict[str, list[InteractionEvent]] = {}

        # Processing mode history for mode detection
        self._mode_history: dict[str, list[tuple[ProcessingMode, datetime]]] = {}

        # Temporal router for temporal awareness
        self.temporal_router = TemporalRouter()  # Add temporal router

        # XAI explanation generator
        self.explanation_generator = ExplanationGenerator()  # Add XAI generator

        logger.info("Cognitive Engine initialized")

    async def track_interaction(self, event: InteractionEvent) -> CognitiveState:
        """Track user interaction and update cognitive state.

        Args:
            event: Interaction event to track

        Returns:
            Updated cognitive state for the user
        """
        # Store interaction in history
        if event.user_id not in self._interaction_history:
            self._interaction_history[event.user_id] = []
        self._interaction_history[event.user_id].append(event)

        # Limit history size
        if len(self._interaction_history[event.user_id]) > 100:
            self._interaction_history[event.user_id] = self._interaction_history[event.user_id][-100:]

        # Get or create user profile
        profile = await self._get_or_create_profile(event.user_id)

        # Create operation description for load estimation
        operation = self._interaction_to_operation(event)

        # Estimate cognitive load
        cognitive_state = self.load_estimator.create_cognitive_state(operation, profile)

        # Detect processing mode
        detected_mode = self.detect_processing_mode(cognitive_state)
        cognitive_state.processing_mode = detected_mode
        cognitive_state.mode_confidence = self._calculate_mode_confidence(event.user_id, detected_mode)

        # Check mental model alignment
        mental_alignment = await self._check_mental_model_alignment(event.user_id, event)
        cognitive_state.mental_model_alignment = mental_alignment["alignment"]
        cognitive_state.model_mismatches = mental_alignment["mismatches"]

        # Add interaction context
        cognitive_state.context.update(
            {
                "time_pressure": operation.get("time_pressure", 0.0),
                "event": event.to_dict(),
                "interaction_count": len(self._interaction_history[event.user_id]),
            }
        )
        cognitive_state.context["domain"] = ActivityDomain.SOFTWARE_DEVELOPMENT.value

        # Cache the state
        self._state_cache[event.user_id] = (cognitive_state, datetime.now())

        # Detect processing mode
        detected_mode = self.detect_processing_mode(cognitive_state)
        cognitive_state.processing_mode = detected_mode
        cognitive_state.mode_confidence = self._calculate_mode_confidence(event.user_id, detected_mode)

        # Check mental model alignment
        mental_alignment = await self._check_mental_model_alignment(event.user_id, event)
        cognitive_state.mental_model_alignment = mental_alignment["alignment"]
        cognitive_state.model_mismatches = mental_alignment["mismatches"]

        # Add interaction context
        cognitive_state.context.update(
            {
                "time_pressure": operation.get("time_pressure", 0.0),
                "event": event.to_dict(),
                "interaction_count": len(self._interaction_history[event.user_id]),
            }
        )
        cognitive_state.context["domain"] = ActivityDomain.SOFTWARE_DEVELOPMENT.value

        # Cache the state
        self._state_cache[event.user_id] = (cognitive_state, datetime.now())

        # Detect processing mode
        detected_mode = self.detect_processing_mode(cognitive_state)
        cognitive_state.processing_mode = detected_mode
        cognitive_state.mode_confidence = self._calculate_mode_confidence(event.user_id, detected_mode)

        # Check mental model alignment
        mental_alignment = await self._check_mental_model_alignment(event.user_id, event)
        cognitive_state.mental_model_alignment = mental_alignment["alignment"]
        cognitive_state.model_mismatches = mental_alignment["mismatches"]

        # Add interaction context
        cognitive_state.context.update(
            {
                "time_pressure": operation.get("time_pressure", 0.0),
                "event": event.to_dict(),
                "interaction_count": len(self._interaction_history[event.user_id]),
            }
        )
        cognitive_state.context["domain"] = ActivityDomain.SOFTWARE_DEVELOPMENT.value

        # Cache the state
        self._state_cache[event.user_id] = (cognitive_state, datetime.now())

        # Update metrics
        if hasattr(self.metrics_collector, "enabled") and self.metrics_collector.enabled:
            self.metrics_collector.set_gauge(
                "cognitive_load",
                cognitive_state.estimated_load,
                {"user_id": event.user_id, "domain": "software_development"},
            )
            self.metrics_collector.set_gauge(
                "processing_mode",
                0 if cognitive_state.processing_mode == ProcessingMode.SYSTEM_1 else 1,
                {"user_id": event.user_id},
            )
            self.metrics_collector.set_gauge(
                "mental_model_alignment", cognitive_state.mental_model_alignment, {"user_id": event.user_id}
            )
            self.metrics_collector.set_gauge(
                "processing_mode",
                0 if cognitive_state.processing_mode == ProcessingMode.SYSTEM_1 else 1,
                {"user_id": event.user_id},
            )
            self.metrics_collector.set_gauge(
                "mental_model_alignment", cognitive_state.mental_model_alignment, {"user_id": event.user_id}
            )

        logger.debug(
            f"Tracked interaction for {event.user_id}: "
            f"load={cognitive_state.estimated_load:.2f}, "
            f"mode={cognitive_state.processing_mode.value}"
        )

        return cognitive_state

    async def adapt_response(
        self,
        query: str,
        context: dict[str, Any],
        user_id: str,
    ) -> tuple[str, list[dict], str]:
        """Generate response adapted to user's cognitive state with explanations.

        Args:
            query: User query
            context: Query context
            user_id: User identifier

        Returns:
            Tuple of (adapted_query, list of adaptations, explanation)
        """
        # Get current cognitive state
        cognitive_state = await self.get_cognitive_state(user_id)
        profile = await self._get_or_create_profile(user_id)

        adaptations: list[dict] = []
        adapted_query = query

        # Extract temporal context
        temporal_context = context.get("temporal", {"pattern": "", "time_sensitivity": 0.5})

        # Get temporal routing decision
        temporal_route = self.temporal_router.route(cognitive_state, profile, temporal_context)

        # Apply temporal adaptations
        if "time_compression" in temporal_route["temporal_adaptations"]:
            adaptations.append({"type": "temporal_compression", "factor": 0.7})
        if "time_expansion" in temporal_route["temporal_adaptations"]:
            adaptations.append({"type": "temporal_expansion", "factor": 1.3})

        # High cognitive load - simplify
        if cognitive_state.estimated_load > 7.0:
            adaptations.append(
                {
                    "type": "simplify",
                    "description": "Simplifying response due to high cognitive load",
                    "priority": "high",
                    "parameters": {"load": cognitive_state.estimated_load},
                }
            )
            # Response adaptation would be applied by the caller

        # System 1 mode - be concise
        elif cognitive_state.processing_mode == ProcessingMode.SYSTEM_1:
            adaptations.append(
                {
                    "type": "concise",
                    "description": "Providing concise response for System 1 mode",
                    "priority": "medium",
                    "parameters": {"mode": "system_1"},
                }
            )

        # System 2 mode - provide more detail
        elif cognitive_state.processing_mode == ProcessingMode.SYSTEM_2:
            adaptations.append(
                {
                    "type": "expand",
                    "description": "Providing detailed response for System 2 mode",
                    "priority": "medium",
                    "parameters": {"mode": "system_2"},
                }
            )

        # Novice user - add scaffolding
        if profile.expertise_level.value in ["novice", "beginner"]:
            adaptations.append(
                {
                    "type": "scaffold",
                    "description": "Adding scaffolding for novice user",
                    "priority": "medium",
                    "parameters": {"expertise": profile.expertise_level.value},
                }
            )

        # Low mental model alignment - add explanations
        if cognitive_state.mental_model_alignment < 0.5:
            adaptations.append(
                {
                    "type": "explain",
                    "description": "Adding explanations for mental model alignment",
                    "priority": "high",
                    "parameters": {
                        "alignment": cognitive_state.mental_model_alignment,
                        "mismatches": cognitive_state.model_mismatches,
                    },
                }
            )

        # Generate XAI explanation
        explanation = self.explanation_generator.explain_adaptive_response(adaptations)

        return (adapted_query, adaptations, explanation)

    def detect_processing_mode(self, state: CognitiveState) -> ProcessingMode:
        """Detect whether user is in System 1 (fast) or System 2 (slow) mode.

        System 1: Fast, automatic, intuitive - low load, low complexity, low time pressure
        System 2: Slow, deliberate, analytical - high load, high complexity, high stakes

        Args:
            state: Current cognitive state

        Returns:
            Detected processing mode
        """
        # System 2 indicators (slow, analytical)
        system_2_score = 0.0

        # High cognitive load suggests System 2
        if state.estimated_load > 6.0:
            system_2_score += 0.3
        elif state.estimated_load > 4.0:
            system_2_score += 0.1

        # High decision complexity suggests System 2
        if state.decision_complexity > 0.7:
            system_2_score += 0.3
        elif state.decision_complexity > 0.5:
            system_2_score += 0.1

        # Time pressure suggests System 1 (need to act fast)
        if state.time_pressure > 0.7:
            system_2_score -= 0.2

        # High working memory usage suggests System 2
        if state.working_memory_usage > 0.7:
            system_2_score += 0.2

        # Decision threshold
        return ProcessingMode.SYSTEM_2 if system_2_score >= 0.3 else ProcessingMode.SYSTEM_1

    def _calculate_mode_confidence(self, user_id: str, detected_mode: ProcessingMode) -> float:
        """Calculate confidence in processing mode detection based on history.

        Args:
            user_id: User identifier
            detected_mode: Currently detected mode

        Returns:
            Confidence score (0-1)
        """
        if user_id not in self._mode_history:
            return 0.5

        # Get recent mode history (last 10 entries)
        recent_modes = self._mode_history[user_id][-10:]

        if not recent_modes:
            return 0.5

        # Count how many match the detected mode
        matches = sum(1 for mode, _ in recent_modes if mode == detected_mode)
        confidence = matches / len(recent_modes)

        return confidence

    def suggest_scaffolding(self, load: float, profile: UserCognitiveProfile | None = None) -> list[ScaffoldingAction]:
        """Suggest cognitive scaffolding for high load situations.

        Args:
            load: Current cognitive load (0-10)
            profile: Optional user profile

        Returns:
            List of scaffolding actions
        """
        actions: list[ScaffoldingAction] = []

        if load > 8.0:
            # Critical load - maximum scaffolding
            actions.append(
                ScaffoldingAction(
                    action_type="hint",
                    content="Here's a hint to get started: ",
                    position="prepend",
                )
            )
            actions.append(
                ScaffoldingAction(
                    action_type="step_by_step",
                    content="Let's break this down into steps:",
                    position="prepend",
                )
            )

        elif load > 6.0:
            # High load - moderate scaffolding
            actions.append(
                ScaffoldingAction(
                    action_type="example",
                    content="For example, consider this similar case:",
                    position="insert",
                )
            )

        # Novice users always get some scaffolding
        if profile and profile.expertise_level.value == "novice":
            actions.append(
                ScaffoldingAction(
                    action_type="explanation",
                    content="To help you understand, here's an explanation:",
                    position="append",
                )
            )

        return actions

    async def get_cognitive_state(self, user_id: str) -> CognitiveState:
        """Get the current cognitive state for a user.

        Args:
            user_id: User identifier

        Returns:
            Current cognitive state
        """
        if user_id in self._state_cache:
            state, timestamp = self._state_cache[user_id]
            # State is valid for 5 minutes
            if datetime.now() - timestamp < timedelta(minutes=5):
                return state

        # Create default state if not cached or expired
        profile = await self._get_or_create_profile(user_id)
        default_state = CognitiveState(
            estimated_load=0.0,
            load_type=CognitiveLoadType.INTRINSIC,
            processing_mode=ProcessingMode.SYSTEM_1,
            mental_model_alignment=profile.model_confidence,
            context={"user_id": user_id},
        )
        self._state_cache[user_id] = (default_state, datetime.now())

        return default_state

    async def get_decision_context(
        self,
        decision_id: str,
        user_id: str,
        description: str = "",
        options: list[dict[str, Any]] | None = None,
    ) -> DecisionContext:
        """Create decision context for a decision-making situation.

        Args:
            decision_id: Unique decision identifier
            user_id: User identifier
            description: Decision description
            options: Available options

        Returns:
            Decision context with cognitive information
        """
        # Get current cognitive state
        cognitive_state = await self.get_cognitive_state(user_id)
        profile = await self._get_or_create_profile(user_id)

        # Determine decision complexity based on cognitive state
        complexity = max(cognitive_state.estimated_load / 10.0, 0.5)

        return DecisionContext(
            decision_id=decision_id,
            description=description,
            options=options or [],
            complexity=min(complexity, 1.0),
            time_pressure=cognitive_state.context.get("time_pressure", 0.0),
            satisficing_threshold=profile.satisficing_tendency,
            metadata={"cognitive_state": cognitive_state.model_dump(mode="json")},
        )

    async def _get_or_create_profile(self, user_id: str) -> UserCognitiveProfile:
        """Get existing profile or create default.

        Args:
            user_id: User identifier

        Returns:
            User cognitive profile
        """
        if self.profile_store:
            profile = await self.profile_store.get_profile(user_id)
            if profile:
                return profile

        # Create default profile
        return UserCognitiveProfile(
            user_id=user_id,
            username=f"User_{user_id[:8]}",
        )

    async def _check_mental_model_alignment(
        self,
        user_id: str,
        event: InteractionEvent,
    ) -> dict[str, Any]:
        """Check alignment between user expectations and system behavior.

        Args:
            user_id: User identifier
            event: Current interaction event

        Returns:
            Dictionary with alignment score and list of mismatches
        """
        # Default: good alignment
        alignment = 0.8
        mismatches: list[str] = []

        # If user has history, check for patterns of frustration or confusion
        if user_id in self._interaction_history:
            recent = self._interaction_history[user_id][-20:]

            # Count negative interactions (simplified heuristic)
            negative_count = sum(
                1 for e in recent if e.metadata.get("sentiment") == "negative" or e.action in ["error", "retry"]
            )

            # Adjust alignment based on negative interactions
            if negative_count > 5:
                alignment -= 0.3
                mismatches.append("Recent negative interactions detected")
            elif negative_count > 2:
                alignment -= 0.1

            # Check for repeated similar actions (may indicate confusion)
            actions = [e.action for e in recent[-10:]]
            if len(actions) > 5 and len(set(actions)) < 3:
                alignment -= 0.2
                mismatches.append("Repetitive actions suggest confusion")

        # Clamp alignment
        alignment = max(0.0, min(1.0, alignment))

        return {"alignment": alignment, "mismatches": mismatches}

    def _interaction_to_operation(self, event: InteractionEvent) -> dict[str, Any]:
        """Convert interaction event to operation for load estimation.

        Args:
            event: Interaction event

        Returns:
            Operation dictionary for load estimator
        """
        base_operation = {
            "information_density": 0.5,
            "novelty": 0.3,
            "complexity": 0.5,
            "time_pressure": 0.0,
            "split_attention": 0.0,
            "element_interactivity": 0.5,
        }

        # Adjust based on action type
        if event.action == "case_start":
            base_operation.update({"complexity": 0.7, "novelty": 0.6})
        elif event.action == "query":
            base_operation.update({"information_density": 0.6, "complexity": 0.4})
        elif event.action == "retry":
            base_operation.update({"novelty": 0.2, "complexity": 0.8})
        elif event.action == "error":
            base_operation.update({"complexity": 0.9, "time_pressure": 0.3})

        # Include metadata
        if event.metadata:
            base_operation.update(event.metadata)

        return base_operation

    def get_interaction_history(
        self,
        user_id: str,
        limit: int = 20,
    ) -> list[InteractionEvent]:
        """Get interaction history for a user.

        Args:
            user_id: User identifier
            limit: Maximum number of events to return

        Returns:
            List of interaction events
        """
        if user_id not in self._interaction_history:
            return []

        return self._interaction_history[user_id][-limit:]

    def clear_state_cache(self, user_id: str | None = None) -> None:
        """Clear cached cognitive states.

        Args:
            user_id: Optional user ID to clear specific user's cache.
                     If None, clears all cached states.
        """
        if user_id is None:
            self._state_cache.clear()
        elif user_id in self._state_cache:
            del self._state_cache[user_id]

        logger.debug(f"Cleared state cache for {user_id or 'all users'}")

    async def _detect_patterns(self, user_id: str) -> dict[str, Any]:
        """Internal pattern detection method."""
        if not self.pattern_matcher:
            return {}

        try:
            # Get recent interactions for pattern detection
            recent_interactions = self.get_interaction_history(user_id, limit=10)

            # Convert to operation data for pattern matching
            operations = [self._interaction_to_operation(event) for event in recent_interactions]

            # Run pattern detection
            patterns = await self.pattern_matcher.recognize_all(operations)

            return patterns
        except Exception as e:
            logger.warning(f"Pattern detection failed for user {user_id}: {e}")
            return {}

    async def detect_patterns_async(self, user_id: str) -> dict[str, Any]:
        """Async pattern detection with latency monitoring."""
        start_time = time.perf_counter()
        patterns = await self._detect_patterns(user_id)
        latency_ms = (time.perf_counter() - start_time) * 1000

        if hasattr(self.metrics_collector, "enabled") and self.metrics_collector.enabled:
            for pattern_type, detection in patterns.items():
                if detection.get("detected", False):
                    if hasattr(self.metrics_collector, "histogram"):
                        self.metrics_collector.histogram(
                            "pattern_detection_latency", latency_ms, {"pattern_type": pattern_type}
                        )

        return patterns


# Global instance for convenience
_cognitive_engine: CognitiveEngine | None = None


def get_cognitive_engine() -> CognitiveEngine:
    """Get the global cognitive engine instance.

    Returns:
        Cognitive engine singleton
    """
    global _cognitive_engine
    if _cognitive_engine is None:
        _cognitive_engine = CognitiveEngine()
    return _cognitive_engine
