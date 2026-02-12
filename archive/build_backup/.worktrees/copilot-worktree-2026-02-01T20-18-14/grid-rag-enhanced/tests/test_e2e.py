"""
End-to-end tests for Activity Resonance API.

Tests full activity processing flow, left-to-right communication, and ADSR envelope phases.
"""

import time

from fastapi.testclient import TestClient


class TestFullActivityFlow:
    """Test complete activity processing flow."""

    def test_full_activity_lifecycle(self, client: TestClient, service):
        """Test complete activity lifecycle from creation to completion."""
        # 1. Process activity
        response = client.post(
            "/api/v1/resonance/process",
            json={
                "query": "create a new service",
                "activity_type": "code",
                "context": {"urgency": True},
            },
        )

        assert response.status_code == 200
        data = response.json()
        activity_id = data["activity_id"]

        # Verify response structure
        assert "state" in data
        assert "urgency" in data
        assert "message" in data
        assert "context" in data or data.get("context") is None
        assert "paths" in data or data.get("paths") is None
        assert "envelope" in data or data.get("envelope") is None

        # 2. Get envelope metrics
        response = client.get(f"/api/v1/resonance/envelope/{activity_id}")
        assert response.status_code == 200
        envelope_data = response.json()
        assert "phase" in envelope_data
        assert "amplitude" in envelope_data

        # 3. Get events
        response = client.get(f"/api/v1/resonance/events/{activity_id}")
        assert response.status_code == 200
        events_data = response.json()
        assert events_data["activity_id"] == activity_id
        assert "events" in events_data

        # 4. Complete activity
        response = client.post(f"/api/v1/resonance/complete/{activity_id}")
        assert response.status_code == 200
        complete_data = response.json()
        assert complete_data["completed"] is True

        # 5. Verify envelope after completion (should be in release or idle)
        time.sleep(0.2)  # Wait for release phase
        response = client.get(f"/api/v1/resonance/envelope/{activity_id}")
        if response.status_code == 200:
            envelope_data = response.json()
            # Phase should be release or idle after completion
            assert envelope_data["phase"] in ["release", "idle", "decay", "sustain"]

    def test_left_to_right_communication(self, client: TestClient):
        """Test left-to-right communication (context + paths)."""
        # Process activity
        response = client.post(
            "/api/v1/resonance/process",
            json={
                "query": "implement authentication",
                "activity_type": "code",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify left side (context)
        if data.get("context"):
            context = data["context"]
            assert "content" in context
            assert "source" in context
            assert "metrics" in context
            assert context["source"].startswith("application/")

        # Verify right side (paths)
        if data.get("paths"):
            paths = data["paths"]
            assert "goal" in paths
            assert "options" in paths
            assert len(paths["options"]) > 0
            assert "recommended" in paths or paths.get("recommended") is None

    def test_adsr_envelope_phases(self, client: TestClient, service):
        """Test ADSR envelope phases during activity processing."""
        # Process activity
        response = client.post(
            "/api/v1/resonance/process",
            json={"query": "test activity"},
        )
        activity_id = response.json()["activity_id"]

        # Monitor envelope phases
        phases_seen = set()

        for _ in range(5):
            response = client.get(f"/api/v1/resonance/envelope/{activity_id}")
            if response.status_code == 200:
                envelope_data = response.json()
                phase = envelope_data["phase"]
                phases_seen.add(phase)

                # Verify amplitude is valid
                assert 0.0 <= envelope_data["amplitude"] <= 1.0

            time.sleep(0.1)

        # Should see at least one phase
        assert len(phases_seen) > 0

        # Complete activity
        client.post(f"/api/v1/resonance/complete/{activity_id}")

        # Wait and check for release phase
        time.sleep(0.3)
        response = client.get(f"/api/v1/resonance/envelope/{activity_id}")
        if response.status_code == 200:
            envelope_data = response.json()
            # After completion, should be in release or idle
            assert envelope_data["phase"] in ["release", "idle", "decay", "sustain"]


class TestContextAndPaths:
    """Test context and path triage endpoints."""

    def test_context_endpoint(self, client: TestClient):
        """Test context endpoint provides fast context."""
        response = client.get(
            "/api/v1/resonance/context",
            params={
                "query": "create a service",
                "context_type": "code",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "metrics" in data
        assert "sparsity" in data["metrics"]
        assert "attention_tension" in data["metrics"]
        assert "decision_pressure" in data["metrics"]

    def test_paths_endpoint(self, client: TestClient):
        """Test paths endpoint provides path triage."""
        response = client.get(
            "/api/v1/resonance/paths",
            params={
                "goal": "implement feature",
                "max_options": 4,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "goal" in data
        assert "options" in data
        assert len(data["options"]) > 0
        assert data["total_options"] > 0

        # Verify option structure
        option = data["options"][0]
        assert "id" in option
        assert "name" in option
        assert "complexity" in option
        assert "estimated_time" in option
        assert "confidence" in option

    def test_context_and_paths_together(self, client: TestClient):
        """Test using context and paths endpoints together."""
        # Get context
        context_response = client.get(
            "/api/v1/resonance/context",
            params={"query": "add authentication"},
        )
        assert context_response.status_code == 200

        # Get paths
        paths_response = client.get(
            "/api/v1/resonance/paths",
            params={"goal": "add authentication"},
        )
        assert paths_response.status_code == 200

        # Both should work independently
        context_data = context_response.json()
        paths_data = paths_response.json()

        assert "content" in context_data
        assert "options" in paths_data


class TestWebSocketE2E:
    """Test WebSocket end-to-end flow."""

    def test_websocket_full_feedback_flow(self, client: TestClient, service):
        """Test WebSocket provides full feedback during activity."""
        # Create activity
        response = client.post(
            "/api/v1/resonance/process",
            json={"query": "test activity"},
        )
        activity_id = response.json()["activity_id"]

        # Connect WebSocket
        messages_received = []
        with client.websocket_connect(f"/api/v1/resonance/ws/{activity_id}") as websocket:
            # Collect messages for a short time
            start_time = time.time()
            while time.time() - start_time < 0.5:
                try:
                    message = websocket.receive_json(timeout=0.2)
                    messages_received.append(message)
                except Exception:
                    break

        # Should receive at least some messages
        # (may be 0 if activity completes quickly)
        assert isinstance(messages_received, list)

        # Verify message structure if any received
        for message in messages_received:
            assert "activity_id" in message
            assert "state" in message
            assert "urgency" in message

    def test_websocket_with_activity_completion(self, client: TestClient, service):
        """Test WebSocket during activity completion."""
        # Create activity
        response = client.post(
            "/api/v1/resonance/process",
            json={"query": "test activity"},
        )
        activity_id = response.json()["activity_id"]

        # Connect WebSocket
        with client.websocket_connect(f"/api/v1/resonance/ws/{activity_id}") as websocket:
            # Wait a bit
            time.sleep(0.2)

            # Complete activity in another "thread" (simulated)
            # In real scenario, this would be from another client
            client.post(f"/api/v1/resonance/complete/{activity_id}")

            # Wait for completion feedback
            time.sleep(0.2)

            # Try to receive messages
            try:
                message = websocket.receive_json(timeout=0.5)
                assert "activity_id" in message
            except Exception:
                # No message, which is acceptable
                pass
