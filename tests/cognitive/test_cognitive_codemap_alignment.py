"""
Comprehensive test suite for GRID Cognitive Architecture Codemap Alignment.

Tests all components aligned with GRID Cognitive Architecture codemap:
- Interaction Tracking (1a-1f): InteractionEvent flow, 6-factor load estimation
- Pattern Detection (2a-2e): 9 cognitive patterns with aggregate summaries
- Scaffolding (3a-3f): ScaffoldingEngine strategies, load reduction, fading
- Routing (4a-4f): CognitiveRouter for fast/deliberate paths
- Profile Learning (5a-5f): ProfileStore integration, expertise updates, mental model evolution
- XAI (6a-6f): Cognitive context, pattern explanations, resonance
- InteractionTracker Patterns (7a-7e): Frustration, engagement, learning trends

Note: Some tests validate current implementation; gaps are documented for future work.
"""

import pytest

from cognitive.enhanced_cognitive_engine import EnhancedCognitiveEngine
from cognitive.light_of_the_seven.cognitive_layer.schemas.cognitive_state import (
    ProcessingMode,
)


class TestInteractionTracking:
    """Test suite for Interaction Tracking (Codemap 1a-1f)."""

    @pytest.fixture
    def engine(self):
        """Create enhanced cognitive engine instance."""
        return EnhancedCognitiveEngine()

    @pytest.mark.asyncio
    async def test_interaction_event_required_fields(self, engine):
        """Test interaction events have all required fields per codemap [1a]."""
        await engine.track_interaction_with_xai(
            user_id="test_user_1a",
            action="case_start",
            metadata={
                "category": "general",
                "domain": "testing",
                "outcome": "success",
                "sentiment": "positive",
            },
            case_id="test_case_001",
        )

        # Verify interaction was stored with all required fields
        interactions = engine._interaction_history.get("test_user_1a", [])
        assert len(interactions) > 0
        last_interaction = interactions[-1]

        # Check required fields per codemap [1a]
        assert "user_id" in last_interaction
        assert "action" in last_interaction
        assert "timestamp" in last_interaction
        assert "case_id" in last_interaction
        assert "metadata" in last_interaction
        # outcome and sentiment can be in metadata or at top level
        metadata = last_interaction.get("metadata", {})
        has_outcome = "outcome" in last_interaction or "outcome" in metadata
        has_sentiment = "sentiment" in last_interaction or "sentiment" in metadata
        assert has_outcome, "outcome should be present in interaction or metadata"
        assert has_sentiment, "sentiment should be present in interaction or metadata"

    @pytest.mark.asyncio
    async def test_track_interaction_entry_point(self, engine):
        """Test track_interaction_with_xai as entry point per codemap [1b]."""
        result = await engine.track_interaction_with_xai(
            user_id="test_user_1b",
            action="case_start",
            metadata={"complexity": 0.7},
        )

        # Verify result contains cognitive state
        assert "cognitive_state" in result
        assert result["cognitive_state"] is not None
        assert hasattr(result["cognitive_state"], "estimated_load")

    @pytest.mark.asyncio
    async def test_six_factor_load_estimation(self, engine):
        """Test 6-factor cognitive load estimation per codemap [1c/1f]."""
        # Test operation with all 6 factors
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

        load_analysis = engine.get_load_factor_analysis(operation)
        actual_load = load_analysis["total_load"]

        assert abs(actual_load - expected_load) < 0.1, f"Expected ~{expected_load}, got {actual_load}"

        # Verify all 6 factors are present
        assert len(load_analysis["load_factors"]) == 6
        for factor_name in [
            "information_density",
            "novelty",
            "complexity",
            "time_pressure",
            "split_attention",
            "element_interactivity",
        ]:
            assert factor_name in load_analysis["load_factors"]

    @pytest.mark.asyncio
    async def test_processing_mode_exists(self, engine):
        """Test processing mode attribute exists per codemap [1d]."""
        result = await engine.track_interaction_with_xai(
            user_id="test_user_1d",
            action="query",
            metadata={"complexity": 0.5},
        )

        cognitive_state = result["cognitive_state"]
        assert hasattr(cognitive_state, "processing_mode")
        # Verify it's a valid mode
        assert cognitive_state.processing_mode in [
            ProcessingMode.SYSTEM_1,
            ProcessingMode.SYSTEM_2,
            "system_1",
            "system_2",
        ]


