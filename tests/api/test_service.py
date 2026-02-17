"""
Unit tests for Activity Resonance API service layer.

Tests service methods, activity tracking, and WebSocket connection management.
"""

from application.resonance.activity_resonance import ResonanceState
from application.resonance.api.service import ResonanceService


class TestResonanceService:
    """Test ResonanceService class."""

    def test_service_initialization(self):
        """Test service initialization."""
        service = ResonanceService()
        assert service._resonance is None
        assert service._activities == {}
        assert service._activity_events == {}

    def test_process_activity(self):
        """Test processing an activity."""
        service = ResonanceService()
        activity_id, feedback = service.process_activity(
            query="create a new service",
            activity_type="code",
            context={"urgency": True},
        )

        assert activity_id is not None
        assert feedback is not None
        assert feedback.state in ResonanceState
        assert activity_id in service._activities
        assert activity_id in service._activity_events

    def test_get_context(self):
        """Test getting context."""
        service = ResonanceService()
        snapshot = service.get_context(
            query="test query",
            context_type="code",
            max_length=200,
        )

        assert snapshot is not None
        assert snapshot.content is not None
        assert snapshot.source is not None
        assert snapshot.metrics is not None

    def test_get_path_triage(self):
        """Test getting path triage."""
        service = ResonanceService()
        triage = service.get_path_triage(
            goal="implement feature",
            context=None,
            max_options=4,
        )

        assert triage is not None
        assert triage.goal == "implement feature"
        assert len(triage.options) > 0
        assert triage.total_options > 0

    def test_get_envelope_metrics(self):
        """Test getting envelope metrics."""
        service = ResonanceService()
        activity_id, _ = service.process_activity(
            query="test",
            activity_type="general",
        )

        metrics = service.get_envelope_metrics(activity_id)
        assert metrics is not None
        assert metrics.amplitude >= 0.0
        assert metrics.amplitude <= 1.0

    def test_get_envelope_metrics_not_found(self):
        """Test getting envelope metrics for non-existent activity."""
        service = ResonanceService()
        metrics = service.get_envelope_metrics("non-existent-id")
        assert metrics is None

    def test_complete_activity(self):
        """Test completing an activity."""
        service = ResonanceService()
        activity_id, _ = service.process_activity(
            query="test",
            activity_type="general",
        )

        completed = service.complete_activity(activity_id)
        assert completed is True

    def test_complete_activity_not_found(self):
        """Test completing non-existent activity."""
        service = ResonanceService()
        completed = service.complete_activity("non-existent-id")
        assert completed is False

    def test_get_activity_events(self):
        """Test getting activity events."""
        service = ResonanceService()
        activity_id, _ = service.process_activity(
            query="test",
            activity_type="general",
        )

        events = service.get_activity_events(activity_id, limit=10)
        assert isinstance(events, list)
        assert len(events) > 0

    def test_get_activity_events_not_found(self):
        """Test getting events for non-existent activity."""
        service = ResonanceService()
        events = service.get_activity_events("non-existent-id")
        assert events == []

    def test_get_activity_state(self):
        """Test getting activity state."""
        service = ResonanceService()
        activity_id, _ = service.process_activity(
            query="test",
            activity_type="general",
        )

        state = service.get_activity_state(activity_id)
        assert state is not None
        assert state in ResonanceState

    def test_get_activity_state_not_found(self):
        """Test getting state for non-existent activity."""
        service = ResonanceService()
        state = service.get_activity_state("non-existent-id")
        assert state is None

    def test_websocket_connection_management(self):
        """Test WebSocket connection management."""
        service = ResonanceService()
        activity_id, _ = service.process_activity(
            query="test",
            activity_type="general",
        )

        # Mock WebSocket connection
        mock_connection = object()

        service.register_websocket_connection(activity_id, mock_connection)
        connections = service.get_websocket_connections(activity_id)
        assert len(connections) == 1
        assert mock_connection in connections

        service.unregister_websocket_connection(activity_id, mock_connection)
        connections = service.get_websocket_connections(activity_id)
        assert len(connections) == 0

    def test_cleanup_activity(self):
        """Test cleaning up an activity."""
        service = ResonanceService()
        activity_id, _ = service.process_activity(
            query="test",
            activity_type="general",
        )

        # Register WebSocket connection
        mock_connection = object()
        service.register_websocket_connection(activity_id, mock_connection)

        # Cleanup
        service.cleanup_activity(activity_id)

        # Verify cleanup
        assert activity_id not in service._activities
        assert activity_id not in service._activity_events
        assert activity_id not in service._websocket_connections
