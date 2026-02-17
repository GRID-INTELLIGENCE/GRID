import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import TypedDict, cast

import bcrypt

from grid.auth.token_manager import TokenManager
from grid.config.runtime_settings import RuntimeSettings
from grid.infrastructure.database import DatabaseManager

logger = logging.getLogger(__name__)


class _UserRow(TypedDict):
    id: str
    username: str
    password_hash: str
    role: str


class _TokenRow(TypedDict, total=False):
    token_id: str
    user_id: str
    revoked: int
    expires_at: datetime | str | int | float | None


class AuthService:
    """
    Handles User Authentication, Registration, and Token Lifecycle.
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        token_manager: TokenManager,
        settings: RuntimeSettings | None = None,
    ):
        self.db = db_manager
        self.tm = token_manager
        runtime = settings or RuntimeSettings.from_env()
        self._refresh_expiry_days = runtime.security.refresh_token_expire_days

    async def register_user(self, username: str, password: str, role: str = "user") -> str:
        """Register a new user."""
        # Check existing
        existing = await self.db.fetch_one("SELECT id FROM users WHERE username = ?", (username,))
        if existing:
            raise ValueError("Username already exists")

        # Hash password
        salt = bcrypt.gensalt()
        pw_hash = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

        user_id = str(uuid.uuid4())
        await self.db.execute(
            "INSERT INTO users (id, username, password_hash, role) VALUES (?, ?, ?, ?)",
            (user_id, username, pw_hash, role),
        )
        await self.db.commit()
        return user_id

    async def login(self, username: str, password: str) -> dict[str, str]:
        """Login user and return tokens."""
        user_raw = await self.db.fetch_one("SELECT * FROM users WHERE username = ?", (username,))
        if not user_raw:
            raise ValueError("Invalid credentials")

        user = cast(_UserRow, dict(user_raw))
        if not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
            raise ValueError("Invalid credentials")

        # Issue tokens
        user_data: dict[str, str] = {"sub": user["id"], "role": user["role"], "username": user["username"]}
        access_token = self.tm.create_access_token(user_data)

        # Create Opaque Refresh Token (Store in DB)
        refresh_token = str(uuid.uuid4())
        expiry = datetime.now(UTC) + timedelta(days=self._refresh_expiry_days)

        await self.db.execute(
            "INSERT INTO tokens (token_id, user_id, expires_at) VALUES (?, ?, ?)", (refresh_token, user["id"], expiry)
        )
        await self.db.commit()

        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

    async def refresh_access(self, refresh_token: str) -> dict[str, str]:
        """Rotate refresh token and issue new access token."""
        # Validate refresh token
        row_raw = await self.db.fetch_one("SELECT * FROM tokens WHERE token_id = ? AND revoked = 0", (refresh_token,))
        if not row_raw:
            raise ValueError("Invalid refresh token")

        row = cast(_TokenRow, row_raw)

        # Check expiry
        # SQLite stores timestamps as strings usually, depends on adapter.
        # aiosqlite with PARSE_DECLTYPES might handle it, but fallback to str comparison
        # or assuming ISO8601 string.
        # Ideally ensure row['expires_at'] is parsed or compatible.
        # For robustness, we'll try to parse if string.
        expires_at = row["expires_at"]
        expires_dt: datetime | None = None
        if isinstance(expires_at, datetime):
            expires_dt = expires_at
        elif isinstance(expires_at, (int, float)):
            expires_dt = datetime.fromtimestamp(expires_at, tz=UTC)
        elif isinstance(expires_at, str):
            try:
                expires_dt = datetime.fromisoformat(expires_at)
            except ValueError:
                expires_dt = None

        now = datetime.now(UTC)
        if expires_dt is None:
            await self.db.execute("UPDATE tokens SET revoked = 1 WHERE token_id = ?", (refresh_token,))
            await self.db.commit()
            raise ValueError("Refresh token expired")

        if expires_dt.tzinfo is None:
            expires_dt = expires_dt.replace(tzinfo=UTC)

        if expires_dt < now:
            await self.db.execute("UPDATE tokens SET revoked = 1 WHERE token_id = ?", (refresh_token,))
            await self.db.commit()
            raise ValueError("Refresh token expired")

        # Revoke old refresh token (Rotation)
        await self.db.execute("UPDATE tokens SET revoked = 1 WHERE token_id = ?", (refresh_token,))

        # Issue new tokens
        user_raw = await self.db.fetch_one("SELECT * FROM users WHERE id = ?", (row["user_id"],))
        if not user_raw:
            raise ValueError("User not found")

        user = cast(_UserRow, dict(user_raw))
        user_data: dict[str, str] = {"sub": user["id"], "role": user["role"], "username": user["username"]}
        new_access = self.tm.create_access_token(user_data)

        new_refresh = str(uuid.uuid4())
        new_expiry = now + timedelta(days=self._refresh_expiry_days)

        await self.db.execute(
            "INSERT INTO tokens (token_id, user_id, expires_at) VALUES (?, ?, ?)", (new_refresh, user["id"], new_expiry)
        )
        await self.db.commit()

        return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer"}
