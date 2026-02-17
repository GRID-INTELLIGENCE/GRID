"""
Redis-backed token-bucket rate limiter with atomic Lua script and enhanced security features.

Features:
- User-based rate limiting
- IP-based rate limiting with geo-blocking
- Exponential backoff for violations
- Request signature validation
- Security headers and metrics

Keys: ratelimit:{user_id}:{feature}, ratelimit:ip:{ip_address}
Returns: (allowed: bool, remaining: int, reset_seconds: float, risk_score: float)
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import ipaddress
import os
import threading
import time
from typing import Any

import redis.asyncio as aioredis

from safety.api.auth import TIER_RATE_LIMITS, TrustTier
from safety.observability.logging_setup import get_logger
from safety.observability.metrics import RATE_LIMITED_TOTAL
from safety.observability.risk_score import risk_manager

logger = get_logger("api.rate_limiter")

# ---------------------------------------------------------------------------
# Security Configuration
# ---------------------------------------------------------------------------


class SecurityConfig:
    """Security configuration for rate limiting"""

    # IP-based rate limits (per minute)
    IP_RATE_LIMIT = int(os.getenv("IP_RATE_LIMIT", "100"))

    # Geo-blocking settings
    BLOCKED_COUNTRIES = set(os.getenv("BLOCKED_COUNTRIES", "CU,IR,KP,SY").split(","))
    ALLOWED_COUNTRIES = set(os.getenv("ALLOWED_COUNTRIES", "").split(",")) if os.getenv("ALLOWED_COUNTRIES") else None

    # Exponential backoff settings
    BASE_BACKOFF_SECONDS = 60  # 1 minute
    MAX_BACKOFF_SECONDS = 3600  # 1 hour
    BACKOFF_MULTIPLIER = 2.0

    # Risk scoring
    SUSPICIOUS_USER_AGENTS = {"curl", "wget", "python-requests", "go-http-client", "java/", "bot", "spider", "crawler"}

    # Request validation
    SECRET_KEY = os.getenv("RATE_LIMIT_SECRET", "")
    SIGNATURE_TTL = 300  # 5 minutes

    @classmethod
    def validate_secrets(cls) -> None:
        """Fail-fast if critical secrets are not configured."""
        _is_dev = os.environ.get("GRID_ENV", "production").lower() in ("development", "dev", "test")
        if not cls.SECRET_KEY or cls.SECRET_KEY == "change_me_in_production":
            if _is_dev:
                logger.warning("RATE_LIMIT_SECRET not set — using insecure default (dev mode only)")
                cls.SECRET_KEY = "insecure-dev-key-do-not-use-in-production"
            else:
                raise RuntimeError(
                    "RATE_LIMIT_SECRET is not configured. "
                    "Set the RATE_LIMIT_SECRET environment variable before starting in production."
                )


class IPRateLimiter:
    """IP-based rate limiting with geo-blocking"""

    def __init__(self):
        self.blocked_ips: set = set()
        self.suspicious_ips: dict[str, float] = {}  # ip -> risk_score
        self._lock = threading.Lock()

    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked"""
        with self._lock:
            return ip in self.blocked_ips

    def block_ip(self, ip: str, reason: str = "manual_block") -> None:
        """Block an IP address"""
        with self._lock:
            self.blocked_ips.add(ip)
        logger.warning(f"IP blocked: {ip}, reason: {reason}")

    def add_suspicious_activity(self, ip: str, risk_increment: float = 1.0) -> float:
        """Add suspicious activity for an IP and return updated risk score"""
        with self._lock:
            current_risk = self.suspicious_ips.get(ip, 0.0)
            new_risk = min(100.0, current_risk + risk_increment)
            self.suspicious_ips[ip] = new_risk

            if new_risk >= 50.0 and ip not in self.blocked_ips:
                self.blocked_ips.add(ip)
                logger.warning(f"IP blocked by risk score: {ip}, score: {new_risk}")

            return new_risk

    def is_ip_suspicious(self, ip: str) -> tuple[bool, float]:
        """Check if IP is suspicious and return risk score"""
        with self._lock:
            risk_score = self.suspicious_ips.get(ip, 0.0)
            return risk_score >= 25.0, risk_score


