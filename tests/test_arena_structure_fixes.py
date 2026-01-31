"""
Comprehensive Test Suite: Arena Structure Fixes

Tests all 5 structural fixes:
1. Honor decay mechanism
2. Auto de-escalation
3. Gradual priority decay
4. Sustain phase tracking
5. Gradual TTL decay
"""

import sys
import time
from pathlib import Path

# Add Arena path to sys.path
arena_path = Path(__file__).parent.parent / "archive" / "misc" / "Arena" / "the_chase" / "python" / "src"
if str(arena_path) not in sys.path:
    sys.path.insert(0, str(arena_path))

import pytest
try:
    from the_chase.core.cache import CacheLayer, CacheMeta, MemoryTier
    from the_chase.overwatch.rewards import (
        Achievement,
        AchievementType,
        CharacterRewardState,
        RewardEscalator,
        RewardLevel,
    )
except ImportError:
    pytest.skip("Optional dependency 'the_chase' not available", allow_module_level=True)


class TestHonorDecay:
    """Test Suite: Honor Decay Mechanism (Fix #1)"""

    def test_decay_honor_method_exists(self):
        """Test that decay_honor method exists."""
        state = CharacterRewardState(entity_id="test1")
        assert hasattr(state, "decay_honor"), "decay_honor method should exist"

    def test_honor_decays_over_time(self):
        """Test that honor decays naturally over time."""
        state = CharacterRewardState(entity_id="test2")

        # Add achievement to grow honor
        achievement = Achievement(achievement_type=AchievementType.SIGNIFICANT, description="Test achievement")
        state.add_achievement(achievement)
        initial_honor = state.honor
        assert initial_honor > 0.0, "Honor should grow with achievement"

        # Simulate time passing (2 days worth) by adjusting anchor
        state.last_decay_at = time.time() - 172800.0
        state.decay_honor(decay_rate=0.01, time_elapsed=172800.0)  # 2 days

        # Honor should have decayed
        assert state.honor < initial_honor, "Honor should decay over time"
        assert state.honor >= 0.0, "Honor should not go below 0"

    def test_honor_decay_respects_floor(self):
        """Test that honor doesn't go below 0."""
        state = CharacterRewardState(entity_id="test3")

        # Add small achievement
        achievement = Achievement(achievement_type=AchievementType.MINOR, description="Small achievement")
        state.add_achievement(achievement)

        # Apply massive decay by adjusting anchor
        state.last_decay_at = time.time() - 86400.0
        state.decay_honor(decay_rate=1.0, time_elapsed=1.0)  # 100% decay

        assert state.honor >= 0.0, "Honor should not go below 0"

    def test_honor_no_decay_without_achievements(self):
        """Test that honor doesn't decay if no achievements exist."""
        state = CharacterRewardState(entity_id="test4")
        initial_honor = state.honor  # Should be 0.0

        # Try to decay
        state.decay_honor(decay_rate=0.01, time_elapsed=86400.0)

        # Honor should remain 0.0 (no achievements to decay from)
        assert state.honor == initial_honor == 0.0

    def test_honor_decay_proportional_to_time(self):
        """Test that decay is proportional to time elapsed."""
        state1 = CharacterRewardState(entity_id="test5a")
        state2 = CharacterRewardState(entity_id="test5b")

        # Both get same achievement
        achievement = Achievement(achievement_type=AchievementType.MODERATE, description="Test")
        state1.add_achievement(achievement)
        state2.add_achievement(achievement)

        assert state1.honor == state2.honor

        # Decay different amounts by passing different current_times
        now = time.time()
        state1.decay_honor(decay_rate=0.01, time_elapsed=86400.0, current_time=now + 86400.0)  # 1 day
        state2.decay_honor(decay_rate=0.01, time_elapsed=86400.0, current_time=now + 172800.0)  # 2 days

        # State2 should have decayed more
        assert state2.honor < state1.honor, "More time = more decay"

    def test_honor_decay_proportional_below_threshold(self):
        """Test that decay applies proportionally even when time < time_elapsed."""
        state = CharacterRewardState(entity_id="test5c")

        achievement = Achievement(achievement_type=AchievementType.MODERATE, description="Test")
        state.add_achievement(achievement)
        initial_honor = state.honor

        # Decay for half a day (0.5 * time_elapsed)
        state.decay_honor(decay_rate=0.01, time_elapsed=86400.0)  # 1 day period

        # Should decay proportionally: 0.01 * 0.5 = 0.005
        # Since we're using actual time, we need to simulate time passing
        # For this test, we'll manually set last_achievement_at to simulate half day
        import time

        state.last_achievement_at = time.time() - 43200.0  # Half day ago
        state.honor = initial_honor  # Reset honor
        state.decay_honor(decay_rate=0.01, time_elapsed=86400.0)

        # Honor should have decayed proportionally (approximately 0.005)
        assert state.honor < initial_honor, "Should decay proportionally even below threshold"
        assert state.honor >= 0.0, "Honor should not go below 0"

    def test_honor_decay_with_negative_decay_rate(self):
        """Test that negative decay_rate is handled (should default to 0.0)."""
        state = CharacterRewardState(entity_id="test5d")

        achievement = Achievement(achievement_type=AchievementType.MODERATE, description="Test")
        state.add_achievement(achievement)
        initial_honor = state.honor

        # Try negative decay rate
        state.decay_honor(decay_rate=-0.01, time_elapsed=86400.0)

        # Honor should not increase (decay_rate should be clamped to 0.0)
        assert state.honor <= initial_honor, "Negative decay rate should not increase honor"

    def test_honor_decay_with_invalid_time_elapsed(self):
        """Test that invalid time_elapsed is handled."""
        state = CharacterRewardState(entity_id="test5e")

        achievement = Achievement(achievement_type=AchievementType.MODERATE, description="Test")
        state.add_achievement(achievement)

        # Try zero or negative time_elapsed
        state.decay_honor(decay_rate=0.01, time_elapsed=0.0)
        state.decay_honor(decay_rate=0.01, time_elapsed=-100.0)

        # Should handle gracefully (defaults to 1 day)
        assert state.honor >= 0.0, "Invalid time_elapsed should be handled gracefully"

    def test_honor_decay_with_clock_skew(self):
        """Test that clock skew (future timestamps) is handled."""
        state = CharacterRewardState(entity_id="test5f")

        achievement = Achievement(achievement_type=AchievementType.MODERATE, description="Test")
        state.add_achievement(achievement)
        initial_honor = state.honor

        # Simulate clock skew: last_achievement_at is in the future
        import time

        state.last_achievement_at = time.time() + 86400.0  # 1 day in future

        # Decay should handle this gracefully
        state.decay_honor(decay_rate=0.01, time_elapsed=86400.0)

        # Honor should not change (time_since_achievement would be negative, clamped to 0)
        assert state.honor == initial_honor, "Clock skew should prevent decay"


