"""Tests for Vection core functionality."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestStreamContext:
    """Test StreamContext class."""

    def test_initialization(self):
        """Test that StreamContext can be initialized."""
        from vection.core.stream_context import StreamContext

        ctx = StreamContext()
        assert ctx is not None

    def test_context_isolation(self):
        """Test that contexts are properly isolated."""
        from vection.core.stream_context import StreamContext

        ctx1 = StreamContext()
        ctx2 = StreamContext()

        assert ctx1 is not ctx2


@pytest.mark.unit
class TestEmergenceLayer:
    """Test EmergenceLayer class."""

    def test_layer_creation(self):
        """Test that EmergenceLayer can be created."""
        from vection.core.emergence_layer import EmergenceLayer

        layer = EmergenceLayer()
        assert layer is not None


@pytest.mark.unit
class TestVelocityTracker:
    """Test VelocityTracker class."""

    def test_initialization_requires_session_id(self):
        """Test that VelocityTracker requires a session_id."""
        from vection.core.velocity_tracker import VelocityTracker

        tracker = VelocityTracker(session_id="test-session-123")
        assert tracker is not None
        assert tracker.session_id == "test-session-123"

    def test_initialization_with_custom_history_size(self):
        """Test VelocityTracker with custom history size."""
        from vection.core.velocity_tracker import VelocityTracker

        tracker = VelocityTracker(
            session_id="test-session",
            history_size=100,
            direction_history_size=30,
        )
        assert tracker.session_id == "test-session"

    def test_current_velocity_returns_zero_initially(self):
        """Test that current_velocity returns zero vector when no events tracked."""
        from vection.core.velocity_tracker import VelocityTracker

        tracker = VelocityTracker(session_id="test-session")
        velocity = tracker.current_velocity

        # Should return a zero vector initially
        assert velocity is not None
        assert velocity.magnitude == 0.0

    @patch("vection.core.velocity_tracker.get_velocity_anomaly_detector", create=True)
    def test_track_event_updates_velocity(self, mock_detector):
        """Test that tracking events updates velocity."""
        from vection.core.velocity_tracker import VelocityTracker

        # Mock the velocity anomaly detector to avoid import issues
        mock_detector.return_value.validate_timestamp_integrity.return_value = True

        tracker = VelocityTracker(session_id="test-session")

        event_data = {
            "direction": "forward",
            "intent": "explore",
            "topic": "testing",
        }

        velocity = tracker.track_event(event_data, event_type="navigation")
        assert velocity is not None

    def test_multiple_events_build_history(self):
        """Test that multiple events build velocity history."""
        from vection.core.velocity_tracker import VelocityTracker

        tracker = VelocityTracker(session_id="test-session", history_size=10)

        # Track several events
        for i in range(5):
            tracker.track_event({"direction": "forward", "topic": f"topic_{i}"}, event_type="navigation")

        # History should have entries
        assert len(tracker.history) > 0


@pytest.mark.unit
class TestVelocityTrackerRegistry:
    """Test VelocityTrackerRegistry class."""

    def test_registry_creates_tracker_on_demand(self):
        """Test that registry creates trackers on demand."""
        from vection.core.velocity_tracker import VelocityTrackerRegistry

        registry = VelocityTrackerRegistry()
        tracker = registry.get_or_create("session-1")

        assert tracker is not None
        assert tracker.session_id == "session-1"

    def test_registry_returns_same_tracker_for_same_session(self):
        """Test that registry returns the same tracker for the same session."""
        from vection.core.velocity_tracker import VelocityTrackerRegistry

        registry = VelocityTrackerRegistry()
        tracker1 = registry.get_or_create("session-1")
        tracker2 = registry.get_or_create("session-1")

        assert tracker1 is tracker2

    def test_registry_creates_different_trackers_for_different_sessions(self):
        """Test that registry creates different trackers for different sessions."""
        from vection.core.velocity_tracker import VelocityTrackerRegistry

        registry = VelocityTrackerRegistry()
        tracker1 = registry.get_or_create("session-1")
        tracker2 = registry.get_or_create("session-2")

        assert tracker1 is not tracker2
        assert tracker1.session_id == "session-1"
        assert tracker2.session_id == "session-2"
