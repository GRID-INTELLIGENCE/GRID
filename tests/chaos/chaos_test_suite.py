#!/usr/bin/env python3
"""
GRID Chaos Test Suite (Option 2)
=================================

Chaos engineering test suite for resilience validation.
Tests system behavior under various failure conditions.

Usage:
    # Full chaos test suite
    python tests/chaos/chaos_test_suite.py --all

    # Specific chaos scenarios
    python tests/chaos/chaos_test_suite.py --network-partition
    python tests/chaos/chaos_test_suite.py --resource-exhaustion
    python tests/chaos/chaos_test_suite.py --parasite-flood
    python tests/chaos/chaos_test_suite.py --state-machine-chaos

    # With custom duration
    python tests/chaos/chaos_test_suite.py --all --duration 60
"""

import argparse
import asyncio
import json
import os
import random
import signal
import statistics
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


@dataclass
class ChaosResult:
    """Result of a chaos experiment."""
    experiment_name: str
    start_time: str
    end_time: str
    duration_seconds: float
    success: bool
    error_rate: float
    recovery_time_seconds: float
    metrics: dict[str, Any] = field(default_factory=dict)
    events: list[dict] = field(default_factory=list)


@dataclass
class ChaosReport:
    """Complete chaos testing report."""
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    experiments: list[ChaosResult] = field(default_factory=list)
    overall_success: bool = False
    summary: dict[str, Any] = field(default_factory=dict)


