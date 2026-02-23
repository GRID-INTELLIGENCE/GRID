"""Contribution tracker with session management."""

from __future__ import annotations

from datetime import datetime
from typing import Any


class ContributionTracker:
    """Track contribution sessions."""

    def __init__(self) -> None:
        self.sessions: dict[str, dict[str, Any]] = {}

    def start_session(self, session_id: str) -> dict[str, str]:
        """Start a contribution session."""
        self.sessions[session_id] = {
            "start_time": datetime.now().isoformat(),
            "status": "active",
        }
        return {"status": "started"}

    def stop_session(self, session_id: str) -> dict[str, str]:
        """Stop a contribution session."""
        if session_id in self.sessions:
            self.sessions[session_id]["status"] = "stopped"
            return {"status": "stopped"}
        return {"error": "Session not found"}
