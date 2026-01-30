"""Multi-organization and multi-user management system.

This module provides comprehensive organization and user management with
discipline, penalties, and rule enforcement for OpenAI, NVIDIA, and Walt Disney Pictures.
"""

from .discipline import DisciplineAction, DisciplineManager, Penalty, PenaltyType, Rule, RuleViolation
from .models import Organization, OrganizationRole, OrganizationSettings, User, UserRole, UserStatus
from .org_manager import OrganizationManager

__all__ = [
    "Organization",
    "OrganizationRole",
    "OrganizationSettings",
    "User",
    "UserRole",
    "UserStatus",
    "DisciplineAction",
    "DisciplineManager",
    "Penalty",
    "PenaltyType",
    "Rule",
    "RuleViolation",
    "OrganizationManager",
]