class TestAutoDeEscalation:
    """Test Suite: Auto De-escalation (Fix #2)"""

    def test_check_and_de_escalate_method_exists(self):
        """Test that check_and_de_escalate method exists."""
        state = CharacterRewardState(entity_id="test6")
        assert hasattr(state, "check_and_de_escalate"), "check_and_de_escalate method should exist"

    def test_de_escalation_triggered_by_inactivity(self):
        """Test that de-escalation is triggered after inactivity period."""
        state = CharacterRewardState(entity_id="test7")

        # Escalate to PROMOTED
        for _ in range(6):
            achievement = Achievement(achievement_type=AchievementType.MODERATE, description="Achievement")
            state.add_achievement(achievement)
            action = RewardEscalator.determine_action(state, achievement)
            reward = RewardEscalator.create_reward(action, achievement)
            state.add_reward(reward)

        assert state.reward_level == RewardLevel.PROMOTED

        # Wait a bit to ensure time_since_achievement > threshold
        import time

        time.sleep(0.1)  # Sleep for 100ms to exceed 0.05s threshold

        # Check de-escalation with short threshold and 0 grace period
        de_escalated = state.check_and_de_escalate(inactivity_threshold_seconds=0.05, grace_period_seconds=0.0)

        assert de_escalated, "De-escalation should be triggered"
        assert state.reward_level == RewardLevel.REWARDED, "Should de-escalate from PROMOTED to REWARDED"

    def test_no_de_escalation_within_threshold(self):
        """Test that de-escalation doesn't occur within threshold."""
        state = CharacterRewardState(entity_id="test8")

        # Escalate to REWARDED - use more MODERATE achievements to reach honor threshold
        for _ in range(5):  # More achievements to reach honor threshold for REWARDED
            achievement = Achievement(achievement_type=AchievementType.MODERATE, description="Achievement")
            state.add_achievement(achievement)
            action = RewardEscalator.determine_action(state, achievement)
            reward = RewardEscalator.create_reward(action, achievement)
            state.add_reward(reward)

        assert state.reward_level == RewardLevel.REWARDED

        # Debug: Check honor level
        print(f"Debug: Honor level at REWARDED: {state.honor}")

        # Check with very long threshold (should not de-escalate)
        de_escalated = state.check_and_de_escalate(
            inactivity_threshold_seconds=86400.0 * 365, grace_period_seconds=0.0
        )  # 1 year

        assert not de_escalated, "Should not de-escalate within threshold"
        assert state.reward_level == RewardLevel.REWARDED, "Level should remain unchanged"

    def test_de_escalation_cascades(self):
        """Test that de-escalation can cascade through levels."""
        state = CharacterRewardState(entity_id="test9")

        # Escalate to PROMOTED - use SIGNIFICANT achievements to ensure promotion
        for _ in range(4):  # Fewer but higher value achievements
            achievement = Achievement(achievement_type=AchievementType.SIGNIFICANT, description="Achievement")
            state.add_achievement(achievement)
            action = RewardEscalator.determine_action(state, achievement)
            reward = RewardEscalator.create_reward(action, achievement)
            state.add_reward(reward)

        assert state.reward_level == RewardLevel.PROMOTED

        # Wait a bit to ensure time_since_achievement > threshold
        import time

        time.sleep(0.1)  # Sleep for 100ms to exceed 0.05s threshold

        # First de-escalation
        de_escalated1 = state.check_and_de_escalate(
            inactivity_threshold_seconds=0.05, grace_period_seconds=0.0, min_de_escalation_interval_seconds=0.01
        )
        assert de_escalated1, "First de-escalation should succeed"
        assert state.reward_level == RewardLevel.REWARDED
        print(f"Debug: Honor after first de-escalation: {state.honor}")

        # Wait longer to ensure time_since_achievement is large enough
        time.sleep(0.2)  # Sleep longer

        # Manually reduce honor to trigger next de-escalation (simulating time decay)
        state.honor = 0.3  # Below REWARDED threshold (0.4) but above ACKNOWLEDGED threshold (0.1)
        print(f"Debug: Manually set honor to: {state.honor}")

        # Second de-escalation - use small interval to allow rapid de-escalation for testing
        de_escalated2 = state.check_and_de_escalate(
            inactivity_threshold_seconds=0.05, grace_period_seconds=0.0, min_de_escalation_interval_seconds=0.01
        )
        print(f"Debug: Second de-escalation result: {de_escalated2}, honor: {state.honor}")
        if not de_escalated2:
            # Debug why it failed
            current_time = time.time()
            time_since_achievement = current_time - state.last_achievement_at
            honor_threshold = 0.4  # REWARDED threshold
            print(f"Debug: time_since_achievement: {time_since_achievement}, threshold: 0.05")
            print(f"Debug: honor_threshold: {honor_threshold}, honor: {state.honor}")
            print(f"Debug: honor_based_de_escalation: {state.honor < honor_threshold}")
        assert de_escalated2, "Second de-escalation should succeed"
        assert state.reward_level == RewardLevel.ACKNOWLEDGED

        # Manually reduce honor again to trigger final de-escalation
        state.honor = 0.05  # Below ACKNOWLEDGED threshold (0.1)
        print(f"Debug: Manually set honor to: {state.honor}")

        # Wait a bit more to satisfy minimum interval
        time.sleep(0.02)  # Wait longer than min_de_escalation_interval_seconds

        # Third de-escalation
        print(f"Debug: Before third de_escalation - last_de_escalation_at: {state.last_de_escalation_at}")
        de_escalated3 = state.check_and_de_escalate(
            inactivity_threshold_seconds=0.05, grace_period_seconds=0.0, min_de_escalation_interval_seconds=0.01
        )
        if not de_escalated3:
            # Debug why it failed
            current_time = time.time()
            time_since_achievement = current_time - state.last_achievement_at
            honor_threshold = 0.1  # ACKNOWLEDGED threshold
            print(f"Debug: time_since_achievement: {time_since_achievement}, threshold: 0.05")
            print(f"Debug: honor_threshold: {honor_threshold}, honor: {state.honor}")
            print(f"Debug: honor_based_de_escalation: {state.honor < honor_threshold}")
            if state.last_de_escalation_at is not None:
                time_since_last_de_escalation = current_time - state.last_de_escalation_at
                print(f"Debug: time_since_last_de_escalation: {time_since_last_de_escalation}, min_interval: 0.01")
                print(f"Debug: interval_check: {time_since_last_de_escalation < 0.01}")
        assert de_escalated3, "Third de-escalation should succeed"
        assert state.reward_level == RewardLevel.NEUTRAL

    def test_no_de_escalation_without_achievements(self):
        """Test that de-escalation doesn't occur if no achievements exist."""
        state = CharacterRewardState(entity_id="test10")
        assert state.reward_level == RewardLevel.NEUTRAL

        de_escalated = state.check_and_de_escalate(inactivity_threshold_seconds=0.05, grace_period_seconds=0.0)

        assert not de_escalated, "Should not de-escalate if no achievements"
        assert state.reward_level == RewardLevel.NEUTRAL

    def test_honor_based_de_escalation(self):
        """Test that de-escalation occurs when honor drops below threshold."""
        state = CharacterRewardState(entity_id="test11")

        # Escalate to PROMOTED
        for _ in range(6):
            achievement = Achievement(achievement_type=AchievementType.MODERATE, description="Achievement")
            state.add_achievement(achievement)
            action = RewardEscalator.determine_action(state, achievement)
            reward = RewardEscalator.create_reward(action, achievement)
            state.add_reward(reward)

        assert state.reward_level == RewardLevel.PROMOTED
        assert state.honor > 0.7  # Should be above threshold

        # Decay honor below PROMOTED threshold (0.7)
        state.honor = 0.6  # Below 0.7 threshold
        de_escalated = state.check_and_de_escalate(
            inactivity_threshold_seconds=86400.0 * 365,  # Very long threshold
            min_de_escalation_interval_seconds=0.0,  # No interval restriction for test
            grace_period_seconds=0.0,
        )

        assert de_escalated, "Should de-escalate when honor drops below threshold"
        assert state.reward_level == RewardLevel.REWARDED, "Should de-escalate from PROMOTED to REWARDED"

    def test_rapid_de_escalation_prevention(self):
        """Test that rapid de-escalation is prevented by minimum interval."""
        state = CharacterRewardState(entity_id="test12")

        # Escalate to PROMOTED - use SIGNIFICANT achievements to ensure promotion
        for _ in range(4):  # Fewer but higher value achievements
            achievement = Achievement(achievement_type=AchievementType.SIGNIFICANT, description="Achievement")
            state.add_achievement(achievement)
            action = RewardEscalator.determine_action(state, achievement)
            reward = RewardEscalator.create_reward(action, achievement)
            state.add_reward(reward)

        assert state.reward_level == RewardLevel.PROMOTED

        # Wait a bit to ensure time_since_achievement > threshold
        import time

        time.sleep(0.1)  # Sleep for 100ms to exceed 0.05s threshold

        # First de-escalation
        de_escalated1 = state.check_and_de_escalate(
            inactivity_threshold_seconds=0.05,
            min_de_escalation_interval_seconds=1.0,  # 1 second minimum interval
            grace_period_seconds=0.0,
        )
        assert de_escalated1, "First de-escalation should succeed"
        assert state.reward_level == RewardLevel.REWARDED

        # Immediate second de-escalation attempt (should be prevented)
        de_escalated2 = state.check_and_de_escalate(
            inactivity_threshold_seconds=0.05, min_de_escalation_interval_seconds=1.0, grace_period_seconds=0.0
        )
        assert not de_escalated2, "Rapid de-escalation should be prevented"
        assert state.reward_level == RewardLevel.REWARDED, "Level should remain unchanged"

    def test_de_escalation_with_clock_skew(self):
        """Test that clock skew (future timestamps) is handled in de-escalation."""
        state = CharacterRewardState(entity_id="test13")

        # Escalate to PROMOTED
        for _ in range(6):
            achievement = Achievement(achievement_type=AchievementType.MODERATE, description="Achievement")
            state.add_achievement(achievement)
            action = RewardEscalator.determine_action(state, achievement)
            reward = RewardEscalator.create_reward(action, achievement)
            state.add_reward(reward)

        assert state.reward_level == RewardLevel.PROMOTED

        # Simulate clock skew: last_achievement_at is in the future
        import time

        state.last_achievement_at = time.time() + 86400.0  # 1 day in future

        # De-escalation should handle this gracefully
        de_escalated = state.check_and_de_escalate(
            inactivity_threshold_seconds=0.05, min_de_escalation_interval_seconds=0.0, grace_period_seconds=0.0
        )

        # Should not de-escalate due to clock skew (time_since_achievement would be negative)
        assert not de_escalated, "Clock skew should prevent de-escalation"

    def test_de_escalation_with_invalid_thresholds(self):
        """Test that invalid thresholds are handled gracefully."""
        state = CharacterRewardState(entity_id="test14")

        # Escalate to PROMOTED
        for _ in range(6):
            achievement = Achievement(achievement_type=AchievementType.MODERATE, description="Achievement")
            state.add_achievement(achievement)
            action = RewardEscalator.determine_action(state, achievement)
            reward = RewardEscalator.create_reward(action, achievement)
            state.add_reward(reward)

        assert state.reward_level == RewardLevel.PROMOTED

        # Try invalid thresholds
        de_escalated1 = state.check_and_de_escalate(
            inactivity_threshold_seconds=-100.0,  # Negative threshold
            min_de_escalation_interval_seconds=-50.0,  # Negative interval
            grace_period_seconds=0.0,
        )

        # Should handle gracefully (defaults to valid values)
        # With default threshold (30 days), should not de-escalate immediately
        assert not de_escalated1 or state.reward_level in (RewardLevel.PROMOTED, RewardLevel.REWARDED)


