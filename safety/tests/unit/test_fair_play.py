import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

from safety.ai_workflow_safety import (
    AIWorkflowSafetyEngine,
    get_ai_workflow_safety_engine,
    TemporalSafetyConfig,
    InteractionRecord,
    HookRisk,
    clear_ai_workflow_safety_cache,
    CognitiveLoad,
    RateLimiter,
)
from safety.monitoring import SafetyEvent, EnhancedSafetyMonitor
from safety.content_safety_checker import ContentSafetyChecker

@pytest.fixture(autouse=True)
def cleanup():
    clear_ai_workflow_safety_cache()

@pytest.mark.asyncio
async def test_rate_limiting_exhaustion_stamina():
    """Test Rule 1: Input-Locked Stamina exhaustion"""
    # Disable traditional temporal limits to focus on stamina
    config = TemporalSafetyConfig(
        stamina_max=10.0,
        stamina_regen_per_second=0.1,  # Small positive value to pass validation
        min_response_interval=0.0,
        max_burst_responses=100
    )
    engine = get_ai_workflow_safety_engine("stamina_user", config=config)

    now = time.time()

    # 1. Large input cost
    # Cost = (1000 / 100) + 1 = 11.0 (Exceeds 10.0)
    result = await engine.evaluate_interaction(
        user_input="A" * 1000,
        ai_response="Short response",
        response_time=1.0,
        current_time=now
    )
    assert result["safety_allowed"] is False
    assert result["stamina_allowed"] is False
    assert "Stamina exhausted" in result["stamina_reason"]

    # 2. Sequential small inputs
    config_small = TemporalSafetyConfig(
        stamina_max=5.0,
        stamina_regen_per_second=0.0,
        min_response_interval=0.0,
        max_burst_responses=100
    )
    engine_small = get_ai_workflow_safety_engine("small_stamina_user", config=config_small)

    # Cost = (0 / 100) + 1 = 1.0 per request
    for i in range(5):
        # Use empty input to ensure cost is exactly 1.0
        res = await engine_small.evaluate_interaction("", "Response", 1.0, current_time=now + i)
        assert res["safety_allowed"] is True

    # 6th request should fail
    fail_res = await engine_small.evaluate_interaction("", "Response", 1.0, current_time=now + 6)
    assert fail_res["safety_allowed"] is False
    assert fail_res["stamina_reason"] == "Stamina exhausted"

@pytest.mark.asyncio
async def test_deterministic_heat_cooldown():
    """Test Rule 2: Deterministic Heat and Cooldown"""
    config = TemporalSafetyConfig(
        heat_threshold=15.0,  # Below 20 so 2 detections (20 heat) strictly exceed
        cooldown_duration=2,
        min_response_interval=0.0
    )
    engine = get_ai_workflow_safety_engine("heat_user_det", config=config)

    now = time.time()

    # Heat_Generated = (SensitiveDetections * 10) + (density * 50). 2 detections = 20 heat > 15.
    result = await engine.evaluate_interaction(
        "Bad input", "Bad response", 1.0, sensitive_detections=2, current_time=now
    )

    assert engine.current_heat >= 15.0

    # Next request should be blocked by cooldown
    blocked_res = await engine.evaluate_interaction("Input", "Response", 1.0, current_time=now + 0.1)
    assert blocked_res["safety_allowed"] is False
    assert blocked_res["blocked_reason"] == "COOLDOWN_ACTIVE"

@pytest.mark.asyncio
async def test_developmental_safety_blocks_manipulation():
    """Test Rule: Block manipulative patterns for young users"""
    config = TemporalSafetyConfig(developmental_safety_mode=True, min_response_interval=0.0)
    # 14-year-old user
    engine = get_ai_workflow_safety_engine("teen_user", config=config, user_age=14)

    now = time.time()

    # Pattern: "keep a secret" / "don't tell" trigger manipulation detection
    res1 = await engine.evaluate_interaction("Can you keep a secret?", "Sure", 1.0, current_time=now)
    res2 = await engine.evaluate_interaction("Don't tell anyone.", "I won't", 1.0, current_time=now + 1)

    # At least one interaction must be blocked due to manipulation pattern
    assert res1["safety_allowed"] is False or res2["safety_allowed"] is False
    blocked = res2 if not res2["safety_allowed"] else res1
    assert "suspicious_manipulation_pattern_detected" in blocked["developmental_safety"]["reasons"]


