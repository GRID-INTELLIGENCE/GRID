"""
Tests for honor decay mechanism validation.

Ensures honor decays over time when not actively maintained,
and level transitions work correctly.
"""

import pytest

from Arena.the_chase.python.src.the_chase.overwatch.rewards import (
    Achievement,
    AchievementType,
    CharacterRewardState,
    RewardLevel,
)


class TestHonorDecayMechanism:
    """Test suite for honor decay mechanism."""

    def test_honor_decay_applies_correctly(self):
        """Verify honor decays by specified rate."""
        rewards = CharacterRewardState()
        rewards.add_achievement(Achievement(AchievementType.VICTORY, 50))
        assert rewards.honor == 50.0

        rewards.decay_honor(rate=0.01)
        assert rewards.honor == 49.5  # 1% decay

    def test_honor_decay_zero_rate(self):
        """Verify zero decay rate maintains honor."""
        rewards = CharacterRewardState()
        rewards.add_achievement(Achievement(AchievementType.VICTORY, 100))
        rewards.decay_honor(rate=0.0)
        assert rewards.honor == 100.0

    def test_honor_decay_full_rate(self):
        """Verify 100% decay rate reduces honor to zero."""
        rewards = CharacterRewardState()
        rewards.add_achievement(Achievement(AchievementType.VICTORY, 100))
        rewards.decay_honor(rate=1.0)
        assert rewards.honor == 0.0

    def test_honor_decay_multiple_calls(self):
        """Verify multiple decay calls compound correctly."""
        rewards = CharacterRewardState()
        rewards.add_achievement(Achievement(AchievementType.MILESTONE, 100))
        assert rewards.honor == 100.0

        rewards.decay_honor(rate=0.1)
        assert rewards.honor == 90.0

        rewards.decay_honor(rate=0.1)
        assert rewards.honor == 81.0  # 90 * 0.9

    def test_honor_never_negative(self):
        """Verify honor never goes below zero."""
        rewards = CharacterRewardState()
        rewards.add_achievement(Achievement(AchievementType.SKILL, 10))
        for _ in range(100):
            rewards.decay_honor(rate=0.5)
        assert rewards.honor >= 0.0

    def test_honor_decay_default_rate(self):
        """Verify default decay rate (1%) works."""
        rewards = CharacterRewardState()
        rewards.add_achievement(Achievement(AchievementType.VICTORY, 100))
        rewards.decay_honor()  # Default rate 0.01
        assert rewards.honor == 99.0


class TestRewardLevelTransitions:
    """Test suite for reward level transitions."""

    def test_neutral_to_acknowledged(self):
        """Verify transition from NEUTRAL to ACKNOWLEDGED."""
        rewards = CharacterRewardState()
        assert rewards.level == RewardLevel.NEUTRAL

        rewards.add_achievement(Achievement(AchievementType.SKILL, 25))
        assert rewards.level == RewardLevel.ACKNOWLEDGED

    def test_acknowledged_to_rewarded(self):
        """Verify transition from ACKNOWLEDGED to REWARDED."""
        rewards = CharacterRewardState()
        rewards.add_achievement(Achievement(AchievementType.MILESTONE, 50))
        assert rewards.level == RewardLevel.REWARDED

    def test_rewarded_to_promoted(self):
        """Verify transition from REWARDED to PROMOTED."""
        rewards = CharacterRewardState()
        rewards.add_achievement(Achievement(AchievementType.VICTORY, 100))
        assert rewards.level == RewardLevel.PROMOTED

    def test_level_downgrade_on_decay(self):
        """Verify level can downgrade when honor decays."""
        rewards = CharacterRewardState()
        rewards.add_achievement(Achievement(AchievementType.VICTORY, 100))
        assert rewards.level == RewardLevel.PROMOTED

        rewards.decay_honor(rate=0.4)  # 100 * 0.6 = 60, which is REWARDED
        assert rewards.honor == 60.0
        assert rewards.level == RewardLevel.REWARDED

    def test_level_downgrade_to_neutral(self):
        """Verify level can decay to NEUTRAL."""
        rewards = CharacterRewardState()
        rewards.add_achievement(Achievement(AchievementType.VICTORY, 100))
        assert rewards.level == RewardLevel.PROMOTED

        for _ in range(10):
            rewards.decay_honor(rate=0.2)
        assert rewards.level == RewardLevel.NEUTRAL

    def test_boundary_25_exactly(self):
        """Verify level at exactly 25 honor points."""
        rewards = CharacterRewardState()
        rewards.honor = 25.0
        rewards._update_level()
        assert rewards.level == RewardLevel.ACKNOWLEDGED

    def test_boundary_50_exactly(self):
        """Verify level at exactly 50 honor points."""
        rewards = CharacterRewardState()
        rewards.honor = 50.0
        rewards._update_level()
        assert rewards.level == RewardLevel.REWARDED

    def test_boundary_100_exactly(self):
        """Verify level at exactly 100 honor points."""
        rewards = CharacterRewardState()
        rewards.honor = 100.0
        rewards._update_level()
        assert rewards.level == RewardLevel.PROMOTED


