"""Discipline and rule enforcement system."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class PenaltyType(str, Enum):
    """Types of penalties."""

    WARNING = "warning"
    POINTS = "points"
    SUSPENSION = "suspension"
    BAN = "ban"
    RATE_LIMIT = "rate_limit"
    FEATURE_RESTRICTION = "feature_restriction"
    RESOURCE_RESTRICTION = "resource_restriction"


class Penalty(BaseModel):
    """Penalty model."""

    penalty_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique penalty identifier")
    user_id: str = Field(description="User who received penalty")
    org_id: str | None = Field(default=None, description="Organization context")
    penalty_type: PenaltyType = Field(description="Type of penalty")
    severity: float = Field(default=1.0, ge=0.0, le=10.0, description="Penalty severity (0-10)")
    points: float = Field(default=0.0, description="Penalty points")
    reason: str = Field(description="Reason for penalty")
    rule_violated: str | None = Field(default=None, description="Rule that was violated")
    duration: timedelta | None = Field(default=None, description="Penalty duration")
    expires_at: datetime | None = Field(default=None, description="When penalty expires")
    active: bool = Field(default=True, description="Whether penalty is active")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(
        use_enum_values=True, json_encoders={datetime: lambda v: v.isoformat(), timedelta: lambda v: v.total_seconds()}
    )

    def is_expired(self) -> bool:
        """Check if penalty is expired."""
        if not self.expires_at:
            return False
        return datetime.now(UTC) > self.expires_at


class RuleViolation(BaseModel):
    """Rule violation record."""

    violation_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique violation identifier")
    user_id: str = Field(description="User who violated rule")
    org_id: str | None = Field(default=None, description="Organization context")
    rule_id: str = Field(description="Rule that was violated")
    rule_name: str = Field(description="Rule name")
    severity: float = Field(default=1.0, ge=0.0, le=10.0, description="Violation severity (0-10)")
    description: str = Field(description="Violation description")
    context: dict[str, Any] = Field(default_factory=dict, description="Violation context")
    penalty_applied: str | None = Field(default=None, description="Penalty ID if penalty was applied")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(use_enum_values=True)

    @field_serializer("created_at", when_used="json")
    def serialize_datetime(self, value: datetime) -> str:
        """Serialize datetime to ISO format."""
        return value.isoformat()


class Rule(BaseModel):
    """Rule definition."""

    rule_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique rule identifier")
    name: str = Field(description="Rule name")
    description: str = Field(description="Rule description")
    category: str = Field(description="Rule category")
    severity: float = Field(default=1.0, ge=0.0, le=10.0, description="Default severity (0-10)")
    penalty_points: float = Field(default=1.0, description="Default penalty points")
    penalty_type: PenaltyType = Field(default=PenaltyType.WARNING, description="Default penalty type")
    enabled: bool = Field(default=True, description="Whether rule is enabled")
    org_specific: bool = Field(default=False, description="Whether rule is organization-specific")
    org_ids: list[str] = Field(default_factory=list, description="Organization IDs if org-specific")
    check_function: str | None = Field(default=None, description="Function name to check rule")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(use_enum_values=True)

    @field_serializer("created_at", when_used="json")
    def serialize_datetime(self, value: datetime) -> str:
        """Serialize datetime to ISO format."""
        return value.isoformat()


class DisciplineAction(BaseModel):
    """Discipline action taken."""

    action_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique action identifier")
    user_id: str = Field(description="User affected")
    org_id: str | None = Field(default=None, description="Organization context")
    action_type: str = Field(description="Type of action (suspend, ban, warn, etc.)")
    reason: str = Field(description="Reason for action")
    duration: timedelta | None = Field(default=None, description="Action duration")
    expires_at: datetime | None = Field(default=None, description="When action expires")
    active: bool = Field(default=True, description="Whether action is active")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(
        use_enum_values=True, json_encoders={datetime: lambda v: v.isoformat(), timedelta: lambda v: v.total_seconds()}
    )

    def is_expired(self) -> bool:
        """Check if action is expired."""
        if not self.expires_at:
            return False
        return datetime.now(UTC) > self.expires_at


class DisciplineManager:
    """Manages discipline, penalties, and rule enforcement."""

    def __init__(self):
        """Initialize discipline manager."""
        self.rules: dict[str, Rule] = {}
        self.violations: dict[str, list[RuleViolation]] = {}
        self.penalties: dict[str, list[Penalty]] = {}
        self.actions: dict[str, list[DisciplineAction]] = {}
        self._rule_checkers: dict[str, Callable[[dict[str, Any]], bool]] = {}

        # Initialize default rules
        self._initialize_default_rules()

    def _initialize_default_rules(self) -> None:
        """Initialize default rules for organizations."""
        # Rate limiting rules
        self.add_rule(
            Rule(
                rule_id="rate_limit_exceeded",
                name="Rate Limit Exceeded",
                description="User exceeded allowed operation rate",
                category="rate_limiting",
                severity=3.0,
                penalty_points=5.0,
                penalty_type=PenaltyType.RATE_LIMIT,
            )
        )

        # Resource abuse rules
        self.add_rule(
            Rule(
                rule_id="resource_abuse",
                name="Resource Abuse",
                description="User abused system resources",
                category="resource",
                severity=5.0,
                penalty_points=10.0,
                penalty_type=PenaltyType.RESOURCE_RESTRICTION,
            )
        )

        # Unauthorized access rules
        self.add_rule(
            Rule(
                rule_id="unauthorized_access",
                name="Unauthorized Access",
                description="User attempted unauthorized access",
                category="security",
                severity=8.0,
                penalty_points=20.0,
                penalty_type=PenaltyType.SUSPENSION,
            )
        )

        # Misconduct rules
        self.add_rule(
            Rule(
                rule_id="misconduct",
                name="Misconduct",
                description="User engaged in misconduct",
                category="conduct",
                severity=7.0,
                penalty_points=15.0,
                penalty_type=PenaltyType.SUSPENSION,
            )
        )

    def add_rule(self, rule: Rule) -> None:
        """Add a rule."""
        self.rules[rule.rule_id] = rule

    def register_rule_checker(self, rule_id: str, checker: Callable[[dict[str, Any]], bool]) -> None:
        """Register a rule checker function."""
        self._rule_checkers[rule_id] = checker

    def check_rule(self, rule_id: str, context: dict[str, Any]) -> bool:
        """Check if a rule is violated.

        Args:
            rule_id: Rule identifier
            context: Context for rule checking

        Returns:
            True if rule is violated, False otherwise
        """
        rule = self.rules.get(rule_id)
        if not rule or not rule.enabled:
            return False

        checker = self._rule_checkers.get(rule_id)
        if checker:
            return checker(context)

        return False

    def record_violation(
        self,
        user_id: str,
        rule_id: str,
        severity: float | None = None,
        description: str | None = None,
        org_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> RuleViolation:
        """Record a rule violation.

        Args:
            user_id: User who violated rule
            rule_id: Rule that was violated
            severity: Optional severity override
            description: Optional description override
            org_id: Optional organization context
            context: Optional violation context

        Returns:
            Created violation record
        """
        rule = self.rules.get(rule_id)
        if not rule:
            raise ValueError(f"Rule {rule_id} not found")

        violation = RuleViolation(
            user_id=user_id,
            org_id=org_id,
            rule_id=rule_id,
            rule_name=rule.name,
            severity=severity or rule.severity,
            description=description or rule.description,
            context=context or {},
        )

        if user_id not in self.violations:
            self.violations[user_id] = []
        self.violations[user_id].append(violation)

        # Apply penalty if auto_penalty is enabled
        # (This would be checked from org settings in real implementation)
        penalty = self.apply_penalty(user_id, rule, violation)
        if penalty:
            violation.penalty_applied = penalty.penalty_id

        return violation

    def apply_penalty(
        self,
        user_id: str,
        rule: Rule,
        violation: RuleViolation,
        org_id: str | None = None,
    ) -> Penalty | None:
        """Apply a penalty for a violation.

        Args:
            user_id: User to penalize
            rule: Rule that was violated
            violation: Violation record
            org_id: Optional organization context

        Returns:
            Created penalty or None
        """
        # Calculate penalty duration based on severity
        duration = None
        expires_at = None
        if violation.severity >= 7.0:
            duration = timedelta(days=7)
            expires_at = datetime.now(UTC) + duration
        elif violation.severity >= 5.0:
            duration = timedelta(days=1)
            expires_at = datetime.now(UTC) + duration

        penalty = Penalty(
            user_id=user_id,
            org_id=org_id,
            penalty_type=rule.penalty_type,
            severity=violation.severity,
            points=rule.penalty_points,
            reason=f"Violated rule: {rule.name}",
            rule_violated=rule.rule_id,
            duration=duration,
            expires_at=expires_at,
        )

        if user_id not in self.penalties:
            self.penalties[user_id] = []
        self.penalties[user_id].append(penalty)

        return penalty

    def get_user_violations(self, user_id: str, limit: int = 100) -> list[RuleViolation]:
        """Get violations for a user."""
        return self.violations.get(user_id, [])[-limit:]

    def get_user_penalties(self, user_id: str, active_only: bool = True) -> list[Penalty]:
        """Get penalties for a user."""
        penalties = self.penalties.get(user_id, [])
        if active_only:
            penalties = [p for p in penalties if p.active and not p.is_expired()]
        return penalties

    def get_user_penalty_points(self, user_id: str) -> float:
        """Get total penalty points for a user."""
        penalties = self.get_user_penalties(user_id, active_only=True)
        return sum(p.points for p in penalties)
