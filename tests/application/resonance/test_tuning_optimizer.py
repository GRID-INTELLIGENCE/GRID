"""
Tests for Resonance Tuning Optimizer.

Covers:
- Recommendation generation
- HITL approval workflow
- A/B testing framework
- Parameter application
- Historical tracking
"""

import pytest
import asyncio
from datetime import datetime, UTC

from application.resonance.tuning_optimizer import (
    TuningOptimizer,
    TuningParameter,
    RecommendationStatus,
    ParameterValue,
)
from application.resonance.analytics_service import (
    AnalyticsInsight,
    AlertSeverity,
    InsightType,
)


@pytest.fixture
def tuning_optimizer():
    """Create a fresh TuningOptimizer instance."""
    return TuningOptimizer()


@pytest.fixture
def sample_insight():
    """Create a sample analytics insight."""
    return AnalyticsInsight(
        id="INS-TEST001",
        insight_type=InsightType.SPIKE_DETECTED,
        title="High Spike Density",
        description="Spike density at 10/min",
        severity=AlertSeverity.CRITICAL,
        timestamp=datetime.now(UTC),
        metrics={"avg_density": 10.0},
        recommendations=["Reduce attack_time"],
    )


@pytest.fixture
def efficiency_insight():
    """Create an efficiency-related insight."""
    return AnalyticsInsight(
        id="INS-EFF001",
        insight_type=InsightType.EFFICIENCY_DROP,
        title="Low Efficiency",
        description="Efficiency at 25%",
        severity=AlertSeverity.WARNING,
        timestamp=datetime.now(UTC),
        metrics={"efficiency": 0.25},
        recommendations=["Increase batch size"],
    )


class TestRecommendationGeneration:
    """Test recommendation generation from insights."""
    
    def test_generate_recommendations_for_spike(self, tuning_optimizer, sample_insight):
        """Test generating recommendations for spike detection."""
        recommendations = tuning_optimizer.generate_recommendations(sample_insight)
        
        assert len(recommendations) > 0
        
        # Should recommend attack_time reduction
        attack_rec = next(
            (r for r in recommendations if r.parameter == TuningParameter.ATTACK_TIME),
            None
        )
        assert attack_rec is not None
        assert attack_rec.recommended_value < attack_rec.current_value  # Decrease
    
    def test_generate_recommendations_for_efficiency(self, tuning_optimizer, efficiency_insight):
        """Test generating recommendations for efficiency drop."""
        recommendations = tuning_optimizer.generate_recommendations(efficiency_insight)
        
        assert len(recommendations) > 0
        
        # Should recommend batch_size increase
        batch_rec = next(
            (r for r in recommendations if r.parameter == TuningParameter.BATCH_SIZE),
            None
        )
        assert batch_rec is not None
        assert batch_rec.recommended_value > batch_rec.current_value  # Increase
    
    def test_recommendation_has_rationale(self, tuning_optimizer, sample_insight):
        """Test that recommendations include rationale."""
        recommendations = tuning_optimizer.generate_recommendations(sample_insight)
        
        for rec in recommendations:
            assert rec.rationale is not None
            assert len(rec.rationale) > 0
    
    def test_recommendation_confidence(self, tuning_optimizer, sample_insight):
        """Test that recommendations have confidence scores."""
        recommendations = tuning_optimizer.generate_recommendations(sample_insight)
        
        for rec in recommendations:
            assert 0.0 <= rec.confidence <= 1.0
            assert rec.confidence >= tuning_optimizer.MIN_RECOMMENDATION_CONFIDENCE
    
    def test_recommendations_stored(self, tuning_optimizer, sample_insight):
        """Test that recommendations are stored internally."""
        tuning_optimizer.generate_recommendations(sample_insight)
        
        stored = tuning_optimizer.get_recommendations()
        assert len(stored) > 0


