from .rbac import ROLE_PERMISSIONS, Permission, Role, get_permissions_for_role, has_permission
from .token_manager import TokenManager

try:
    from .middleware import AuthMiddleware
    from .service import AuthService
except ImportError:
    AuthMiddleware = None  # type: ignore[assignment]
    AuthService = None  # type: ignore[assignment]

__all__ = [
    "TokenManager",
    "AuthService",
    "AuthMiddleware",
    "Permission",
    "Role",
    "ROLE_PERMISSIONS",
    "get_permissions_for_role",
    "has_permission",
]
