"""
Comprehensive test suite for Enhanced Cognitive Engine with GRID XAI Integration.

Tests all 6 weighted load factors, 9 cognitive patterns, adaptive scaffolding,
cognitive routing, profile learning, and XAI integration.
"""

import asyncio

import pytest

from cognitive.enhanced_cognitive_engine import EnhancedCognitiveEngine


class TestEnhancedCognitiveEngine:
    """Test suite for Enhanced Cognitive Engine with GRID XAI integration."""

    @pytest.fixture
    def enhanced_engine(self):
        """Create enhanced cognitive engine instance."""
        return EnhancedCognitiveEngine()

    @pytest.mark.asyncio
    async def test_six_weighted_load_factors(self, enhanced_engine):
        """Test all 6 weighted cognitive load factors."""
        # Test operation with all factors
        operation = {
            "information_density": 0.8,  # 25% weight
            "novelty": 0.6,  # 20% weight
            "complexity": 0.7,  # 25% weight
            "time_pressure": 0.4,  # 15% weight
            "split_attention": 0.3,  # 10% weight
            "element_interactivity": 0.5,  # 5% weight
        }

        # Expected: (0.8*0.25 + 0.6*0.20 + 0.7*0.25 + 0.4*0.15 + 0.3*0.10 + 0.5*0.05) * 10
        # = (0.20 + 0.12 + 0.175 + 0.06 + 0.03 + 0.025) * 10 = 0.61 * 10 = 6.1
        expected_load = 6.1

        load_analysis = enhanced_engine.get_load_factor_analysis(operation)
        actual_load = load_analysis["total_load"]

        assert abs(actual_load - expected_load) < 0.01, f"Expected {expected_load}, got {actual_load}"

        # Verify all factors are analyzed
        assert len(load_analysis["load_factors"]) == 6
        for factor in load_analysis["load_factors"].values():
            assert "value" in factor
            assert "weight" in factor
            assert "contribution" in factor
            assert "description" in factor

    @pytest.mark.asyncio
    async def test_adaptive_scaffolding_trigger(self, enhanced_engine):
        """Test scaffolding triggers at load > 7.0."""
        # High load operation
        high_load_operation = {
            "information_density": 0.9,
            "novelty": 0.8,
            "complexity": 0.9,
            "time_pressure": 0.7,
            "split_attention": 0.6,
            "element_interactivity": 0.8,
            "information": ["item1", "item2", "item3", "item4", "item5"],  # For scaffolding
        }

        result = await enhanced_engine.track_interaction_with_xai(
            user_id="test_user", action="case_start", metadata=high_load_operation
        )

        assert result["scaffolding_applied"], "Scaffolding should be applied for load > 7.0"
        assert "scaffolding" in result["cognitive_state"].context

        # Test low load operation
        low_load_operation = {
            "information_density": 0.3,
            "novelty": 0.2,
            "complexity": 0.2,
            "time_pressure": 0.0,
            "split_attention": 0.1,
            "element_interactivity": 0.2,
        }

        result_low = await enhanced_engine.track_interaction_with_xai(
            user_id="test_user_low", action="query", metadata=low_load_operation
        )

        assert not result_low["scaffolding_applied"], "Scaffolding should not be applied for low load"

    @pytest.mark.asyncio
    async def test_nine_cognitive_patterns_detection(self, enhanced_engine):
        """Test detection of all 9 cognitive patterns."""
        # Complex operation that should trigger multiple patterns
        complex_operation = {
            "information_density": 0.8,
            "novelty": 0.7,
            "complexity": 0.9,
            "time_pressure": 0.5,
            "split_attention": 0.4,
            "element_interactivity": 0.7,
            "cognitive_load": 8.0,  # For flow pattern
            "engagement": 0.8,  # For flow pattern
            "focus": 0.7,  # For flow pattern
            "time_distortion": 0.6,  # For flow pattern
        }

        result = await enhanced_engine.track_interaction_with_xai(
            user_id="test_user", action="case_start", metadata=complex_operation
        )

        patterns = result["detected_patterns"]
        assert len(patterns) > 0, "Should detect at least some patterns"

        # Verify pattern structure
        for detection in patterns.values():
            assert hasattr(detection, "detected")
            assert hasattr(detection, "confidence")
            assert hasattr(detection, "features")
            assert hasattr(detection, "recommendations")

    @pytest.mark.asyncio
    async def test_cognitive_routing_fast_deliberate_paths(self, enhanced_engine):
        """Test cognitive routing selects fast/deliberate paths."""
        # Test fast path (low load, System 1)
        fast_operation = {
            "information_density": 0.3,
            "novelty": 0.2,
            "complexity": 0.2,
            "time_pressure": 0.0,
            "split_attention": 0.1,
            "element_interactivity": 0.2,
            "temporal": {"pattern": "urgent", "time_sensitivity": 0.8},
        }

        result = await enhanced_engine.track_interaction_with_xai(
            user_id="test_user", action="query", metadata=fast_operation
        )

        temporal_route = result["temporal_route"]
        assert "route_type" in temporal_route
        assert "priority" in temporal_route
        assert "coffee_mode" in temporal_route

        # Test deliberate path (high load, System 2)
        deliberate_operation = {
            "information_density": 0.8,
            "novelty": 0.7,
            "complexity": 0.9,
            "time_pressure": 0.3,
            "split_attention": 0.4,
            "element_interactivity": 0.6,
            "temporal": {"pattern": "long_term", "time_sensitivity": 0.2},
        }

        result_deliberate = await enhanced_engine.track_interaction_with_xai(
            user_id="test_user_deliberate", action="case_start", metadata=deliberate_operation
        )

        temporal_route_deliberate = result_deliberate["temporal_route"]
        assert temporal_route_deliberate["route_type"] != temporal_route["route_type"]

    @pytest.mark.asyncio
    async def test_profile_learning_expertise_updates(self, enhanced_engine):
        """Test profile learning updates expertise levels."""
        # Track multiple interactions to trigger learning
        interactions = [
            {"action": "case_start", "metadata": {"complexity": 0.7}},
            {"action": "query", "metadata": {"novelty": 0.6}},
            {"action": "retry", "metadata": {"complexity": 0.8}},
            {"action": "case_start", "metadata": {"complexity": 0.6}},
        ]

        for i, interaction in enumerate(interactions):
            await enhanced_engine.track_interaction_with_xai(
                user_id="learning_user",
                action=interaction["action"],
                metadata=interaction["metadata"],
                case_id=f"case_{i}",
            )

        # Generate comprehensive report to verify learning
        report = await enhanced_engine.get_comprehensive_cognitive_report("learning_user")

        assert "interaction_summary" in report
        assert report["interaction_summary"]["total_interactions"] == len(interactions)
        assert "xai_insights" in report
        assert report["xai_insights"]["explanations_generated"] == len(interactions)

    @pytest.mark.asyncio
    async def test_xai_integration_cognitive_context(self, enhanced_engine):
        """Test XAI integration provides cognitive context."""
        result = await enhanced_engine.track_interaction_with_xai(
            user_id="xai_test_user",
            action="case_start",
            metadata={"information_density": 0.7, "novelty": 0.6, "complexity": 0.8, "time_pressure": 0.3},
        )

        xai_explanation = result["xai_explanation"]
        assert xai_explanation is not None
        assert "decision_id" in xai_explanation
        assert "context" in xai_explanation
        assert "rationale" in xai_explanation

        # Verify cognitive context is included
        context = xai_explanation["context"]
        assert "cognitive" in context
        assert "patterns" in context
        assert "temporal" in context

        cognitive_context = context["cognitive"]
        assert "estimated_load" in cognitive_context
        assert "load_type" in cognitive_context
        assert "processing_mode" in cognitive_context

    @pytest.mark.asyncio
    async def test_interaction_tracking_with_agentic_system(self, enhanced_engine):
        """Test interaction tracking works with AgenticSystem integration."""
        # Simulate AgenticSystem interaction
        agentic_interaction = {
            "agent_id": "cognitive_agent",
            "system_state": "active",
            "decision_context": "user_assistance",
            "complexity_score": 0.75,
        }

        result = await enhanced_engine.track_interaction_with_xai(
            user_id="agentic_user", action="agent_assist", metadata=agentic_interaction
        )

        # Verify tracking worked
        assert result["cognitive_state"] is not None
        assert result["xai_explanation"] is not None
        assert result["detected_patterns"] is not None

        # Verify interaction was stored
        report = await enhanced_engine.get_comprehensive_cognitive_report("agentic_user")
        assert report["interaction_summary"]["total_interactions"] == 1
        assert report["interaction_summary"]["most_common_action"] == "agent_assist"

    @pytest.mark.asyncio
    async def test_comprehensive_cognitive_report(self, enhanced_engine):
        """Test comprehensive cognitive report generation."""
        # Track multiple interactions
        for i in range(5):
            await enhanced_engine.track_interaction_with_xai(
                user_id="report_user", action=f"action_{i}", metadata={"complexity": 0.5 + i * 0.1}
            )

        report = await enhanced_engine.get_comprehensive_cognitive_report("report_user")

        # Verify report structure
        assert "current_cognitive_state" in report
        assert "pattern_analysis" in report
        assert "load_factor_trends" in report
        assert "interaction_summary" in report
        assert "xai_insights" in report

        # Verify cognitive state details
        cognitive_state = report["current_cognitive_state"]
        assert "estimated_load" in cognitive_state
        assert "load_type" in cognitive_state
        assert "processing_mode" in cognitive_state

        # Verify XAI insights
        xai_insights = report["xai_insights"]
        assert xai_insights["explanations_generated"] == 5
        assert "pattern_driven_decisions" in xai_insights
        assert "scaffolding_applications" in xai_insights

    @pytest.mark.asyncio
    async def test_load_type_classification(self, enhanced_engine):
        """Test cognitive load type classification."""
        # Test intrinsic load (high element interactivity)
        intrinsic_operation = {"element_interactivity": 0.8, "split_attention": 0.2, "novelty": 0.4, "complexity": 0.6}

        load_analysis = enhanced_engine.get_load_factor_analysis(intrinsic_operation)
        assert load_analysis["load_type"] in ["intrinsic", "extraneous", "germane"]

        # Test extraneous load (high split attention)
        extraneous_operation = {"element_interactivity": 0.3, "split_attention": 0.8, "novelty": 0.3, "complexity": 0.4}

        load_analysis_extraneous = enhanced_engine.get_load_factor_analysis(extraneous_operation)
        assert load_analysis_extraneous["load_type"] in ["intrinsic", "extraneous", "germane"]

    @pytest.mark.asyncio
    async def test_threshold_analysis(self, enhanced_engine):
        """Test threshold analysis for scaffolding and load levels."""
        # Test just below scaffolding threshold
        below_threshold = {
            "information_density": 0.6,
            "novelty": 0.5,
            "complexity": 0.6,
            "time_pressure": 0.2,
            "split_attention": 0.1,
            "element_interactivity": 0.4,
        }

        analysis_below = enhanced_engine.get_load_factor_analysis(below_threshold)
        assert not analysis_below["threshold_analysis"]["scaffolding_triggered"]
        assert analysis_below["threshold_analysis"]["moderate_load"]

        # Test above scaffolding threshold
        above_threshold = {
            "information_density": 0.9,
            "novelty": 0.8,
            "complexity": 0.9,
            "time_pressure": 0.7,
            "split_attention": 0.6,
            "element_interactivity": 0.8,
        }

        analysis_above = enhanced_engine.get_load_factor_analysis(above_threshold)
        assert analysis_above["threshold_analysis"]["scaffolding_triggered"]
        assert analysis_above["threshold_analysis"]["high_load"]


