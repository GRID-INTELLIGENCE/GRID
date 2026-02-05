#!/usr/bin/env python3
"""Continuous health monitoring for parasitic leak remediation."""

import asyncio
import time
from pathlib import Path
from typing import Any

import requests

# Add src to path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

METRICS_URL = "http://localhost:8000/metrics"
HEALTH_URL = "http://localhost:8000/health/parasitic-leaks"
CHECK_INTERVAL = 60  # Check every 60 seconds


def fetch_metrics() -> dict[str, float]:
    """Fetch metrics from Prometheus endpoint."""
    try:
        response = requests.get(METRICS_URL, timeout=5)
        response.raise_for_status()

        metrics = {}
        for line in response.text.splitlines():
            if line.startswith("eventbus_active_subscriptions"):
                metrics["eventbus_active"] = float(line.split()[-1])
            if line.startswith("db_active_connections"):
                metrics["db_active"] = float(line.split()[-1])

        return metrics
    except Exception as e:
        print(f"Error fetching metrics: {e}")
        return {}


def fetch_health() -> dict[str, Any]:
    """Fetch health status."""
    try:
        response = requests.get(HEALTH_URL, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching health: {e}")
        return {}


def check_thresholds(metrics: dict[str, float]) -> list[str]:
    """Check if metrics exceed thresholds."""
    alerts = []

    if metrics.get("eventbus_active", 0) > 1000:
        alerts.append(f"High EventBus subscriptions: {metrics['eventbus_active']}")

    if metrics.get("db_active", 0) > 50:
        alerts.append(f"High DB connections: {metrics['db_active']}")

    return alerts


async def monitor_loop() -> None:
    """Main monitoring loop."""
    print("=== Parasitic Leak Health Monitor ===")
    print(f"Monitoring {METRICS_URL}")
    print(f"Checking every {CHECK_INTERVAL} seconds\n")

    while True:
        try:
            # Fetch metrics
            metrics = fetch_metrics()
            health = fetch_health()

            # Check thresholds
            alerts = check_thresholds(metrics)

            # Print status
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            status = "✓" if health.get("status") == "healthy" else "✗"

            print(f"[{timestamp}] {status} EventBus: {metrics.get('eventbus_active', 0):.0f} | DB: {metrics.get('db_active', 0):.0f}")

            # Print alerts
            for alert in alerts:
                print(f"  ⚠️  {alert}")

            # Print health status
            if health.get("components"):
                for component, status in health["components"].items():
                    if not status.get("healthy", True):
                        print(f"  ✗ {component}: {status.get('error', 'unhealthy')}")

        except Exception as e:
            print(f"Error in monitoring loop: {e}")

        await asyncio.sleep(CHECK_INTERVAL)


async def main() -> None:
    """Run health monitor."""
    try:
        await monitor_loop()
    except KeyboardInterrupt:
        print("\nMonitor stopped")


if __name__ == "__main__":
    asyncio.run(main())
