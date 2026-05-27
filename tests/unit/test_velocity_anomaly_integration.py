"""Integration tests: high-drift signal → AnomalyDetector → VELOCITY_ANOMALY violation.

Tests the full pipeline that dispatch() wires together:
  VelocityTracker.track_event()
    → AnomalyDetector.check_velocity_anomaly()
    → EntityAttributionEngine.record_violation(VELOCITY_ANOMALY)

Also covers: EntityRecord.drift_score, update_drift(), effective_budget()
drift surcharge, and confidence-weighting.
"""

from __future__ import annotations

import pytest

from application.mothership.middleware.admission_gate import (
    DRIFT_SURCHARGE_THRESHOLD,
    EntityAttributionEngine,
    ViolationType,
)
from vection.core.velocity_tracker import VelocityTracker, VelocityTrackerRegistry
from vection.schemas.velocity_vector import VelocityVector
from vection.security.anomaly_detector import (
    AnomalyDetector,
    AnomalyDetectorConfig,
    AnomalyType,
    DetectionThresholds,
)

# ---------------------------------------------------------------------------
# ViolationType and BASE_PENALTIES
# ---------------------------------------------------------------------------


class TestVelocityAnomalyViolationType:
    def test_velocity_anomaly_exists(self) -> None:
        assert ViolationType.VELOCITY_ANOMALY == "velocity_anomaly"

    def test_velocity_anomaly_base_penalty(self) -> None:
        assert EntityAttributionEngine.BASE_PENALTIES[ViolationType.VELOCITY_ANOMALY] == 8

    def test_velocity_anomaly_in_base_penalties(self) -> None:
        assert ViolationType.VELOCITY_ANOMALY in EntityAttributionEngine.BASE_PENALTIES


# ---------------------------------------------------------------------------
# EntityRecord.drift_score and update_drift()
# ---------------------------------------------------------------------------


class TestUpdateDrift:
    def test_drift_score_defaults_to_zero(self) -> None:
        engine = EntityAttributionEngine()
        record = engine.get_record("entity-a")
        assert record.drift_score == pytest.approx(0.0)

    def test_update_drift_sets_score(self) -> None:
        engine = EntityAttributionEngine()
        engine.update_drift("entity-a", 0.75)
        assert engine.get_record("entity-a").drift_score == pytest.approx(0.75)

    def test_update_drift_clamps_above_one(self) -> None:
        engine = EntityAttributionEngine()
        engine.update_drift("entity-a", 1.5)
        assert engine.get_record("entity-a").drift_score == pytest.approx(1.0)

    def test_update_drift_clamps_below_zero(self) -> None:
        engine = EntityAttributionEngine()
        engine.update_drift("entity-a", -0.3)
        assert engine.get_record("entity-a").drift_score == pytest.approx(0.0)

    def test_update_drift_creates_record_if_absent(self) -> None:
        engine = EntityAttributionEngine()
        assert engine.peek_record("new-entity") is None
        engine.update_drift("new-entity", 0.5)
        assert engine.peek_record("new-entity") is not None


# ---------------------------------------------------------------------------
# effective_budget() drift surcharge
# ---------------------------------------------------------------------------