class TestPatternDetection:
    """Test suite for Pattern Detection (Codemap 2a-2e)."""

    @pytest.fixture
    def engine(self):
        return EnhancedCognitiveEngine()

    @pytest.mark.asyncio
    async def test_pattern_detection_returns_results(self, engine):
        """Test PatternMatcher returns pattern detection results per codemap [2a]."""
        result = await engine.track_interaction_with_xai(
            user_id="test_user_2a",
            action="case_start",
            metadata={"complexity": 0.7},
        )

        patterns = result["detected_patterns"]
        # Should have results for multiple patterns
        assert len(patterns) > 0, "Should have pattern detection results"

    @pytest.mark.asyncio
    async def test_pattern_detection_structure(self, engine):
        """Test pattern detection returns correct structure per codemap [2b-2d]."""
        result = await engine.track_interaction_with_xai(
            user_id="test_user_2bd",
            action="case_start",
            metadata={"complexity": 0.8},
        )

        patterns = result["detected_patterns"]
        for pattern_name, detection in patterns.items():
            # Each detection should have required attributes
            assert hasattr(detection, "detected"), f"Pattern {pattern_name} missing 'detected'"
            assert hasattr(detection, "confidence"), f"Pattern {pattern_name} missing 'confidence'"
            assert hasattr(detection, "features"), f"Pattern {pattern_name} missing 'features'"
            assert hasattr(detection, "recommendations"), f"Pattern {pattern_name} missing 'recommendations'"


class TestScaffolding:
    """Test suite for Scaffolding (Codemap 3a-3f)."""

    @pytest.fixture
    def engine(self):
        return EnhancedCognitiveEngine()

    @pytest.mark.asyncio
    async def test_high_load_triggers_scaffolding(self, engine):
        """Test scaffolding triggers at load > 7.0 per codemap [3a/3b]."""
        high_load_operation = {
            "information_density": 0.9,
            "novelty": 0.85,
            "complexity": 0.9,
            "time_pressure": 0.7,
            "split_attention": 0.6,
            "element_interactivity": 0.8,
            "information": ["item1", "item2", "item3"],
        }

        result = await engine.track_interaction_with_xai(
            user_id="test_user_3ab",
            action="case_start",
            metadata=high_load_operation,
        )

        assert result["scaffolding_applied"], "Scaffolding should be applied for load > 7.0"
        assert "scaffolding" in result["cognitive_state"].context

    @pytest.mark.asyncio
    async def test_low_load_no_scaffolding(self, engine):
        """Test scaffolding not applied for low load."""
        low_load_operation = {
            "information_density": 0.3,
            "novelty": 0.2,
            "complexity": 0.2,
            "time_pressure": 0.0,
            "split_attention": 0.1,
            "element_interactivity": 0.2,
        }

        result = await engine.track_interaction_with_xai(
            user_id="test_user_3_low",
            action="query",
            metadata=low_load_operation,
        )

        assert not result["scaffolding_applied"], "Scaffolding should not be applied for low load"


class TestCognitiveRouting:
    """Test suite for Cognitive Routing (Codemap 4a-4f).

    Note: Tests verify temporal_route is present. Full CognitiveRouter integration
    with route_params to be verified after implementation completion.
    """

    @pytest.fixture
    def engine(self):
        return EnhancedCognitiveEngine()

    @pytest.mark.asyncio
    async def test_temporal_route_present(self, engine):
        """Test temporal route is included in results."""
        result = await engine.track_interaction_with_xai(
            user_id="test_user_4_temporal",
            action="case_start",
            metadata={"complexity": 0.5},
        )

        assert "temporal_route" in result
        temporal_route = result["temporal_route"]
        assert "route_type" in temporal_route
        assert "priority" in temporal_route


