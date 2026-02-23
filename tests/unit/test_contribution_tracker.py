import pytest

from grid.services.contribution_tracker import ContributionTracker


class TestContributionTracker:
    @pytest.fixture
    def tracker(self):
        return ContributionTracker()

    def test_start_and_stop_session(self, tracker):
        session_id = "test_session"
        start_result = tracker.start_session(session_id)
        assert start_result["status"] == "started"
        assert tracker.sessions[session_id]["status"] == "active"

        stop_result = tracker.stop_session(session_id)
        assert stop_result["status"] == "stopped"
        assert tracker.sessions[session_id]["status"] == "stopped"
