"""StreamContext - Session/Thread/Anchor Management.

Manages the flow of context across requests rather than resetting
per-request. StreamContext is the persistence layer for VECTION,
tracking sessions, managing thread anchors, and providing session
lifecycle management.

Core Responsibilities:
- Session creation, tracking, and dissolution
- Thread anchor management with automatic promotion/demotion
- Cross-session signal sharing
- Context flow and continuity
"""

from __future__ import annotations

import hashlib
import logging
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Any, TypeVar

from vection.schemas.context_state import Anchor, AnchorType, ContextStatus, VectionContext
from vection.schemas.emergence_signal import EmergenceSignal, SignalType

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class ThreadState:
    """State for a conversation thread within a session.

    A session can have multiple threads representing different
    conversation flows or task contexts.
    """

    thread_id: str
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    anchors: list[Anchor] = field(default_factory=list)
    event_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def age_seconds(self) -> float:
        """Get thread age in seconds."""
        return (datetime.now() - self.created_at).total_seconds()

    @property
    def idle_seconds(self) -> float:
        """Get seconds since last activity."""
        return (datetime.now() - self.last_active).total_seconds()

    def touch(self) -> None:
        """Mark thread as active."""
        self.last_active = datetime.now()
        self.event_count += 1

    def add_anchor(self, anchor: Anchor) -> None:
        """Add or reinforce an anchor."""
        for existing in self.anchors:
            if existing.anchor_type == anchor.anchor_type and existing.value == anchor.value:
                existing.reference()
                return
        self.anchors.append(anchor)

    def get_dominant_anchors(self, limit: int = 3) -> list[Anchor]:
        """Get the most important anchors for this thread."""
        sorted_anchors = sorted(
            [a for a in self.anchors if not a.is_stale()],
            key=lambda a: a.effective_weight,
            reverse=True,
        )
        return sorted_anchors[:limit]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "thread_id": self.thread_id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "age_seconds": round(self.age_seconds, 1),
            "idle_seconds": round(self.idle_seconds, 1),
            "event_count": self.event_count,
            "anchor_count": len(self.anchors),
            "dominant_anchors": [a.to_dict() for a in self.get_dominant_anchors()],
            "metadata": self.metadata,
        }


@dataclass
class SessionSnapshot:
    """Point-in-time snapshot of a session for history tracking."""

    timestamp: datetime
    context_status: ContextStatus
    anchor_count: int
    signal_count: int
    velocity_direction: str | None
    interaction_count: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "context_status": self.context_status.value,
            "anchor_count": self.anchor_count,
            "signal_count": self.signal_count,
            "velocity_direction": self.velocity_direction,
            "interaction_count": self.interaction_count,
        }


