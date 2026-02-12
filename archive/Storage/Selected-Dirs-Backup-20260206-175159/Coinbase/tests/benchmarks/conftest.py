"""Benchmark fixtures and utilities for performance testing.

This module provides:
- BenchmarkTimer: Context manager for timing operations
- BenchmarkResult: Data class for storing benchmark results
- Fixtures for common benchmark scenarios
"""

import statistics
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime

import pytest


@dataclass
class BenchmarkResult:
    """Stores results from a benchmark run."""

    name: str
    iterations: int
    total_time_ms: float
    min_time_ms: float
    max_time_ms: float
    mean_time_ms: float
    median_time_ms: float
    std_dev_ms: float
    ops_per_second: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        """Convert result to dictionary."""
        return {
            "name": self.name,
            "iterations": self.iterations,
            "total_time_ms": round(self.total_time_ms, 4),
            "min_time_ms": round(self.min_time_ms, 4),
            "max_time_ms": round(self.max_time_ms, 4),
            "mean_time_ms": round(self.mean_time_ms, 4),
            "median_time_ms": round(self.median_time_ms, 4),
            "std_dev_ms": round(self.std_dev_ms, 4),
            "ops_per_second": round(self.ops_per_second, 2),
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    def __str__(self) -> str:  # noqa: override
        return (
            f"{self.name}:\n"
            f"  Iterations: {self.iterations}\n"
            f"  Total Time: {self.total_time_ms:.2f}ms\n"
            f"  Mean: {self.mean_time_ms:.4f}ms\n"
            f"  Median: {self.median_time_ms:.4f}ms\n"
            f"  Min: {self.min_time_ms:.4f}ms\n"
            f"  Max: {self.max_time_ms:.4f}ms\n"
            f"  Std Dev: {self.std_dev_ms:.4f}ms\n"
            f"  Ops/sec: {self.ops_per_second:.2f}"
        )


class BenchmarkTimer:
    """Context manager for timing operations.

    Usage:
        with BenchmarkTimer() as timer:
            # operation to benchmark
            pass
        print(f"Elapsed: {timer.elapsed_ms}ms")
    """

    def __init__(self) -> None:
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.elapsed_ms: float = 0.0

    def __enter__(self) -> "BenchmarkTimer":
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args: object) -> None:
        self.end_time = time.perf_counter()
        self.elapsed_ms = (self.end_time - self.start_time) * 1000


class Benchmark:
    """Utility class for running benchmarks."""

    warmup_iterations: int
    min_iterations: int
    max_iterations: int
    target_time_ms: float

    def __init__(
        self,
        warmup_iterations: int = 3,
        min_iterations: int = 10,
        max_iterations: int = 1000,
        target_time_ms: float = 1000.0,
    ) -> None:
        self.warmup_iterations = warmup_iterations
        self.min_iterations = min_iterations
        self.max_iterations = max_iterations
        self.target_time_ms = target_time_ms
        self.results: list[BenchmarkResult] = []

    def run(
        self,
        name: str,
        func: Callable[[], object],
        iterations: int | None = None,
        setup: Callable[[], None] | None = None,
        teardown: Callable[[], None] | None = None,
        metadata: dict[str, object] | None = None,
    ) -> BenchmarkResult:
        """Run a benchmark for the given function.

        Args:
            name: Name of the benchmark
            func: Function to benchmark (no arguments)
            iterations: Number of iterations (auto-determined if None)
            setup: Optional setup function called before each iteration
            teardown: Optional teardown function called after each iteration
            metadata: Optional metadata to attach to results

        Returns:
            BenchmarkResult with timing statistics
        """
        # Warmup phase
        for _ in range(self.warmup_iterations):
            if setup:
                setup()
            func()
            if teardown:
                teardown()

        # Determine iterations if not specified
        if iterations is None:
            iterations = self._determine_iterations(func, setup, teardown)

        # Run benchmark
        times_ms: list[float] = []
        total_start = time.perf_counter()

        for _ in range(iterations):
            if setup:
                setup()

            start = time.perf_counter()
            func()
            end = time.perf_counter()

            times_ms.append((end - start) * 1000)

            if teardown:
                teardown()

        total_end = time.perf_counter()
        total_time_ms = (total_end - total_start) * 1000

        # Calculate statistics
        result = BenchmarkResult(
            name=name,
            iterations=iterations,
            total_time_ms=total_time_ms,
            min_time_ms=min(times_ms),
            max_time_ms=max(times_ms),
            mean_time_ms=statistics.mean(times_ms),
            median_time_ms=statistics.median(times_ms),
            std_dev_ms=statistics.stdev(times_ms) if len(times_ms) > 1 else 0.0,
            ops_per_second=iterations / (total_time_ms / 1000) if total_time_ms > 0 else 0,
            metadata=metadata or {},
        )

        self.results.append(result)
        return result

    def _determine_iterations(
        self,
        func: Callable[[], object],
        setup: Callable[[], None] | None,
        teardown: Callable[[], None] | None,
    ) -> int:
        """Determine the number of iterations to reach target time."""
        # Run a few iterations to estimate time
        times: list[float] = []
        for _ in range(5):
            if setup:
                setup()
            start = time.perf_counter()
            func()
            end = time.perf_counter()
            times.append(end - start)
            if teardown:
                teardown()

        avg_time_ms = statistics.mean(times) * 1000

        if avg_time_ms <= 0:
            return self.min_iterations

        # Calculate iterations to reach target time
        estimated_iterations = int(self.target_time_ms / avg_time_ms)

        # Clamp to min/max
        return max(self.min_iterations, min(self.max_iterations, estimated_iterations))

    def print_results(self) -> None:
        """Print all benchmark results."""
        print("\n" + "=" * 60)
        print("BENCHMARK RESULTS")
        print("=" * 60)
        for result in self.results:
            print(result)
            print("-" * 60)

    def get_summary(self) -> dict[str, object]:
        """Get summary of all benchmark results."""
        return {
            "total_benchmarks": len(self.results),
            "results": [r.to_dict() for r in self.results],
            "timestamp": datetime.now(UTC).isoformat(),
        }


