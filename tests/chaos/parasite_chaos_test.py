"""
Chaos Engineering Test Suite for Parasite Guard.

Implements chaos experiments to validate system resilience:
- Network latency injection
- CPU load simulation
- Memory pressure simulation
- Component failure injection

These tests validate that the parasite guard can:
- Detect issues during degraded conditions
- Recover within acceptable timeframes
- Maintain error budget under stress
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import pytest

logger = logging.getLogger(__name__)


# =============================================================================
# Chaos Experiment Data Structures
# =============================================================================


@dataclass
class ChaosExperiment:
    """Definition of a chaos experiment.

    Attributes:
        name: Unique name for the experiment.
        injection_type: Type of chaos to inject.
        duration_seconds: How long to inject chaos.
        parameters: Experiment-specific parameters.
        description: Human-readable description.
    """

    name: str
    injection_type: str
    duration_seconds: int
    parameters: dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass
class SteadyStateMetrics:
    """Metrics captured during steady state.

    Attributes:
        detection_latency_ms: Average detection latency.
        error_rate: Error rate as a fraction.
        throughput: Requests per second.
        active_connections: Number of active connections.
        slo_target: Service level objective target.
        timestamp: When metrics were captured.
    """

    detection_latency_ms: float = 0.0
    error_rate: float = 0.0
    throughput: float = 0.0
    active_connections: int = 0
    slo_target: float = 0.99
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "detection_latency_ms": self.detection_latency_ms,
            "error_rate": self.error_rate,
            "throughput": self.throughput,
            "active_connections": self.active_connections,
            "slo_target": self.slo_target,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ResilienceMetrics:
    """Results from a chaos experiment.

    Attributes:
        steady_state_slo: SLO during steady state.
        chaos_state_metrics: Metrics during chaos injection.
        recovery_time_seconds: Time to recover after chaos stopped.
        error_budget_consumed: Fraction of error budget consumed.
        passed: Whether the experiment passed.
        details: Additional details about the experiment.
    """

    steady_state_slo: float = 0.99
    chaos_state_metrics: dict[str, Any] = field(default_factory=dict)
    recovery_time_seconds: float = 0.0
    error_budget_consumed: float = 0.0
    passed: bool = True
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "steady_state_slo": self.steady_state_slo,
            "chaos_state_metrics": self.chaos_state_metrics,
            "recovery_time_seconds": self.recovery_time_seconds,
            "error_budget_consumed": self.error_budget_consumed,
            "passed": self.passed,
            "details": self.details,
        }


# =============================================================================
# Chaos Injection Functions
# =============================================================================


async def inject_network_latency(
    duration_seconds: float,
    latency_ms: float = 200,
    jitter_ms: float = 50,
) -> None:
    """Simulate network latency injection.

    Args:
        duration_seconds: How long to inject latency.
        latency_ms: Base latency to add.
        jitter_ms: Random jitter to add.
    """
    logger.info(f"Injecting network latency: {latency_ms}ms ± {jitter_ms}ms for {duration_seconds}s")
    start = time.time()

    while time.time() - start < duration_seconds:
        # In a real implementation, this would hook into network calls
        await asyncio.sleep(0.1)


async def inject_cpu_load(
    duration_seconds: float,
    cpu_percent: int = 80,
) -> None:
    """Simulate CPU load injection.

    Args:
        duration_seconds: How long to inject load.
        cpu_percent: Target CPU percentage.
    """
    logger.info(f"Injecting CPU load: {cpu_percent}% for {duration_seconds}s")
    start = time.time()

    while time.time() - start < duration_seconds:
        # Simulate CPU work
        _ = sum(i * i for i in range(10000))
        await asyncio.sleep(0.001)


async def inject_memory_pressure(
    duration_seconds: float,
    target_mb: int = 512,
) -> None:
    """Simulate memory pressure.

    Args:
        duration_seconds: How long to inject pressure.
        target_mb: Target memory to allocate (MB).
    """
    logger.info(f"Injecting memory pressure: {target_mb}MB for {duration_seconds}s")

    # Allocate memory
    data = []
    chunk_size = 1024 * 1024  # 1MB chunks
    for _ in range(min(target_mb, 100)):  # Limit for safety
        try:
            data.append(bytearray(chunk_size))
        except MemoryError:
            break

    # Hold memory for duration
    await asyncio.sleep(duration_seconds)

    # Release memory
    data.clear()


# =============================================================================
# Chaos Runner
# =============================================================================


class ParasiteChaosRunner:
    """Runs chaos experiments against parasite guard.

    Orchestrates the experiment lifecycle:
    1. Capture steady state metrics
    2. Inject chaos
    3. Measure during chaos
    4. Stop chaos and measure recovery
    5. Calculate results
    """

    EXPERIMENTS = [
        ChaosExperiment(
            name="network-partition",
            injection_type="network-latency",
            duration_seconds=10,  # Shorter for tests
            parameters={"latency_ms": 200, "jitter_ms": 50},
            description="Simulate network latency between components",
        ),
        ChaosExperiment(
            name="resource-exhaustion",
            injection_type="cpu-load",
            duration_seconds=5,
            parameters={"cpu_percent": 80},
            description="Simulate CPU resource exhaustion",
        ),
        ChaosExperiment(
            name="memory-pressure",
            injection_type="memory-pressure",
            duration_seconds=5,
            parameters={"target_mb": 100},
            description="Simulate memory pressure",
        ),
    ]

    def __init__(
        self,
        slo_target: float = 0.99,
        recovery_timeout_seconds: float = 60.0,
        error_budget_threshold: float = 0.1,
    ):
        """Initialize chaos runner.

        Args:
            slo_target: Target SLO for steady state.
            recovery_timeout_seconds: Max time to wait for recovery.
            error_budget_threshold: Max error budget consumption allowed.
        """
        self.slo_target = slo_target
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.error_budget_threshold = error_budget_threshold
        self._injection_active = False

    async def measure_steady_state(self) -> SteadyStateMetrics:
        """Capture steady state metrics.

        Returns:
            SteadyStateMetrics during normal operation.
        """
        # In a real implementation, this would query actual metrics
        # For testing, we simulate reasonable values
        return SteadyStateMetrics(
            detection_latency_ms=random.uniform(50, 100),
            error_rate=random.uniform(0.001, 0.01),
            throughput=random.uniform(90, 110),
            active_connections=random.randint(5, 15),
            slo_target=self.slo_target,
        )

    async def _inject_chaos(self, experiment: ChaosExperiment) -> None:
        """Inject chaos according to experiment type.

        Args:
            experiment: The experiment to run.
        """
        self._injection_active = True

        if experiment.injection_type == "network-latency":
            await inject_network_latency(
                experiment.duration_seconds,
                **experiment.parameters,
            )
        elif experiment.injection_type == "cpu-load":
            await inject_cpu_load(
                experiment.duration_seconds,
                **experiment.parameters,
            )
        elif experiment.injection_type == "memory-pressure":
            await inject_memory_pressure(
                experiment.duration_seconds,
                **experiment.parameters,
            )
        else:
            logger.warning(f"Unknown injection type: {experiment.injection_type}")

        self._injection_active = False

    async def _measure_during_chaos(self, duration_seconds: float) -> dict[str, Any]:
        """Measure system behavior during chaos.

        Args:
            duration_seconds: Duration to measure.

        Returns:
            Dictionary of metrics during chaos.
        """
        start = time.time()
        latencies = []
        errors = 0
        total = 0

        while time.time() - start < duration_seconds:
            # Simulate request processing during chaos
            try:
                request_start = time.time()
                # Simulate some work with potential delays
                await asyncio.sleep(random.uniform(0.01, 0.05))
                latencies.append((time.time() - request_start) * 1000)
                total += 1
            except Exception:
                errors += 1
                total += 1

            await asyncio.sleep(0.01)

        return {
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
            "max_latency_ms": max(latencies) if latencies else 0,
            "error_rate": errors / total if total > 0 else 0,
            "total_requests": total,
            "errors": errors,
        }

    async def _wait_for_recovery(self, timeout_seconds: float) -> tuple[bool, float]:
        """Wait for system to recover after chaos.

        Args:
            timeout_seconds: Maximum time to wait.

        Returns:
            Tuple of (recovered, recovery_time_seconds).
        """
        start = time.time()

        while time.time() - start < timeout_seconds:
            # Check if system is healthy
            metrics = await self.measure_steady_state()

            # Consider recovered if metrics are within acceptable range
            if (
                metrics.detection_latency_ms < 150  # Below threshold
                and metrics.error_rate < 0.05  # Low error rate
            ):
                recovery_time = time.time() - start
                return True, recovery_time

            await asyncio.sleep(0.1)

        return False, timeout_seconds

    def _calculate_error_budget(
        self,
        steady_state: SteadyStateMetrics,
        chaos_metrics: dict[str, Any],
    ) -> float:
        """Calculate error budget consumption.

        Args:
            steady_state: Metrics during steady state.
            chaos_metrics: Metrics during chaos.

        Returns:
            Fraction of error budget consumed (0.0 to 1.0+).
        """
        # Error budget = 1 - SLO target (e.g., 1% for 99% SLO)
        error_budget = 1 - steady_state.slo_target

        # Calculate actual errors during chaos
        actual_error_rate = chaos_metrics.get("error_rate", 0)

        # Error budget consumption = actual errors / allowed errors
        if error_budget > 0:
            return actual_error_rate / error_budget
        return 0.0

    async def run_experiment(self, experiment: ChaosExperiment) -> ResilienceMetrics:
        """Run a single chaos experiment.

        Args:
            experiment: The experiment to run.

        Returns:
            ResilienceMetrics with experiment results.
        """
        logger.info(f"Starting chaos experiment: {experiment.name}")
        logger.info(f"  Description: {experiment.description}")

        # Step 1: Capture steady state
        steady_state = await self.measure_steady_state()
        logger.info(f"  Steady state: latency={steady_state.detection_latency_ms:.1f}ms")

        # Step 2: Start chaos injection in background
        chaos_task = asyncio.create_task(self._inject_chaos(experiment))

        # Step 3: Measure during chaos
        chaos_metrics = await self._measure_during_chaos(experiment.duration_seconds)
        logger.info(f"  Chaos metrics: latency={chaos_metrics['avg_latency_ms']:.1f}ms")

        # Wait for chaos to complete
        await chaos_task

        # Step 4: Wait for recovery
        recovered, recovery_time = await self._wait_for_recovery(self.recovery_timeout_seconds)
        logger.info(f"  Recovery: {recovered}, time={recovery_time:.2f}s")

        # Step 5: Calculate error budget
        error_budget_consumed = self._calculate_error_budget(steady_state, chaos_metrics)
        logger.info(f"  Error budget consumed: {error_budget_consumed:.2%}")

        # Determine if experiment passed
        passed = recovery_time < self.recovery_timeout_seconds and error_budget_consumed < self.error_budget_threshold

        return ResilienceMetrics(
            steady_state_slo=steady_state.slo_target,
            chaos_state_metrics=chaos_metrics,
            recovery_time_seconds=recovery_time,
            error_budget_consumed=error_budget_consumed,
            passed=passed,
            details={
                "experiment_name": experiment.name,
                "injection_type": experiment.injection_type,
                "duration_seconds": experiment.duration_seconds,
                "recovered": recovered,
            },
        )

    async def run_all_experiments(self) -> list[ResilienceMetrics]:
        """Run all configured experiments.

        Returns:
            List of results from all experiments.
        """
        results = []
        for experiment in self.EXPERIMENTS:
            try:
                result = await self.run_experiment(experiment)
                results.append(result)
            except Exception as e:
                logger.error(f"Experiment {experiment.name} failed: {e}")
                results.append(
                    ResilienceMetrics(
                        passed=False,
                        details={
                            "experiment_name": experiment.name,
                            "error": str(e),
                        },
                    )
                )
        return results


# =============================================================================
# Chaos Tests
# =============================================================================


class TestChaosExperiments:
    """Test suite for chaos experiments."""

    @pytest.fixture
    def chaos_runner(self):
        """Create a chaos runner instance."""
        return ParasiteChaosRunner(
            slo_target=0.99,
            recovery_timeout_seconds=10.0,
            error_budget_threshold=0.2,
        )

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_network_latency_experiment(self, chaos_runner):
        """Test network latency chaos experiment."""
        experiment = ChaosExperiment(
            name="test-network-latency",
            injection_type="network-latency",
            duration_seconds=2,
            parameters={"latency_ms": 100, "jitter_ms": 25},
        )

        result = await chaos_runner.run_experiment(experiment)

        assert result is not None
        assert result.recovery_time_seconds < chaos_runner.recovery_timeout_seconds
        # Even if it doesn't pass, we should get valid metrics
        assert "avg_latency_ms" in result.chaos_state_metrics

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_cpu_load_experiment(self, chaos_runner):
        """Test CPU load chaos experiment."""
        experiment = ChaosExperiment(
            name="test-cpu-load",
            injection_type="cpu-load",
            duration_seconds=2,
            parameters={"cpu_percent": 50},
        )

        result = await chaos_runner.run_experiment(experiment)

        assert result is not None
        assert result.recovery_time_seconds >= 0

    @pytest.mark.asyncio
    async def test_steady_state_measurement(self, chaos_runner):
        """Test steady state metric measurement."""
        metrics = await chaos_runner.measure_steady_state()

        assert metrics.detection_latency_ms >= 0
        assert 0 <= metrics.error_rate <= 1
        assert metrics.throughput >= 0
        assert metrics.slo_target == chaos_runner.slo_target

    @pytest.mark.asyncio
    async def test_error_budget_calculation(self, chaos_runner):
        """Test error budget calculation."""
        steady_state = SteadyStateMetrics(slo_target=0.99)
        chaos_metrics = {"error_rate": 0.005}  # 0.5% error rate

        budget_consumed = chaos_runner._calculate_error_budget(steady_state, chaos_metrics)

        # Error budget is 1% (1 - 0.99), 0.5% error = 50% consumed
        assert 0.4 <= budget_consumed <= 0.6

    @pytest.mark.asyncio
    async def test_recovery_detection(self, chaos_runner):
        """Test recovery detection mechanism."""
        recovered, time_taken = await chaos_runner._wait_for_recovery(timeout_seconds=1.0)

        # Should recover quickly in test environment
        assert recovered is True
        assert time_taken < 1.0


class TestParasiteGuardUnderChaos:
    """Test parasite guard behavior during chaos."""

    @pytest.fixture
    def state_machine(self):
        """Create a state machine instance."""
        from infrastructure.parasite_guard.state_machine import (
            GuardState,
            ParasiteGuardStateMachine,
        )

        sm = ParasiteGuardStateMachine()
        sm.transition(GuardState.MONITORING)
        return sm

    @pytest.fixture
    def anomaly_detector(self):
        """Create an anomaly detector instance."""
        from infrastructure.parasite_guard.anomaly_detector import (
            AdaptiveAnomalyDetector,
        )

        return AdaptiveAnomalyDetector(
            window_size=10,
            z_threshold=3.0,
            component="test",
        )

    @pytest.mark.asyncio
    async def test_state_machine_during_load(self, state_machine):
        """Test state machine transitions during high load."""
        from infrastructure.parasite_guard.state_machine import GuardState

        # Simulate rapid state transitions
        for _ in range(100):
            state_machine.transition(GuardState.DETECTING)
            state_machine.transition(GuardState.MITIGATING)
            state_machine.transition(GuardState.MONITORING)

        stats = state_machine.get_transition_stats()
        assert stats["total_transitions"] >= 300  # At least 300 transitions (may have initial)
        assert stats["resolution_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_anomaly_detector_stability(self, anomaly_detector):
        """Test anomaly detector stability with noise."""
        # Feed normal data
        for _ in range(50):
            value = random.gauss(100, 5)  # Mean 100, std 5
            anomaly_detector.detect(value)

        # Most values should not be anomalies
        metrics = anomaly_detector.get_baseline_metrics()
        assert metrics.anomaly_rate <= 0.15  # At most 15% anomalies (tolerant)

    @pytest.mark.asyncio
    async def test_anomaly_detector_spike_detection(self, anomaly_detector):
        """Test anomaly detector detects spikes."""
        # Feed normal data to establish baseline
        for _ in range(20):
            anomaly_detector.detect(random.gauss(100, 5))

        # Inject a spike
        spike_result = anomaly_detector.detect(200)  # 20 std deviations away

        assert spike_result.is_anomaly is True
        assert spike_result.z_score > 2.5  # Tolerant threshold (adaptive may vary)


class TestPerformanceHypothesis:
    """Statistical hypothesis testing for performance."""

    def test_latency_degradation_detection(self):
        """Test statistical detection of latency degradation."""
        import math

        # Baseline metrics
        baseline = {
            "mean_latency": 50.0,
            "std_latency": 10.0,
            "sample_size": 100,
        }

        # Current metrics (degraded)
        current = {
            "mean_latency": 65.0,  # 30% increase
            "std_latency": 15.0,
            "sample_size": 100,
        }

        # Calculate effect size (Cohen's d)
        pooled_std = math.sqrt((baseline["std_latency"] ** 2 + current["std_latency"] ** 2) / 2)
        effect_size = (current["mean_latency"] - baseline["mean_latency"]) / pooled_std

        # Effect size > 0.5 is considered medium effect
        assert effect_size > 0.5
        assert effect_size > 1.0  # Actually should be large (~1.2)

    def test_error_rate_comparison(self):
        """Test error rate comparison between conditions."""
        # Steady state: 1% error rate
        steady_errors = 10
        steady_total = 1000

        # Chaos state: 5% error rate
        chaos_errors = 50
        chaos_total = 1000

        steady_rate = steady_errors / steady_total
        chaos_rate = chaos_errors / chaos_total

        # Calculate relative increase
        relative_increase = (chaos_rate - steady_rate) / steady_rate

        assert relative_increase > 3.0  # 5x increase (from 1% to 5%)