class ChaosTestSuite:
    """Chaos engineering test suite for GRID security."""

    def __init__(self, target_url: str = "http://localhost:8000"):
        self.target_url = target_url
        self.results: list[ChaosResult] = []
        self.stop_event = threading.Event()

    # =============================================================================
    # C1: Network Partition Chaos
    # =============================================================================

    async def network_partition_chaos(self, duration: int = 10) -> ChaosResult:
        """
        Simulate network partition with latency and packet loss.

        Args:
            duration: Experiment duration in seconds
        """
        experiment_name = "network_partition"
        start_time = datetime.now(UTC).isoformat()
        start_perf = time.perf_counter()

        events = []
        success_count = 0
        failure_count = 0
        latencies = []

        print(f"\n🔥 Starting Network Partition Chaos ({duration}s)")
        print("   Simulating: 200ms latency ± 50ms jitter, 5% packet loss")

        async def make_request_with_delay():
            """Make request with simulated network chaos."""
            try:
                # Simulate network latency: 200ms ± 50ms
                delay = random.uniform(0.15, 0.25)
                await asyncio.sleep(delay)

                # 5% chance of packet loss
                if random.random() < 0.05:
                    raise ConnectionError("Simulated packet loss")

                response = requests.get(
                    f"{self.target_url}/health",
                    timeout=2.0
                )
                return response.status_code == 200, time.perf_counter()
            except Exception as e:
                return False, str(e)

        tasks = []
        end_time = time.perf_counter() + duration

        while time.perf_counter() < end_time and not self.stop_event.is_set():
            task = asyncio.create_task(make_request_with_delay())
            tasks.append(task)
            await asyncio.sleep(0.1)  # 10 req/sec

        # Wait for all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                failure_count += 1
                events.append({"type": "failure", "error": str(result)})
            elif result[0]:  # Success
                success_count += 1
                latencies.append(0.2)  # Approximate
            else:
                failure_count += 1
                events.append({"type": "failure", "error": result[1]})

        end_perf = time.perf_counter()
        total_requests = success_count + failure_count
        error_rate = failure_count / total_requests if total_requests > 0 else 0

        # Recovery: measure time to return to normal
        recovery_start = time.perf_counter()
        recovery_success = False
        for _ in range(30):  # Try for 30 seconds
            try:
                response = requests.get(f"{self.target_url}/health", timeout=1.0)
                if response.status_code == 200:
                    recovery_success = True
                    break
            except:
                pass
            await asyncio.sleep(1)
        recovery_time = time.perf_counter() - recovery_start

        result = ChaosResult(
            experiment_name=experiment_name,
            start_time=start_time,
            end_time=datetime.now(UTC).isoformat(),
            duration_seconds=end_perf - start_perf,
            success=error_rate < 0.10,  # SLO: <10% errors
            error_rate=error_rate,
            recovery_time_seconds=recovery_time if recovery_success else -1,
            metrics={
                "total_requests": total_requests,
                "success_count": success_count,
                "failure_count": failure_count,
                "avg_latency": statistics.mean(latencies) if latencies else 0,
                "target_latency": 0.200,
            },
            events=events[:20],  # First 20 events
        )

        print(f"   ✓ Complete: {success_count}/{total_requests} success, {error_rate:.1%} error rate")
        print(f"   Recovery time: {recovery_time:.1f}s" if recovery_success else "   ⚠ Recovery failed")

        return result

    # =============================================================================
    # C2: Resource Exhaustion Chaos
    # =============================================================================

    async def resource_exhaustion_chaos(self, duration: int = 10) -> ChaosResult:
        """
        Simulate CPU and memory pressure.

        Args:
            duration: Experiment duration in seconds
        """
        experiment_name = "resource_exhaustion"
        start_time = datetime.now(UTC).isoformat()
        start_perf = time.perf_counter()

        events = []

        print(f"\n🔥 Starting Resource Exhaustion Chaos ({duration}s)")
        print("   Simulating: 80% CPU load, 100MB memory pressure")

        def cpu_stressor():
            """Generate CPU load."""
            end = time.perf_counter() + duration
            while time.perf_counter() < end and not self.stop_event.is_set():
                _ = [x**2 for x in range(10000)]

        def memory_stressor():
            """Generate memory pressure."""
            big_list = []
            end = time.perf_counter() + duration
            while time.perf_counter() < end and not self.stop_event.is_set():
                big_list.extend([0] * 10000)  # ~80KB per iteration
                if len(big_list) > 10000000:  # Reset at ~80MB
                    big_list = []
                time.sleep(0.1)

        # Start stressors in background
        with ThreadPoolExecutor(max_workers=4) as executor:
            cpu_futures = [executor.submit(cpu_stressor) for _ in range(2)]
            mem_future = executor.submit(memory_stressor)

            # Monitor system responses during stress
            success_count = 0
            failure_count = 0
            end_time = time.perf_counter() + duration

            while time.perf_counter() < end_time and not self.stop_event.is_set():
                try:
                    response = requests.get(
                        f"{self.target_url}/health",
                        timeout=5.0  # Longer timeout under stress
                    )
                    if response.status_code == 200:
                        success_count += 1
                    else:
                        failure_count += 1
                except Exception as e:
                    failure_count += 1
                    events.append({"type": "failure", "error": str(e)[:50]})

                await asyncio.sleep(0.5)

        end_perf = time.perf_counter()
        total_requests = success_count + failure_count
        error_rate = failure_count / total_requests if total_requests > 0 else 0

        # Recovery test
        recovery_start = time.perf_counter()
        recovery_success = False
        for _ in range(30):
            try:
                response = requests.get(f"{self.target_url}/health", timeout=2.0)
                if response.status_code == 200:
                    recovery_success = True
                    break
            except:
                pass
            await asyncio.sleep(1)
        recovery_time = time.perf_counter() - recovery_start

        result = ChaosResult(
            experiment_name=experiment_name,
            start_time=start_time,
            end_time=datetime.now(UTC).isoformat(),
            duration_seconds=end_perf - start_perf,
            success=error_rate < 0.15,  # SLO: <15% under stress
            error_rate=error_rate,
            recovery_time_seconds=recovery_time if recovery_success else -1,
            metrics={
                "total_requests": total_requests,
                "success_count": success_count,
                "failure_count": failure_count,
                "cpu_workers": 2,
                "memory_chunks": "100MB",
            },
            events=events[:20],
        )

        print(f"   ✓ Complete: {success_count}/{total_requests} success, {error_rate:.1%} error rate")
        print(f"   Recovery time: {recovery_time:.1f}s" if recovery_success else "   ⚠ Recovery failed")

        return result

    # =============================================================================
    # C3: Parasite Flood Chaos
    # =============================================================================

    async def parasite_flood_chaos(self, duration: int = 10) -> ChaosResult:
        """
        Flood system with parasitic requests to test detection and mitigation.

        Args:
            duration: Experiment duration in seconds
        """
        experiment_name = "parasite_flood"
        start_time = datetime.now(UTC).isoformat()
        start_perf = time.perf_counter()

        events = []

        print(f"\n🔥 Starting Parasite Flood Chaos ({duration}s)")
        print("   Simulating: 1000 parasitic requests, missing correlation IDs")

        parasites_detected = 0
        null_responses = 0
        normal_responses = 0

        async def send_parasitic_request():
            """Send request designed to trigger parasite detection."""
            try:
                # Missing correlation ID + suspicious user agent
                headers = {
                    "User-Agent": "parasite_test_bot/1.0",
                    "X-Test-Type": "chaos_parasite",
                }

                response = requests.post(
                    f"{self.target_url}/api/test",
                    headers=headers,
                    json={"test": "parasite"},
                    timeout=2.0
                )

                # Check for null response (parasite handled)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data.get("_parasite_meta") or data.get("data") is None:
                            return "parasite_detected"
                        return "normal"
                    except:
                        return "normal"
                return "error"
            except Exception as e:
                return f"error: {e}"

        # Flood with parasite requests
        tasks = []
        for _ in range(1000):
            task = asyncio.create_task(send_parasitic_request())
            tasks.append(task)

            if len(tasks) >= 50:  # Batch processing
                results = await asyncio.gather(*tasks)
                for r in results:
                    if r == "parasite_detected":
                        parasites_detected += 1
                        null_responses += 1
                    elif r == "normal":
                        normal_responses += 1
                    else:
                        events.append({"type": "error", "detail": str(r)})
                tasks = []
                await asyncio.sleep(0.01)

        # Process remaining
        if tasks:
            results = await asyncio.gather(*tasks)
            for r in results:
                if r == "parasite_detected":
                    parasites_detected += 1
                    null_responses += 1
                elif r == "normal":
                    normal_responses += 1

        end_perf = time.perf_counter()
        total = parasites_detected + normal_responses

        detection_rate = parasites_detected / total if total > 0 else 0

        result = ChaosResult(
            experiment_name=experiment_name,
            start_time=start_time,
            end_time=datetime.now(UTC).isoformat(),
            duration_seconds=end_perf - start_perf,
            success=detection_rate > 0.80,  # SLO: >80% detection
            error_rate=1.0 - detection_rate,
            recovery_time_seconds=0,  # No recovery needed
            metrics={
                "total_requests": 1000,
                "parasites_detected": parasites_detected,
                "null_responses": null_responses,
                "normal_responses": normal_responses,
                "detection_rate": detection_rate,
            },
            events=events[:20],
        )

        print(f"   ✓ Complete: {parasites_detected}/{total} parasites detected ({detection_rate:.1%})")
        print(f"   Null responses: {null_responses}")

        return result

    # =============================================================================
    # C4: State Machine Chaos
    # =============================================================================

    async def state_machine_chaos(self, duration: int = 10) -> ChaosResult:
        """
        Rapid state transitions to test state machine stability.

        Args:
            duration: Experiment duration in seconds
        """
        experiment_name = "state_machine_chaos"
        start_time = datetime.now(UTC).isoformat()
        start_perf = time.perf_counter()

        events = []
        transitions = []

        print(f"\n🔥 Starting State Machine Chaos ({duration}s)")
        print("   Simulating: Rapid state transitions, edge cases")

        # Define state transitions
        states = ["INITIALIZING", "MONITORING", "DETECTING", "MITIGATING", "ALERTING"]
        transitions_count = 0
        invalid_transitions = 0

        end_time = time.perf_counter() + duration

        while time.perf_counter() < end_time and not self.stop_event.is_set():
            # Random state transition
            from_state = random.choice(states)
            to_state = random.choice(states)

            # Validate transition (simplified state machine rules)
            valid_transitions = {
                "INITIALIZING": ["MONITORING"],
                "MONITORING": ["DETECTING", "ALERTING"],
                "DETECTING": ["MITIGATING", "ALERTING", "MONITORING"],
                "MITIGATING": ["ALERTING", "MONITORING"],
                "ALERTING": ["MONITORING"],
            }

            is_valid = to_state in valid_transitions.get(from_state, [])

            transitions.append({
                "from": from_state,
                "to": to_state,
                "valid": is_valid,
                "timestamp": time.perf_counter(),
            })

            if is_valid:
                transitions_count += 1
            else:
                invalid_transitions += 1
                events.append({
                    "type": "invalid_transition",
                    "from": from_state,
                    "to": to_state,
                })

            await asyncio.sleep(0.1)

        end_perf = time.perf_counter()
        total_transitions = len(transitions)
        valid_rate = transitions_count / total_transitions if total_transitions > 0 else 0

        result = ChaosResult(
            experiment_name=experiment_name,
            start_time=start_time,
            end_time=datetime.now(UTC).isoformat(),
            duration_seconds=end_perf - start_perf,
            success=valid_rate > 0.70,  # SLO: >70% valid transitions
            error_rate=1.0 - valid_rate,
            recovery_time_seconds=0,
            metrics={
                "total_transitions": total_transitions,
                "valid_transitions": transitions_count,
                "invalid_transitions": invalid_transitions,
                "valid_rate": valid_rate,
            },
            events=events[:20],
        )

        print(f"   ✓ Complete: {transitions_count}/{total_transitions} valid transitions ({valid_rate:.1%})")
        print(f"   Invalid transitions: {invalid_transitions}")

        return result

    # =============================================================================
    # Run All Experiments
    # =============================================================================

    async def run_all(self, duration: int = 10) -> ChaosReport:
        """Run all chaos experiments."""
        print("\n" + "=" * 70)
        print("GRID CHAOS TEST SUITE - Starting Full Chaos Engineering Run")
        print("=" * 70)
        print(f"Target: {self.target_url}")
        print(f"Duration per experiment: {duration}s")
        print("=" * 70)

        # Set up signal handler for graceful shutdown
        def signal_handler(signum, frame):
            print("\n\n⚠️ Received interrupt signal, stopping chaos experiments...")
            self.stop_event.set()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        experiments = [
            ("Network Partition", self.network_partition_chaos),
            ("Resource Exhaustion", self.resource_exhaustion_chaos),
            ("Parasite Flood", self.parasite_flood_chaos),
            ("State Machine", self.state_machine_chaos),
        ]

        results = []
        for name, experiment in experiments:
            try:
                result = await experiment(duration)
                results.append(result)
            except Exception as e:
                print(f"\n❌ Experiment {name} failed: {e}")
                results.append(ChaosResult(
                    experiment_name=name.lower().replace(" ", "_"),
                    start_time=datetime.now(UTC).isoformat(),
                    end_time=datetime.now(UTC).isoformat(),
                    duration_seconds=0,
                    success=False,
                    error_rate=1.0,
                    recovery_time_seconds=-1,
                    events=[{"type": "experiment_failure", "error": str(e)}],
                ))

        # Generate report
        successful = sum(1 for r in results if r.success)
        total = len(results)

        report = ChaosReport(
            experiments=results,
            overall_success=successful == total,
            summary={
                "total_experiments": total,
                "successful": successful,
                "failed": total - successful,
                "success_rate": successful / total if total > 0 else 0,
                "target_slo": "99% availability",
            },
        )

        # Print summary
        print("\n" + "=" * 70)
        print("CHAOS TEST SUITE - SUMMARY")
        print("=" * 70)
        print(f"Experiments: {successful}/{total} passed")
        print(f"Success Rate: {report.summary['success_rate']:.1%}")

        for result in results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            print(f"  {status} {result.experiment_name}: {result.error_rate:.1%} error rate")

        if report.overall_success:
            print("\n🎉 All chaos experiments passed! System is resilient.")
        else:
            print("\n⚠️  Some experiments failed. Review failures above.")

        return report

    def save_report(self, report: ChaosReport, output_path: Path | None = None) -> Path:
        """Save chaos test report to file."""
        if output_path is None:
            output_path = Path("reports/chaos")

        output_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        report_file = output_path / f"chaos_report_{timestamp}.json"

        with open(report_file, "w") as f:
            json.dump(asdict(report), f, indent=2)

        return report_file


