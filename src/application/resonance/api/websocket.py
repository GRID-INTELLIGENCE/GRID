"""
Activity Resonance WebSocket Handler.

Real-time feedback streaming for activity processing with ADSR envelope updates.
Implements ACK/NACK protocol for reliable message delivery.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect, status

from .service import ResonanceService

logger = logging.getLogger(__name__)


# =============================================================================
# ACK/NACK Protocol Components
# =============================================================================


@dataclass
class MessageEnvelope:
    """Contract for all WebSocket messages.

    Every message sent through the WebSocket is wrapped in an envelope
    that includes metadata for tracking and acknowledgment.

    Attributes:
        id: Unique message identifier for ACK correlation.
        type: Message type (e.g., "feedback", "envelope", "ping").
        payload: The actual message payload.
        timestamp: When the message was created.
        requires_ack: Whether this message requires acknowledgment.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "message"
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    requires_ack: bool = True

    def to_json(self) -> str:
        """Serialize envelope to JSON string."""
        return json.dumps(self.to_dict(), default=str)

    def to_dict(self) -> dict[str, Any]:
        """Serialize envelope to dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "requires_ack": self.requires_ack,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MessageEnvelope:
        """Create envelope from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            type=data.get("type", "message"),
            payload=data.get("payload", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(UTC),
            requires_ack=data.get("requires_ack", True),
        )


@dataclass
class PendingMessage:
    """Tracks a message awaiting acknowledgment.

    Attributes:
        envelope: The message envelope.
        sent_at: When the message was sent.
        retries: Number of retry attempts.
        connection_id: Associated connection identifier.
    """

    envelope: MessageEnvelope
    sent_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    retries: int = 0
    connection_id: str = ""


