"""Tests for merit standing engine: badges, scoring, roll numbers, and permission checks."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from application.mothership.security.merit_standing import (
    ACTION_CLASS_BADGE_REQUIREMENTS,
    ACTION_CLASS_SCOPE_REQUIREMENTS,
    BADGE_THRESHOLDS,
    ActionClass,
    Badge,
    MeritScoringEngine,
    MeritStanding,
    Scope,
    get_merit_engine,
)


# ---------------------------------------------------------------------------
# Badge and Threshold Tests
# ---------------------------------------------------------------------------


class TestBadges:
    def test_badge_values(self) -> None:
        """Badge values match expected strings."""
        assert Badge.B0_RESTRICTED.value == "B0_RESTRICTED"
        assert Badge.B1_TRUSTED.value == "B1_TRUSTED"
        assert Badge.B2_VERIFIED.value == "B2_VERIFIED"
        assert Badge.B3_PRIVILEGED.value == "B3_PRIVILEGED"

    def test_badge_ordering(self) -> None:
        """Badges are ordered B0 < B1 < B2 < B3."""
        assert Badge.B0_RESTRICTED.value < Badge.B1_TRUSTED.value
        assert Badge.B1_TRUSTED.value < Badge.B2_VERIFIED.value
        assert Badge.B2_VERIFIED.value < Badge.B3_PRIVILEGED.value

    def test_badge_thresholds(self) -> None:
        """Badge thresholds match spec."""
        assert BADGE_THRESHOLDS[Badge.B3_PRIVILEGED] == 80
        assert BADGE_THRESHOLDS[Badge.B2_VERIFIED] == 65
        assert BADGE_THRESHOLDS[Badge.B1_TRUSTED] == 45
        assert BADGE_THRESHOLDS[Badge.B0_RESTRICTED] == 0


class TestActionClassRequirements:
    def test_public_basic_requires_b0(self) -> None:
        """Public basic actions require B0_RESTRICTED minimum."""
        assert ACTION_CLASS_BADGE_REQUIREMENTS[ActionClass.PUBLIC_BASIC] == Badge.B0_RESTRICTED

    def test_analysis_read_requires_b1(self) -> None:
        """Analysis/read actions require B1_TRUSTED minimum."""
        assert ACTION_CLASS_BADGE_REQUIREMENTS[ActionClass.ANALYSIS_READ] == Badge.B1_TRUSTED

    def test_action_write_requires_b2(self) -> None:
        """Write actions require B2_VERIFIED minimum."""
        assert ACTION_CLASS_BADGE_REQUIREMENTS[ActionClass.ACTION_WRITE] == Badge.B2_VERIFIED

    def test_control_admin_requires_b3(self) -> None:
        """Admin/control actions require B3_PRIVILEGED minimum."""
        assert ACTION_CLASS_BADGE_REQUIREMENTS[ActionClass.CONTROL_ADMIN] == Badge.B3_PRIVILEGED

    def test_scope_requirements(self) -> None:
        """Scope requirements match action classes."""
        assert ACTION_CLASS_SCOPE_REQUIREMENTS[ActionClass.PUBLIC_BASIC] == set()
        assert ACTION_CLASS_SCOPE_REQUIREMENTS[ActionClass.ANALYSIS_READ] == {Scope.READ}
        assert ACTION_CLASS_SCOPE_REQUIREMENTS[ActionClass.ACTION_WRITE] == {Scope.READ, Scope.WRITE}
        assert ACTION_CLASS_SCOPE_REQUIREMENTS[ActionClass.CONTROL_ADMIN] == {
            Scope.READ,
            Scope.WRITE,
            Scope.ADMIN,
        }


# ---------------------------------------------------------------------------
# MeritStanding Tests
# ---------------------------------------------------------------------------


class TestMeritStanding:
    def test_new_entity_starts_b0(self) -> None:
        """New entities start with B0_RESTRICTED badge."""
        standing = MeritStanding(entity_id="test-entity")
        assert standing.badge == Badge.B0_RESTRICTED

    def test_new_entity_default_score(self) -> None:
        """New entities have default score of 45 (B1 threshold, but B0 due to badge)."""
        standing = MeritStanding(entity_id="test-entity")
        assert standing.score == 45

    def test_new_entity_clean_streak_zero(self) -> None:
        """New entities have zero clean streak."""
        standing = MeritStanding(entity_id="test-entity")
        assert standing.clean_streak == 0
        assert standing.clean_streak_bonus == 0

    def test_eligible_scopes_derived_from_badge(self) -> None:
        """Eligible scopes are derived from badge level."""
        b0 = MeritStanding(entity_id="b0", badge=Badge.B0_RESTRICTED)
        b1 = MeritStanding(entity_id="b1", badge=Badge.B1_TRUSTED)
        b2 = MeritStanding(entity_id="b2", badge=Badge.B2_VERIFIED)
        b3 = MeritStanding(entity_id="b3", badge=Badge.B3_PRIVILEGED)

        assert b0.eligible_scopes == set()
        assert b1.eligible_scopes == {Scope.READ, Scope.ANALYSIS}
        assert b2.eligible_scopes == {Scope.READ, Scope.WRITE, Scope.ANALYSIS}
        assert b3.eligible_scopes == {Scope.READ, Scope.WRITE, Scope.ADMIN, Scope.ANALYSIS, Scope.CONTROL}

    def test_to_dict_serialization(self) -> None:
        """MeritStanding serializes to dict correctly."""
        standing = MeritStanding(entity_id="test-entity")
        data = standing.to_dict()

        assert data["entity_id"] == "test-entity"
        assert data["badge"] == "B0_RESTRICTED"
        assert "score" in data
        assert "roll_number" in data
        assert "eligible_scopes" in data


# ---------------------------------------------------------------------------
# MeritScoringEngine Tests
# ---------------------------------------------------------------------------


class TestMeritScoringEngine:
    def test_get_or_create_standing(self) -> None:
        """Engine creates standing for new entities."""
        engine = MeritScoringEngine()
        standing = engine.get_or_create_standing("new-entity")

        assert standing is not None
        assert standing.entity_id == "new-entity"
        assert standing.badge == Badge.B0_RESTRICTED

    def test_get_standing_returns_none_for_unknown(self) -> None:
        """Engine returns None for unknown entities without creating."""
        engine = MeritScoringEngine()
        assert engine.get_standing("unknown") is None

    def test_record_violation_updates_penalty(self) -> None:
        """Recording a violation adds penalty points."""
        engine = MeritScoringEngine()
        standing = engine.record_violation("entity-a", penalty_points=10)

        assert standing.total_penalty_points == 10
        assert standing.violation_count == 1

    def test_record_violation_resets_clean_streak(self) -> None:
        """Recording a violation resets clean streak."""
        engine = MeritScoringEngine()
        engine.record_successful_action("entity-a")
        engine.record_successful_action("entity-a")
        assert engine.get_standing("entity-a") is not None
        assert engine.get_standing("entity-a").clean_streak == 2

        engine.record_violation("entity-a", penalty_points=5)
        assert engine.get_standing("entity-a").clean_streak == 0

    def test_critical_violation_sets_last_critical_at(self) -> None:
        """Critical violations set last_critical_at timestamp."""
        engine = MeritScoringEngine()
        standing = engine.record_violation("entity-a", penalty_points=10, is_critical=True)

        assert standing.last_critical_at is not None
        assert standing.recent_critical_penalty == 25  # CRITICAL_PENALTY_DEDUCTION

    def test_record_successful_action_increments_streak(self) -> None:
        """Successful actions increment clean streak."""
        engine = MeritScoringEngine()
        standing = engine.record_successful_action("entity-a")

        assert standing.clean_streak == 1

    def test_clean_streak_bonus_cap(self) -> None:
        """Clean streak bonus caps at 15."""
        engine = MeritScoringEngine()

        # Record 400 successful actions (400 // 20 = 20, but capped at 15)
        for _ in range(400):
            engine.record_successful_action("entity-a")

        standing = engine.get_standing("entity-a")
        assert standing.clean_streak == 400
        assert standing.clean_streak_bonus == 15  # MAX_CLEAN_STREAK_BONUS

    def test_review_adjustment_range(self) -> None:
        """Review adjustment must be in -10 to +10 range."""
        engine = MeritScoringEngine()

        with pytest.raises(ValueError, match="range"):
            engine.apply_review_adjustment("entity-a", adjustment=11)

        with pytest.raises(ValueError, match="range"):
            engine.apply_review_adjustment("entity-a", adjustment=-11)

    def test_review_adjustment_updates_score(self) -> None:
        """Review adjustment modifies score."""
        engine = MeritScoringEngine()
        standing = engine.get_or_create_standing("entity-a")

        # Initial score is 100 for new entity (100 - 0 - 0 + 0 + 0)
        initial_score = standing.score
        standing = engine.apply_review_adjustment("entity-a", adjustment=5)

        # Score = 100 + 5 = 105, clamped to 100
        assert standing.score == 100  # Max score
        assert standing.review_adjustment == 5


# ---------------------------------------------------------------------------
# Score Calculation Tests
# ---------------------------------------------------------------------------


class TestScoreCalculation:
    def test_new_entity_score_starts_at_45(self) -> None:
        """New entities start with score=45 (B1 threshold baseline)."""
        engine = MeritScoringEngine()
        standing = engine.get_or_create_standing("new-entity")
        # Default from MeritStanding dataclass
        assert standing.score == 45

    def test_penalty_reduces_score(self) -> None:
        """Penalty points reduce score."""
        engine = MeritScoringEngine()
        standing = engine.record_violation("entity-a", penalty_points=10)

        # Score = 100 - 10 = 90 (recalculate_score uses DEFAULT_BASE_SCORE=100)
        assert standing.score == 90

    def test_critical_penalty_applies_25_deduction(self) -> None:
        """Critical penalty adds 25 point deduction."""
        engine = MeritScoringEngine()
        standing = engine.record_violation("entity-a", penalty_points=10, is_critical=True)

        # Score = 100 - 10 - 25 = 65
        assert standing.score == 65
        assert standing.recent_critical_penalty == 25

    def test_clean_streak_bonus_adds_to_score(self) -> None:
        """Clean streak bonus adds to score."""
        engine = MeritScoringEngine()

        # Get initial standing and modify it
        standing = engine.get_or_create_standing("entity-a")

        # Manually set clean streak to 40 (40 // 20 = 2 bonus)
        standing.clean_streak = 40
        standing.clean_streak_bonus = 2
        engine._recalculate_score(standing)

        # Score = 100 - 0 - 0 + 2 + 0 = 102, clamped to 100
        assert standing.score == 100

    def test_score_clamped_to_100(self) -> None:
        """Score cannot exceed 100."""
        engine = MeritScoringEngine()
        standing = engine.get_or_create_standing("entity-a")

        # Set all bonuses to max
        standing.clean_streak_bonus = 15
        standing.review_adjustment = 10
        standing.total_penalty_points = 0
        standing.recent_critical_penalty = 0

        engine._recalculate_score(standing)

        assert standing.score == 100

    def test_score_clamped_to_0(self) -> None:
        """Score cannot go below 0."""
        engine = MeritScoringEngine()
        standing = engine.record_violation("entity-a", penalty_points=150)

        assert standing.score == 0


# ---------------------------------------------------------------------------
# Badge Calculation Tests
# ---------------------------------------------------------------------------


class TestBadgeCalculation:
    def test_score_below_45_is_b0(self) -> None:
        """Score below 45 results in B0_RESTRICTED."""
        engine = MeritScoringEngine()
        standing = engine.record_violation("entity-a", penalty_points=60)

        # Score = 100 - 60 = 40, which is < 45
        assert standing.score == 40
        assert standing.badge == Badge.B0_RESTRICTED

    def test_score_45_64_is_b1(self) -> None:
        """Score 45-64 results in B1_TRUSTED."""
        engine = MeritScoringEngine()
        standing = engine.get_or_create_standing("entity-a")

        # Set score via penalty to land in 45-64 range
        standing.total_penalty_points = 40  # 100 - 40 = 60
        engine._recalculate_score(standing)

        # Score = 60, which is in 45-64 range
        assert 45 <= standing.score <= 64
        assert standing.badge == Badge.B1_TRUSTED

    def test_score_65_79_is_b2(self) -> None:
        """Score 65-79 results in B2_VERIFIED."""
        engine = MeritScoringEngine()
        standing = engine.get_or_create_standing("entity-a")

        # Set score via penalty to land in 65-79 range
        standing.total_penalty_points = 30  # 100 - 30 = 70
        engine._recalculate_score(standing)

        # Score = 70, which is in 65-79 range
        assert 65 <= standing.score <= 79
        assert standing.badge == Badge.B2_VERIFIED

    def test_score_80_plus_is_b3(self) -> None:
        """Score 80+ with no recent critical results in B3_PRIVILEGED."""
        engine = MeritScoringEngine()
        # Record a successful action to trigger recalc
        standing = engine.record_successful_action("entity-a")

        # After successful action, score is recalculated
        # Score = 100 - 0 - 0 + 0 + 0 = 100, which is >= 80
        assert standing.score >= 80
        assert standing.badge == Badge.B3_PRIVILEGED

    def test_recent_critical_blocks_b3(self) -> None:
        """Recent critical event blocks B3 promotion."""
        engine = MeritScoringEngine()
        standing = engine.record_violation("entity-a", penalty_points=0, is_critical=True)

        # Score = 100 - 0 - 25 = 75 (critical penalty still applies)
        # Also, last_critical_at is set, blocking B3
        assert standing.score == 75  # 100 - 25 critical penalty
        assert standing.badge == Badge.B2_VERIFIED  # Not B3 due to recent critical

    def test_critical_older_than_30_days_allows_b3(self) -> None:
        """Critical event older than 30 days allows B3."""
        engine = MeritScoringEngine()
        standing = engine.record_violation("entity-a", penalty_points=0, is_critical=True)

        # Set last_critical_at to 31 days ago and recalc
        standing.last_critical_at = datetime.now(UTC) - timedelta(days=31)
        engine._recalculate_score(standing)

        # Critical penalty expires after 14 days
        # Score should now be >= 80 and B3 eligible
        assert standing.badge == Badge.B3_PRIVILEGED


# ---------------------------------------------------------------------------
# Roll Number Tests
# ---------------------------------------------------------------------------


class TestRollNumbers:
    def test_roll_number_assigned(self) -> None:
        """Roll numbers are assigned to entities."""
        engine = MeritScoringEngine()
        standing = engine.get_or_create_standing("entity-a")

        assert standing.roll_number >= 0

    def test_higher_score_better_roll(self) -> None:
        """Higher score entities have higher roll numbers."""
        engine = MeritScoringEngine()

        # Create two entities with different scores
        standing_a = engine.get_or_create_standing("entity-a")
        standing_b = engine.get_or_create_standing("entity-b")

        # Entity A has higher score
        standing_a.score = 80
        standing_b.score = 50

        engine._recalculate_roll_numbers()

        # Higher score = higher roll number
        assert standing_a.roll_number > standing_b.roll_number

    def test_lower_penalty_better_tiebreak(self) -> None:
        """Lower penalty points break score ties."""
        engine = MeritScoringEngine()

        standing_a = engine.get_or_create_standing("entity-a")
        standing_b = engine.get_or_create_standing("entity-b")

        # Same score, different penalties
        standing_a.score = 60
        standing_a.total_penalty_points = 5
        standing_b.score = 60
        standing_b.total_penalty_points = 10

        engine._recalculate_roll_numbers()

        assert standing_a.roll_number > standing_b.roll_number


# ---------------------------------------------------------------------------
# Permission Check Tests
# ---------------------------------------------------------------------------


class TestPermissionCheck:
    def test_b0_can_public_basic(self) -> None:
        """B0_RESTRICTED can access PUBLIC_BASIC."""
        engine = MeritScoringEngine()
        standing = engine.get_or_create_standing("entity-a")
        standing.badge = Badge.B0_RESTRICTED
        standing.eligible_scopes = set()
        engine._recalculate_roll_numbers()

        allowed, details = engine.check_permission("entity-a", ActionClass.PUBLIC_BASIC)
        assert allowed is True
        assert details["has_badge"] is True

    def test_b0_cannot_analysis_read(self) -> None:
        """B0_RESTRICTED cannot access ANALYSIS_READ."""
        engine = MeritScoringEngine()
        standing = engine.get_or_create_standing("entity-a")
        standing.badge = Badge.B0_RESTRICTED
        standing.eligible_scopes = set()

        allowed, details = engine.check_permission("entity-a", ActionClass.ANALYSIS_READ)
        assert allowed is False
        assert details["required_badge"] == "B1_TRUSTED"
        assert details["actual_badge"] == "B0_RESTRICTED"

    def test_b1_can_analysis_read(self) -> None:
        """B1_TRUSTED can access ANALYSIS_READ."""
        engine = MeritScoringEngine()
        standing = engine.get_or_create_standing("entity-a")
        standing.badge = Badge.B1_TRUSTED
        standing.eligible_scopes = {Scope.READ, Scope.ANALYSIS}

        allowed, _ = engine.check_permission("entity-a", ActionClass.ANALYSIS_READ)
        assert allowed is True

    def test_b2_can_action_write(self) -> None:
        """B2_VERIFIED can access ACTION_WRITE."""
        engine = MeritScoringEngine()
        standing = engine.get_or_create_standing("entity-a")
        standing.badge = Badge.B2_VERIFIED
        standing.eligible_scopes = {Scope.READ, Scope.WRITE, Scope.ANALYSIS}

        allowed, _ = engine.check_permission("entity-a", ActionClass.ACTION_WRITE)
        assert allowed is True

    def test_b3_can_control_admin(self) -> None:
        """B3_PRIVILEGED can access CONTROL_ADMIN."""
        engine = MeritScoringEngine()
        standing = engine.get_or_create_standing("entity-a")
        standing.badge = Badge.B3_PRIVILEGED
        standing.eligible_scopes = {Scope.READ, Scope.WRITE, Scope.ADMIN, Scope.ANALYSIS, Scope.CONTROL}

        allowed, _ = engine.check_permission("entity-a", ActionClass.CONTROL_ADMIN)
        assert allowed is True

    def test_scope_requirement(self) -> None:
        """Permission check includes scope validation."""
        engine = MeritScoringEngine()
        standing = engine.get_or_create_standing("entity-a")
        standing.badge = Badge.B2_VERIFIED
        standing.eligible_scopes = {Scope.READ, Scope.WRITE}

        allowed, details = engine.check_permission(
            "entity-a", ActionClass.ACTION_WRITE, required_scope=Scope.WRITE
        )
        assert allowed is True
        assert details["has_specific_scope"] is True


# ---------------------------------------------------------------------------
# Leaderboard Tests
# ---------------------------------------------------------------------------


class TestLeaderboard:
    def test_leaderboard_returns_sorted_entities(self) -> None:
        """Leaderboard returns entities sorted by roll number."""
        engine = MeritScoringEngine()

        # Create multiple entities
        for i in range(5):
            standing = engine.get_or_create_standing(f"entity-{i}")
            standing.score = 50 + i * 10

        engine._recalculate_roll_numbers()

        leaderboard = engine.get_leaderboard(limit=10)

        assert len(leaderboard) == 5
        # Highest roll number first (highest score)
        assert leaderboard[0]["score"] == 90  # entity-4 has highest score

    def test_leaderboard_limit(self) -> None:
        """Leaderboard respects limit parameter."""
        engine = MeritScoringEngine()

        for i in range(10):
            engine.get_or_create_standing(f"entity-{i}")

        leaderboard = engine.get_leaderboard(limit=3)
        assert len(leaderboard) == 3


# ---------------------------------------------------------------------------
# Global Engine Tests
# ---------------------------------------------------------------------------


class TestGlobalEngine:
    def test_get_merit_engine_returns_singleton(self) -> None:
        """get_merit_engine returns the global instance."""
        engine1 = get_merit_engine()
        engine2 = get_merit_engine()

        assert engine1 is engine2

    def test_global_engine_reset(self) -> None:
        """Global engine can be reset."""
        engine = get_merit_engine()
        engine.get_or_create_standing("test-entity")

        assert len(engine.get_all_standings()) > 0

        engine.reset()

        assert len(engine.get_all_standings()) == 0