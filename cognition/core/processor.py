"""
Cognitive Processor - Core Cognitive Processing Engine.

Orchestrates all cognitive processing operations:
- State management and tracking
- Pattern recognition integration
- Temporal processing
- Adaptive response generation
- Cognitive load optimization
"""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any

from cognition.models.core import (
    AttentionLevel,
    CoffeeMode,
    CognitiveContext,
    CognitiveMetrics,
    CognitiveState,
    ProcessingMode,
)
from cognition.Pattern import PatternManager
from cognition.Time import TimeManager

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result of cognitive processing."""

    success: bool
    input_data: Any
    output: Any | None = None
    cognitive_context: CognitiveContext | None = None
    processing_time_ms: float = 0.0
    patterns_detected: list[str] = field(default_factory=list)
    adaptations_applied: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "output": self.output,
            "cognitive_context": self.cognitive_context.to_dict() if self.cognitive_context else None,
            "processing_time_ms": self.processing_time_ms,
            "patterns_detected": self.patterns_detected,
            "adaptations_applied": self.adaptations_applied,
            "errors": self.errors,
        }


class CognitiveProcessor:
    """
    Core Cognitive Processing Engine.

    Manages cognitive state, integrates pattern and temporal managers,
    and orchestrates adaptive processing based on cognitive context.
    """

    def __init__(self):
        self._state = CognitiveState.IDLE
        self._metrics = CognitiveMetrics()
        self._context = CognitiveContext()
        self._pattern_manager = PatternManager()
        self._time_manager = TimeManager()

        # Processing hooks
        self._pre_processors: list[Callable[[Any], Awaitable[Any]]] = []
        self._post_processors: list[Callable[[ProcessingResult], Awaitable[ProcessingResult]]] = []

        # Statistics
        self._stats = defaultdict(int)
        self._processing_history: list[ProcessingResult] = []

        # State listeners
        self._state_listeners: list[Callable[[CognitiveState, CognitiveState], None]] = []

    @property
    def state(self) -> CognitiveState:
        """Get current cognitive state."""
        return self._state

    @property
    def metrics(self) -> CognitiveMetrics:
        """Get current cognitive metrics."""
        return self._metrics

    @property
    def context(self) -> CognitiveContext:
        """Get current cognitive context."""
        return self._context

    def _set_state(self, new_state: CognitiveState) -> None:
        """Set cognitive state and notify listeners."""
        if new_state != self._state:
            old_state = self._state
            self._state = new_state
            self._context.state = new_state

            for listener in self._state_listeners:
                try:
                    listener(old_state, new_state)
                except Exception as e:
                    logger.error(f"State listener error: {e}")

    def on_state_change(self, callback: Callable[[CognitiveState, CognitiveState], None]) -> None:
        """Register a state change listener."""
        self._state_listeners.append(callback)

    def add_pre_processor(self, processor: Callable[[Any], Awaitable[Any]]) -> None:
        """Add a pre-processing hook."""
        self._pre_processors.append(processor)

    def add_post_processor(self, processor: Callable[[ProcessingResult], Awaitable[ProcessingResult]]) -> None:
        """Add a post-processing hook."""
        self._post_processors.append(processor)

    async def process_input(self, input_data: Any) -> ProcessingResult:
        """
        Process input through the cognitive pipeline.

        Steps:
        1. Pre-processing hooks
        2. State transition to PROCESSING
        3. Pattern detection
        4. Temporal context analysis
        5. Adaptive processing based on cognitive load
        6. State transition based on outcome
        7. Post-processing hooks

        Args:
            input_data: The input to process

        Returns:
            ProcessingResult with outcome and cognitive context
        """
        start_time = datetime.now()
        errors: list[str] = []
        patterns_detected: list[str] = []
        adaptations_applied: list[str] = []

        try:
            # 1. Pre-processing hooks
            processed_input = input_data
            for pre_proc in self._pre_processors:
                try:
                    processed_input = await pre_proc(processed_input)
                except Exception as e:
                    errors.append(f"Pre-processor error: {e}")

            # 2. Transition to PROCESSING
            self._set_state(CognitiveState.PROCESSING)
            self._context.update_activity()

            # 3. Pattern detection
            patterns_detected = await self._detect_patterns(processed_input)
            if patterns_detected:
                self._metrics.pattern_matches += len(patterns_detected)

            # 4. Temporal context analysis
            temporal_context = await self._analyze_temporal()

            # 5. Adaptive processing
            output, adaptations = await self._adaptive_process(processed_input, patterns_detected, temporal_context)
            adaptations_applied = adaptations

            # 6. Update metrics and determine final state
            self._update_metrics_post_processing(patterns_detected, adaptations)
            final_state = self._determine_final_state()
            self._set_state(final_state)

            # Build result
            processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            self._metrics.time_to_first_response = processing_time_ms / 1000

            result = ProcessingResult(
                success=len(errors) == 0,
                input_data=input_data,
                output=output,
                cognitive_context=self._context,
                processing_time_ms=processing_time_ms,
                patterns_detected=patterns_detected,
                adaptations_applied=adaptations_applied,
                errors=errors,
            )

            # 7. Post-processing hooks
            for post_proc in self._post_processors:
                try:
                    result = await post_proc(result)
                except Exception as e:
                    result.errors.append(f"Post-processor error: {e}")

            # Update stats
            self._stats["total_processed"] += 1
            self._stats["patterns_detected"] += len(patterns_detected)
            self._stats["adaptations_applied"] += len(adaptations_applied)
            self._processing_history.append(result)

            return result

        except Exception as e:
            logger.error(f"Processing error: {e}")
            self._set_state(CognitiveState.RECOVERING)
            self._stats["errors"] += 1

            return ProcessingResult(
                success=False,
                input_data=input_data,
                errors=[str(e)],
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
            )

    async def _detect_patterns(self, input_data: Any) -> list[str]:
        """Detect patterns in input data."""
        try:
            # Convert input to string for pattern matching
            if isinstance(input_data, dict):
                text = str(input_data)
            elif isinstance(input_data, str):
                text = input_data
            else:
                text = repr(input_data)

            matches = self._pattern_manager.find_matches({"text": text})
            return [pattern_id for pattern_id, _, _ in matches] if matches else []

        except Exception as e:
            logger.warning(f"Pattern detection error: {e}")
            return []

    async def _analyze_temporal(self) -> dict[str, Any]:
        """Analyze temporal context."""
        try:
            context = self._time_manager.get_context("processing")
            if context is None:
                context = self._time_manager.create_context("processing")
            now = datetime.now()

            return {
                **asdict(context),
                "hour": now.hour,
                "weekday": now.weekday(),
                "is_business_hours": 9 <= now.hour <= 17 and now.weekday() < 5,
            }

        except Exception as e:
            logger.warning(f"Temporal analysis error: {e}")
            return {}

    async def _adaptive_process(
        self,
        input_data: Any,
        patterns: list[str],
        temporal_context: dict[str, Any],
    ) -> tuple[Any, list[str]]:
        """
        Process input adaptively based on cognitive context.

        Adjusts processing based on:
        - Current cognitive load
        - Detected patterns
        - Temporal context
        - Processing mode (System 1 vs System 2)
        """
        adaptations: list[str] = []

        # Determine coffee mode based on cognitive load
        coffee_mode = self._metrics.get_coffee_mode()
        self._context.coffee_mode = coffee_mode

        # Adjust processing based on load
        if self._metrics.is_overloaded():
            adaptations.append("reduced_complexity")
            self._context.processing_mode = ProcessingMode.SYSTEM_1
            # Simplified processing for overload
            output = await self._simplified_process(input_data)

        elif self._metrics.is_optimal():
            adaptations.append("full_analysis")
            self._context.processing_mode = ProcessingMode.SYSTEM_2
            # Full processing for optimal state
            output = await self._full_process(input_data, patterns)

        else:
            # Balanced processing
            adaptations.append("balanced_processing")
            output = await self._balanced_process(input_data, patterns)

        # Pattern-based adaptations
        if "URGENT_PATTERN" in patterns:
            adaptations.append("prioritized")
            self._context.attention = AttentionLevel.FOCUSED

        if "COMPLEX_PATTERN" in patterns and coffee_mode != CoffeeMode.COLD_BREW:
            adaptations.append("complexity_warning")

        return output, adaptations

    async def _simplified_process(self, input_data: Any) -> Any:
        """Simplified processing for high-load situations."""
        # Return minimal processing result
        return {
            "mode": "simplified",
            "input_received": True,
            "deferred_analysis": True,
        }

    async def _full_process(self, input_data: Any, patterns: list[str]) -> Any:
        """Full processing for optimal cognitive state."""
        return {
            "mode": "full",
            "input_data": input_data,
            "patterns": patterns,
            "analysis_complete": True,
            "insights": self._generate_insights(patterns),
        }

    async def _balanced_process(self, input_data: Any, patterns: list[str]) -> Any:
        """Balanced processing for normal cognitive state."""
        return {
            "mode": "balanced",
            "input_received": True,
            "patterns": patterns,
            "partial_analysis": True,
        }

    def _generate_insights(self, patterns: list[str]) -> list[str]:
        """Generate insights from detected patterns."""
        insights = []
        if patterns:
            insights.append(f"Detected {len(patterns)} pattern(s)")
        if self._metrics.is_optimal():
            insights.append("Cognitive state optimal for complex analysis")
        return insights

    def _update_metrics_post_processing(self, patterns: list[str], adaptations: list[str]) -> None:
        """Update cognitive metrics after processing."""
        # Increase cognitive load slightly with processing
        self._metrics.cognitive_load = min(10.0, self._metrics.cognitive_load + 0.1 * len(patterns))

        # Update context switches if adaptations were needed
        if adaptations:
            self._metrics.context_switches += 1

        # Update attention based on patterns
        if patterns:
            self._metrics.attention_level = min(1.0, self._metrics.attention_level + 0.05)
        else:
            self._metrics.attention_level = max(0.0, self._metrics.attention_level - 0.02)

    def _determine_final_state(self) -> CognitiveState:
        """Determine final cognitive state based on metrics."""
        if self._metrics.is_overloaded():
            return CognitiveState.OVERLOADED
        elif self._metrics.is_optimal():
            return CognitiveState.FLOW
        elif self._metrics.attention_level > 0.7:
            return CognitiveState.FOCUSED
        else:
            return CognitiveState.IDLE

    async def reset(self) -> None:
        """Reset processor to initial state."""
        self._set_state(CognitiveState.IDLE)
        self._metrics = CognitiveMetrics()
        self._context = CognitiveContext()
        logger.info("Cognitive processor reset")

    def reduce_load(self, amount: float = 1.0) -> None:
        """Manually reduce cognitive load (e.g., after break)."""
        self._metrics.cognitive_load = max(0.0, self._metrics.cognitive_load - amount)
        if self._state == CognitiveState.OVERLOADED:
            self._set_state(CognitiveState.RECOVERING)

    def get_stats(self) -> dict[str, Any]:
        """Get processing statistics."""
        return {
            "total_processed": self._stats["total_processed"],
            "patterns_detected": self._stats["patterns_detected"],
            "adaptations_applied": self._stats["adaptations_applied"],
            "errors": self._stats["errors"],
            "current_state": self._state.value,
            "cognitive_load": self._metrics.cognitive_load,
            "coffee_mode": self._metrics.get_coffee_mode().value,
        }

    def get_recent_results(self, count: int = 10) -> list[dict[str, Any]]:
        """Get recent processing results."""
        return [r.to_dict() for r in self._processing_history[-count:]]


# Singleton instance
_processor: CognitiveProcessor | None = None


def get_cognitive_processor() -> CognitiveProcessor:
    """Get the singleton CognitiveProcessor instance."""
    global _processor
    if _processor is None:
        _processor = CognitiveProcessor()
    return _processor
