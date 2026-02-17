"""Emergency real-time processing for rare occasions."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any


class RealtimeFlow(StrEnum):
    """Types of real-time flows."""

    EMERGENCY = "emergency"  # Critical emergency processing
    ALERT = "alert"  # Alert processing
    CRITICAL_UPDATE = "critical_update"  # Critical state update
    SYSTEM_FAILURE = "system_failure"  # System failure response


class EmergencyRealtimeProcessor:
    """Processes emergency real-time I/O flows for rare occasions only."""

    def __init__(self) -> None:
        """Initialize emergency real-time processor."""
        self._handlers: dict[RealtimeFlow, Callable[[dict[str, Any]], Any]] = {}
        self._throttle_limit = 10  # Max real-time operations per minute
        self._throttle_window: list[datetime] = []
        self._stats: dict[str, Any] = {
            "total_processed": 0,
            "throttled": 0,
            "by_type": {},
        }

    def register_handler(self, flow_type: RealtimeFlow, handler: Callable[[dict[str, Any]], Any]) -> None:
        """Register a handler for a flow type.

        Args:
            flow_type: Flow type
            handler: Handler function
        """
        self._handlers[flow_type] = handler

    def process(
        self,
        flow_type: RealtimeFlow,
        data: dict[str, Any],
        force: bool = False,
    ) -> dict[str, Any]:
        """Process an emergency real-time flow.

        Args:
            flow_type: Type of real-time flow
            data: Data to process
            force: Force processing even if throttled

        Returns:
            Processing result

        Raises:
            ValueError: If throttled and not forced
        """
        # Check throttle
        if not force and not self._check_throttle():
            self._stats["throttled"] += 1
            raise ValueError("Real-time processing throttled. Use periodic processing instead.")

        # Get handler
        handler = self._handlers.get(flow_type)
        if not handler:
            raise ValueError(f"No handler registered for flow type: {flow_type}")

        # Process
        start_time = datetime.now(UTC)
        try:
            result = handler(data)
            duration = (datetime.now(UTC) - start_time).total_seconds()

            # Update stats
            self._stats["total_processed"] += 1
            self._stats["by_type"][flow_type.value] = self._stats["by_type"].get(flow_type.value, 0) + 1
            self._throttle_window.append(start_time)

            # Clean old throttle entries
            cutoff = datetime.now(UTC).replace(second=0, microsecond=0) - timedelta(minutes=1)
            self._throttle_window = [t for t in self._throttle_window if t > cutoff]

            return {
                "success": True,
                "flow_type": flow_type.value,
                "duration_seconds": duration,
                "result": result,
            }
        except Exception as e:
            return {
                "success": False,
                "flow_type": flow_type.value,
                "error": str(e),
            }

    def _check_throttle(self) -> bool:
        """Check if real-time processing is allowed (not throttled).

        Returns:
            True if allowed, False if throttled
        """
        # Count recent operations
        recent_count = len(self._throttle_window)
        return recent_count < self._throttle_limit

    def get_stats(self) -> dict[str, Any]:
        """Get processing statistics.

        Returns:
            Statistics dictionary
        """
        return {
            **self._stats,
            "throttle_limit": self._throttle_limit,
            "current_throttle_count": len(self._throttle_window),
        }

    def set_throttle_limit(self, limit: int) -> None:
        """Set throttle limit.

        Args:
            limit: Maximum real-time operations per minute
        """
        self._throttle_limit = limit
