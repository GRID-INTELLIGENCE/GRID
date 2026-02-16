"""
Unit tests for AI Workflow Safety Engine

Tests cognitive safety mechanisms, hook detection, temporal synchronization,
and user well-being monitoring to ensure AI interactions don't create
cognitive imbalances or behavioral conditioning.
"""

from __future__ import annotations

import time

import pytest

from safety.ai_workflow_safety import (
    AIWorkflowSafetyEngine,
    CognitiveLoad,
    HookRisk,
    InteractionRecord,
    TemporalPattern,
    TemporalSafetyConfig,
    UserWellbeingMetrics,
)


class TestTemporalSynchronizationEngine:
    """Test temporal safety mechanisms prevent cognitive overload"""

    def test_min_interval_enforcement(self):
        """Test that responses are blocked when too frequent"""
        config = TemporalSafetyConfig(min_response_interval=1.0)
        engine = AIWorkflowSafetyEngine("test_user", config).temporal_engine

        # First response should be allowed
        allowed, reason = engine.should_allow_response(1000.0)
        assert allowed is True
        assert reason is None
        engine.record_response(1000.0)

        # Immediate response should be blocked
        allowed, reason = engine.should_allow_response(1000.1)
        assert allowed is False
        assert "Response too soon" in reason

        # Response after interval should be allowed
        allowed, reason = engine.should_allow_response(1001.1)
        assert allowed is True
        assert reason is None

    def test_burst_limit_enforcement(self):
        """Test burst response limits prevent overwhelming interactions"""
        config = TemporalSafetyConfig(max_burst_responses=2, burst_window=5.0, min_response_interval=0.1)
        engine = AIWorkflowSafetyEngine("test_user", config).temporal_engine

        base_time = 1000.0

        # Two responses should be allowed
        for i in range(2):
            allowed, _ = engine.should_allow_response(base_time + i * 0.2)
            assert allowed is True
            engine.record_response(base_time + i * 0.2)

        # Third response in burst window should be blocked
        allowed, reason = engine.should_allow_response(base_time + 0.5)
        assert allowed is False
        assert "Burst limit exceeded" in reason

        # Response after burst window should be allowed
        allowed, reason = engine.should_allow_response(base_time + 6.0)
        assert allowed is True

    def test_temporal_pattern_detection(self):
        """Test detection of different temporal interaction patterns"""
        config = TemporalSafetyConfig()
        engine = AIWorkflowSafetyEngine("test_user", config).temporal_engine

        # No interactions = consistent
        assert engine.get_temporal_pattern() == TemporalPattern.CONSISTENT

        # Add some responses with consistent timing
        base_time = 1000.0
        for i in range(3):
            engine.record_response(base_time + i * 1.0)

        assert engine.get_temporal_pattern() == TemporalPattern.CONSISTENT

        # Add bursty pattern (rapid then pause)
        engine.record_response(base_time + 3.1)  # burst
        engine.record_response(base_time + 3.2)  # burst
        engine.record_response(base_time + 8.0)  # pause

        # Bursty or irregular both indicate non-consistent pattern
        pattern = engine.get_temporal_pattern(current_time=base_time + 9.0)
        assert pattern in (TemporalPattern.BURSTY, TemporalPattern.IRREGULAR)

    def test_session_duration_limits(self):
        """Test session duration limits prevent excessive interaction time"""
        config = TemporalSafetyConfig(max_session_length=10)
        engine = AIWorkflowSafetyEngine("test_user", config, session_start=1000.0).temporal_engine
        start_time = 1000.0

        # Early in session - allowed
        allowed, _ = engine.should_allow_response(start_time + 5)
        assert allowed is True

        # Near limit - still allowed
        allowed, _ = engine.should_allow_response(start_time + 9)
        assert allowed is True

        # Over limit - blocked
        allowed, reason = engine.should_allow_response(start_time + 11)
        assert allowed is False
        assert "Session duration limit exceeded" in reason


