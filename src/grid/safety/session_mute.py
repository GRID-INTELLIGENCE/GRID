"""Session-scoped mute registry for safety-sensitive flows.

Callers can treat ``session_is_muted(session_id)`` as a fail-open hint:
when true, skip non-essential side effects (extra audit fan-out, proactive
notifications) for that session until TTL expires or :func:`unmute_session`
is invoked.
"""

from __future__ import annotations

import threading
import time
from typing import Any

_PERMANENT: Any = object()


class SessionMuteRegistry:
    """Thread-safe registry of muted session identifiers."""

    __slots__ = ("_lock", "_sessions")

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # session_id -> monotonic deadline (float) or _PERMANENT
        self._sessions: dict[str, float | Any] = {}

    def mute(self, session_id: str, *, ttl_seconds: float | None = None) -> None:
        """Mark *session_id* muted. ``ttl_seconds=None`` means until :meth:`unmute`."""
        if not session_id:
            return
        with self._lock:
            if ttl_seconds is None:
                self._sessions[session_id] = _PERMANENT
            else:
                self._sessions[session_id] = time.monotonic() + max(0.0, float(ttl_seconds))

    def unmute(self, session_id: str) -> None:
        """Remove mute for *session_id* if present."""
        if not session_id:
            return
        with self._lock:
            self._sessions.pop(session_id, None)

    def is_muted(self, session_id: str) -> bool:
        """Return True if *session_id* is muted and (if timed) not yet expired."""
        if not session_id:
            return False
        with self._lock:
            deadline = self._sessions.get(session_id)
            if deadline is None:
                return False
            if deadline is _PERMANENT:
                return True
            if time.monotonic() >= float(deadline):
                del self._sessions[session_id]
                return False
            return True

    def clear(self) -> None:
        """Remove all mutes (test / admin use)."""
        with self._lock:
            self._sessions.clear()


default_registry = SessionMuteRegistry()


def mute_session(session_id: str, *, ttl_seconds: float | None = None) -> None:
    """Mute *session_id* on the process-wide :data:`default_registry`."""
    default_registry.mute(session_id, ttl_seconds=ttl_seconds)


def unmute_session(session_id: str) -> None:
    """Unmute *session_id* on the process-wide :data:`default_registry`."""
    default_registry.unmute(session_id)


def session_is_muted(session_id: str) -> bool:
    """Return whether *session_id* is muted on :data:`default_registry`."""
    return default_registry.is_muted(session_id)
