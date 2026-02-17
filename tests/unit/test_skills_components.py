"""Unit tests for GRID Skills execution tracker."""

import os
import time

import pytest


class TestSkillExecutionTracker:
    """Unit tests for execution tracking functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset singleton for each test."""
        from grid.skills.execution_tracker import SkillExecutionTracker

        SkillExecutionTracker._instance = None
        yield

    def test_singleton_pattern(self):
        """Verify tracker uses singleton pattern."""
        from grid.skills.execution_tracker import SkillExecutionTracker

        t1 = SkillExecutionTracker.get_instance()
        t2 = SkillExecutionTracker.get_instance()

        assert t1 is t2

    def test_track_execution_returns_record(self):
        """Verify track_execution returns a valid record."""
        from grid.skills.execution_tracker import ExecutionStatus, SkillExecutionTracker

        tracker = SkillExecutionTracker.get_instance()

        record = tracker.track_execution(
            skill_id="test.unit_test", input_args={"data": "test"}, output={"result": "success"}, execution_time_ms=50
        )

        assert record is not None
        assert record.skill_id == "test.unit_test"
        assert record.execution_time_ms == 50
        assert record.status == ExecutionStatus.SUCCESS

    def test_track_execution_with_error(self):
        """Verify error status is set when error provided."""
        from grid.skills.execution_tracker import ExecutionStatus, SkillExecutionTracker

        tracker = SkillExecutionTracker.get_instance()

        record = tracker.track_execution(
            skill_id="test.error_test",
            input_args={},
            output=None,
            error="Test error",
            status=ExecutionStatus.FAILURE,  # Explicit status
            execution_time_ms=10,
        )

        assert record.status == ExecutionStatus.FAILURE
        assert record.error == "Test error"

    def test_execution_history_limit(self):
        """Verify execution history respects limit."""
        from grid.skills.execution_tracker import SkillExecutionTracker

        tracker = SkillExecutionTracker.get_instance()

        # Track multiple executions
        for i in range(10):
            tracker.track_execution(skill_id="test.history", input_args={"i": i}, output={}, execution_time_ms=i)

        history = tracker.get_execution_history(skill_id="test.history", limit=5)
        assert len(history) <= 5

    def test_pending_count(self):
        """Verify pending count tracking."""
        from grid.skills.execution_tracker import SkillExecutionTracker

        os.environ["GRID_SKILLS_BATCH_SIZE"] = "100"  # High batch to accumulate
        tracker = SkillExecutionTracker()  # Fresh instance

        initial = tracker.get_pending_count()

        tracker.track_execution(skill_id="test.pending", input_args={}, output={}, execution_time_ms=1)

        assert tracker.get_pending_count() >= initial

    def test_graceful_degradation_without_inventory(self):
        """Verify tracker works even if inventory unavailable."""
        from grid.skills.execution_tracker import SkillExecutionTracker

        tracker = SkillExecutionTracker()
        tracker._inventory = None
        tracker._inventory_available = False

        # Should not raise
        record = tracker.track_execution(skill_id="test.degradation", input_args={}, output={}, execution_time_ms=1)

        assert record is not None

    def test_force_flush(self):
        """Verify force_flush works."""
        from grid.skills.execution_tracker import SkillExecutionTracker

        tracker = SkillExecutionTracker.get_instance()

        tracker.track_execution(skill_id="test.flush", input_args={}, output={}, execution_time_ms=1)

        # Should not raise
        tracker.force_flush()


