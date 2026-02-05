#!/usr/bin/env python3
"""
Runtime Attack Simulation for Parasite Guard State Machine Validation.

Simulates parasitic attack patterns:
- Missing correlation headers
- High-frequency bursts
- Suspicious User-Agents
- Missing authentication

Monitors:
- State machine transitions
- Detection rates (by status code and _parasite_meta)
- Null response generation
- Sanitization triggers

Detection semantics:
- A request is "detected" if:
  1. HTTP status = 403 (Parasite Guard default block response), OR
  2. Response body contains `_parasite_meta` field
- Timeouts/errors are tracked separately for visibility

Configuration (environment variables or CLI):
- ATTACK_SIM_TIMEOUT: Request timeout in seconds (default: 30)
"""

import asyncio
import json
import logging
import os
import random
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import httpx

# Configurable timeout (seconds)
DEFAULT_TIMEOUT = float(os.getenv("ATTACK_SIM_TIMEOUT", "30.0"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("attack_simulation")


# =============================================================================
# Attack Patterns
# =============================================================================

SUSPICIOUS_USER_AGENTS = [
    "curl/7.68.0",
    "python-requests/2.28.0",
    "Mozilla/5.0 (compatible; BadBot/1.0)",
    "scanner/1.0",
    "",  # Empty user agent
]

ATTACK_PATTERNS = {
    "missing_correlation": {
        "headers": {},
        "description": "Requests without correlation IDs",
    },
    "high_frequency": {
        "headers": {"X-Correlation-ID": "burst-attack"},
        "description": "Rapid-fire requests (100+ req/s)",
    },
    "suspicious_ua": {
        "headers": {"User-Agent": random.choice(SUSPICIOUS_USER_AGENTS)},
        "description": "Suspicious User-Agent strings",
    },
    "missing_auth": {
        "headers": {},
        "description": "Requests without authentication headers",
    },
    "mixed_attack": {
        "headers": {
            "User-Agent": random.choice(SUSPICIOUS_USER_AGENTS),
        },
        "description": "Combined attack patterns",
    },
    "slowloris": {
        "headers": {"X-Correlation-ID": "slow-attack"},
        "description": "Slow, persistent connections exhausting resources",
    },
    "credential_stuffing": {
        "headers": {"X-Correlation-ID": "creds-{random}"},
        "description": "High-volume authentication attempts with stolen credentials",
    },
    "cascade": {
        "headers": {},
        "description": "Multi-stage: flood -> pause -> flood pattern",
    },
    "api_abuse": {
        "headers": {"X-Correlation-ID": "api-abuse"},
        "description": "Rapid API calls with varying endpoints",
    },
}


# =============================================================================
# State Machine Monitor
# =============================================================================


@dataclass
class StateTransition:
    """Record of a state transition."""

    from_state: str
    to_state: str
    timestamp: datetime
    trigger: str = ""
    confidence: float = 1.0


@dataclass
class AttackResult:
    """Result from a single attack request.

    Detection semantics:
    - detected_by_status: True if HTTP 403 (Parasite Guard block)
    - detected_by_body: True if response contains _parasite_meta
    - is_detected: True if either of the above
    - is_timeout_or_error: True if request failed (status=0)
    """

    pattern: str
    status_code: int
    response_time_ms: float
    is_null_response: bool = False
    parasite_meta: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    # Detection breakdown
    detected_by_status: bool = False  # HTTP 403
    detected_by_body: bool = False  # _parasite_meta in body
    is_timeout_or_error: bool = False  # Request failed

    @property
    def is_detected(self) -> bool:
        """True if detected by status (403) OR body (_parasite_meta)."""
        return self.detected_by_status or self.detected_by_body


@dataclass
class SimulationMetrics:
    """Aggregated metrics from attack simulation.

    Tracks detection breakdown:
    - detected_by_status_403: Count of 403 responses
    - detected_by_body: Count of responses with _parasite_meta
    - detected_total: Count where either of the above is true
    - timeouts_or_errors: Count of failed requests (status=0)
    - status_breakdown: Dict of status_code -> count
    """

    total_requests: int = 0
    detected_parasites: int = 0  # Legacy: same as detected_total
    null_responses: int = 0
    normal_responses: int = 0
    avg_response_time_ms: float = 0.0
    detection_rate: float = 0.0
    state_transitions: list[StateTransition] = field(default_factory=list)
    attack_results: list[AttackResult] = field(default_factory=list)
    # Detection breakdown
    detected_by_status_403: int = 0
    detected_by_body: int = 0
    detected_total: int = 0
    timeouts_or_errors: int = 0
    status_breakdown: dict[int, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize metrics to dictionary."""
        return {
            "total_requests": self.total_requests,
            "detected_parasites": self.detected_parasites,
            "null_responses": self.null_responses,
            "normal_responses": self.normal_responses,
            "avg_response_time_ms": self.avg_response_time_ms,
            "detection_rate": self.detection_rate,
            # Detection breakdown
            "detected_by_status_403": self.detected_by_status_403,
            "detected_by_body": self.detected_by_body,
            "detected_total": self.detected_total,
            "timeouts_or_errors": self.timeouts_or_errors,
            "status_breakdown": self.status_breakdown,
            "state_transitions": [
                {
                    "from": t.from_state,
                    "to": t.to_state,
                    "timestamp": t.timestamp.isoformat(),
                    "trigger": t.trigger,
                }
                for t in self.state_transitions
            ],
        }


class StateMachineMonitor:
    """Monitors state machine transitions during attack."""

    def __init__(self):
        self.transitions: list[StateTransition] = []
        self.current_state = "INITIALIZING"

    def record_transition(self, from_state: str, to_state: str, trigger: str = "", confidence: float = 1.0):
        """Record a state transition."""
        transition = StateTransition(
            from_state=from_state,
            to_state=to_state,
            timestamp=datetime.now(UTC),
            trigger=trigger,
            confidence=confidence,
        )
        self.transitions.append(transition)
        self.current_state = to_state
        logger.info(f"State transition: {from_state} -> {to_state} (trigger: {trigger})")

    def get_transition_graph(self) -> dict[str, int]:
        """Get transition counts for visualization."""
        graph = defaultdict(int)
        for t in self.transitions:
            edge = f"{t.from_state} -> {t.to_state}"
            graph[edge] += 1
        return dict(graph)


# =============================================================================
# Attack Simulator
# =============================================================================


class ParasiteAttackSimulator:
    """Simulates parasitic attacks and monitors system response."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        state_machine_monitor: StateMachineMonitor | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.base_url = base_url
        self.monitor = state_machine_monitor or StateMachineMonitor()
        self.metrics = SimulationMetrics()
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def send_parasitic_request(
        self,
        pattern: str,
        path: str = "/api/v1/health",
        method: str = "GET",
        extra_headers: dict | None = None,
    ) -> AttackResult:
        """Send a single parasitic request."""
        attack_config = ATTACK_PATTERNS.get(pattern, ATTACK_PATTERNS["missing_correlation"])

        headers = attack_config["headers"].copy()
        # Add random correlation ID if not present (for some patterns)
        if "X-Correlation-ID" not in headers and pattern != "missing_correlation":
            headers["X-Correlation-ID"] = f"test-{random.randint(1000, 9999)}"
        # Merge extra headers
        if extra_headers:
            headers.update(extra_headers)

        start_time = time.time()

        try:
            response = await self.client.request(
                method=method,
                url=f"{self.base_url}{path}",
                headers=headers,
            )

            response_time_ms = (time.time() - start_time) * 1000

            # Check detection by status code (403 = Parasite Guard block)
            detected_by_status = response.status_code == 403

            # Check detection by body (_parasite_meta field)
            is_null_response = False
            parasite_meta = {}
            detected_by_body = False

            try:
                body = response.json()
                if "_parasite_meta" in body:
                    is_null_response = True
                    detected_by_body = True
                    parasite_meta = body.get("_parasite_meta", {})
            except Exception:
                pass

            result = AttackResult(
                pattern=pattern,
                status_code=response.status_code,
                response_time_ms=response_time_ms,
                is_null_response=is_null_response,
                parasite_meta=parasite_meta,
                detected_by_status=detected_by_status,
                detected_by_body=detected_by_body,
                is_timeout_or_error=False,
            )

            return result

        except Exception as e:
            logger.error(f"Request failed: {e}")
            return AttackResult(
                pattern=pattern,
                status_code=0,
                response_time_ms=(time.time() - start_time) * 1000,
                is_timeout_or_error=True,
            )

    async def burst_attack(self, pattern: str, count: int = 100, delay_ms: float = 10.0) -> list[AttackResult]:
        """Send a burst of requests."""
        logger.info(f"Starting burst attack: {pattern} ({count} requests, {delay_ms}ms delay)")

        # Simulate state transition: MONITORING -> DETECTING
        if self.monitor.current_state == "MONITORING":
            self.monitor.record_transition("MONITORING", "DETECTING", trigger=f"burst_{pattern}")

        results = []
        tasks = []

        for i in range(count):
            task = self.send_parasitic_request(pattern)
            tasks.append(task)

            # Small delay to avoid overwhelming
            if delay_ms > 0:
                await asyncio.sleep(delay_ms / 1000.0)

        # Wait for all requests
        results = await asyncio.gather(*tasks)

        # Simulate state transition: DETECTING -> MITIGATING
        if self.monitor.current_state == "DETECTING":
            detected_count = sum(1 for r in results if r.is_detected)
            if detected_count > 0:
                self.monitor.record_transition(
                    "DETECTING",
                    "MITIGATING",
                    trigger=f"{detected_count}_parasites_detected",
                    confidence=min(detected_count / count, 1.0),
                )

        return results

    async def slowloris_attack(
        self, duration_seconds: int = 30, connection_interval: float = 0.1
    ) -> list[AttackResult]:
        """Simulate slowloris-style attack with persistent connections."""
        logger.info(f"Starting slowloris attack ({duration_seconds}s duration, {connection_interval}s interval)")

        if self.monitor.current_state == "MONITORING":
            self.monitor.record_transition("MONITORING", "DETECTING", trigger="slowloris_started")

        results = []
        start_time = time.time()

        while time.time() - start_time < duration_seconds:
            try:
                result = await self.send_parasitic_request("slowloris")
                results.append(result)
                await asyncio.sleep(connection_interval)
            except Exception as e:
                logger.debug(f"Slowloris request failed: {e}")

        if self.monitor.current_state == "DETECTING" and len(results) > 50:
            self.monitor.record_transition("DETECTING", "MITIGATING", trigger="slowloris_connection_flood")

        return results

    async def credential_stuffing_attack(self, count: int = 100, delay_ms: float = 50.0) -> list[AttackResult]:
        """Simulate credential stuffing with varying correlation IDs."""
        logger.info(f"Starting credential stuffing attack ({count} requests, {delay_ms}ms delay)")

        if self.monitor.current_state == "MONITORING":
            self.monitor.record_transition("MONITORING", "DETECTING", trigger="auth_anomaly")

        results = []
        tasks = []

        for i in range(count):
            extra_headers = {"X-Correlation-ID": f"creds-{random.randint(10000, 99999)}"}
            task = self.send_parasitic_request(
                "credential_stuffing", path="/api/v1/auth/login", extra_headers=extra_headers
            )
            tasks.append(task)
            if delay_ms > 0:
                await asyncio.sleep(delay_ms / 1000.0)

        results = await asyncio.gather(*tasks)

        if self.monitor.current_state == "DETECTING":
            detected_count = sum(1 for r in results if r.status_code in [401, 403, 429])
            if detected_count > count * 0.5:
                self.monitor.record_transition("DETECTING", "MITIGATING", trigger=f"auth_failure_{detected_count}")

        return results

    async def cascade_attack(self, waves: int = 3, requests_per_wave: int = 50) -> list[AttackResult]:
        """Simulate cascading attack with flood -> pause -> flood pattern."""
        logger.info(f"Starting cascade attack ({waves} waves, {requests_per_wave} reqs/wave)")

        if self.monitor.current_state == "MONITORING":
            self.monitor.record_transition("MONITORING", "DETECTING", trigger="cascade_start")

        all_results = []

        for wave in range(waves):
            logger.info(f"Cascade wave {wave + 1}/{waves}")
            wave_results = await self.burst_attack("cascade", count=requests_per_wave, delay_ms=5.0)
            all_results.extend(wave_results)

            pause_duration = 2.0 if wave < waves - 1 else 0
            if pause_duration > 0:
                await asyncio.sleep(pause_duration)

        if self.monitor.current_state == "MITIGATING":
            self.monitor.record_transition("MITIGATING", "DETECTING", trigger="cascade_pause")

        if self.monitor.current_state == "DETECTING":
            self.monitor.record_transition("DETECTING", "MITIGATING", trigger="cascade_complete")

        return all_results

    async def api_abuse_attack(self, total_requests: int = 200) -> list[AttackResult]:
        """Simulate API abuse with varying endpoints."""
        logger.info(f"Starting API abuse attack ({total_requests} requests across endpoints)")

        if self.monitor.current_state == "MONITORING":
            self.monitor.record_transition("MONITORING", "DETECTING", trigger="api_abuse")

        endpoints = [
            "/api/v1/users",
            "/api/v1/data",
            "/api/v1/search",
            "/api/v1/export",
            "/api/v1/admin",
        ]

        results = []
        tasks = []

        for i in range(total_requests):
            endpoint = endpoints[i % len(endpoints)]
            task = self.send_parasitic_request("api_abuse", path=endpoint)
            tasks.append(task)
            await asyncio.sleep(0.02)

        results = await asyncio.gather(*tasks)

        if self.monitor.current_state == "DETECTING":
            unique_endpoints = len(set(r for r in results))
            if unique_endpoints >= 3:
                self.monitor.record_transition(
                    "DETECTING", "MITIGATING", trigger=f"api_abuse_{unique_endpoints}_endpoints"
                )

        return results

    async def mixed_attack(self, total_requests: int = 200) -> SimulationMetrics:
        """Run a mixed attack with multiple patterns."""
        logger.info(f"Starting mixed attack simulation ({total_requests} total requests)")

        # Initialize state machine
        self.monitor.record_transition("INITIALIZING", "MONITORING", trigger="simulation_start")

        all_results = []

        # Phase 1: Normal traffic (should not trigger)
        logger.info("Phase 1: Normal traffic baseline")
        normal_results = await self.burst_attack("missing_correlation", count=20, delay_ms=100.0)
        all_results.extend(normal_results)

        # Phase 2: High-frequency attack
        logger.info("Phase 2: High-frequency burst attack")
        burst_results = await self.burst_attack("high_frequency", count=100, delay_ms=5.0)
        all_results.extend(burst_results)

        # Phase 3: Suspicious User-Agent attack
        logger.info("Phase 3: Suspicious User-Agent attack")
        ua_results = await self.burst_attack("suspicious_ua", count=50, delay_ms=20.0)
        all_results.extend(ua_results)

        # Phase 4: Mixed attack
        logger.info("Phase 4: Mixed attack patterns")
        mixed_results = await self.burst_attack("mixed_attack", count=30, delay_ms=15.0)
        all_results.extend(mixed_results)

        # Simulate recovery: MITIGATING -> MONITORING
        if self.monitor.current_state == "MITIGATING":
            self.monitor.record_transition("MITIGATING", "MONITORING", trigger="attack_complete")

        # Calculate metrics
        self.metrics.total_requests = len(all_results)

        # Detection breakdown
        self.metrics.detected_by_status_403 = sum(1 for r in all_results if r.detected_by_status)
        self.metrics.detected_by_body = sum(1 for r in all_results if r.detected_by_body)
        self.metrics.detected_total = sum(1 for r in all_results if r.is_detected)
        self.metrics.timeouts_or_errors = sum(1 for r in all_results if r.is_timeout_or_error)

        # Legacy metrics (for backward compatibility)
        self.metrics.detected_parasites = self.metrics.detected_total
        self.metrics.null_responses = self.metrics.detected_by_body
        self.metrics.normal_responses = self.metrics.total_requests - self.metrics.detected_total - self.metrics.timeouts_or_errors

        # Status code breakdown
        status_counts: dict[int, int] = defaultdict(int)
        for r in all_results:
            status_counts[r.status_code] += 1
        self.metrics.status_breakdown = dict(status_counts)

        self.metrics.avg_response_time_ms = (
            sum(r.response_time_ms for r in all_results) / len(all_results) if all_results else 0.0
        )
        self.metrics.detection_rate = (
            self.metrics.detected_total / self.metrics.total_requests if self.metrics.total_requests > 0 else 0.0
        )
        self.metrics.attack_results = all_results
        self.metrics.state_transitions = self.monitor.transitions

        return self.metrics

    def print_summary(self):
        """Print attack simulation summary."""
        print("\n" + "=" * 80)
        print("ATTACK SIMULATION SUMMARY")
        print("=" * 80)

        print(f"\nRequest Metrics:")
        print(f"  Total Requests:     {self.metrics.total_requests}")
        print(f"  Detection Rate:     {self.metrics.detection_rate:.2%}")
        print(f"  Avg Response Time:  {self.metrics.avg_response_time_ms:.2f}ms")

        print(f"\nDetection Breakdown:")
        print(f"  Detected (total):   {self.metrics.detected_total}")
        print(f"    - By 403 status:  {self.metrics.detected_by_status_403}")
        print(f"    - By body meta:   {self.metrics.detected_by_body}")
        print(f"  Timeouts/Errors:    {self.metrics.timeouts_or_errors}")
        print(f"  Normal (unblocked): {self.metrics.normal_responses}")

        print(f"\nStatus Code Breakdown:")
        for status, count in sorted(self.metrics.status_breakdown.items()):
            label = "(timeout/error)" if status == 0 else ""
            print(f"  HTTP {status:3d}: {count:4d} {label}")

        print(f"\nState Transitions:")
        if self.monitor.transitions:
            for i, t in enumerate(self.monitor.transitions, 1):
                print(f"  {i}. {t.from_state} -> {t.to_state} ({t.trigger})")
        else:
            print("  No state transitions recorded")

        print(f"\nTransition Graph:")
        graph = self.monitor.get_transition_graph()
        for edge, count in graph.items():
            print(f"  {edge}: {count}")

        print(f"\nAttack Pattern Breakdown:")
        pattern_stats = defaultdict(lambda: {"total": 0, "detected": 0, "by_403": 0, "by_body": 0, "errors": 0})
        for result in self.metrics.attack_results:
            pattern_stats[result.pattern]["total"] += 1
            if result.is_detected:
                pattern_stats[result.pattern]["detected"] += 1
            if result.detected_by_status:
                pattern_stats[result.pattern]["by_403"] += 1
            if result.detected_by_body:
                pattern_stats[result.pattern]["by_body"] += 1
            if result.is_timeout_or_error:
                pattern_stats[result.pattern]["errors"] += 1

        for pattern, stats in pattern_stats.items():
            rate = stats["detected"] / stats["total"] if stats["total"] > 0 else 0.0
            print(f"  {pattern:20s}: {stats['detected']}/{stats['total']} ({rate:.2%})")
            print(f"      403={stats['by_403']}, body={stats['by_body']}, err={stats['errors']}")

        print("\n" + "=" * 80)

    async def close(self):
        """Cleanup resources."""
        await self.client.aclose()


# =============================================================================
# Main Entry Point
# =============================================================================


async def main():
    """Run attack simulation."""
    import argparse

    parser = argparse.ArgumentParser(description="Parasite Guard Attack Simulation")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of target application")
    parser.add_argument("--requests", type=int, default=200, help="Total number of requests")
    parser.add_argument("--output", help="Output JSON file for results")
    parser.add_argument("--pattern", choices=list(ATTACK_PATTERNS.keys()), help="Single pattern to test")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="Request timeout in seconds")

    args = parser.parse_args()

    simulator = ParasiteAttackSimulator(base_url=args.url, timeout=args.timeout)
    logger.info(f"Using timeout: {args.timeout}s")

    try:
        if args.pattern:
            # Single pattern test
            logger.info(f"Testing single pattern: {args.pattern}")
            results = await simulator.burst_attack(args.pattern, count=args.requests, delay_ms=10.0)
            simulator.metrics.attack_results = results
            simulator.metrics.total_requests = len(results)

            # Calculate detection breakdown
            simulator.metrics.detected_by_status_403 = sum(1 for r in results if r.detected_by_status)
            simulator.metrics.detected_by_body = sum(1 for r in results if r.detected_by_body)
            simulator.metrics.detected_total = sum(1 for r in results if r.is_detected)
            simulator.metrics.timeouts_or_errors = sum(1 for r in results if r.is_timeout_or_error)
            simulator.metrics.detected_parasites = simulator.metrics.detected_total
            simulator.metrics.null_responses = simulator.metrics.detected_by_body
            simulator.metrics.normal_responses = len(results) - simulator.metrics.detected_total - simulator.metrics.timeouts_or_errors

            # Status breakdown
            status_counts: dict[int, int] = defaultdict(int)
            for r in results:
                status_counts[r.status_code] += 1
            simulator.metrics.status_breakdown = dict(status_counts)

            simulator.metrics.detection_rate = simulator.metrics.detected_total / len(results) if results else 0.0
        else:
            # Mixed attack
            await simulator.mixed_attack(total_requests=args.requests)

        simulator.print_summary()

        # Save results
        if args.output:
            with open(args.output, "w") as f:
                json.dump(simulator.metrics.to_dict(), f, indent=2)
            logger.info(f"Results saved to {args.output}")

    finally:
        await simulator.close()


if __name__ == "__main__":
    asyncio.run(main())
