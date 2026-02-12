"""
Wellness Studio - Rate Limiting & Abuse Prevention
Prevents API abuse, excessive requests, and ensures fair usage
"""
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading


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


@dataclass
class RateLimitStatus:
    """Current rate limit status"""
    allowed: bool
    remaining: int
    reset_time: datetime
    retry_after: Optional[int] = None
    limit: int = 0
    window: int = 0


class RateLimiter:
    """
    Rate limiter with multiple strategies and scopes
    Thread-safe implementation
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        self._storage: Dict[str, Dict] = {}
        self._lock = threading.RLock()
        self._violation_log: List[Dict] = []
    
    def _get_key(self, identifier: str, scope: Optional[RateLimitScope] = None) -> str:
        """Generate storage key based on scope"""
        scope = scope or self.config.scope
        return f"{scope.value}:{identifier}"
    
    def check_rate_limit(
        self, 
        identifier: str, 
        scope: Optional[RateLimitScope] = None
    ) -> RateLimitStatus:
        """
        Check if request is within rate limit
        
        Args:
            identifier: User ID, IP, or other identifier
            scope: Rate limit scope
            
        Returns:
            RateLimitStatus with current limit info
        """
        key = self._get_key(identifier, scope)
        now = datetime.now()
        
        with self._lock:
            if key not in self._storage:
                self._storage[key] = {
                    'requests': [],
                    'blocked_until': None,
                    'violation_count': 0
                }
            
            entry = self._storage[key]
            
            # Check if currently blocked
            if entry['blocked_until'] and now < entry['blocked_until']:
                retry_after = int((entry['blocked_until'] - now).total_seconds())
                return RateLimitStatus(
                    allowed=False,
                    remaining=0,
                    reset_time=entry['blocked_until'],
                    retry_after=retry_after,
                    limit=self.config.requests_per_window,
                    window=self.config.window_seconds
                )
            
            # Clean old requests based on strategy
            if self.config.strategy == RateLimitStrategy.SLIDING_WINDOW:
                cutoff = now - timedelta(seconds=self.config.window_seconds)
                entry['requests'] = [r for r in entry['requests'] if r > cutoff]
            
            # Check if limit exceeded
            current_count = len(entry['requests'])
            
            if current_count >= self.config.requests_per_window:
                # Block the identifier
                block_until = now + timedelta(seconds=self.config.block_duration_seconds)
                entry['blocked_until'] = block_until
                entry['violation_count'] += 1
                
                self._log_violation(identifier, scope, current_count)
                
                return RateLimitStatus(
                    allowed=False,
                    remaining=0,
                    reset_time=block_until,
                    retry_after=self.config.block_duration_seconds,
                    limit=self.config.requests_per_window,
                    window=self.config.window_seconds
                )
            
            # Calculate reset time
            if entry['requests']:
                oldest = min(entry['requests'])
                reset_time = oldest + timedelta(seconds=self.config.window_seconds)
            else:
                reset_time = now + timedelta(seconds=self.config.window_seconds)
            
            return RateLimitStatus(
                allowed=True,
                remaining=self.config.requests_per_window - current_count - 1,
                reset_time=reset_time,
                limit=self.config.requests_per_window,
                window=self.config.window_seconds
            )
    
    def record_request(
        self, 
        identifier: str, 
        scope: Optional[RateLimitScope] = None
    ) -> RateLimitStatus:
        """
        Record a request and return updated rate limit status
        
        Args:
            identifier: User ID, IP, or other identifier
            scope: Rate limit scope
            
        Returns:
            Updated RateLimitStatus
        """
        key = self._get_key(identifier, scope)
        now = datetime.now()
        
        with self._lock:
            if key not in self._storage:
                self._storage[key] = {
                    'requests': [],
                    'blocked_until': None,
                    'violation_count': 0
                }
            
            entry = self._storage[key]
            
            # Don't record if blocked
            if entry['blocked_until'] and now < entry['blocked_until']:
                return self.check_rate_limit(identifier, scope)
            
            # Record the request
            entry['requests'].append(now)
        
        return self.check_rate_limit(identifier, scope)
    
    def _log_violation(
        self, 
        identifier: str, 
        scope: Optional[RateLimitScope],
        request_count: int
    ):
        """Log rate limit violation"""
        self._violation_log.append({
            'timestamp': datetime.now().isoformat(),
            'identifier_hash': hash(identifier) % 10000,  # Anonymized
            'scope': scope.value if scope else self.config.scope.value,
            'request_count': request_count,
            'limit': self.config.requests_per_window,
            'window_seconds': self.config.window_seconds
        })
    
    def get_violations(
        self, 
        since: Optional[datetime] = None
    ) -> List[Dict]:
        """Get rate limit violations"""
        if since is None:
            return self._violation_log
        
        return [
            v for v in self._violation_log
            if datetime.fromisoformat(v['timestamp']) >= since
        ]
    
    def reset(self, identifier: str, scope: Optional[RateLimitScope] = None):
        """Reset rate limit for an identifier"""
        key = self._get_key(identifier, scope)
        with self._lock:
            if key in self._storage:
                del self._storage[key]
    
    def get_stats(self, identifier: Optional[str] = None) -> Dict[str, Any]:
        """Get rate limiting statistics"""
        with self._lock:
            if identifier:
                key = self._get_key(identifier)
                if key not in self._storage:
                    return {}
                entry = self._storage[key]
                return {
                    'request_count': len(entry.get('requests', [])),
                    'violation_count': entry.get('violation_count', 0),
                    'is_blocked': entry.get('blocked_until') is not None
                }
            
            return {
                'total_tracked': len(self._storage),
                'total_violations': len(self._violation_log),
                'recent_violations': len([
                    v for v in self._violation_log
                    if datetime.now() - datetime.fromisoformat(v['timestamp']) < timedelta(hours=24)
                ])
            }


class AbusePrevention:
    """
    Advanced abuse prevention with pattern detection
    """
    
    def __init__(self):
        self.pattern_history: Dict[str, List[datetime]] = {}
        self.suspicious_patterns: List[Dict] = []
        self._lock = threading.RLock()
    
    def analyze_request_pattern(
        self, 
        identifier: str, 
        request_type: str,
        content_fingerprint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze request for suspicious patterns
        
        Returns:
            Analysis results with threat assessment
        """
        now = datetime.now()
        key = f"{identifier}:{request_type}"
        
        with self._lock:
            if key not in self.pattern_history:
                self.pattern_history[key] = []
            
            self.pattern_history[key].append(now)
            
            # Clean old entries (keep last hour)
            cutoff = now - timedelta(hours=1)
            self.pattern_history[key] = [
                t for t in self.pattern_history[key] if t > cutoff
            ]
            
            recent_count = len(self.pattern_history[key])
        
        # Detect patterns
        threats = []
        
        # Rapid fire detection
        if recent_count > 60:  # More than 1 per minute average
            threats.append({
                'type': 'rapid_fire',
                'severity': 'medium',
                'count': recent_count
            })
        
        # Burst detection
        if len(self.pattern_history[key]) >= 10:
            recent = self.pattern_history[key][-10:]
            time_span = (recent[-1] - recent[0]).total_seconds()
            if time_span < 10:  # 10 requests in 10 seconds
                threats.append({
                    'type': 'burst_attack',
                    'severity': 'high',
                    'rate': 10 / max(time_span, 0.1)
                })
        
        # Repetitive content detection (if fingerprint provided)
        if content_fingerprint:
            # Would compare with previous fingerprints
            pass
        
        return {
            'identifier_anonymized': hash(identifier) % 10000,
            'request_type': request_type,
            'recent_requests': recent_count,
            'threats_detected': len(threats),
            'threats': threats,
            'is_suspicious': len(threats) > 0
        }
    
    def flag_suspicious_activity(
        self, 
        identifier: str, 
        reason: str,
        details: Dict
    ):
        """Flag activity as suspicious"""
        self.suspicious_patterns.append({
            'timestamp': datetime.now().isoformat(),
            'identifier_hash': hash(identifier) % 10000,
            'reason': reason,
            'details': details
        })
    
    def get_threat_assessment(self) -> Dict[str, Any]:
        """Get overall threat assessment"""
        recent_flags = [
            f for f in self.suspicious_patterns
            if datetime.now() - datetime.fromisoformat(f['timestamp']) < timedelta(hours=24)
        ]
        
        return {
            'total_suspicious_activities': len(self.suspicious_patterns),
            'recent_flags': len(recent_flags),
            'threat_level': 'high' if len(recent_flags) > 10 else 'medium' if len(recent_flags) > 5 else 'low',
            'requires_investigation': len(recent_flags) > 5
        }


