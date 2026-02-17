from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MovementMonitor:
    """Monitors WebSocket and API movements for accountability."""

    def __init__(self, retention_hours: int = 96):
        self.retention_hours = retention_hours
        self.api_movements: dict[str, list[dict]] = defaultdict(list)
        self.websocket_connections: dict[str, dict] = {}
        self.cleanup_interval = 3600  # 1 hour in seconds
        self._cleanup_task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_old_entries())

    async def stop(self) -> None:
        """Stop the cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

    async def _cleanup_old_entries(self) -> None:
        """Periodically clean up old entries."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                self.cleanup_old_data()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")

    def cleanup_old_data(self) -> None:
        """Remove data older than the retention period."""
        cutoff = datetime.utcnow() - timedelta(hours=self.retention_hours)

        # Clean API movements
        for endpoint in list(self.api_movements.keys()):
            self.api_movements[endpoint] = [m for m in self.api_movements[endpoint] if m["timestamp"] >= cutoff]
            if not self.api_movements[endpoint]:
                del self.api_movements[endpoint]

        # Clean WebSocket connections
        disconnected = []
        for conn_id, conn in self.websocket_connections.items():
            if conn.get("last_activity", datetime.min) < cutoff:
                disconnected.append(conn_id)

        for conn_id in disconnected:
            self.websocket_connections.pop(conn_id, None)

        logger.info(f"Cleaned up {len(disconnected)} old WebSocket connections")

    def record_api_movement(
        self,
        path: str,
        method: str,
        status_code: int,
        client_ip: str,
        user_id: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Record an API request/response."""
        movement = {
            "timestamp": datetime.utcnow(),
            "path": path,
            "method": method.upper(),
            "status_code": status_code,
            "client_ip": client_ip,
            "user_id": user_id,
            "metadata": metadata or {},
        }

        self.api_movements[path].append(movement)

    def record_websocket_connection(
        self,
        connection_id: str,
        path: str,
        client_ip: str,
        user_id: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Record a new WebSocket connection."""
        self.websocket_connections[connection_id] = {
            "connection_id": connection_id,
            "path": path,
            "client_ip": client_ip,
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "metadata": metadata or {},
            "message_count": 0,
            "last_message": None,
        }

    def record_websocket_message(
        self,
        connection_id: str,
        message_type: str,
        message_size: int,
        direction: str = "inbound",
        metadata: dict | None = None,
    ) -> None:
        """Record a WebSocket message."""
        if connection_id not in self.websocket_connections:
            return

        conn = self.websocket_connections[connection_id]
        conn["last_activity"] = datetime.utcnow()
        conn["message_count"] += 1
        conn["last_message"] = {
            "timestamp": datetime.utcnow(),
            "type": message_type,
            "size": message_size,
            "direction": direction,
        }

        # Update metadata if provided
        if metadata:
            conn["metadata"].update(metadata)

    def record_websocket_disconnection(
        self,
        connection_id: str,
        reason: str = "normal",
        error: str | None = None,
    ) -> None:
        """Record a WebSocket disconnection."""
        if connection_id not in self.websocket_connections:
            return

        conn = self.websocket_connections[connection_id]
        conn["disconnected_at"] = datetime.utcnow()
        conn["disconnect_reason"] = reason
        conn["disconnect_error"] = error

        # Move to historical data (in a real implementation)
        # self._archive_connection(conn)

        # Remove from active connections
        self.websocket_connections.pop(connection_id, None)

    def get_connection_stats(self) -> dict:
        """Get statistics about WebSocket connections."""
        now = datetime.utcnow()
        active_connections = len(self.websocket_connections)

        # Calculate connection durations
        durations = [(now - conn["connected_at"]).total_seconds() for conn in self.websocket_connections.values()]

        return {
            "active_connections": active_connections,
            "total_messages": sum(conn["message_count"] for conn in self.websocket_connections.values()),
            "avg_connection_duration_sec": (sum(durations) / len(durations) if durations else 0),
            "max_connection_duration_sec": max(durations) if durations else 0,
            "messages_per_minute": self._calculate_messages_per_minute(),
        }

    def _calculate_messages_per_minute(self) -> float:
        """Calculate messages per minute over the last hour."""
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)

        # Count messages in the last hour
        recent_messages = 0
        for conn in self.websocket_connections.values():
            if conn.get("last_activity", datetime.min) >= one_hour_ago:
                recent_messages += conn["message_count"]

        # Convert to messages per minute
        return recent_messages / 60 if recent_messages > 0 else 0.0

    def detect_anomalies(self) -> list[dict]:
        """Detect anomalous behavior in API and WebSocket traffic."""
        anomalies = []

        # 1. Check for unusual API patterns
        for endpoint, movements in self.api_movements.items():
            # Check for error rate spikes
            total_requests = len(movements)
            if total_requests == 0:
                continue

            error_requests = sum(1 for m in movements if m["status_code"] >= 400)
            error_rate = error_requests / total_requests

            if error_rate > 0.1:  # 10% error rate threshold
                anomalies.append(
                    {
                        "type": "high_error_rate",
                        "endpoint": endpoint,
                        "error_rate": error_rate,
                        "severity": "high",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

        # 2. Check for unusual WebSocket behavior
        for conn_id, conn in self.websocket_connections.items():
            # Check for high message rates
            if conn["message_count"] > 1000:  # Arbitrary threshold
                anomalies.append(
                    {
                        "type": "high_websocket_activity",
                        "connection_id": conn_id,
                        "message_count": conn["message_count"],
                        "severity": "medium",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

            # Check for long-running connections
            duration_hours = (datetime.utcnow() - conn["connected_at"]).total_seconds() / 3600
            if duration_hours > 24:  # 24-hour threshold
                anomalies.append(
                    {
                        "type": "long_running_connection",
                        "connection_id": conn_id,
                        "duration_hours": duration_hours,
                        "severity": "low",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

        return anomalies


# Singleton instance
movement_monitor = MovementMonitor()
