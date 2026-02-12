"""
Enhanced Cognitive Engine with GRID XAI Integration.

Bridges cognitive architecture with GRID's native XAI framework
to provide comprehensive explainable AI with cognitive context.

Architecture Features:
- Phased execution pipeline with circuit breakers
- Tiered pattern detection (fast scan → deep analysis)
- Robust error handling with graceful degradation
- Operational metrics and observability hooks
- State validation and sanity checks

Aligned with GRID Cognitive Architecture codemap:
- Interaction Tracking (1a-1f)
- Pattern Detection (2a-2e)
- Scaffolding (3a-3f)
- Routing (4a-4f)
- Profile Learning (5a-5f)
- XAI (6a-6f)
- InteractionTracker Patterns (7a-7e)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from cognitive.light_of_the_seven.cognitive_layer.cognitive_load.load_estimator import (
    CognitiveLoadEstimator,
)
from cognitive.light_of_the_seven.cognitive_layer.cognitive_load.scaffolding import (
    ScaffoldingManager,
)
from cognitive.light_of_the_seven.cognitive_layer.schemas.cognitive_state import (
    CognitiveState,
)
from cognitive.light_of_the_seven.cognitive_layer.schemas.user_cognitive_profile import (
    UserCognitiveProfile,
)
from cognitive.patterns import PatternMatcher
from cognitive.temporal.temporal_router import TemporalRouter
from cognitive.xai.explanation_generator import ExplanationGenerator
from grid.xai.explainer import XAIExplainer

logger = logging.getLogger(__name__)


# ============================================================================
# Constants and Configuration
# ============================================================================


class ProcessingTier(str, Enum):
    """Processing tiers for tiered execution."""

    FAST = "fast"  # Quick checks only
    STANDARD = "standard"  # Normal processing
    DEEP = "deep"  # Full analysis


@dataclass
class EngineConfig:
    """Configuration for EnhancedCognitiveEngine."""

    # Load thresholds
    load_min: float = 0.0
    load_max: float = 10.0
    scaffolding_threshold: float = 7.0
    high_load_threshold: float = 5.0

    # Timeouts (seconds)
    pattern_detection_timeout: float = 5.0
    xai_generation_timeout: float = 3.0
    profile_update_timeout: float = 2.0

    # Cache settings
    max_interactions_per_user: int = 100
    state_cache_ttl_seconds: int = 3600

    # Circuit breaker settings
    max_consecutive_failures: int = 3
    circuit_reset_seconds: int = 60

    # Tiered processing thresholds
    fast_processing_load_threshold: float = 3.0
    deep_processing_complexity_threshold: float = 0.8


@dataclass
class ProcessingMetrics:
    """Metrics for a single processing run."""

    start_time: float = field(default_factory=time.time)
    phase_timings: dict[str, float] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    tier: ProcessingTier = ProcessingTier.STANDARD

    def record_phase(self, phase_name: str, duration: float) -> None:
        """Record timing for a processing phase."""
        self.phase_timings[phase_name] = duration

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)

    @property
    def total_duration(self) -> float:
        """Get total processing duration."""
        return time.time() - self.start_time

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_duration_ms": self.total_duration * 1000,
            "phase_timings_ms": {k: v * 1000 for k, v in self.phase_timings.items()},
            "errors": self.errors,
            "warnings": self.warnings,
            "tier": self.tier.value,
        }


@dataclass
class CircuitBreaker:
    """Circuit breaker for component isolation."""

    name: str
    max_failures: int = 3
    reset_seconds: int = 60

    _failure_count: int = field(default=0, init=False)
    _last_failure_time: float | None = field(default=None, init=False)
    _is_open: bool = field(default=False, init=False)

    def record_success(self) -> None:
        """Record a successful operation."""
        self._failure_count = 0
        self._is_open = False

    def record_failure(self) -> None:
        """Record a failed operation."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._failure_count >= self.max_failures:
            self._is_open = True
            logger.warning(f"Circuit breaker '{self.name}' opened after {self._failure_count} failures")

    def is_available(self) -> bool:
        """Check if the circuit is available (closed or half-open)."""
        if not self._is_open:
            return True

        # Check if enough time has passed to try again
        if self._last_failure_time and (time.time() - self._last_failure_time) > self.reset_seconds:
            logger.info(f"Circuit breaker '{self.name}' entering half-open state")
            return True

        return False

    def reset(self) -> None:
        """Reset the circuit breaker."""
        self._failure_count = 0
        self._is_open = False
        self._last_failure_time = None