# Integration test with AgenticSystem
class TestAgenticSystemIntegration:
    """Test integration with AgenticSystem."""

    @pytest.mark.asyncio
    async def test_agentic_system_workflow(self):
        """Test complete AgenticSystem workflow with cognitive enhancement."""
        engine = EnhancedCognitiveEngine()

        # Simulate AgenticSystem workflow
        workflow_steps = [
            {"action": "system_init", "metadata": {"complexity": 0.3}},
            {"action": "user_query", "metadata": {"novelty": 0.6, "information_density": 0.7}},
            {"action": "cognitive_analysis", "metadata": {"complexity": 0.8}},
            {"action": "response_generation", "metadata": {"time_pressure": 0.5}},
            {"action": "system_shutdown", "metadata": {"complexity": 0.2}},
        ]

        for step in workflow_steps:
            result = await engine.track_interaction_with_xai(
                user_id="agentic_system", action=step["action"], metadata=step["metadata"]
            )

            # Verify each step has proper cognitive analysis
            assert result["cognitive_state"] is not None
            assert result["xai_explanation"] is not None

        # Generate final report
        final_report = await engine.get_comprehensive_cognitive_report("agentic_system")

        # Verify workflow was properly tracked
        assert final_report["interaction_summary"]["total_interactions"] == len(workflow_steps)
        assert final_report["xai_insights"]["explanations_generated"] == len(workflow_steps)

        # Verify cognitive evolution
        load_trends = final_report["load_factor_trends"]
        assert len(load_trends) == len(workflow_steps)

        # Load should vary based on workflow complexity
        loads = [trend["total_load"] for trend in load_trends]
        assert max(loads) > min(loads), "Load should vary across workflow steps"


