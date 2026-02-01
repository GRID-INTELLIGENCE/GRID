"""Tests for AI Safety Monitor Skill."""

from grid.skills.ai_safety.monitor import (
    MonitoringSession,
    SafetyMonitor,
    get_monitor,
    monitor_handler,
)


class TestMonitoringSession:
    """Test monitoring session functionality."""

    def test_session_creation(self):
        """Test creating a monitoring session."""
        session = MonitoringSession(
            session_id="test_123",
            stream_id="stream_1",
            start_time=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
            check_interval=60,
        )
        assert session.session_id == "test_123"
        assert session.stream_id == "stream_1"
        assert session.active is True

    def test_session_to_dict(self):
        """Test session serialization."""
        from datetime import UTC, datetime

        session = MonitoringSession(
            session_id="test_123",
            stream_id="stream_1",
            start_time=datetime.now(UTC),
            check_interval=60,
        )
        data = session.to_dict()
        assert "session_id" in data
        assert "stream_id" in data
        assert "uptime_seconds" in data


class TestSafetyMonitor:
    """Test safety monitor functionality."""

    def test_create_session(self):
        """Test creating a monitoring session."""
        monitor = SafetyMonitor()
        session = monitor.create_session("test_stream", 30)
        assert session.stream_id == "test_stream"
        assert session.check_interval == 30
        assert session.active is True

    def test_get_session_stats(self):
        """Test getting session statistics."""
        monitor = SafetyMonitor()
        session = monitor.create_session("test_stream")
        stats = monitor.get_session_stats(session.session_id)
        assert stats is not None
        assert stats["stream_id"] == "test_stream"

    def test_stop_session(self):
        """Test stopping a monitoring session."""
        monitor = SafetyMonitor()
        session = monitor.create_session("test_stream")
        success = monitor.stop_session(session.session_id)
        assert success is True
        assert session.active is False

    def test_check_content_detects_violations(self):
        """Test that content checking detects violations."""
        monitor = SafetyMonitor()
        session = monitor.create_session("test_stream")
        report = monitor.check_content(
            session.session_id,
            "This contains violence and hate speech.",
        )
        assert report is not None
        assert hasattr(report, "threat_level")

    def test_check_content_updates_stats(self):
        """Test that content checking updates session stats."""
        monitor = SafetyMonitor()
        session = monitor.create_session("test_stream")
        initial_count = session.contents_checked
        monitor.check_content(session.session_id, "Test content")
        assert session.contents_checked == initial_count + 1


class TestMonitorHandler:
    """Test the monitor skill handler."""

    def test_handler_create_operation(self):
        """Test creating a monitoring session via handler."""
        args = {
            "operation": "create",
            "stream_id": "test_stream",
            "check_interval": 30,
        }
        result = monitor_handler(args)
        assert result["success"] is True
        assert "session_id" in result

    def test_handler_create_requires_stream_id(self):
        """Test that create requires stream_id."""
        args = {"operation": "create"}
        result = monitor_handler(args)
        assert result["success"] is False
        assert "error" in result

    def test_handler_check_operation(self):
        """Test checking content via handler."""
        # First create a session
        create_args = {
            "operation": "create",
            "stream_id": "test_stream",
        }
        create_result = monitor_handler(create_args)
        session_id = create_result["session_id"]

        # Then check content
        check_args = {
            "operation": "check",
            "session_id": session_id,
            "content": "Test content for safety check.",
        }
        result = monitor_handler(check_args)
        assert result["success"] is True
        assert "report" in result

    def test_handler_stats_operation(self):
        """Test getting stats via handler."""
        # Create a session first
        create_args = {
            "operation": "create",
            "stream_id": "test_stream",
        }
        monitor_handler(create_args)

        # Get all sessions
        args = {"operation": "stats"}
        result = monitor_handler(args)
        assert result["success"] is True
        assert "sessions" in result
        assert "count" in result

    def test_handler_stop_operation(self):
        """Test stopping a session via handler."""
        # Create a session first
        create_args = {
            "operation": "create",
            "stream_id": "test_stream",
        }
        create_result = monitor_handler(create_args)
        session_id = create_result["session_id"]

        # Stop the session
        args = {
            "operation": "stop",
            "session_id": session_id,
        }
        result = monitor_handler(args)
        assert result["success"] is True

    def test_handler_list_operation(self):
        """Test listing sessions via handler."""
        args = {"operation": "list"}
        result = monitor_handler(args)
        assert result["success"] is True
        assert "sessions" in result

    def test_handler_unknown_operation(self):
        """Test handling unknown operation."""
        args = {"operation": "unknown"}
        result = monitor_handler(args)
        assert result["success"] is False
        assert "error" in result


class TestGetMonitor:
    """Test the global monitor singleton."""

    def test_get_monitor_returns_singleton(self):
        """Test that get_monitor returns the same instance."""
        monitor1 = get_monitor()
        monitor2 = get_monitor()
        assert monitor1 is monitor2
