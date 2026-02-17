"""
Role-Based Access Control (RBAC) System.

Re-exports shared RBAC types from grid.auth.rbac.
Application-layer module kept for backward compatibility.
"""

from grid.auth.rbac import (
    ROLE_PERMISSIONS,
    Permission,
    Role,
    get_permissions_for_role,
    has_permission,
)

__all__ = [
    "Permission",
    "Role",
    "ROLE_PERMISSIONS",
    "get_permissions_for_role",
    "has_permission",
]