class TestIntelligenceTracker:
    """Unit tests for intelligence tracking functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset singleton for each test."""
        from grid.skills.intelligence_tracker import IntelligenceTracker

        IntelligenceTracker._instance = None
        yield

    def test_singleton_pattern(self):
        """Verify tracker uses singleton pattern."""
        from grid.skills.intelligence_tracker import IntelligenceTracker

        t1 = IntelligenceTracker.get_instance()
        t2 = IntelligenceTracker.get_instance()

        assert t1 is t2

    def test_track_decision_returns_record(self):
        """Verify track_decision returns a valid record."""
        from grid.skills.intelligence_tracker import DecisionType, IntelligenceTracker

        tracker = IntelligenceTracker.get_instance()

        record = tracker.track_decision(
            skill_id="test.decision",
            decision_type=DecisionType.ROUTING,
            context={"test": True},
            confidence=0.85,
            rationale="Test decision",
            alternatives=["A", "B"],
            outcome="success",
        )

        assert record is not None
        assert record.skill_id == "test.decision"
        assert record.confidence == 0.85
        assert record.decision_type == DecisionType.ROUTING

    def test_get_intelligence_patterns(self):
        """Verify intelligence patterns aggregation."""
        from grid.skills.intelligence_tracker import DecisionType, IntelligenceTracker

        tracker = IntelligenceTracker.get_instance()

        # Track multiple decisions
        for i in range(5):
            tracker.track_decision(
                skill_id="test.patterns",
                decision_type=DecisionType.ADAPTATION,
                context={},
                confidence=0.7 + i * 0.05,
                rationale=f"Decision {i}",
                alternatives=[],
                outcome="success",
            )

        patterns = tracker.get_intelligence_patterns("test.patterns")

        assert "total_decisions" in patterns
        assert patterns["total_decisions"] >= 5

    def test_get_recent_decisions(self):
        """Verify recent decisions retrieval."""
        from grid.skills.intelligence_tracker import DecisionType, IntelligenceTracker

        tracker = IntelligenceTracker.get_instance()

        tracker.track_decision(
            skill_id="test.recent",
            decision_type=DecisionType.FALLBACK,
            context={},
            confidence=0.6,
            rationale="Recent test",
            alternatives=[],
            outcome="success",
        )

        recent = tracker.get_recent_decisions("test.recent", limit=10)
        assert len(recent) >= 1


class TestPerformanceGuard:
    """Unit tests for performance regression detection."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset singleton for each test."""
        from grid.skills.performance_guard import PerformanceGuard

        PerformanceGuard._instance = None
        yield

    def test_singleton_pattern(self):
        """Verify guard uses singleton pattern."""
        from grid.skills.performance_guard import PerformanceGuard

        g1 = PerformanceGuard.get_instance()
        g2 = PerformanceGuard.get_instance()

        assert g1 is g2

    def test_check_execution_no_baseline(self):
        """Verify no alert when no baseline exists."""
        from grid.skills.performance_guard import PerformanceGuard

        guard = PerformanceGuard.get_instance()

        # No baseline for this skill
        alert = guard.check_execution("test.no_baseline", 100)

        assert alert is None

    def test_regression_threshold(self):
        """Verify regression threshold is configurable."""
        from grid.skills.performance_guard import PerformanceGuard

        guard = PerformanceGuard.get_instance()

        # Default threshold is 1.2
        assert guard.REGRESSION_THRESHOLD == 1.2

    def test_alert_deduplication(self):
        """Verify alert deduplication window."""
        from grid.skills.performance_guard import PerformanceGuard

        guard = PerformanceGuard.get_instance()

        # Record an alert for skill
        guard._recent_alerts["test.dedupe"] = time.time()

        # Should be deduplicated
        assert guard._is_deduplicated("test.dedupe")

    def test_get_recent_alerts(self):
        """Verify recent alerts retrieval."""
        from grid.skills.performance_guard import PerformanceGuard

        guard = PerformanceGuard.get_instance()

        # Add test alert
        guard._recent_alerts["test.alert"] = time.time()

        alerts = guard.get_recent_alerts()
        assert isinstance(alerts, list)