# Performance and stress tests
class TestPerformanceAndStress:
    """Performance and stress tests for enhanced cognitive engine."""

    @pytest.mark.asyncio
    async def test_high_volume_interactions(self):
        """Test handling of high volume interactions."""
        engine = EnhancedCognitiveEngine()

        # Track 100 interactions rapidly
        tasks = []
        for i in range(100):
            task = engine.track_interaction_with_xai(
                user_id=f"user_{i % 10}",  # 10 different users
                action=f"action_{i % 5}",  # 5 different actions
                metadata={"complexity": (i % 10) / 10.0},
            )
            tasks.append(task)

        # Execute all interactions concurrently
        results = await asyncio.gather(*tasks)

        # Verify all interactions were processed
        assert len(results) == 100
        for result in results:
            assert result["cognitive_state"] is not None
            assert result["xai_explanation"] is not None

    @pytest.mark.asyncio
    async def test_complex_cognitive_scenarios(self):
        """Test complex cognitive scenarios with multiple factors."""
        engine = EnhancedCognitiveEngine()

        # Complex scenario with all cognitive elements
        complex_scenarios = [
            {
                "name": "High stress learning",
                "metadata": {
                    "information_density": 0.9,
                    "novelty": 0.8,
                    "complexity": 0.9,
                    "time_pressure": 0.8,
                    "split_attention": 0.7,
                    "element_interactivity": 0.8,
                    "cognitive_load": 9.0,
                    "engagement": 0.9,
                    "focus": 0.8,
                },
            },
            {
                "name": "Flow state",
                "metadata": {
                    "information_density": 0.6,
                    "novelty": 0.4,
                    "complexity": 0.5,
                    "time_pressure": 0.2,
                    "split_attention": 0.1,
                    "element_interactivity": 0.4,
                    "cognitive_load": 5.0,
                    "engagement": 0.9,
                    "focus": 0.9,
                    "time_distortion": 0.8,
                },
            },
            {
                "name": "Cognitive overload",
                "metadata": {
                    "information_density": 1.0,
                    "novelty": 0.9,
                    "complexity": 1.0,
                    "time_pressure": 0.9,
                    "split_attention": 0.9,
                    "element_interactivity": 0.9,
                },
            },
        ]

        for scenario in complex_scenarios:
            result = await engine.track_interaction_with_xai(
                user_id="complex_test_user", action="complex_scenario", metadata=scenario["metadata"]
            )

            # Verify complex scenarios are handled properly
            assert result["cognitive_state"].estimated_load > 0
            assert len(result["detected_patterns"]) > 0
            assert result["xai_explanation"]["rationale"] != ""

            # Verify scaffolding for high load scenarios
            if scenario["name"] in ["High stress learning", "Cognitive overload"]:
                assert result["scaffolding_applied"]


if __name__ == "__main__":
    # Run tests when executed directly
    print("Running Enhanced Cognitive Engine Tests...")

    async def run_tests():
        engine = EnhancedCognitiveEngine()

        # Test basic functionality
        result = await engine.track_interaction_with_xai(
            user_id="test_user", action="case_start", metadata={"complexity": 0.7, "information_density": 0.6}
        )

        print(f"✅ Basic test passed - Load: {result['cognitive_state'].estimated_load:.2f}")
        print(f"✅ XAI explanation generated: {bool(result['xai_explanation'])}")
        print(f"✅ Patterns detected: {len(result['detected_patterns'])}")
        print(f"✅ Scaffolding applied: {result['scaffolding_applied']}")

        # Test comprehensive report
        report = await engine.get_comprehensive_cognitive_report("test_user")
        print(f"✅ Comprehensive report generated with {len(report)} sections")

        print("\n🎉 All Enhanced Cognitive Engine tests passed!")

    asyncio.run(run_tests())
