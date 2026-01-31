"""
Knowledge Base Security System
===============================

Comprehensive security system providing authentication, authorization,
rate limiting, and data protection for the GRID Knowledge Base.
"""

import hashlib
import logging
import re
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from typing import Any

import jwt

from ..core.config import KnowledgeBaseConfig

logger = logging.getLogger(__name__)


@dataclass
class User:
    """User account information."""
    user_id: str
    username: str
    email: str
    role: str = "user"
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_login: datetime | None = None
    permissions: list[str] = field(default_factory=list)


@dataclass
class APIKey:
    """API key for programmatic access."""
    key_id: str
    name: str
    user_id: str
    key_hash: str
    permissions: list[str]
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime | None = None
    last_used: datetime | None = None


@dataclass
class RateLimitRule:
    """Rate limiting rule."""
    name: str
    max_requests: int
    window_seconds: int
    block_duration: int = 300  # 5 minutes


class JWTManager:
    """JSON Web Token management."""

    def __init__(self, config: KnowledgeBaseConfig):
        self.config = config
        if not config.security.jwt_secret:
            raise ValueError("JWT_SECRET is required for authentication")

    def create_token(self, user: User) -> str:
        """Create JWT token for user."""
        payload = {
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role,
            "permissions": user.permissions,
            "iat": datetime.now().timestamp(),
            "exp": (datetime.now() + timedelta(seconds=self.config.security.jwt_expiration)).timestamp()
        }

        return jwt.encode(payload, self.config.security.jwt_secret, algorithm=self.config.security.jwt_algorithm)

    def verify_token(self, token: str) -> dict[str, Any] | None:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.config.security.jwt_secret,
                               algorithms=[self.config.security.jwt_algorithm])

            # Check if token is expired
            if payload.get("exp", 0) < datetime.now().timestamp():
                return None

            return payload
        except jwt.InvalidTokenError:
            return None

    def get_user_from_token(self, token: str) -> User | None:
        """Extract user information from token."""
        payload = self.verify_token(token)
        if not payload:
            return None

        return User(
            user_id=payload["user_id"],
            username=payload["username"],
            email="",  # Email not stored in token
            role=payload.get("role", "user"),
            permissions=payload.get("permissions", [])
        )


class APIKeyManager:
    """API key management and validation."""

    def __init__(self):
        self.keys: dict[str, APIKey] = {}
        # In production, this would be stored in a database

    def create_key(self, name: str, user_id: str, permissions: list[str],
                  expires_days: int | None = None) -> str:
        """Create a new API key."""
        # Generate secure random key
        raw_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        key_id = secrets.token_urlsafe(8)

        expires_at = None
        if expires_days:
            expires_at = datetime.now() + timedelta(days=expires_days)

        api_key = APIKey(
            key_id=key_id,
            name=name,
            user_id=user_id,
            key_hash=key_hash,
            permissions=permissions,
            expires_at=expires_at
        )

        self.keys[key_id] = api_key

        logger.info(f"API key created: {name} for user {user_id}")
        return raw_key  # Return the actual key only once

    def validate_key(self, provided_key: str) -> APIKey | None:
        """Validate an API key."""
        # Hash the provided key
        key_hash = hashlib.sha256(provided_key.encode()).hexdigest()

        # Find matching key
        for api_key in self.keys.values():
            if api_key.key_hash == key_hash and api_key.is_active:
                # Check expiration
                if api_key.expires_at and datetime.now() > api_key.expires_at:
                    api_key.is_active = False
                    continue

                # Update last used
                api_key.last_used = datetime.now()
                return api_key

        return None

    def revoke_key(self, key_id: str) -> bool:
        """Revoke an API key."""
        if key_id in self.keys:
            self.keys[key_id].is_active = False
            logger.info(f"API key revoked: {key_id}")
            return True
        return False

    def list_user_keys(self, user_id: str) -> list[dict[str, Any]]:
        """List API keys for a user."""
        user_keys = []
        for api_key in self.keys.values():
            if api_key.user_id == user_id:
                user_keys.append({
                    "key_id": api_key.key_id,
                    "name": api_key.name,
                    "permissions": api_key.permissions,
                    "is_active": api_key.is_active,
                    "created_at": api_key.created_at.isoformat(),
                    "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
                    "last_used": api_key.last_used.isoformat() if api_key.last_used else None
                })

        return user_keys