class ResourceQuotaManager:
    """
    Manages resource quotas and limits
    """
    
    def __init__(self):
        self.quotas: Dict[str, Dict] = {}
        self._lock = threading.RLock()
    
    def set_quota(
        self, 
        identifier: str, 
        daily_limit: int,
        monthly_limit: int
    ):
        """Set quota for an identifier"""
        with self._lock:
            self.quotas[identifier] = {
                'daily_limit': daily_limit,
                'monthly_limit': monthly_limit,
                'daily_used': 0,
                'monthly_used': 0,
                'last_reset': datetime.now()
            }
    
    def check_quota(self, identifier: str) -> Dict[str, Any]:
        """Check current quota status"""
        with self._lock:
            if identifier not in self.quotas:
                return {'has_quota': False}
            
            quota = self.quotas[identifier]
            
            # Check if need to reset daily
            last_reset = quota['last_reset']
            now = datetime.now()
            if last_reset.date() != now.date():
                quota['daily_used'] = 0
                quota['last_reset'] = now
            
            return {
                'has_quota': True,
                'daily_remaining': quota['daily_limit'] - quota['daily_used'],
                'monthly_remaining': quota['monthly_limit'] - quota['monthly_used'],
                'daily_limit': quota['daily_limit'],
                'monthly_limit': quota['monthly_limit'],
                'within_quota': (
                    quota['daily_used'] < quota['daily_limit'] and
                    quota['monthly_used'] < quota['monthly_limit']
                )
            }
    
    def consume_quota(self, identifier: str, amount: int = 1) -> bool:
        """Consume quota, returns True if successful"""
        with self._lock:
            if identifier not in self.quotas:
                return False
            
            quota = self.quotas[identifier]
            status = self.check_quota(identifier)
            
            if not status['within_quota']:
                return False
            
            quota['daily_used'] += amount
            quota['monthly_used'] += amount
            return True


