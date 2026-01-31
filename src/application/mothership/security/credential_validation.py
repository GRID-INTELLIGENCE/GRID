"""Production credential validation service.

Provides secure user authentication with:
- User database queries
- Password hash verification (bcrypt)
- Account status checks (active, suspended, banned, etc.)
- Failed login attempt tracking
- Account lockout protection
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from grid.organization.models import User, UserStatus

logger = logging.getLogger(__name__)


@dataclass
class AuthResult:
    """Authentication result."""

    success: bool
    user: User | None = None
    error_message: str | None = None
    error_code: str | None = None


class CredentialValidationService:
    """Production credential validation service.

    Handles secure user authentication with:
    - User database queries
    - Password hash verification
    - Account status checks
    - Failed login tracking
    """

    def __init__(self, user_store: dict[str, User] | None = None, max_failed_attempts: int = 5, lockout_duration_minutes: int = 30):
        """Initialize the credential validation service.

        Args:
            user_store: In-memory user store (for testing/demo). In production, use database.
            max_failed_attempts: Maximum failed login attempts before lockout
            lockout_duration_minutes: Duration of account lockout in minutes
        """
        self._user_store = user_store or {}
        self._max_failed_attempts = max_failed_attempts
        self._lockout_duration = timedelta(minutes=lockout_duration_minutes)
        self._failed_attempts: dict[str, list[datetime]] = {}
        self._lockouts: dict[str, datetime] = {}

    async def validate_credentials(self, username: str, password: str) -> AuthResult:
        """Validate user credentials for production.

        Args:
            username: Username to validate
            password: Plain-text password to verify

        Returns:
            AuthResult with success status and user or error details
        """
        # Check if account is locked out
        lockout_result = self._check_lockout(username)
        if lockout_result:
            return lockout_result

        # Query user from database/store
        user = await self._query_user(username)
        if not user:
            self._record_failed_attempt(username)
            return AuthResult(
                success=False,
                error_message="Invalid username or password",
                error_code="INVALID_CREDENTIALS"
            )

        # Check account status
        status_result = self._check_account_status(user)
        if status_result:
            return status_result

        # Verify password hash
        if not await self._verify_password(password, user):
            self._record_failed_attempt(username)
            return AuthResult(
                success=False,
                error_message="Invalid username or password",
                error_code="INVALID_CREDENTIALS"
            )

        # Clear failed attempts on successful login
        self._clear_failed_attempts(username)
        user.update_activity()

        logger.info(f"User authenticated successfully: {username}")
        return AuthResult(success=True, user=user)

    async def _query_user(self, username: str) -> User | None:
        """Query user from database by username.

        In production, this would query PostgreSQL or similar.
        For now, uses in-memory store with case-insensitive lookup.
        """
        # Case-insensitive username lookup
        username_lower = username.lower()

        # Check in-memory store first
        for user in self._user_store.values():
            if user.username.lower() == username_lower:
                return user

        # TODO: In production, query database here
        # Example with asyncpg:
        # async with db_pool.acquire() as conn:
        #     row = await conn.fetchrow(
        #         "SELECT * FROM users WHERE LOWER(username) = LOWER($1)",
        #         username
        #     )
        #     if row:
        #         return User.from_db_row(row)

        return None

    def _check_account_status(self, user: User) -> AuthResult | None:
        """Check if user account is in valid state for login.

        Returns:
            AuthResult with error if account is not active, None if OK
        """
        if user.status == UserStatus.SUSPENDED:
            return AuthResult(
                success=False,
                error_message="Account is suspended. Please contact support.",
                error_code="ACCOUNT_SUSPENDED"
            )

        if user.status == UserStatus.BANNED:
            return AuthResult(
                success=False,
                error_message="Account has been banned.",
                error_code="ACCOUNT_BANNED"
            )

        if user.status == UserStatus.INACTIVE:
            return AuthResult(
                success=False,
                error_message="Account is inactive. Please activate your account.",
                error_code="ACCOUNT_INACTIVE"
            )

        if user.status == UserStatus.PENDING:
            return AuthResult(
                success=False,
                error_message="Account registration is pending approval.",
                error_code="ACCOUNT_PENDING"
            )

        return None

    async def _verify_password(self, password: str, user: User) -> bool:
        """Verify password against stored hash.

        Uses bcrypt for secure password hashing.
        """
        try:
            import bcrypt

            # Get stored password hash from user metadata
            # In production, this would be in a dedicated password_hash field
            stored_hash = user.metadata.get("password_hash")
            if not stored_hash:
                logger.warning(f"User {user.username} has no password hash stored")
                return False

            # Verify password
            if isinstance(stored_hash, str):
                stored_hash = stored_hash.encode('utf-8')

            return bcrypt.checkpw(password.encode('utf-8'), stored_hash)

        except ImportError:
            logger.error("bcrypt not installed, cannot verify password")
            return False
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    def _check_lockout(self, username: str) -> AuthResult | None:
        """Check if account is currently locked out.

        Returns:
            AuthResult with error if locked out, None if OK
        """
        username_lower = username.lower()

        # Check if currently locked out
        if username_lower in self._lockouts:
            lockout_end = self._lockouts[username_lower] + self._lockout_duration
            if datetime.now(UTC) < lockout_end:
                remaining = lockout_end - datetime.now(UTC)
                return AuthResult(
                    success=False,
                    error_message=f"Account is locked. Try again in {remaining.seconds // 60} minutes.",
                    error_code="ACCOUNT_LOCKED"
                )
            else:
                # Lockout expired, remove it
                del self._lockouts[username_lower]
                self._failed_attempts.pop(username_lower, None)

        return None

    def _record_failed_attempt(self, username: str) -> None:
        """Record a failed login attempt."""
        username_lower = username.lower()

        if username_lower not in self._failed_attempts:
            self._failed_attempts[username_lower] = []

        # Add timestamp
        self._failed_attempts[username_lower].append(datetime.now(UTC))

        # Clean old attempts (older than lockout duration)
        cutoff = datetime.now(UTC) - self._lockout_duration
        self._failed_attempts[username_lower] = [
            t for t in self._failed_attempts[username_lower] if t > cutoff
        ]

        # Check if should lockout
        if len(self._failed_attempts[username_lower]) >= self._max_failed_attempts:
            self._lockouts[username_lower] = datetime.now(UTC)
            logger.warning(f"Account locked due to failed attempts: {username}")

    def _clear_failed_attempts(self, username: str) -> None:
        """Clear failed login attempts for user."""
        username_lower = username.lower()
        self._failed_attempts.pop(username_lower, None)
        self._lockouts.pop(username_lower, None)

    async def create_user(
        self,
        username: str,
        password: str,
        email: str | None = None,
        org_id: str | None = None,
        role: str = "viewer"
    ) -> User:
        """Create a new user with hashed password.

        Args:
            username: Unique username
            password: Plain-text password (will be hashed)
            email: Email address
            org_id: Organization ID
            role: User role

        Returns:
            Created User object
        """
        import bcrypt

        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))

        # Create user
        user = User(
            username=username,
            email=email,
            org_id=org_id,
            status=UserStatus.ACTIVE,
        )

        # Store password hash in metadata
        user.metadata["password_hash"] = password_hash.decode('utf-8')

        # Add to store
        self._user_store[user.user_id] = user

        logger.info(f"Created user: {username}")
        return user


# Global instance for convenience
credential_validator: CredentialValidationService | None = None


def get_credential_validator() -> CredentialValidationService:
    """Get or create the global credential validator."""
    global credential_validator
    if credential_validator is None:
        credential_validator = CredentialValidationService()
    return credential_validator


async def validate_production_credentials(username: str, password: str) -> AuthResult:
    """Convenience function for production credential validation.

    Args:
        username: Username to validate
        password: Password to verify

    Returns:
        AuthResult with authentication status
    """
    validator = get_credential_validator()
    return await validator.validate_credentials(username, password)
