"""
Rewards system for The Chase
"""

from enum import Enum


class RewardLevel(Enum):
    NEUTRAL = "neutral"
    ACKNOWLEDGED = "acknowledged"
    REWARDED = "rewarded"
    PROMOTED = "promoted"


class AchievementType(Enum):
    VICTORY = "victory"
    MILESTONE = "milestone"
    SKILL = "skill"
    SIGNIFICANT = "significant"
    MODERATE = "moderate"
    MINOR = "minor"
    EXCEPTIONAL = "exceptional"

    @property
    def default_points(self) -> int:
        """Default points for each achievement type."""
        return {
            AchievementType.VICTORY: 25,
            AchievementType.MILESTONE: 20,
            AchievementType.SKILL: 15,
            AchievementType.SIGNIFICANT: 12,
            AchievementType.MODERATE: 8,
            AchievementType.MINOR: 5,
            AchievementType.EXCEPTIONAL: 30,
        }[self]


class Achievement:
    """Individual achievements"""

    def __init__(self, achievement_type: AchievementType, points: int | None = None, description: str = ""):
        self.type = achievement_type
        self.points = points if points is not None else achievement_type.default_points
        self.description = description


class CharacterRewardState:
    """Player reward state"""

    def __init__(self, entity_id: str = "default"):
        self.entity_id = entity_id
        self.honor = 0.0
        self._level = RewardLevel.NEUTRAL
        self.achievements = []

    @property
    def level(self) -> RewardLevel:
        """Get current reward level."""
        return self._level

    @level.setter
    def level(self, value: RewardLevel):
        """Set reward level."""
        self._level = value

    @property
    def reward_level(self) -> RewardLevel:
        """Alias for level (test compatibility)."""
        return self._level

    @reward_level.setter
    def reward_level(self, value: RewardLevel):
        """Alias for level (test compatibility)."""
        self._level = value

    @property
    def achievement_count(self) -> int:
        """Return count of achievements."""
        return len(self.achievements)

    def add_achievement(self, achievement: Achievement):
        """Add achievement and increase honor"""
        self.achievements.append(achievement)
        self.honor += achievement.points
        self._update_level()

    def decay_honor(self, rate: float = 0.01):
        """Apply honor decay (MISSING FEATURE)"""
        self.honor = max(0.0, self.honor * (1 - rate))
        self._update_level()

    def _update_level(self):
        """Update reward level based on honor"""
        if self.honor >= 50:
            self._level = RewardLevel.PROMOTED
        elif self.honor >= 25:
            self._level = RewardLevel.REWARDED
        elif self.honor >= 10:
            self._level = RewardLevel.ACKNOWLEDGED
        else:
            self._level = RewardLevel.NEUTRAL
