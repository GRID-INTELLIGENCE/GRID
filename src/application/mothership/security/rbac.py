"""
Role-Based Access Control (RBAC) System.

Re-exports shared RBAC types from grid.auth.rbac.
Application-layer module kept for backward compatibility.
"""

from __future__ import annotations

from enum import StrEnum


class Permission(StrEnum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    EXECUTE = "execute"
    SENSITIVE_READ = "sensitive_read"
    BILLING_READ = "billing_read"
    BILLING_WRITE = "billing_write"


class Role(StrEnum):
    ANONYMOUS = "anonymous"
    READER = "reader"
    WRITER = "writer"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    SERVICE_ACCOUNT = "service_account"


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
    if isinstance(role, str):
        try:
            role = Role(role.lower())
        except ValueError:
            return set()
    return {permission.value for permission in ROLE_PERMISSIONS.get(role, set())}


def has_permission(user_permissions: set[str], required_permission: str | Permission) -> bool:
    if isinstance(required_permission, Permission):
        required_permission = required_permission.value
    return "admin" in user_permissions or required_permission in user_permissions

__all__ = [
    "Permission",
    "Role",
    "ROLE_PERMISSIONS",
    "get_permissions_for_role",
    "has_permission",
]
