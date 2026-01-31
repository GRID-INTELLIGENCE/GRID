"""AI Safety Monitor Skill.

Real-time monitoring of content streams with periodic safety checks.
"""

from __future__ import annotations

import hashlib
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from grid.skills.base import SimpleSkill

from .base import SafetyReport, calculate_safety_score, determine_threat_level
from .config import get_config
from .rules import evaluate_rules, load_rules

logger = logging.getLogger(__name__)


@dataclass
class MonitoringSession:
    """Active monitoring session."""

    session_id: str
    stream_id: str
    start_time: datetime
    check_interval: int
    violations_detected: int = 0
    contents_checked: int = 0
    last_check_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    history: deque = field(default_factory=lambda: deque(maxlen=1000))
    active: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "session_id": self.session_id,
            "stream_id": self.stream_id,
            "start_time": self.start_time.isoformat(),
            "check_interval": self.check_interval,
            "violations_detected": self.violations_detected,
            "contents_checked": self.contents_checked,
            "last_check_time": self.last_check_time.isoformat(),
            "active": self.active,
            "uptime_seconds": (datetime.now(UTC) - self.start_time).total_seconds(),
        }


class SafetyMonitor:
    """Real-time safety monitor for content streams."""

    def __init__(self):
        self.sessions: dict[str, MonitoringSession] = {}
        self.config = get_config()

    def create_session(
        self,
        stream_id: str,
        check_interval: int = 60,
    ) -> MonitoringSession:
        """Create a new monitoring session.

        Args:
            stream_id: Identifier for the stream being monitored.
            check_interval: Seconds between checks.

        Returns:
            New monitoring session.
        """
        session_id = f"MON_{stream_id}_{int(time.time())}"

        session = MonitoringSession(
            session_id=session_id,
            stream_id=stream_id,
            start_time=datetime.now(UTC),
            check_interval=check_interval,
        )

        self.sessions[session_id] = session
        logger.info(f"Created monitoring session: {session_id}")

        return session

    def check_content(
        self,
        session_id: str,
        content: str,
        context: dict[str, Any] | None = None,
    ) -> SafetyReport:
        """Check content for safety violations.

        Args:
            session_id: Monitoring session ID.
            content: Content to check.
            context: Optional context.

        Returns:
            Safety report.
        """
        start_time = time.time()
        context = context or {}

        session = self.sessions.get(session_id)
        if not session or not session.active:
            return SafetyReport(
                overall_score=0.0,
                threat_level="high",
                violations=[],
                metadata={"error": "Invalid or inactive session"},
            )

        # Generate content hash
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        # Load and evaluate rules
        rules = load_rules()
        violations = evaluate_rules(content, rules, context)

        # Calculate safety score and threat level
        overall_score = calculate_safety_score(violations)
        threat_level = determine_threat_level(
            overall_score, violations, self.config.safety_thresholds
        )

        processing_time = time.time() - start_time

        # Update session statistics
        session.contents_checked += 1
        session.last_check_time = datetime.now(UTC)

        if violations:
            session.violations_detected += len(violations)

        # Add to history
        session.history.append({
            "timestamp": datetime.now(UTC).isoformat(),
            "content_hash": content_hash,
            "threat_level": threat_level.value,
            "violation_count": len(violations),
        })

        return SafetyReport(
            overall_score=overall_score,
            threat_level=threat_level,
            violations=violations,
            metadata={
                "stream_id": session.stream_id,
                "session_id": session_id,
                "content_hash": content_hash,
                "context": context,
            },
            processing_time=processing_time,
            content_hash=content_hash,
        )

    def get_session_stats(self, session_id: str) -> dict[str, Any] | None:
        """Get statistics for a monitoring session.

        Args:
            session_id: Session ID.

        Returns:
            Session statistics or None if not found.
        """
        session = self.sessions.get(session_id)
        if not session:
            return None

        return session.to_dict()

    def stop_session(self, session_id: str) -> bool:
        """Stop a monitoring session.

        Args:
            session_id: Session ID.

        Returns:
            True if stopped successfully.
        """
        session = self.sessions.get(session_id)
        if not session:
            return False

        session.active = False
        logger.info(f"Stopped monitoring session: {session_id}")
        return True

    def get_all_sessions(self) -> list[dict[str, Any]]:
        """Get all active sessions.

        Returns:
            List of session statistics.
        """
        return [
            session.to_dict()
            for session in self.sessions.values()
            if session.active
        ]


# Global monitor instance
_monitor: SafetyMonitor | None = None


def get_monitor() -> SafetyMonitor:
    """Get the global safety monitor instance.

    Returns:
        SafetyMonitor singleton.
    """
    global _monitor
    if _monitor is None:
        _monitor = SafetyMonitor()
    return _monitor


def monitor_handler(args: dict[str, Any]) -> dict[str, Any]:
    """Handle safety monitoring operations.

    Args:
        args: Dictionary containing:
            - operation: str, required (create, check, stats, stop, list)
            - stream_id: str, required for create
            - session_id: str, required for check/stats/stop
            - content: str, required for check
            - check_interval: int, optional for create (default 60)
            - context: dict, optional

    Returns:
        Dictionary with operation result.
    """
    operation = args.get("operation", "stats")
    monitor = get_monitor()

    if operation == "create":
        stream_id = args.get("stream_id")
        if not stream_id:
            return {"success": False, "error": "stream_id required for create"}

        check_interval = args.get("check_interval", 60)
        session = monitor.create_session(stream_id, check_interval)

        return {
            "success": True,
            "session_id": session.session_id,
            "stream_id": session.stream_id,
            "check_interval": session.check_interval,
        }

    elif operation == "check":
        session_id = args.get("session_id")
        content = args.get("content")

        if not session_id:
            return {"success": False, "error": "session_id required for check"}
        if content is None:
            return {"success": False, "error": "content required for check"}

        context = args.get("context", {})
        report = monitor.check_content(session_id, content, context)

        return {
            "success": True,
            "report": report.to_dict(),
        }

    elif operation == "stats":
        session_id = args.get("session_id")

        if session_id:
            stats = monitor.get_session_stats(session_id)
            if not stats:
                return {"success": False, "error": f"Session not found: {session_id}"}
            return {"success": True, "session": stats}
        else:
            # Return all sessions
            sessions = monitor.get_all_sessions()
            return {"success": True, "sessions": sessions, "count": len(sessions)}

    elif operation == "stop":
        session_id = args.get("session_id")
        if not session_id:
            return {"success": False, "error": "session_id required for stop"}

        success = monitor.stop_session(session_id)
        return {
            "success": success,
            "message": f"Session {session_id} stopped" if success else f"Session {session_id} not found",
        }

    elif operation == "list":
        sessions = monitor.get_all_sessions()
        return {"success": True, "sessions": sessions, "count": len(sessions)}

    else:
        return {"success": False, "error": f"Unknown operation: {operation}"}


# Skill instance
ai_safety_monitor = SimpleSkill(
    id="ai_safety_monitor",
    name="AI Safety Monitor",
    description="Real-time monitoring of content streams with safety checks",
    handler=monitor_handler,
    version="1.0.0",
)
