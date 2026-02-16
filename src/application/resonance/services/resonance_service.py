"""
Resonance Service Layer (Mothership-aligned).

Service for orchestrating ActivityResonance, context, path triage, and envelope metrics.
Follows Mothership patterns: FastAPI routers → services → repositories.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from ..activity_resonance import (
    ActivityEvent,
    ActivityResonance,
    ResonanceFeedback,
    ResonanceState,
)
from ..adsr_envelope import EnvelopeMetrics
from ..context_provider import ContextSnapshot
from ..databricks_bridge import DatabricksBridge
from ..path_visualizer import PathTriage
from ..repositories.resonance_repository import ResonanceRepository

logger = logging.getLogger(__name__)


class ResonanceService:
    """Service for Activity Resonance operations (Mothership-aligned)."""

    def __init__(
        self,
        repository: ResonanceRepository | None = None,
        application_path: str | None = None,
        light_path: str | None = None,
    ):
        """
        Initialize resonance service.

        Args:
            repository: Resonance repository for persistence
            application_path: Path to application directory
            light_path: Path to light_of_the_seven directory
        """
        self._repository = repository or ResonanceRepository()
        self._application_path = application_path
        self._light_path = light_path
        self._activities: dict[str, ActivityResonance] = {}
        self._activity_events: dict[str, list[ActivityEvent]] = {}
        self._websocket_connections: dict[str, list[Any]] = {}  # activity_id -> connections
        self.databricks_bridge = DatabricksBridge()

        # Initialize Databricks Bridge
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(self.databricks_bridge.start(), loop)
        except Exception as e:
            logger.warning(f"Failed to start Databricks Bridge: {e}")

    def _get_or_create_resonance(self, activity_id: str | None = None) -> ActivityResonance:
        """Get or create ActivityResonance instance."""
        if activity_id:
            if activity_id not in self._activities:
                self._activities[activity_id] = ActivityResonance(
                    application_path=self._application_path,
                    light_path=self._light_path,
                    feedback_callback=self._create_feedback_callback(activity_id),
                )
                self._activity_events[activity_id] = []
            return self._activities[activity_id]

        # Shared instance for non-activity-specific operations
        if not hasattr(self, "_shared_resonance"):
            self._shared_resonance = ActivityResonance(
                application_path=self._application_path,
                light_path=self._light_path,
            )
        return self._shared_resonance

    def _create_feedback_callback(self, activity_id: str):
        """Create feedback callback for an activity."""

        def callback(feedback: ResonanceFeedback) -> None:
            """Callback to handle feedback updates."""
            # Persist feedback via repository
            # Note: save_feedback is async, but callbacks are sync
            # We'll store feedback synchronously via the activity events instead
            try:
                # Store in activity events for immediate access
                if activity_id not in self._activity_events:
                    self._activity_events[activity_id] = []
                # Feedback is already stored via process_activity, so we just log
                logger.debug(f"Feedback callback received for {activity_id}")
            except Exception as e:
                logger.warning(f"Failed to handle feedback callback for {activity_id}: {e}")

        return callback

    async def process_activity(
        self,
        query: str,
        activity_type: str = "general",
        context: dict[str, Any] | None = None,
    ) -> tuple[str, ResonanceFeedback]:
        """
        Process an activity and return activity ID and feedback.

        Args:
            query: The query or goal
            activity_type: Type of activity
            context: Optional additional context

        Returns:
            Tuple of (activity_id, feedback)
        """
        activity_id = str(uuid.uuid4())
        resonance = self._get_or_create_resonance(activity_id)

        # Process activity
        feedback = resonance.process_activity(
            activity_type=activity_type,
            query=query,
            context=context,
        )

        # Store events locally (sync, fast)
        events = resonance.get_recent_events(limit=100)
        self._activity_events[activity_id] = events

        # Get envelope metrics for richer telemetry
        envelope_metrics = resonance.envelope.get_metrics()

        # Parallelize I/O: persist metadata + log to Databricks concurrently
        await asyncio.gather(
            self._repository.save_activity_metadata(activity_id, activity_type, query, context),
            self.databricks_bridge.log_event(
                "ACTIVITY_PROCESSED",
                {
                    "activity_id": activity_id,
                    "type": activity_type,
                    "query": query,
                    "feedback": feedback.__dict__ if hasattr(feedback, "__dict__") else str(feedback),
                    "envelope": envelope_metrics.__dict__ if envelope_metrics else None,
                },
                impact=0.9,
            ),
            return_exceptions=True,
        )

        return activity_id, feedback

    async def get_context(
        self,
        query: str,
        context_type: str = "general",
        max_length: int = 200,
    ) -> ContextSnapshot:
        """
        Get fast context for a query.

        Args:
            query: The query
            context_type: Type of context
            max_length: Maximum context length

        Returns:
            Context snapshot
        """
        resonance = self._get_or_create_resonance()
        return resonance.context_provider.provide_context(
            query=query,
            context_type=context_type,
            max_length=max_length,
        )

    async def get_path_triage(
        self,
        goal: str,
        context: dict[str, Any] | None = None,
        max_options: int = 4,
    ) -> PathTriage:
        """
        Get path triage for a goal.

        Args:
            goal: The goal or task
            context: Optional context
            max_options: Maximum number of options

        Returns:
            Path triage
        """
        resonance = self._get_or_create_resonance()
        return resonance.path_visualizer.triage_paths(
            goal=goal,
            context=context,
            max_options=max_options,
        )

    async def get_envelope_metrics(self, activity_id: str) -> EnvelopeMetrics | None:
        """
        Get current envelope metrics for an activity.

        Args:
            activity_id: Activity ID

        Returns:
            Envelope metrics or None if activity not found
        """
        if activity_id not in self._activities:
            return None

        resonance = self._activities[activity_id]
        return resonance.envelope.get_metrics()

    async def complete_activity(self, activity_id: str) -> bool:
        """
        Complete an activity (trigger release phase).

        Args:
            activity_id: Activity ID

        Returns:
            True if activity was found and completed
        """
        if activity_id not in self._activities:
            return False

        resonance = self._activities[activity_id]
        resonance.complete_activity()
        await self._repository.mark_activity_completed(activity_id)
        return True

    async def get_activity_events(self, activity_id: str, limit: int = 100) -> list[ActivityEvent]:
        """
        Get activity events history.

        Args:
            activity_id: Activity ID
            limit: Maximum number of events to return

        Returns:
            List of activity events
        """
        if activity_id not in self._activity_events:
            return []

        return self._activity_events[activity_id][-limit:]

    async def get_activity_state(self, activity_id: str) -> ResonanceState | None:
        """
        Get current state of an activity.

        Args:
            activity_id: Activity ID

        Returns:
            Resonance state or None if activity not found
        """
        if activity_id not in self._activities:
            return None

        resonance = self._activities[activity_id]
        return resonance.get_state()

    async def cleanup_activity(self, activity_id: str) -> None:
        """
        Clean up an activity and its resources.

        Args:
            activity_id: Activity ID
        """
        # Stop feedback loop if running
        if activity_id in self._activities:
            resonance = self._activities[activity_id]
            resonance.stop_feedback_loop()

        # Remove from tracking and repository
        self._activities.pop(activity_id, None)
        self._activity_events.pop(activity_id, None)
        self._websocket_connections.pop(activity_id, None)
        await self._repository.delete_activity(activity_id)

    async def list_activities(self, user_id: str | None = None) -> list[dict[str, Any]]:
        """
        List activities, optionally filtered by user.

        Args:
            user_id: Optional user ID filter

        Returns:
            List of activity summaries
        """
        return await self._repository.list_activities(user_id=user_id)

    def register_websocket_connection(self, activity_id: str, connection: Any) -> None:
        """
        Register a WebSocket connection for an activity.

        Args:
            activity_id: Activity ID
            connection: WebSocket connection object
        """
        if activity_id not in self._websocket_connections:
            self._websocket_connections[activity_id] = []
        self._websocket_connections[activity_id].append(connection)

    def unregister_websocket_connection(self, activity_id: str, connection: Any) -> None:
        """
        Unregister a WebSocket connection.

        Args:
            activity_id: Activity ID
            connection: WebSocket connection object
        """
        if activity_id in self._websocket_connections:
            try:
                self._websocket_connections[activity_id].remove(connection)
            except ValueError:
                pass

    def unregister_websocket(self, activity_id: str, connection: Any) -> None:
        """
        Unregister a WebSocket connection (alias for unregister_websocket_connection).

        Args:
            activity_id: Activity ID
            connection: WebSocket connection object
        """
        self.unregister_websocket_connection(activity_id, connection)

    def get_websocket_connections(self, activity_id: str) -> list[Any]:
        """
        Get all WebSocket connections for an activity.

        Args:
            activity_id: Activity ID

        Returns:
            List of WebSocket connections
        """
        return self._websocket_connections.get(activity_id, [])
