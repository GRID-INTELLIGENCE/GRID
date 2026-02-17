"""
XAI Performance Optimization for GRID
Provides caching, load balancing, and adaptive processing capabilities.
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Single cache entry."""

    key: str
    value: Any
    created_at: datetime
    expires_at: datetime
    hit_count: int = 0
    size_bytes: int = 0

    def is_expired(self) -> bool:
        return datetime.now() >= self.expires_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "hit_count": self.hit_count,
            "size_bytes": self.size_bytes,
            "is_expired": self.is_expired(),
        }


@dataclass
class LoadBalancingMetrics:
    """Metrics for load balancing decisions."""

    server_id: str
    load_score: float
    active_tasks: int
    response_times: list[float] = field(default_factory=list)
    capacity: int = 0
    last_updated: datetime = field(default_factory=datetime.now)

    def update_load(self, new_load: float, response_time: float) -> None:
        """Update load metrics."""
        self.response_times.append(response_time)
        # Keep only last 100 response times
        if len(self.response_times) > 100:
            self.response_times = self.response_times[-100:]

        # Calculate exponential moving average
        alpha = 0.1
        self.load_score = alpha * new_load + (1 - alpha) * self.load_score
        self.active_tasks = max(0, self.active_tasks - 1)
        self.last_updated = datetime.now()

    def get_average_response_time(self) -> float:
        """Get average response time."""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)

    def get_load_factor(self) -> float:
        """Get load factor for capacity calculation."""
        if self.capacity == 0:
            return 1.0
        return self.load_score / self.capacity


