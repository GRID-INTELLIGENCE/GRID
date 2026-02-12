import asyncio
import logging
import time
from typing import Optional

from safety.observability.security_monitoring import (
    SecurityEvent,
    SecurityEventSeverity,
)
from safety.workers.worker_utils import get_redis

logger = logging.getLogger(__name__)

# Lua script for atomic risk score updates: decay + increment
RISK_UPDATE_LUA = """
local score_key = KEYS[1]
local last_update_key = KEYS[2]
local weight = tonumber(ARGV[1])
local decay_rate = tonumber(ARGV[2])
local max_score = tonumber(ARGV[3])
local min_score = tonumber(ARGV[4])
local now = tonumber(ARGV[5])

local raw_score = redis.call('GET', score_key)
local score = tonumber(raw_score or "0")
local raw_last = redis.call('GET', last_update_key)
local last_update = tonumber(raw_last or tostring(now))

-- Apply decay
local hours_passed = math.max(0, (now - last_update) / 3600.0)
local decay_amount = hours_passed * decay_rate
score = math.max(min_score, score - decay_amount)

-- Add violation weight
local new_score = math.min(max_score, score + weight)

-- Save back
redis.call('SET', score_key, tostring(new_score))
redis.call('SET', last_update_key, tostring(now))

return tostring(new_score)
"""


class RiskScoreManager:
    """Manages dynamic user risk scores in Redis."""

    DECAY_RATE = 0.1  # Score decreases by 0.1 per hour of inactive/clean behavior
    MAX_SCORE = 1.0
    MIN_SCORE = 0.0

    SEVERITY_WEIGHTS = {
        SecurityEventSeverity.LOW: 0.05,
        SecurityEventSeverity.MEDIUM: 0.15,
        SecurityEventSeverity.HIGH: 0.4,
        SecurityEventSeverity.CRITICAL: 1.0,
    }

    def __init__(self):
        self._lua_sha: Optional[str] = None
        self._lua_lock = asyncio.Lock()

    async def _ensure_lua_script(self, client) -> str:
        if self._lua_sha is None:
            async with self._lua_lock:
                if self._lua_sha is None:
                    self._lua_sha = await client.script_load(RISK_UPDATE_LUA)
        return self._lua_sha or ""

    async def record_violation(self, event: SecurityEvent):
        """Update risk score based on a new violation."""
        if not event.user_id or event.user_id == "system":
            return

        weight = self.SEVERITY_WEIGHTS.get(event.severity, 0.05)

        try:
            client = await get_redis()
            if not client:
                return

            sha = await self._ensure_lua_script(client)

            score_key = f"risk:score:{event.user_id}"
            last_key = f"risk:last_update:{event.user_id}"

            # Atomic update via Lua
            new_score_raw = await client.evalsha(  # type: ignore[misc]
                sha or "",
                2,
                score_key,
                last_key,
                str(weight),
                str(self.DECAY_RATE),
                str(self.MAX_SCORE),
                str(self.MIN_SCORE),
                str(time.time()),
            )

            new_score = float(new_score_raw)
            logger.info(f"Updated risk score for {event.user_id}: {new_score:.2f} (+{weight})")

        except Exception as e:
            logger.error(f"Failed to record risk violation: {e}")

    async def get_score(self, user_id: str) -> float:
        """Get the current decayed risk score for a user."""
        try:
            client = await get_redis()
            if not client:
                return self.MIN_SCORE

            key = f"risk:score:{user_id}"
            last_key = f"risk:last_update:{user_id}"

            raw_score = await client.get(key)
            raw_last = await client.get(last_key)

            if raw_score is None:
                return self.MIN_SCORE

            score = float(raw_score)
            last_update = float(raw_last or time.time())

            # Application of decay
            hours_passed = max(0.0, (time.time() - last_update) / 3600.0)
            decay_amount = hours_passed * self.DECAY_RATE

            final_score = max(self.MIN_SCORE, score - decay_amount)
            return final_score

        except Exception as e:
            logger.error(f"Failed to get risk score: {e}")
            return self.MIN_SCORE


# Global Singleton
risk_manager = RiskScoreManager()
