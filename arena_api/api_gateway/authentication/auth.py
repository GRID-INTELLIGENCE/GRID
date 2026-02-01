"""
Authentication Manager for Arena API Gateway
===========================================

This module implements comprehensive authentication and authorization
for the Arena API Gateway, ensuring secure access to dynamic services.

Key Features:
- JWT token validation
- API key authentication
- Role-based access control (RBAC)
- Service-to-service authentication
- AI safety compliance checks
"""

import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import Any

import jwt
from fastapi import Request

logger = logging.getLogger(__name__)


class AuthManager:
    """
    Authentication manager handling various auth methods for the Arena system.
    """

    def __init__(self):
        self.jwt_secret = os.getenv("ARENA_JWT_SECRET", "arena-secret-key-change-in-production")
        self.jwt_algorithm = "HS256"
        self.api_keys = self._load_api_keys()
        self.service_tokens = {}

    def _load_api_keys(self) -> dict[str, dict[str, Any]]:
        """Load API keys from configuration."""
        # In production, load from secure storage
        return {
            "admin_key": {"key": "arena-admin-key-2024", "permissions": ["read", "write", "admin"], "rate_limit": 1000},
            "service_key": {"key": "arena-service-key-2024", "permissions": ["read", "write"], "rate_limit": 500},
        }

    async def authenticate(self, request: Request) -> dict[str, Any]:
        """
        Authenticate a request using available methods.

        Returns:
            Dict with authentication result
        """
        try:
            # Try JWT token first
            jwt_result = await self._authenticate_jwt(request)
            if jwt_result["authenticated"]:
                return jwt_result

            # Try API key
            api_key_result = await self._authenticate_api_key(request)
            if api_key_result["authenticated"]:
                return api_key_result

            # Try service token
            service_result = await self._authenticate_service_token(request)
            if service_result["authenticated"]:
                return service_result

            return {"authenticated": False, "user": None, "permissions": [], "method": None}

        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return {"authenticated": False, "error": str(e), "user": None, "permissions": []}

    async def _authenticate_jwt(self, request: Request) -> dict[str, Any]:
        """Authenticate using JWT token."""
        try:
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return {"authenticated": False}

            token = auth_header.replace("Bearer ", "")
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])

            # Check token expiration
            if payload.get("exp", 0) < datetime.utcnow().timestamp():
                return {"authenticated": False, "error": "Token expired"}

            return {
                "authenticated": True,
                "user": payload.get("sub"),
                "permissions": payload.get("permissions", []),
                "method": "jwt",
                "user_id": payload.get("user_id"),
                "roles": payload.get("roles", []),
            }

        except jwt.ExpiredSignatureError:
            return {"authenticated": False, "error": "Token expired"}
        except jwt.InvalidTokenError:
            return {"authenticated": False, "error": "Invalid token"}
        except Exception as e:
            logger.error(f"JWT authentication error: {str(e)}")
            return {"authenticated": False, "error": str(e)}

    async def _authenticate_api_key(self, request: Request) -> dict[str, Any]:
        """Authenticate using API key."""
        try:
            api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
            if not api_key:
                return {"authenticated": False}

            # Hash the key for comparison (in production, use proper key storage)
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()

            for key_name, key_data in self.api_keys.items():
                stored_hash = hashlib.sha256(key_data["key"].encode()).hexdigest()
                if key_hash == stored_hash:
                    return {
                        "authenticated": True,
                        "user": f"api_key_{key_name}",
                        "permissions": key_data["permissions"],
                        "method": "api_key",
                        "key_name": key_name,
                        "rate_limit": key_data["rate_limit"],
                    }

            return {"authenticated": False, "error": "Invalid API key"}

        except Exception as e:
            logger.error(f"API key authentication error: {str(e)}")
            return {"authenticated": False, "error": str(e)}

    async def _authenticate_service_token(self, request: Request) -> dict[str, Any]:
        """Authenticate service-to-service calls."""
        try:
            service_token = request.headers.get("X-Service-Token")
            if not service_token:
                return {"authenticated": False}

            # Validate service token
            service_info = self.service_tokens.get(service_token)
            if not service_info:
                return {"authenticated": False, "error": "Invalid service token"}

            # Check token expiration
            if service_info.get("expires_at", 0) < datetime.utcnow().timestamp():
                return {"authenticated": False, "error": "Service token expired"}

            return {
                "authenticated": True,
                "user": f"service_{service_info['service_name']}",
                "permissions": service_info["permissions"],
                "method": "service_token",
                "service_name": service_info["service_name"],
            }

        except Exception as e:
            logger.error(f"Service token authentication error: {str(e)}")
            return {"authenticated": False, "error": str(e)}

    def authorize(self, user_permissions: list[str], required_permissions: list[str]) -> bool:
        """
        Check if user has required permissions.

        Args:
            user_permissions: list of user's permissions
            required_permissions: list of required permissions

        Returns:
            True if authorized, False otherwise
        """
        if "admin" in user_permissions:
            return True

        return all(perm in user_permissions for perm in required_permissions)

    def generate_jwt_token(
        self, user_id: str, permissions: list[str] = None, roles: list[str] = None, expires_in: int = 3600
    ) -> str:
        """
        Generate a JWT token for authenticated users.

        Args:
            user_id: User identifier
            permissions: list of user permissions
            roles: list of user roles
            expires_in: Token expiration time in seconds

        Returns:
            JWT token string
        """
        if permissions is None:
            permissions = []
        if roles is None:
            roles = []

        payload = {
            "sub": user_id,
            "user_id": user_id,
            "permissions": permissions,
            "roles": roles,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(seconds=expires_in),
        }

        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return token

    def generate_service_token(self, service_name: str, permissions: list[str] = None, expires_in: int = 3600) -> str:
        """
        Generate a service-to-service token.

        Args:
            service_name: Name of the service
            permissions: Service permissions
            expires_in: Token expiration time in seconds

        Returns:
            Service token string
        """
        if permissions is None:
            permissions = ["read"]

        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow().timestamp() + expires_in

        self.service_tokens[token] = {
            "service_name": service_name,
            "permissions": permissions,
            "expires_at": expires_at,
            "created_at": datetime.utcnow().timestamp(),
        }

        return token

    def validate_service_token(self, token: str) -> dict[str, Any] | None:
        """
        Validate a service token.

        Args:
            token: Service token to validate

        Returns:
            Service info if valid, None otherwise
        """
        service_info = self.service_tokens.get(token)
        if not service_info:
            return None

        if service_info.get("expires_at", 0) < datetime.utcnow().timestamp():
            # Remove expired token
            del self.service_tokens[token]
            return None

        return service_info