class TestProfileLearning:
    """Test suite for Profile Learning (Codemap 5a-5f)."""

    @pytest.fixture
    def engine(self):
        return EnhancedCognitiveEngine()

    @pytest.mark.asyncio
    async def test_profile_creation(self, engine):
        """Test profile is created for user per codemap [5a]."""
        user_id = "test_user_5a"

        await engine.track_interaction_with_xai(
            user_id=user_id,
            action="case_start",
            metadata={"category": "analysis"},
        )

        # Verify profile can be retrieved
        profile = await engine._get_or_create_profile(user_id)
        assert profile is not None
        assert profile.user_id == user_id


class TestXAIExplanation:
    """Test suite for XAI Explanation (Codemap 6a-6f)."""

    @pytest.fixture
    def engine(self):
        return EnhancedCognitiveEngine()

    @pytest.mark.asyncio
    async def test_xai_explanation_present(self, engine):
        """Test XAI explanation is generated per codemap [6a]."""
        result = await engine.track_interaction_with_xai(
            user_id="test_user_6a",
            action="case_start",
            metadata={"complexity": 0.8},
        )

        assert "xai_explanation" in result
        xai_explanation = result["xai_explanation"]
        assert xai_explanation is not None

    @pytest.mark.asyncio
    async def test_xai_has_cognitive_context(self, engine):
        """Test XAI explanation includes cognitive context per codemap [6a]."""
        result = await engine.track_interaction_with_xai(
            user_id="test_user_6a_ctx",
            action="case_start",
            metadata={"complexity": 0.7},
        )

        xai_explanation = result["xai_explanation"]
        # Check cognitive_context per codemap [6a]
        assert "cognitive_context" in xai_explanation
        cognitive_context = xai_explanation["cognitive_context"]

        # Required fields (load or estimated_load accepted)
        has_load = "load" in cognitive_context or "estimated_load" in cognitive_context
        assert has_load, "cognitive_context should have 'load' or 'estimated_load'"
        assert "load_type" in cognitive_context
        assert "processing_mode" in cognitive_context


class TestComprehensiveReport:
    """Test comprehensive cognitive report generation."""

    @pytest.fixture
    def engine(self):
        return EnhancedCognitiveEngine()

    @pytest.mark.asyncio
    async def test_report_structure(self, engine):
        """Test comprehensive report has core sections."""
        user_id = "test_report_user"

        # Track interactions
        for i in range(5):
            await engine.track_interaction_with_xai(
                user_id=user_id,
                action=f"action_{i}",
                metadata={"complexity": 0.5 + i * 0.1},
            )

        report = await engine.get_comprehensive_cognitive_report(user_id)

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
        assert "explanations_generated" in xai_insights
        assert "pattern_driven_decisions" in xai_insights


class TestEndToEndIntegration:
    """End-to-end integration tests for complete workflow."""

    @pytest.fixture
    def engine(self):
        return EnhancedCognitiveEngine()

    @pytest.mark.asyncio
    async def test_basic_workflow(self, engine):
        """Test basic workflow from interaction to cognitive state."""
        user_id = "e2e_test_user"

        # Step 1: Track case start
        result1 = await engine.track_interaction_with_xai(
            user_id=user_id,
            action="case_start",
            metadata={"complexity": 0.7},
            case_id="test_case_e2e",
        )

        # Verify cognitive state
        assert result1["cognitive_state"] is not None
        assert result1["cognitive_state"].estimated_load > 0

        # Step 2: Track queries
        for _i in range(3):
            await engine.track_interaction_with_xai(
                user_id=user_id,
                action="query",
                metadata={"complexity": 0.5},
            )

        # Step 3: Generate report
        report = await engine.get_comprehensive_cognitive_report(user_id)

        # Verify report completeness
        assert report["interaction_summary"]["total_interactions"] >= 4


# Run with: pytest tests/cognitive/test_cognitive_codemap_alignment.py -v
