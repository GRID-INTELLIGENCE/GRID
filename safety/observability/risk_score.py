"""
Project GUARDIAN: Risk Score Manager.
Tracks user risk based on historical safety violations in Redis.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from safety.observability.security_monitoring import (
    SecurityEvent,
    SecurityEventSeverity,
)
from safety.workers.worker_utils import get_redis

logger = logging.getLogger(__name__)

class RiskScoreManager:
    """Manages dynamic user risk scores in Redis."""

    # Redis Keys
    # risk:score:{user_id} -> float current score
    # risk:last_update:{user_id} -> timestamp of last decay

    DECAY_RATE = 0.1  # Score decreases by 0.1 per hour of inactive/clean behavior
    MAX_SCORE = 1.0
    MIN_SCORE = 0.0

    SEVERITY_WEIGHTS = {
        SecurityEventSeverity.LOW: 0.05,
        SecurityEventSeverity.MEDIUM: 0.15,
        SecurityEventSeverity.HIGH: 0.4,
        SecurityEventSeverity.CRITICAL: 1.0
    }

    async def record_violation(self, event: SecurityEvent):
        """Update risk score based on a new violation."""
        if not event.user_id or event.user_id == "system":
            return

        weight = self.SEVERITY_WEIGHTS.get(event.severity, 0.05)
        
        try:
            client = await get_redis()
            if not client:
                return

            # 1. Decay the existing score first
            current_score = await self.get_score(event.user_id)
            
            # 2. Add current violation
            new_score = min(self.MAX_SCORE, current_score + weight)
            
            # 3. Save to Redis
            key = f"risk:score:{event.user_id}"
            await client.set(key, new_score)
            await client.set(f"risk:last_update:{event.user_id}", time.time())
            
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
            hours_passed = (time.time() - last_update) / 3600.0
            decay_amount = hours_passed * self.DECAY_RATE
            
            final_score = max(self.MIN_SCORE, score - decay_amount)
            return final_score
            
        except Exception as e:
            logger.error(f"Failed to get risk score: {e}")
            return self.MIN_SCORE

# Global Singleton
risk_manager = RiskScoreManager()
