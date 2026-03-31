"""Merit Standing Engine — Entity Roll-Number Model with Badge Thresholds.

Implements a strict-restricted baseline (normal preset) with entity-first identity.
Enforces access by role + scope + merit badge (threshold badges), not role alone.
Uses persistent runtime records to drive compounding perks (promotion) and blocked
scopes (demotion), with twice-weekly manual bonus/penalty review adjustments.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


def _entity_fingerprint(entity_id: str) -> str:
    """Non-reversible, log-safe identifier for entity ids."""
    digest = hashlib.sha256(entity_id.encode("utf-8", errors="replace")).hexdigest()
    return digest[:12]


# ---------------------------------------------------------------------------
# Enums and Constants
# ---------------------------------------------------------------------------


class Badge(StrEnum):
    """Merit badge levels based on standing score thresholds."""

    B0_RESTRICTED = "B0_RESTRICTED"  # < 45 points
    B1_TRUSTED = "B1_TRUSTED"  # 45-64 points
    B2_VERIFIED = "B2_VERIFIED"  # 65-79 points
    B3_PRIVILEGED = "B3_PRIVILEGED"  # >= 80 points, no high/critical in last 30 days


class ActionClass(StrEnum):
    """Action classes that map to badge requirements."""

    PUBLIC_BASIC = "public_basic"  # B0 required
    ANALYSIS_READ = "analysis_read"  # B1 required
    ACTION_WRITE = "action_write"  # B2 + write scope
    CONTROL_ADMIN = "control_admin"  # B3 + admin scope


class Scope(StrEnum):
    """Eligible scopes that can be unlocked through merit standing."""

    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    ANALYSIS = "analysis"
    CONTROL = "control"


# Badge thresholds (inclusive minimums)
BADGE_THRESHOLDS: dict[Badge, int] = {
    Badge.B3_PRIVILEGED: 80,
    Badge.B2_VERIFIED: 65,
    Badge.B1_TRUSTED: 45,
    Badge.B0_RESTRICTED: 0,
}

# Action class to required badge mapping
ACTION_CLASS_BADGE_REQUIREMENTS: dict[ActionClass, Badge] = {
    ActionClass.PUBLIC_BASIC: Badge.B0_RESTRICTED,
    ActionClass.ANALYSIS_READ: Badge.B1_TRUSTED,
    ActionClass.ACTION_WRITE: Badge.B2_VERIFIED,
    ActionClass.CONTROL_ADMIN: Badge.B3_PRIVILEGED,
}

# Action class to required scope mapping
ACTION_CLASS_SCOPE_REQUIREMENTS: dict[ActionClass, set[Scope]] = {
    ActionClass.PUBLIC_BASIC: set(),
    ActionClass.ANALYSIS_READ: {Scope.READ},
    ActionClass.ACTION_WRITE: {Scope.READ, Scope.WRITE},
    ActionClass.CONTROL_ADMIN: {Scope.READ, Scope.WRITE, Scope.ADMIN},
}

# Score calculation constants
DEFAULT_BASE_SCORE = 100
CRITICAL_PENALTY_DEDUCTION = 25
CLEAN_STREAK_BONUS_PER_20 = 1
MAX_CLEAN_STREAK_BONUS = 15
REVIEW_ADJUSTMENT_RANGE = (-10, 10)
CRITICAL_EVENT_WINDOW_DAYS = 14
B3_CLEAN_WINDOW_DAYS = 30


# ---------------------------------------------------------------------------
# Merit Standing Record
# ---------------------------------------------------------------------------


@dataclass
class MeritStanding:
    """
    Persistent runtime record for entity merit standing.

    This record drives:
    - Compounding perks (promotion) via clean_streak_bonus and review_adjustment
    - Blocked scopes (demotion) via critical penalties and total_penalty_points
    - Roll number ordering for priority access
    """

    entity_id: str
    # Baseline: new entities start at the B1 threshold with READ/ANALYSIS scopes.
    # This matches the documented "generous baseline" and avoids a contradictory
    # state where score==45 but badge remains B0_RESTRICTED.
    badge: Badge = Badge.B1_TRUSTED
    score: int = 45  # Starting at B1 threshold for new entities (generous baseline)
    roll_number: int = 0  # Descending rank (higher = better standing)

    # Core tracking fields
    total_penalty_points: int = 0
    recent_critical_penalty: int = 0  # +25 if critical event in last 14 days
    clean_streak: int = 0  # Consecutive successful gated actions
    clean_streak_bonus: int = 0  # +1 per 20 consecutive, capped at +15

    # Review adjustment (twice-weekly manual review)
    review_adjustment: int = 0  # Manual -10..+10
    last_reviewed_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Scope eligibility (derived from badge)
    eligible_scopes: set[Scope] = field(default_factory=set)

    # Metadata
    first_seen_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_seen_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_critical_at: datetime | None = None  # For B3 eligibility check

    # Audit trail reference
    violation_count: int = 0

    def __post_init__(self) -> None:
        """Ensure eligible_scopes reflects current badge level."""
        self._update_eligible_scopes()

    def _update_eligible_scopes(self) -> None:
        """Update eligible scopes based on current badge."""
        scopes: set[Scope] = set()
        if self.badge == Badge.B0_RESTRICTED:
            scopes = set()  # No scopes by default
        elif self.badge == Badge.B1_TRUSTED:
            scopes = {Scope.READ, Scope.ANALYSIS}
        elif self.badge == Badge.B2_VERIFIED:
            scopes = {Scope.READ, Scope.WRITE, Scope.ANALYSIS}
        elif self.badge == Badge.B3_PRIVILEGED:
            scopes = {Scope.READ, Scope.WRITE, Scope.ADMIN, Scope.ANALYSIS, Scope.CONTROL}
        self.eligible_scopes = scopes

    def to_dict(self) -> dict[str, Any]:
        """Serialize standing to dictionary."""
        return {
            "entity_id": self.entity_id,
            "badge": self.badge.value,
            "score": self.score,
            "roll_number": self.roll_number,
            "total_penalty_points": self.total_penalty_points,
            "recent_critical_penalty": self.recent_critical_penalty,
            "clean_streak": self.clean_streak,
            "clean_streak_bonus": self.clean_streak_bonus,
            "review_adjustment": self.review_adjustment,
            "last_reviewed_at": self.last_reviewed_at.isoformat() if self.last_reviewed_at else None,
            "eligible_scopes": [s.value for s in self.eligible_scopes],
            "first_seen_at": self.first_seen_at.isoformat() if self.first_seen_at else None,
            "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at else None,
            "last_critical_at": self.last_critical_at.isoformat() if self.last_critical_at else None,
            "violation_count": self.violation_count,
        }


# ---------------------------------------------------------------------------
# Merit Scoring Engine
# ---------------------------------------------------------------------------


class MeritScoringEngine:
    """
    Score formula: clamp(100 - total_penalty_points - recent_critical_penalty
                        + clean_streak_bonus + review_adjustment, 0, 100)

    Badges:
    - B0_RESTRICTED: < 45
    - B1_TRUSTED: 45-64
    - B2_VERIFIED: 65-79
    - B3_PRIVILEGED: >= 80 with no high/critical in last 30 days
    """

    def __init__(self) -> None:
        self._standings: dict[str, MeritStanding] = {}

    def get_or_create_standing(self, entity_id: str) -> MeritStanding:
        """Get existing standing or create new with score-derived badge."""
        if entity_id not in self._standings:
            standing = MeritStanding(entity_id=entity_id)
            standing.badge = self._calculate_badge(standing)
            standing._update_eligible_scopes()
            self._standings[entity_id] = standing
        return self._standings[entity_id]

    def get_standing(self, entity_id: str) -> MeritStanding | None:
        """Get standing if exists, without creating."""
        return self._standings.get(entity_id)

    def record_violation(
        self,
        entity_id: str,
        penalty_points: int,
        is_critical: bool = False,
    ) -> MeritStanding:
        """
        Record a violation and update standing.

        Args:
            entity_id: The entity that committed the violation
            penalty_points: Base penalty points for the violation
            is_critical: Whether this is a high/critical severity event

        Returns:
            Updated MeritStanding
        """
        standing = self.get_or_create_standing(entity_id)
        standing.total_penalty_points += penalty_points
        standing.violation_count += 1
        standing.clean_streak = 0  # Reset clean streak on violation

        if is_critical:
            standing.recent_critical_penalty = CRITICAL_PENALTY_DEDUCTION
            standing.last_critical_at = datetime.now(UTC)

        self._recalculate_score(standing)
        self._recalculate_roll_numbers()

        logger.info(
            "merit_standing.violation_recorded entity_fp=%s points=%d critical=%s new_score=%d badge=%s",
            _entity_fingerprint(entity_id),
            penalty_points,
            is_critical,
            standing.score,
            standing.badge,
        )

        return standing

    def record_successful_action(self, entity_id: str) -> MeritStanding:
        """
        Record a successful gated action, incrementing clean streak.

        Clean streak bonus: +1 per 20 consecutive successful gated actions, capped at +15.
        """
        standing = self.get_or_create_standing(entity_id)
        standing.clean_streak += 1

        # Calculate streak bonus: 1 per 20, capped at 15
        streak_bonus = min(standing.clean_streak // 20, MAX_CLEAN_STREAK_BONUS)
        standing.clean_streak_bonus = streak_bonus

        self._recalculate_score(standing)
        self._recalculate_roll_numbers()

        return standing

    def apply_review_adjustment(self, entity_id: str, adjustment: int) -> MeritStanding:
        """
        Apply manual review adjustment (twice-weekly review cadence).

        Args:
            entity_id: Entity to adjust
            adjustment: Value between -10 and +10

        Returns:
            Updated MeritStanding
        """
        if not REVIEW_ADJUSTMENT_RANGE[0] <= adjustment <= REVIEW_ADJUSTMENT_RANGE[1]:
            raise ValueError(f"Adjustment must be in range {REVIEW_ADJUSTMENT_RANGE}")

        standing = self.get_or_create_standing(entity_id)
        standing.review_adjustment = adjustment
        standing.last_reviewed_at = datetime.now(UTC)

        self._recalculate_score(standing)
        self._recalculate_roll_numbers()

        logger.info(
            "merit_standing.review_adjusted entity_fp=%s adjustment=%d new_score=%d",
            _entity_fingerprint(entity_id),
            adjustment,
            standing.score,
        )

        return standing

    def _recalculate_score(self, standing: MeritStanding) -> None:
        """
        Recalculate score using formula:
        score = clamp(100 - total_penalty_points - recent_critical_penalty
                      + clean_streak_bonus + review_adjustment, 0, 100)
        """
        # Check if critical penalty should still apply (within window)
        now = datetime.now(UTC)
        if standing.last_critical_at:
            days_since_critical = (now - standing.last_critical_at).days
            if days_since_critical > CRITICAL_EVENT_WINDOW_DAYS:
                standing.recent_critical_penalty = 0

        raw_score = (
            DEFAULT_BASE_SCORE
            - standing.total_penalty_points
            - standing.recent_critical_penalty
            + standing.clean_streak_bonus
            + standing.review_adjustment
        )

        standing.score = max(0, min(100, raw_score))
        self._update_badge(standing)

    def _update_badge(self, standing: MeritStanding) -> None:
        """Update badge based on score and eligibility criteria."""
        old_badge = standing.badge
        new_badge = self._calculate_badge(standing)

        if new_badge != old_badge:
            standing.badge = new_badge
            standing._update_eligible_scopes()
            logger.info(
                "merit_standing.badge_changed entity_fp=%s old=%s new=%s score=%d",
                _entity_fingerprint(standing.entity_id),
                old_badge.value,
                new_badge.value,
                standing.score,
            )

    def _calculate_badge(self, standing: MeritStanding) -> Badge:
        """Calculate badge from score and critical event history."""
        score = standing.score

        # B3 requires no high/critical in last 30 days
        if score >= BADGE_THRESHOLDS[Badge.B3_PRIVILEGED]:
            if standing.last_critical_at:
                days_since = (datetime.now(UTC) - standing.last_critical_at).days
                if days_since >= B3_CLEAN_WINDOW_DAYS:
                    return Badge.B3_PRIVILEGED
            else:
                return Badge.B3_PRIVILEGED
            # Score high but recent critical - cap at B2
            return Badge.B2_VERIFIED

        if score >= BADGE_THRESHOLDS[Badge.B2_VERIFIED]:
            return Badge.B2_VERIFIED

        if score >= BADGE_THRESHOLDS[Badge.B1_TRUSTED]:
            return Badge.B1_TRUSTED

        return Badge.B0_RESTRICTED

    def _recalculate_roll_numbers(self) -> None:
        """
        Recalculate roll numbers for all entities.

        Roll number ordering:
        1. Descending score (higher first)
        2. Lower penalty points (fewer first)
        3. Longer clean streak (longer first)
        4. Earlier first-seen timestamp (earlier first)
        """
        if not self._standings:
            return

        # Sort by criteria
        sorted_entities = sorted(
            self._standings.values(),
            key=lambda s: (
                -s.score,  # Higher score first
                s.total_penalty_points,  # Lower penalties first
                -s.clean_streak,  # Longer streak first
                s.first_seen_at.timestamp() if s.first_seen_at else 0,  # Earlier first
            ),
        )

        # Assign roll numbers (1-based, higher = better standing)
        for rank, standing in enumerate(sorted_entities, start=1):
            standing.roll_number = len(sorted_entities) - rank + 1

    def check_permission(
        self,
        entity_id: str,
        action_class: ActionClass,
        required_scope: Scope | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """
        Check if entity has permission for an action class.

        Args:
            entity_id: Entity to check
            action_class: The action class being attempted
            required_scope: Optional specific scope required

        Returns:
            Tuple of (allowed, details dict)
        """
        standing = self.get_or_create_standing(entity_id)
        required_badge = ACTION_CLASS_BADGE_REQUIREMENTS[action_class]
        required_scopes = ACTION_CLASS_SCOPE_REQUIREMENTS[action_class]

        # Check badge level
        badge_values = {
            b: i for i, b in enumerate([Badge.B0_RESTRICTED, Badge.B1_TRUSTED, Badge.B2_VERIFIED, Badge.B3_PRIVILEGED])
        }
        has_badge = badge_values[standing.badge] >= badge_values[required_badge]

        # Check scope eligibility
        has_scopes = required_scopes.issubset(standing.eligible_scopes)

        # Check specific scope requirement
        has_specific_scope = True
        if required_scope:
            has_specific_scope = required_scope in standing.eligible_scopes

        allowed = has_badge and has_scopes and has_specific_scope

        details = {
            "entity_id": entity_id,
            "action_class": action_class.value,
            "required_badge": required_badge.value,
            "actual_badge": standing.badge.value,
            "has_badge": has_badge,
            "required_scopes": [s.value for s in required_scopes],
            "eligible_scopes": [s.value for s in standing.eligible_scopes],
            "has_scopes": has_scopes,
            "required_scope": required_scope.value if required_scope else None,
            "has_specific_scope": has_specific_scope,
            "allowed": allowed,
            "score": standing.score,
            "roll_number": standing.roll_number,
        }

        return allowed, details

    def get_leaderboard(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get ranked list of entities by standing."""
        sorted_standings = sorted(
            self._standings.values(),
            key=lambda s: -s.roll_number,  # Higher roll number first
        )
        return [s.to_dict() for s in sorted_standings[:limit]]

    def get_all_standings(self) -> dict[str, MeritStanding]:
        """Get all standings (for persistence)."""
        return dict(self._standings)

    def load_standings(self, standings: dict[str, MeritStanding]) -> None:
        """Hydrate standings from persistence."""
        self._standings = standings
        self._recalculate_roll_numbers()
        logger.info("merit_standing.loaded count=%d", len(standings))

    def reset(self) -> None:
        """Reset all standings (for testing)."""
        self._standings.clear()


# ---------------------------------------------------------------------------
# Global Engine Instance
# ---------------------------------------------------------------------------

MERIT_SCORING_ENGINE = MeritScoringEngine()


def get_merit_engine() -> MeritScoringEngine:
    """Get the global merit scoring engine."""
    return MERIT_SCORING_ENGINE
