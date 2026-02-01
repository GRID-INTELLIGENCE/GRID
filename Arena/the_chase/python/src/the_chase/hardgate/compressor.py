"""
Compressor guardian for rate limiting
"""
import threading
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class RateLimitScope(Enum):
    """Scope of rate limiting"""
    GLOBAL = "global"
    USER = "user"
    IP = "ip"
    SESSION = "session"
    RESOURCE = "resource"

class RateLimitStrategy(Enum):
    """Rate limiting strategies"""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    requests_per_window: int = 100
    window_seconds: int = 60
    block_duration_seconds: int = 300
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    scope: RateLimitScope = RateLimitScope.USER

class Compressor:
    """Rate limiting guardian (enhanced with Wellness Studio RateLimiter)"""
    def __init__(self, config: RateLimitConfig):
        self.limiter = RateLimiter(config)  # Reuse Wellness Studio implementation
        self.strategy = config.strategy

    def check_rate_limit(self, identifier: str, scope: RateLimitScope | None = None) -> Any:
        return self.limiter.check_rate_limit(identifier, scope)

class RateLimiter:
    """
    Rate limiter with multiple strategies and scopes
    Thread-safe implementation
    """

    def __init__(self, config: RateLimitConfig | None = None):
        self.config = config or RateLimitConfig()
        self._storage: dict[str, dict] = {}
        self._lock = threading.RLock()
        self._violation_log: list[dict] = []

    def _get_key(self, identifier: str, scope: RateLimitScope | None = None) -> str:
        """Generate storage key based on scope"""
        scope = scope or self.config.scope
        return f"{scope.value}:{identifier}"

    def check_rate_limit(self, identifier: str, scope: RateLimitScope | None = None) -> dict[str, Any]:
        """Check if request is within rate limit"""
        key = self._get_key(identifier, scope)
        current_time = datetime.now().timestamp()

        if key not in self._storage:
            self._storage[key] = {
                'count': 0,
                'window_start': current_time
            }

        storage = self._storage[key]
        elapsed = current_time - storage['window_start']

        if elapsed > self.config.window_seconds:
            storage['count'] = 0
            storage['window_start'] = current_time

        if storage['count'] < self.config.requests_per_window:
            storage['count'] += 1
            return {
                'allowed': True,
                'remaining': self.config.requests_per_window - storage['count'],
                'reset_at': storage['window_start'] + self.config.window_seconds
            }
        else:
            self._log_violation(key, 'rate_limit_exceeded')
            return {
                'allowed': False,
                'remaining': 0,
                'reset_at': storage['window_start'] + self.config.window_seconds
            }

    def _log_violation(self, key: str, reason: str):
        """Log a rate limit violation"""
        self._violation_log.append({
            'key': key,
            'reason': reason,
            'timestamp': datetime.now().timestamp()
        })