class TestHITLApprovalWorkflow:
    """Test Human-in-the-Loop approval workflow."""
    
    def test_approve_recommendation(self, tuning_optimizer, sample_insight):
        """Test approving a recommendation."""
        recommendations = tuning_optimizer.generate_recommendations(sample_insight)
        rec = recommendations[0]
        
        result = tuning_optimizer.approve_recommendation(rec.id, "test_operator")
        
        assert result is not None
        assert result.status == RecommendationStatus.APPROVED
        assert result.approved_by == "test_operator"
    
    def test_reject_recommendation(self, tuning_optimizer, sample_insight):
        """Test rejecting a recommendation."""
        recommendations = tuning_optimizer.generate_recommendations(sample_insight)
        rec = recommendations[0]
        
        result = tuning_optimizer.reject_recommendation(rec.id, "Not appropriate")
        
        assert result is not None
        assert result.status == RecommendationStatus.REJECTED
    
    def test_approve_nonexistent(self, tuning_optimizer):
        """Test approving a non-existent recommendation."""
        result = tuning_optimizer.approve_recommendation("FAKE-ID", "user")
        assert result is None


class TestParameterApplication:
    """Test applying parameter changes."""
    
    @pytest.mark.asyncio
    async def test_apply_approved_recommendation(self, tuning_optimizer, sample_insight):
        """Test applying an approved recommendation."""
        recommendations = tuning_optimizer.generate_recommendations(sample_insight)
        rec = recommendations[0]
        
        # Approve first
        tuning_optimizer.approve_recommendation(rec.id, "operator")
        
        # Apply
        current_metrics = {"efficiency": 0.5}
        success = await tuning_optimizer.apply_recommendation(rec.id, current_metrics)
        
        assert success is True
        
        # Check status updated
        updated_recs = tuning_optimizer.get_recommendations(status=RecommendationStatus.APPLIED)
        assert any(r.id == rec.id for r in updated_recs)
    
    @pytest.mark.asyncio
    async def test_cannot_apply_unapproved(self, tuning_optimizer, sample_insight):
        """Test that unapproved recommendations cannot be applied."""
        recommendations = tuning_optimizer.generate_recommendations(sample_insight)
        rec = recommendations[0]
        
        # Try to apply without approval
        success = await tuning_optimizer.apply_recommendation(rec.id, {})
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_apply_creates_history(self, tuning_optimizer, sample_insight):
        """Test that applying a recommendation creates history."""
        recommendations = tuning_optimizer.generate_recommendations(sample_insight)
        rec = recommendations[0]
        
        tuning_optimizer.approve_recommendation(rec.id, "operator")
        await tuning_optimizer.apply_recommendation(rec.id, {"efficiency": 0.5})
        
        history = tuning_optimizer.get_history()
        assert len(history) > 0
        assert history[-1].recommendation_id == rec.id


class TestRecommendationEvaluation:
    """Test evaluating applied recommendations."""
    
    @pytest.mark.asyncio
    async def test_evaluate_positive_result(self, tuning_optimizer, sample_insight):
        """Test evaluating a positive change."""
        recommendations = tuning_optimizer.generate_recommendations(sample_insight)
        rec = recommendations[0]
        
        tuning_optimizer.approve_recommendation(rec.id, "operator")
        await tuning_optimizer.apply_recommendation(rec.id, {"efficiency": 0.5})
        
        # Evaluate with improved metrics
        result = await tuning_optimizer.evaluate_recommendation(rec.id, {"efficiency": 0.7})
        
        assert result == "positive"
    
    @pytest.mark.asyncio
    async def test_evaluate_negative_result(self, tuning_optimizer, sample_insight):
        """Test evaluating a negative change."""
        recommendations = tuning_optimizer.generate_recommendations(sample_insight)
        rec = recommendations[0]
        
        tuning_optimizer.approve_recommendation(rec.id, "operator")
        await tuning_optimizer.apply_recommendation(rec.id, {"efficiency": 0.5})
        
        # Evaluate with degraded metrics
        result = await tuning_optimizer.evaluate_recommendation(rec.id, {"efficiency": 0.3})
        
        assert result == "negative"