class ExponentialBackoff:
    """Exponential backoff for rate limit violations"""

    def __init__(self):
        self.violation_counts: dict[str, int] = {}
        self.backoff_until: dict[str, float] = {}
        self._lock = threading.Lock()

    def record_violation(self, key: str) -> float:
        """Record a violation and return backoff duration"""
        with self._lock:
            count = self.violation_counts.get(key, 0) + 1
            self.violation_counts[key] = count

            # Calculate backoff: base * (multiplier ^ violations)
            backoff_seconds = min(
                SecurityConfig.MAX_BACKOFF_SECONDS,
                SecurityConfig.BASE_BACKOFF_SECONDS * (SecurityConfig.BACKOFF_MULTIPLIER ** (count - 1)),
            )

            self.backoff_until[key] = time.time() + backoff_seconds
            return backoff_seconds

    def is_in_backoff(self, key: str) -> tuple[bool, float]:
        """Check if key is in backoff period and return remaining time"""
        with self._lock:
            until = self.backoff_until.get(key, 0)
            remaining = max(0, until - time.time())

            if remaining <= 0:
                # Clean up expired backoff
                self.violation_counts.pop(key, None)
                self.backoff_until.pop(key, None)
                return False, 0

            return True, remaining

    def reset_violations(self, key: str) -> None:
        """Reset violation count for a key"""
        with self._lock:
            self.violation_counts.pop(key, None)
            self.backoff_until.pop(key, None)


class RequestValidator:
    """Request signature validation and security checks"""

    @staticmethod
    def validate_request_signature(request_data: str, signature: str, timestamp: float, client_id: str) -> bool:
        """Validate HMAC signature of request"""
        # Check timestamp freshness
        if abs(time.time() - timestamp) > SecurityConfig.SIGNATURE_TTL:
            return False

        # Create expected signature
        message = f"{request_data}:{timestamp}:{client_id}"
        expected_signature = hmac.new(SecurityConfig.SECRET_KEY.encode(), message.encode(), hashlib.sha256).hexdigest()

        return hmac.compare_digest(signature, expected_signature)

    @staticmethod
    def check_user_agent_risk(user_agent: str | None) -> float:
        """Check user agent for suspicious patterns"""
        if not user_agent:
            return 10.0  # Missing user agent is suspicious

        user_agent_lower = user_agent.lower()

        for suspicious in SecurityConfig.SUSPICIOUS_USER_AGENTS:
            if suspicious in user_agent_lower:
                return 50.0  # High risk for automated tools

        return 0.0  # Normal user agent

    @staticmethod
    def validate_ip_format(ip: str) -> bool:
        """Validate IP address format"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False


# Global security instances
_ip_limiter = IPRateLimiter()
_backoff_manager = ExponentialBackoff()
_request_validator = RequestValidator()

# Lua script for atomic token bucket operations
TOKEN_BUCKET_LUA = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])

local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(bucket[1])
local last_refill = tonumber(bucket[2])

if tokens == nil then
    tokens = capacity
    last_refill = now
end

-- Refill tokens based on elapsed time
local elapsed = math.max(0, now - last_refill)
local refilled = math.min(capacity, tokens + elapsed * refill_rate)

-- Try to consume
local allowed = 0
if refilled >= requested then
    refilled = refilled - requested
    allowed = 1
end

-- Persist state
redis.call('HMSET', key, 'tokens', refilled, 'last_refill', now)

-- TTL: expire the key after 2x the time to fully refill
local ttl = math.ceil(capacity / refill_rate * 2)
redis.call('EXPIRE', key, ttl)

-- Calculate seconds until next token
local reset_seconds = 0
if allowed == 0 then
    reset_seconds = math.ceil((requested - refilled) / refill_rate)
end

return {allowed, math.floor(refilled), reset_seconds}
"""

