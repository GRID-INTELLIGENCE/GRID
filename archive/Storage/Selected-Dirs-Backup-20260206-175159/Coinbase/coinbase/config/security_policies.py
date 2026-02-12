"""
Security Policies Configuration
===============================
Access control rules, data classification policies, and AI safety controls.

Usage:
    from coinbase.config.security_policies import SecurityPolicyManager, AccessLevel

    policies = SecurityPolicyManager()
    policies.configure_default_policies()

    if policies.check_access('user123', 'portfolio_data', AccessLevel.READ):
        # Allow access
        pass
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AccessLevel(Enum):
    """Access levels for resources."""

    NONE = "none"
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class DataClassification(Enum):
    """Data classification levels."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    CRITICAL = "critical"


class UserRole(Enum):
    """User roles for access control."""

    ANONYMOUS = "anonymous"
    USER = "user"
    PREMIUM = "premium"
    ANALYST = "analyst"
    ADMIN = "admin"
    SYSTEM = "system"


@dataclass
class ResourcePolicy:
    """Policy for a specific resource."""

    resource_type: str
    classification: DataClassification
    min_access_level: AccessLevel
    allowed_roles: set[UserRole] = field(default_factory=set)
    audit_required: bool = True
    ai_accessible: bool = False


@dataclass
class UserContext:
    """Context for user access decisions."""

    user_id: str
    role: UserRole
    session_id: str | None = None
    ip_address: str | None = None
    mfa_verified: bool = False
    permissions: set[str] = field(default_factory=set)


