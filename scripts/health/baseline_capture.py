#!/usr/bin/env python3
"""Capture 24h baseline metrics snapshots for parasitic leak remediation."""

import asyncio
import datetime as dt
import json
import time
import urllib.request
from pathlib import Path

METRICS_URL = "http://localhost:8000/metrics"
OUT_FILE = Path("artifacts/baseline_metrics.jsonl")


def fetch_metrics() -> str:
    """Fetch metrics from the metrics endpoint."""
    with urllib.request.urlopen(METRICS_URL) as resp:
        return resp.read().decode("utf-8")


def extract(metrics_text: str) -> dict[str, float]:
    """Extract key metrics from Prometheus text format."""
    out: dict[str, float] = {}
    for line in metrics_text.splitlines():
        if line.startswith("eventbus_active_subscriptions"):
            out["eventbus_active_subscriptions"] = float(line.split()[-1])
        if line.startswith("db_active_connections"):
            out["db_active_connections"] = float(line.split()[-1])
    return out


def main() -> None:
    """Capture baseline metrics for 24 hours."""
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    print(f"Starting baseline capture to {OUT_FILE}")
    print(f"Metrics URL: {METRICS_URL}")
    print("Capturing every 5 minutes for 24 hours...")

    for i in range(24 * 12):  # 24h at 5m intervals
        try:
            metrics_text = fetch_metrics()
            snapshot = {
                "timestamp": dt.datetime.utcnow().isoformat(),
                "snapshot_number": i + 1,
                **extract(metrics_text),
            }

            with open(OUT_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(snapshot) + "\n")

            elapsed = (i + 1) * 5
            print(f"[{elapsed:3d}m] Snapshot {i + 1}/288 captured")

        except Exception as e:
            print(f"Error capturing snapshot {i + 1}: {e}")

        time.sleep(300)  # 5 minutes

    print(f"\nBaseline capture complete. Output: {OUT_FILE}")


if __name__ == "__main__":
    main()