class StreamContext:
    """Session and thread context manager.

    Manages the lifecycle of sessions and threads, providing context
    continuity across requests. This is the foundational layer that
    enables VECTION's "context that flows, not resets" capability.

    Features:
    - Multi-session management with automatic cleanup
    - Thread-level context within sessions
    - Anchor promotion from thread to session level
    - Cross-session signal sharing
    - Session history and snapshots
    """

    _instance: StreamContext | None = None
    _lock: Lock = Lock()

    def __init__(
        self,
        max_sessions: int = 1000,
        max_threads_per_session: int = 50,
        session_ttl_hours: float = 24.0,
        thread_ttl_hours: float = 4.0,
        snapshot_interval_minutes: float = 5.0,
    ) -> None:
        """Initialize the StreamContext manager.

        Args:
            max_sessions: Maximum number of concurrent sessions.
            max_threads_per_session: Maximum threads per session.
            session_ttl_hours: Session time-to-live in hours.
            thread_ttl_hours: Thread time-to-live in hours.
            snapshot_interval_minutes: Interval between automatic snapshots.
        """
        self._sessions: dict[str, VectionContext] = {}
        self._threads: dict[str, dict[str, ThreadState]] = defaultdict(dict)
        self._session_history: dict[str, list[SessionSnapshot]] = defaultdict(list)
        self._shared_signals: dict[str, EmergenceSignal] = {}

        self._max_sessions = max_sessions
        self._max_threads_per_session = max_threads_per_session
        self._session_ttl_seconds = session_ttl_hours * 3600
        self._thread_ttl_seconds = thread_ttl_hours * 3600
        self._snapshot_interval_seconds = snapshot_interval_minutes * 60

        self._last_cleanup: float = time.time()
        self._cleanup_interval: float = 300.0  # 5 minutes

        self._event_hooks: dict[str, list[Callable[..., Any]]] = defaultdict(list)

        logger.info(
            f"StreamContext initialized: max_sessions={max_sessions}, "
            f"session_ttl={session_ttl_hours}h, thread_ttl={thread_ttl_hours}h"
        )

    @classmethod
    def get_instance(cls) -> StreamContext:
        """Get the singleton StreamContext instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (for testing)."""
        with cls._lock:
            cls._instance = None

    # =========================================================================
    # Session Management
    # =========================================================================

    def create_session(
        self,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> VectionContext:
        """Create a new session context.

        Args:
            session_id: Optional session ID (generated if not provided).
            metadata: Optional session metadata.

        Returns:
            New VectionContext for the session.
        """
        if session_id is None:
            session_id = self._generate_session_id()

        if session_id in self._sessions:
            logger.warning(f"Session {session_id} already exists, returning existing")
            return self._sessions[session_id]

        # Enforce max sessions
        if len(self._sessions) >= self._max_sessions:
            self._evict_oldest_session()

        context = VectionContext.create(session_id, metadata)
        self._sessions[session_id] = context
        self._threads[session_id] = {}
        self._session_history[session_id] = []

        self._emit("session_created", session_id, context)
        logger.debug(f"Created session: {session_id}")

        return context

    def get_session(self, session_id: str) -> VectionContext | None:
        """Get an existing session context.

        Args:
            session_id: Session identifier.

        Returns:
            VectionContext or None if not found.
        """
        return self._sessions.get(session_id)

    def get_or_create_session(
        self,
        session_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> VectionContext:
        """Get existing session or create new one.

        Args:
            session_id: Session identifier.
            metadata: Metadata for new session.

        Returns:
            VectionContext for the session.
        """
        if session_id in self._sessions:
            return self._sessions[session_id]
        return self.create_session(session_id, metadata)

    def dissolve_session(self, session_id: str) -> bool:
        """Dissolve a session and clean up resources.

        Args:
            session_id: Session to dissolve.

        Returns:
            True if session was dissolved.
        """
        if session_id not in self._sessions:
            return False

        context = self._sessions[session_id]
        context.dissolve()

        # Clean up threads
        if session_id in self._threads:
            del self._threads[session_id]

        # Keep history for a while (don't delete immediately)
        del self._sessions[session_id]

        self._emit("session_dissolved", session_id)
        logger.info(f"Dissolved session: {session_id}")

        return True

    def list_sessions(self) -> list[str]:
        """Get all active session IDs."""
        return list(self._sessions.keys())

    def get_session_count(self) -> int:
        """Get number of active sessions."""
        return len(self._sessions)

    # =========================================================================
    # Thread Management
    # =========================================================================

    def create_thread(
        self,
        session_id: str,
        thread_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ThreadState | None:
        """Create a thread within a session.

        Args:
            session_id: Parent session ID.
            thread_id: Optional thread ID (generated if not provided).
            metadata: Optional thread metadata.

        Returns:
            ThreadState or None if session doesn't exist.
        """
        if session_id not in self._sessions:
            logger.warning(f"Cannot create thread: session {session_id} not found")
            return None

        if thread_id is None:
            thread_id = self._generate_thread_id(session_id)

        # Enforce max threads
        if len(self._threads[session_id]) >= self._max_threads_per_session:
            self._evict_oldest_thread(session_id)

        thread = ThreadState(
            thread_id=thread_id,
            session_id=session_id,
            metadata=metadata or {},
        )

        self._threads[session_id][thread_id] = thread
        self._emit("thread_created", session_id, thread_id, thread)

        logger.debug(f"Created thread: {thread_id} in session {session_id}")
        return thread

    def get_thread(self, session_id: str, thread_id: str) -> ThreadState | None:
        """Get a thread by ID.

        Args:
            session_id: Parent session ID.
            thread_id: Thread identifier.

        Returns:
            ThreadState or None if not found.
        """
        return self._threads.get(session_id, {}).get(thread_id)

    def get_or_create_thread(
        self,
        session_id: str,
        thread_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> ThreadState | None:
        """Get existing thread or create new one.

        Args:
            session_id: Parent session ID.
            thread_id: Thread identifier.
            metadata: Metadata for new thread.

        Returns:
            ThreadState or None if session doesn't exist.
        """
        existing = self.get_thread(session_id, thread_id)
        if existing:
            return existing
        return self.create_thread(session_id, thread_id, metadata)

    def list_threads(self, session_id: str) -> list[str]:
        """Get all thread IDs for a session."""
        return list(self._threads.get(session_id, {}).keys())

    def dissolve_thread(self, session_id: str, thread_id: str) -> bool:
        """Dissolve a thread.

        Args:
            session_id: Parent session ID.
            thread_id: Thread to dissolve.

        Returns:
            True if thread was dissolved.
        """
        if session_id not in self._threads:
            return False

        if thread_id not in self._threads[session_id]:
            return False

        # Promote important anchors to session level before dissolving
        thread = self._threads[session_id][thread_id]
        session = self._sessions.get(session_id)
        if session:
            for anchor in thread.get_dominant_anchors(limit=2):
                if anchor.effective_weight > 0.6:
                    session.add_anchor(anchor)

        del self._threads[session_id][thread_id]
        self._emit("thread_dissolved", session_id, thread_id)

        logger.debug(f"Dissolved thread: {thread_id} from session {session_id}")
        return True

    # =========================================================================
    # Anchor Management
    # =========================================================================

    def add_anchor_to_session(
        self,
        session_id: str,
        anchor: Anchor,
    ) -> bool:
        """Add an anchor directly to a session.

        Args:
            session_id: Session identifier.
            anchor: Anchor to add.

        Returns:
            True if anchor was added.
        """
        session = self._sessions.get(session_id)
        if session is None:
            return False

        session.add_anchor(anchor)
        return True

    def add_anchor_to_thread(
        self,
        session_id: str,
        thread_id: str,
        anchor: Anchor,
    ) -> bool:
        """Add an anchor to a thread.

        Args:
            session_id: Session identifier.
            thread_id: Thread identifier.
            anchor: Anchor to add.

        Returns:
            True if anchor was added.
        """
        thread = self.get_thread(session_id, thread_id)
        if thread is None:
            return False

        thread.add_anchor(anchor)
        return True

    def promote_anchor(
        self,
        session_id: str,
        thread_id: str,
        anchor_id: str,
    ) -> bool:
        """Promote an anchor from thread to session level.

        Args:
            session_id: Session identifier.
            thread_id: Thread identifier.
            anchor_id: Anchor to promote.

        Returns:
            True if anchor was promoted.
        """
        thread = self.get_thread(session_id, thread_id)
        session = self._sessions.get(session_id)

        if thread is None or session is None:
            return False

        for anchor in thread.anchors:
            if anchor.anchor_id == anchor_id:
                session.add_anchor(anchor)
                logger.debug(f"Promoted anchor {anchor_id} to session level")
                return True

        return False

    def get_session_anchors(
        self,
        session_id: str,
        anchor_type: AnchorType | None = None,
    ) -> list[Anchor]:
        """Get anchors for a session.

        Args:
            session_id: Session identifier.
            anchor_type: Optional filter by type.

        Returns:
            List of anchors.
        """
        session = self._sessions.get(session_id)
        if session is None:
            return []

        if anchor_type is None:
            return list(session.thread_anchors)

        return session.get_anchors_by_type(anchor_type)

    # =========================================================================
    # Signal Sharing
    # =========================================================================

    def share_signal(self, signal: EmergenceSignal) -> None:
        """Share a signal with the global emergence context.

        Security: ASIF (AI Session Isolation Framework) enforced.
        """
        try:
            from vection.core.security.session_isolation import validate_session_boundary

            if not validate_session_boundary(signal, self.session_id):
                # Silent drop. Attacker believes the signal was shared.
                return
        except ImportError:
            pass

        self._shared_signals[signal.signal_id] = signal
        self._emit("signal_shared", signal)

        # Enforce size limit
        if len(self._shared_signals) > 500:
            self._prune_shared_signals()

    def get_shared_signals(
        self,
        signal_type: SignalType | None = None,
        min_salience: float = 0.3,
    ) -> list[EmergenceSignal]:
        """Get shared signals.

        Args:
            signal_type: Optional filter by type.
            min_salience: Minimum effective salience.

        Returns:
            List of matching signals.
        """
        signals = []
        for signal in self._shared_signals.values():
            if signal.effective_salience < min_salience:
                continue
            if signal_type is not None and signal.signal_type != signal_type:
                continue
            signals.append(signal)

        return sorted(signals, key=lambda s: s.effective_salience, reverse=True)

    # =========================================================================
    # Snapshots and History
    # =========================================================================

    def take_snapshot(self, session_id: str) -> SessionSnapshot | None:
        """Take a snapshot of session state.

        Args:
            session_id: Session to snapshot.

        Returns:
            SessionSnapshot or None if session not found.
        """
        session = self._sessions.get(session_id)
        if session is None:
            return None

        velocity_direction = None
        if session.has_velocity and hasattr(session.cognitive_velocity, "direction"):
            velocity_direction = session.cognitive_velocity.direction.value

        snapshot = SessionSnapshot(
            timestamp=datetime.now(),
            context_status=session.status,
            anchor_count=session.anchor_count,
            signal_count=session.signal_count,
            velocity_direction=velocity_direction,
            interaction_count=session.interaction_count,
        )

        self._session_history[session_id].append(snapshot)

        # Keep only recent history
        if len(self._session_history[session_id]) > 100:
            self._session_history[session_id] = self._session_history[session_id][-100:]

        return snapshot

    def get_session_history(
        self,
        session_id: str,
        limit: int = 20,
    ) -> list[SessionSnapshot]:
        """Get session history snapshots.

        Args:
            session_id: Session identifier.
            limit: Maximum snapshots to return.

        Returns:
            List of snapshots (newest first).
        """
        history = self._session_history.get(session_id, [])
        return list(reversed(history[-limit:]))

    # =========================================================================
    # Maintenance
    # =========================================================================

    async def cleanup(self) -> dict[str, int]:
        """Run cleanup of stale sessions and threads.

        Returns:
            Dictionary with cleanup statistics.
        """
        now = time.time()
        stats = {
            "sessions_dissolved": 0,
            "threads_dissolved": 0,
            "signals_pruned": 0,
        }

        # Clean up stale sessions
        for session_id in list(self._sessions.keys()):
            session = self._sessions[session_id]
            if session.staleness > self._session_ttl_seconds:
                self.dissolve_session(session_id)
                stats["sessions_dissolved"] += 1

        # Clean up stale threads
        for session_id in list(self._threads.keys()):
            for thread_id in list(self._threads[session_id].keys()):
                thread = self._threads[session_id][thread_id]
                if thread.idle_seconds > self._thread_ttl_seconds:
                    self.dissolve_thread(session_id, thread_id)
                    stats["threads_dissolved"] += 1

        # Prune shared signals
        before_count = len(self._shared_signals)
        self._prune_shared_signals()
        stats["signals_pruned"] = before_count - len(self._shared_signals)

        self._last_cleanup = now
        logger.debug(f"Cleanup completed: {stats}")

        return stats

    async def maybe_cleanup(self) -> None:
        """Run cleanup if enough time has passed."""
        if time.time() - self._last_cleanup > self._cleanup_interval:
            await self.cleanup()

    def get_stats(self) -> dict[str, Any]:
        """Get StreamContext statistics."""
        total_threads = sum(len(threads) for threads in self._threads.values())
        total_anchors = sum(len(s.thread_anchors) for s in self._sessions.values())

        return {
            "active_sessions": len(self._sessions),
            "total_threads": total_threads,
            "total_anchors": total_anchors,
            "shared_signals": len(self._shared_signals),
            "max_sessions": self._max_sessions,
            "session_ttl_hours": self._session_ttl_seconds / 3600,
        }

    # =========================================================================
    # Event Hooks
    # =========================================================================

    def on(self, event: str, callback: Callable[..., Any]) -> None:
        """Register an event hook.

        Args:
            event: Event name (session_created, thread_created, etc.).
            callback: Callback function.
        """
        self._event_hooks[event].append(callback)

    def off(self, event: str, callback: Callable[..., Any]) -> None:
        """Unregister an event hook.

        Args:
            event: Event name.
            callback: Callback to remove.
        """
        if callback in self._event_hooks[event]:
            self._event_hooks[event].remove(callback)

    def _emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        """Emit an event to all registered hooks."""
        for callback in self._event_hooks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Event hook error for {event}: {e}")

    # =========================================================================
    # Internal Helpers
    # =========================================================================

    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        hash_input = f"session:{time.time()}:{id(self)}"
        return f"ses_{hashlib.md5(hash_input.encode()).hexdigest()[:12]}"

    def _generate_thread_id(self, session_id: str) -> str:
        """Generate a unique thread ID."""
        thread_count = len(self._threads.get(session_id, {}))
        hash_input = f"thread:{session_id}:{thread_count}:{time.time()}"
        return f"thr_{hashlib.md5(hash_input.encode()).hexdigest()[:10]}"

    def _evict_oldest_session(self) -> None:
        """Evict the oldest session to make room."""
        if not self._sessions:
            return

        oldest_id = min(
            self._sessions.keys(),
            key=lambda sid: self._sessions[sid].established_at,
        )
        self.dissolve_session(oldest_id)
        logger.info(f"Evicted oldest session: {oldest_id}")

    def _evict_oldest_thread(self, session_id: str) -> None:
        """Evict the oldest thread in a session."""
        threads = self._threads.get(session_id, {})
        if not threads:
            return

        oldest_id = min(
            threads.keys(),
            key=lambda tid: threads[tid].created_at,
        )
        self.dissolve_thread(session_id, oldest_id)
        logger.info(f"Evicted oldest thread: {oldest_id} from {session_id}")

    def _prune_shared_signals(self) -> None:
        """Remove expired shared signals."""
        to_remove = []
        for signal_id, signal in self._shared_signals.items():
            if signal.is_expired() or signal.effective_salience < 0.1:
                to_remove.append(signal_id)

        for signal_id in to_remove:
            del self._shared_signals[signal_id]


# Module-level convenience functions
def get_stream_context() -> StreamContext:
    """Get the global StreamContext instance."""
    return StreamContext.get_instance()


def create_session(
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> VectionContext:
    """Create a new session."""
    return get_stream_context().create_session(session_id, metadata)


def get_session(session_id: str) -> VectionContext | None:
    """Get an existing session."""
    return get_stream_context().get_session(session_id)
