"""Codebase activity tracker for monitoring Git and file system changes."""

import asyncio
import logging
import os
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ActivityEvent:
    """Represents a codebase activity event."""

    def __init__(self, event_type: str, path: str, details: dict[str, Any] | None = None, severity: str = "info"):
        self.timestamp = datetime.now(UTC).isoformat()
        self.event_type = event_type
        self.path = path
        self.details = details or {}
        self.severity = severity

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "path": self.path,
            "details": self.details,
            "severity": self.severity,
        }


class CodebaseTracker:
    """Monitors codebase for activity changes."""

    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.git_dir = self.root_dir / ".git"
        self._last_checked_time = time.time()
        self._last_commit_hash = self._get_latest_commit()

    def _get_latest_commit(self) -> str | None:
        """Get the latest commit hash."""
        try:
            if not self.git_dir.exists():
                return None
            return subprocess.check_output(  # noqa: S603 subprocess call is intentional
                ["git", "-C", str(self.root_dir), "rev-parse", "HEAD"],
                text=True,
                stderr=subprocess.STDOUT,  # noqa: S607 partial path is intentional
            ).strip()
        except Exception:
            return None

    async def _get_latest_commit_async(self) -> str | None:
        """Get the latest commit hash (async)."""
        try:
            if not self.git_dir.exists():
                return None
            proc = await asyncio.create_subprocess_exec(
                "git",
                "-C",
                str(self.root_dir),
                "rev-parse",
                "HEAD",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            return stdout.decode().strip() if proc.returncode == 0 else None
        except Exception:
            return None

    def poll_activity(self) -> list[ActivityEvent]:
        """Poll for new activity since last check."""
        events = []

        # Check for new commits
        current_commit = self._get_latest_commit()
        if current_commit and current_commit != self._last_commit_hash:
            events.append(self._capture_commit_event(current_commit))
            self._last_commit_hash = current_commit

        # Check for modified files (quick poll)
        modified_files = self._get_modified_files()
        events.extend(
            ActivityEvent(event_type="file_modified", path=file_path, details={"polled": True})
            for file_path in modified_files
        )

        self._last_checked_time = time.time()
        return events

    async def poll_activity_async(self) -> list[ActivityEvent]:
        """Poll for new activity since last check (async)."""
        events = []

        # Check for new commits
        current_commit = await self._get_latest_commit_async()
        if current_commit and current_commit != self._last_commit_hash:
            event = await self._capture_commit_event_async(current_commit)
            events.append(event)
            self._last_commit_hash = current_commit

        # Check for modified files (quick poll)
        modified_files = await self._get_modified_files_async()
        events.extend(
            ActivityEvent(event_type="file_modified", path=file_path, details={"polled": True})
            for file_path in modified_files
        )

        self._last_checked_time = time.time()
        return events

    def _capture_commit_event(self, commit_hash: str) -> ActivityEvent:
        """Capture details about a new commit."""
        try:
            show_output = subprocess.check_output(  # noqa: S603 subprocess call is intentional
                ["git", "-C", str(self.root_dir), "show", "--name-only", "--format=%s", commit_hash],
                text=True,  # noqa: S607 partial path is intentional
            ).splitlines()

            message = show_output[0]
            files = show_output[1:] if len(show_output) > 1 else []

            return ActivityEvent(
                event_type="git_commit",
                path=commit_hash,
                details={
                    "message": message,
                    "files": files,
                    "author": subprocess.check_output(  # noqa: S603 subprocess call is intentional
                        ["git", "-C", str(self.root_dir), "show", "-s", "--format=%an", commit_hash],
                        text=True,  # noqa: S607 partial path is intentional
                    ).strip(),
                },
                severity="info",
            )
        except Exception as e:
            return ActivityEvent(event_type="error", path="git", details={"error": str(e)}, severity="error")

    def _get_modified_files(self) -> list[str]:
        """Get list of files modified since last check using git status."""
        try:
            output = subprocess.check_output(  # noqa: S603 subprocess call is intentional
                ["git", "-C", str(self.root_dir), "status", "--porcelain"],
                text=True,  # noqa: S607 partial path is intentional
            ).splitlines()

            modified = []
            for line in output:
                if line.strip():
                    parts = line.split(maxsplit=1)
                    if len(parts) == 2:
                        modified.append(parts[1])
            return modified
        except Exception:
            return []

    async def _capture_commit_event_async(self, commit_hash: str) -> ActivityEvent:
        """Capture details about a new commit (async)."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "git",
                "-C",
                str(self.root_dir),
                "show",
                "--name-only",
                "--format=%s",
                commit_hash,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            show_output = stdout.decode().splitlines() if proc.returncode == 0 else []

            message = show_output[0] if show_output else ""
            files = show_output[1:] if len(show_output) > 1 else []

            proc_author = await asyncio.create_subprocess_exec(
                "git",
                "-C",
                str(self.root_dir),
                "show",
                "-s",
                "--format=%an",
                commit_hash,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout_author, _ = await proc_author.communicate()
            author = stdout_author.decode().strip() if proc_author.returncode == 0 else "unknown"

            return ActivityEvent(
                event_type="git_commit",
                path=commit_hash,
                details={
                    "message": message,
                    "files": files,
                    "author": author,
                },
                severity="info",
            )
        except Exception as e:
            return ActivityEvent(event_type="error", path="git", details={"error": str(e)}, severity="error")

    async def _get_modified_files_async(self) -> list[str]:
        """Get list of files modified since last check using git status (async)."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "git",
                "-C",
                str(self.root_dir),
                "status",
                "--porcelain",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            output = stdout.decode().splitlines() if proc.returncode == 0 else []

            modified = []
            for line in output:
                if line.strip():
                    parts = line.split(maxsplit=1)
                    if len(parts) == 2:
                        modified.append(parts[1])
            return modified
        except Exception:
            return []


if __name__ == "__main__":
    # Basic self-test
    tracker = CodebaseTracker(os.getcwd())
    print(f"Tracking: {tracker.root_dir}")
    while True:
        events = tracker.poll_activity()
        if events:
            for event in events:
                print(f"[{event.timestamp}] {event.event_type}: {event.path}")
        time.sleep(5)