class CognitiveEngineError(Exception):
    """Base exception for cognitive engine errors."""

    pass


class InvalidLoadStateError(CognitiveEngineError):
    """Raised when cognitive load is in an invalid state."""

    pass


class ProcessingTimeoutError(CognitiveEngineError):
    """Raised when processing exceeds timeout."""

    pass


class CircuitOpenError(CognitiveEngineError):
    """Raised when a circuit breaker is open."""

    pass


# ============================================================================
# Enhanced Cognitive Engine
# ============================================================================


class EnhancedCognitiveEngine:
    """
    Enhanced Cognitive Engine with GRID XAI integration.

    Features:
    - Phased execution pipeline
    - Circuit breakers for fault isolation
    - Tiered pattern detection
    - Comprehensive metrics and observability
    - Graceful degradation on failures
    """

    def __init__(
        self,
        xai_trace_dir: str | Path = "e:/grid/logs/xai_traces",
        config: EngineConfig | None = None,
    ):
        """Initialize enhanced cognitive engine with XAI integration.

        Args:
            xai_trace_dir: Directory for XAI trace files
            config: Optional engine configuration
        """
        self.config = config or EngineConfig()

        # Core cognitive components
        self.load_estimator = CognitiveLoadEstimator()
        self.scaffolding_manager = ScaffoldingManager()
        self.pattern_matcher = PatternMatcher()
        self.temporal_router = TemporalRouter()
        self.explanation_generator = ExplanationGenerator()

        # GRID XAI integration
        self.xai_explainer = XAIExplainer(trace_dir=Path(xai_trace_dir))

        # State management with bounded caches
        self._state_cache: dict[str, tuple[CognitiveState, datetime]] = {}
        self._interaction_history: dict[str, list[dict[str, Any]]] = {}

        # Circuit breakers for component isolation
        self._circuit_breakers = {
            "pattern_detection": CircuitBreaker(
                "pattern_detection",
                max_failures=self.config.max_consecutive_failures,
                reset_seconds=self.config.circuit_reset_seconds,
            ),
            "xai_generation": CircuitBreaker(
                "xai_generation",
                max_failures=self.config.max_consecutive_failures,
                reset_seconds=self.config.circuit_reset_seconds,
            ),
            "profile_update": CircuitBreaker(
                "profile_update",
                max_failures=self.config.max_consecutive_failures,
                reset_seconds=self.config.circuit_reset_seconds,
            ),
        }

        # Metrics tracking
        self._total_requests = 0
        self._failed_requests = 0
        self._degraded_requests = 0

        logger.info("Enhanced Cognitive Engine initialized with circuit breakers")

    # ========================================================================
    # Main Entry Point with Phased Execution
    # ========================================================================

    async def track_interaction_with_xai(
        self,
        user_id: str,
        action: str,
        metadata: dict[str, Any] | None = None,
        case_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Track user interaction with comprehensive XAI explanation.

        Uses phased execution pipeline:
        1. Input validation and preparation
        2. Load estimation with sanity checks
        3. Tiered pattern detection
        4. Scaffolding (if needed)
        5. Routing decision
        6. Profile update (async, non-blocking)
        7. XAI explanation generation

        Args:
            user_id: User identifier
            action: Action performed
            metadata: Additional event metadata
            case_id: Optional case identifier

        Returns:
            Comprehensive cognitive state with XAI explanations
        """
        metrics = ProcessingMetrics()
        self._total_requests += 1

        try:
            # Phase 1: Input Validation and Preparation
            phase_start = time.time()
            interaction, profile, operation = await self._phase_prepare(user_id, action, metadata, case_id)
            metrics.record_phase("prepare", time.time() - phase_start)

            # Phase 2: Load Estimation with Sanity Checks
            phase_start = time.time()
            cognitive_state = self._phase_estimate_load(operation, profile, metrics)
            metrics.record_phase("load_estimation", time.time() - phase_start)

            # Determine processing tier based on load
            metrics.tier = self._determine_processing_tier(cognitive_state, operation)

            # Phase 3: Pattern Detection (tiered)
            phase_start = time.time()
            patterns = await self._phase_detect_patterns(operation, metrics)
            metrics.record_phase("pattern_detection", time.time() - phase_start)

            # Phase 4: Scaffolding (conditional)
            phase_start = time.time()
            scaffolding_result = self._phase_apply_scaffolding(cognitive_state, profile, operation, metrics)
            metrics.record_phase("scaffolding", time.time() - phase_start)

            # Phase 5: Routing Decision
            phase_start = time.time()
            temporal_route = self._phase_route(cognitive_state, profile, operation)
            cognitive_state.context["temporal_route"] = temporal_route
            metrics.record_phase("routing", time.time() - phase_start)

            # Phase 6: Profile Update (non-blocking, with circuit breaker)
            phase_start = time.time()
            await self._phase_update_profile(user_id, cognitive_state, patterns, metrics)
            metrics.record_phase("profile_update", time.time() - phase_start)

            # Phase 7: XAI Explanation Generation (with circuit breaker)
            phase_start = time.time()
            xai_explanation = await self._phase_generate_xai(
                interaction, cognitive_state, patterns, temporal_route, metrics
            )
            metrics.record_phase("xai_generation", time.time() - phase_start)

            # Cache state
            self._state_cache[user_id] = (cognitive_state, datetime.now())

            # Build result
            result = {
                "cognitive_state": cognitive_state,
                "detected_patterns": patterns,
                "xai_explanation": xai_explanation,
                "temporal_route": temporal_route,
                "scaffolding_applied": scaffolding_result is not None,
                "scaffolding_result": scaffolding_result,
                "processing_metrics": metrics.to_dict(),
            }

            if metrics.errors:
                self._degraded_requests += 1
                result["degraded"] = True
                result["degradation_reasons"] = metrics.errors

            return result

        except CognitiveEngineError as e:
            self._failed_requests += 1
            logger.error(f"Cognitive engine error for user {user_id}: {e}")
            return self._create_fallback_response(user_id, action, str(e), metrics)

        except Exception as e:
            self._failed_requests += 1
            logger.exception(f"Unexpected error in cognitive engine for user {user_id}")
            return self._create_fallback_response(user_id, action, str(e), metrics)

    # ========================================================================
    # Phase 1: Preparation
    # ========================================================================

    async def _phase_prepare(
        self,
        user_id: str,
        action: str,
        metadata: dict[str, Any] | None,
        case_id: str | None,
    ) -> tuple[dict[str, Any], UserCognitiveProfile, dict[str, Any]]:
        """Prepare interaction data, profile, and operation."""
        # Validate inputs
        if not user_id or not user_id.strip():
            raise CognitiveEngineError("Invalid user_id: cannot be empty")

        if not action or not action.strip():
            raise CognitiveEngineError("Invalid action: cannot be empty")

        # Create interaction event
        interaction = {
            "user_id": user_id,
            "action": action,
            "timestamp": datetime.now(),
            "case_id": case_id,
            "metadata": metadata or {},
        }

        # Store in bounded history
        self._store_interaction(user_id, interaction)

        # Get or create profile
        profile = await self._get_or_create_profile(user_id)

        # Convert to operation
        operation = self._interaction_to_operation(interaction)

        return interaction, profile, operation

    def _store_interaction(self, user_id: str, interaction: dict[str, Any]) -> None:
        """Store interaction with bounded history."""
        if user_id not in self._interaction_history:
            self._interaction_history[user_id] = []

        history = self._interaction_history[user_id]
        history.append(interaction)

        # Enforce bound
        if len(history) > self.config.max_interactions_per_user:
            # Remove oldest entries
            self._interaction_history[user_id] = history[-self.config.max_interactions_per_user :]

    # ========================================================================
    # Phase 2: Load Estimation with Sanity Checks
    # ========================================================================

    def _phase_estimate_load(
        self,
        operation: dict[str, Any],
        profile: UserCognitiveProfile,
        metrics: ProcessingMetrics,
    ) -> CognitiveState:
        """Estimate cognitive load with sanity checks."""
        # Validate operation inputs
        self._validate_operation_inputs(operation, metrics)

        # Create cognitive state
        cognitive_state = self.load_estimator.create_cognitive_state(operation, profile)

        # Sanity check: load must be within valid range
        if cognitive_state.estimated_load < self.config.load_min:
            metrics.add_warning(
                f"Load below minimum ({cognitive_state.estimated_load}), clamping to {self.config.load_min}"
            )
            cognitive_state.estimated_load = self.config.load_min

        if cognitive_state.estimated_load > self.config.load_max:
            metrics.add_warning(
                f"Load above maximum ({cognitive_state.estimated_load}), clamping to {self.config.load_max}"
            )
            cognitive_state.estimated_load = self.config.load_max

        # Sanity check: working memory usage must be 0-1
        if not 0.0 <= cognitive_state.working_memory_usage <= 1.0:
            raise InvalidLoadStateError(f"Invalid working memory usage: {cognitive_state.working_memory_usage}")

        return cognitive_state

    def _validate_operation_inputs(
        self,
        operation: dict[str, Any],
        metrics: ProcessingMetrics,
    ) -> None:
        """Validate operation input values."""
        load_factors = [
            "information_density",
            "novelty",
            "complexity",
            "time_pressure",
            "split_attention",
            "element_interactivity",
        ]

        for factor in load_factors:
            value = operation.get(factor, 0.5)
            if not isinstance(value, (int, float)):
                metrics.add_warning(f"Non-numeric {factor}: {value}, defaulting to 0.5")
                operation[factor] = 0.5
            elif not 0.0 <= value <= 1.0:
                metrics.add_warning(f"{factor} out of range: {value}, clamping to [0,1]")
                operation[factor] = max(0.0, min(1.0, value))

    # ========================================================================
    # Phase 3: Tiered Pattern Detection
    # ========================================================================

    async def _phase_detect_patterns(
        self,
        operation: dict[str, Any],
        metrics: ProcessingMetrics,
    ) -> dict[str, Any]:
        """Detect patterns with tiered approach and circuit breaker."""
        circuit = self._circuit_breakers["pattern_detection"]

        if not circuit.is_available():
            metrics.add_error("Pattern detection circuit open - using empty patterns")
            return self._create_empty_patterns()

        try:
            if metrics.tier == ProcessingTier.FAST:
                # Fast tier: only detect critical patterns
                patterns = await self._detect_critical_patterns(operation)
            else:
                # Standard/Deep tier: full pattern detection
                patterns = await self.pattern_matcher.recognize_all(operation)

            circuit.record_success()
            return patterns

        except Exception as e:
            circuit.record_failure()
            metrics.add_error(f"Pattern detection failed: {e}")
            logger.warning(f"Pattern detection failed, using fallback: {e}")
            return self._create_empty_patterns()

    async def _detect_critical_patterns(self, operation: dict[str, Any]) -> dict[str, Any]:
        """Detect only critical patterns for fast processing."""
        # For fast tier, only detect flow and deviation patterns
        critical_patterns = ["flow", "deviation"]
        patterns = {}

        for pattern_name in critical_patterns:
            try:
                if hasattr(self.pattern_matcher, "patterns") and pattern_name in self.pattern_matcher.patterns:
                    recognizer = self.pattern_matcher.patterns[pattern_name]
                    result = recognizer.recognize(operation)
                    patterns[pattern_name] = result
            except Exception as e:
                logger.debug(f"Failed to detect {pattern_name} pattern: {e}")

        return patterns

    def _create_empty_patterns(self) -> dict[str, Any]:
        """Create empty pattern results for fallback."""
        return {}

    # ========================================================================
    # Phase 4: Scaffolding
    # ========================================================================

    def _phase_apply_scaffolding(
        self,
        cognitive_state: CognitiveState,
        profile: UserCognitiveProfile,
        operation: dict[str, Any],
        metrics: ProcessingMetrics,
    ) -> dict[str, Any] | None:
        """Apply scaffolding if needed."""
        if cognitive_state.estimated_load <= self.config.scaffolding_threshold:
            return None

        try:
            information = operation.get("information", [])
            scaffolding = self.scaffolding_manager.progressive_disclosure(information, profile)

            cognitive_state.context["scaffolding"] = scaffolding

            return {
                "applied": True,
                "load_at_application": cognitive_state.estimated_load,
                "disclosure_result": scaffolding,
            }

        except Exception as e:
            metrics.add_error(f"Scaffolding failed: {e}")
            logger.warning(f"Scaffolding failed, continuing without: {e}")
            return None

    # ========================================================================
    # Phase 5: Routing
    # ========================================================================

    def _phase_route(
        self,
        cognitive_state: CognitiveState,
        profile: UserCognitiveProfile,
        operation: dict[str, Any],
    ) -> dict[str, Any]:
        """Determine processing route."""
        temporal_context = operation.get("temporal", {})

        try:
            return self.temporal_router.route(cognitive_state, profile, temporal_context)
        except Exception as e:
            logger.warning(f"Routing failed, using default route: {e}")
            return {
                "route_type": "standard",
                "priority": "medium",
                "temporal_adaptations": [],
            }

    # ========================================================================
    # Phase 6: Profile Update
    # ========================================================================

    async def _phase_update_profile(
        self,
        user_id: str,
        cognitive_state: CognitiveState,
        patterns: dict[str, Any],
        metrics: ProcessingMetrics,
    ) -> None:
        """Update profile with circuit breaker protection."""
        circuit = self._circuit_breakers["profile_update"]

        if not circuit.is_available():
            metrics.add_warning("Profile update circuit open - skipping update")
            return

        try:
            await self._update_profile_learning(user_id, cognitive_state, patterns)
            circuit.record_success()
        except Exception as e:
            circuit.record_failure()
            metrics.add_warning(f"Profile update failed: {e}")
            logger.warning(f"Profile update failed, continuing: {e}")

    async def _update_profile_learning(
        self,
        user_id: str,
        cognitive_state: CognitiveState,
        patterns: dict[str, Any],
    ) -> None:
        """Update user profile based on learning."""
        detected_count = sum(
            1 for detection in patterns.values() if hasattr(detection, "detected") and detection.detected
        )
        logger.debug(f"Updated profile for {user_id} based on {detected_count} detected patterns")

    # ========================================================================
    # Phase 7: XAI Generation
    # ========================================================================

    async def _phase_generate_xai(
        self,
        interaction: dict[str, Any],
        cognitive_state: CognitiveState,
        patterns: dict[str, Any],
        temporal_route: dict[str, Any],
        metrics: ProcessingMetrics,
    ) -> dict[str, Any]:
        """Generate XAI explanation with circuit breaker protection."""
        circuit = self._circuit_breakers["xai_generation"]

        if not circuit.is_available():
            metrics.add_error("XAI generation circuit open - using minimal explanation")
            return self._create_minimal_xai_explanation(interaction, cognitive_state)

        try:
            explanation = await self._generate_xai_explanation(interaction, cognitive_state, patterns, temporal_route)
            circuit.record_success()
            return explanation
        except Exception as e:
            circuit.record_failure()
            metrics.add_error(f"XAI generation failed: {e}")
            logger.warning(f"XAI generation failed, using minimal: {e}")
            return self._create_minimal_xai_explanation(interaction, cognitive_state)

    async def _generate_xai_explanation(
        self,
        interaction: dict[str, Any],
        cognitive_state: CognitiveState,
        patterns: dict[str, Any],
        temporal_route: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate comprehensive XAI explanation with cognitive context."""
        decision_id = f"{interaction['user_id']}_{interaction['action']}_{datetime.now().isoformat()}"

        # Build cognitive context
        load_type = cognitive_state.load_type
        processing_mode = cognitive_state.processing_mode

        cognitive_context = {
            "estimated_load": cognitive_state.estimated_load,
            "load": cognitive_state.estimated_load,  # Alias
            "load_type": load_type if isinstance(load_type, str) else load_type.value,
            "processing_mode": processing_mode if isinstance(processing_mode, str) else processing_mode.value,
            "working_memory_usage": cognitive_state.working_memory_usage,
            "mental_model_alignment": cognitive_state.mental_model_alignment,
            "decision_complexity": cognitive_state.decision_complexity,
            "time_pressure": cognitive_state.time_pressure,
        }

        # Build pattern context
        pattern_context = [
            {
                "pattern": pattern_name,
                "detected": detection.detected,
                "confidence": detection.confidence,
                "features": detection.features,
                "recommendations": detection.recommendations,
            }
            for pattern_name, detection in patterns.items()
            if hasattr(detection, "detected") and detection.detected
        ]

        # Build temporal context
        temporal_context = {
            "route_type": temporal_route.get("route_type"),
            "priority": temporal_route.get("priority"),
            "coffee_mode": temporal_route.get("coffee_mode"),
            "temporal_adaptations": temporal_route.get("temporal_adaptations", []),
        }

        # Generate rationale
        rationale = self._generate_cognitive_rationale(cognitive_state, patterns, temporal_route)

        # Use GRID's XAIExplainer
        try:
            xai_result = self.xai_explainer.synthesize_explanation(
                decision_id=decision_id,
                context={
                    "interaction": interaction,
                    "cognitive": cognitive_context,
                    "patterns": pattern_context,
                    "temporal": temporal_context,
                },
                rationale=rationale,
                cognitive_state=cognitive_context,
                detected_patterns=pattern_context,
            )
            return xai_result
        except Exception as e:
            logger.warning(f"XAI explainer failed: {e}")
            # Return a minimal valid explanation
            return {
                "decision_id": decision_id,
                "cognitive_context": cognitive_context,
                "rationale": rationale,
                "resonance_explanation": "Unable to generate full explanation",
            }

    def _generate_cognitive_rationale(
        self,
        cognitive_state: CognitiveState,
        patterns: dict[str, Any],
        temporal_route: dict[str, Any],
    ) -> str:
        """Generate cognitive rationale for XAI explanation."""
        rationale_parts = []

        load_type = cognitive_state.load_type
        processing_mode = cognitive_state.processing_mode
        load_type_str = load_type if isinstance(load_type, str) else load_type.value
        processing_mode_str = processing_mode if isinstance(processing_mode, str) else processing_mode.value

        if cognitive_state.estimated_load > self.config.scaffolding_threshold:
            rationale_parts.append(
                f"High cognitive load ({cognitive_state.estimated_load:.1f}/10) "
                f"triggered adaptive scaffolding for {load_type_str} load"
            )
        elif cognitive_state.estimated_load > self.config.high_load_threshold:
            rationale_parts.append(
                f"Moderate cognitive load ({cognitive_state.estimated_load:.1f}/10) "
                f"required {processing_mode_str} processing mode"
            )
        else:
            rationale_parts.append(
                f"Low cognitive load ({cognitive_state.estimated_load:.1f}/10) enabled {processing_mode_str} processing"
            )

        # Pattern-based rationale
        detected_patterns = [
            name for name, detection in patterns.items() if hasattr(detection, "detected") and detection.detected
        ]
        if detected_patterns:
            rationale_parts.append(f"Detected patterns: {', '.join(detected_patterns)} influenced response adaptation")

        # Temporal rationale
        if temporal_route.get("temporal_adaptations"):
            rationale_parts.append(
                f"Temporal routing selected {temporal_route.get('route_type')} path "
                f"with {', '.join(temporal_route.get('temporal_adaptations', []))}"
            )

        return ". ".join(rationale_parts)

    def _create_minimal_xai_explanation(
        self,
        interaction: dict[str, Any],
        cognitive_state: CognitiveState,
    ) -> dict[str, Any]:
        """Create minimal XAI explanation for fallback."""
        load_type = cognitive_state.load_type
        processing_mode = cognitive_state.processing_mode

        return {
            "decision_id": f"{interaction['user_id']}_{interaction['action']}_fallback",
            "cognitive_context": {
                "estimated_load": cognitive_state.estimated_load,
                "load": cognitive_state.estimated_load,
                "load_type": load_type if isinstance(load_type, str) else load_type.value,
                "processing_mode": processing_mode if isinstance(processing_mode, str) else processing_mode.value,
            },
            "rationale": f"Cognitive load: {cognitive_state.estimated_load:.1f}/10",
            "resonance_explanation": "Minimal explanation due to processing constraints",
            "fallback": True,
        }

    async def _get_or_create_profile(self, user_id: str) -> UserCognitiveProfile:
        """Get existing profile or create default."""
        profile_store = getattr(self, "profile_store", None)
        if profile_store is None:
            try:
                from cognitive.profile_store import get_profile_store

                profile_store = get_profile_store()
                self.profile_store = profile_store
            except Exception as exc:
                logger.debug(f"Profile store unavailable: {exc}")
                profile_store = None

        if profile_store:
            profile = await profile_store.get_profile(user_id)
            if profile:
                return profile

        return UserCognitiveProfile(
            user_id=user_id,
            username=f"User_{user_id[:8]}",
        )

    def _get_cached_state(self, user_id: str) -> CognitiveState | None:
        """Get cached cognitive state if within TTL."""
        cached = self._state_cache.get(user_id)
        if not cached:
            return None

        state, timestamp = cached
        if (datetime.now() - timestamp).total_seconds() > self.config.state_cache_ttl_seconds:
            del self._state_cache[user_id]
            return None

        return state

    def _create_fallback_response(
        self,
        user_id: str,
        action: str,
        reason: str,
        metrics: ProcessingMetrics,
    ) -> dict[str, Any]:
        """Create a safe fallback response when processing fails."""
        cognitive_state = self._get_cached_state(user_id)
        if cognitive_state is None:
            cognitive_state = CognitiveState(
                context={"user_id": user_id, "action": action},
            )

        minimal_xai = self._create_minimal_xai_explanation(
            {"user_id": user_id, "action": action},
            cognitive_state,
        )

        return {
            "cognitive_state": cognitive_state,
            "detected_patterns": {},
            "xai_explanation": minimal_xai,
            "temporal_route": {
                "route_type": "fallback",
                "priority": "low",
                "temporal_adaptations": [],
            },
            "scaffolding_applied": False,
            "scaffolding_result": None,
            "processing_metrics": metrics.to_dict(),
            "degraded": True,
            "degradation_reasons": [reason],
        }

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _determine_processing_tier(
        self,
        cognitive_state: CognitiveState,
        operation: dict[str, Any],
    ) -> ProcessingTier:
        """Determine processing tier based on load and complexity."""
        if cognitive_state.estimated_load < self.config.fast_processing_load_threshold:
            return ProcessingTier.FAST

        complexity = operation.get("complexity", 0.5)
        if complexity > self.config.deep_processing_complexity_threshold:
            return ProcessingTier.DEEP

        return ProcessingTier.STANDARD

    def _interaction_to_operation(self, interaction: dict[str, Any]) -> dict[str, Any]:
        """Convert interaction to operation description for load estimation."""
        metadata = interaction.get("metadata", {})

        base_operation = {
            "information_density": metadata.get("information_density", 0.5),
            "novelty": metadata.get("novelty", 0.5),
            "complexity": metadata.get("complexity", 0.5),
            "time_pressure": metadata.get("time_pressure", 0.0),
            "split_attention": metadata.get("split_attention", 0.0),
            "element_interactivity": metadata.get("element_interactivity", 0.5),
        }

        # Adjust based on action type
        action = interaction.get("action", "")
        if action == "case_start":
            base_operation.update(
                {
                    "complexity": max(base_operation["complexity"], 0.7),
                    "novelty": max(base_operation["novelty"], 0.6),
                }
            )
        elif action == "query":
            base_operation.update(
                {
                    "information_density": max(base_operation["information_density"], 0.6),
                    "complexity": min(base_operation["complexity"], 0.4),
                }
            )
        elif action == "retry":
            base_operation.update(
                {
                    "novelty": min(base_operation["novelty"], 0.2),
                    "complexity": max(base_operation["complexity"], 0.8),
                }
            )
        elif action == "error":
            base_operation.update(
                {
                    "complexity": max(base_operation["complexity"], 0.9),
                    "time_pressure": max(base_operation["time_pressure"], 0.3),
                }
            )

        if metadata:
            base_operation.update(metadata)

        return base_operation