class AckTracker:
    """Tracks pending ACKs with timeout enforcement.

    Implements the ACK/NACK protocol for reliable WebSocket message delivery.
    Messages without acknowledgment within the timeout period trigger
    parasite detection and connection cleanup.

    ACK Contract:
    - Client sends: {"type": "ack", "ack_id": "<message_id>", "status": "ok|error"}
    - Server tracks pending messages and enforces timeout
    - Timeout triggers parasite detection

    Attributes:
        timeout_seconds: Maximum time to wait for ACK (default: 3.0s).
        max_retries: Maximum retry attempts before giving up (default: 3).
    """

    def __init__(self, timeout_seconds: float = 3.0, max_retries: int = 3):
        """Initialize ACK tracker.

        Args:
            timeout_seconds: Maximum time to wait for ACK.
            max_retries: Maximum retry attempts.
        """
        self._pending: dict[str, PendingMessage] = {}
        self._timeout = timeout_seconds
        self._max_retries = max_retries
        self._stats = {
            "messages_sent": 0,
            "acks_received": 0,
            "timeouts": 0,
            "retries": 0,
        }

    @property
    def pending_count(self) -> int:
        """Get number of pending ACKs."""
        return len(self._pending)

    @property
    def stats(self) -> dict[str, int]:
        """Get ACK statistics."""
        return dict(self._stats)

    async def send_with_ack(
        self,
        ws: WebSocket,
        envelope: MessageEnvelope,
        connection_id: str = "",
    ) -> bool:
        """Send message and wait for ACK.

        Args:
            ws: WebSocket connection.
            envelope: Message envelope to send.
            connection_id: Identifier for this connection.

        Returns:
            True if ACK received successfully, False on timeout/error.
        """
        self._stats["messages_sent"] += 1

        # Send the message
        try:
            await ws.send_text(envelope.to_json())
        except Exception as e:
            logger.warning(f"Failed to send message {envelope.id}: {e}")
            return False

        # Track pending message
        self._pending[envelope.id] = PendingMessage(
            envelope=envelope,
            connection_id=connection_id,
        )

        # Wait for ACK if required
        if not envelope.requires_ack:
            del self._pending[envelope.id]
            return True

        # Retry loop
        for attempt in range(self._max_retries):
            try:
                ack_data = await asyncio.wait_for(
                    ws.receive_text(),
                    timeout=self._timeout,
                )
                ack = json.loads(ack_data)

                # Check if this is an ACK for our message
                if ack.get("type") == "ack" and ack.get("ack_id") == envelope.id:
                    self._stats["acks_received"] += 1

                    if ack.get("status") == "ok":
                        del self._pending[envelope.id]
                        return True
                    else:
                        # NACK received - client reported error
                        logger.warning(
                            f"NACK received for message {envelope.id}: " f"{ack.get('error_code', 'unknown')}"
                        )
                        del self._pending[envelope.id]
                        return False

                # Received something else (not an ACK), could be a regular message
                # In a real implementation, you'd queue this for processing
                # For now, continue waiting for ACK

            except TimeoutError:
                self._stats["timeouts"] += 1
                self._pending[envelope.id].retries += 1
                self._stats["retries"] += 1

                if attempt < self._max_retries - 1:
                    logger.debug(f"ACK timeout for {envelope.id}, retry {attempt + 1}/{self._max_retries}")
                    # Retry send
                    try:
                        await ws.send_text(envelope.to_json())
                    except Exception:
                        break
                else:
                    logger.warning(f"ACK timeout for message {envelope.id} after " f"{self._max_retries} retries")

            except json.JSONDecodeError:
                # Not valid JSON, continue waiting
                continue
            except Exception as e:
                logger.warning(f"Error waiting for ACK: {e}")
                break

        # All retries exhausted or error occurred
        if envelope.id in self._pending:
            del self._pending[envelope.id]
        return False

    def get_pending_messages(self) -> list[PendingMessage]:
        """Get all pending messages awaiting ACK."""
        return list(self._pending.values())

    def clear_pending(self, message_id: str | None = None) -> None:
        """Clear pending message(s).

        Args:
            message_id: Specific message ID to clear, or None to clear all.
        """
        if message_id:
            self._pending.pop(message_id, None)
        else:
            self._pending.clear()

    def acknowledge(self, message_id: str) -> bool:
        """Manually acknowledge a message.

        Args:
            message_id: Message ID to acknowledge.

        Returns:
            True if message was pending, False otherwise.
        """
        if message_id in self._pending:
            del self._pending[message_id]
            self._stats["acks_received"] += 1
            return True
        return False


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
        self.ack_tracker = AckTracker()

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

        FIXED: Implements ACK/NACK pattern to ensure message delivery.
        Messages without ACK are retried, failed connections are cleaned up.
        """
        if activity_id not in self._active_connections:
            return

        # Convert feedback to WebSocket message
        # Convert feedback to WebSocket message payload
        feedback_data = {
            "activity_id": activity_id,
            "state": feedback.state.value if hasattr(feedback.state, "value") else str(feedback.state),
            "urgency": feedback.urgency,
            "message": feedback.message,
        }

        # Add envelope metrics if available
        if feedback.envelope:
            feedback_data["envelope"] = {
                "phase": (
                    feedback.envelope.phase.value
                    if hasattr(feedback.envelope.phase, "value")
                    else str(feedback.envelope.phase)
                ),
                "amplitude": feedback.envelope.amplitude,
                "velocity": feedback.envelope.velocity,
                "time_in_phase": feedback.envelope.time_in_phase,
                "total_time": feedback.envelope.total_time,
                "peak_amplitude": feedback.envelope.peak_amplitude,
            }

        # Wrap in envelope
        envelope = MessageEnvelope(
            id=str(uuid.uuid4()),
            type="feedback",
            payload=feedback_data,
            timestamp=datetime.now(UTC),
        )

        # Send to all connections with ACK/NACK pattern
        disconnected = []
        for websocket in self._active_connections[activity_id]:
            success = await self.ack_tracker.send_with_ack(websocket, envelope)
            if not success:
                logger.warning(f"Failed to send feedback to socket for {activity_id}, disconnecting")
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

        phase_str = envelope_metrics.phase.value if hasattr(envelope_metrics.phase, "value") else envelope_metrics.phase

        payload = {
            "activity_id": activity_id,
            "state": "active",
            "urgency": envelope_metrics.amplitude,
            "message": f"Envelope: {phase_str} ({envelope_metrics.amplitude:.2f})",
            "envelope": {
                "phase": phase_str,
                "amplitude": envelope_metrics.amplitude,
                "velocity": envelope_metrics.velocity,
                "time_in_phase": envelope_metrics.time_in_phase,
                "total_time": envelope_metrics.total_time,
                "peak_amplitude": envelope_metrics.peak_amplitude,
            },
        }

        envelope = MessageEnvelope(
            id=str(uuid.uuid4()),
            type="envelope_update",
            payload=payload,
            timestamp=datetime.now(UTC),
        )

        disconnected = []
        for websocket in self._active_connections[activity_id]:
            success = await self.ack_tracker.send_with_ack(websocket, envelope)
            if not success:
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
    "MessageEnvelope",
    "PendingMessage",
    "AckTracker",
]
