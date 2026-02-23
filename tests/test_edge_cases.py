"""
Edge case tests for The Chase core functionality.

Comprehensive edge case coverage for ADSR envelope, rewards system,
guardians, and integration points.
"""

import pytest

from Arena.the_chase.python.src.the_chase.core.adsr_envelope import (
    ADSREnvelope,
    EnvelopePhase,
)
from Arena.the_chase.python.src.the_chase.hardgate.aegis import (
    Aegis,
    ValidationResult,
)
from Arena.the_chase.python.src.the_chase.hardgate.compressor import (
    Compressor,
    RateLimitConfig,
)
from Arena.the_chase.python.src.the_chase.hardgate.lumen import (
    Lumen,
)
from Arena.the_chase.python.src.the_chase.overwatch.core import (
    MorphState,
    Overwatch,
    OverwatchConfig,
)
from Arena.the_chase.python.src.the_chase.overwatch.rewards import (
    Achievement,
    AchievementType,
    CharacterRewardState,
    RewardLevel,
)


class TestADSREnvelopeEdgeCases:
    """Edge cases for ADSR envelope."""

    @pytest.fixture
    def config(self) -> OverwatchConfig:
        """Create test configuration."""
        return OverwatchConfig()

    def test_extremely_small_attack_energy(self):
        """Test with very small attack energy."""
        config = OverwatchConfig(attack_energy=0.001)
        envelope = ADSREnvelope(config)
        envelope.trigger(current_time=0.0)
        envelope.update(0.001)
        assert envelope.quality >= 0.0

    def test_extremely_large_attack_energy(self):
        """Test with very large attack energy."""
        config = OverwatchConfig(attack_energy=100.0)
        envelope = ADSREnvelope(config)
        envelope.trigger(current_time=0.0)
        envelope.update(0.1)
        assert envelope.quality >= 0.0

    def test_zero_decay_rate(self):
        """Test with zero decay rate."""
        config = OverwatchConfig(decay_rate=0.0)
        envelope = ADSREnvelope(config)
        envelope.trigger(current_time=0.0)
        envelope.update(0.5)  # Sustain (sustain 0.15–1.15)
        envelope.update(1.5)  # Past sustain
        assert envelope.quality >= 0.0

    def test_very_high_decay_rate(self):
        """Test with very high decay rate."""
        config = OverwatchConfig(decay_rate=10.0)
        envelope = ADSREnvelope(config)
        envelope.trigger(current_time=0.0)
        envelope.update(0.5)  # In or past decay
        envelope.update(20.0)
        assert envelope.quality >= 0.0

    def test_zero_sustain_level(self):
        """Test with zero sustain level."""
        config = OverwatchConfig(sustain_level=0.0)
        envelope = ADSREnvelope(config)
        envelope.trigger(current_time=0.0)
        envelope.update(0.5)  # Sustain phase
        assert envelope.quality == 0.0

    def test_max_sustain_level(self):
        """Test with maximum sustain level."""
        config = OverwatchConfig(sustain_level=1.0)
        envelope = ADSREnvelope(config)
        envelope.trigger(current_time=0.0)
        envelope.update(0.5)  # Within sustain phase
        assert envelope.quality == 1.0

    def test_zero_release_rate(self):
        """Test with zero release rate."""
        config = OverwatchConfig(release_rate=0.0)
        envelope = ADSREnvelope(config)
        envelope.trigger(current_time=0.0)
        envelope.update(1.5)  # Past sustain → release
        assert envelope.quality >= 0.0

    def test_high_release_rate(self):
        """Test with high release rate."""
        config = OverwatchConfig(release_rate=5.0)
        envelope = ADSREnvelope(config)
        envelope.trigger(current_time=0.0)
        envelope.update(1.5)  # Past sustain → release
        assert envelope.quality >= 0.0

    def test_zero_release_threshold(self):
        """Test with zero release threshold."""
        config = OverwatchConfig(release_threshold=0.0)
        envelope = ADSREnvelope(config)
        envelope.trigger(current_time=0.0)
        envelope.update(1.5)
        assert envelope.quality >= 0.0

    def test_high_release_threshold(self):
        """Test with high release threshold."""
        config = OverwatchConfig(release_threshold=1.0)
        envelope = ADSREnvelope(config)
        envelope.trigger(current_time=0.0)
        envelope.update(1.5)
        assert envelope.quality >= 0.0

    def test_rapid_updates(self):
        """Test with rapid successive updates."""
        envelope = ADSREnvelope(OverwatchConfig())
        envelope.trigger(current_time=0.0)
        for i in range(1000):
            envelope.update(float(i) * 0.001)
        assert envelope.phase in [
            EnvelopePhase.ATTACK,
            EnvelopePhase.SUSTAIN,
            EnvelopePhase.DECAY,
            EnvelopePhase.RELEASE,
        ]

    def test_negative_time_updates(self):
        """Test with negative time values."""
        envelope = ADSREnvelope(OverwatchConfig())
        envelope.trigger(current_time=0.0)
        for i in range(10):
            envelope.update(float(-i))
        assert envelope.phase == EnvelopePhase.ATTACK

    def test_very_large_time_value(self):
        """Test with very large time values."""
        envelope = ADSREnvelope(OverwatchConfig())
        envelope.trigger(current_time=0.0)
        envelope.update(1_000_000.0)
        assert envelope.quality >= 0.0