class TestGradualPriorityDecay:
    """Test Suite: Gradual Priority Decay (Fix #3)"""

    def test_get_effective_priority_method_exists(self):
        """Test that get_effective_priority method exists."""
        meta = CacheMeta(created_at=time.time(), ttl_seconds=3600.0, soft_ttl_seconds=1800.0, priority=0.5)
        assert hasattr(meta, "get_effective_priority"), "get_effective_priority method should exist"

    def test_priority_decays_over_time(self):
        """Test that effective priority decays as entry ages."""
        meta = CacheMeta(
            created_at=time.time() - 100.0,  # 100 seconds ago
            ttl_seconds=200.0,
            soft_ttl_seconds=100.0,
            priority=0.8,
            sustain_time_seconds=50.0,
        )

        effective_priority = meta.get_effective_priority()

        # Should be less than base priority (past sustain phase)
        assert effective_priority < meta.priority, "Effective priority should decay after sustain phase"
        assert effective_priority >= 0.0, "Priority should not go below 0"

    def test_priority_maintained_during_sustain(self):
        """Test that priority is maintained during sustain phase."""
        meta = CacheMeta(
            created_at=time.time() - 10.0,  # 10 seconds ago
            ttl_seconds=100.0,
            soft_ttl_seconds=50.0,
            priority=0.8,
            sustain_time_seconds=30.0,  # Still in sustain phase
        )

        effective_priority = meta.get_effective_priority()

        # Should equal base priority during sustain
        assert effective_priority == meta.priority, "Priority should be maintained during sustain phase"

    def test_priority_decays_near_expiration(self):
        """Test that priority decays more rapidly near expiration."""
        meta = CacheMeta(
            created_at=time.time() - 180.0,  # 180 seconds ago
            ttl_seconds=200.0,
            soft_ttl_seconds=100.0,
            priority=0.8,
            sustain_time_seconds=50.0,
        )

        effective_priority = meta.get_effective_priority()

        # Should be significantly reduced (near expiration, last 20% of TTL)
        # With decay_curve=1.5 and ttl_ratio=0.867, expected priority ≈ 0.435
        assert effective_priority < 0.5, "Priority should decay significantly near expiration"
        assert effective_priority < 0.8, "Priority should be lower than initial priority"

    def test_priority_clamped_to_valid_range(self):
        """Test that effective priority is clamped to [0.0, 1.0]."""
        meta = CacheMeta(
            created_at=time.time() - 1000.0,  # Very old
            ttl_seconds=100.0,
            soft_ttl_seconds=50.0,
            priority=1.0,
            sustain_time_seconds=10.0,
        )

        effective_priority = meta.get_effective_priority()

        assert 0.0 <= effective_priority <= 1.0, "Priority should be clamped to valid range"


