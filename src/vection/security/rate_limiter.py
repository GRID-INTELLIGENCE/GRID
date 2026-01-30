"""Rate Limiter - Configurable request throttling.

Provides rate limiting to prevent abuse of VECTION operations.
Implements sliding window rate limiting with configurable limits
per operation type and session.

Features:
- Sliding window algorithm for smooth rate limiting
- Per-session, per-operation tracking
- Configurable limits for different operation types
- Clear feedback when limits are exceeded
- Integration with audit logging
- Thread-safe implementation
- Automatic cleanup of stale entries

Usage:
    from vection.security.rate_limiter import RateLimiter, RateLimitConfig

    limiter = RateLimiter()

    # Check if operation is allowed
    if limiter.allow(session_id, operation="reinforce"):
        # Proceed with operation
        pass
    else:
        # Rate limit exceeded - return appropriate error
        raise RateLimitExceeded("Too many reinforce calls")

    # Or use the decorator
    @limiter.rate_limited(operation="signal_create")
    async def create_signal(session_id: str, ...):
        ...
"""

from __future__ import annotations

import functools
import threading
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded.

    Attributes:
        operation: The operation that was rate limited.
        session_id: The session that exceeded the limit.
        current_count: Current request count.
        limit: Maximum allowed requests.
        window_seconds: Time window in seconds.
        retry_after: Seconds until the limit resets.
    """

    def __init__(
        self,
        message: str,
        operation: str = "",
        session_id: str = "",
        current_count: int = 0,
        limit: int = 0,
        window_seconds: float = 0,
        retry_after: float = 0,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Error message.
            operation: Operation that was rate limited.
            session_id: Session identifier.
            current_count: Current request count.
            limit: Maximum allowed requests.
            window_seconds: Time window.
            retry_after: Seconds until retry is allowed.
        """
        super().__init__(message)
        self.operation = operation
        self.session_id = session_id
        self.current_count = current_count
        self.limit = limit
        self.window_seconds = window_seconds
        self.retry_after = retry_after

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses.

        Returns:
            Dictionary with rate limit details.
        """
        return {
            "error": "rate_limit_exceeded",
            "message": str(self),
            "operation": self.operation,
            "current_count": self.current_count,
            "limit": self.limit,
            "window_seconds": self.window_seconds,
            "retry_after": round(self.retry_after, 2),
        }


class OperationType(str, Enum):
    """Standard operation types for rate limiting."""

    # Signal operations
    SIGNAL_CREATE = "signal_create"
    SIGNAL_REINFORCE = "signal_reinforce"
    SIGNAL_SHARE = "signal_share"

    # Context operations
    CONTEXT_ESTABLISH = "context_establish"
    CONTEXT_QUERY = "context_query"
    CONTEXT_PROJECT = "context_project"

    # Session operations
    SESSION_CREATE = "session_create"
    SESSION_ACCESS = "session_access"

    # Velocity operations
    VELOCITY_TRACK = "velocity_track"

    # Generic
    DEFAULT = "default"


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting.

    Attributes:
        default_limit: Default requests per window.
        default_window_seconds: Default time window.
        operation_limits: Per-operation limit overrides.
        operation_windows: Per-operation window overrides.
        global_limit: Optional global limit across all operations.
        global_window_seconds: Window for global limit.
        cleanup_interval_seconds: How often to clean stale entries.
        enable_logging: Whether to log rate limit events.
    """

    default_limit: int = 100
    default_window_seconds: float = 60.0
    operation_limits: dict[str, int] = field(default_factory=dict)
    operation_windows: dict[str, float] = field(default_factory=dict)
    global_limit: int | None = None
    global_window_seconds: float = 60.0
    cleanup_interval_seconds: float = 300.0
    enable_logging: bool = True

    def __post_init__(self) -> None:
        """Set default operation limits."""
        # More restrictive limits for sensitive operations
        defaults = {
            OperationType.SIGNAL_REINFORCE.value: 50,  # Prevent burst reinforcement
            OperationType.SIGNAL_SHARE.value: 20,  # Limit sharing frequency
            OperationType.SESSION_CREATE.value: 10,  # Limit session creation
            OperationType.CONTEXT_ESTABLISH.value: 200,  # Higher for normal use
            OperationType.CONTEXT_QUERY.value: 500,  # Queries are lightweight
            OperationType.CONTEXT_PROJECT.value: 100,  # Projections are moderate
        }

        for op, limit in defaults.items():
            if op not in self.operation_limits:
                self.operation_limits[op] = limit