class TestRewardsEdgeCases:
    """Edge cases for rewards system."""

    def test_maximum_honor_value(self):
        """Test with very high honor value."""
        rewards = CharacterRewardState()
        rewards.add_achievement(Achievement(AchievementType.VICTORY, 1_000_000))
        assert rewards.honor == 1_000_000
        assert rewards.level == RewardLevel.PROMOTED

    def test_negative_honor(self):
        """Test with negative honor."""
        rewards = CharacterRewardState()
        rewards.add_achievement(Achievement(AchievementType.SKILL, -100))
        assert rewards.honor == -100

    def test_fractional_honor(self):
        """Test with fractional honor points."""
        rewards = CharacterRewardState()
        rewards.add_achievement(Achievement(AchievementType.SKILL, 0.5))
        assert rewards.honor == 0.5

    def test_very_small_decay_rate(self):
        """Test with very small decay rate."""
        rewards = CharacterRewardState()
        rewards.add_achievement(Achievement(AchievementType.VICTORY, 100))
        rewards.decay_honor(rate=0.0001)
        assert rewards.honor < 100.0
        assert rewards.honor > 99.0

    def test_very_large_decay_rate(self):
        """Test with very large decay rate."""
        rewards = CharacterRewardState()
        rewards.add_achievement(Achievement(AchievementType.VICTORY, 100))
        rewards.decay_honor(rate=10.0)
        assert rewards.honor >= 0.0

    def test_many_small_achievements(self):
        """Test with many small achievements."""
        rewards = CharacterRewardState()
        for _ in range(1000):
            rewards.add_achievement(Achievement(AchievementType.SKILL, 1))
        assert rewards.honor == 1000.0
        assert len(rewards.achievements) == 1000

    def test_many_decay_cycles(self):
        """Test with many decay cycles."""
        rewards = CharacterRewardState()
        rewards.add_achievement(Achievement(AchievementType.VICTORY, 100))
        for _ in range(1000):
            rewards.decay_honor(rate=0.01)
        assert rewards.honor >= 0.0
        assert rewards.honor < 1.0

    def test_boundary_values(self):
        """Test honor at exact level boundaries."""
        tests = [
            (0.0, RewardLevel.NEUTRAL),
            (24.999, RewardLevel.NEUTRAL),
            (25.0, RewardLevel.ACKNOWLEDGED),
            (49.999, RewardLevel.ACKNOWLEDGED),
            (50.0, RewardLevel.REWARDED),
            (99.999, RewardLevel.REWARDED),
            (100.0, RewardLevel.PROMOTED),
        ]
        for honor, expected_level in tests:
            rewards = CharacterRewardState()
            rewards.honor = honor
            rewards._update_level()
            assert rewards.level == expected_level


class TestGuardianEdgeCases:
    """Edge cases for guardians."""

    def test_aegis_none_input(self):
        """Test Aegis with None input."""
        aegis = Aegis()
        result = aegis.validate_action({"key": None})
        assert isinstance(result, ValidationResult)

    def test_aegis_very_long_input(self):
        """Test Aegis with very long input."""
        aegis = Aegis()
        long_input = {"data": "x" * 1_000_000}
        result = aegis.validate_action(long_input)
        assert isinstance(result, ValidationResult)

    def test_aegis_nested_dict(self):
        """Test Aegis with deeply nested dictionary."""
        aegis = Aegis()
        nested = {"level1": {"level2": {"level3": {"value": "test"}}}}
        result = aegis.validate_action(nested)
        assert isinstance(result, ValidationResult)

    def test_aegis_special_characters(self):
        """Test Aegis with various special characters."""
        aegis = Aegis()
        special = {"data": "test<>&\"'\\x00\x01\x02"}
        result = aegis.validate_action(special)
        assert isinstance(result, ValidationResult)

    def test_compressor_very_small_window(self):
        """Test Compressor with very small window."""
        config = RateLimitConfig(requests_per_window=1, window_seconds=0.001)
        compressor = Compressor(config)
        result = compressor.check_rate_limit("user")
        assert result is not None

    def test_compressor_very_large_window(self):
        """Test Compressor with very large window."""
        config = RateLimitConfig(requests_per_window=1_000_000, window_seconds=1_000_000)
        compressor = Compressor(config)
        result = compressor.check_rate_limit("user")
        assert result is not None

    def test_compressor_special_identifier(self):
        """Test Compressor with special identifier characters."""
        config = RateLimitConfig()
        compressor = Compressor(config)
        special_ids = ["user@example.com", "user:tag", "user/tag", "user\\path"]
        for uid in special_ids:
            result = compressor.check_rate_limit(uid)
            assert result is not None

    def test_lumen_unicode_content(self):
        """Test Lumen with unicode content."""
        lumen = Lumen()
        unicode_text = "Hello 世界 🌍 Привет مرحبا"
        result = lumen.validate_boundary(unicode_text)
        assert isinstance(result, bool)

    def test_lumen_very_long_content(self):
        """Test Lumen with very long content."""
        lumen = Lumen()
        long_text = "a" * 1_000_000
        result = lumen.validate_boundary(long_text)
        assert isinstance(result, bool)

    def test_lumen_empty_and_whitespace(self):
        """Test Lumen with empty and whitespace content."""
        lumen = Lumen()
        assert lumen.validate_boundary("") is True
        assert lumen.validate_boundary("   ") is True
        assert lumen.validate_boundary("\n\t\r") is True