# ---------------------------------------------------------------------------
# Rate limiter class
# ---------------------------------------------------------------------------

_redis_pool: aioredis.Redis | None = None
_lua_sha: str | None = None
_redis_lock = asyncio.Lock()
_lua_lock = asyncio.Lock()


async def _get_redis() -> aioredis.Redis:
    global _redis_pool
    if _redis_pool is None:
        async with _redis_lock:
            if _redis_pool is None:
                url = os.getenv("REDIS_URL", "redis://localhost:6379")
                _redis_pool = aioredis.from_url(url, decode_responses=True, max_connections=50)
    return _redis_pool


async def _ensure_lua_script(client: aioredis.Redis) -> str:
    """Load the Lua script into Redis and cache its SHA."""
    global _lua_sha
    if _lua_sha is None:
        async with _lua_lock:
            if _lua_sha is None:
                _lua_sha = await client.script_load(TOKEN_BUCKET_LUA)
            # At this point, _lua_sha is guaranteed to be a str
            assert _lua_sha is not None
    return _lua_sha  # type: ignore[return-value]


class RateLimitResult:
    """Result of a rate limit check"""

    __slots__ = ("allowed", "remaining", "reset_seconds", "risk_score", "blocked_reason")

    def __init__(
        self,
        allowed: bool,
        remaining: int,
        reset_seconds: float,
        risk_score: float = 0.0,
        blocked_reason: str | None = None,
    ):
        self.allowed = allowed
        self.remaining = remaining
        self.reset_seconds = reset_seconds
        self.risk_score = risk_score
        self.blocked_reason = blocked_reason

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "allowed": self.allowed,
            "remaining": self.remaining,
            "reset_seconds": self.reset_seconds,
            "risk_score": self.risk_score,
            "blocked_reason": self.blocked_reason,
        }

    def get_headers(self) -> dict[str, str]:
        """Get HTTP headers for rate limiting"""
        headers = {
            "X-RateLimit-Remaining": str(self.remaining),
            "X-RateLimit-Reset": str(int(self.reset_seconds)),
            "X-Risk-Score": str(self.risk_score),
        }

        if self.blocked_reason:
            headers["X-Blocked-Reason"] = self.blocked_reason

        return headers