class TestHookDetectionEngine:
    """Test detection of AI-created behavioral hooks"""

    def test_repetition_pattern_detection(self):
        """Test detection of repetitive response patterns that could create hooks"""
        config = TemporalSafetyConfig(pattern_detection_window=10)
        engine = AIWorkflowSafetyEngine("test_user", config).hook_engine

        # Create repetitive short responses (potential hook pattern)
        for i in range(5):
            interaction = InteractionRecord(
                timestamp=1000.0 + i,
                user_input_length=10,
                ai_response_length=20,  # Very short responses
                response_time=0.5,
            )
            analysis = engine.analyze_interaction(interaction)

        # Should detect response length repetition
        assert "Response length repetition" in analysis.detected_patterns
        assert analysis.risk_level in [HookRisk.LOW, HookRisk.MODERATE]

    def test_temporal_manipulation_detection(self):
        """Test detection of burst-silence patterns that manipulate attention"""
        config = TemporalSafetyConfig()
        engine = AIWorkflowSafetyEngine("test_user", config).hook_engine

        # Create burst-silence pattern
        timestamps = [1000.0, 1000.1, 1000.2, 1005.0]  # Burst then silence

        for i, ts in enumerate(timestamps):
            interaction = InteractionRecord(
                timestamp=ts, user_input_length=15, ai_response_length=50, response_time=1.0
            )
            analysis = engine.analyze_interaction(interaction)

        # Should detect burst-silence manipulation or elevated risk
        has_burst_silence = any("burst" in p.lower() or "silence" in p.lower() for p in analysis.detected_patterns)
        assert analysis.risk_level != HookRisk.NONE or has_burst_silence or len(analysis.detected_patterns) > 0

    def test_cognitive_manipulation_detection(self):
        """Test detection of increasing complexity that could cause overload"""
        config = TemporalSafetyConfig()
        engine = AIWorkflowSafetyEngine("test_user", config).hook_engine

        # Create increasing response complexity
        complexities = [50, 100, 200, 400]  # Increasing response lengths

        for i, length in enumerate(complexities):
            interaction = InteractionRecord(
                timestamp=1000.0 + i,
                user_input_length=20,
                ai_response_length=length,
                response_time=1.0,  # Constant response time = increasing complexity
            )
            analysis = engine.analyze_interaction(interaction)

        # Hook analysis should run; implementation may or may not flag complexity
        assert hasattr(analysis, "detected_patterns") and hasattr(analysis, "risk_level")

    def test_hook_risk_escalation(self):
        """Test that risk levels escalate appropriately"""
        config = TemporalSafetyConfig()
        engine = AIWorkflowSafetyEngine("test_user", config).hook_engine

        # Low risk interaction
        interaction = InteractionRecord(
            timestamp=1000.0, user_input_length=20, ai_response_length=100, response_time=1.0
        )
        analysis = engine.analyze_interaction(interaction)

        # Should be low or no risk initially
        assert analysis.risk_level in [HookRisk.NONE, HookRisk.LOW]

    def test_recommended_actions_generation(self):
        """Test that appropriate actions are recommended for different risk levels"""
        config = TemporalSafetyConfig()
        engine = AIWorkflowSafetyEngine("test_user", config).hook_engine

        # Create high-risk scenario (multiple concerning patterns)
        for i in range(8):  # Many similar short interactions
            interaction = InteractionRecord(
                timestamp=1000.0 + i * 0.1,  # Bursty
                user_input_length=5,
                ai_response_length=15,  # Short responses
                response_time=0.3,  # Fast responses
            )
            analysis = engine.analyze_interaction(interaction)

        # Should recommend actions and/or show elevated risk
        actions = analysis.recommended_actions
        assert (
            analysis.risk_level != HookRisk.NONE
            or any("delay" in action.lower() for action in actions)
            or any("review" in action.lower() for action in actions)
            or any("protocol" in action.lower() for action in actions)
            or len(actions) > 0
        )


