#!/usr/bin/env python3
"""
Load test script for Resonance API.

This script runs a configurable load test against the Resonance API
and reports latency metrics (p50, p95, p99).

Usage:
    # Run with defaults (100 requests, 10 concurrent)
    python tests/performance/test_resonance_load.py

    # Run with custom settings
    python tests/performance/test_resonance_load.py --requests 500 --concurrency 20 --base-url http://localhost:8080

Requirements:
    - httpx (included in project dependencies)
    - Running Mothership server

Output:
    Prints latency statistics and saves results to benchmark_metrics.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    import httpx
except ImportError:
    print("httpx is required. Install with: pip install httpx")
    sys.exit(1)


@dataclass
class RequestResult:
    """Result of a single request."""

    success: bool
    status_code: int
    latency_ms: float
    error: str | None = None


@dataclass
class LoadTestResult:
    """Aggregated load test results."""

    total_requests: int
    successful_requests: int
    failed_requests: int
    total_duration_s: float
    requests_per_second: float
    latencies_ms: list[float] = field(default_factory=list)

    @property
    def p50_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        sorted_latencies = sorted(self.latencies_ms)
        idx = int(len(sorted_latencies) * 0.50)
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)]

    @property
    def p95_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        sorted_latencies = sorted(self.latencies_ms)
        idx = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)]

    @property
    def p99_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        sorted_latencies = sorted(self.latencies_ms)
        idx = int(len(sorted_latencies) * 0.99)
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)]

    @property
    def avg_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        return statistics.mean(self.latencies_ms)

    @property
    def min_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        return min(self.latencies_ms)

    @property
    def max_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        return max(self.latencies_ms)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.successful_requests / self.total_requests if self.total_requests > 0 else 0,
            "total_duration_s": round(self.total_duration_s, 3),
            "requests_per_second": round(self.requests_per_second, 2),
            "latency": {
                "min_ms": round(self.min_ms, 2),
                "avg_ms": round(self.avg_ms, 2),
                "p50_ms": round(self.p50_ms, 2),
                "p95_ms": round(self.p95_ms, 2),
                "p99_ms": round(self.p99_ms, 2),
                "max_ms": round(self.max_ms, 2),
            },
        }


async def make_request(
    client: httpx.AsyncClient,
    url: str,
    payload: dict[str, Any],
) -> RequestResult:
    """Make a single request and measure latency."""
    start = time.perf_counter()
    try:
        response = await client.post(url, json=payload)
        latency_ms = (time.perf_counter() - start) * 1000
        return RequestResult(
            success=response.status_code == 200,
            status_code=response.status_code,
            latency_ms=latency_ms,
            error=None if response.status_code == 200 else response.text[:200],
        )
    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000
        return RequestResult(
            success=False,
            status_code=0,
            latency_ms=latency_ms,
            error=str(e),
        )


async def run_load_test(
    base_url: str,
    total_requests: int,
    concurrency: int,
    endpoint: str = "/api/v1/resonance/definitive",
) -> LoadTestResult:
    """Run the load test with specified parameters."""
    url = f"{base_url.rstrip('/')}{endpoint}"
    payload = {
        "query": "Load test query - where do these features connect?",
        "activity_type": "general",
        "progress": 0.65,
        "target_schema": "context_engineering",
        "use_rag": False,
        "use_llm": False,
        "max_chars": 200,
    }

    results: list[RequestResult] = []
    semaphore = asyncio.Semaphore(concurrency)

    async def bounded_request(client: httpx.AsyncClient) -> RequestResult:
        async with semaphore:
            return await make_request(client, url, payload)

    print(f"Starting load test: {total_requests} requests, {concurrency} concurrent")
    print(f"Target: {url}")
    print("-" * 60)

    start_time = time.perf_counter()

    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [bounded_request(client) for _ in range(total_requests)]
        results = await asyncio.gather(*tasks)

    end_time = time.perf_counter()
    total_duration = end_time - start_time

    # Aggregate results
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    result = LoadTestResult(
        total_requests=total_requests,
        successful_requests=len(successful),
        failed_requests=len(failed),
        total_duration_s=total_duration,
        requests_per_second=total_requests / total_duration if total_duration > 0 else 0,
        latencies_ms=[r.latency_ms for r in successful],
    )

    return result


def print_results(result: LoadTestResult) -> None:
    """Print formatted results."""
    print("\n" + "=" * 60)
    print("LOAD TEST RESULTS")
    print("=" * 60)
    print(f"Total Requests:     {result.total_requests}")
    print(f"Successful:         {result.successful_requests}")
    print(f"Failed:             {result.failed_requests}")
    print(f"Success Rate:       {result.successful_requests / result.total_requests * 100:.1f}%")
    print(f"Total Duration:     {result.total_duration_s:.2f}s")
    print(f"Requests/second:    {result.requests_per_second:.1f}")
    print("-" * 60)
    print("LATENCY (successful requests)")
    print("-" * 60)
    print(f"  Min:              {result.min_ms:.2f}ms")
    print(f"  Avg:              {result.avg_ms:.2f}ms")
    print(f"  p50 (median):     {result.p50_ms:.2f}ms")
    print(f"  p95:              {result.p95_ms:.2f}ms")
    print(f"  p99:              {result.p99_ms:.2f}ms")
    print(f"  Max:              {result.max_ms:.2f}ms")
    print("=" * 60)


def save_results(result: LoadTestResult, output_path: str) -> None:
    """Save results to JSON file."""
    data = {
        "timestamp": datetime.now(UTC).isoformat(),
        "test_type": "resonance_api_load_test",
        "api_version": "1.0.0",
        "results": result.to_dict(),
    }

    path = Path(output_path)
    path.write_text(json.dumps(data, indent=2))
    print(f"\nResults saved to: {path}")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Resonance API Load Test")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8080",
        help="Base URL of the API server",
    )
    parser.add_argument(
        "--requests",
        "-n",
        type=int,
        default=100,
        help="Total number of requests to make",
    )
    parser.add_argument(
        "--concurrency",
        "-c",
        type=int,
        default=10,
        help="Number of concurrent requests",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="benchmark_metrics.json",
        help="Output file for results",
    )
    parser.add_argument(
        "--endpoint",
        default="/api/v1/resonance/definitive",
        help="API endpoint to test",
    )

    args = parser.parse_args()

    try:
        result = await run_load_test(
            base_url=args.base_url,
            total_requests=args.requests,
            concurrency=args.concurrency,
            endpoint=args.endpoint,
        )

        print_results(result)
        save_results(result, args.output)

        # Exit with error if success rate is below threshold
        if result.successful_requests / result.total_requests < 0.95:
            print("\nWARNING: Success rate below 95% threshold")
            sys.exit(1)

    except httpx.ConnectError:
        print(f"\nERROR: Could not connect to {args.base_url}")
        print("Make sure the Mothership server is running:")
        print("  .\\venv\\Scripts\\python.exe -m application.mothership.main")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
