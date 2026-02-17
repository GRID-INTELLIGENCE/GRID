"""
Monitoring Manager - Stub Implementation
"""


class MonitoringManager:
    """Stub monitoring manager."""

    def __init__(self) -> None:
        pass

    async def collect_metrics(self) -> None:
        """Collect system metrics."""
        pass

    async def cleanup(self) -> None:
        """Cleanup resources."""
        pass

    def record_request(self, request_type: str, duration: float) -> None:
        """Record a request metric."""
        pass

    def record_error(self, error_type: str) -> None:
        """Record an error metric."""
        pass