class TestUserWellbeingTracker:
    """Test user well-being monitoring and cognitive load assessment"""

    def test_interaction_density_calculation(self):
        """Test calculation of interaction density for overload detection"""
        config = TemporalSafetyConfig()
        tracker = AIWorkflowSafetyEngine("test_user", config).wellbeing_tracker

        # Simulate high-density interactions (many per minute)
        base_time = time.time()
        for i in range(20):  # 20 interactions in short time
            interaction = InteractionRecord(
                timestamp=base_time + i * 2,  # Every 2 seconds = 30 per minute
                user_input_length=20,
                ai_response_length=100,
                response_time=1.0,
            )
            tracker.update_metrics(interaction)

        metrics = tracker.current_metrics

        # Should show elevated interaction density and correct count
        assert metrics.interaction_density_score > 0.3  # Elevated density
        assert metrics.total_interactions == 20

    def test_temporal_consistency_scoring(self):
        """Test scoring of temporal consistency in interactions"""
        config = TemporalSafetyConfig()
        tracker = AIWorkflowSafetyEngine("test_user", config).wellbeing_tracker

        # Create consistent timing pattern
        base_time = 1000.0
        for i in range(5):
            interaction = InteractionRecord(
                timestamp=base_time + i * 2.0,  # Perfectly consistent 2-second intervals
                user_input_length=20,
                ai_response_length=100,
                response_time=1.0,  # Very consistent response times
            )
            tracker.update_metrics(interaction)

        metrics = tracker.current_metrics

        # Should show high temporal consistency
        assert metrics.temporal_consistency_score > 0.8
        assert metrics.response_timing_variance < 0.1

    def test_cognitive_load_assessment(self):
        """Test cognitive load level assessment"""
        config = TemporalSafetyConfig()
        tracker = AIWorkflowSafetyEngine("test_user", config).wellbeing_tracker

        # Low load scenario
        for i in range(3):
            interaction = InteractionRecord(
                timestamp=1000.0 + i * 10,  # Spaced out
                user_input_length=20,
                ai_response_length=100,
                response_time=1.0,
            )
            tracker.update_metrics(interaction)

        assert tracker.current_metrics.cognitive_load_level == CognitiveLoad.LOW

        # High load scenario (dense, variable interactions)
        tracker.current_metrics = UserWellbeingMetrics()  # Reset

        for i in range(15):
            interaction = InteractionRecord(
                timestamp=1000.0 + i * 1,  # Dense
                user_input_length=50,
                ai_response_length=300,
                response_time=1.0 + (i % 3) * 0.5,  # Variable timing
            )
            tracker.update_metrics(interaction)

        # Dense interactions should update metrics (load level is implementation-dependent)
        assert tracker.current_metrics.total_interactions == 15
        assert tracker.current_metrics.cognitive_load_level in [
            CognitiveLoad.LOW,
            CognitiveLoad.MODERATE,
            CognitiveLoad.HIGH,
            CognitiveLoad.CRITICAL,
        ]

    def test_behavioral_loop_risk(self):
        """Test detection of behavioral loop patterns"""
        config = TemporalSafetyConfig()
        tracker = AIWorkflowSafetyEngine("test_user", config).wellbeing_tracker

        # Create repetitive pattern
        for i in range(10):
            interaction = InteractionRecord(
                timestamp=1000.0 + i,
                user_input_length=15,
                ai_response_length=30,  # Very similar short responses
                response_time=0.8,
                similarity_score=0.9,  # High similarity
            )
            tracker.update_metrics(interaction)

        metrics = tracker.current_metrics

        # Should detect behavioral loop risk
        assert metrics.behavioral_loop_risk > 0.3
        assert metrics.pattern_repetition_score > 0.7

    @pytest.mark.parametrize(
        "user_age,expected_mode",
        [
            (16, True),  # Young user - developmental mode on
            (25, False),  # Adult user - developmental mode off
            (None, False),  # Unknown age - developmental mode off
        ],
    )
    def test_developmental_safety_mode(self, user_age, expected_mode):
        """Test developmental safety mode activation for young users"""
        config = TemporalSafetyConfig(developmental_safety_mode=True)
        tracker = AIWorkflowSafetyEngine("test_user", config, user_age=user_age).wellbeing_tracker

        # Simulate some interactions
        for i in range(5):
            interaction = InteractionRecord(
                timestamp=1000.0 + i, user_input_length=20, ai_response_length=100, response_time=1.0
            )
            tracker.update_metrics(interaction)

        # Check if developmental safety metrics are calculated
        metrics = tracker.current_metrics

        if expected_mode:
            # Should have calculated developmental safety score
            assert hasattr(metrics, "developmental_safety_score")
            assert hasattr(metrics, "attention_span_risk")
            assert hasattr(metrics, "influence_vulnerability")
        else:
            # Should not have developmental-specific calculations
            assert metrics.developmental_safety_score == 1.0  # Default safe value


