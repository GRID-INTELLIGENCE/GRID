#!/usr/bin/env python
"""Benchmark runner for CI/CD and local execution.

This script discovers and runs all benchmarks, outputting results
in various formats suitable for CI/CD pipelines and local analysis.

Usage:
    # Run all benchmarks
    python -m tests.benchmarks.benchmark_runner

    # Run with JSON output
    python -m tests.benchmarks.benchmark_runner --output json

    # Run specific benchmark
    python -m tests.benchmarks.benchmark_runner --filter crypto

    # Compare against baseline
    python -m tests.benchmarks.benchmark_runner --baseline baseline.json

    # Save results
    python -m tests.benchmarks.benchmark_runner --save results.json
"""

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.benchmarks.conftest import Benchmark, BenchmarkResult  # noqa: E402


class BenchmarkRunner:
    """Runs benchmarks and collects results."""

    verbose: bool
    benchmark: Benchmark
    results: list[BenchmarkResult]
    start_time: datetime | None
    end_time: datetime | None

    def __init__(self, verbose: bool = True) -> None:
        self.verbose = verbose
        self.benchmark = Benchmark()
        self.results = []
        self.start_time = None
        self.end_time = None

    def log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(message)

    def run_all(self, filter_pattern: str | None = None) -> list[BenchmarkResult]:
        """Run all benchmarks, optionally filtered by pattern."""
        self.start_time = datetime.now(UTC)
        self.log("\n" + "=" * 70)
        self.log("COINBASE BENCHMARK SUITE")
        self.log(f"Started at: {self.start_time.isoformat()}")
        self.log("=" * 70 + "\n")

        # Run benchmark categories
        benchmark_methods = [
            ("Core Operations", self._run_core_benchmarks),
            ("Crypto Skills", self._run_crypto_skill_benchmarks),
            ("Data Processing", self._run_data_processing_benchmarks),
            ("Security Operations", self._run_security_benchmarks),
        ]

        for name, method in benchmark_methods:
            if filter_pattern and filter_pattern.lower() not in name.lower():
                continue
            self.log(f"\n>>> Running {name} benchmarks...")
            self.log("-" * 50)
            method()

        self.end_time = datetime.now(UTC)
        self.results = self.benchmark.results
        return self.results

    def _run_core_benchmarks(self) -> None:
        """Run core operation benchmarks."""

        # Benchmark: Simple function call
        def simple_operation() -> int:
            result = 0
            for i in range(100):
                result += i
            return result

        self.benchmark.run(
            name="simple_loop_operation",
            func=simple_operation,
            metadata={"category": "core", "description": "Simple loop operation"},
        )
        self.log("  ✓ simple_loop_operation")

        # Benchmark: Dictionary operations
        def dict_operations() -> dict[str, int]:
            data: dict[str, int] = {}
            for i in range(100):
                data[f"key_{i}"] = i * 2
            return data

        self.benchmark.run(
            name="dictionary_operations",
            func=dict_operations,
            metadata={"category": "core", "description": "Dictionary creation and population"},
        )
        self.log("  ✓ dictionary_operations")

        # Benchmark: List comprehension
        def list_comprehension() -> list[int]:
            return [x * 2 for x in range(1000)]

        self.benchmark.run(
            name="list_comprehension",
            func=list_comprehension,
            metadata={"category": "core", "description": "List comprehension with 1000 items"},
        )
        self.log("  ✓ list_comprehension")

        # Benchmark: String operations
        def string_operations() -> str:
            parts: list[str] = []
            for i in range(100):
                parts.append(f"item_{i}")
            return ",".join(parts)

        self.benchmark.run(
            name="string_operations",
            func=string_operations,
            metadata={"category": "core", "description": "String building and joining"},
        )
        self.log("  ✓ string_operations")

    def _run_crypto_skill_benchmarks(self) -> None:
        """Run crypto skill benchmarks."""

        # Benchmark: Price calculation simulation
        def price_calculation() -> float:
            prices = [100.0 + (i * 0.5) for i in range(1000)]
            avg = sum(prices) / len(prices)
            variance = sum((p - avg) ** 2 for p in prices) / len(prices)
            return variance**0.5

        self.benchmark.run(
            name="price_volatility_calculation",
            func=price_calculation,
            metadata={"category": "crypto", "description": "Calculate price volatility"},
        )
        self.log("  ✓ price_volatility_calculation")

        # Benchmark: Portfolio value calculation
        def portfolio_calculation() -> float:
            holdings: list[dict[str, float]] = [
                {"amount": 10.0 + i, "price": 100.0 + (i * 10)} for i in range(50)
            ]
            total = sum(h["amount"] * h["price"] for h in holdings)
            return total

        self.benchmark.run(
            name="portfolio_value_calculation",
            func=portfolio_calculation,
            metadata={"category": "crypto", "description": "Calculate portfolio total value"},
        )
        self.log("  ✓ portfolio_value_calculation")

        # Benchmark: Moving average calculation
        def moving_average() -> list[float]:
            prices = [100.0 + (i * 0.1) for i in range(1000)]
            window = 20
            result: list[float] = []
            for i in range(window, len(prices)):
                avg = sum(prices[i - window : i]) / window
                result.append(avg)
            return result

        self.benchmark.run(
            name="moving_average_calculation",
            func=moving_average,
            metadata={"category": "crypto", "description": "Calculate 20-period moving average"},
        )
        self.log("  ✓ moving_average_calculation")

        # Benchmark: RSI calculation simulation
        def rsi_calculation() -> float:
            prices = [100.0 + (i * 0.1) - ((i % 10) * 0.5) for i in range(100)]
            gains: list[float] = []
            losses: list[float] = []
            for i in range(1, len(prices)):
                change = prices[i] - prices[i - 1]
                if change > 0:
                    gains.append(change)
                    losses.append(0.0)
                else:
                    gains.append(0.0)
                    losses.append(abs(change))
            avg_gain = sum(gains[-14:]) / 14
            avg_loss = sum(losses[-14:]) / 14
            if avg_loss == 0:
                return 100.0
            rs = avg_gain / avg_loss
            return 100 - (100 / (1 + rs))

        self.benchmark.run(
            name="rsi_calculation",
            func=rsi_calculation,
            metadata={"category": "crypto", "description": "Calculate RSI indicator"},
        )
        self.log("  ✓ rsi_calculation")

    def _run_data_processing_benchmarks(self) -> None:
        """Run data processing benchmarks."""

        # Benchmark: JSON serialization
        def json_serialization() -> str:
            data: dict[str, Any] = {
                "users": [{"id": i, "name": f"User{i}", "balance": i * 100.0} for i in range(100)],
                "timestamp": "2024-01-01T00:00:00Z",
                "metadata": {"version": "1.0", "count": 100},
            }
            return json.dumps(data)

        self.benchmark.run(
            name="json_serialization",
            func=json_serialization,
            metadata={"category": "data", "description": "Serialize complex dict to JSON"},
        )
        self.log("  ✓ json_serialization")

        # Benchmark: JSON deserialization
        json_data = json.dumps(
            {
                "users": [{"id": i, "name": f"User{i}", "balance": i * 100.0} for i in range(100)],
                "timestamp": "2024-01-01T00:00:00Z",
            }
        )

        def json_deserialization() -> dict[str, Any]:
            result: dict[str, Any] = json.loads(json_data)
            return result

        self.benchmark.run(
            name="json_deserialization",
            func=json_deserialization,
            metadata={"category": "data", "description": "Deserialize JSON to dict"},
        )
        self.log("  ✓ json_deserialization")

        # Benchmark: Data filtering
        dataset = [{"id": i, "value": i * 2, "active": i % 2 == 0} for i in range(1000)]

        def data_filtering() -> list[dict[str, Any]]:
            return [item for item in dataset if item["active"] and item["value"] > 500]

        self.benchmark.run(
            name="data_filtering",
            func=data_filtering,
            metadata={"category": "data", "description": "Filter large dataset"},
        )
        self.log("  ✓ data_filtering")

        # Benchmark: Data sorting
        unsorted_data = [{"id": i, "value": (i * 17) % 1000} for i in range(500)]

        def data_sorting() -> list[dict[str, Any]]:
            return sorted(unsorted_data, key=lambda x: x["value"])

        self.benchmark.run(
            name="data_sorting",
            func=data_sorting,
            metadata={"category": "data", "description": "Sort dataset by value"},
        )
        self.log("  ✓ data_sorting")

    def _run_security_benchmarks(self) -> None:
        """Run security-related benchmarks."""
        import hashlib

        # Benchmark: SHA-256 hashing
        test_data = b"This is a test string for hashing operations" * 10

        def sha256_hashing() -> str:
            return hashlib.sha256(test_data).hexdigest()

        self.benchmark.run(
            name="sha256_hashing",
            func=sha256_hashing,
            metadata={"category": "security", "description": "SHA-256 hash operation"},
        )
        self.log("  ✓ sha256_hashing")

        # Benchmark: Multiple hash rounds
        def multiple_hash_rounds() -> str:
            data = test_data
            for _ in range(100):
                data = hashlib.sha256(data).digest()
            return data.hex()

        self.benchmark.run(
            name="multiple_hash_rounds",
            func=multiple_hash_rounds,
            metadata={"category": "security", "description": "100 rounds of SHA-256"},
        )
        self.log("  ✓ multiple_hash_rounds")

        # Benchmark: User ID hashing (privacy simulation)
        user_ids = [f"user_{i}@example.com" for i in range(100)]

        def user_id_hashing() -> list[str]:
            return [hashlib.sha256(uid.encode()).hexdigest() for uid in user_ids]

        self.benchmark.run(
            name="user_id_hashing",
            func=user_id_hashing,
            metadata={"category": "security", "description": "Hash 100 user IDs for privacy"},
        )
        self.log("  ✓ user_id_hashing")

    def get_summary(self) -> dict[str, Any]:
        """Get summary of all benchmark results."""
        if not self.results:
            return {"error": "No benchmarks run"}

        total_time = sum(r.total_time_ms for r in self.results)
        return {
            "total_benchmarks": len(self.results),
            "total_time_ms": round(total_time, 2),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "results": [r.to_dict() for r in self.results],
            "categories": self._get_category_summary(),
        }

    def _get_category_summary(self) -> dict[str, dict[str, Any]]:
        """Get summary grouped by category."""
        categories: dict[str, list[BenchmarkResult]] = {}
        for result in self.results:
            category_value = result.metadata.get("category", "unknown")
            category: str = str(category_value) if category_value is not None else "unknown"
            if category not in categories:
                categories[category] = []
            categories[category].append(result)

        summary: dict[str, dict[str, Any]] = {}
        for category, results in categories.items():
            total_time = sum(r.total_time_ms for r in results)
            summary[category] = {
                "count": len(results),
                "total_time_ms": round(total_time, 2),
                "benchmarks": [r.name for r in results],
            }
        return summary

    def compare_baseline(self, baseline_path: str) -> dict[str, Any]:
        """Compare results against a baseline file."""
        try:
            with open(baseline_path) as f:
                baseline: dict[str, Any] = json.load(f)
        except FileNotFoundError:
            return {"error": f"Baseline file not found: {baseline_path}"}
        except json.JSONDecodeError:
            return {"error": f"Invalid JSON in baseline file: {baseline_path}"}

        baseline_results: dict[str, Any] = {r["name"]: r for r in baseline.get("results", [])}
        comparisons: list[dict[str, Any]] = []
        regressions: list[str] = []

        for result in self.results:
            if result.name in baseline_results:
                base = baseline_results[result.name]
                base_mean = base["mean_time_ms"]
                current_mean = result.mean_time_ms
                change_pct = ((current_mean - base_mean) / base_mean) * 100 if base_mean > 0 else 0

                comparison = {
                    "name": result.name,
                    "baseline_mean_ms": base_mean,
                    "current_mean_ms": round(current_mean, 4),
                    "change_percent": round(change_pct, 2),
                    "status": (
                        "faster" if change_pct < -5 else "slower" if change_pct > 5 else "stable"
                    ),
                }
                comparisons.append(comparison)

                # Track regressions (>10% slower)
                if change_pct > 10:
                    regressions.append(result.name)

        return {
            "comparisons": comparisons,
            "regressions": regressions,
            "regression_count": len(regressions),
            "has_regressions": len(regressions) > 0,
        }

    def print_results(self, output_format: str = "text") -> None:
        """Print benchmark results in specified format."""
        if output_format == "json":
            print(json.dumps(self.get_summary(), indent=2))
        else:
            self.benchmark.print_results()
            print("\n" + "=" * 70)
            print("SUMMARY")
            print("=" * 70)
            summary = self.get_summary()
            print(f"Total Benchmarks: {summary['total_benchmarks']}")
            print(f"Total Time: {summary['total_time_ms']:.2f}ms")
            print("\nBy Category:")
            categories = summary.get("categories", {})
            if isinstance(categories, dict):
                for category, info in categories.items():
                    if isinstance(info, dict):
                        print(
                            f"  {category}: {info['count']} benchmarks, {info['total_time_ms']:.2f}ms"
                        )

    def save_results(self, output_path: str) -> None:
        """Save results to a JSON file."""
        summary = self.get_summary()
        with open(output_path, "w") as f:
            json.dump(summary, f, indent=2)
        self.log(f"\nResults saved to: {output_path}")