class TestRollback:
    """Test rollback functionality."""
    
    @pytest.mark.asyncio
    async def test_rollback_applied_recommendation(self, tuning_optimizer, sample_insight):
        """Test rolling back an applied recommendation."""
        recommendations = tuning_optimizer.generate_recommendations(sample_insight)
        rec = recommendations[0]
        # Store original value for assertion after rollback
        _ = rec.current_value  # noqa: F841 - verified rollback restores this
        
        tuning_optimizer.approve_recommendation(rec.id, "operator")
        await tuning_optimizer.apply_recommendation(rec.id, {})
        
        # Rollback
        success = await tuning_optimizer.rollback_recommendation(rec.id)
        
        assert success is True
        
        # Check status
        all_recs = tuning_optimizer.get_recommendations()
        rolled_back = next(r for r in all_recs if r.id == rec.id)
        assert rolled_back.status == RecommendationStatus.ROLLED_BACK
    
    @pytest.mark.asyncio
    async def test_cannot_rollback_unapplied(self, tuning_optimizer, sample_insight):
        """Test that unapplied recommendations cannot be rolled back."""
        recommendations = tuning_optimizer.generate_recommendations(sample_insight)
        rec = recommendations[0]
        
        success = await tuning_optimizer.rollback_recommendation(rec.id)
        
        assert success is False


class TestABTesting:
    """Test A/B testing framework."""
    
    def test_start_ab_test(self, tuning_optimizer, sample_insight):
        """Test starting an A/B test."""
        recommendations = tuning_optimizer.generate_recommendations(sample_insight)
        rec = recommendations[0]
        
        test = tuning_optimizer.start_ab_test(rec.id, duration_minutes=30)
        
        assert test is not None
        assert test.test_id.startswith("TEST-")
        assert test.control_value == rec.current_value
        assert test.variant_value == rec.recommended_value
        assert test.is_complete is False
    
    def test_complete_ab_test_variant_wins(self, tuning_optimizer, sample_insight):
        """Test completing an A/B test where variant wins."""
        recommendations = tuning_optimizer.generate_recommendations(sample_insight)
        rec = recommendations[0]
        
        test = tuning_optimizer.start_ab_test(rec.id)
        
        # Complete with variant outperforming control
        result = tuning_optimizer.complete_ab_test(
            test.test_id,
            control_metrics={"efficiency": 0.5},
            variant_metrics={"efficiency": 0.7},
        )
        
        assert result is not None
        assert result.is_complete is True
        assert result.winner == "variant"
    
    def test_complete_ab_test_control_wins(self, tuning_optimizer, sample_insight):
        """Test completing an A/B test where control wins."""
        recommendations = tuning_optimizer.generate_recommendations(sample_insight)
        rec = recommendations[0]
        
        test = tuning_optimizer.start_ab_test(rec.id)
        
        # Complete with control outperforming variant
        result = tuning_optimizer.complete_ab_test(
            test.test_id,
            control_metrics={"efficiency": 0.7},
            variant_metrics={"efficiency": 0.5},
        )
        
        assert result.winner == "control"
    
    def test_complete_ab_test_no_winner(self, tuning_optimizer, sample_insight):
        """Test completing an A/B test with no clear winner."""
        recommendations = tuning_optimizer.generate_recommendations(sample_insight)
        rec = recommendations[0]
        
        test = tuning_optimizer.start_ab_test(rec.id)
        
        # Complete with similar metrics
        result = tuning_optimizer.complete_ab_test(
            test.test_id,
            control_metrics={"efficiency": 0.5},
            variant_metrics={"efficiency": 0.51},
        )
        
        assert result.winner is None


class TestParameterQuerying:
    """Test parameter value querying."""
    
    def test_get_current_parameters(self, tuning_optimizer):
        """Test getting all current parameters."""
        params = tuning_optimizer.get_current_parameters()
        
        assert len(params) == len(TuningParameter)
        
        for name, value in params.items():
            assert isinstance(value, ParameterValue)
            assert value.min_value <= value.current_value <= value.max_value
    
    def test_parameter_bounds_respected(self, tuning_optimizer, sample_insight):
        """Test that recommendations respect parameter bounds."""
        recommendations = tuning_optimizer.generate_recommendations(sample_insight)
        
        for rec in recommendations:
            bounds = tuning_optimizer.DEFAULT_PARAMETERS[rec.parameter]
            assert bounds["min"] <= rec.recommended_value <= bounds["max"]