class TestEffectiveBudgetDriftSurcharge:
    def test_zero_drift_no_surcharge(self) -> None:
        engine = EntityAttributionEngine()
        engine.update_drift("e", 0.0)
        budget = engine.effective_budget("e", 100)
        assert budget == 100  # no penalty, no drift

    def test_drift_below_threshold_no_surcharge(self) -> None:
        engine = EntityAttributionEngine()
        engine.update_drift("e", 0.49)
        assert engine.effective_budget("e", 100) == 100

    def test_drift_at_threshold_no_surcharge(self) -> None:
        engine = EntityAttributionEngine()
        engine.update_drift("e", 0.5)
        assert engine.effective_budget("e", 100) == 100

    def test_drift_above_threshold_reduces_budget(self) -> None:
        engine = EntityAttributionEngine()
        engine.update_drift("e", 1.0)  # max drift → 20% surcharge
        budget = engine.effective_budget("e", 100)
        assert budget < 100
        assert budget == 80  # (1.0 - 0.5) * 0.4 = 0.20 reduction

    def test_drift_midpoint_surcharge(self) -> None:
        engine = EntityAttributionEngine()
        engine.update_drift("e", 0.75)  # (0.75 - 0.5) * 0.4 = 0.10 → 10% reduction
        budget = engine.effective_budget("e", 100)
        assert budget == 90

    def test_drift_surcharge_combined_with_penalty(self) -> None:
        engine = EntityAttributionEngine()
        engine.record_violation("e", ViolationType.BUDGET_EXCEEDED)  # 5 pts → 5% reduction
        engine.update_drift("e", 1.0)  # 20% surcharge
        budget = engine.effective_budget("e", 100)
        # total reduction = min(0.05 + 0.20, 0.90) = 0.25 → 75
        assert budget == 75

    def test_bannered_entity_always_zero(self) -> None:
        engine = EntityAttributionEngine(banner_threshold=1)
        # Force banner by exceeding threshold
        for _ in range(5):
            engine.record_violation("e", ViolationType.ORIGIN_DENIED)
        engine.update_drift("e", 0.0)
        assert engine.effective_budget("e", 100) == 0

    def test_floor_at_ten_percent(self) -> None:
        # Use a high banner_threshold so piling on penalty points doesn't ban the entity
        # before we can test the floor logic.
        engine = EntityAttributionEngine(banner_threshold=1000)
        engine.update_drift("e", 1.0)
        # Pile on penalty points to push total reduction to 90%
        for _ in range(18):
            engine.record_violation("e", ViolationType.ORIGIN_DENIED)  # 10 pts each
        budget = engine.effective_budget("e", 100)
        assert budget >= 10  # floor is max(1, base // 10)


# ---------------------------------------------------------------------------
# Confidence-weighted drift passed to update_drift
# ---------------------------------------------------------------------------


class TestDriftConfidenceWeighting:
    """Verifies that multiplying drift by confidence before update_drift() means
    low-observation entities don't trigger the surcharge prematurely."""

    def test_low_confidence_high_raw_drift_no_surcharge(self) -> None:
        tracker = VelocityTracker(session_id="t", history_size=100, direction_history_size=100)
        # 2 events → confidence = 0.1; even fully alternating → weighted drift = 0.1
        tracker.direction_sequence.append("A")
        tracker.history.append(object())  # type: ignore[arg-type]
        tracker.direction_sequence.append("B")
        tracker.history.append(object())  # type: ignore[arg-type]

        drift = tracker._calculate_drift()       # 1.0 (one transition, both different)
        confidence = tracker._calculate_confidence()  # 2/20 = 0.1
        weighted = drift * confidence

        engine = EntityAttributionEngine()
        engine.update_drift("e", weighted)
        assert engine.get_record("e").drift_score < 0.5  # below surcharge threshold

    def test_high_confidence_high_raw_drift_triggers_surcharge(self) -> None:
        tracker = VelocityTracker(session_id="t", history_size=100, direction_history_size=100)
        # 20 events alternating → confidence = 1.0, drift = 1.0, weighted = 1.0
        for i in range(20):
            tracker.direction_sequence.append("A" if i % 2 == 0 else "B")
            tracker.history.append(object())  # type: ignore[arg-type]

        drift = tracker._calculate_drift()
        confidence = tracker._calculate_confidence()
        weighted = drift * confidence

        engine = EntityAttributionEngine()
        engine.update_drift("e", weighted)
        record = engine.get_record("e")
        assert record.drift_score > 0.5
        assert engine.effective_budget("e", 100) < 100


# ---------------------------------------------------------------------------
# End-to-end: high-drift entity → DRIFT_ANOMALY → VELOCITY_ANOMALY violation
# ---------------------------------------------------------------------------


