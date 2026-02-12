"""
Activity Resonance Tool - Main Orchestrator.

Coordinates left-to-right communication:
- Left: Fast context from application/
- Right: Path visualization from light_of_the_seven/

Uses ADSR envelope for haptic-like feedback and mitigates asyncio
constraints with synchronous-like feedback.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .adsr_envelope import ADSREnvelope, EnvelopeMetrics, EnvelopePhase
from .context_provider import ContextProvider, ContextSnapshot
from .path_visualizer import PathTriage, PathVisualizer

logger = logging.getLogger(__name__)


class ResonanceState(str, Enum):
    """State of the activity resonance system."""

    IDLE = "idle"
    CONTEXT_LOADING = "context_loading"
    PATH_TRIAGING = "path_triaging"
    ACTIVE = "active"
    FEEDBACK = "feedback"
    COMPLETE = "complete"


@dataclass
class ActivityEvent:
    """An activity event in the system."""

    event_id: str
    timestamp: float
    activity_type: str
    payload: dict[str, Any]
    context_snapshot: ContextSnapshot | None = None
    path_triage: PathTriage | None = None
    envelope_metrics: EnvelopeMetrics | None = None


@dataclass
class ResonanceFeedback:
    """Feedback from the resonance system."""

    state: ResonanceState
    context: ContextSnapshot | None = None
    paths: PathTriage | None = None
    envelope: EnvelopeMetrics | None = None
    message: str = ""
    urgency: float = 0.0  # 0.0 to 1.0


class ActivityResonance:
    """
    Activity Resonance Tool - Left-to-Right Communication.

    Coordinates:
    - Fast context from application/ (left)
    - Path visualization from light_of_the_seven/ (right)
    - ADSR envelope feedback (haptic-like)
    - Synchronous-like feedback (mitigates asyncio constraints)
    """

    def __init__(
        self,
        application_path: str | None = None,
        light_path: str | None = None,
        feedback_callback: Callable[[ResonanceFeedback], None] | None = None,
    ):
        """
        Initialize activity resonance system.

        Args:
            application_path: Path to application directory
            light_path: Path to light_of_the_seven directory
            feedback_callback: Optional callback for real-time feedback
        """
        from pathlib import Path as PathlibPath

        app_path = PathlibPath(application_path) if isinstance(application_path, str) else application_path
        light_p = PathlibPath(light_path) if isinstance(light_path, str) else light_path
        self.context_provider = ContextProvider(app_path)
        self.path_visualizer = PathVisualizer(light_p)
        self.envelope = ADSREnvelope()
        self.feedback_callback = feedback_callback

        self._state = ResonanceState.IDLE
        self._events: list[ActivityEvent] = []
        self._feedback_thread: threading.Thread | None = None
        self._feedback_running = False
        self._lock = threading.Lock()

    def process_activity(
        self, activity_type: str, query: str, context: dict[str, Any] | None = None
    ) -> ResonanceFeedback:
        """
        Process an activity with left-to-right communication.

        Args:
            activity_type: Type of activity ("code", "config", "general")
            query: The query or goal
            context: Optional additional context

        Returns:
            Resonance feedback with context and paths
        """
        import uuid

        event_id = str(uuid.uuid4())
        timestamp = time.time()

        # Trigger envelope (attack phase)
        self.envelope.trigger()

        # Update state
        with self._lock:
            self._state = ResonanceState.CONTEXT_LOADING

        # Left side: Fast context
        context_snapshot = self.context_provider.provide_context(query, context_type=activity_type)

        # Update state
        with self._lock:
            self._state = ResonanceState.PATH_TRIAGING

        # Right side: Path triage
        path_triage = self.path_visualizer.triage_paths(goal=query, context=context, max_options=4)

        # Update state
        with self._lock:
            self._state = ResonanceState.ACTIVE

        # Update envelope
        envelope_metrics = self.envelope.update()

        # Create event
        event = ActivityEvent(
            event_id=event_id,
            timestamp=timestamp,
            activity_type=activity_type,
            payload={"query": query, "context": context or {}},
            context_snapshot=context_snapshot,
            path_triage=path_triage,
            envelope_metrics=envelope_metrics,
        )

        with self._lock:
            self._events.append(event)

        # Generate feedback
        feedback = self._generate_feedback(context_snapshot, path_triage, envelope_metrics)

        # Send feedback if callback provided
        if self.feedback_callback:
            self.feedback_callback(feedback)

        return feedback

    def _generate_feedback(
        self, context: ContextSnapshot, paths: PathTriage, envelope: EnvelopeMetrics
    ) -> ResonanceFeedback:
        """Generate resonance feedback."""
        # Calculate urgency from metrics
        urgency = (
            context.metrics.attention_tension * 0.4
            + context.metrics.decision_pressure * 0.3
            + (1.0 - context.metrics.clarity) * 0.3
        )

        # Generate message
        message_parts = []

        # Context message
        if context.metrics.sparsity > 0.7:
            message_parts.append("⚠️ Sparse context - providing vivid explanation")
        if context.metrics.attention_tension > 0.7:
            message_parts.append("⚡ High attention tension detected")

        # Path message
        if paths.recommended:
            message_parts.append(
                f"🎯 Recommended: {paths.recommended.name} "
                f"({paths.recommended.complexity.value}, {paths.recommended.estimated_time:.1f}s)"
            )

        # Envelope message
        if envelope.phase == EnvelopePhase.ATTACK:
            message_parts.append("📈 Attack phase - initial response")
        elif envelope.phase == EnvelopePhase.SUSTAIN:
            message_parts.append("🔄 Sustain phase - maintaining feedback")

        message = " | ".join(message_parts) if message_parts else "Activity processing"

        return ResonanceFeedback(
            state=self._state,
            context=context,
            paths=paths,
            envelope=envelope,
            message=message,
            urgency=urgency,
        )

    def start_feedback_loop(self, interval: float = 0.1) -> None:
        """
        Start continuous feedback loop for synchronous-like updates.

        Args:
            interval: Update interval in seconds
        """
        if self._feedback_running:
            return

        self._feedback_running = True

        def feedback_loop():
            while self._feedback_running:
                # Update envelope
                envelope_metrics = self.envelope.update()

                # Send feedback if active
                if self.envelope.is_active() and self.feedback_callback:
                    with self._lock:
                        state = self._state

                    # Get latest context and paths if available
                    latest_event = self._events[-1] if self._events else None
                    if latest_event:
                        feedback = ResonanceFeedback(
                            state=state,
                            context=latest_event.context_snapshot,
                            paths=latest_event.path_triage,
                            envelope=envelope_metrics,
                            message=f"Envelope: {envelope_metrics.phase.value} ({envelope_metrics.amplitude:.2f})",
                            urgency=envelope_metrics.amplitude,
                        )
                        self.feedback_callback(feedback)

                time.sleep(interval)

        self._feedback_thread = threading.Thread(target=feedback_loop, daemon=True)
        self._feedback_thread.start()

    def stop_feedback_loop(self) -> None:
        """Stop feedback loop."""
        self._feedback_running = False
        if self._feedback_thread:
            self._feedback_thread.join(timeout=1.0)

    def complete_activity(self) -> None:
        """Complete current activity (trigger release phase)."""
        self.envelope.release()
        with self._lock:
            self._state = ResonanceState.COMPLETE

    def get_state(self) -> ResonanceState:
        """Get current resonance state."""
        with self._lock:
            return self._state

    def get_recent_events(self, limit: int = 10) -> list[ActivityEvent]:
        """Get recent activity events."""
        with self._lock:
            return self._events[-limit:]

    def clear_history(self) -> None:
        """Clear event history."""
        with self._lock:
            self._events.clear()
