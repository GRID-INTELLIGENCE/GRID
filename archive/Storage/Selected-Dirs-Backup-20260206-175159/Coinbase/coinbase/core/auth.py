"""
Authentication and Authorization System
========================================
JWT-based authentication with session management and MFA support.

Usage:
    from coinbase.core.auth import AuthManager, UserSession

    auth = AuthManager()

    # Authenticate user
    session = auth.authenticate("user123", "password")

    # Verify token
    payload = auth.verify_token(session.token)
"""

import base64
import hashlib
import logging
import secrets
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import jwt

logger = logging.getLogger(__name__)


class UserRole(Enum):
    """User roles for authorization."""

    ADMIN = "admin"
    USER = "user"
    ANALYST = "analyst"
    API = "api"


@dataclass
class UserSession:
    """User session information."""

    user_id: str
    token: str
    role: UserRole
    created_at: datetime
    expires_at: datetime
    last_accessed: datetime
    mfa_verified: bool = False
    permissions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.now() > self.expires_at

    def is_active(self) -> bool:
        """Check if session is active."""
        return not self.is_expired()

    def touch(self) -> None:
        """Update last accessed time."""
        self.last_accessed = datetime.now()


@dataclass
class AuthConfig:
    """Authentication configuration."""

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    mfa_enabled: bool = False
    max_sessions_per_user: int = 5
    password_hash_algorithm: str = "sha256"