class TestAnomalyToViolationPipeline:
    """Drives the full pipeline without mocking the anomaly detector."""

    def _high_drift_velocity(self) -> VelocityVector:
        """Build a VelocityTracker with 20 fully alternating events and return
        the final VelocityVector."""
        tracker = VelocityTracker(session_id="entity-drift", history_size=100, direction_history_size=100)
        for i in range(20):
            tracker.track_event(
                {"action": "GET" if i % 2 == 0 else "POST", "query": "/a" if i % 2 == 0 else "/b"},
                event_type="request",
            )
        return tracker.current_velocity

    def _make_detector(self) -> AnomalyDetector:
        """Detector using default sensitivity (1.0) so thresholds equal their configured values."""
        return AnomalyDetector(
            AnomalyDetectorConfig(
                thresholds=DetectionThresholds(drift_threshold=0.7),
            )
        )

    def test_high_drift_triggers_drift_anomaly(self) -> None:
        velocity = self._high_drift_velocity()
        # Raw drift must exceed the detector threshold (0.7 at sensitivity=1.0)
        assert velocity.drift > 0.7

        alert = self._make_detector().check_velocity_anomaly(
            session_id="entity-drift",
            velocity_magnitude=velocity.magnitude,
            velocity_direction=velocity.direction.value,
            momentum=velocity.momentum,
            drift=velocity.drift,
        )
        assert alert is not None
        assert alert.anomaly_type == AnomalyType.DRIFT_ANOMALY

    def test_drift_anomaly_alert_records_violation(self) -> None:
        velocity = self._high_drift_velocity()
        alert = self._make_detector().check_velocity_anomaly(
            session_id="entity-drift",
            velocity_magnitude=velocity.magnitude,
            velocity_direction=velocity.direction.value,
            momentum=velocity.momentum,
            drift=velocity.drift,
        )
        assert alert is not None

        # Simulate what dispatch() does: record violation for MEDIUM, HIGH, or CRITICAL.
        from vection.security.anomaly_detector import AlertSeverity

        engine = EntityAttributionEngine()
        if alert.severity in (AlertSeverity.MEDIUM, AlertSeverity.HIGH, AlertSeverity.CRITICAL):
            engine.record_violation(
                "entity-drift",
                ViolationType.VELOCITY_ANOMALY,
                metadata={
                    "anomaly_type": alert.anomaly_type.value,
                    "severity": alert.severity.value,
                    "drift": velocity.drift,
                    "momentum": velocity.momentum,
                },
            )

        record = engine.get_record("entity-drift")
        velocity_violations = [v for v in record.violations if v.violation_type == ViolationType.VELOCITY_ANOMALY]
        assert len(velocity_violations) == 1
        assert velocity_violations[0].penalty_points == 8
        assert velocity_violations[0].metadata["anomaly_type"] == AnomalyType.DRIFT_ANOMALY.value

    def test_low_drift_produces_no_violation(self) -> None:
        """A stable entity (same direction throughout) must not trigger anomaly."""
        tracker = VelocityTracker(session_id="entity-stable", history_size=100, direction_history_size=100)
        for _ in range(20):
            tracker.track_event({"action": "GET", "query": "/api/health"}, event_type="request")
        velocity = tracker.current_velocity

        from vection.security.anomaly_detector import AlertSeverity

        alert = self._make_detector().check_velocity_anomaly(
            session_id="entity-stable",
            velocity_magnitude=velocity.magnitude,
            velocity_direction=velocity.direction.value,
            momentum=velocity.momentum,
            drift=velocity.drift,
        )

        engine = EntityAttributionEngine()
        if alert and alert.severity in (AlertSeverity.MEDIUM, AlertSeverity.HIGH, AlertSeverity.CRITICAL):
            engine.record_violation("entity-stable", ViolationType.VELOCITY_ANOMALY)

        record = engine.peek_record("entity-stable")
        velocity_violations = [
            v for v in (record.violations if record else []) if v.violation_type == ViolationType.VELOCITY_ANOMALY
        ]
        assert len(velocity_violations) == 0

    def test_full_pipeline_reduces_budget_for_high_drift_entity(self) -> None:
        """A high-drift entity ends up with reduced effective budget after the
        full confidence-weighted update."""
        velocity = self._high_drift_velocity()
        weighted_drift = velocity.drift * velocity.confidence

        engine = EntityAttributionEngine()
        engine.update_drift("entity-drift", weighted_drift)

        from vection.security.anomaly_detector import AlertSeverity

        alert = self._make_detector().check_velocity_anomaly(
            session_id="entity-drift",
            velocity_magnitude=velocity.magnitude,
            velocity_direction=velocity.direction.value,
            momentum=velocity.momentum,
            drift=velocity.drift,
        )
        if alert and alert.severity in (AlertSeverity.MEDIUM, AlertSeverity.HIGH, AlertSeverity.CRITICAL):
            engine.record_violation(
                "entity-drift",
                ViolationType.VELOCITY_ANOMALY,
                metadata={"anomaly_type": alert.anomaly_type.value, "severity": alert.severity.value},
            )

        budget = engine.effective_budget("entity-drift", 100)
        assert budget < 100