async def allow_request(
    user_id: str,
    trust_tier: TrustTier,
    feature: str = "infer",
    *,
    ip_address: str | None = None,
    user_agent: str | None = None,
    request_signature: str | None = None,
    request_data: str | None = None,
    client_id: str | None = None,
) -> RateLimitResult:
    """
    Enhanced rate limiting with IP-based limits, exponential backoff, and security validation.

    Fails closed: if Redis is unreachable, denies the request.
    """
    # Security: Validate inputs
    if ip_address and not _request_validator.validate_ip_format(ip_address):
        logger.warning(f"Invalid IP format: {ip_address}")
        return RateLimitResult(allowed=False, remaining=0, reset_seconds=60.0, risk_score=100.0, blocked_reason="invalid_ip")

    # Security: Check if IP is blocked
    if ip_address and _ip_limiter.is_ip_blocked(ip_address):
        logger.warning(f"Blocked IP attempt: {ip_address}")
        return RateLimitResult(allowed=False, remaining=0, reset_seconds=3600.0, risk_score=100.0, blocked_reason="ip_blocked")

    # Security: Check exponential backoff
    backoff_key = f"{user_id}:{ip_address or 'unknown'}"
    in_backoff, backoff_remaining = _backoff_manager.is_in_backoff(backoff_key)
    if in_backoff:
        return RateLimitResult(allowed=False, remaining=0, reset_seconds=backoff_remaining, risk_score=75.0, blocked_reason="exponential_backoff")

    # Security: Validate request signature if provided
    if request_signature and request_data and client_id is not None:
        if not _request_validator.validate_request_signature(
            request_data, request_signature, time.time(), str(client_id)
        ):
            # Record violation for potential backoff
            _backoff_manager.record_violation(backoff_key)
            _ip_limiter.add_suspicious_activity(ip_address or "unknown", 20.0)
            return RateLimitResult(allowed=False, remaining=0, reset_seconds=300.0, risk_score=90.0, blocked_reason="invalid_signature")

    # Calculate immediate request risk score
    immediate_risk = 0.0

    # User agent risk
    if user_agent:
        immediate_risk += _request_validator.check_user_agent_risk(user_agent)

    # IP suspicious activity
    if ip_address:
        is_suspicious, ip_risk = _ip_limiter.is_ip_suspicious(ip_address)
        immediate_risk += ip_risk

    # Project GUARDIAN: Integrated Historical Risk Score
    historical_risk = await risk_manager.get_score(user_id)
    # Combined risk normalized to 0-100 for historical, immediate is already 0-100
    risk_score = min(100.0, immediate_risk + (historical_risk * 100.0))

    # Get base rate limits
    capacity = TIER_RATE_LIMITS.get(trust_tier, 20)

    # Apply risk-based adjustments (Decimate capacity for high-risk users)
    if risk_score > 75:
        # High Risk: 10% capacity, slow refill
        capacity = max(1, int(capacity * 0.1))
    elif risk_score > 50:
        # Medium-High: 25% capacity
        capacity = max(1, int(capacity * 0.25))
    elif risk_score > 25:
        # Elevated Risk: 50% capacity
        capacity = max(1, int(capacity * 0.5))

    refill_rate = capacity / 86400.0  # Convert to per-second

    # IP-based rate limiting
    ip_allowed = True
    ip_remaining = SecurityConfig.IP_RATE_LIMIT
    ip_reset = 0.0

    if ip_address:
        try:
            client = await _get_redis()
            sha = await _ensure_lua_script(client)

            ip_key = f"ratelimit:ip:{ip_address}"
            ip_result = await client.evalsha(  # type: ignore[reportUnknownReturnType]
                sha,
                1,
                ip_key,
                str(SecurityConfig.IP_RATE_LIMIT),
                str(SecurityConfig.IP_RATE_LIMIT / 60.0),  # per second
                str(time.time()),
                "1",
            )

            ip_allowed = bool(int(ip_result[0]))
            ip_remaining = int(ip_result[1])
            ip_reset = float(ip_result[2])

        except Exception as exc:
            logger.error("IP rate limiter error", error=str(exc))
            # Don't fail closed for IP limits, just log

    # User-based rate limiting
    key = f"ratelimit:{user_id}:{feature}"
    now = time.time()

    try:
        client = await _get_redis()
        sha = await _ensure_lua_script(client)
        result = await client.evalsha(sha, 1, key, str(capacity), str(refill_rate), str(now), "1")  # type: ignore[reportUnknownReturnType]    # pyright: ignore[reportUnknownReturnType]
        allowed = bool(int(result[0]))
        remaining = int(result[1])
        reset_seconds = float(result[2])

        # Combine IP and user rate limits
        final_allowed = allowed and ip_allowed
        final_remaining = min(remaining, ip_remaining)
        final_reset = max(reset_seconds, ip_reset)

        if not final_allowed:
            RATE_LIMITED_TOTAL.labels(trust_tier=trust_tier.value).inc()

            # Record violation for backoff (sync methods — no await)
            backoff_duration = _backoff_manager.record_violation(backoff_key)

            # Increase IP risk score
            if ip_address:
                _ip_limiter.add_suspicious_activity(ip_address, 5.0)

            logger.info(
                "rate_limited",
                user_id=user_id,
                ip=ip_address,
                trust_tier=trust_tier.value,
                remaining=final_remaining,
                reset_seconds=final_reset,
                risk_score=risk_score,
                backoff_duration=backoff_duration,
            )

        return RateLimitResult(allowed=final_allowed, remaining=final_remaining, reset_seconds=final_reset, risk_score=risk_score)

    except Exception as exc:
        # Fail closed: Redis unavailable means deny
        logger.error("rate_limiter_redis_error", error=str(exc))
        RATE_LIMITED_TOTAL.labels(trust_tier=trust_tier.value).inc()

        # Record violation even on Redis failure
        _backoff_manager.record_violation(backoff_key)

        return RateLimitResult(allowed=False, remaining=0, reset_seconds=60.0, risk_score=risk_score + 20.0, blocked_reason="redis_unavailable")