class TestSignalClassification:
    """Unit tests for signal classification."""

    def test_classify_valid_execution(self):
        """Verify valid execution classified as signal."""
        from grid.skills.execution_tracker import ExecutionStatus, SkillExecutionRecord
        from grid.skills.signal_classification import SignalClassifier, SignalType

        classifier = SignalClassifier()

        record = SkillExecutionRecord(
            skill_id="test.classify",
            timestamp=time.time(),
            status=ExecutionStatus.SUCCESS,
            input_args={"test": True},
            output={"result": "ok"},
            error=None,
            execution_time_ms=50,
            confidence_score=0.9,
            fallback_used=False,
        )

        result = classifier.classify(record, baseline={"p50_ms": 100})

        assert not result.is_noise
        assert result.signal_type == SignalType.VALID_EXECUTION.value
        assert result.action == "preserve"

    def test_classify_noise_timeout(self):
        """Verify timeout classified as noise."""
        from grid.skills.execution_tracker import ExecutionStatus, SkillExecutionRecord
        from grid.skills.signal_classification import SignalClassifier

        classifier = SignalClassifier()

        record = SkillExecutionRecord(
            skill_id="test.timeout",
            timestamp=time.time(),
            status=ExecutionStatus.FAILURE,
            input_args={},
            output=None,
            error="Connection timeout",
            execution_time_ms=65000,
            confidence_score=None,
            fallback_used=False,
        )

        result = classifier.classify(record)

        assert result.is_noise
        assert result.action == "filter"

    def test_classify_regression(self):
        """Verify genuine regression detected."""
        from grid.skills.execution_tracker import ExecutionStatus, SkillExecutionRecord
        from grid.skills.signal_classification import SignalClassifier, SignalType

        classifier = SignalClassifier()

        record = SkillExecutionRecord(
            skill_id="test.regression",
            timestamp=time.time(),
            status=ExecutionStatus.SUCCESS,
            input_args={"test": True},
            output={},
            error=None,
            execution_time_ms=200,  # Much higher than baseline
            confidence_score=0.8,
            fallback_used=False,
        )

        result = classifier.classify(record, baseline={"p50_ms": 50})

        assert result.signal_type == SignalType.GENUINE_REGRESSION.value
        assert result.action == "alert"


class TestNSRTracker:
    """Unit tests for NSR tracking."""

    def test_initial_nsr_zero(self):
        """Verify initial NSR is zero."""
        from grid.skills.signal_classification import NSRTracker

        tracker = NSRTracker()
        assert tracker.get_current_nsr() == 0.0

    def test_nsr_calculation(self):
        """Verify NSR calculation."""
        from grid.skills.signal_classification import ClassificationResult, NSRTracker

        tracker = NSRTracker()

        # 3 signals, 1 noise = 25% NSR
        for _ in range(3):
            tracker.record_classification(
                ClassificationResult(
                    signal_type="valid",
                    is_noise=False,
                    confidence=0.9,
                    nsr_contribution=0,
                    action="preserve",
                    reason="",
                )
            )

        tracker.record_classification(
            ClassificationResult(
                signal_type="noise", is_noise=True, confidence=0.5, nsr_contribution=0.1, action="filter", reason=""
            )
        )

        nsr = tracker.get_current_nsr()
        assert 0.2 <= nsr <= 0.3  # Should be ~25%

    def test_noise_breakdown(self):
        """Verify noise breakdown tracking."""
        from grid.skills.signal_classification import ClassificationResult, NoiseType, NSRTracker

        tracker = NSRTracker()

        tracker.record_classification(
            ClassificationResult(
                signal_type=NoiseType.TIMEOUT_SPIKE.value,
                is_noise=True,
                confidence=0.5,
                nsr_contribution=0.1,
                action="filter",
                reason="",
            )
        )

        breakdown = tracker.get_noise_breakdown()
        assert NoiseType.TIMEOUT_SPIKE.value in breakdown


class TestPersistenceVerifier:
    """Unit tests for persistence verification."""

    def test_run_all_checks(self):
        """Verify all checks run without error."""
        from grid.skills.persistence_verifier import PersistenceVerifier

        verifier = PersistenceVerifier()
        checks = verifier.run_all_checks()

        assert "execution_integrity" in checks
        assert "intelligence_integrity" in checks
        assert "baseline_consistency" in checks
        assert "schema_version" in checks
        assert "foreign_keys" in checks
        assert "data_freshness" in checks

    def test_schema_version_check(self):
        """Verify schema version check."""
        from grid.skills.persistence_verifier import PersistenceVerifier

        verifier = PersistenceVerifier()
        check = verifier._check_schema_version()

        # Should pass with version 2
        assert check.passed
        assert "2" in check.details


class TestDiagnostics:
    """Unit tests for diagnostics system."""

    def test_run_full_diagnostics(self):
        """Verify diagnostics run without error."""
        from grid.skills.diagnostics import SkillsDiagnostics

        diag = SkillsDiagnostics()
        report = diag.run_full_diagnostics()

        assert report.timestamp > 0
        assert "registry" in report.component_statuses
        assert isinstance(report.recommendations, list)

    def test_check_components(self):
        """Verify component checking."""
        from grid.skills.diagnostics import SkillsDiagnostics

        diag = SkillsDiagnostics()
        statuses = diag._check_components()

        assert "registry" in statuses
        assert "execution_tracker" in statuses
        assert "inventory" in statuses
