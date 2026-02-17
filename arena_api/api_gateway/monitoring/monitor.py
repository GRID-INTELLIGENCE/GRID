"""
Monitoring Manager - Stub Implementation
"""


class MonitoringManager:
    """Stub monitoring manager."""

    def __init__(self):
        pass

    async def collect_metrics(self):
        """Collect system metrics."""
        pass

    async def cleanup(self):
        """Cleanup resources."""
        pass

    def record_request(self, request_type: str, duration: float):
        """Record a request metric."""
        pass

    def record_error(self, error_type: str):
        """Record an error metric."""
        pass