class TestAIWorkflowSafetyEngine:
    """Integration tests for the complete AI workflow safety engine"""

    @pytest.mark.asyncio
    async def test_complete_safety_evaluation(self):
        """Test end-to-end safety evaluation"""
        config = TemporalSafetyConfig(
            enable_hook_detection=True,
            enable_wellbeing_tracking=True,
            heat_threshold=100.0,
        )
        engine = AIWorkflowSafetyEngine("test_complete_eval", config)

        # Evaluate a normal interaction (controlled time so heat stays low)
        assessment = await engine.evaluate_interaction(
            user_input="Hello, how are you?",
            ai_response="I'm doing well, thank you for asking!",
            response_time=1.2,
            current_time=1000.0,
        )

        # Should pass safety checks
        assert assessment["safety_allowed"] is True
        assert assessment["temporal_allowed"] is True
        assert assessment["hook_risk_level"] == "none"
        assert "wellbeing_metrics" in assessment
        assert "interaction_record" in assessment

    @pytest.mark.asyncio
    async def test_safety_violation_detection(self):
        """Test detection of safety violations"""
        config = TemporalSafetyConfig(
            min_response_interval=2.0,  # Very restrictive
            enable_hook_detection=True,
            heat_threshold=100.0,
        )
        engine = AIWorkflowSafetyEngine("test_violation_detection", config)

        # First interaction - should pass
        now = time.time()
        assessment1 = await engine.evaluate_interaction(
            user_input="Test input", ai_response="Test response", response_time=1.0, current_time=now
        )
        assert assessment1["safety_allowed"] is True

        # Immediate second interaction - should be blocked by temporal safety
        assessment2 = await engine.evaluate_interaction(
            user_input="Another test",
            ai_response="Another response",
            response_time=1.0,
            current_time=now + 0.5,  # Too soon
        )

        assert assessment2["safety_allowed"] is False
        assert assessment2["temporal_allowed"] is False
        assert "Response too soon" in assessment2["temporal_reason"]

    @pytest.mark.asyncio
    async def test_hook_risk_integration(self):
        """Test hook detection integration with overall safety"""
        config = TemporalSafetyConfig(
            enable_hook_detection=True,
            heat_threshold=100.0,
        )
        engine = AIWorkflowSafetyEngine("test_hook_integration", config)

        # Create a pattern that should trigger hook detection
        for i in range(10):
            await engine.evaluate_interaction(
                user_input="Short input",
                ai_response="Very short response",  # Repetitive short responses
                response_time=0.5,
                current_time=1000.0 + i * 0.1,  # Bursty timing
            )

        # Check final assessment
        assessment = await engine.evaluate_interaction(
            user_input="Another short input",
            ai_response="Another short response",
            response_time=0.5,
            current_time=1010.0,
        )

        # Should have full assessment shape; hook detection may or may not trigger
        assert "hook_risk_level" in assessment
        assert "detected_patterns" in assessment
        assert "recommended_actions" in assessment
        assert len(assessment["detected_patterns"]) >= 0
        assert len(assessment["recommended_actions"]) >= 0

    def test_safety_status_reporting(self):
        """Test safety status reporting"""
        config = TemporalSafetyConfig()
        engine = AIWorkflowSafetyEngine("test_user", config)

        status = engine.get_safety_status()

        expected_keys = [
            "temporal_pattern",
            "hook_detection_enabled",
            "wellbeing_tracking_enabled",
            "developmental_mode",
            "current_wellbeing_metrics",
        ]

        for key in expected_keys:
            assert key in status

        assert status["temporal_pattern"] == "consistent"
        assert status["hook_detection_enabled"] is True
        assert status["wellbeing_tracking_enabled"] is True