class RBACManager:
    """
    Role-Based Access Control manager for fine-grained permissions.
    """

    def __init__(self):
        self.roles = self._load_roles()
        self.permissions = self._load_permissions()

    def _load_roles(self) -> dict[str, dict[str, Any]]:
        """Load role definitions."""
        return {
            "admin": {"permissions": ["*"], "description": "Full system access"},
            "service": {"permissions": ["read", "write", "service_call"], "description": "Service-to-service access"},
            "user": {"permissions": ["read"], "description": "Basic user access"},
            "analyst": {"permissions": ["read", "analyze"], "description": "Data analysis access"},
        }

    def _load_permissions(self) -> dict[str, str]:
        """Load permission definitions."""
        return {
            "read": "Read access to resources",
            "write": "Write access to resources",
            "delete": "Delete access to resources",
            "admin": "Administrative access",
            "analyze": "Data analysis access",
            "service_call": "Service-to-service calls",
            "*": "All permissions",
        }

    def get_role_permissions(self, role: str) -> list[str]:
        """Get permissions for a role."""
        role_data = self.roles.get(role, {})
        return role_data.get("permissions", [])

    def has_permission(self, user_roles: list[str], permission: str) -> bool:
        """Check if user roles include the required permission."""
        for role in user_roles:
            role_permissions = self.get_role_permissions(role)
            if "*" in role_permissions or permission in role_permissions:
                return True
        return False
