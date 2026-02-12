"""Tests for learning coordinator."""

import pytest

from coinbase.learning_coordinator import LearningCoordinator
from coinbase.tracer import ExecutionOutcome


def test_record_execution_outcome_success():
    """Test recording successful execution outcome."""
    coordinator = LearningCoordinator()

    coordinator.record_execution_outcome(
        case_id="skill-123", trace_id="trace-abc", outcome=ExecutionOutcome.SUCCESS, duration_ms=500
    )

    stats = coordinator.get_skill_stats("skill-123")

    assert stats is not None
    assert stats.usage_count == 1
    assert stats.success_count == 1
    assert stats.total_latency_ms == 500
    assert stats.success_rate == 1.0


def test_record_execution_outcome_failure():
    """Test recording failed execution outcome."""
    coordinator = LearningCoordinator()

    coordinator.record_execution_outcome(
        case_id="skill-456",
        trace_id="trace-def",
        outcome=ExecutionOutcome.FAILURE,
        duration_ms=1000,
    )

    stats = coordinator.get_skill_stats("skill-456")

    assert stats is not None
    assert stats.usage_count == 1
    assert stats.success_count == 0
    assert stats.total_latency_ms == 1000
    assert stats.success_rate == 0.0


def test_multiple_executions():
    """Test tracking multiple executions for same skill."""
    coordinator = LearningCoordinator()

    # Record multiple executions
    coordinator.record_execution_outcome(
        case_id="skill-multi", trace_id="trace-1", outcome=ExecutionOutcome.SUCCESS, duration_ms=300
    )
    coordinator.record_execution_outcome(
        case_id="skill-multi", trace_id="trace-2", outcome=ExecutionOutcome.SUCCESS, duration_ms=400
    )
    coordinator.record_execution_outcome(
        case_id="skill-multi", trace_id="trace-3", outcome=ExecutionOutcome.FAILURE, duration_ms=200
    )

    stats = coordinator.get_skill_stats("skill-multi")

    assert stats.usage_count == 3
    assert stats.success_count == 2
    assert stats.total_latency_ms == 900
    assert stats.success_rate == pytest.approx(0.667, rel=0.01)
    assert stats.avg_latency_ms == 300


def test_get_ranked_skills():
    """Test getting ranked skills by success rate."""
    coordinator = LearningCoordinator()

    # Add skills with different success rates
    coordinator.record_execution_outcome("skill-a", "trace-1", ExecutionOutcome.SUCCESS, 100)
    coordinator.record_execution_outcome("skill-a", "trace-2", ExecutionOutcome.SUCCESS, 150)

    coordinator.record_execution_outcome("skill-b", "trace-3", ExecutionOutcome.SUCCESS, 200)
    coordinator.record_execution_outcome("skill-b", "trace-4", ExecutionOutcome.FAILURE, 250)

    coordinator.record_execution_outcome("skill-c", "trace-5", ExecutionOutcome.FAILURE, 300)

    ranked = coordinator.get_ranked_skills()

    assert len(ranked) == 3
    assert ranked[0][0] == "skill-a"  # Highest success rate
    assert ranked[1][0] == "skill-b"
    assert ranked[2][0] == "skill-c"


def test_recommend_skills():
    """Test skill recommendation."""
    coordinator = LearningCoordinator()

    # Add some skills
    coordinator.record_execution_outcome("skill-1", "trace-1", ExecutionOutcome.SUCCESS, 100)
    coordinator.record_execution_outcome("skill-2", "trace-2", ExecutionOutcome.SUCCESS, 200)
    coordinator.record_execution_outcome("skill-3", "trace-3", ExecutionOutcome.FAILURE, 150)

    recommendations = coordinator.recommend_skills(limit=2)

    assert len(recommendations) == 2
    assert "skill-1" in recommendations
    assert "skill-2" in recommendations


def test_learning_summary():
    """Test getting learning summary."""
    coordinator = LearningCoordinator()

    coordinator.record_execution_outcome("skill-1", "trace-1", ExecutionOutcome.SUCCESS, 100)
    coordinator.record_execution_outcome("skill-2", "trace-2", ExecutionOutcome.FAILURE, 200)

    summary = coordinator.get_learning_summary()

    assert summary["total_skills"] == 2
    assert summary["total_executions"] == 2
    assert summary["overall_success_rate"] == 0.5


def test_learning_checkpoint():
    """Test learning checkpoint logging."""
    coordinator = LearningCoordinator()

    # Record 10 executions to trigger checkpoint
    for i in range(10):
        coordinator.record_execution_outcome(
            f"skill-{i}", f"trace-{i}", ExecutionOutcome.SUCCESS, 100
        )

    # Should have processed 10 samples
    assert coordinator.learning_samples == 10
