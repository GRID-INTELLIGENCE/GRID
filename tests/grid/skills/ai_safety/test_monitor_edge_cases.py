"""Edge case tests for AI Safety Monitor."""

from __future__ import annotations

from typing import Generator

import pytest

import grid.skills.ai_safety.monitor as monitor_module
from grid.skills.ai_safety.monitor import SafetyMonitor


@pytest.fixture()
def reset_monitor() -> Generator[None]:
    """Reset global monitor singleton for isolation."""
    monitor_module._monitor = None
    yield
    monitor_module._monitor = None


import hashlib
from datetime import UTC, datetime
from unittest.mock import patch

from grid.skills.ai_safety.base import SafetyReport, ThreatLevel
from grid.skills.ai_safety.monitor import MonitoringSession, get_monitor


class TestSafetyMonitorEdgeCases:
    """Test SafetyMonitor edge cases and boundary conditions."""

    def test_check_content_invalid_session(self) -> None:
        """Return error report for invalid sessions."""
        monitor = SafetyMonitor()
        report = monitor.check_content("missing", "Test content")

        assert report.metadata["error"] == "Invalid or inactive session"
        assert report.overall_score == 0.0
        assert report.threat_level == "high"

    def test_get_session_stats_missing_returns_none(self) -> None:
        """Missing session stats should return None."""
        monitor = SafetyMonitor()

        assert monitor.get_session_stats("missing") is None

    def test_stop_session_missing_returns_false(self) -> None:
        """Stopping a missing session should return False."""
        monitor = SafetyMonitor()

        assert monitor.stop_session("missing") is False

    def test_get_all_sessions_excludes_inactive(self) -> None:
        """Inactive sessions should be excluded from listings."""
        monitor = SafetyMonitor()
        session = monitor.create_session("test_stream")
        monitor.stop_session(session.session_id)

        sessions = monitor.get_all_sessions()

        assert sessions == []

    def test_check_content_updates_history(self) -> None:
        """Content checks should update history with hashes and violations."""
        monitor = SafetyMonitor()
        session = monitor.create_session("test_stream")

        report = monitor.check_content(session.session_id, "Test content")

        assert report.content_hash
        assert session.history
        last_entry = session.history[-1]
        assert last_entry["content_hash"] == report.content_hash
        assert "threat_level" in last_entry

    def test_check_content_inactive_session(self) -> None:
        """Test checking content with inactive session returns error report."""
        monitor = SafetyMonitor()
        session = monitor.create_session("test_stream")
        monitor.stop_session(session.session_id)

        result = monitor.check_content(session.session_id, "test content")

        assert result.overall_score == 0.0
        assert result.threat_level == ThreatLevel.HIGH
        assert "error" in result.metadata

    def test_check_content_empty_content(self) -> None:
        """Test checking empty content."""
        monitor = SafetyMonitor()
        session = monitor.create_session("test_stream")

        result = monitor.check_content(session.session_id, "")

        assert isinstance(result, SafetyReport)
        assert result.content_hash == hashlib.sha256(b"").hexdigest()[:16]

    def test_check_content_very_long_content(self) -> None:
        """Test checking very long content."""
        monitor = SafetyMonitor()
        session = monitor.create_session("test_stream")
        long_content = "test " * 10000  # 50,000 characters

        result = monitor.check_content(session.session_id, long_content)

        assert isinstance(result, SafetyReport)
        assert result.processing_time > 0

    def test_check_content_with_malicious_content(self) -> None:
        """Test checking content that triggers safety violations."""
        monitor = SafetyMonitor()
        session = monitor.create_session("test_stream")
        malicious_content = "I want to kill someone with a weapon"

        result = monitor.check_content(session.session_id, malicious_content)

        assert isinstance(result, SafetyReport)
        assert len(result.violations) > 0
        assert result.overall_score < 1.0

    @patch("grid.skills.ai_safety.monitor.load_rules")
    def test_check_content_rules_loading_error(self, mock_load) -> None:
        """Test handling of rules loading error."""
        mock_load.side_effect = Exception("Rules loading failed")
        monitor = SafetyMonitor()
        session = monitor.create_session("test_stream")

        with pytest.raises(Exception, match="Rules loading failed"):
            monitor.check_content(session.session_id, "test content")

    def test_session_history_max_length(self) -> None:
        """Test that session history respects max length."""
        monitor = SafetyMonitor()
        session = monitor.create_session("test_stream")

        # Add more than max length (1000) entries
        for i in range(1005):
            session.history.append({"test": i})

        assert len(session.history) == 1000
        assert session.history[-1]["test"] == 1004

    def test_concurrent_session_creation(self) -> None:
        """Test creating multiple sessions."""
        monitor = SafetyMonitor()
        sessions = []
        for i in range(10):
            session = monitor.create_session(f"stream_{i}")
            sessions.append(session)

        assert len(sessions) == 10
        assert len(monitor.sessions) == 10

        # Verify all session IDs are unique
        session_ids = [s.session_id for s in sessions]
        assert len(set(session_ids)) == 10

    def test_content_hash_consistency(self) -> None:
        """Test content hash generation is consistent."""
        monitor = SafetyMonitor()
        session = monitor.create_session("test_stream")
        content = "test content"

        result1 = monitor.check_content(session.session_id, content)
        result2 = monitor.check_content(session.session_id, content)

        assert result1.content_hash == result2.content_hash

    def test_session_statistics_tracking(self) -> None:
        """Test session statistics are properly tracked."""
        monitor = SafetyMonitor()
        session = monitor.create_session("test_stream")

        # Check multiple content pieces
        for i in range(5):
            monitor.check_content(session.session_id, f"content {i}")

        stats = monitor.get_session_stats(session.session_id)
        assert stats["contents_checked"] == 5


