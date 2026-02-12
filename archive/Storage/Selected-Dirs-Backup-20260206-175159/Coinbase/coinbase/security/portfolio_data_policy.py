"""
Portfolio Data Policy
====================
Defines sensitivity levels, allowed purposes, and output rules for portfolio data.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class DataSensitivity(Enum):
    """Data sensitivity classification."""

    PUBLIC = "public"
    SENSITIVE = "sensitive"
    CRITICAL = "critical"


class AccessPurpose(Enum):
    """Allowed purposes for data access."""

    ANALYTICS = "analytics"
    REPORTING = "reporting"
    AI_TRAINING = "ai_training"
    AI_INFERENCE = "ai_inference"
    AUDIT = "audit"
    COMPLIANCE = "compliance"
    RESEARCH = "research"


class OutputRule(Enum):
    """Output sanitization rules."""

    RAW = "raw"
    SANITIZED = "sanitized"
    AGGREGATED = "aggregated"
    SYMBOL_ONLY = "symbol_only"
    METRICS_ONLY = "metrics_only"
    NONE = "none"


@dataclass
class FieldPolicy:
    """Policy for a specific data field."""

    field_name: str
    sensitivity: DataSensitivity
    allowed_purposes: set[AccessPurpose]
    output_rules: set[OutputRule]
    required_for_analytics: bool = False


class PortfolioDataPolicy:
    """
    Defines policy rules for portfolio data access and output.

    Enforces that portfolio data is treated as CRITICAL with full guardrails.
    """

    # Field policies for portfolio data
    FIELD_POLICIES: dict[str, FieldPolicy] = {
        "user_id": FieldPolicy(
            field_name="user_id",
            sensitivity=DataSensitivity.CRITICAL,
            allowed_purposes={AccessPurpose.AUDIT, AccessPurpose.COMPLIANCE},
            output_rules={OutputRule.NONE},
            required_for_analytics=False,
        ),
        "user_id_hash": FieldPolicy(
            field_name="user_id_hash",
            sensitivity=DataSensitivity.CRITICAL,
            allowed_purposes={
                AccessPurpose.ANALYTICS,
                AccessPurpose.AUDIT,
                AccessPurpose.COMPLIANCE,
            },
            output_rules={OutputRule.SANITIZED},
            required_for_analytics=True,
        ),
        "symbol": FieldPolicy(
            field_name="symbol",
            sensitivity=DataSensitivity.PUBLIC,
            allowed_purposes=set(AccessPurpose),
            output_rules={OutputRule.RAW, OutputRule.SANITIZED},
            required_for_analytics=True,
        ),
        "quantity": FieldPolicy(
            field_name="quantity",
            sensitivity=DataSensitivity.CRITICAL,
            allowed_purposes={AccessPurpose.ANALYTICS, AccessPurpose.RESEARCH},
            output_rules={OutputRule.AGGREGATED, OutputRule.NONE, OutputRule.RAW},
            required_for_analytics=True,
        ),
        "purchase_price": FieldPolicy(
            field_name="purchase_price",
            sensitivity=DataSensitivity.CRITICAL,
            allowed_purposes={AccessPurpose.ANALYTICS, AccessPurpose.RESEARCH},
            output_rules={OutputRule.AGGREGATED, OutputRule.NONE, OutputRule.RAW},
            required_for_analytics=True,
        ),
        "current_price": FieldPolicy(
            field_name="current_price",
            sensitivity=DataSensitivity.PUBLIC,
            allowed_purposes=set(AccessPurpose),
            output_rules={OutputRule.RAW, OutputRule.SANITIZED},
            required_for_analytics=True,
        ),
        "current_value": FieldPolicy(
            field_name="current_value",
            sensitivity=DataSensitivity.SENSITIVE,
            allowed_purposes={AccessPurpose.ANALYTICS, AccessPurpose.REPORTING},
            output_rules={OutputRule.AGGREGATED, OutputRule.METRICS_ONLY},
            required_for_analytics=True,
        ),
        "gain_loss": FieldPolicy(
            field_name="gain_loss",
            sensitivity=DataSensitivity.SENSITIVE,
            allowed_purposes={AccessPurpose.ANALYTICS, AccessPurpose.REPORTING},
            output_rules={OutputRule.AGGREGATED, OutputRule.METRICS_ONLY},
            required_for_analytics=True,
        ),
        "gain_loss_percentage": FieldPolicy(
            field_name="gain_loss_percentage",
            sensitivity=DataSensitivity.SENSITIVE,
            allowed_purposes={AccessPurpose.ANALYTICS, AccessPurpose.REPORTING},
            output_rules={OutputRule.RAW, OutputRule.SANITIZED},
            required_for_analytics=True,
        ),
        "commission": FieldPolicy(
            field_name="commission",
            sensitivity=DataSensitivity.SENSITIVE,
            allowed_purposes={AccessPurpose.ANALYTICS, AccessPurpose.AUDIT},
            output_rules={OutputRule.AGGREGATED, OutputRule.NONE},
            required_for_analytics=True,
        ),
        "sector": FieldPolicy(
            field_name="sector",
            sensitivity=DataSensitivity.PUBLIC,
            allowed_purposes=set(AccessPurpose),
            output_rules={OutputRule.RAW, OutputRule.SANITIZED},
            required_for_analytics=True,
        ),
        "comment": FieldPolicy(
            field_name="comment",
            sensitivity=DataSensitivity.CRITICAL,
            allowed_purposes={AccessPurpose.AUDIT, AccessPurpose.COMPLIANCE},
            output_rules={OutputRule.NONE},
            required_for_analytics=False,
        ),
    }

    # Allowed outputs by purpose
    PURPOSE_OUTPUT_RULES: dict[AccessPurpose, set[OutputRule]] = {
        AccessPurpose.ANALYTICS: {
            OutputRule.AGGREGATED,
            OutputRule.METRICS_ONLY,
            OutputRule.SYMBOL_ONLY,
            OutputRule.SANITIZED,
        },
        AccessPurpose.REPORTING: {
            OutputRule.AGGREGATED,
            OutputRule.METRICS_ONLY,
            OutputRule.SYMBOL_ONLY,
            OutputRule.SANITIZED,
        },
        AccessPurpose.AI_TRAINING: {OutputRule.SANITIZED, OutputRule.AGGREGATED},
        AccessPurpose.AI_INFERENCE: {OutputRule.SANITIZED, OutputRule.AGGREGATED},
        AccessPurpose.AUDIT: {OutputRule.RAW},
        AccessPurpose.COMPLIANCE: {OutputRule.RAW},
        AccessPurpose.RESEARCH: {OutputRule.SANITIZED, OutputRule.AGGREGATED},
    }

    @classmethod
    def get_field_policy(cls, field_name: str) -> FieldPolicy | None:
        """
        Get policy for a specific field.

        Args:
            field_name: Name of the field

        Returns:
            FieldPolicy or None if field not found
        """
        return cls.FIELD_POLICIES.get(field_name)

    @classmethod
    def is_access_allowed(cls, field_name: str, purpose: AccessPurpose) -> bool:
        """
        Check if access to a field is allowed for a given purpose.

        Args:
            field_name: Name of the field
            purpose: Purpose of access

        Returns:
            True if access is allowed
        """
        policy = cls.get_field_policy(field_name)
        if not policy:
            return False
        return purpose in policy.allowed_purposes

    @classmethod
    def get_allowed_output_rules(cls, field_name: str, purpose: AccessPurpose) -> set[OutputRule]:
        """
        Get allowed output rules for a field and purpose.

        Args:
            field_name: Name of the field
            purpose: Purpose of access

        Returns:
            Set of allowed OutputRule
        """
        policy = cls.get_field_policy(field_name)
        if not policy:
            return set()

        purpose_rules = cls.PURPOSE_OUTPUT_RULES.get(purpose, set())
        return policy.output_rules.intersection(purpose_rules)

    @classmethod
    def should_output_field(
        cls, field_name: str, purpose: AccessPurpose, output_rule: OutputRule
    ) -> bool:
        """
        Check if a field should be output with a given rule.

        Args:
            field_name: Name of the field
            purpose: Purpose of access
            output_rule: Output rule to apply

        Returns:
            True if field should be output
        """
        allowed_rules = cls.get_allowed_output_rules(field_name, purpose)
        return output_rule in allowed_rules

    @classmethod
    def sanitize_field_value(cls, field_name: str, value: Any, output_rule: OutputRule) -> Any:
        """
        Sanitize a field value based on output rule.

        Args:
            field_name: Name of the field
            value: Value to sanitize
            output_rule: Output rule to apply

        Returns:
            Sanitized value
        """
        if output_rule == OutputRule.NONE:
            return None
        elif output_rule == OutputRule.RAW:
            return value
        elif output_rule == OutputRule.SANITIZED:
            return cls._sanitize_value(value)
        elif output_rule == OutputRule.AGGREGATED:
            return cls._aggregate_value(value)
        elif output_rule == OutputRule.SYMBOL_ONLY:
            return cls._symbol_only(value, field_name)
        elif output_rule == OutputRule.METRICS_ONLY:
            return cls._metrics_only(value, field_name)
        return None

    @classmethod
    def _sanitize_value(cls, value: Any) -> Any:
        """Apply basic sanitization to value."""
        if isinstance(value, str):
            return value[:100]  # Truncate long strings
        elif isinstance(value, (int, float)):
            return round(value, 2)
        return value

    @classmethod
    def _aggregate_value(cls, value: Any) -> Any:
        """Convert to aggregated form."""
        if isinstance(value, (int, float)):
            return round(value, 2)
        return value

    @classmethod
    def _symbol_only(cls, value: Any, field_name: str) -> Any:
        """Return symbol only for applicable fields."""
        if field_name == "symbol":
            return str(value).upper() if value else None
        return None

    @classmethod
    def _metrics_only(cls, value: Any, field_name: str) -> Any:
        """Return metrics only for applicable fields."""
        metric_fields = {
            "current_value",
            "gain_loss",
            "gain_loss_percentage",
            "total_value",
            "total_gain_loss",
        }
        if field_name in metric_fields:
            return round(float(value), 2) if value else 0.0
        return None

    @classmethod
    def get_required_analytics_fields(cls) -> list[str]:
        """
        Get list of fields required for analytics.

        Returns:
            List of field names
        """
        return [
            name for name, policy in cls.FIELD_POLICIES.items() if policy.required_for_analytics
        ]

    @classmethod
    def validate_output_dict(
        cls, data: dict[str, Any], purpose: AccessPurpose, output_rule: OutputRule
    ) -> dict[str, Any]:
        """
        Validate and sanitize output dictionary.

        Args:
            data: Dictionary of field names to values
            purpose: Purpose of access
            output_rule: Output rule to apply

        Returns:
            Sanitized dictionary
        """
        result = {}
        for field_name, value in data.items():
            if cls.should_output_field(field_name, purpose, output_rule):
                sanitized = cls.sanitize_field_value(field_name, value, output_rule)
                if sanitized is not None:
                    result[field_name] = sanitized
        return result

    @classmethod
    def is_critical_data(cls, field_name: str) -> bool:
        """
        Check if a field contains critical data.

        Args:
            field_name: Name of the field

        Returns:
            True if field is critical
        """
        policy = cls.get_field_policy(field_name)
        if policy is None:
            return False
        return policy.sensitivity == DataSensitivity.CRITICAL


def get_portfolio_data_policy() -> PortfolioDataPolicy:
    """
    Get singleton instance of PortfolioDataPolicy.

    Returns:
        PortfolioDataPolicy instance
    """
    return PortfolioDataPolicy()