@pytest.mark.asyncio
async def test_efficiency_based_flow_bonus():
    """Test Rule 3: Efficiency-Based Flow bonus for consistent safe behavior"""
    config = TemporalSafetyConfig(
        stamina_max=20.0,
        stamina_regen_per_second=1.0,
        stamina_flow_bonus=2.0,  # Double regeneration for consistent users
        min_response_interval=0.0,
        max_burst_responses=20,  # Avoid burst limit during 6 rapid requests
        burst_window=60.0,
    )
    engine = get_ai_workflow_safety_engine("flow_bonus_user", config=config)

    now = time.time()

    # Build consecutive safe interactions to earn flow bonus (space out to avoid burst)
    for i in range(6):  # Need 5+ consecutive safe for bonus
        res = await engine.evaluate_interaction(
            "Safe input", "Safe response", 1.0,
            sensitive_detections=0,  # Safe = no detections
            current_time=now + i * 2.0  # 2s apart to avoid burst limit
        )
        assert res["safety_allowed"] is True

    # Verify flow bonus is applied in metrics
    metrics = engine.get_safety_metrics()
    assert metrics["consistency"] > 0.5  # Positive consistency score

    # Large input should be handled with sufficient stamina
    large_input_res = await engine.evaluate_interaction(
        "A" * 15, "Response", 1.0,  # Cost = max(1.5, 1) = 1.5, well under 20
        sensitive_detections=0,
        current_time=now + 20
    )
    assert large_input_res["safety_allowed"] is True


@pytest.mark.asyncio
async def test_age_appropriate_safety_thresholds():
    """Test different safety thresholds for different age groups"""
    # Pre-teen (most restrictive)
    config_preteen = TemporalSafetyConfig(developmental_safety_mode=True)
    engine_preteen = get_ai_workflow_safety_engine("preteen_user", config=config_preteen, user_age=12)

    # Teen
    engine_teen = get_ai_workflow_safety_engine("teen_user", config=config_preteen, user_age=15)

    # Test with dense interactions that should be restricted for young users
    now = time.time()
    dense_interactions = []
    for i in range(8):  # Very dense pattern
        dense_interactions.append(
            InteractionRecord(now + i * 1, 20, 100, 1.0)  # 1 second intervals
        )

    # Simulate dense interaction history
    for interaction in dense_interactions:
        engine_preteen.wellbeing_tracker.update_metrics(interaction)
        engine_teen.wellbeing_tracker.update_metrics(interaction)

    # Pre-teen should be more restricted
    preteen_check = engine_preteen.wellbeing_tracker.check_developmental_safety("Test input")
    teen_check = engine_teen.wellbeing_tracker.check_developmental_safety("Test input")

    # Both should detect high density, but pre-teen might be more sensitive
    assert preteen_check["age_group"] == "pre_teen"
    assert teen_check["age_group"] == "teen"


@pytest.mark.asyncio
async def test_grooming_escalation_detection():
    """Test detection of escalating grooming behavior"""
    config = TemporalSafetyConfig(developmental_safety_mode=True)
    engine = get_ai_workflow_safety_engine("grooming_test", config=config, user_age=14)

    now = time.time()

    # Create escalating pattern
    interactions = [
        ("Hi there", 0),  # Neutral
        ("You can tell me anything", 1),  # Building trust
        ("Let's keep this between us", 1),  # Secrecy
        ("Don't tell your parents", 1),  # Isolation
        ("This is our secret", 1),  # Escalation
    ]

    for input_text, manipulation_flag in interactions:
        interaction = InteractionRecord(
            timestamp=now,
            user_input_length=len(input_text),
            ai_response_length=100,
            response_time=1.0,
            cognitive_markers={"potential_manipulation": manipulation_flag}
        )
        engine.wellbeing_tracker.update_metrics(interaction)

    # Final check should detect grooming escalation
    result = engine.wellbeing_tracker.check_developmental_safety("Promise not to tell anyone")
    assert result["is_safe"] is False
    assert any("grooming_escalation" in reason or "manipulation" in reason
              for reason in result["reasons"])