class RateLimiter:
    """Rate limiting system."""

    def __init__(self):
        self.requests: dict[str, list[float]] = {}
        self.blocked: dict[str, float] = {}

    def check_limit(self, identifier: str, rule: RateLimitRule) -> bool:
        """Check if request is within rate limits."""
        now = time.time()

        # Check if user is blocked
        if identifier in self.blocked:
            if now < self.blocked[identifier]:
                return False  # Still blocked
            else:
                del self.blocked[identifier]  # Block expired

        # Initialize request history
        if identifier not in self.requests:
            self.requests[identifier] = []

        # Clean old requests outside the window
        window_start = now - rule.window_seconds
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]

        # Check if under limit
        if len(self.requests[identifier]) < rule.max_requests:
            self.requests[identifier].append(now)
            return True

        # Rate limit exceeded - block user
        self.blocked[identifier] = now + rule.block_duration
        logger.warning(f"Rate limit exceeded for {identifier}, blocked for {rule.block_duration}s")
        return False

    def get_remaining_requests(self, identifier: str, rule: RateLimitRule) -> int:
        """Get remaining requests for user."""
        now = time.time()
        window_start = now - rule.window_seconds

        valid_requests = [
            req_time for req_time in self.requests.get(identifier, [])
            if req_time > window_start
        ]

        return max(0, rule.max_requests - len(valid_requests))

    def clear_expired_blocks(self) -> None:
        """Clear expired blocks."""
        now = time.time()
        expired = [k for k, v in self.blocked.items() if now >= v]
        for key in expired:
            del self.blocked[key]


class AccessControl:
    """Role-based access control system."""

    def __init__(self):
        # Define roles and their permissions
        self.role_permissions = {
            "admin": [
                "read:*", "write:*", "delete:*", "admin:*",
                "search:*", "generate:*", "ingest:*"
            ],
            "editor": [
                "read:*", "write:documents", "write:chunks",
                "search:*", "generate:*", "ingest:*"
            ],
            "user": [
                "read:documents", "read:chunks", "search:*", "generate:basic"
            ],
            "viewer": [
                "read:documents", "read:chunks", "search:public"
            ]
        }

    def has_permission(self, user_permissions: list[str], required_permission: str) -> bool:
        """Check if user has required permission."""
        # Check exact match
        if required_permission in user_permissions:
            return True

        # Check wildcards
        for perm in user_permissions:
            if perm.endswith("*"):
                prefix = perm[:-1]
                if required_permission.startswith(prefix):
                    return True

        return False

    def get_role_permissions(self, role: str) -> list[str]:
        """Get permissions for a role."""
        return self.role_permissions.get(role, [])

    def add_role_permission(self, role: str, permission: str) -> None:
        """Add permission to a role."""
        if role not in self.role_permissions:
            self.role_permissions[role] = []

        if permission not in self.role_permissions[role]:
            self.role_permissions[role].append(permission)

    def remove_role_permission(self, role: str, permission: str) -> None:
        """Remove permission from a role."""
        if role in self.role_permissions and permission in self.role_permissions[role]:
            self.role_permissions[role].remove(permission)