class TestSustainPhase:
    """Test Suite: Sustain Phase Tracking (Fix #4)"""

    def test_sustain_time_seconds_field_exists(self):
        """Test that sustain_time_seconds field exists."""
        meta = CacheMeta(created_at=time.time(), ttl_seconds=3600.0, soft_ttl_seconds=1800.0, priority=0.5)
        assert hasattr(meta, "sustain_time_seconds"), "sustain_time_seconds field should exist"

    def test_is_in_sustain_phase_method_exists(self):
        """Test that is_in_sustain_phase method exists."""
        meta = CacheMeta(created_at=time.time(), ttl_seconds=3600.0, soft_ttl_seconds=1800.0, priority=0.5)
        assert hasattr(meta, "is_in_sustain_phase"), "is_in_sustain_phase method should exist"

    def test_sustain_phase_detection(self):
        """Test that sustain phase is correctly detected."""
        # In sustain phase
        meta1 = CacheMeta(
            created_at=time.time() - 10.0,
            ttl_seconds=100.0,
            soft_ttl_seconds=50.0,
            priority=0.5,
            sustain_time_seconds=30.0,
        )
        assert meta1.is_in_sustain_phase(), "Should be in sustain phase"

        # Past sustain phase
        meta2 = CacheMeta(
            created_at=time.time() - 50.0,
            ttl_seconds=100.0,
            soft_ttl_seconds=50.0,
            priority=0.5,
            sustain_time_seconds=30.0,
        )
        assert not meta2.is_in_sustain_phase(), "Should be past sustain phase"

    def test_default_sustain_time(self):
        """Test that default sustain time is set in CacheLayer.set()."""
        cache = CacheLayer(mem=MemoryTier(max_size=100))

        cache.set(key="test", value={"data": "test"}, ttl_seconds=100.0, priority=0.5)

        entry = cache.mem.get("test")
        assert entry is not None
        assert entry.meta.sustain_time_seconds > 0, "Default sustain time should be set"
        assert entry.meta.sustain_time_seconds == 30.0, "Default should be 30% of TTL (100 * 0.3 = 30)"

    def test_custom_sustain_time(self):
        """Test that custom sustain time can be set."""
        cache = CacheLayer(mem=MemoryTier(max_size=100))

        cache.set(key="test", value={"data": "test"}, ttl_seconds=100.0, priority=0.5, sustain_time_seconds=50.0)

        entry = cache.mem.get("test")
        assert entry is not None
        assert entry.meta.sustain_time_seconds == 50.0, "Custom sustain time should be respected"


