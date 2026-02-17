"""
Monitoring and Logging Infrastructure for Arena API Gateway
==========================================================

This module implements comprehensive monitoring, logging, and observability
for the dynamic API system, providing insights into performance, health,
and security of the transformed architecture.

Key Features:
- Real-time metrics collection
- Structured logging with correlation IDs
- Performance monitoring and alerting
- Security event tracking
- Health dashboard integration
- Anomaly detection
"""

import asyncio
import logging
import os
import statistics
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, StrEnum
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


class MetricType(StrEnum):
    """Types of metrics that can be tracked."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class MetricData:
    """Container for metric data."""

    name: str
    value: float
    timestamp: datetime
    tags: dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE


@dataclass
class RequestMetrics:
    """Metrics for API requests."""

    method: str
    path: str
    status_code: int
    response_time: float
    user_id: str | None = None
    service_name: str | None = None
    client_ip: str | None = None
    user_agent: str | None = None


class MonitoringManager:
    """
    Comprehensive monitoring and logging system for the Arena API Gateway.
    """

    def __init__(self):
        self.metrics_buffer: deque = deque(maxlen=10000)
        self.log_buffer: deque = deque(maxlen=5000)
        self.alerts_buffer: deque = deque(maxlen=1000)

        # Metrics storage
        self.counters = defaultdict(int)
        self.gauges = {}
        self.histograms = defaultdict(list)
        self.timers = defaultdict(list)

        # Alert thresholds
        self.alert_thresholds = self._load_alert_thresholds()

        # Background tasks
        self._running = False
        self._tasks = []

        # External integrations
        self.dashboard_url = os.getenv("ARENA_DASHBOARD_URL")
        self.metrics_endpoint = os.getenv("ARENA_METRICS_ENDPOINT")

    def _load_alert_thresholds(self) -> dict[str, Any]:
        """Load alert threshold configurations."""
        return {
            "response_time_p95": 2.0,  # seconds
            "error_rate": 0.05,  # 5%
            "rate_limit_violations": 10,  # per minute
            "service_unhealthy_count": 2,  # services
            "memory_usage": 0.8,  # 80%
            "cpu_usage": 0.9,  # 90%
        }

    async def start(self):
        """Start monitoring system."""
        if self._running:
            return

        self._running = True
        logger.info("Starting monitoring system")

        # Start background tasks
        self._tasks = [
            asyncio.create_task(self._metrics_collector()),
            asyncio.create_task(self._log_processor()),
            asyncio.create_task(self._alert_monitor()),
            asyncio.create_task(self._metrics_exporter()),
        ]

    async def stop(self):
        """Stop monitoring system."""
        self._running = False

        # Cancel tasks
        for task in self._tasks:
            task.cancel()

        await asyncio.gather(*self._tasks, return_exceptions=True)
        logger.info("Monitoring system stopped")

    async def record_request(self, request, response, processing_time: float, authenticated: bool = False):
        """
        Record metrics for an API request.

        Args:
            request: FastAPI Request object
            response: Response data or object
            processing_time: Time taken to process request
            authenticated: Whether request was authenticated
        """
        try:
            # Extract request information
            method = request.method
            path = request.url.path
            status_code = response.status_code if hasattr(response, "status_code") else 200
            user_id = getattr(request.state, "user_id", None) if hasattr(request, "state") else None
            client_ip = getattr(request.client, "host", None) if request.client else None
            user_agent = request.headers.get("User-Agent")

            # Create request metrics
            metrics = RequestMetrics(
                method=method,
                path=path,
                status_code=status_code,
                response_time=processing_time,
                user_id=user_id,
                client_ip=client_ip,
                user_agent=user_agent,
            )

            # Add to metrics buffer
            self.metrics_buffer.append(metrics)

            # Update counters
            self.counters["requests_total"] += 1
            self.counters[f"requests_method_{method.lower()}"] += 1
            self.counters[f"requests_status_{status_code}"] += 1

            if authenticated:
                self.counters["requests_authenticated"] += 1

            # Update response time histogram
            self.histograms["response_time"].append(processing_time)

            # Update gauges
            self.gauges["active_requests"] = self.gauges.get("active_requests", 0) + 1

            # Log request (structured)
            await self._log_request(metrics)

            # Check for alerts
            await self._check_request_alerts(metrics)

        except Exception as e:
            logger.error(f"Error recording request metrics: {str(e)}")

    async def record_error(self, request, error: str, processing_time: float):
        """
        Record error metrics.

        Args:
            request: FastAPI Request object
            error: Error description
            processing_time: Time taken before error
        """
        try:
            self.counters["errors_total"] += 1

            # Log error
            error_log = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "ERROR",
                "type": "request_error",
                "method": request.method,
                "path": request.url.path,
                "error": error,
                "processing_time": processing_time,
                "client_ip": getattr(request.client, "host", None) if request.client else None,
            }

            self.log_buffer.append(error_log)

            # Check error rate alerts
            await self._check_error_alerts()

        except Exception as e:
            logger.error(f"Error recording error metrics: {str(e)}")

    async def record_rate_limit_violation(self, request, limit_type: str, current_usage: int, limit: int):
        """
        Record rate limit violation.

        Args:
            request: FastAPI Request object
            limit_type: Type of limit violated
            current_usage: Current usage count
            limit: Limit threshold
        """
        try:
            self.counters["rate_limit_violations"] += 1
            self.counters[f"rate_limit_{limit_type}_violations"] += 1

            # Log violation
            violation_log = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "WARNING",
                "type": "rate_limit_violation",
                "limit_type": limit_type,
                "method": request.method,
                "path": request.url.path,
                "current_usage": current_usage,
                "limit": limit,
                "client_ip": getattr(request.client, "host", None) if request.client else None,
            }

            self.log_buffer.append(violation_log)

            # Check rate limit alerts
            await self._check_rate_limit_alerts()

        except Exception as e:
            logger.error(f"Error recording rate limit violation: {str(e)}")

    async def record_security_event(self, event_type: str, details: dict[str, Any], severity: str = "INFO"):
        """
        Record security-related events.

        Args:
            event_type: Type of security event
            details: Event details
            severity: Event severity
        """
        try:
            self.counters[f"security_events_{event_type}"] += 1

            security_log = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": severity,
                "type": "security_event",
                "event_type": event_type,
                "details": details,
            }

            self.log_buffer.append(security_log)

            # High severity security events trigger alerts
            if severity in ["ERROR", "CRITICAL"]:
                await self._create_alert("security", f"Security event: {event_type}", severity, details)

        except Exception as e:
            logger.error(f"Error recording security event: {str(e)}")

    async def _log_request(self, metrics: RequestMetrics):
        """Log request metrics in structured format."""
        try:
            request_log = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "INFO",
                "type": "request",
                "method": metrics.method,
                "path": metrics.path,
                "status_code": metrics.status_code,
                "response_time": metrics.response_time,
                "user_id": metrics.user_id,
                "client_ip": metrics.client_ip,
                "user_agent": metrics.user_agent,
            }

            self.log_buffer.append(request_log)

        except Exception as e:
            logger.error(f"Error logging request: {str(e)}")

    async def _check_request_alerts(self, metrics: RequestMetrics):
        """Check for request-related alerts."""
        try:
            # Response time alert
            if metrics.response_time > self.alert_thresholds["response_time_p95"]:
                await self._create_alert(
                    "performance",
                    f"High response time: {metrics.response_time:.2f}s",
                    "WARNING",
                    {"method": metrics.method, "path": metrics.path, "response_time": metrics.response_time},
                )

            # Error status alert
            if metrics.status_code >= 500:
                await self._create_alert(
                    "error",
                    f"Server error: {metrics.status_code}",
                    "ERROR",
                    {"method": metrics.method, "path": metrics.path, "status_code": metrics.status_code},
                )

        except Exception as e:
            logger.error(f"Error checking request alerts: {str(e)}")

    async def _check_error_alerts(self):
        """Check error rate alerts."""
        try:
            total_requests = self.counters.get("requests_total", 0)
            total_errors = self.counters.get("errors_total", 0)

            if total_requests > 100:  # Only check after sufficient sample
                error_rate = total_errors / total_requests
                if error_rate > self.alert_thresholds["error_rate"]:
                    await self._create_alert(
                        "error_rate",
                        f"High error rate: {error_rate:.2%}",
                        "ERROR",
                        {"error_rate": error_rate, "total_requests": total_requests, "total_errors": total_errors},
                    )

        except Exception as e:
            logger.error(f"Error checking error alerts: {str(e)}")

    async def _check_rate_limit_alerts(self):
        """Check rate limit violation alerts."""
        try:
            violations = self.counters.get("rate_limit_violations", 0)

            # Check if violations exceed threshold in last minute
            if violations > self.alert_thresholds["rate_limit_violations"]:
                await self._create_alert(
                    "rate_limit", f"High rate limit violations: {violations}", "WARNING", {"violations": violations}
                )

        except Exception as e:
            logger.error(f"Error checking rate limit alerts: {str(e)}")

    async def _create_alert(self, alert_type: str, message: str, severity: str, details: dict[str, Any]):
        """Create an alert."""
        try:
            alert = {
                "id": f"{alert_type}_{int(time.time())}",
                "type": alert_type,
                "message": message,
                "severity": severity,
                "details": details,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "acknowledged": False,
            }

            self.alerts_buffer.append(alert)

            # Log alert
            logger.warning(f"Alert created: {alert_type} - {message}")

            # Send to external dashboard if configured
            if self.dashboard_url:
                await self._send_alert_to_dashboard(alert)

        except Exception as e:
            logger.error(f"Error creating alert: {str(e)}")

    async def _send_alert_to_dashboard(self, alert: dict[str, Any]):
        """Send alert to external dashboard."""
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(f"{self.dashboard_url}/alerts", json=alert, timeout=aiohttp.ClientTimeout(total=5))
        except Exception as e:
            logger.error(f"Error sending alert to dashboard: {str(e)}")

    async def _metrics_collector(self):
        """Collect and aggregate metrics."""
        while self._running:
            try:
                await asyncio.sleep(60)  # Collect every minute

                # Calculate percentiles for response times
                if self.histograms["response_time"]:
                    response_times = self.histograms["response_time"]
                    p50 = statistics.median(response_times)
                    p95 = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
                    p99 = statistics.quantiles(response_times, n=100)[98]  # 99th percentile

                    self.gauges["response_time_p50"] = p50
                    self.gauges["response_time_p95"] = p95
                    self.gauges["response_time_p99"] = p99

                # Clear old histogram data (keep last 1000 entries)
                if len(self.histograms["response_time"]) > 1000:
                    self.histograms["response_time"] = self.histograms["response_time"][-1000:]

            except Exception as e:
                logger.error(f"Metrics collection error: {str(e)}")
                await asyncio.sleep(30)

    async def _log_processor(self):
        """Process and export logs."""
        while self._running:
            try:
                await asyncio.sleep(30)  # Process every 30 seconds

                if self.log_buffer:
                    # Group logs by level
                    logs_by_level = defaultdict(list)
                    while self.log_buffer:
                        log_entry = self.log_buffer.popleft()
                        logs_by_level[log_entry["level"]].append(log_entry)

                    # Export logs (placeholder - implement actual export)
                    for level, logs in logs_by_level.items():
                        logger.log(getattr(logging, level), f"Processed {len(logs)} {level} logs")

            except Exception as e:
                logger.error(f"Log processing error: {str(e)}")
                await asyncio.sleep(10)

    async def _alert_monitor(self):
        """Monitor and escalate alerts."""
        while self._running:
            try:
                await asyncio.sleep(120)  # Check every 2 minutes

                # Check for unacknowledged critical alerts
                critical_alerts = [
                    alert
                    for alert in self.alerts_buffer
                    if alert["severity"] in ["ERROR", "CRITICAL"] and not alert["acknowledged"]
                ]

                if len(critical_alerts) > 5:
                    logger.critical(f"Multiple critical alerts: {len(critical_alerts)}")
                    # Could trigger escalation procedures here

            except Exception as e:
                logger.error(f"Alert monitoring error: {str(e)}")
                await asyncio.sleep(60)

    async def _metrics_exporter(self):
        """Export metrics to external systems."""
        while self._running:
            try:
                await asyncio.sleep(300)  # Export every 5 minutes

                if self.metrics_endpoint:
                    metrics_data = {
                        "counters": dict(self.counters),
                        "gauges": self.gauges.copy(),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }

                    async with aiohttp.ClientSession() as session:
                        await session.post(
                            self.metrics_endpoint, json=metrics_data, timeout=aiohttp.ClientTimeout(total=10)
                        )

            except Exception as e:
                logger.error(f"Metrics export error: {str(e)}")
                await asyncio.sleep(60)

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get a summary of current metrics."""
        return {
            "counters": dict(self.counters),
            "gauges": self.gauges.copy(),
            "active_alerts": len([a for a in self.alerts_buffer if not a["acknowledged"]]),
            "buffer_sizes": {
                "metrics": len(self.metrics_buffer),
                "logs": len(self.log_buffer),
                "alerts": len(self.alerts_buffer),
            },
        }

    def get_recent_alerts(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent alerts."""
        alerts = list(self.alerts_buffer)
        return alerts[-limit:] if len(alerts) > limit else alerts

    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        for alert in self.alerts_buffer:
            if alert["id"] == alert_id:
                alert["acknowledged"] = True
                return True
        return False