@dataclass
class RateLimitEntry:
    """A single rate limit tracking entry.

    Attributes:
        timestamps: List of request timestamps in the current window.
        window_start: Start of the current window.
    """

    timestamps: list[float] = field(default_factory=list)
    window_start: float = field(default_factory=time.time)

    def cleanup_old(self, window_seconds: float) -> None:
        """Remove timestamps outside the current window.

        Args:
            window_seconds: Window size in seconds.
        """
        cutoff = time.time() - window_seconds
        self.timestamps = [ts for ts in self.timestamps if ts > cutoff]

    def add_request(self) -> None:
        """Record a new request."""
        self.timestamps.append(time.time())

    def get_count(self, window_seconds: float) -> int:
        """Get request count in current window.

        Args:
            window_seconds: Window size.

        Returns:
            Number of requests in window.
        """
        self.cleanup_old(window_seconds)
        return len(self.timestamps)

    def get_oldest_timestamp(self) -> float | None:
        """Get the oldest timestamp in the window.

        Returns:
            Oldest timestamp or None if empty.
        """
        return min(self.timestamps) if self.timestamps else None


@dataclass
class RateLimitStatus:
    """Status of a rate limit check.

    Attributes:
        allowed: Whether the request is allowed.
        current_count: Current request count.
        limit: Maximum allowed requests.
        remaining: Requests remaining in window.
        window_seconds: Time window.
        retry_after: Seconds until retry allowed (if blocked).
        utilization_percent: Percentage of limit used.
    """

    allowed: bool
    current_count: int
    limit: int
    remaining: int
    window_seconds: float
    retry_after: float = 0.0
    utilization_percent: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "allowed": self.allowed,
            "current_count": self.current_count,
            "limit": self.limit,
            "remaining": self.remaining,
            "window_seconds": self.window_seconds,
            "retry_after": round(self.retry_after, 2),
            "utilization_percent": round(self.utilization_percent, 2),
        }

    def to_headers(self) -> dict[str, str]:
        """Convert to HTTP headers format.

        Returns:
            Dictionary of rate limit headers.
        """
        return {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(self.remaining),
            "X-RateLimit-Reset": str(int(time.time() + self.window_seconds)),
            "X-RateLimit-Window": str(int(self.window_seconds)),
        }