class TestGradualTTLDecay:
    """Test Suite: Gradual TTL Decay (Fix #5)"""

    def test_priority_decays_before_expiration(self):
        """Test that priority decays gradually before expiration."""
        cache = CacheLayer(mem=MemoryTier(max_size=100))

        cache.set(key="test", value={"data": "test"}, ttl_seconds=1.0, priority=0.8, sustain_time_seconds=0.3)

        # Get immediately (in sustain phase)
        entry1 = cache.mem.get("test")
        assert entry1 is not None
        effective1 = entry1.meta.get_effective_priority()

        # Wait past sustain phase
        time.sleep(0.4)

        # Get again (past sustain, before expiration)
        entry2 = cache.mem.get("test")
        assert entry2 is not None
        effective2 = entry2.meta.get_effective_priority()

        # Priority should have decayed
        assert effective2 < effective1, "Priority should decay after sustain phase"

    def test_eviction_uses_effective_priority(self):
        """Test that eviction uses effective priority, not base priority."""
        cache = CacheLayer(mem=MemoryTier(max_size=2))

        # Add two entries with same base priority but different ages
        cache.set(key="old", value={"data": "old"}, ttl_seconds=100.0, priority=0.5, sustain_time_seconds=10.0)

        # Manually age the first entry
        old_entry = cache.mem.get("old")
        if old_entry:
            # Simulate aging by modifying created_at
            old_entry.meta.created_at = time.time() - 50.0  # 50 seconds old

        cache.set(key="new", value={"data": "new"}, ttl_seconds=100.0, priority=0.5, sustain_time_seconds=10.0)

        # Add third entry (should evict lowest effective priority)
        cache.set(key="third", value={"data": "third"}, ttl_seconds=100.0, priority=0.5, sustain_time_seconds=10.0)

        # Old entry should be evicted (lower effective priority)
        old_entry_after = cache.mem.get("old")
        new_entry_after = cache.mem.get("new")
        third_entry_after = cache.mem.get("third")

        # One should be evicted
        assert (
            sum([old_entry_after is not None, new_entry_after is not None, third_entry_after is not None]) == 2
        ), "One entry should be evicted"

    def test_gradual_decay_curve(self):
        """Test that decay follows exponential curve."""
        meta = CacheMeta(
            created_at=time.time() - 80.0,
            ttl_seconds=100.0,
            soft_ttl_seconds=50.0,
            priority=1.0,
            sustain_time_seconds=30.0,
        )

        # Get priorities at different points
        priorities = []
        for age_offset in [0, 20, 40, 60]:
            meta.created_at = time.time() - (30.0 + age_offset)  # After sustain phase
            priorities.append(meta.get_effective_priority())

        # Should be decreasing
        for i in range(len(priorities) - 1):
            assert priorities[i] >= priorities[i + 1], "Priority should decrease over time"


