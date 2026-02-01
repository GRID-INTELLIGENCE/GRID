import logging
import uuid
from datetime import UTC, datetime, timedelta

import bcrypt

from src.application.mothership.config import MothershipSettings
from src.grid.auth.token_manager import TokenManager
from src.grid.infrastructure.database import DatabaseManager

logger = logging.getLogger(__name__)
settings = MothershipSettings.from_env()

class AuthService:
    """
    Handles User Authentication, Registration, and Token Lifecycle.
    """
    def __init__(self, db_manager: DatabaseManager, token_manager: TokenManager):
        self.db = db_manager
        self.tm = token_manager
        self._refresh_expiry_days = settings.security.refresh_token_expire_days

    async def register_user(self, username: str, password: str, role: str = "user") -> str:
        """Register a new user."""
        # Check existing
        existing = await self.db.fetch_one("SELECT id FROM users WHERE username = ?", (username,))
        if existing:
            raise ValueError("Username already exists")

        # Hash password
        salt = bcrypt.gensalt()
        pw_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

        user_id = str(uuid.uuid4())
        await self.db.execute(
            "INSERT INTO users (id, username, password_hash, role) VALUES (?, ?, ?, ?)",
            (user_id, username, pw_hash, role)
        )
        await self.db.commit()
        return user_id

    async def login(self, username: str, password: str) -> dict[str, str]:
        """Login user and return tokens."""
        user = await self.db.fetch_one("SELECT * FROM users WHERE username = ?", (username,))
        if not user:
            raise ValueError("Invalid credentials")

        if not bcrypt.checkpw(password.encode('utf-8'), user["password_hash"].encode('utf-8')):
            raise ValueError("Invalid credentials")

        # Issue tokens
        user_data = {"sub": user["id"], "role": user["role"], "username": user["username"]}
        access_token = self.tm.create_access_token(user_data)

        # Create Opaque Refresh Token (Store in DB)
        refresh_token = str(uuid.uuid4())
        expiry = datetime.now(UTC) + timedelta(days=self._refresh_expiry_days)

        await self.db.execute(
            "INSERT INTO tokens (token_id, user_id, expires_at) VALUES (?, ?, ?)",
            (refresh_token, user["id"], expiry)
        )
        await self.db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    async def refresh_access(self, refresh_token: str) -> dict[str, str]:
        """Rotate refresh token and issue new access token."""
        # Validate refresh token
        row = await self.db.fetch_one(
            "SELECT * FROM tokens WHERE token_id = ? AND revoked = 0",
            (refresh_token,)
        )
        if not row:
            raise ValueError("Invalid refresh token")

        # Check expiry
        # SQLite stores timestamps as strings usually, depends on adapter.
        # aiosqlite with PARSE_DECLTYPES might handle it, but fallback to str comparison
        # or assuming ISO8601 string.
        # Ideally ensure row['expires_at'] is parsed or compatible.
        # For robustness, we'll try to parse if string.
        expires_at = row["expires_at"]
        if isinstance(expires_at, str):
            try:
                expires_at = datetime.fromisoformat(expires_at)
            except ValueError:
                pass # Already timestamp? or fail.

        # If localized/naive mismatch, assume UTC
        now = datetime.now(UTC)
        if expires_at.replace(tzinfo=UTC) < now:
             await self.db.execute("UPDATE tokens SET revoked = 1 WHERE token_id = ?", (refresh_token,))
             await self.db.commit()
             raise ValueError("Refresh token expired")

        # Revoke old refresh token (Rotation)
        await self.db.execute("UPDATE tokens SET revoked = 1 WHERE token_id = ?", (refresh_token,))

        # Issue new tokens
        user = await self.db.fetch_one("SELECT * FROM users WHERE id = ?", (row["user_id"],))
        if not user:
            raise ValueError("User not found")

        user_data = {"sub": user["id"], "role": user["role"], "username": user["username"]}
        new_access = self.tm.create_access_token(user_data)

        new_refresh = str(uuid.uuid4())
        new_expiry = now + timedelta(days=self._refresh_expiry_days)

        await self.db.execute(
            "INSERT INTO tokens (token_id, user_id, expires_at) VALUES (?, ?, ?)",
            (new_refresh, user["id"], new_expiry)
        )
        await self.db.commit()

        return {
            "access_token": new_access,
            "refresh_token": new_refresh,
            "token_type": "bearer"
        }
