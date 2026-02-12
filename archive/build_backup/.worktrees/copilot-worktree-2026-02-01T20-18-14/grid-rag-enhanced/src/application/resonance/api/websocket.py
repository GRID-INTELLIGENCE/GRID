"""
Activity Resonance WebSocket Handler.

Real-time feedback streaming for activity processing with ADSR envelope updates.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect, status

from .schemas import WebSocketFeedbackMessage
from .service import ResonanceService

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time feedback."""

    def __init__(self, service: ResonanceService):
        """
        Initialize WebSocket manager.

        Args:
            service: ResonanceService instance
        """
        self.service = service
        self._active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, activity_id: str) -> None:
        """
        Accept and register a WebSocket connection.

        Args:
            websocket: WebSocket connection
            activity_id: Activity ID to monitor
        """
        await websocket.accept()
        self.service.register_websocket_connection(activity_id, websocket)

        if activity_id not in self._active_connections:
            self._active_connections[activity_id] = []
        self._active_connections[activity_id].append(websocket)

        logger.info(f"WebSocket connected for activity {activity_id}")

    async def disconnect(self, websocket: WebSocket, activity_id: str) -> None:
        """
        Unregister and close a WebSocket connection.

        Args:
            websocket: WebSocket connection
            activity_id: Activity ID
        """
        self.service.unregister_websocket_connection(activity_id, websocket)

        if activity_id in self._active_connections:
            try:
                self._active_connections[activity_id].remove(websocket)
            except ValueError:
                pass

        logger.info(f"WebSocket disconnected for activity {activity_id}")

    async def send_feedback(
        self,
        activity_id: str,
        feedback: Any,
    ) -> None:
        """
        Send feedback message to all connections for an activity.

        Args:
            activity_id: Activity ID
            feedback: Feedback data to send
        """
        if activity_id not in self._active_connections:
            return

        # Convert feedback to WebSocket message
        message = WebSocketFeedbackMessage(
            activity_id=activity_id,
            state=feedback.state.value if hasattr(feedback.state, "value") else str(feedback.state),
            urgency=feedback.urgency,
            message=feedback.message,
            envelope=None,  # Will be populated from feedback.envelope if available
        )

        # Add envelope metrics if available
        if feedback.envelope:
            from .schemas import EnvelopeMetricsResponse

            message.envelope = EnvelopeMetricsResponse(
                phase=(
                    feedback.envelope.phase.value
                    if hasattr(feedback.envelope.phase, "value")
                    else str(feedback.envelope.phase)
                ),
                amplitude=feedback.envelope.amplitude,
                velocity=feedback.envelope.velocity,
                time_in_phase=feedback.envelope.time_in_phase,
                total_time=feedback.envelope.total_time,
                peak_amplitude=feedback.envelope.peak_amplitude,
            )

        message_json = json.dumps(message.model_dump(), default=str)

        # Send to all connections
        disconnected = []
        for websocket in self._active_connections[activity_id]:
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.warning(f"Error sending WebSocket message: {e}")
                disconnected.append(websocket)

        # Remove disconnected connections
        for websocket in disconnected:
            await self.disconnect(websocket, activity_id)

    async def broadcast_envelope_update(
        self,
        activity_id: str,
        envelope_metrics: Any,
    ) -> None:
        """
        Broadcast envelope metrics update.

        Args:
            activity_id: Activity ID
            envelope_metrics: Envelope metrics
        """
        if activity_id not in self._active_connections:
            return

        from .schemas import EnvelopeMetricsResponse, WebSocketFeedbackMessage

        phase_str = envelope_metrics.phase.value if hasattr(envelope_metrics.phase, "value") else envelope_metrics.phase
        message = WebSocketFeedbackMessage(
            activity_id=activity_id,
            state="active",
            urgency=envelope_metrics.amplitude,
            message=f"Envelope: {phase_str} ({envelope_metrics.amplitude:.2f})",
            envelope=EnvelopeMetricsResponse(
                phase=(
                    envelope_metrics.phase.value
                    if hasattr(envelope_metrics.phase, "value")
                    else str(envelope_metrics.phase)
                ),
                amplitude=envelope_metrics.amplitude,
                velocity=envelope_metrics.velocity,
                time_in_phase=envelope_metrics.time_in_phase,
                total_time=envelope_metrics.total_time,
                peak_amplitude=envelope_metrics.peak_amplitude,
            ),
        )

        message_json = json.dumps(message.model_dump(), default=str)

        disconnected = []
        for websocket in self._active_connections[activity_id]:
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.warning(f"Error broadcasting envelope update: {e}")
                disconnected.append(websocket)

        for websocket in disconnected:
            await self.disconnect(websocket, activity_id)


async def websocket_endpoint(
    websocket: WebSocket,
    activity_id: str,
    service: ResonanceService,
) -> None:
    """
    WebSocket endpoint for real-time activity feedback.

    Args:
        websocket: WebSocket connection
        activity_id: Activity ID to monitor
        service: ResonanceService instance
    """
    manager = WebSocketManager(service)

    # Verify activity exists - handle both sync and async service versions
    if inspect.iscoroutinefunction(service.get_activity_state):
        state = await service.get_activity_state(activity_id)
    else:
        state = service.get_activity_state(activity_id)

    if state is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Activity not found")
        return

    try:
        await manager.connect(websocket, activity_id)

        # Start feedback loop if not already running
        # Handle both sync and async service versions
        if hasattr(service, "_activities"):
            resonance = service._activities.get(activity_id)
            if resonance and hasattr(resonance, "_feedback_running") and not resonance._feedback_running:
                if hasattr(resonance, "start_feedback_loop"):
                    resonance.start_feedback_loop(interval=0.1)

        # Keep connection alive and stream updates
        while True:
            # Check for incoming messages (ping/pong)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                # Handle ping/pong or other messages if needed
                if data == "ping":
                    await websocket.send_text("pong")
            except TimeoutError:
                # No message received, continue
                pass
            except WebSocketDisconnect:
                break

            # Get current envelope metrics and broadcast - handle both sync and async
            if inspect.iscoroutinefunction(service.get_envelope_metrics):
                envelope_metrics = await service.get_envelope_metrics(activity_id)
            else:
                envelope_metrics = service.get_envelope_metrics(activity_id)
            if envelope_metrics:
                await manager.broadcast_envelope_update(activity_id, envelope_metrics)

            # Small delay to prevent tight loop
            await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for activity {activity_id}")
    except Exception as e:
        logger.error(f"WebSocket error for activity {activity_id}: {e}")
    finally:
        await manager.disconnect(websocket, activity_id)


__all__ = [
    "WebSocketManager",
    "websocket_endpoint",
]