class TestIntegrationEdgeCases:
    """Edge cases for integrations."""

    def test_bridge_empty_cache(self):
        """Test ADSR-Arena bridge with empty cache."""
        from Arena.the_chase.python.src.the_chase.integration.adsr_arena import ADSRArenaBridge

        grid_adsr = ADSREnvelope(OverwatchConfig())

        class MockCache:
            def keys(self):
                return []

            @property
            def l1(self):
                return {}

        cache = MockCache()
        rewards = CharacterRewardState()

        bridge = ADSRArenaBridge(grid_adsr, cache, rewards)
        bridge.sync_sustain_phase()  # Should not raise

    def test_bridge_zero_honor(self):
        """Test ADSR-Arena bridge with zero honor."""
        from Arena.the_chase.python.src.the_chase.integration.adsr_arena import ADSRArenaBridge

        grid_adsr = ADSREnvelope(OverwatchConfig())
        cache = MockCacheLayer()
        rewards = CharacterRewardState()  # Zero honor

        bridge = ADSRArenaBridge(grid_adsr, cache, rewards)
        grid_adsr.update(20.0)  # Decay
        bridge.sync_decay_phase()  # Should not raise

    def test_hooks_no_registered_callbacks(self):
        """Test hooks with no registered callbacks."""
        from Arena.the_chase.python.src.the_chase.overwatch.hooks import OverwatchHooks

        hooks = OverwatchHooks()
        hooks.trigger_hook("pre_user_prompt", "test")  # Should not raise

    def test_mcp_no_servers(self):
        """Test MCP with no servers configured."""
        from Arena.the_chase.python.src.the_chase.overwatch.mcp import OverwatchMCP

        mcp = OverwatchMCP({})
        result = mcp.call_mcp_tool("any_server", "any_tool", {})
        assert result["status"] == "error"

    def test_arena_mode_no_models(self):
        """Test Arena Mode with no models."""
        from Arena.the_chase.python.src.the_chase.overwatch.arena_mode import OverwatchArenaMode

        arena = OverwatchArenaMode()
        results = arena.compare_models("test", [])
        assert results == {}

    def test_plan_mode_empty_task(self):
        """Test Plan Mode with empty task."""
        from Arena.the_chase.python.src.the_chase.overwatch.plan_mode import OverwatchPlanMode

        plan = OverwatchPlanMode()
        result = plan.create_plan("")
        assert "steps" in result


class TestStateTransitionEdgeCases:
    """Edge cases for state transitions."""

    def test_phase_transition_boundaries(self):
        """Test exact phase transition boundaries."""
        config = OverwatchConfig()
        envelope = ADSREnvelope(config)
        envelope.trigger(current_time=0.0)
        # Phase boundaries: attack 0–0.15, decay 0.15–0.40, sustain 0.40–1.40
        sustain_start = config.attack_energy + config.decay_rate  # 0.40

        envelope.update(sustain_start + 0.1)  # Just inside sustain
        assert envelope.phase == EnvelopePhase.SUSTAIN

        envelope.release(current_time=sustain_start + 0.5)
        envelope.update(sustain_start + 0.6)  # During release
        assert envelope.phase == EnvelopePhase.RELEASE

    def test_rapid_phase_changes(self):
        """Test rapid phase changes."""
        envelope = ADSREnvelope(OverwatchConfig())
        envelope.trigger(current_time=0.0)
        for i in range(20):
            envelope.update(float(i) * 0.1)  # 0.0 to 1.9
        assert envelope.phase in [
            EnvelopePhase.ATTACK,
            EnvelopePhase.DECAY,
            EnvelopePhase.SUSTAIN,
            EnvelopePhase.RELEASE,
            EnvelopePhase.IDLE,
        ]

    def test_level_transition_boundaries(self):
        """Test exact level transition boundaries."""
        tests = [24.99, 25.0, 25.01, 49.99, 50.0, 50.01, 99.99, 100.0, 100.01]
        for honor in tests:
            rewards = CharacterRewardState()
            rewards.honor = honor
            rewards._update_level()
            assert rewards.level in RewardLevel

    def test_morph_state_transitions(self):
        """Test MorphState transitions."""
        overwatch = Overwatch(OverwatchConfig())
        assert overwatch.morph_state == MorphState.GREEN