class TestGlobalMonitorInstance:
    """Test global monitor instance management."""

    def test_get_monitor_singleton(self) -> None:
        """Test that get_monitor returns singleton instance."""
        monitor1 = get_monitor()
        monitor2 = get_monitor()

        assert monitor1 is monitor2

    def test_monitor_state_persistence(self) -> None:
        """Test monitor state persists across get_monitor calls."""
        monitor1 = get_monitor()
        session = monitor1.create_session("test_stream")

        monitor2 = get_monitor()
        stats = monitor2.get_session_stats(session.session_id)

        assert stats is not None
        assert stats["stream_id"] == "test_stream"


class TestMonitoringSessionEdgeCases:
    """Test monitoring session edge cases."""

    def test_session_with_zero_check_interval(self) -> None:
        """Test session creation with zero check interval."""
        session = MonitoringSession(
            session_id="test",
            stream_id="test",
            start_time=datetime.now(UTC),
            check_interval=0,
        )

        assert session.check_interval == 0
        assert session.active is True

    def test_session_history_with_complex_data(self) -> None:
        """Test session history with complex data structures."""
        session = MonitoringSession(
            session_id="test",
            stream_id="test",
            start_time=datetime.now(UTC),
            check_interval=60,
        )

        # Add complex data to history
        complex_data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "content_hash": "abc123",
            "threat_level": "medium",
            "violation_count": 2,
            "metadata": {
                "nested": {"data": [1, 2, 3]},
                "special_chars": "!@#$%^&*()",
            },
        }
        session.history.append(complex_data)

        assert len(session.history) == 1
        assert session.history[0] == complex_data


class TestSafetyMonitorAdvancedCases:
    """Test advanced edge cases for SafetyMonitor."""

    def test_unicode_content_handling(self) -> None:
        """Test handling of unicode and special characters."""
        monitor = SafetyMonitor()
        session = monitor.create_session("test_stream")

        unicode_content = "Test with emojis 🚀 and special chars: ñáéíóú"
        result = monitor.check_content(session.session_id, unicode_content)

        assert isinstance(result, SafetyReport)
        assert result.content_hash is not None

    def test_binary_like_content_handling(self) -> None:
        """Test handling of binary-like string content."""
        monitor = SafetyMonitor()
        session = monitor.create_session("test_stream")

        binary_content = "\x00\x01\x02\x03 binary data"
        result = monitor.check_content(session.session_id, binary_content)

        assert isinstance(result, SafetyReport)
        assert result.content_hash is not None

    def test_malformed_rules_handling(self) -> None:
        """Test handling of malformed rules."""
        monitor = SafetyMonitor()
        session = monitor.create_session("test_stream")

        # Content that might trigger rule parsing issues
        content = "{invalid: json, structure}"
        result = monitor.check_content(session.session_id, content)

        assert isinstance(result, SafetyReport)

    def test_extreme_session_count(self) -> None:
        """Test monitor with many sessions."""
        monitor = SafetyMonitor()

        # Create many sessions to test performance
        for i in range(100):
            monitor.create_session(f"stream_{i}")

        all_sessions = monitor.get_all_sessions()
        assert len(all_sessions) == 100

    def test_rapid_session_stop_start(self) -> None:
        """Test rapid session stop and start cycles."""
        monitor = SafetyMonitor()
        session = monitor.create_session("test_stream")

        # Stop and create new session rapidly
        for i in range(10):
            monitor.stop_session(session.session_id)
            session = monitor.create_session(f"test_stream_{i}")

        # Should only have the last active session
        active_sessions = monitor.get_all_sessions()
        assert len(active_sessions) == 1