class DataProtection:
    """Data protection and privacy utilities."""

    @staticmethod
    def mask_sensitive_data(text: str) -> str:
        """Mask sensitive information in text."""
        # Email masking
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                     '[EMAIL_MASKED]', text)

        # Phone number masking
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
                     '[PHONE_MASKED]', text)

        # SSN masking
        text = re.sub(r'\b\d{3}[-]?\d{2}[-]?\d{4}\b',
                     '[SSN_MASKED]', text)

        return text

    @staticmethod
    def validate_content_safety(text: str) -> dict[str, Any]:
        """Validate content for safety and compliance."""
        issues = []

        # Check for potentially harmful content
        harmful_patterns = [
            r'\b(hack|exploit|attack|malware)\b',
            r'\b(password|credential|secret)\b.*\b(leak|steal|hack)\b',
            r'\b(illegal|criminal|terrorist)\b'
        ]

        for pattern in harmful_patterns:
            if re.search(pattern, text.lower()):
                issues.append(f"Potentially harmful content detected: {pattern}")

        return {
            "safe": len(issues) == 0,
            "issues": issues,
            "content_length": len(text)
        }


class SecurityMiddleware:
    """Security middleware for request processing."""

    def __init__(self, config: KnowledgeBaseConfig):
        self.config = config
        self.jwt_manager = JWTManager(config)
        self.api_key_manager = APIKeyManager()
        self.rate_limiter = RateLimiter()
        self.access_control = AccessControl()

        # Default rate limit rule
        self.default_rule = RateLimitRule(
            name="default",
            max_requests=config.security.rate_limit_requests,
            window_seconds=config.security.rate_limit_window
        )

    def authenticate_request(self, token: str | None = None,
                           api_key: str | None = None) -> User | None:
        """Authenticate a request."""
        if not self.config.security.enable_auth:
            # Return anonymous user
            return User(
                user_id="anonymous",
                username="anonymous",
                email="",
                role="viewer",
                permissions=self.access_control.get_role_permissions("viewer")
            )

        # Try JWT token first
        if token:
            user = self.jwt_manager.get_user_from_token(token)
            if user:
                user.permissions = self.access_control.get_role_permissions(user.role)
                return user

        # Try API key
        if api_key:
            api_key_obj = self.api_key_manager.validate_key(api_key)
            if api_key_obj:
                # Create user from API key
                user = User(
                    user_id=api_key_obj.user_id,
                    username=f"api_{api_key_obj.key_id}",
                    email="",
                    permissions=api_key_obj.permissions
                )
                return user

        return None

    def check_rate_limit(self, identifier: str) -> bool:
        """Check rate limit for a request."""
        return self.rate_limiter.check_limit(identifier, self.default_rule)

    def authorize_action(self, user: User, action: str, resource: str = "") -> bool:
        """Authorize a user action."""
        required_permission = f"{action}:{resource}" if resource else action

        return self.access_control.has_permission(user.permissions, required_permission)

    def validate_content(self, content: str) -> dict[str, Any]:
        """Validate content for security."""
        return DataProtection.validate_content_safety(content)

    def create_api_key(self, name: str, user_id: str, permissions: list[str]) -> str:
        """Create an API key."""
        return self.api_key_manager.create_key(name, user_id, permissions)

    def get_user_api_keys(self, user_id: str) -> list[dict[str, Any]]:
        """Get API keys for a user."""
        return self.api_key_manager.list_user_keys(user_id)

    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key."""
        return self.api_key_manager.revoke_key(key_id)

    def get_security_status(self) -> dict[str, Any]:
        """Get security system status."""
        return {
            "authentication_enabled": self.config.security.enable_auth,
            "rate_limiting_enabled": True,
            "active_api_keys": len([k for k in self.api_key_manager.keys.values() if k.is_active]),
            "blocked_users": len(self.rate_limiter.blocked),
            "jwt_expiration_hours": self.config.security.jwt_expiration / 3600
        }


def require_auth(permission: str = ""):
    """Decorator for requiring authentication and permissions."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # This would be implemented in the actual API layer
            # For now, just log the requirement
            logger.debug(f"Function {func.__name__} requires permission: {permission}")
            return func(*args, **kwargs)
        return wrapper
    return decorator


def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """Decorator for rate limiting."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # This would be implemented in the actual API layer
            # For now, just log the limit
            logger.debug(f"Function {func.__name__} rate limited: {max_requests}/{window_seconds}s")
            return func(*args, **kwargs)
        return wrapper
    return decorator