# ---------------------------------------------------------------------------
# Aggregate drift observability
# ---------------------------------------------------------------------------


class TestDriftSummary:
    def test_empty_engine_zero_summary(self) -> None:
        summary = EntityAttributionEngine().drift_summary()
        assert summary["tracked_entities"] == 0
        assert summary["mean_drift"] == pytest.approx(0.0)
        assert summary["max_drift"] == pytest.approx(0.0)
        assert summary["high_drift_count"] == 0
        assert summary["top_drifting"] == []

    def test_threshold_matches_enforcement_constant(self) -> None:
        summary = EntityAttributionEngine().drift_summary()
        assert summary["high_drift_threshold"] == DRIFT_SURCHARGE_THRESHOLD

    def test_mean_and_max(self) -> None:
        engine = EntityAttributionEngine()
        engine.update_drift("a", 0.2)
        engine.update_drift("b", 0.8)
        summary = engine.drift_summary()
        assert summary["tracked_entities"] == 2
        assert summary["mean_drift"] == pytest.approx(0.5)
        assert summary["max_drift"] == pytest.approx(0.8)

    def test_high_drift_count_uses_surcharge_threshold(self) -> None:
        engine = EntityAttributionEngine()
        engine.update_drift("below", DRIFT_SURCHARGE_THRESHOLD)  # not strictly above
        engine.update_drift("above1", 0.6)
        engine.update_drift("above2", 0.9)
        summary = engine.drift_summary()
        assert summary["high_drift_count"] == 2

    def test_top_drifting_ranked_descending(self) -> None:
        engine = EntityAttributionEngine()
        engine.update_drift("low", 0.1)
        engine.update_drift("high", 0.9)
        engine.update_drift("mid", 0.5)
        summary = engine.drift_summary(top_n=3)
        ids = [d["entity_id"] for d in summary["top_drifting"]]
        assert ids == ["high", "mid", "low"]

    def test_top_drifting_respects_top_n(self) -> None:
        engine = EntityAttributionEngine()
        for i in range(10):
            engine.update_drift(f"e{i}", i / 10.0)
        summary = engine.drift_summary(top_n=3)
        assert len(summary["top_drifting"]) == 3
        assert summary["top_drifting"][0]["entity_id"] == "e9"

    def test_top_n_zero_skips_ranking(self) -> None:
        engine = EntityAttributionEngine()
        engine.update_drift("a", 0.9)
        summary = engine.drift_summary(top_n=0)
        assert summary["top_drifting"] == []
        # Scalar aggregates still computed
        assert summary["max_drift"] == pytest.approx(0.9)

    def test_top_drifting_excludes_zero_drift(self) -> None:
        engine = EntityAttributionEngine()
        engine.update_drift("zero", 0.0)
        engine.update_drift("nonzero", 0.3)
        summary = engine.drift_summary(top_n=10)
        ids = [d["entity_id"] for d in summary["top_drifting"]]
        assert ids == ["nonzero"]
