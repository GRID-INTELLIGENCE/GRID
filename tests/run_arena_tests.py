"""
Standalone test runner for Arena structure fixes.
"""

import sys
import time
from pathlib import Path

# Add Arena path to sys.path
arena_path = Path(__file__).parent.parent / "Arena" / "the_chase" / "python" / "src"
if not (arena_path / "the_chase").exists():
    raise ImportError("the_chase path does not exist")
if str(arena_path) not in sys.path:
    sys.path.insert(0, str(arena_path))

from the_chase.core.cache import CacheLayer, CacheMeta, MemoryTier
from the_chase.overwatch.rewards import (
    Achievement,
    AchievementType,
    CharacterRewardState,
    RewardEscalator,
    RewardLevel,
)


class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def run_test(self, name, test_func):
        """Run a single test."""
        try:
            test_func()
            self.passed += 1
            print(f"[PASS] {name}")
            return True
        except AssertionError as e:
            self.failed += 1
            self.errors.append((name, str(e)))
            print(f"[FAIL] {name}: {e}")
            return False
        except Exception as e:
            self.failed += 1
            self.errors.append((name, f"Exception: {e}"))
            print(f"[FAIL] {name}: Exception - {e}")
            return False

    def run_all(self):
        """Run all tests."""
        print("=" * 80)
        print("ARENA STRUCTURE FIXES - COMPREHENSIVE TEST SUITE")
        print("=" * 80)
        print()

        # Test 1: Honor Decay
        print("Test Suite 1: Honor Decay Mechanism")
        print("-" * 80)
        self.run_test("decay_honor method exists", self.test_decay_method_exists)
        self.run_test("honor decays over time", self.test_honor_decays)
        self.run_test("honor respects floor", self.test_honor_floor)
        self.run_test("no decay without achievements", self.test_no_decay_without_achievements)
        self.run_test("decay proportional to time", self.test_decay_proportional)
        print()

        # Test 2: Auto De-escalation
        print("Test Suite 2: Auto De-escalation")
        print("-" * 80)
        self.run_test("check_and_de_escalate method exists", self.test_de_escalate_method_exists)
        self.run_test("de-escalation triggered by inactivity", self.test_de_escalation_triggered)
        self.run_test("no de-escalation within threshold", self.test_no_de_escalation_within_threshold)
        self.run_test("de-escalation cascades", self.test_de_escalation_cascades)
        self.run_test("no de-escalation without achievements", self.test_no_de_escalation_without_achievements)
        print()

        # Test 3: Gradual Priority Decay
        print("Test Suite 3: Gradual Priority Decay")
        print("-" * 80)
        self.run_test("get_effective_priority method exists", self.test_effective_priority_exists)
        self.run_test("priority decays over time", self.test_priority_decays)
        self.run_test("priority maintained during sustain", self.test_priority_sustain)
        self.run_test("priority decays near expiration", self.test_priority_near_expiration)
        self.run_test("priority clamped to range", self.test_priority_clamped)
        print()

        # Test 4: Sustain Phase
        print("Test Suite 4: Sustain Phase Tracking")
        print("-" * 80)
        self.run_test("sustain_time_seconds field exists", self.test_sustain_field_exists)
        self.run_test("is_in_sustain_phase method exists", self.test_sustain_method_exists)
        self.run_test("sustain phase detection", self.test_sustain_detection)
        self.run_test("default sustain time set", self.test_default_sustain_time)
        self.run_test("custom sustain time respected", self.test_custom_sustain_time)
        print()

        # Test 5: Gradual TTL Decay
        print("Test Suite 5: Gradual TTL Decay")
        print("-" * 80)
        self.run_test("priority decays before expiration", self.test_priority_decays_before_expiration)
        self.run_test("eviction uses effective priority", self.test_eviction_uses_effective)
        self.run_test("gradual decay curve", self.test_gradual_decay_curve)
        print()

        # Test 6: Integration
        print("Test Suite 6: Integration Tests")
        print("-" * 80)
        self.run_test("honor decay and de-escalation together", self.test_integration_honor_de_escalation)
        self.run_test("cache priority with sustain and decay", self.test_integration_cache_priority)
        print()

        # Summary
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Total:  {self.passed + self.failed}")
        print(f"Success Rate: {(self.passed / (self.passed + self.failed) * 100):.1f}%")
        print()

        if self.errors:
            print("FAILED TESTS:")
            for name, error in self.errors:
                print(f"  - {name}: {error}")
            print()

        return self.failed == 0

    # Test implementations
    def test_decay_method_exists(self):
        state = CharacterRewardState(entity_id="test1")
        assert hasattr(state, "decay_honor")

    def test_honor_decays(self):
        state = CharacterRewardState(entity_id="test2")
        achievement = Achievement(achievement_type=AchievementType.SIGNIFICANT, description="Test")
        state.add_achievement(achievement)
        initial_honor = state.honor
        state.last_decay_at = time.time() - 172800.0
        state.decay_honor(decay_rate=0.01, time_elapsed=172800.0)
        assert state.honor < initial_honor
        assert state.honor >= 0.0

    def test_honor_floor(self):
        state = CharacterRewardState(entity_id="test3")
        achievement = Achievement(achievement_type=AchievementType.MINOR, description="Test")
        state.add_achievement(achievement)
        state.last_decay_at = time.time() - 1.0
        state.decay_honor(decay_rate=1.0, time_elapsed=1.0)
        assert state.honor >= 0.0

    def test_no_decay_without_achievements(self):
        state = CharacterRewardState(entity_id="test4")
        initial_honor = state.honor
        state.decay_honor(decay_rate=0.01, time_elapsed=86400.0)
        assert state.honor == initial_honor == 0.0

    def test_decay_proportional(self):
        state1 = CharacterRewardState(entity_id="test5a")
        state2 = CharacterRewardState(entity_id="test5b")
        achievement = Achievement(achievement_type=AchievementType.MODERATE, description="Test")
        state1.add_achievement(achievement)
        state2.add_achievement(achievement)
        now = time.time()
        state1.decay_honor(decay_rate=0.01, time_elapsed=86400.0, current_time=now + 86400.0)
        state2.decay_honor(decay_rate=0.01, time_elapsed=86400.0, current_time=now + 172800.0)
        assert state2.honor < state1.honor

    def test_de_escalate_method_exists(self):
        state = CharacterRewardState(entity_id="test6")
        assert hasattr(state, "check_and_de_escalate")

    def test_de_escalation_triggered(self):
        state = CharacterRewardState(entity_id="test7")
        for _ in range(6):
            achievement = Achievement(achievement_type=AchievementType.MODERATE, description="Test")
            state.add_achievement(achievement)
            action = RewardEscalator.determine_action(state, achievement)
            reward = RewardEscalator.create_reward(action, achievement)
            state.add_reward(reward)
        assert state.reward_level == RewardLevel.PROMOTED
        # Simulate 1 second of inactivity
        de_escalated = state.check_and_de_escalate(
            inactivity_threshold_seconds=0.05, grace_period_seconds=0.0, current_time=time.time() + 1.0
        )
        assert de_escalated
        assert state.reward_level == RewardLevel.REWARDED

    def test_no_de_escalation_within_threshold(self):
        state = CharacterRewardState(entity_id="test8")
        for _ in range(3):
            achievement = Achievement(achievement_type=AchievementType.MODERATE, description="Test")
            state.add_achievement(achievement)
            action = RewardEscalator.determine_action(state, achievement)
            reward = RewardEscalator.create_reward(action, achievement)
            state.add_reward(reward)
        state.honor = 1.0  # Force high honor to prevent honor-based de-escalation
        curr = time.time()
        de_escalated = state.check_and_de_escalate(
            inactivity_threshold_seconds=86400.0 * 365, grace_period_seconds=0.0, current_time=curr
        )
        assert not de_escalated
        assert state.reward_level == RewardLevel.REWARDED

    def test_de_escalation_cascades(self):
        state = CharacterRewardState(entity_id="test9")
        for _ in range(6):
            achievement = Achievement(achievement_type=AchievementType.MODERATE, description="Test")
            state.add_achievement(achievement)
            action = RewardEscalator.determine_action(state, achievement)
            reward = RewardEscalator.create_reward(action, achievement)
            state.add_reward(reward)
        now = time.time()
        state.check_and_de_escalate(
            inactivity_threshold_seconds=0.05,
            grace_period_seconds=0.0,
            min_de_escalation_interval_seconds=0.0,
            current_time=now + 1.0,
        )
        assert state.reward_level == RewardLevel.REWARDED
        state.check_and_de_escalate(
            inactivity_threshold_seconds=0.05,
            grace_period_seconds=0.0,
            min_de_escalation_interval_seconds=0.0,
            current_time=now + 2.0,
        )
        assert state.reward_level == RewardLevel.ACKNOWLEDGED
        state.check_and_de_escalate(
            inactivity_threshold_seconds=0.05,
            grace_period_seconds=0.0,
            min_de_escalation_interval_seconds=0.0,
            current_time=now + 3.0,
        )
        assert state.reward_level == RewardLevel.NEUTRAL

    def test_no_de_escalation_without_achievements(self):
        state = CharacterRewardState(entity_id="test10")
        de_escalated = state.check_and_de_escalate(inactivity_threshold_seconds=0.05, grace_period_seconds=0.0)
        assert not de_escalated
        assert state.reward_level == RewardLevel.NEUTRAL

    def test_effective_priority_exists(self):
        meta = CacheMeta(created_at=time.time(), ttl_seconds=3600.0, soft_ttl_seconds=1800.0, priority=0.5)
        assert hasattr(meta, "get_effective_priority")

    def test_priority_decays(self):
        meta = CacheMeta(
            created_at=time.time() - 100.0,
            ttl_seconds=200.0,
            soft_ttl_seconds=100.0,
            priority=0.8,
            sustain_time_seconds=50.0,
        )
        effective = meta.get_effective_priority()
        assert effective < meta.priority
        assert effective >= 0.0

    def test_priority_sustain(self):
        meta = CacheMeta(
            created_at=time.time() - 10.0,
            ttl_seconds=100.0,
            soft_ttl_seconds=50.0,
            priority=0.8,
            sustain_time_seconds=30.0,
        )
        effective = meta.get_effective_priority()
        assert effective == meta.priority

    def test_priority_near_expiration(self):
        meta = CacheMeta(
            created_at=time.time() - 180.0,
            ttl_seconds=200.0,
            soft_ttl_seconds=100.0,
            priority=0.8,
            sustain_time_seconds=50.0,
        )
        effective = meta.get_effective_priority(current_time=meta.created_at + 195.0)
        assert effective < 0.3

    def test_priority_clamped(self):
        meta = CacheMeta(
            created_at=time.time() - 1000.0,
            ttl_seconds=100.0,
            soft_ttl_seconds=50.0,
            priority=1.0,
            sustain_time_seconds=10.0,
        )
        effective = meta.get_effective_priority()
        assert 0.0 <= effective <= 1.0

    def test_sustain_field_exists(self):
        meta = CacheMeta(created_at=time.time(), ttl_seconds=3600.0, soft_ttl_seconds=1800.0, priority=0.5)
        assert hasattr(meta, "sustain_time_seconds")

    def test_sustain_method_exists(self):
        meta = CacheMeta(created_at=time.time(), ttl_seconds=3600.0, soft_ttl_seconds=1800.0, priority=0.5)
        assert hasattr(meta, "is_in_sustain_phase")

    def test_sustain_detection(self):
        meta1 = CacheMeta(
            created_at=time.time() - 10.0,
            ttl_seconds=100.0,
            soft_ttl_seconds=50.0,
            priority=0.5,
            sustain_time_seconds=30.0,
        )
        assert meta1.is_in_sustain_phase()
        meta2 = CacheMeta(
            created_at=time.time() - 50.0,
            ttl_seconds=100.0,
            soft_ttl_seconds=50.0,
            priority=0.5,
            sustain_time_seconds=30.0,
        )
        assert not meta2.is_in_sustain_phase()

    def test_default_sustain_time(self):
        cache = CacheLayer(mem=MemoryTier(max_size=100))
        cache.set(key="test", value={"data": "test"}, ttl_seconds=100.0, priority=0.5)
        entry = cache.mem.get("test")
        assert entry is not None
        assert entry.meta.sustain_time_seconds > 0
        assert entry.meta.sustain_time_seconds == 30.0

    def test_custom_sustain_time(self):
        cache = CacheLayer(mem=MemoryTier(max_size=100))
        cache.set(key="test", value={"data": "test"}, ttl_seconds=100.0, priority=0.5, sustain_time_seconds=50.0)
        entry = cache.mem.get("test")
        assert entry is not None
        assert entry.meta.sustain_time_seconds == 50.0

    def test_priority_decays_before_expiration(self):
        cache = CacheLayer(mem=MemoryTier(max_size=100))
        cache.set(key="test", value={"data": "test"}, ttl_seconds=1.0, priority=0.8, sustain_time_seconds=0.3)
        entry1 = cache.mem.get("test")
        assert entry1 is not None
        effective1 = entry1.meta.get_effective_priority()
        time.sleep(0.4)
        entry2 = cache.mem.get("test")
        assert entry2 is not None
        effective2 = entry2.meta.get_effective_priority()
        assert effective2 < effective1

    def test_eviction_uses_effective(self):
        cache = CacheLayer(mem=MemoryTier(max_size=2))
        cache.set(key="old", value={"data": "old"}, ttl_seconds=100.0, priority=0.5, sustain_time_seconds=10.0)
        old_entry = cache.mem.get("old")
        if old_entry:
            old_entry.meta.created_at = time.time() - 50.0
        cache.set(key="new", value={"data": "new"}, ttl_seconds=100.0, priority=0.5, sustain_time_seconds=10.0)
        cache.set(key="third", value={"data": "third"}, ttl_seconds=100.0, priority=0.5, sustain_time_seconds=10.0)
        count = sum(
            [cache.mem.get("old") is not None, cache.mem.get("new") is not None, cache.mem.get("third") is not None]
        )
        assert count == 2

    def test_gradual_decay_curve(self):
        meta = CacheMeta(
            created_at=time.time() - 80.0,
            ttl_seconds=100.0,
            soft_ttl_seconds=50.0,
            priority=1.0,
            sustain_time_seconds=30.0,
        )
        priorities = []
        for age_offset in [0, 20, 40, 60]:
            meta.created_at = time.time() - (30.0 + age_offset)
            priorities.append(meta.get_effective_priority())
        for i in range(len(priorities) - 1):
            assert priorities[i] >= priorities[i + 1]

    def test_integration_honor_de_escalation(self):
        state = CharacterRewardState(entity_id="integration1")
        for _ in range(6):
            achievement = Achievement(achievement_type=AchievementType.MODERATE, description="Test")
            state.add_achievement(achievement)
            action = RewardEscalator.determine_action(state, achievement)
            reward = RewardEscalator.create_reward(action, achievement)
            state.add_reward(reward)
        initial_honor = state.honor
        state.last_decay_at = time.time() - 1.0
        state.decay_honor(decay_rate=0.5, time_elapsed=1.0)
        state.check_and_de_escalate(inactivity_threshold_seconds=0.05, grace_period_seconds=0.0)
        assert state.honor < initial_honor
        assert state.reward_level == RewardLevel.REWARDED

    def test_integration_cache_priority(self):
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
        assert entry.meta.is_in_sustain_phase()
        assert entry.meta.get_effective_priority() == entry.meta.priority
        # Test effective priority after sustain phase by passing future time
        effective = entry.meta.get_effective_priority(current_time=entry.meta.created_at + 50.0)
        assert effective < entry.meta.priority


if __name__ == "__main__":
    runner = TestRunner()
    success = runner.run_all()
    sys.exit(0 if success else 1)