# =============================================================================
# Pytest Fixtures
# =============================================================================


@pytest.fixture
def benchmark_timer() -> type[BenchmarkTimer]:
    """Provide the BenchmarkTimer class."""
    return BenchmarkTimer


@pytest.fixture
def benchmark() -> Benchmark:
    """Provide a Benchmark instance for running performance tests."""
    return Benchmark()


@pytest.fixture
def benchmark_quick() -> Benchmark:
    """Provide a quick Benchmark instance with fewer iterations."""
    return Benchmark(
        warmup_iterations=1,
        min_iterations=5,
        max_iterations=100,
        target_time_ms=100.0,
    )


@pytest.fixture
def performance_threshold() -> dict[str, float]:
    """Default performance thresholds in milliseconds."""
    return {
        "crypto_skill_execution": 100.0,  # 100ms per skill
        "database_query": 50.0,  # 50ms per query
        "agent_execution": 500.0,  # 500ms per agent run
        "encryption_operation": 10.0,  # 10ms per encrypt/decrypt
        "hashing_operation": 1.0,  # 1ms per hash
    }


@pytest.fixture
def sample_crypto_data() -> dict[str, object]:
    """Sample crypto data for benchmarks."""
    return {
        "symbol": "BTC",
        "price": 45000.0,
        "volume_24h": 1000000000.0,
        "market_cap": 850000000000.0,
        "change_24h": 2.5,
        "prices_history": [{"timestamp": i, "price": 45000 + (i * 10)} for i in range(100)],
    }


@pytest.fixture
def sample_portfolio_data() -> dict[str, object]:
    """Sample portfolio data for benchmarks."""
    return {
        "portfolio_id": "test-portfolio-001",
        "user_id": "hashed-user-id",
        "holdings": [
            {"symbol": "BTC", "amount": 1.5, "avg_cost": 40000.0},
            {"symbol": "ETH", "amount": 10.0, "avg_cost": 2500.0},
            {"symbol": "SOL", "amount": 100.0, "avg_cost": 100.0},
        ],
        "total_value": 100000.0,
    }


def assert_performance(
    result: BenchmarkResult,
    max_mean_ms: float | None = None,
    max_median_ms: float | None = None,
    min_ops_per_second: float | None = None,
) -> None:
    """Assert that benchmark results meet performance requirements.

    Args:
        result: The benchmark result to check
        max_mean_ms: Maximum allowed mean time in milliseconds
        max_median_ms: Maximum allowed median time in milliseconds
        min_ops_per_second: Minimum required operations per second

    Raises:
        AssertionError: If any threshold is exceeded
    """
    if max_mean_ms is not None:
        assert (
            result.mean_time_ms <= max_mean_ms
        ), f"Mean time {result.mean_time_ms:.4f}ms exceeds threshold {max_mean_ms}ms"

    if max_median_ms is not None:
        assert (
            result.median_time_ms <= max_median_ms
        ), f"Median time {result.median_time_ms:.4f}ms exceeds threshold {max_median_ms}ms"

    if min_ops_per_second is not None:
        assert (
            result.ops_per_second >= min_ops_per_second
        ), f"Ops/sec {result.ops_per_second:.2f} below threshold {min_ops_per_second}"