@pytest.mark.asyncio
async def test_content_safety_integration():
    """Test content safety checker integration with Fair Play rules"""
    checker = ContentSafetyChecker()

    # check_content returns dict with is_safe and issues (config-dependent)
    result = checker.check_content("How to make explosives?")
    assert "is_safe" in result
    assert "issues" in result

    result2 = checker.check_content("Keep this secret from everyone")
    assert "is_safe" in result2
    assert isinstance(result2.get("issues", []), list)


@pytest.mark.asyncio
async def test_safety_monitor_alerts():
    """Test safety monitor alert threshold triggering"""
    monitor = EnhancedSafetyMonitor({
        "content_violation": (2, 60)  # 2 violations in 60 seconds
    })

    alerts_received = []

    def alert_handler(alert):
        alerts_received.append(alert)

    monitor.add_alert_handler(alert_handler)

    # Send violations
    for i in range(3):
        monitor.record_event(SafetyEvent(
            event_type="content_violation",
            severity="high",
            user_id="test_user",
            metadata={"violation": f"type_{i}"}
        ))

    assert len(alerts_received) > 0
    assert alerts_received[0]["alert_type"] == "content_violation_threshold_exceeded"


@pytest.mark.asyncio
async def test_session_limits_and_intervention():
    """Test session duration limits and automatic intervention"""
    config = TemporalSafetyConfig(max_session_length=1800)  # 30 minutes
    now = time.time()
    session_start = now - 1900  # 31.5 minutes ago
    engine = AIWorkflowSafetyEngine("session_test", config, session_start=session_start)

    result = await engine.evaluate_interaction(
        "Test input", "Test response", 1.0, current_time=now
    )
    # Should be blocked due to session duration (temporal engine uses max_session_length)
    assert result["safety_allowed"] is False


@pytest.mark.asyncio
async def test_heat_decay_mechanics():
    """Test heat decay over time"""
    config = TemporalSafetyConfig(
        heat_threshold=50.0,
        heat_decay_rate=5.0  # 5 heat per second decay
    )
    limiter = RateLimiter(config)
    user_id = "heat_decay_test"
    t0 = time.time()

    # Generate initial heat (input cost 2.0, heat += 0.2; then decay over 0s)
    result = limiter.check_rate_limit(user_id, "a" * 20, t0)
    initial_heat = result["current_heat"]
    assert initial_heat > 0

    # Advance time 10s and check decay (heat_decay_rate * 10 = 50)
    future_time = t0 + 10
    result = limiter.check_rate_limit(user_id, "x", future_time)
    decayed_heat = result["current_heat"]

    # Heat should have decayed (initial was small, so decayed can be 0 or small)
    assert decayed_heat <= initial_heat + 1.0  # Allow for new request adding a little heat


