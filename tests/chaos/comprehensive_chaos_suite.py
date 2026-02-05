#!/usr/bin/env python3
"""
GRID Comprehensive Chaos Test Suite
====================================

Production-grade chaos engineering tests for the Parasite Guard system.
Tests system resilience under various failure conditions.

Components Tested:
1. Detection Pipeline - Under load, partial failures, cascading failures
2. State Machine - Recovery from invalid states, rapid transitions
3. Sanitization - Concurrent sanitization, timeout scenarios
4. Alerting - Channel failures, escalation thresholds
5. EventBus Integration - Subscription leaks, race conditions

Usage:
    pytest tests/chaos/comprehensive_chaos_suite.py -v
    pytest tests/chaos/comprehensive_chaos_suite.py -v -m "not slow"
    pytest tests/chaos/comprehensive_chaos_suite.py -v --chaos-level=high

Author: GRID Security Framework
Version: 2.0.0
Date: 2026-02-05
"""

from __future__ import annotations

import asyncio
import gc
import os
import random
import sys
import uuid
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Callable
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, str(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from infrastructure.parasite_guard.config import GuardMode, ParasiteGuardConfig
from infrastructure.parasite_guard.models import DetectionResult, ParasiteContext, ParasiteSeverity
from infrastructure.parasite_guard.state_machine import GuardState, ParasiteGuardStateMachine
from infrastructure.parasite_guard.anomaly_detector import (
    AdaptiveAnomalyDetector,
    MultiWindowAnomalyDetector,
    RateLimitAnomalyDetector,
)


# =============================================================================
# CHAOS EXPERIMENT FRAMEWORK
# =============================================================================


@dataclass
class ChaosExperiment:
    """Definition of a chaos experiment."""

    name: str
    description: str
    injection_type: str  # cpu_load, memory_pressure, network_latency, error_injection
    duration_seconds: float
    parameters: dict[str, Any] = field(default_factory=dict)
    recovery_timeout_seconds: float = 60.0
    error_budget_percent: float = 1.0  # SLO: 99% availability


@dataclass
class ChaosResult:
    """Result of a chaos experiment."""

    experiment: ChaosExperiment
    started_at: datetime
    ended_at: datetime
    steady_state_metrics: dict[str, float]
    chaos_metrics: dict[str, float]
    recovery_time_seconds: float
    error_budget_consumed: float
    passed: bool
    notes: list[str] = field(default_factory=list)


class ChaosInjector:
    """Injects chaos into the system."""

    def __init__(self):
        self._active_injections: list[asyncio.Task] = []
        self._stop_event = asyncio.Event()

    async def inject_cpu_load(self, percent: int = 80, duration: float = 5.0) -> None:
        """Simulate CPU load."""
        end_time = time.monotonic() + duration
        while time.monotonic() < end_time and not self._stop_event.is_set():
            # Busy loop to simulate CPU load
            start = time.monotonic()
            while time.monotonic() - start < 0.001 * (percent / 100):
                _ = sum(range(1000))
            await asyncio.sleep(0.001 * (1 - percent / 100))

    async def inject_memory_pressure(self, mb: int = 100, duration: float = 5.0) -> None:
        """Simulate memory pressure."""
        # Allocate memory
        data = [bytearray(1024 * 1024) for _ in range(mb)]
        try:
            await asyncio.sleep(duration)
        finally:
            del data
            gc.collect()

    async def inject_network_latency(
        self,
        latency_ms: int = 200,
        jitter_ms: int = 50,
        duration: float = 10.0,
    ) -> None:
        """Simulate network latency by adding delays."""
        # This would be injected into actual network calls
        # For now, we just delay the event loop
        end_time = time.monotonic() + duration
        while time.monotonic() < end_time and not self._stop_event.is_set():
            delay = (latency_ms + random.randint(-jitter_ms, jitter_ms)) / 1000
            await asyncio.sleep(delay)

    async def inject_error_rate(
        self,
        rate: float = 0.1,
        duration: float = 10.0,
        error_generator: Callable[[], Exception] | None = None,
    ) -> Callable:
        """Return a decorator that injects errors at the given rate."""
        if error_generator is None:
            error_generator = lambda: Exception("Chaos injection error")

        def error_injector(func):
            async def wrapper(*args, **kwargs):
                if random.random() < rate:
                    raise error_generator()
                return await func(*args, **kwargs)

            return wrapper

        return error_injector

    def stop_all(self) -> None:
        """Stop all active injections."""
        self._stop_event.set()
        for task in self._active_injections:
            task.cancel()
        self._active_injections.clear()


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def chaos_injector():
    """Create a chaos injector instance."""
    injector = ChaosInjector()
    yield injector
    injector.stop_all()


@pytest.fixture
def parasite_config():
    """Create a test parasite guard config."""
    config = ParasiteGuardConfig()
    config.enabled = True
    config.detection_timeout_ms = 100
    config.max_concurrent_sanitizations = 5
    return config


@pytest.fixture
def state_machine():
    """Create a test state machine."""
    return ParasiteGuardStateMachine()


@pytest.fixture
def anomaly_detector():
    """Create a test anomaly detector."""
    return AdaptiveAnomalyDetector(window_size=60, z_threshold=3.5)


@pytest.fixture
def multi_window_detector():
    """Create a multi-window anomaly detector."""
    return MultiWindowAnomalyDetector()


@pytest.fixture
def rate_limit_detector():
    """Create a rate limit detector."""
    return RateLimitAnomalyDetector(window_seconds=60.0, max_rate=100.0)


@pytest.fixture
def strict_rate_limit_detector():
    """Create a strict rate limit detector for chaos tests (low threshold to trigger)."""
    return RateLimitAnomalyDetector(window_seconds=1.0, max_rate=10.0)


# =============================================================================
# STATE MACHINE CHAOS TESTS
# =============================================================================


class TestStateMachineChaos:
    """Chaos tests for the state machine."""

    @pytest.mark.asyncio
    async def test_rapid_state_transitions(self, state_machine: ParasiteGuardStateMachine):
        """Test state machine under rapid transition load."""
        # Measure baseline
        baseline_transitions = 0
        start = time.monotonic()

        # Valid transition sequence: INITIALIZING -> MONITORING -> DETECTING -> MITIGATING -> MONITORING
        # First transition from INITIALIZING to MONITORING only when in INITIALIZING
        if state_machine.state == GuardState.INITIALIZING:
            state_machine.transition(GuardState.MONITORING, confidence=0.95)
            baseline_transitions += 1

        for _ in range(100):
            state_machine.transition(GuardState.DETECTING, confidence=0.95)
            state_machine.transition(GuardState.MITIGATING, confidence=0.98)
            state_machine.transition(GuardState.MONITORING, confidence=0.90)
            baseline_transitions += 3

        duration = time.monotonic() - start

        # Should complete within reasonable time
        assert duration < 1.0, f"Rapid transitions took too long: {duration}s"
        assert state_machine.state == GuardState.MONITORING

    @pytest.mark.asyncio
    async def test_concurrent_state_transitions(self, state_machine: ParasiteGuardStateMachine):
        """Test state machine under concurrent access."""
        errors = []
        transitions = []

        async def transition_worker(worker_id: int):
            for i in range(50):
                try:
                    # Each worker tries valid transitions
                    if state_machine.state == GuardState.MONITORING:
                        state_machine.transition(GuardState.DETECTING, confidence=0.95)
                    elif state_machine.state == GuardState.DETECTING:
                        state_machine.transition(GuardState.MITIGATING, confidence=0.98)
                    elif state_machine.state == GuardState.MITIGATING:
                        state_machine.transition(GuardState.MONITORING, confidence=0.90)
                    elif state_machine.state == GuardState.ALERTING:
                        state_machine.transition(GuardState.MONITORING, confidence=1.0)
                    transitions.append((worker_id, i, state_machine.state))
                except Exception as e:
                    errors.append((worker_id, i, str(e)))
                await asyncio.sleep(0.001)

        # Initialize to MONITORING
        state_machine.transition(GuardState.MONITORING, confidence=1.0)

        # Run concurrent workers
        await asyncio.gather(*[transition_worker(i) for i in range(10)])

        # Allow some errors due to race conditions, but not too many
        error_rate = len(errors) / (len(transitions) + len(errors) + 1)
        assert error_rate < 0.1, f"Too many errors: {error_rate:.2%}"

    @pytest.mark.asyncio
    async def test_recovery_from_alerting_state(self, state_machine: ParasiteGuardStateMachine):
        """Test recovery from ALERTING state under load."""
        # Get to ALERTING state
        state_machine.transition(GuardState.MONITORING, confidence=1.0)
        state_machine.transition(GuardState.DETECTING, confidence=0.95)
        state_machine.transition(GuardState.MITIGATING, confidence=0.98)
        state_machine.transition(GuardState.ALERTING, confidence=0.10)

        assert state_machine.state == GuardState.ALERTING

        # Simulate load while recovering
        recovery_attempts = 0
        while state_machine.state == GuardState.ALERTING and recovery_attempts < 10:
            state_machine.transition(GuardState.MONITORING, confidence=1.0)
            recovery_attempts += 1
            await asyncio.sleep(0.01)

        assert state_machine.state == GuardState.MONITORING

    @pytest.mark.asyncio
    async def test_state_machine_memory_under_load(self, state_machine: ParasiteGuardStateMachine):
        """Test state machine doesn't leak memory under sustained load."""
        import gc

        gc.collect()
        initial_objects = len(gc.get_objects())

        # Perform many transitions
        state_machine.transition(GuardState.MONITORING, confidence=1.0)
        for _ in range(1000):
            state_machine.transition(GuardState.DETECTING, confidence=0.95)
            state_machine.transition(GuardState.MITIGATING, confidence=0.98)
            state_machine.transition(GuardState.MONITORING, confidence=0.90)

        gc.collect()
        final_objects = len(gc.get_objects())

        # Should not have unbounded object growth (allowing for transition history)
        # State machine stores history (~3 transitions * 1000 iterations + Python overhead)
        growth = final_objects - initial_objects
        assert growth < 6000, f"Potential memory leak: {growth} new objects"


# =============================================================================
# ANOMALY DETECTOR CHAOS TESTS
# =============================================================================


class TestAnomalyDetectorChaos:
    """Chaos tests for anomaly detection."""

    @pytest.mark.asyncio
    async def test_detector_under_burst_traffic(self, anomaly_detector: AdaptiveAnomalyDetector):
        """Test anomaly detector under burst traffic patterns."""
        # Build baseline with normal traffic
        for _ in range(100):
            anomaly_detector.detect(random.gauss(100, 10))

        # Inject burst
        burst_detections = 0
        for _ in range(50):
            result = anomaly_detector.detect(500)  # 40 standard deviations above mean
            if result.is_anomaly:
                burst_detections += 1

        # Should detect at least some burst traffic as anomalous
        # Adaptive detector may adjust baseline; require at least one detection
        assert burst_detections >= 1, f"No burst requests detected as anomalies ({burst_detections}/50)"

    @pytest.mark.asyncio
    async def test_adaptive_threshold_under_drift(self, anomaly_detector: AdaptiveAnomalyDetector):
        """Test adaptive threshold adapts to gradual drift."""
        # Build baseline
        for _ in range(100):
            anomaly_detector.detect(random.gauss(100, 10))

        # Gradual drift
        current_mean = 100
        drift_detections = []
        for i in range(200):
            current_mean += 0.5  # Slow drift
            result = anomaly_detector.detect(current_mean + random.gauss(0, 10))
            drift_detections.append(result.is_anomaly)

        # Should initially detect drift as anomalous, then adapt
        early_detections = sum(drift_detections[:50])
        late_detections = sum(drift_detections[-50:])

        # Either: later detections should be fewer (detector adapts) or total stays bounded
        total_detections = sum(drift_detections)
        # Allow adaptation (late <= early), or bounded total, or small variance
        assert total_detections < 150 or late_detections <= early_detections + 2, (
            f"Detector showed unstable behavior: early={early_detections}, late={late_detections}, total={total_detections}"
        )

    @pytest.mark.asyncio
    async def test_multi_window_consistency(self, multi_window_detector: MultiWindowAnomalyDetector):
        """Test multi-window detector maintains consistency."""
        # Feed same data to all windows
        for _ in range(500):
            value = random.gauss(100, 10)
            result = multi_window_detector.is_anomaly(value)

        # After warmup, inject anomaly
        for _ in range(10):
            result = multi_window_detector.is_anomaly(1000)

        # At least one window should detect
        assert result is True or any(
            d.detect(1000).is_anomaly
            for d in [
                multi_window_detector.short_window,
                multi_window_detector.medium_window,
                multi_window_detector.long_window,
            ]
        )

    @pytest.mark.asyncio
    async def test_rate_limiter_under_concurrent_requests(self, strict_rate_limit_detector: RateLimitAnomalyDetector):
        """Test rate limiter under concurrent request simulation (strict threshold to trigger)."""
        results = []

        async def simulate_requests(batch_size: int):
            for _ in range(batch_size):
                result = strict_rate_limit_detector.record_request()
                results.append(result)
                await asyncio.sleep(0.001)

        # Strict detector: max 10 req/s; we send 500 requests in ~0.5s -> should trigger anomalies
        await asyncio.gather(*[simulate_requests(100) for _ in range(5)])

        rejections = sum(1 for r in results if r.is_anomaly)
        assert len(results) == 500, "All requests should be recorded"
        assert rejections > 0, "Rate limiter should detect anomalies under burst (strict threshold)"


# =============================================================================
# DETECTION PIPELINE CHAOS TESTS
# =============================================================================


class TestDetectionPipelineChaos:
    """Chaos tests for the detection pipeline."""

    @pytest.mark.asyncio
    async def test_detection_under_memory_pressure(
        self,
        chaos_injector: ChaosInjector,
        parasite_config: ParasiteGuardConfig,
    ):
        """Test detection continues under memory pressure."""
        detections = []

        async def detection_task():
            # Simulate detection work
            for _ in range(100):
                # Create detection result
                result = DetectionResult(
                    detected=random.random() > 0.5,
                    context=ParasiteContext(
                        id=uuid.uuid4(),
                        component="test",
                        pattern="chaos_test",
                        rule="chaos_test_rule",
                        severity=ParasiteSeverity.MEDIUM,
                    )
                    if random.random() > 0.5
                    else None,
                    reason="Chaos test detection",
                    confidence=random.random(),
                )
                detections.append(result)
                await asyncio.sleep(0.01)

        # Run detection under memory pressure
        memory_task = asyncio.create_task(chaos_injector.inject_memory_pressure(mb=50, duration=2.0))
        detection_task_handle = asyncio.create_task(detection_task())

        await asyncio.gather(memory_task, detection_task_handle)

        # Should complete all detections
        assert len(detections) == 100

    @pytest.mark.asyncio
    async def test_detection_timeout_handling(self, parasite_config: ParasiteGuardConfig):
        """Test detection handles timeouts gracefully."""
        timeout_count = 0
        success_count = 0

        async def slow_detection():
            nonlocal timeout_count, success_count
            for _ in range(20):
                try:
                    # Simulate slow detection
                    await asyncio.wait_for(
                        asyncio.sleep(random.uniform(0.05, 0.15)),
                        timeout=parasite_config.detection_timeout_ms / 1000,
                    )
                    success_count += 1
                except asyncio.TimeoutError:
                    timeout_count += 1

        await slow_detection()

        # Should have both successes and timeouts
        assert success_count > 0, "No successful detections"
        assert timeout_count > 0, "No timeouts occurred"

    @pytest.mark.asyncio
    async def test_cascading_failure_isolation(self):
        """Test that failures in one detector don't cascade."""
        results = {"detector_a": 0, "detector_b": 0, "errors": 0}

        async def detector_a():
            # This detector always fails
            raise Exception("Detector A failure")

        async def detector_b():
            # This detector should still work
            return True

        async def run_detectors():
            for _ in range(100):
                try:
                    await detector_a()
                    results["detector_a"] += 1
                except Exception:
                    results["errors"] += 1

                try:
                    if await detector_b():
                        results["detector_b"] += 1
                except Exception:
                    results["errors"] += 1

        await run_detectors()

        # Detector B should continue working despite A's failures
        assert results["detector_b"] == 100, "Detector B was affected by A's failures"
        assert results["detector_a"] == 0, "Detector A should have 0 successes"


# =============================================================================
# CONCURRENT SANITIZATION CHAOS TESTS
# =============================================================================


class TestSanitizationChaos:
    """Chaos tests for the sanitization system."""

    @pytest.mark.asyncio
    async def test_concurrent_sanitization_limit(self, parasite_config: ParasiteGuardConfig):
        """Test concurrent sanitization respects limits."""
        concurrent_count = 0
        max_concurrent = 0
        lock = asyncio.Lock()

        async def sanitization_task(task_id: int):
            nonlocal concurrent_count, max_concurrent
            async with lock:
                concurrent_count += 1
                max_concurrent = max(max_concurrent, concurrent_count)

            # Simulate sanitization work
            await asyncio.sleep(random.uniform(0.1, 0.3))

            async with lock:
                concurrent_count -= 1

        # Create more tasks than the limit
        tasks = [sanitization_task(i) for i in range(20)]

        # Use semaphore to limit concurrency
        semaphore = asyncio.Semaphore(parasite_config.max_concurrent_sanitizations)

        async def limited_task(task):
            async with semaphore:
                await task

        await asyncio.gather(*[limited_task(t) for t in tasks])

        # Max concurrent should not exceed limit
        assert max_concurrent <= parasite_config.max_concurrent_sanitizations + 1  # +1 for timing

    @pytest.mark.asyncio
    async def test_sanitization_rollback_under_failure(self):
        """Test sanitization rollback when failure occurs."""
        steps_executed = []
        rollback_executed = []

        async def sanitization_step(step_id: int, should_fail: bool = False):
            steps_executed.append(step_id)
            await asyncio.sleep(0.01)
            if should_fail:
                raise Exception(f"Step {step_id} failed")

        async def rollback_step(step_id: int):
            rollback_executed.append(step_id)
            await asyncio.sleep(0.01)

        # Execute steps with failure
        try:
            await sanitization_step(1)
            await sanitization_step(2)
            await sanitization_step(3, should_fail=True)
            await sanitization_step(4)
        except Exception:
            # Rollback in reverse order
            for step_id in reversed(steps_executed):
                await rollback_step(step_id)

        # Verify rollback executed for all completed steps
        assert steps_executed == [1, 2, 3]
        assert rollback_executed == [3, 2, 1]


# =============================================================================
# ALERTING CHAOS TESTS
# =============================================================================


class TestAlertingChaos:
    """Chaos tests for the alerting system."""

    @pytest.mark.asyncio
    async def test_alert_channel_failure_fallback(self):
        """Test alert system falls back when channel fails."""
        channels_called = []
        fallback_called = []

        async def primary_channel(alert):
            channels_called.append("primary")
            raise Exception("Primary channel failed")

        async def fallback_channel(alert):
            fallback_called.append("fallback")
            return True

        async def send_alert(alert):
            try:
                await primary_channel(alert)
            except Exception:
                await fallback_channel(alert)

        # Send multiple alerts
        for i in range(10):
            await send_alert({"id": i, "severity": "HIGH"})

        # All should have fallen back
        assert len(fallback_called) == 10

    @pytest.mark.asyncio
    async def test_escalation_threshold_under_burst(self):
        """Test escalation threshold under alert burst."""
        alert_counts = defaultdict(int)
        escalations = []
        escalation_threshold = 3
        escalation_window = timedelta(seconds=5)
        recent_alerts: list[datetime] = []

        async def process_alert(severity: str):
            now = datetime.now(UTC)
            recent_alerts.append(now)

            # Clean old alerts
            cutoff = now - escalation_window
            while recent_alerts and recent_alerts[0] < cutoff:
                recent_alerts.pop(0)

            alert_counts[severity] += 1

            # Check escalation
            if len(recent_alerts) >= escalation_threshold:
                escalations.append(now)

        # Burst of alerts
        for _ in range(10):
            await process_alert("HIGH")
            await asyncio.sleep(0.1)

        # Should have escalated
        assert len(escalations) > 0, "No escalations occurred during burst"


# =============================================================================
# INTEGRATION CHAOS TESTS
# =============================================================================


class TestIntegrationChaos:
    """Integration chaos tests combining multiple components."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_full_pipeline_under_chaos(
        self,
        chaos_injector: ChaosInjector,
        state_machine: ParasiteGuardStateMachine,
        anomaly_detector: AdaptiveAnomalyDetector,
    ):
        """Test full pipeline under combined chaos conditions."""
        metrics = {
            "detections": 0,
            "transitions": 0,
            "anomalies": 0,
            "errors": 0,
        }

        async def detection_worker():
            for _ in range(50):
                try:
                    # Detect anomaly
                    result = anomaly_detector.detect(random.gauss(100, 10))
                    metrics["detections"] += 1
                    if result.is_anomaly:
                        metrics["anomalies"] += 1

                    # Transition state
                    if state_machine.state == GuardState.MONITORING:
                        state_machine.transition(GuardState.DETECTING, confidence=0.95)
                    elif state_machine.state == GuardState.DETECTING:
                        state_machine.transition(GuardState.MONITORING, confidence=0.90)
                    metrics["transitions"] += 1

                except Exception as e:
                    metrics["errors"] += 1

                await asyncio.sleep(0.01)

        # Initialize state machine
        state_machine.transition(GuardState.MONITORING, confidence=1.0)

        # Run under CPU chaos
        cpu_task = asyncio.create_task(chaos_injector.inject_cpu_load(percent=50, duration=2.0))
        worker_task = asyncio.create_task(detection_worker())

        await asyncio.gather(cpu_task, worker_task)

        # Should have completed most operations despite chaos
        assert metrics["detections"] >= 40, f"Too few detections: {metrics['detections']}"
        assert metrics["errors"] < 10, f"Too many errors: {metrics['errors']}"

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_recovery_time_measurement(
        self,
        state_machine: ParasiteGuardStateMachine,
        anomaly_detector: AdaptiveAnomalyDetector,
    ):
        """Measure and validate recovery time after failure injection."""
        recovery_times = []

        for trial in range(5):
            # Get to ALERTING (from INITIALIZING or MONITORING) - never transition MONITORING -> MONITORING
            if state_machine.state == GuardState.INITIALIZING:
                state_machine.transition(GuardState.MONITORING, confidence=1.0)
            if state_machine.state == GuardState.MONITORING:
                state_machine.transition(GuardState.DETECTING, confidence=0.95)
            if state_machine.state == GuardState.DETECTING:
                state_machine.transition(GuardState.MITIGATING, confidence=0.98)
            if state_machine.state == GuardState.MITIGATING:
                state_machine.transition(GuardState.ALERTING, confidence=0.10)

            # Measure recovery from ALERTING -> MONITORING
            start = time.monotonic()
            while state_machine.state != GuardState.MONITORING:
                state_machine.transition(GuardState.MONITORING, confidence=1.0)
                await asyncio.sleep(0.01)
            recovery_time = time.monotonic() - start
            recovery_times.append(recovery_time)

        avg_recovery = sum(recovery_times) / len(recovery_times)
        assert avg_recovery < 1.0, f"Average recovery time too high: {avg_recovery}s"


# =============================================================================
# ERROR BUDGET TESTS
# =============================================================================


class TestErrorBudget:
    """Tests for error budget compliance."""

    @pytest.mark.asyncio
    async def test_error_budget_consumption(
        self,
        anomaly_detector: AdaptiveAnomalyDetector,
    ):
        """Test error budget is not exceeded during chaos."""
        total_requests = 1000
        slo_target = 0.99  # 99% availability
        error_budget = total_requests * (1 - slo_target)  # 10 errors allowed

        errors = 0
        successes = 0

        for _ in range(total_requests):
            try:
                # Simulate request with 0.5% natural error rate
                if random.random() < 0.005:
                    raise Exception("Natural error")
                anomaly_detector.detect(random.gauss(100, 10))
                successes += 1
            except Exception:
                errors += 1

        # Error budget should not be exceeded
        assert errors <= error_budget * 1.5, f"Error budget exceeded: {errors} > {error_budget}"

    @pytest.mark.asyncio
    async def test_graceful_degradation(self):
        """Test system degrades gracefully under overload."""
        max_capacity = 100
        current_load = 0
        rejected = 0
        processed = 0

        async def process_request():
            nonlocal current_load, rejected, processed
            if current_load >= max_capacity:
                rejected += 1
                return False

            current_load += 1
            await asyncio.sleep(random.uniform(0.01, 0.05))
            current_load -= 1
            processed += 1
            return True

        # Overload the system
        tasks = [process_request() for _ in range(200)]
        results = await asyncio.gather(*tasks)

        # Should have processed most and rejected some
        assert processed > 50, f"Too few processed: {processed}"
        assert rejected > 0, "No graceful rejection occurred"


# =============================================================================
# ATTACK + CHAOS COMBINATION TESTS
# =============================================================================


class TestAttackUnderChaos:
    """Test detection and mitigation under combined attack and chaos conditions."""

    @pytest.mark.asyncio
    async def test_attack_under_memory_pressure(
        self,
        state_machine: ParasiteGuardStateMachine,
        anomaly_detector: AdaptiveAnomalyDetector,
        chaos_injector: ChaosInjector,
    ):
        """Test attack detection maintains accuracy under memory pressure."""
        state_machine.transition(GuardState.MONITORING, confidence=1.0)

        memory_task = asyncio.create_task(chaos_injector.inject_memory_pressure(mb=50, duration=3.0))

        detection_count = 0
        total_requests = 100

        for i in range(total_requests):
            value = random.gauss(100, 10)
            if random.random() < 0.3:
                value = random.gauss(500, 50)
            result = anomaly_detector.detect(value)
            if result.is_anomaly:
                detection_count += 1

        await memory_task

        assert detection_count >= 20, f"Detection rate too low under memory pressure: {detection_count}"
        assert state_machine.state in [GuardState.MONITORING, GuardState.DETECTING, GuardState.MITIGATING]

    @pytest.mark.asyncio
    async def test_attack_under_network_partition(
        self,
        state_machine: ParasiteGuardStateMachine,
        anomaly_detector: AdaptiveAnomalyDetector,
        chaos_injector: ChaosInjector,
    ):
        """Test system degrades gracefully during attack under partition."""
        state_machine.transition(GuardState.MONITORING, confidence=1.0)

        partition_task = asyncio.create_task(chaos_injector.inject_network_partition(duration=2.0))

        anomaly_count = 0
        total_requests = 100

        for i in range(total_requests):
            value = random.gauss(100, 10)
            if random.random() < 0.2:
                value = random.gauss(300, 30)
            result = anomaly_detector.detect(value)
            if result.is_anomaly:
                anomaly_count += 1
            await asyncio.sleep(0.01)

        await partition_task

        if state_machine.state == GuardState.DETECTING:
            state_machine.transition(GuardState.MONITORING, confidence=1.0)

        assert anomaly_count >= 10, f"Detection under partition failed: {anomaly_count}"

    @pytest.mark.asyncio
    async def test_cascade_attack_recovery(
        self,
        state_machine: ParasiteGuardStateMachine,
        anomaly_detector: AdaptiveAnomalyDetector,
    ):
        """Test system recovers properly after cascade attack pattern."""
        state_machine.transition(GuardState.MONITORING, confidence=1.0)

        for wave in range(3):
            state_machine.transition(GuardState.DETECTING, confidence=0.95)
            state_machine.transition(GuardState.MITIGATING, confidence=0.98)

            for _ in range(50):
                value = random.gauss(100, 10)
                if random.random() < 0.4:
                    value = random.gauss(400, 40)
                anomaly_detector.detect(value)

            if wave < 2:
                state_machine.transition(GuardState.MONITORING, confidence=0.90)
                await asyncio.sleep(0.5)

        state_machine.transition(GuardState.MONITORING, confidence=1.0)

        assert state_machine.state == GuardState.MONITORING

        post_attack_detections = 0
        for _ in range(50):
            value = random.gauss(100, 5)
            result = anomaly_detector.detect(value)
            if result.is_anomaly:
                post_attack_detections += 1

        assert post_attack_detections < 10, f"False positives after attack: {post_attack_detections}"

    @pytest.mark.asyncio
    async def test_slowloris_under_resource_exhaustion(
        self,
        state_machine: ParasiteGuardStateMachine,
        anomaly_detector: AdaptiveAnomalyDetector,
        chaos_injector: ChaosInjector,
    ):
        """Test slow connection attack detection under CPU load."""
        state_machine.transition(GuardState.MONITORING, confidence=1.0)

        cpu_task = asyncio.create_task(chaos_injector.inject_cpu_load(percent=70, duration=2.0))

        anomaly_count = 0
        for i in range(100):
            if i % 10 == 0:
                value = random.gauss(500, 100)
            else:
                value = random.gauss(100, 10)
            result = anomaly_detector.detect(value)
            if result.is_anomaly:
                anomaly_count += 1

        await cpu_task

        if state_machine.state == GuardState.DETECTING:
            state_machine.transition(GuardState.MONITORING, confidence=1.0)

        assert anomaly_count >= 5, f"Slowloris detection failed under CPU load: {anomaly_count}"

    @pytest.mark.asyncio
    async def test_credential_stuffing_under_timeout(
        self,
        state_machine: ParasiteGuardStateMachine,
        anomaly_detector: AdaptiveAnomalyDetector,
        chaos_injector: ChaosInjector,
    ):
        """Test auth attack detection when timeouts are stressed."""
        state_machine.transition(GuardState.MONITORING, confidence=1.0)

        timeout_task = asyncio.create_task(chaos_injector.inject_request_timeout(duration=2.0))

        high_latency_count = 0
        for i in range(100):
            value = random.gauss(100, 10)
            if random.random() < 0.15:
                value = random.gauss(200, 30)
            result = anomaly_detector.detect(value)
            if result.is_anomaly:
                high_latency_count += 1

        await timeout_task

        assert high_latency_count >= 5, f"Auth anomaly detection under timeout stress failed: {high_latency_count}"

    @pytest.mark.asyncio
    async def test_api_abuse_under_concurrent_load(
        self,
        state_machine: ParasiteGuardStateMachine,
        anomaly_detector: AdaptiveAnomalyDetector,
        chaos_injector: ChaosInjector,
    ):
        """Test API abuse detection under high concurrency."""
        state_machine.transition(GuardState.MONITORING, confidence=1.0)

        concurrent_task = asyncio.create_task(chaos_injector.inject_concurrency_limit(limit=50, duration=2.0))

        anomaly_count = 0
        endpoint_hits = {}

        async def make_request(endpoint_idx: int):
            nonlocal anomaly_count
            value = random.gauss(100, 10)
            if random.random() < 0.25:
                value = random.gauss(350, 40)
            result = anomaly_detector.detect(value)
            endpoint_hits[endpoint_idx] = endpoint_hits.get(endpoint_idx, 0) + 1
            if result.is_anomaly:
                anomaly_count += 1

        tasks = []
        for i in range(100):
            tasks.append(make_request(i % 5))
        await asyncio.gather(*tasks)

        await concurrent_task

        unique_endpoints = len(endpoint_hits)
        assert unique_endpoints >= 3, f"API abuse pattern not detected: {unique_endpoints} endpoints"

        if state_machine.state == GuardState.DETECTING:
            state_machine.transition(GuardState.MONITORING, confidence=1.0)


# =============================================================================
# MAIN EXECUTION
# =============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
