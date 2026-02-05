"""Handler tests for AI Safety Monitor."""

from __future__ import annotations

from typing import Generator

import pytest

import grid.skills.ai_safety.monitor as monitor_module
from grid.skills.ai_safety.monitor import monitor_handler


@pytest.fixture()
def reset_monitor() -> Generator[None]:
    """Reset global monitor singleton for isolation."""
    monitor_module._monitor = None
    yield
    monitor_module._monitor = None


class TestMonitorHandlerEdgeCases:
    """Test monitor handler error paths and edge cases."""

    def test_check_missing_session_id(self, reset_monitor: None) -> None:
        """Check operation should require session_id."""
        result = monitor_handler({"operation": "check", "content": "Test"})

        assert result["success"] is False
        assert result["error"] == "session_id required for check"

    def test_check_missing_content(self, reset_monitor: None) -> None:
        """Check operation should require content."""
        result = monitor_handler({"operation": "check", "session_id": "missing"})

        assert result["success"] is False
        assert result["error"] == "content required for check"

    def test_stats_missing_session_id(self, reset_monitor: None) -> None:
        """Stats should error when session_id is unknown."""
        result = monitor_handler({"operation": "stats", "session_id": "missing"})

        assert result["success"] is False
        assert result["error"] == "Session not found: missing"

    def test_stop_missing_session_id(self, reset_monitor: None) -> None:
        """Stop operation should require session_id."""
        result = monitor_handler({"operation": "stop"})

        assert result["success"] is False
        assert result["error"] == "session_id required for stop"

    def test_create_uses_default_interval(self, reset_monitor: None) -> None:
        """Create should default to configured check interval."""
        result = monitor_handler({"operation": "create", "stream_id": "stream"})

        assert result["success"] is True
        assert result["check_interval"] == 60

    def test_handler_create_operation_success(self, reset_monitor: None) -> None:
        """Test successful session creation via handler."""
        args = {
            "operation": "create",
            "stream_id": "test_stream",
            "check_interval": 30,
        }

        result = monitor_handler(args)

        assert result["success"] is True
        assert "session_id" in result
        assert result["stream_id"] == "test_stream"
        assert result["check_interval"] == 30

    def test_handler_check_operation_success(self, reset_monitor: None) -> None:
        """Test successful content check via handler."""
        # First create a session
        session_result = monitor_handler(
            {
                "operation": "create",
                "stream_id": "test_stream",
            }
        )
        session_id = session_result["session_id"]

        args = {
            "operation": "check",
            "session_id": session_id,
            "content": "This is safe content",
            "context": {"user_id": "123"},
        }

        result = monitor_handler(args)

        assert result["success"] is True
        assert "report" in result
        assert isinstance(result["report"], dict)

    def test_handler_check_operation_invalid_session(self, reset_monitor: None) -> None:
        """Test content check with invalid session."""
        args = {
            "operation": "check",
            "session_id": "invalid_session",
            "content": "test content",
        }

        result = monitor_handler(args)

        assert result["success"] is True
        assert result["report"]["threat_level"] == "high"
        assert "error" in result["report"]["metadata"]

    def test_handler_stats_operation_specific_session(self, reset_monitor: None) -> None:
        """Test getting stats for specific session via handler."""
        # First create a session
        session_result = monitor_handler(
            {
                "operation": "create",
                "stream_id": "test_stream",
            }
        )
        session_id = session_result["session_id"]

        args = {
            "operation": "stats",
            "session_id": session_id,
        }

        result = monitor_handler(args)

        assert result["success"] is True
        assert "session" in result
        assert result["session"]["stream_id"] == "test_stream"

    def test_handler_stats_operation_all_sessions(self, reset_monitor: None) -> None:
        """Test getting stats for all sessions via handler."""
        # Create multiple sessions
        monitor_handler({"operation": "create", "stream_id": "stream1"})
        monitor_handler({"operation": "create", "stream_id": "stream2"})

        args = {"operation": "stats"}

        result = monitor_handler(args)

        assert result["success"] is True
        assert "sessions" in result
        assert "count" in result
        assert result["count"] == 2

    def test_handler_stop_operation_success(self, reset_monitor: None) -> None:
        """Test successful session stop via handler."""
        # First create a session
        session_result = monitor_handler(
            {
                "operation": "create",
                "stream_id": "test_stream",
            }
        )
        session_id = session_result["session_id"]

        args = {
            "operation": "stop",
            "session_id": session_id,
        }

        result = monitor_handler(args)

        assert result["success"] is True
        assert "stopped" in result["message"]

    def test_handler_stop_operation_nonexistent_session(self, reset_monitor: None) -> None:
        """Test stopping non-existent session."""
        args = {
            "operation": "stop",
            "session_id": "nonexistent",
        }

        result = monitor_handler(args)

        assert result["success"] is False
        assert "not found" in result["message"]

    def test_handler_list_operation(self, reset_monitor: None) -> None:
        """Test listing all active sessions via handler."""
        # Create multiple sessions
        monitor_handler({"operation": "create", "stream_id": "stream1"})
        monitor_handler({"operation": "create", "stream_id": "stream2"})

        args = {"operation": "list"}

        result = monitor_handler(args)

        assert result["success"] is True
        assert "sessions" in result
        assert "count" in result
        assert result["count"] == 2

    def test_handler_list_operation_empty(self, reset_monitor: None) -> None:
        """Test listing sessions when none exist."""
        args = {"operation": "list"}

        result = monitor_handler(args)

        assert result["success"] is True
        assert result["sessions"] == []
        assert result["count"] == 0

    def test_handler_unknown_operation(self, reset_monitor: None) -> None:
        """Test handling unknown operation."""
        args = {"operation": "unknown"}

        result = monitor_handler(args)

        assert result["success"] is False
        assert "Unknown operation" in result["error"]

    def test_handler_default_operation(self, reset_monitor: None) -> None:
        """Test default operation when none specified."""
        args = {}

        result = monitor_handler(args)

        assert result["success"] is True
        assert "sessions" in result  # Defaults to stats operation

    def test_handler_with_complex_context(self, reset_monitor: None) -> None:
        """Test handler with complex context data."""
        session_result = monitor_handler(
            {
                "operation": "create",
                "stream_id": "test_stream",
            }
        )
        session_id = session_result["session_id"]

        complex_context = {
            "user_id": "123",
            "metadata": {
                "source": "web",
                "timestamp": "2024-01-01T00:00:00Z",
                "tags": ["test", "safety"],
                "nested": {"key": "value"},
            },
        }

        args = {
            "operation": "check",
            "session_id": session_id,
            "content": "test content",
            "context": complex_context,
        }

        result = monitor_handler(args)

        assert result["success"] is True

    def test_handler_with_unicode_content(self, reset_monitor: None) -> None:
        """Test handler with unicode and special characters."""
        session_result = monitor_handler(
            {
                "operation": "create",
                "stream_id": "test_stream",
            }
        )
        session_id = session_result["session_id"]

        unicode_content = "Test with emojis 🚀 and special chars: ñáéíóú"

        args = {
            "operation": "check",
            "session_id": session_id,
            "content": unicode_content,
        }

        result = monitor_handler(args)

        assert result["success"] is True
        assert result["report"]["content_hash"] is not None

    def test_handler_operation_case_sensitivity(self, reset_monitor: None) -> None:
        """Test that operation names are case sensitive."""
        args = {"operation": "CREATE", "stream_id": "test"}

        result = monitor_handler(args)

        assert result["success"] is False
        assert "Unknown operation" in result["error"]

    def test_handler_multiple_operations_sequence(self, reset_monitor: None) -> None:
        """Test sequence of multiple handler operations."""
        # Create session
        create_result = monitor_handler(
            {
                "operation": "create",
                "stream_id": "test_stream",
            }
        )
        session_id = create_result["session_id"]

        # Check content
        check_result = monitor_handler(
            {
                "operation": "check",
                "session_id": session_id,
                "content": "test content",
            }
        )
        assert check_result["success"] is True

        # Get stats
        stats_result = monitor_handler(
            {
                "operation": "stats",
                "session_id": session_id,
            }
        )
        assert stats_result["success"] is True
        assert stats_result["session"]["contents_checked"] == 1

        # Stop session
        stop_result = monitor_handler(
            {
                "operation": "stop",
                "session_id": session_id,
            }
        )
        assert stop_result["success"] is True

    def test_handler_create_missing_stream_id(self, reset_monitor: None) -> None:
        """Test session creation with missing stream_id."""
        args = {"operation": "create"}

        result = monitor_handler(args)

        assert result["success"] is False
        assert "stream_id required" in result["error"]
