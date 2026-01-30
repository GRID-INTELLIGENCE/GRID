"""
Role-Based Access Control (RBAC) System.

Defines roles, permissions, and hierarchical access levels for GRID.
"""

from __future__ import annotations

from enum import Enum


class Permission(str, Enum):
    """Granular permissions for the system."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    EXECUTE = "execute"
    SENSITIVE_READ = "sensitive_read"
    BILLING_READ = "billing_read"
    BILLING_WRITE = "billing_write"


class Role(str, Enum):
    """Standardized roles for users and services."""

    ANONYMOUS = "anonymous"
    READER = "reader"
    WRITER = "writer"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    SERVICE_ACCOUNT = "service_account"


# Hierarchical role mapping (Industry Grade)
# Each role inherits permissions from the roles below it in the hierarchy
ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.ANONYMOUS: {Permission.READ},
    Role.READER: {Permission.READ, Permission.EXECUTE},
    Role.WRITER: {Permission.READ, Permission.WRITE, Permission.EXECUTE},
    Role.ADMIN: {
        Permission.READ,
        Permission.WRITE,
        Permission.EXECUTE,
        Permission.DELETE,
        Permission.SENSITIVE_READ,
        Permission.BILLING_READ,
    },
    Role.SUPER_ADMIN: {
        Permission.READ,
        Permission.WRITE,
        Permission.EXECUTE,
        Permission.DELETE,
        Permission.SENSITIVE_READ,
        Permission.ADMIN,
        Permission.BILLING_READ,
        Permission.BILLING_WRITE,
    },
    Role.SERVICE_ACCOUNT: {Permission.READ, Permission.WRITE, Permission.EXECUTE},
}


def get_permissions_for_role(role: str | Role) -> set[str]:
    """Get all permissions (including inherited) for a given role."""
    if isinstance(role, str):
        try:
            role = Role(role.lower())
        except ValueError:
            return set()

    return {p.value for p in ROLE_PERMISSIONS.get(role, set())}


def has_permission(user_permissions: set[str], required_permission: str | Permission) -> bool:
    """Check if the provided permissions satisfy the required permission."""
    if isinstance(required_permission, Permission):
        required_permission = required_permission.value

    # Super admin and ADMIN usually bypass most checks if they have the 'admin' permission string
    if "admin" in user_permissions:
        return True

    return required_permission in user_permissions