def main() -> int:
    """Main entry point for benchmark runner."""
    parser = argparse.ArgumentParser(description="Run Coinbase benchmarks")
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--filter",
        type=str,
        default=None,
        help="Filter benchmarks by category name",
    )
    parser.add_argument(
        "--baseline",
        type=str,
        default=None,
        help="Path to baseline JSON file for comparison",
    )
    parser.add_argument(
        "--save",
        type=str,
        default=None,
        help="Save results to JSON file",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output",
    )
    parser.add_argument(
        "--fail-on-regression",
        action="store_true",
        help="Exit with error code if regressions detected",
    )

    args = parser.parse_args()

    runner = BenchmarkRunner(verbose=not args.quiet and args.output != "json")

    try:
        runner.run_all(filter_pattern=args.filter)
    except Exception as e:
        print(f"Error running benchmarks: {e}", file=sys.stderr)
        return 1

    # Print results
    runner.print_results(output_format=args.output)

    # Save results if requested
    if args.save:
        runner.save_results(args.save)

    # Compare with baseline if provided
    if args.baseline:
        comparison = runner.compare_baseline(args.baseline)
        if args.output == "json":
            print(json.dumps(comparison, indent=2))
        else:
            print("\n" + "=" * 70)
            print("BASELINE COMPARISON")
            print("=" * 70)
            if "error" in comparison:
                print(f"Error: {comparison['error']}")
            else:
                for comp in comparison.get("comparisons", []):
                    status_symbol = {
                        "faster": "🟢",
                        "slower": "🔴",
                        "stable": "🟡",
                    }.get(comp["status"], "⚪")
                    baseline_ms = comp["baseline_mean_ms"]
                    current_ms = comp["current_mean_ms"]
                    change_pct = comp["change_percent"]
                    print(
                        f"{status_symbol} {comp['name']}: "
                        + f"{baseline_ms:.4f}ms -> {current_ms:.4f}ms "
                        + f"({change_pct:+.2f}%)"
                    )

                regressions = comparison.get("regressions", [])
                if regressions:
                    print(f"\n⚠️  Regressions detected: {', '.join(regressions)}")

        if args.fail_on_regression and comparison.get("has_regressions"):
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