class SecurityPolicyManager:
    """
    Central security policy manager.

    Manages access control, data classification, and AI safety policies.
    """

    def __init__(self) -> None:
        """Initialize security policy manager."""
        self.resource_policies: dict[str, ResourcePolicy] = {}
        self.user_policies: dict[str, dict[str, Any]] = {}
        self.ai_safety_rules: list[dict[str, Any]] = []
        self._configure_default_policies()

    def _configure_default_policies(self) -> None:
        """Configure default security policies."""
        # Portfolio data - CRITICAL
        self.register_resource_policy(
            ResourcePolicy(
                resource_type="portfolio_data",
                classification=DataClassification.CRITICAL,
                min_access_level=AccessLevel.READ,
                allowed_roles={UserRole.USER, UserRole.PREMIUM, UserRole.ANALYST, UserRole.ADMIN},
                audit_required=True,
                ai_accessible=False,
            )
        )

        # Transaction history - CRITICAL
        self.register_resource_policy(
            ResourcePolicy(
                resource_type="transaction_history",
                classification=DataClassification.CRITICAL,
                min_access_level=AccessLevel.READ,
                allowed_roles={UserRole.USER, UserRole.PREMIUM, UserRole.ANALYST, UserRole.ADMIN},
                audit_required=True,
                ai_accessible=False,
            )
        )

        # Market data - PUBLIC
        self.register_resource_policy(
            ResourcePolicy(
                resource_type="market_data",
                classification=DataClassification.PUBLIC,
                min_access_level=AccessLevel.READ,
                allowed_roles={
                    UserRole.ANONYMOUS,
                    UserRole.USER,
                    UserRole.PREMIUM,
                    UserRole.ANALYST,
                    UserRole.ADMIN,
                },
                audit_required=False,
                ai_accessible=True,
            )
        )

        # Trading signals - INTERNAL
        self.register_resource_policy(
            ResourcePolicy(
                resource_type="trading_signals",
                classification=DataClassification.INTERNAL,
                min_access_level=AccessLevel.READ,
                allowed_roles={UserRole.USER, UserRole.PREMIUM, UserRole.ANALYST, UserRole.ADMIN},
                audit_required=True,
                ai_accessible=True,
            )
        )

        # User preferences - CONFIDENTIAL
        self.register_resource_policy(
            ResourcePolicy(
                resource_type="user_preferences",
                classification=DataClassification.CONFIDENTIAL,
                min_access_level=AccessLevel.READ,
                allowed_roles={UserRole.USER, UserRole.PREMIUM, UserRole.ADMIN},
                audit_required=True,
                ai_accessible=False,
            )
        )

        # Analytics results - RESTRICTED
        self.register_resource_policy(
            ResourcePolicy(
                resource_type="analytics_results",
                classification=DataClassification.RESTRICTED,
                min_access_level=AccessLevel.READ,
                allowed_roles={UserRole.PREMIUM, UserRole.ANALYST, UserRole.ADMIN},
                audit_required=True,
                ai_accessible=True,
            )
        )

        # AI safety rules
        self.ai_safety_rules = [
            {
                "name": "portfolio_data_protection",
                "description": "AI cannot access raw portfolio data",
                "resource_types": ["portfolio_data", "transaction_history"],
                "ai_allowed": False,
                "sanitization_required": True,
            },
            {
                "name": "market_data_access",
                "description": "AI can access market data with restrictions",
                "resource_types": ["market_data"],
                "ai_allowed": True,
                "sanitization_required": False,
            },
            {
                "name": "trading_signals_caution",
                "description": "AI can access trading signals but not recommend actions",
                "resource_types": ["trading_signals"],
                "ai_allowed": True,
                "sanitization_required": True,
                "restrictions": ["no_direct_recommendations"],
            },
        ]

    def register_resource_policy(self, policy: ResourcePolicy) -> None:
        """
        Register a resource policy.

        Args:
            policy: Resource policy to register
        """
        self.resource_policies[policy.resource_type] = policy
        logger.info(f"Registered policy for {policy.resource_type}")

    def check_access(
        self, user_context: UserContext, resource_type: str, access_level: AccessLevel
    ) -> bool:
        """
        Check if user has access to resource.

        Args:
            user_context: User context
            resource_type: Type of resource
            access_level: Requested access level

        Returns:
            True if access allowed
        """
        policy = self.resource_policies.get(resource_type)
        if not policy:
            logger.warning(f"No policy found for {resource_type}, denying access")
            return False

        # Check if user role is allowed
        if user_context.role not in policy.allowed_roles:
            logger.warning(f"Role {user_context.role.value} not allowed for {resource_type}")
            return False

        # Check access level hierarchy
        access_hierarchy = [
            AccessLevel.NONE,
            AccessLevel.READ,
            AccessLevel.WRITE,
            AccessLevel.ADMIN,
        ]
        user_level_idx = access_hierarchy.index(policy.min_access_level)
        requested_level_idx = access_hierarchy.index(access_level)

        if requested_level_idx > user_level_idx:
            logger.warning(f"Insufficient access level for {resource_type}")
            return False

        # Check MFA for critical data
        if policy.classification == DataClassification.CRITICAL and not user_context.mfa_verified:
            if user_context.role not in [UserRole.SYSTEM, UserRole.ADMIN]:
                logger.warning(f"MFA required for {resource_type}")
                return False

        logger.debug(f"Access granted for {user_context.user_id} to {resource_type}")
        return True

    def get_data_classification(self, resource_type: str) -> DataClassification | None:
        """
        Get data classification for resource type.

        Args:
            resource_type: Type of resource

        Returns:
            Data classification or None
        """
        policy = self.resource_policies.get(resource_type)
        return policy.classification if policy else None

    def check_ai_access(self, resource_type: str, operation: str) -> dict[str, Any]:
        """
        Check if AI can access resource.

        Args:
            resource_type: Type of resource
            operation: AI operation type

        Returns:
            Access decision with restrictions
        """
        policy = self.resource_policies.get(resource_type)
        if not policy:
            return {"allowed": False, "reason": "Unknown resource type"}

        # Check AI safety rules
        for rule in self.ai_safety_rules:
            if resource_type in rule.get("resource_types", []):
                result = {
                    "allowed": rule.get("ai_allowed", False),
                    "sanitization_required": rule.get("sanitization_required", True),
                    "restrictions": rule.get("restrictions", []),
                }

                if not result["allowed"]:
                    result["reason"] = rule.get("description", "AI access denied")

                return result

        # Default deny
        return {"allowed": False, "reason": "No AI safety rule defined for this resource"}

    def sanitize_for_ai(self, data: Any, resource_type: str) -> Any:
        """
        Sanitize data before AI access.

        Args:
            data: Data to sanitize
            resource_type: Type of resource

        Returns:
            Sanitized data
        """
        policy = self.resource_policies.get(resource_type)
        if not policy:
            return None

        # Critical data - remove all sensitive fields
        if policy.classification == DataClassification.CRITICAL:
            if isinstance(data, dict):
                sanitized = {}
                for key, value in data.items():
                    if any(
                        sensitive in key.lower()
                        for sensitive in ["password", "token", "secret", "key"]
                    ):
                        sanitized[key] = "***REDACTED***"
                    elif isinstance(value, (dict, list)):
                        sanitized[key] = self.sanitize_for_ai(value, resource_type)
                    else:
                        sanitized[key] = value
                return sanitized
            elif isinstance(data, list):
                return [self.sanitize_for_ai(item, resource_type) for item in data]

        # Restricted data - aggregate and anonymize
        elif policy.classification == DataClassification.RESTRICTED:
            if isinstance(data, dict):
                # Remove identifying information
                return {k: v for k, v in data.items() if k not in ["user_id", "email", "name"]}

        return data

    def get_audit_requirements(self, resource_type: str) -> bool:
        """
        Check if audit logging is required for resource.

        Args:
            resource_type: Type of resource

        Returns:
            True if audit required
        """
        policy = self.resource_policies.get(resource_type)
        return policy.audit_required if policy else True

    def get_all_policies(self) -> dict[str, ResourcePolicy]:
        """Get all registered policies."""
        return self.resource_policies.copy()

    def get_ai_safety_rules(self) -> list[dict[str, Any]]:
        """Get all AI safety rules."""
        return self.ai_safety_rules.copy()


# Global policy manager instance
_global_policy_manager: SecurityPolicyManager | None = None


def get_policy_manager() -> SecurityPolicyManager:
    """Get global security policy manager instance."""
    global _global_policy_manager
    if _global_policy_manager is None:
        _global_policy_manager = SecurityPolicyManager()
    return _global_policy_manager


# Convenience functions
def check_resource_access(
    user_id: str,
    role: UserRole,
    resource_type: str,
    access_level: AccessLevel,
    mfa_verified: bool = False,
) -> bool:
    """Quick check for resource access."""
    manager = get_policy_manager()
    context = UserContext(user_id=user_id, role=role, mfa_verified=mfa_verified)
    return manager.check_access(context, resource_type, access_level)


def check_ai_resource_access(resource_type: str, operation: str = "read") -> dict[str, Any]:
    """Quick check for AI resource access."""
    manager = get_policy_manager()
    return manager.check_ai_access(resource_type, operation)