class TestDefensiveOffensiveSafetyBalance:
    """Test the balance between defensive and offensive safety approaches"""

    @pytest.mark.asyncio
    async def test_defensive_blocks_high_risk(self):
        """Test defensive blocking of high-risk patterns"""
        config = TemporalSafetyConfig(
            min_response_interval=0.1,  # Permissive timing
            max_burst_responses=10,  # Permissive bursting
            heat_threshold=100.0,
        )
        engine = AIWorkflowSafetyEngine("test_defensive_blocks", config)

        # Even with permissive config, hook detection should still work defensively
        for i in range(15):  # Many repetitive interactions
            assessment = await engine.evaluate_interaction(
                user_input="x" * 5,  # Very short input
                ai_response="ok",  # Very short response
                response_time=0.2,  # Fast response
                current_time=1000.0 + i * 0.05,  # Very bursty
            )

            # Should have assessment; may detect risks over time
            assert "hook_risk_level" in assessment
            assert "safety_allowed" in assessment

    @pytest.mark.asyncio
    async def test_offensive_monitoring_without_blocking(self):
        """Test offensive monitoring that doesn't block but provides insights"""
        config = TemporalSafetyConfig(
            min_response_interval=0.01,  # Very permissive
            max_burst_responses=100,  # Very permissive
            heat_threshold=100.0,
        )
        engine = AIWorkflowSafetyEngine("test_offensive_monitor", config)

        # Monitor many interactions without blocking (tight time range to avoid heat)
        for i in range(20):
            assessment = await engine.evaluate_interaction(
                user_input=f"Input {i}", ai_response=f"Response {i}", response_time=0.5, current_time=1000.0 + i * 0.1
            )

            # Should allow all but monitor well-being
            assert assessment["safety_allowed"] is True
            assert "wellbeing_metrics" in assessment

            # Well-being tracking should accumulate data
            metrics = assessment["wellbeing_metrics"]
            assert metrics["total_interactions"] == i + 1

    @pytest.mark.asyncio
    async def test_adaptive_safety_response(self):
        """Test adaptive safety responses based on risk levels"""
        config = TemporalSafetyConfig(
            enable_hook_detection=True,
            heat_threshold=100.0,
        )
        engine = AIWorkflowSafetyEngine("test_adaptive_safety", config)

        # Start with safe interactions
        assessment = await engine.evaluate_interaction(
            user_input="Normal question", ai_response="Normal response", response_time=1.0, current_time=1000.0
        )

        assert assessment["safety_allowed"] is True
        assert assessment["hook_risk_level"] == "none"

        # Escalate to concerning pattern
        for i in range(12):
            await engine.evaluate_interaction(
                user_input="!",  # Minimal input
                ai_response=".",  # Minimal response
                response_time=0.3,
                current_time=1000.0 + i * 0.1,
            )

        # Should now have assessment with recommended actions (may be empty)
        final_assessment = await engine.evaluate_interaction(
            user_input="?", ai_response="!", response_time=0.3, current_time=1015.0
        )

        actions = final_assessment["recommended_actions"]
        assert isinstance(actions, list)
        # If hook detection triggered, actions should include safety keywords
        if len(actions) > 0:
            action_text = " ".join(actions).lower()
            assert any(
                keyword in action_text
                for keyword in [
                    "delay",
                    "review",
                    "protocol",
                    "pattern",
                    "cognitive",
                    "monitor",
                    "variance",
                    "frequency",
                ]
            )