class CircuitBreaker:
    """
    Circuit breaker pattern for fault tolerance
    """
    
    def __init__(
        self, 
        failure_threshold: int = 5,
        recovery_timeout: int = 30
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count: Dict[str, int] = {}
        self.last_failure: Dict[str, datetime] = {}
        self.state: Dict[str, str] = {}  # 'closed', 'open', 'half-open'
        self._lock = threading.RLock()
    
    def can_execute(self, service: str) -> bool:
        """Check if service can be called"""
        with self._lock:
            if service not in self.state:
                self.state[service] = 'closed'
                return True
            
            if self.state[service] == 'closed':
                return True
            
            if self.state[service] == 'open':
                # Check if recovery timeout passed
                last_fail = self.last_failure.get(service)
                if last_fail:
                    elapsed = (datetime.now() - last_fail).total_seconds()
                    if elapsed > self.recovery_timeout:
                        self.state[service] = 'half-open'
                        return True
                return False
            
            return True  # half-open
    
    def record_success(self, service: str):
        """Record successful execution"""
        with self._lock:
            self.failure_count[service] = 0
            self.state[service] = 'closed'
    
    def record_failure(self, service: str):
        """Record failed execution"""
        with self._lock:
            self.failure_count[service] = self.failure_count.get(service, 0) + 1
            self.last_failure[service] = datetime.now()
            
            if self.failure_count[service] >= self.failure_threshold:
                self.state[service] = 'open'
    
    def get_status(self, service: str) -> Dict[str, Any]:
        """Get circuit breaker status"""
        with self._lock:
            return {
                'state': self.state.get(service, 'closed'),
                'failure_count': self.failure_count.get(service, 0),
                'threshold': self.failure_threshold
            }