class XAICache:
    """
    High-performance cache for XAI operations.
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl_seconds: int = 3600,  # 1 hour
        max_memory_mb: int = 512,
    ):
        self.max_size = max_size
        self.default_ttl = timedelta(seconds=default_ttl_seconds)
        self.max_memory_mb = max_memory_mb
        self.cache: dict[str, CacheEntry] = {}
        self.memory_usage_mb = 0.0
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def _generate_key(self, prefix: str, **kwargs: Any) -> str:
        """Generate cache key from parameters."""
        key_data = json.dumps(kwargs, sort_keys=True, default=str)
        return f"{prefix}:{hashlib.md5(key_data.encode()).hexdigest()}"  # noqa: S324 non-cryptographic use

    def _estimate_size(self, value: Any) -> int:
        """Estimate memory size of a value."""
        return len(json.dumps(value, default=str).encode())

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        entry = self.cache.get(key)

        if entry is None:
            self.misses += 1
            return None

        if entry.is_expired():
            del self.cache[key]
            self.misses += 1
            return None

        # Update hit statistics
        entry.hit_count += 1
        self.hits += 1

        return entry.value

    async def put(self, key: str, value: Any, ttl: timedelta | None = None, priority: int = 0) -> bool:
        """Put value in cache."""
        # Check memory constraints
        new_entry_size = self._estimate_size(value)
        current_size = sum(entry.size_bytes for entry in self.cache.values())

        if current_size + new_entry_size > (self.max_memory_mb * 1024 * 1024):
            # Try to evict expired entries first
            expired_keys = [k for k, v in self.cache.items() if v.is_expired()]

            for k in expired_keys:
                v = self.cache[k]
                del self.cache[k]
                self.evictions += 1
                current_size -= self._estimate_size(v.value)

            if current_size + new_entry_size > (self.max_memory_mb * 1024 * 1024):
                # Still not enough space, evict least recently used
                sorted_entries = sorted(self.cache.items(), key=lambda item: item[1].created_at)

                # Evict entries until space is available
                for k, v in sorted_entries:
                    del self.cache[k]
                    current_size -= v.size_bytes
                    self.evictions += 1
                    if current_size + new_entry_size <= (self.max_memory_mb * 1024 * 1024):
                        break

        # Check cache size limit
        if len(self.cache) >= self.max_size:
            # Evict oldest entries
            sorted_entries = sorted(self.cache.items(), key=lambda item: item[1].created_at)

            evict_count = len(self.cache) - self.max_size + 1
            for i in range(evict_count):
                k, v = sorted_entries[i]
                del self.cache[k]
                self.evictions += 1

        ttl = ttl or self.default_ttl

        entry = CacheEntry(
            key=key, value=value, created_at=datetime.now(), expires_at=datetime.now() + ttl, size_bytes=new_entry_size
        )

        self.cache[key] = entry
        self.memory_usage_mb = sum(entry.size_bytes for entry in self.cache.values()) / (1024 * 1024)

        return True

    def get_stats(self) -> dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0.0

        return {
            "cache_size": len(self.cache),
            "max_size": self.max_size,
            "memory_usage_mb": self.memory_usage_mb,
            "max_memory_mb": self.max_memory_mb,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "evictions": self.evictions,
            "total_requests": total_requests,
        }


class XAILoadBalancer:
    """
    Load balancer for distributing XAI requests across multiple servers/instances.
    """

    def __init__(self):
        self.servers: dict[str, LoadBalancingMetrics] = {}
        self.current_round_robin = 0
        self.health_checks: dict[str, datetime] = {}

    def add_server(self, server_id: str, capacity: int = 100) -> None:
        """Add a server to the load balancer."""
        self.servers[server_id] = LoadBalancingMetrics(
            server_id=server_id, load_score=0.0, active_tasks=0, capacity=capacity, last_updated=datetime.now()
        )

        self.health_checks[server_id] = datetime.now()

    def update_server_health(self, server_id: str, is_healthy: bool) -> None:
        """Update server health status."""
        if server_id in self.servers:
            if is_healthy:
                self.health_checks[server_id] = datetime.now()
            self.servers[server_id].last_updated = datetime.now()

    def select_server(self, task_priority: int = 0) -> str | None:
        """Select best server for a task."""
        if not self.servers:
            return None

        # Filter healthy servers
        healthy_servers = {
            server_id: metrics
            for server_id, metrics in self.servers.items()
            if server_id in self.health_checks or (datetime.now() - self.health_checks[server_id]).total_seconds() < 300
        }

        if not healthy_servers:
            return None

        # Different selection strategies based on priority
        if task_priority > 7:  # High priority
            # Select server with lowest load
            return min(healthy_servers.items(), key=lambda item: item[1].get_load_factor())[0]
        else:  # Normal priority
            # Use round-robin for normal priority
            available_servers = list(healthy_servers.keys())
            if not available_servers:
                return None

            server = available_servers[self.current_round_robin % len(available_servers)]
            self.current_round_robin = (self.current_round_robin + 1) % len(available_servers)
            return server

    def update_server_load(self, server_id: str, response_time: float, task_complexity: float = 1.0) -> None:
        """Update server load metrics."""
        if server_id in self.servers:
            self.servers[server_id].update_load(response_time, task_complexity)

    def get_server_status(self) -> dict[str, Any]:
        """Get load balancing status."""
        return {
            "total_servers": len(self.servers),
            "healthy_servers": len(
                [
                    server_id
                    for server_id, check_time in self.health_checks.items()
                    if (datetime.now() - check_time).total_seconds() < 300
                ]
            ),
            "servers": {
                server_id: {
                    "load_score": metrics.load_score,
                    "active_tasks": metrics.active_tasks,
                    "capacity": metrics.capacity,
                    "load_factor": metrics.get_load_factor(),
                    "average_response_time": metrics.get_average_response_time(),
                    "last_updated": metrics.last_updated.isoformat(),
                    "is_healthy": server_id in self.health_checks
                    and (datetime.now() - self.health_checks[server_id]).total_seconds() < 300,
                }
                for server_id, metrics in self.servers.items()
            },
        }


class XAIAdaptiveProcessor:
    """
    Adaptive processing that adjusts behavior based on system load and performance.
    """

    def __init__(self):
        self.current_load = 0.5  # 0.0 to 1.0
        self.performance_history: list[float] = []
        self.adaptation_threshold = 0.8  # Trigger adaptation at 80% load
        self.processing_mode = "normal"  # fast, normal, thorough

    def update_load(self, new_load: float) -> None:
        """Update current system load."""
        alpha = 0.1  # Smoothing factor
        self.current_load = alpha * new_load + (1 - alpha) * self.current_load

    def record_performance(self, response_time: float) -> None:
        """Record performance metrics."""
        self.performance_history.append(response_time)
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]

    def get_adaptive_config(self) -> dict[str, Any]:
        """Get adaptive processing configuration."""
        avg_performance = (
            sum(self.performance_history) / len(self.performance_history) if self.performance_history else 0.0
        )

        # Adjust processing mode based on load and performance
        if self.current_load > self.adaptation_threshold:
            self.processing_mode = "fast"
            config = {
                "processing_mode": self.processing_mode,
                "batch_size": 32,  # Smaller batches for fast mode
                "timeout_seconds": 10,  # Shorter timeouts
                "retry_attempts": 2,
                "priority_boost": 1.5,  # Boost priority for fast completion
            }
        elif avg_performance > 2.0:  # Slow average response time
            self.processing_mode = "thorough"
            config = {
                "processing_mode": self.processing_mode,
                "batch_size": 128,  # Larger batches for thorough analysis
                "timeout_seconds": 60,  # Longer timeouts
                "retry_attempts": 5,
                "priority_boost": 0.5,  # Lower priority for resource conservation
            }
        else:
            config = {
                "processing_mode": self.processing_mode,
                "batch_size": 64,
                "timeout_seconds": 30,
                "retry_attempts": 3,
                "priority_boost": 1.0,
            }

        return {
            "current_load": self.current_load,
            "average_performance": avg_performance,
            "adaptation_threshold": self.adaptation_threshold,
            "processing_mode": self.processing_mode,
            "config": config,
        }


# Global instances for convenience
cache = XAICache()
load_balancer = XAILoadBalancer()
adaptive_processor = XAIAdaptiveProcessor()