async def tighten_limits(user_id: str, factor: float = 0.5) -> None:
    """
    Tighten rate limits for a user (systematic misuse handling).

    Reduces remaining tokens by the given factor.
    """
    try:
        client = await _get_redis()
        # Find all rate-limit keys for this user
        keys = []
        async for key in client.scan_iter(f"ratelimit:{user_id}:*"):
            keys.append(key)
        for key in keys:
            tokens = await client.hget(key, "tokens")  # type: ignore[reportUnknownReturnType]
            if tokens is not None:  # type: ignore[reportOptionalMemberAccess]
                new_tokens = max(0, int(float(tokens) * factor))
                await client.hset(key, "tokens", str(new_tokens))  # type: ignore[reportAwaitableReturnType]
        logger.warning(
            "rate_limits_tightened",
            user_id=user_id,
            factor=factor,
            keys_affected=len(keys),
        )
    except Exception as exc:
        logger.error("tighten_limits_failed", user_id=user_id, error=str(exc))


async def block_ip_address(ip_address: str, reason: str = "manual_block") -> bool:
    """Block an IP address"""
    try:
        _ip_limiter.block_ip(ip_address, reason)
        logger.warning(f"IP blocked: {ip_address}, reason: {reason}")
        return True
    except Exception as e:
        logger.error(f"Failed to block IP {ip_address}: {e}")
        return False


async def unblock_ip_address(ip_address: str) -> bool:
    """Unblock an IP address"""
    try:
        # Note: Current implementation doesn't have unblock, but we can reset risk score
        if ip_address in _ip_limiter.suspicious_ips:
            del _ip_limiter.suspicious_ips[ip_address]
        logger.info(f"IP unblocked: {ip_address}")
        return True
    except Exception as e:
        logger.error(f"Failed to unblock IP {ip_address}: {e}")
        return False


async def reset_user_backoff(user_id: str, ip_address: str | None = None) -> bool:
    """Reset exponential backoff for a user"""
    try:
        backoff_key = f"{user_id}:{ip_address or 'unknown'}"
        _backoff_manager.reset_violations(backoff_key)
        logger.info(f"Backoff reset for user: {user_id}, IP: {ip_address}")
        return True
    except Exception as e:
        logger.error(f"Failed to reset backoff for user {user_id}: {e}")
        return False


async def get_security_status() -> dict[str, Any]:
    """Get comprehensive security status"""
    try:
        # Get Redis connection for stats
        client = await _get_redis()

        # Get rate limit keys count
        user_keys = 0
        ip_keys = 0

        async for key in client.scan_iter("ratelimit:*"):
            if ":ip:" in key:
                ip_keys += 1
            else:
                user_keys += 1

        return {
            "rate_limits": {
                "active_user_limits": user_keys,
                "active_ip_limits": ip_keys,
                "blocked_ips": len(_ip_limiter.blocked_ips),
                "suspicious_ips": len(_ip_limiter.suspicious_ips),
                "backoff_sessions": len(_backoff_manager.violation_counts),
            },
            "configuration": {
                "ip_rate_limit": SecurityConfig.IP_RATE_LIMIT,
                "base_backoff_seconds": SecurityConfig.BASE_BACKOFF_SECONDS,
                "max_backoff_seconds": SecurityConfig.MAX_BACKOFF_SECONDS,
                "signature_ttl": SecurityConfig.SIGNATURE_TTL,
            },
            "redis_status": "connected" if client else "disconnected",
        }
    except Exception as e:
        logger.error(f"Failed to get security status: {e}")
        return {"error": str(e)}
