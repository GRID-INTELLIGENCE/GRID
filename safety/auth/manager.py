from datetime import datetime, timedelta, timezone
from typing import Any

import redis
from jose import JWTError, jwt
from passlib.context import CryptContext

from ...src.grid.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthManager:
    """Authentication and authorization manager"""

    def __init__(self):
        self.redis_client = redis.Redis.from_url(settings.REDIS_URI)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)

    def create_access_token(self, data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    def verify_token(self, token: str) -> dict[str, Any] | None:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError:
            return None

    def authenticate_user(self, username: str, password: str) -> dict[str, Any] | None:
        """Authenticate user with username and password"""
        # In real implementation, this would query the database
        # For now, return mock user data
        if username == "admin" and password == "admin123":
            return {
                "id": 1,
                "username": username,
                "email": "admin@example.com",
                "full_name": "Administrator",
                "is_active": True,
                "trust_tier": "privileged",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "hashed_password": self.get_password_hash(password),
            }
        elif username == "user" and password == "user123":
            return {
                "id": 2,
                "username": username,
                "email": "user@example.com",
                "full_name": "Regular User",
                "is_active": True,
                "trust_tier": "user",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "hashed_password": self.get_password_hash(password),
            }
        return None

    def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        """Get user by username"""
        # In real implementation, this would query the database
        if username == "admin":
            return {
                "id": 1,
                "username": username,
                "email": "admin@example.com",
                "full_name": "Administrator",
                "is_active": True,
                "trust_tier": "privileged",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        elif username == "user":
            return {
                "id": 2,
                "username": username,
                "email": "user@example.com",
                "full_name": "Regular User",
                "is_active": True,
                "trust_tier": "user",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        return None

    def check_rate_limit(self, user_id: str, action: str = "request") -> bool:
        """Check if user is within rate limits"""
        key = f"ratelimit:{user_id}:{action}"
        current_time = datetime.now(timezone.utc).timestamp()

        # Clean old entries
        self.redis_client.zremrangebyscore(key, 0, current_time - settings.RATE_LIMIT_WINDOW)

        # Check current count
        count = self.redis_client.zcard(key)

        if count >= settings.RATE_LIMIT_REQUESTS:
            return False

        # Add new request
        self.redis_client.zadd(key, {str(current_time): current_time})
        self.redis_client.expire(key, settings.RATE_LIMIT_WINDOW)

        return True

    def get_trust_tier_limits(self, trust_tier: str) -> dict[str, int]:
        """Get rate limits for trust tier"""
        limits = {
            "anon": {"requests": 10, "window": 60},
            "user": {"requests": 100, "window": 60},
            "verified": {"requests": 500, "window": 60},
            "privileged": {"requests": 1000, "window": 60},
        }
        return limits.get(trust_tier, limits["anon"])

    def validate_trust_tier_access(self, user_tier: str, required_tier: str) -> bool:
        """Validate if user has required trust tier"""
        tiers = ["anon", "user", "verified", "privileged"]
        user_level = tiers.index(user_tier) if user_tier in tiers else 0
        required_level = tiers.index(required_tier) if required_tier in tiers else 0
        return user_level >= required_level

    def log_security_event(self, event_type: str, user_id: str, details: dict[str, Any]):
        """Log security-related events"""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "details": details,
        }
        # In real implementation, this would log to security database
        print(f"Security Event: {event}")


# Global auth manager instance
auth_manager = AuthManager()