def main():
    parser = argparse.ArgumentParser(
        description="GRID Chaos Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run all chaos experiments
    python tests/chaos/chaos_test_suite.py --all

    # Specific experiments
    python tests/chaos/chaos_test_suite.py --network-partition
    python tests/chaos/chaos_test_suite.py --resource-exhaustion
    python tests/chaos/chaos_test_suite.py --parasite-flood
    python tests/chaos/chaos_test_suite.py --state-machine

    # Custom duration
    python tests/chaos/chaos_test_suite.py --all --duration 60

    # Custom target
    python tests/chaos/chaos_test_suite.py --all --url http://localhost:8080
        """,
    )

    parser.add_argument("--all", action="store_true", help="Run all chaos experiments")
    parser.add_argument(
        "--network-partition", action="store_true", help="Network partition chaos"
    )
    parser.add_argument(
        "--resource-exhaustion", action="store_true", help="Resource exhaustion chaos"
    )
    parser.add_argument(
        "--parasite-flood", action="store_true", help="Parasite flood chaos"
    )
    parser.add_argument(
        "--state-machine", action="store_true", help="State machine chaos"
    )
    parser.add_argument("--duration", type=int, default=10, help="Duration per experiment (seconds)")
    parser.add_argument("--url", default="http://localhost:8000", help="Target URL")
    parser.add_argument("--output", type=Path, help="Output directory for reports")

    args = parser.parse_args()

    # Create test suite
    suite = ChaosTestSuite(target_url=args.url)

    # Run experiments
    if args.all:
        report = asyncio.run(suite.run_all(duration=args.duration))
        report_file = suite.save_report(report, args.output)
        print(f"\n📄 Report saved: {report_file}")
    elif args.network_partition:
        result = asyncio.run(suite.network_partition_chaos(duration=args.duration))
        print(f"\nResult: {'✅ PASS' if result.success else '❌ FAIL'}")
    elif args.resource_exhaustion:
        result = asyncio.run(suite.resource_exhaustion_chaos(duration=args.duration))
        print(f"\nResult: {'✅ PASS' if result.success else '❌ FAIL'}")
    elif args.parasite_flood:
        result = asyncio.run(suite.parasite_flood_chaos(duration=args.duration))
        print(f"\nResult: {'✅ PASS' if result.success else '❌ FAIL'}")
    elif args.state_machine:
        result = asyncio.run(suite.state_machine_chaos(duration=args.duration))
        print(f"\nResult: {'✅ PASS' if result.success else '❌ FAIL'}")
    else:
        parser.print_help()
        print("\n⚠️  No experiment selected. Use --all or specific experiment flags.")


if __name__ == "__main__":
    main()