class AuthManager:
    """
    Authentication and authorization manager.

    Features:
    - JWT token generation and validation
    - Session management
    - Multi-factor authentication
    - Role-based access control
    """

    def __init__(self, config: AuthConfig | None = None):
        """
        Initialize auth manager.

        Args:
            config: Authentication configuration
        """
        # Get config from environment if not provided
        if config is None:
            import os

            jwt_secret = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
            config = AuthConfig(jwt_secret=jwt_secret)

        self.config = config
        self._sessions: dict[str, UserSession] = {}
        self._user_sessions: dict[str, list[str]] = {}  # user_id -> session_ids
        self._lock = threading.Lock()

    def hash_password(self, password: str, salt: str | None = None) -> tuple[str, str]:
        """
        Hash password with salt.

        Args:
            password: Plain text password
            salt: Optional salt

        Returns:
            Tuple of (hash, salt)
        """
        if salt is None:
            salt = secrets.token_hex(16)

        salted = f"{password}{salt}"
        hash_value = hashlib.sha256(salted.encode()).hexdigest()

        return hash_value, salt

    def verify_password(self, password: str, hash_value: str, salt: str) -> bool:
        """
        Verify password against hash.

        Args:
            password: Plain text password
            hash_value: Stored hash
            salt: Stored salt

        Returns:
            True if password matches
        """
        computed_hash, _ = self.hash_password(password, salt)
        return computed_hash == hash_value

    def create_access_token(
        self,
        user_id: str,
        role: UserRole,
        mfa_verified: bool = False,
        additional_claims: dict | None = None,
    ) -> str:
        """
        Create JWT access token.

        Args:
            user_id: User identifier
            role: User role
            mfa_verified: MFA verification status
            additional_claims: Optional additional claims

        Returns:
            JWT token
        """
        now = datetime.utcnow()  # Use UTC for consistency
        expires = now + timedelta(minutes=self.config.access_token_expire_minutes)

        payload = {
            "sub": user_id,
            "role": role.value,
            "mfa_verified": mfa_verified,
            "iat": now - timedelta(seconds=1),  # Subtract 1s to avoid clock skew issues
            "exp": expires,
            "jti": secrets.token_hex(16),  # Unique token ID
        }

        if additional_claims:
            payload.update(additional_claims)

        token = jwt.encode(payload, self.config.jwt_secret, algorithm=self.config.jwt_algorithm)

        return token

    def verify_token(self, token: str) -> dict[str, Any] | None:
        """
        Verify and decode JWT token.

        Args:
            token: JWT token

        Returns:
            Decoded payload or None if invalid
        """
        try:
            payload = jwt.decode(
                token, self.config.jwt_secret, algorithms=[self.config.jwt_algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None

    def authenticate(
        self,
        user_id: str,
        password: str,
        stored_hash: str,
        stored_salt: str,
        role: UserRole = UserRole.USER,
    ) -> UserSession | None:
        """
        Authenticate user and create session.

        Args:
            user_id: User identifier
            password: Plain text password
            stored_hash: Stored password hash
            stored_salt: Stored password salt
            role: User role

        Returns:
            UserSession or None if authentication fails
        """
        # Verify password
        if not self.verify_password(password, stored_hash, stored_salt):
            logger.warning(f"Authentication failed for user: {user_id}")
            return None

        with self._lock:
            # Check max sessions
            if user_id in self._user_sessions:
                if len(self._user_sessions[user_id]) >= self.config.max_sessions_per_user:
                    # Remove oldest session
                    oldest_session = self._sessions[self._user_sessions[user_id][0]]
                    self._remove_session(oldest_session.token)

            # Create token
            token = self.create_access_token(user_id, role)

            # Create session
            now = datetime.now()
            session = UserSession(
                user_id=user_id,
                token=token,
                role=role,
                created_at=now,
                expires_at=now + timedelta(minutes=self.config.access_token_expire_minutes),
                last_accessed=now,
                mfa_verified=False,
            )

            # Store session
            self._sessions[token] = session

            if user_id not in self._user_sessions:
                self._user_sessions[user_id] = []
            self._user_sessions[user_id].append(token)

            logger.info(f"User authenticated: {user_id}")
            return session

    def verify_session(self, token: str) -> UserSession | None:
        """
        Verify session token.

        Args:
            token: Session token

        Returns:
            UserSession or None if invalid/expired
        """
        with self._lock:
            session = self._sessions.get(token)

            if not session:
                return None

            if session.is_expired():
                self._remove_session(token)
                return None

            # Update last accessed
            session.touch()

            return session

    def logout(self, token: str) -> bool:
        """
        Logout user and invalidate session.

        Args:
            token: Session token

        Returns:
            True if session was removed
        """
        with self._lock:
            return self._remove_session(token)

    def logout_all_sessions(self, user_id: str) -> int:
        """
        Logout all sessions for a user.

        Args:
            user_id: User identifier

        Returns:
            Number of sessions removed
        """
        with self._lock:
            tokens = self._user_sessions.get(user_id, [])
            count = 0
            for token in tokens[:]:
                if self._remove_session(token):
                    count += 1
            return count

    def _remove_session(self, token: str) -> bool:
        """Remove session from storage."""
        session = self._sessions.get(token)
        if not session:
            return False

        del self._sessions[token]

        if session.user_id in self._user_sessions:
            if token in self._user_sessions[session.user_id]:
                self._user_sessions[session.user_id].remove(token)

        return True

    def check_permission(self, session: UserSession, required_permission: str) -> bool:
        """
        Check if session has required permission.

        Args:
            session: User session
            required_permission: Required permission

        Returns:
            True if has permission
        """
        # Admin has all permissions
        if session.role == UserRole.ADMIN:
            return True

        # Check specific permissions
        return required_permission in session.permissions

    def require_mfa(self, token: str, mfa_code: str, secret: str) -> bool:
        """
        Verify MFA code and mark session as MFA verified.

        Args:
            token: Session token
            mfa_code: MFA code
            secret: MFA secret

        Returns:
            True if MFA verified
        """
        # Simple TOTP verification (simplified)
        import base64
        import hmac
        import struct

        try:
            # Decode secret
            key = base64.b32decode(secret.upper())

            # Get current timestamp
            counter = int(datetime.now().timestamp()) // 30

            # Generate TOTP
            counter_bytes = struct.pack(">Q", counter)
            mac = hmac.new(key, counter_bytes, hashlib.sha1).digest()
            offset = mac[-1] & 0x0F
            code = (
                (mac[offset] & 0x7F) << 24
                | (mac[offset + 1] & 0xFF) << 16
                | (mac[offset + 2] & 0xFF) << 8
                | (mac[offset + 3] & 0xFF)
            )
            code = code % 1000000
            expected_code = f"{code:06d}"

            if mfa_code == expected_code:
                # Mark session as MFA verified
                with self._lock:
                    session = self._sessions.get(token)
                    if session:
                        session.mfa_verified = True
                return True

            return False

        except Exception as e:
            logger.error(f"MFA verification failed: {e}")
            return False

    def get_active_sessions(self, user_id: str | None = None) -> list[UserSession]:
        """
        Get active sessions.

        Args:
            user_id: Optional user filter

        Returns:
            List of active sessions
        """
        with self._lock:
            sessions = list(self._sessions.values())

            # Filter expired
            sessions = [s for s in sessions if not s.is_expired()]

            # Filter by user
            if user_id:
                sessions = [s for s in sessions if s.user_id == user_id]

            return sessions

    def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions.

        Returns:
            Number of sessions removed
        """
        with self._lock:
            expired_tokens = [
                token for token, session in self._sessions.items() if session.is_expired()
            ]

            for token in expired_tokens:
                self._remove_session(token)

            return len(expired_tokens)

    def generate_mfa_secret(self) -> str:
        """Generate MFA secret."""
        return base64.b32encode(secrets.token_bytes(20)).decode("utf-8")

    def get_session_stats(self) -> dict[str, Any]:
        """Get session statistics."""
        with self._lock:
            total_sessions = len(self._sessions)
            active_sessions = len([s for s in self._sessions.values() if s.is_active()])
            expired_sessions = total_sessions - active_sessions

            users_with_sessions = len(self._user_sessions)

            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "expired_sessions": expired_sessions,
                "users_with_sessions": users_with_sessions,
                "max_sessions_per_user": self.config.max_sessions_per_user,
            }


# Global auth manager instance
_global_auth_manager: AuthManager | None = None


def get_auth_manager() -> AuthManager:
    """Get global auth manager instance."""
    global _global_auth_manager
    if _global_auth_manager is None:
        _global_auth_manager = AuthManager()
    return _global_auth_manager


# Decorator for requiring authentication
def require_auth(permission: str | None = None) -> Any:
    """
    Decorator to require authentication.

    Args:
        permission: Optional required permission
    """

    def decorator(func: Any) -> Any:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get token from kwargs or args
            token = kwargs.get("token") or (args[0] if args else None)

            if not token:
                raise AuthenticationError("Authentication required")

            auth = get_auth_manager()
            session = auth.verify_session(token)

            if not session:
                raise AuthenticationError("Invalid or expired session")

            if permission and not auth.check_permission(session, permission):
                raise AuthorizationError(f"Permission required: {permission}")

            # Add session to kwargs
            kwargs["session"] = session

            return func(*args, **kwargs)

        return wrapper

    return decorator


class AuthenticationError(Exception):
    """Exception for authentication failures."""

    pass


class AuthorizationError(Exception):
    """Exception for authorization failures."""

    pass