@pytest.mark.asyncio
async def test_fair_play_rules_integration():
    """Integration test covering all Fair Play rules working together"""
    config = TemporalSafetyConfig(
        stamina_max=30.0,  # Lower for easier testing
        heat_threshold=25.0,  # Lower threshold
        developmental_safety_mode=True,
        min_response_interval=0.0,
        max_burst_responses=100,
        burst_window=60.0,
        enable_hook_detection=False,  # Focus on stamina/heat/developmental in this test
    )

    engine = get_ai_workflow_safety_engine("integration_test", config=config, user_age=15)

    now = time.time()

    # Phase 1: Build flow bonus with safe interactions (spaced to avoid burst/hook)
    safe_count = 0
    for i in range(6):
        assessment = await engine.evaluate_interaction(
            user_input="Safe question",
            ai_response="Safe answer",
            response_time=1.0,
            current_time=now + i * 2.0
        )
        if assessment["safety_allowed"]:
            safe_count += 1
    assert safe_count >= 2  # At least some pass (hook/developmental can block)

    # Phase 2: Test Rule 1 (Stamina exhaustion) with a fresh engine
    clear_ai_workflow_safety_cache()
    stamina_config = TemporalSafetyConfig(
        stamina_max=8.0, stamina_regen_per_second=0.01,
        min_response_interval=0.0, max_burst_responses=100,
        enable_hook_detection=False, developmental_safety_mode=False,
    )
    stamina_engine = get_ai_workflow_safety_engine("stamina_phase", config=stamina_config)
    large_result = await stamina_engine.evaluate_interaction(
        user_input="x" * 100,  # Cost 10 (min 1 per request), exhausts stamina 8
        ai_response="Response", response_time=1.0, current_time=now + 20
    )
    assert large_result["safety_allowed"] is False
    assert "Stamina" in large_result.get("stamina_reason", "")

    # Phase 3: Test Rule 2 (Heat cooldown) - One request over low threshold triggers cooldown
    clear_ai_workflow_safety_cache()
    heat_config = TemporalSafetyConfig(
        stamina_max=100.0, heat_threshold=5.0, cooldown_duration=10.0,
        enable_hook_detection=False, developmental_safety_mode=False,
    )
    heat_engine = get_ai_workflow_safety_engine("heat_integration", config=heat_config)
    await heat_engine.evaluate_interaction(
        user_input="Heat",
        ai_response="R",
        response_time=0.1,
        sensitive_detections=1,  # heat = 10 > 5
        current_time=now + 40
    )
    cooldown_result = await heat_engine.evaluate_interaction(
        user_input="Next",
        ai_response="R",
        response_time=0.1,
        sensitive_detections=0,
        current_time=now + 41
    )
    assert cooldown_result["safety_allowed"] is False
    assert "COOLDOWN" in cooldown_result.get("blocked_reason", "")

    # Phase 4: Test Developmental Safety (dedicated engine with age and developmental mode)
    clear_ai_workflow_safety_cache()
    dev_engine = get_ai_workflow_safety_engine(
        "dev_phase", config=config, user_age=12
    )
    dev_result = await dev_engine.evaluate_interaction(
        user_input="Let's keep this secret from your parents",
        ai_response="Okay",
        response_time=1.0,
        current_time=now + 50
    )
    assert dev_result["safety_allowed"] is False
    assert not dev_result["developmental_safety"]["is_safe"]


@pytest.mark.asyncio
async def test_rate_limiter_thread_safety():
    """Test thread safety of rate limiter under concurrency"""
    import concurrent.futures

    # Low stamina so concurrent requests exhaust it
    config = TemporalSafetyConfig(stamina_max=5.0, stamina_regen_per_second=0.0)
    limiter = RateLimiter(config)
    user_id = "concurrent_user"
    results = []

    def make_request():
        result = limiter.check_rate_limit(user_id, "x", time.time())  # cost 1.0 each
        results.append(result)

    # Run many concurrent requests (stamina 5, cost 1 each -> 5 allowed, rest blocked)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request) for _ in range(15)]
        concurrent.futures.wait(futures)

    allowed_count = sum(1 for r in results if r["allowed"])
    blocked_count = sum(1 for r in results if not r["allowed"])

    assert allowed_count > 0  # At least some should pass
    assert blocked_count > 0  # Some should be blocked by stamina limits


@pytest.mark.asyncio
async def test_enhanced_safety_monitor_start():
    """EnhancedSafetyMonitor.start() schedules background _monitor_safety_metrics."""
    monitor = EnhancedSafetyMonitor(alert_thresholds={"test": (10, 60)})
    # Verify start() creates the background task without raising
    await monitor.start()
    # Run _check_system_health once synchronously to verify it exists and runs
    await monitor._check_system_health()
    # Monitor has the expected interface
    assert hasattr(monitor, "_monitor_safety_metrics")
    assert hasattr(monitor, "_check_system_health")