class TestAchievementSystem:
    """Test suite for achievement system."""

    def test_add_victory_achievement(self):
        """Verify victory achievements add honor."""
        rewards = CharacterRewardState()
        rewards.add_achievement(Achievement(AchievementType.VICTORY, 50))
        assert len(rewards.achievements) == 1
        assert rewards.honor == 50.0

    def test_add_milestone_achievement(self):
        """Verify milestone achievements add honor."""
        rewards = CharacterRewardState()
        rewards.add_achievement(Achievement(AchievementType.MILESTONE, 30))
        assert len(rewards.achievements) == 1
        assert rewards.honor == 30.0

    def test_add_skill_achievement(self):
        """Verify skill achievements add honor."""
        rewards = CharacterRewardState()
        rewards.add_achievement(Achievement(AchievementType.SKILL, 20))
        assert len(rewards.achievements) == 1
        assert rewards.honor == 20.0

    def test_multiple_achievements(self):
        """Verify multiple achievements stack correctly."""
        rewards = CharacterRewardState()
        rewards.add_achievement(Achievement(AchievementType.VICTORY, 50))
        rewards.add_achievement(Achievement(AchievementType.MILESTONE, 30))
        rewards.add_achievement(Achievement(AchievementType.SKILL, 20))
        assert len(rewards.achievements) == 3
        assert rewards.honor == 100.0

    def test_achievement_tracks_type(self):
        """Verify achievements track their type."""
        achievement = Achievement(AchievementType.VICTORY, 50)
        assert achievement.type == AchievementType.VICTORY
        assert achievement.points == 50


class TestCharacterRewardStateEdgeCases:
    """Edge case tests for character reward state."""

    def test_initial_state(self):
        """Verify correct initial state."""
        rewards = CharacterRewardState()
        assert rewards.honor == 0.0
        assert rewards.level == RewardLevel.NEUTRAL
        assert len(rewards.achievements) == 0

    def test_decay_zero_honor(self):
        """Verify decaying zero honor stays at zero."""
        rewards = CharacterRewardState()
        rewards.decay_honor(rate=0.5)
        assert rewards.honor == 0.0

    def test_decay_with_small_honor(self):
        """Verify decay with small honor values."""
        rewards = CharacterRewardState()
        rewards.add_achievement(Achievement(AchievementType.SKILL, 1))
        rewards.decay_honor(rate=0.5)
        assert rewards.honor == 0.5

    def test_achievement_zero_points(self):
        """Verify zero-point achievements work."""
        rewards = CharacterRewardState()
        rewards.add_achievement(Achievement(AchievementType.SKILL, 0))
        assert rewards.honor == 0.0
        assert len(rewards.achievements) == 1

    def test_achievement_negative_points(self):
        """Verify negative-point achievements work."""
        rewards = CharacterRewardState()
        rewards.add_achievement(Achievement(AchievementType.SKILL, -10))
        assert rewards.honor == -10.0

    def test_large_decay_rate(self):
        """Verify large decay rates work correctly."""
        rewards = CharacterRewardState()
        rewards.add_achievement(Achievement(AchievementType.VICTORY, 100))
        rewards.decay_honor(rate=0.99)
        assert rewards.honor == pytest.approx(1.0, abs=0.01)

    def test_multiple_decay_to_zero(self):
        """Verify honor reaches exactly zero after multiple decays."""
        rewards = CharacterRewardState()
        rewards.add_achievement(Achievement(AchievementType.VICTORY, 3))
        for _ in range(100):
            rewards.decay_honor(rate=0.1)
        assert rewards.honor >= 0.0
        assert rewards.honor < 1.0


class TestHonorDecayIntegration:
    """Integration tests for honor decay with other systems."""

    def test_honor_decay_after_achievements(self):
        """Full workflow: add achievements then decay."""
        rewards = CharacterRewardState()
        rewards.add_achievement(Achievement(AchievementType.VICTORY, 100))
        assert rewards.level == RewardLevel.PROMOTED

        for _ in range(5):
            rewards.decay_honor(rate=0.1)

        assert rewards.honor < 100.0
        assert rewards.honor > 0.0

    def test_achievements_after_decay(self):
        """Full workflow: decay then add more achievements."""
        rewards = CharacterRewardState()
        rewards.add_achievement(Achievement(AchievementType.VICTORY, 50))
        rewards.decay_honor(rate=0.2)  # 40 honor
        rewards.add_achievement(Achievement(AchievementType.MILESTONE, 30))
        assert rewards.honor == 70.0
        assert rewards.level == RewardLevel.REWARDED