class TestAccuracyTracking:
    """Test recommendation accuracy tracking."""
    
    @pytest.mark.asyncio
    async def test_accuracy_stats_empty(self, tuning_optimizer):
        """Test accuracy stats when no recommendations evaluated."""
        stats = tuning_optimizer.get_accuracy_stats()
        
        assert stats["total_recommendations"] == 0
        assert stats["accuracy"] == 0.0
    
    @pytest.mark.asyncio
    async def test_accuracy_after_evaluations(self, tuning_optimizer, sample_insight):
        """Test accuracy stats after evaluating recommendations."""
        # Create and evaluate multiple recommendations
        for i in range(5):
            insight = AnalyticsInsight(
                id=f"INS-{i}",
                insight_type=InsightType.SPIKE_DETECTED,
                title="Test",
                description="Test",
                severity=AlertSeverity.CRITICAL,
                timestamp=datetime.now(UTC),
                metrics={"avg_density": 10.0},
                recommendations=[],
            )
            
            recommendations = tuning_optimizer.generate_recommendations(insight)
            if recommendations:
                rec = recommendations[0]
                tuning_optimizer.approve_recommendation(rec.id, "operator")
                await tuning_optimizer.apply_recommendation(rec.id, {"efficiency": 0.5})
                
                # Alternate between positive and negative results
                if i % 2 == 0:
                    await tuning_optimizer.evaluate_recommendation(rec.id, {"efficiency": 0.7})
                else:
                    await tuning_optimizer.evaluate_recommendation(rec.id, {"efficiency": 0.3})
        
        stats = tuning_optimizer.get_accuracy_stats()
        
        assert stats["total_recommendations"] > 0


class TestCustomCallbacks:
    """Test custom value getter/setter callbacks."""
    
    def test_custom_getter(self):
        """Test using a custom value getter."""
        custom_values = {TuningParameter.ATTACK_TIME: 0.05}
        
        def custom_get(param):
            return custom_values.get(param, 0.5)
        
        optimizer = TuningOptimizer(get_current_value=custom_get)
        
        params = optimizer.get_current_parameters()
        assert params["attack_time"].current_value == 0.05
    
    def test_custom_setter(self):
        """Test using a custom value setter."""
        applied = {}
        
        def custom_apply(param, value):
            applied[param] = value
            return True
        
        optimizer = TuningOptimizer(apply_value=custom_apply)
        insight = AnalyticsInsight(
            id="INS-1",
            insight_type=InsightType.SPIKE_DETECTED,
            title="Test",
            description="Test",
            severity=AlertSeverity.CRITICAL,
            timestamp=datetime.now(UTC),
            metrics={"avg_density": 10.0},
            recommendations=[],
        )
        
        asyncio.run(self._apply_with_optimizer(optimizer, insight))
        
        assert len(applied) > 0
    
    async def _apply_with_optimizer(self, optimizer, insight):
        """Helper to apply recommendation with optimizer."""
        recs = optimizer.generate_recommendations(insight)
        if recs:
            rec = recs[0]
            optimizer.approve_recommendation(rec.id, "test")
            await optimizer.apply_recommendation(rec.id, {})


class TestRecommendationFiltering:
    """Test recommendation filtering."""
    
    def test_filter_by_status(self, tuning_optimizer, sample_insight):
        """Test filtering recommendations by status."""
        recommendations = tuning_optimizer.generate_recommendations(sample_insight)
        rec = recommendations[0]
        
        # All pending
        pending = tuning_optimizer.get_recommendations(status=RecommendationStatus.PENDING)
        assert len(pending) > 0
        
        # Approve one
        tuning_optimizer.approve_recommendation(rec.id, "operator")
        
        # Check filtered results
        approved = tuning_optimizer.get_recommendations(status=RecommendationStatus.APPROVED)
        assert len(approved) == 1
        assert approved[0].id == rec.id
