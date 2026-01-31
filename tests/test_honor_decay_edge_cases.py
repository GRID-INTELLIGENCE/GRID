"""
Verification Tests for Phase 1: Honor Decay Edge Cases & De-escalation Grace Period (Standalone)
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
    from the_chase.overwatch.rewards import (
        Achievement,
        AchievementType,
        CharacterRewardState,
        RewardEscalator,
        RewardLevel,
    )
except ImportError:
    pytest.skip("Optional dependency 'the_chase' not available", allow_module_level=True)


def test_incremental_decay():
    """Test that multiple calls to decay_honor are incremental, not cumulative from achievement."""
    print("Running test_incremental_decay...")
    state = CharacterRewardState(entity_id="test_incremental")
    ach = Achievement(achievement_type=AchievementType.EXCEPTIONAL, description="Big Win")
    state.add_achievement(ach)
    initial_honor = state.honor

    now = time.time()
    state.last_decay_at = now - 86400.0

    state.decay_honor(decay_rate=0.01, time_elapsed=86400.0, current_time=now)
    honor_after_first = state.honor
    assert honor_after_first < initial_honor

    # Immediate second decay call (should decay 0.0)
    state.decay_honor(decay_rate=0.01, time_elapsed=86400.0, current_time=now)
    assert state.honor == honor_after_first
    print("[PASS]")


def test_decay_preserves_floor():
    """Test honor floor with new incremental decay."""
    print("Running test_decay_preserves_floor...")
    state = CharacterRewardState(entity_id="test_floor")
    state.add_achievement(Achievement(achievement_type=AchievementType.MINOR))

    now = time.time()
    state.last_decay_at = now - 86400.0
    state.decay_honor(decay_rate=10.0, time_elapsed=86400.0, current_time=now)
    assert state.honor == 0.0
    print("[PASS]")


def test_de_escalation_grace_period():
    """Test that de-escalation is blocked during the grace period."""
    print("Running test_de_escalation_grace_period...")
    state = CharacterRewardState(entity_id="test_grace")
    for _ in range(6):
        ach = Achievement(achievement_type=AchievementType.MODERATE)
        state.add_achievement(ach)
        action = RewardEscalator.determine_action(state, ach)
        state.add_reward(RewardEscalator.create_reward(action, ach))

    assert state.reward_level == RewardLevel.PROMOTED
    state.honor = 0.5

    now = time.time()
    # Initially within grace period
    de_escalated = state.check_and_de_escalate(
        inactivity_threshold_seconds=86400.0, grace_period_seconds=3600.0, current_time=now
    )
    assert not de_escalated, "Should NOT de-escalate within grace period"

    # Pass grace period
    de_escalated = state.check_and_de_escalate(
        inactivity_threshold_seconds=86400.0, grace_period_seconds=3600.0, current_time=now + 4000.0
    )
    assert de_escalated, "Should de-escalate after grace period"
    print("[PASS]")


if __name__ == "__main__":
    try:
        test_incremental_decay()
        test_decay_preserves_floor()
        test_de_escalation_grace_period()
        print("\nAll edge case tests PASSED")
    except AssertionError as e:
        print(f"\n[FAIL] {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)