class RateLimiter:
    """Sliding window rate limiter.

    Provides rate limiting for VECTION operations with configurable
    limits per operation type and session. Uses sliding window algorithm
    for smooth rate limiting behavior.

    Thread-safe and suitable for concurrent use.

    Usage:
        limiter = RateLimiter()

        # Simple check
        if limiter.allow(session_id, "reinforce"):
            do_reinforce()

        # With full status
        status = limiter.check(session_id, "reinforce")
        if status.allowed:
            do_reinforce()
        else:
            return error_response(retry_after=status.retry_after)
    """

    def __init__(self, config: RateLimitConfig | None = None) -> None:
        """Initialize the rate limiter.

        Args:
            config: Rate limit configuration.
        """
        self.config = config or RateLimitConfig()
        self._lock = threading.Lock()

        # Per-session, per-operation tracking
        # Structure: {session_id: {operation: RateLimitEntry}}
        self._entries: dict[str, dict[str, RateLimitEntry]] = defaultdict(dict)

        # Global tracking (across all sessions)
        self._global_entries: dict[str, RateLimitEntry] = {}

        # Statistics
        self._total_requests = 0
        self._total_blocked = 0
        self._last_cleanup = time.time()

        # Audit logger (lazy loaded)
        self._audit_logger: Any = None

    def allow(
        self,
        session_id: str,
        operation: str = "default",
        consume: bool = True,
    ) -> bool:
        """Check if a request is allowed and optionally consume quota.

        Args:
            session_id: Session identifier.
            operation: Operation type.
            consume: Whether to consume quota if allowed.

        Returns:
            True if request is allowed, False if rate limited.
        """
        status = self.check(session_id, operation, consume)
        return status.allowed

    def check(
        self,
        session_id: str,
        operation: str = "default",
        consume: bool = True,
    ) -> RateLimitStatus:
        """Check rate limit status with full details.

        Args:
            session_id: Session identifier.
            operation: Operation type.
            consume: Whether to consume quota if allowed.

        Returns:
            RateLimitStatus with full details.
        """
        with self._lock:
            self._maybe_cleanup()
            self._total_requests += 1

            # Get limits for this operation
            limit = self.config.operation_limits.get(operation, self.config.default_limit)
            window = self.config.operation_windows.get(operation, self.config.default_window_seconds)

            # Get or create entry
            if operation not in self._entries[session_id]:
                self._entries[session_id][operation] = RateLimitEntry()

            entry = self._entries[session_id][operation]

            # Get current count
            current_count = entry.get_count(window)

            # Check if allowed
            allowed = current_count < limit

            # Calculate retry_after if blocked
            retry_after = 0.0
            if not allowed:
                oldest = entry.get_oldest_timestamp()
                if oldest:
                    retry_after = max(0, (oldest + window) - time.time())

            # Calculate remaining
            remaining = max(0, limit - current_count - (1 if allowed and consume else 0))

            # Calculate utilization
            utilization = (current_count / limit * 100) if limit > 0 else 0

            # Consume quota if allowed and requested
            if allowed and consume:
                entry.add_request()
                current_count += 1

            # Check global limit if configured
            if allowed and self.config.global_limit is not None:
                global_status = self._check_global(session_id, operation, consume)
                if not global_status.allowed:
                    allowed = False
                    retry_after = global_status.retry_after

            # Log the event
            if self.config.enable_logging:
                self._log_rate_limit_event(
                    session_id=session_id,
                    operation=operation,
                    allowed=allowed,
                    current_count=current_count,
                    limit=limit,
                    window=window,
                )

            # Update stats
            if not allowed:
                self._total_blocked += 1

            return RateLimitStatus(
                allowed=allowed,
                current_count=current_count,
                limit=limit,
                remaining=remaining,
                window_seconds=window,
                retry_after=retry_after,
                utilization_percent=utilization,
            )

    def _check_global(
        self,
        session_id: str,
        operation: str,
        consume: bool,
    ) -> RateLimitStatus:
        """Check global rate limit.

        Args:
            session_id: Session identifier.
            operation: Operation type.
            consume: Whether to consume quota.

        Returns:
            RateLimitStatus for global limit.
        """
        if self.config.global_limit is None:
            return RateLimitStatus(
                allowed=True,
                current_count=0,
                limit=0,
                remaining=0,
                window_seconds=0,
            )

        key = f"global:{operation}"
        if key not in self._global_entries:
            self._global_entries[key] = RateLimitEntry()

        entry = self._global_entries[key]
        window = self.config.global_window_seconds
        limit = self.config.global_limit

        current_count = entry.get_count(window)
        allowed = current_count < limit

        retry_after = 0.0
        if not allowed:
            oldest = entry.get_oldest_timestamp()
            if oldest:
                retry_after = max(0, (oldest + window) - time.time())

        if allowed and consume:
            entry.add_request()
            current_count += 1

        remaining = max(0, limit - current_count)

        return RateLimitStatus(
            allowed=allowed,
            current_count=current_count,
            limit=limit,
            remaining=remaining,
            window_seconds=window,
            retry_after=retry_after,
            utilization_percent=(current_count / limit * 100) if limit > 0 else 0,
        )

    def require(
        self,
        session_id: str,
        operation: str = "default",
    ) -> RateLimitStatus:
        """Check rate limit and raise exception if exceeded.

        Args:
            session_id: Session identifier.
            operation: Operation type.

        Returns:
            RateLimitStatus if allowed.

        Raises:
            RateLimitExceeded: If rate limit is exceeded.
        """
        status = self.check(session_id, operation)
        if not status.allowed:
            raise RateLimitExceeded(
                message=f"Rate limit exceeded for operation '{operation}'",
                operation=operation,
                session_id=session_id,
                current_count=status.current_count,
                limit=status.limit,
                window_seconds=status.window_seconds,
                retry_after=status.retry_after,
            )
        return status

    def rate_limited(
        self,
        operation: str = "default",
        session_id_param: str = "session_id",
    ) -> Callable[[F], F]:
        """Decorator to rate limit a function.

        Args:
            operation: Operation type for rate limiting.
            session_id_param: Name of the session_id parameter.

        Returns:
            Decorator function.

        Usage:
            @limiter.rate_limited(operation="signal_create")
            async def create_signal(session_id: str, data: dict):
                ...
        """

        def decorator(func: F) -> F:
            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                # Extract session_id from kwargs or args
                session_id = kwargs.get(session_id_param)
                if session_id is None and args:
                    # Try to get from first positional arg
                    session_id = str(args[0])

                if session_id is None:
                    session_id = "unknown"

                self.require(session_id, operation)
                return func(*args, **kwargs)

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                session_id = kwargs.get(session_id_param)
                if session_id is None and args:
                    session_id = str(args[0])

                if session_id is None:
                    session_id = "unknown"

                self.require(session_id, operation)
                return await func(*args, **kwargs)

            # Return appropriate wrapper based on function type
            import asyncio

            if asyncio.iscoroutinefunction(func):
                return async_wrapper  # type: ignore
            return wrapper  # type: ignore

        return decorator

    def reset(self, session_id: str, operation: str | None = None) -> None:
        """Reset rate limit for a session.

        Args:
            session_id: Session identifier.
            operation: Specific operation to reset (None for all).
        """
        with self._lock:
            if session_id in self._entries:
                if operation is None:
                    del self._entries[session_id]
                elif operation in self._entries[session_id]:
                    del self._entries[session_id][operation]

    def reset_all(self) -> None:
        """Reset all rate limits."""
        with self._lock:
            self._entries.clear()
            self._global_entries.clear()

    def get_session_status(self, session_id: str) -> dict[str, RateLimitStatus]:
        """Get rate limit status for all operations in a session.

        Args:
            session_id: Session identifier.

        Returns:
            Dictionary mapping operation to status.
        """
        with self._lock:
            result: dict[str, RateLimitStatus] = {}

            if session_id in self._entries:
                for operation in self._entries[session_id]:
                    # Check without consuming
                    result[operation] = self.check(session_id, operation, consume=False)

            return result

    def get_stats(self) -> dict[str, Any]:
        """Get rate limiter statistics.

        Returns:
            Dictionary with statistics.
        """
        with self._lock:
            total_sessions = len(self._entries)
            total_operations = sum(len(ops) for ops in self._entries.values())

            return {
                "total_requests": self._total_requests,
                "total_blocked": self._total_blocked,
                "block_rate_percent": (
                    round((self._total_blocked / self._total_requests) * 100, 2) if self._total_requests > 0 else 0
                ),
                "active_sessions": total_sessions,
                "active_operations": total_operations,
                "config": {
                    "default_limit": self.config.default_limit,
                    "default_window_seconds": self.config.default_window_seconds,
                    "global_limit": self.config.global_limit,
                },
            }

    def _maybe_cleanup(self) -> None:
        """Cleanup stale entries if interval has passed."""
        now = time.time()
        if now - self._last_cleanup < self.config.cleanup_interval_seconds:
            return

        self._last_cleanup = now
        max_window = max(
            self.config.default_window_seconds,
            self.config.global_window_seconds,
            *self.config.operation_windows.values(),
        )

        # Cleanup session entries
        for session_id in list(self._entries.keys()):
            for operation in list(self._entries[session_id].keys()):
                entry = self._entries[session_id][operation]
                entry.cleanup_old(max_window)
                if not entry.timestamps:
                    del self._entries[session_id][operation]

            if not self._entries[session_id]:
                del self._entries[session_id]

        # Cleanup global entries
        for key in list(self._global_entries.keys()):
            entry = self._global_entries[key]
            entry.cleanup_old(self.config.global_window_seconds)
            if not entry.timestamps:
                del self._global_entries[key]

    def _log_rate_limit_event(
        self,
        session_id: str,
        operation: str,
        allowed: bool,
        current_count: int,
        limit: int,
        window: float,
    ) -> None:
        """Log rate limit event to audit logger."""
        try:
            if self._audit_logger is None:
                from vection.security.audit_logger import get_audit_logger

                self._audit_logger = get_audit_logger()

            from vection.security.audit_logger import SecurityEventType

            event_type = SecurityEventType.RATE_LIMIT_CHECKED if allowed else SecurityEventType.RATE_LIMIT_EXCEEDED

            self._audit_logger.log_rate_limit_event(
                event_type=event_type,
                session_id=session_id,
                operation=operation,
                current_count=current_count,
                limit=limit,
                window_seconds=window,
            )
        except Exception:
            # Don't let logging failures break rate limiting
            pass


# Module-level singleton
_rate_limiter: RateLimiter | None = None


def get_rate_limiter(config: RateLimitConfig | None = None) -> RateLimiter:
    """Get the global rate limiter instance.

    Args:
        config: Configuration (only used on first call).

    Returns:
        RateLimiter singleton.
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(config)
    return _rate_limiter