class TestConcurrencyEdgeCases:
    """Edge cases for concurrent operations."""

    def test_multiple_guardians_concurrent(self):
        """Test multiple guardians operating together."""
        aegis = Aegis()
        compressor = Compressor(RateLimitConfig())
        lumen = Lumen()

        # All should work independently
        aegis_result = aegis.validate_action({"test": "action"})
        compressor_result = compressor.check_rate_limit("user")
        lumen_result = lumen.validate_boundary("test data")

        assert isinstance(aegis_result, ValidationResult)
        assert compressor_result is not None
        assert isinstance(lumen_result, bool)

    def test_rewards_concurrent_access(self):
        """Test rewards system with concurrent-style access."""
        rewards = CharacterRewardState()

        # Simulate concurrent additions and decays
        for i in range(100):
            rewards.add_achievement(Achievement(AchievementType.SKILL, 10))
            rewards.decay_honor(rate=0.01)

        assert rewards.honor >= 0.0
        assert len(rewards.achievements) == 100


class TestBoundaryValueEdgeCases:
    """Boundary value analysis tests."""

    def test_config_boundary_values(self):
        """Test configuration with boundary values."""
        boundaries = [
            ("attack_energy", [0.001, 0.01, 1.0, 100.0]),  # Avoid 0.0 to prevent division by zero
            ("decay_rate", [0.0, 0.001, 1.0, 100.0]),
            ("sustain_level", [0.0, 0.001, 1.0]),
            ("release_rate", [0.0, 0.001, 1.0, 100.0]),
            ("release_threshold", [0.0, 0.001, 1.0]),
        ]

        for attr, values in boundaries:
            for value in values:
                config = OverwatchConfig(**{attr: value})
                envelope = ADSREnvelope(config)
                envelope.update(4.0)
                assert envelope.quality >= 0.0

    def test_rate_limit_boundaries(self):
        """Test rate limit configuration boundaries."""
        boundaries = [
            ("requests_per_window", [1, 100, 1_000_000]),  # Avoid 0
            ("window_seconds", [0.001, 1, 1_000_000]),  # Avoid 0
            ("block_duration_seconds", [0, 1, 300, 1_000_000]),
        ]

        for attr, values in boundaries:
            for value in values:
                config = RateLimitConfig(**{attr: value})
                compressor = Compressor(config)
                result = compressor.check_rate_limit("user")
                assert result is not None

    def test_achievement_point_boundaries(self):
        """Test achievement point boundaries."""
        boundaries = [-1_000_000, -1, 0, 1, 1_000_000]
        for points in boundaries:
            achievement = Achievement(AchievementType.SKILL, points)
            assert achievement.points == points


class TestErrorHandlingEdgeCases:
    """Error handling edge cases."""

    def test_invalid_config_type(self):
        """Test with invalid config type."""
        try:
            envelope = ADSREnvelope(None)
            envelope.update(4.0)
            assert envelope.quality >= 0.0
        except (AttributeError, TypeError):
            pass  # Expected for None config

    def test_malformed_action(self):
        """Test Aegis with malformed action."""
        aegis = Aegis()
        result = aegis.validate_action("string instead of dict")
        assert isinstance(result, ValidationResult)

    def test_cache_corruption_simulation(self):
        """Test bridge with simulated cache corruption."""
        from Arena.the_chase.python.src.the_chase.integration.adsr_arena import ADSRArenaBridge

        class BrokenCache:
            def keys(self):
                raise Exception("Cache corrupted")

            @property
            def l1(self):
                raise Exception("Cache corrupted")

        grid_adsr = ADSREnvelope(OverwatchConfig())
        cache = BrokenCache()
        rewards = CharacterRewardState()

        bridge = ADSRArenaBridge(grid_adsr, cache, rewards)
        # Should handle gracefully
        try:
            bridge.sync_sustain_phase()
        except Exception:
            pass  # Expected for broken cache


class MockCacheLayer:
    """Mock cache layer for testing."""

    def __init__(self):
        self.l1 = {}
        self.l2 = {}

    def keys(self):
        return self.l1.keys()