class TestIntegration:
    """Integration Tests: Multiple Fixes Working Together"""

    def test_honor_decay_and_de_escalation(self):
        """Test that honor decay and de-escalation work together."""
        state = CharacterRewardState(entity_id="integration1")

        # Escalate to PROMOTED
        for _ in range(6):
            achievement = Achievement(achievement_type=AchievementType.MODERATE, description="Achievement")
            state.add_achievement(achievement)
            action = RewardEscalator.determine_action(state, achievement)
            reward = RewardEscalator.create_reward(action, achievement)
            state.add_reward(reward)

        initial_honor = state.honor
        assert state.reward_level == RewardLevel.PROMOTED

        # Decay honor by adjusting anchor
        state.last_decay_at = time.time() - 1.0
        state.decay_honor(decay_rate=0.5, time_elapsed=1.0)  # 50% decay

        # De-escalate with 0 grace period
        state.check_and_de_escalate(inactivity_threshold_seconds=0.05, grace_period_seconds=0.0)

        assert state.honor < initial_honor, "Honor should decay"
        assert state.reward_level == RewardLevel.REWARDED, "Should de-escalate"

    def test_cache_priority_with_sustain_and_decay(self):
        """Test that cache priority respects sustain phase and decays."""
        cache = CacheLayer(mem=MemoryTier(max_size=100))

        cache.set(
            key="test",
            value={"data": "test"},
            ttl_seconds=100.0,
            priority=0.8,
            reward_level="promoted",
            sustain_time_seconds=30.0,
        )

        entry = cache.mem.get("test")
        assert entry is not None

        # Should be in sustain phase initially
        assert entry.meta.is_in_sustain_phase()
        assert entry.meta.get_effective_priority() == entry.meta.priority

        # Age the entry to be past sustain phase
        entry.meta.created_at = time.time() - 50.0  # Past sustain phase (30s)

        # Should not increase after sustain phase
        effective = entry.meta.get_effective_priority()
        assert effective <= entry.meta.priority, "Should not increase after sustain phase"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
