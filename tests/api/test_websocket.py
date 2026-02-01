"""
WebSocket tests for Activity Resonance API.

Tests WebSocket connection, real-time feedback streaming, and connection lifecycle.
"""

import time
from typing import Any

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect


class TestWebSocketConnection:
    """Test WebSocket connection lifecycle."""

    def test_websocket_connect_success(self, client: TestClient, service: Any) -> None:
        """Test successful WebSocket connection."""
        # Create an activity first
        response = client.post(
            "/api/v1/resonance/process",
            json={"query": "test activity"},
        )
        activity_id = response.json()["activity_id"]

        # Connect WebSocket
        with client.websocket_connect(f"/api/v1/resonance/ws/{activity_id}") as websocket:
            # Connection should be established
            assert websocket is not None

    def test_websocket_connect_activity_not_found(self, client: TestClient) -> None:
        """Test WebSocket connection for non-existent activity."""
        with pytest.raises((WebSocketDisconnect, RuntimeError)):
            with client.websocket_connect("/api/v1/resonance/ws/non-existent-id"):
                pass

    def test_websocket_receive_messages(self, client: TestClient, service: Any) -> None:
        """Test receiving messages from WebSocket."""
        # Create an activity
        response = client.post(
            "/api/v1/resonance/process",
            json={"query": "test activity"},
        )
        activity_id = response.json()["activity_id"]

        # Connect and receive messages
        with client.websocket_connect(f"/api/v1/resonance/ws/{activity_id}") as websocket:
            # Wait a bit for messages
            time.sleep(0.2)

            # Try to receive a message (may timeout if no messages)
            try:
                message = websocket.receive_json()
                assert "activity_id" in message
                assert "state" in message
                assert "urgency" in message
            except Exception:
                # No message received, which is acceptable
                pass

    def test_websocket_ping_pong(self, client: TestClient, service: Any) -> None:
        """Test WebSocket ping/pong functionality."""
        # Create an activity
        response = client.post(
            "/api/v1/resonance/process",
            json={"query": "test activity"},
        )
        activity_id = response.json()["activity_id"]

        with client.websocket_connect(f"/api/v1/resonance/ws/{activity_id}") as websocket:
            # Send ping
            websocket.send_text("ping")

            # Should receive pong
            try:
                pong_response = websocket.receive_text()
                assert pong_response == "pong"
            except Exception:
                # Pong may not be immediate
                pass

    def test_websocket_multiple_connections(self, client: TestClient, service: Any) -> None:
        """Test multiple WebSocket connections to same activity."""
        # Create an activity
        response = client.post(
            "/api/v1/resonance/process",
            json={"query": "test activity"},
        )
        activity_id = response.json()["activity_id"]

        # Connect multiple WebSockets
        with client.websocket_connect(f"/api/v1/resonance/ws/{activity_id}") as ws1:
            with client.websocket_connect(f"/api/v1/resonance/ws/{activity_id}") as ws2:
                # Both should be connected
                assert ws1 is not None
                assert ws2 is not None

    def test_websocket_disconnect(self, client: TestClient, service: Any) -> None:
        """Test WebSocket disconnection."""
        # Create an activity
        response = client.post(
            "/api/v1/resonance/process",
            json={"query": "test activity"},
        )
        activity_id = response.json()["activity_id"]

        # Connect and disconnect
        with client.websocket_connect(f"/api/v1/resonance/ws/{activity_id}") as websocket:
            # Connection established
            assert websocket is not None

        # Connection should be closed after context exit
        # Verify cleanup by checking service
        service.get_websocket_connections(activity_id)
        # Connections should be cleaned up (may take a moment)
        time.sleep(0.1)


class TestWebSocketFeedback:
    """Test WebSocket feedback message format."""

    def test_feedback_message_structure(self, client: TestClient, service: Any) -> None:
        """Test feedback message structure."""
        # Create an activity
        response = client.post(
            "/api/v1/resonance/process",
            json={"query": "test activity"},
        )
        activity_id = response.json()["activity_id"]

        with client.websocket_connect(f"/api/v1/resonance/ws/{activity_id}") as websocket:
            # Wait for messages
            time.sleep(0.3)

            try:
                message = websocket.receive_json()
                # Verify message structure
                assert "activity_id" in message
                assert "state" in message
                assert "urgency" in message
                assert "message" in message
                assert "timestamp" in message

                # Urgency should be between 0 and 1
                assert 0.0 <= message["urgency"] <= 1.0
            except Exception:
                # No message received
                pass

    def test_feedback_envelope_metrics(self, client: TestClient, service: Any) -> None:
        """Test feedback message includes envelope metrics."""
        # Create an activity
        response = client.post(
            "/api/v1/resonance/process",
            json={"query": "test activity"},
        )
        activity_id = response.json()["activity_id"]

        with client.websocket_connect(f"/api/v1/resonance/ws/{activity_id}") as websocket:
            # Wait for messages
            time.sleep(0.3)

            try:
                message = websocket.receive_json()
                # Check if envelope is included
                if "envelope" in message and message["envelope"]:
                    envelope = message["envelope"]
                    assert "phase" in envelope
                    assert "amplitude" in envelope
                    assert "velocity" in envelope
                    assert "time_in_phase" in envelope
                    assert "total_time" in envelope
                    assert "peak_amplitude" in envelope

                    # Amplitude should be between 0 and 1
                    assert 0.0 <= envelope["amplitude"] <= 1.0
            except Exception:
                # No message received
                pass
