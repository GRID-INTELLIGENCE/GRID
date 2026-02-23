"""
Cache layer for The Chase - Multi-level cache with ADSR-inspired sustain/decay semantics.

ADSR MAPPING:
- Attack: Initial priority assignment (0.0 → peak)
- Decay: Priority reduction for penalized entries (peak → sustain)
- Sustain: Maintained priority during activity (constant level)
- Release: TTL expiration and removal (fade to zero)
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RewardLevel(Enum):
    """Reward levels for behavioral contrast."""

    NEUTRAL = "neutral"
    ACKNOWLEDGED = "acknowledged"
    REWARDED = "rewarded"
    PROMOTED = "promoted"


class PenaltyLevel(Enum):
    """Penalty levels for behavioral contrast."""

    NONE = "none"
    WARNED = "warned"
    FINED = "fined"
    SUSPENDED = "suspended"
    BANNED = "banned"


@dataclass
class CacheMeta:
    """Metadata for cache entries with ADSR-inspired tracking."""

    priority: float = 0.5
    ttl_seconds: float = 60.0
    soft_ttl_seconds: float = 30.0
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    reward_level: RewardLevel = RewardLevel.NEUTRAL
    penalty_level: PenaltyLevel = PenaltyLevel.NONE
    sustain_time: float = 0.0  # Explicit sustain phase duration
    decay_rate: float = 0.0  # Priority decay rate (0 = no decay during sustain)

    def is_expired(self) -> bool:
        """Check if hard TTL has expired."""
        return time.time() > self.created_at + self.ttl_seconds

    def is_soft_expired(self) -> bool:
        """Check if soft TTL has expired (sustain phase complete)."""
        return time.time() > self.created_at + self.soft_ttl_seconds

    def time_in_sustain(self) -> float:
        """Calculate time spent in sustain phase."""
        soft_expired = self.created_at + self.soft_ttl_seconds
        if time.time() <= soft_expired:
            return 0.0
        return time.time() - soft_expired


class CacheEntry:
    """Wrapper for cache entries to provide .meta and .value access."""

    def __init__(self, value: Any, meta: CacheMeta):
        self.value = value
        self.meta = meta


class MemoryTier:
    """Memory tier with capacity limits and ADSR sustain/decay support."""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._store: dict[str, dict[str, Any]] = {}
        self._access_order: list[str] = []

    @property
    def priority_boost(self) -> dict[RewardLevel, float]:
        """Priority boost per reward level."""
        return {
            RewardLevel.NEUTRAL: 0.0,
            RewardLevel.ACKNOWLEDGED: 0.1,
            RewardLevel.REWARDED: 0.2,
            RewardLevel.PROMOTED: 0.3,
        }

    @property
    def ttl_multiplier(self) -> dict[RewardLevel, float]:
        """TTL extension multiplier per reward level."""
        return {
            RewardLevel.NEUTRAL: 1.0,
            RewardLevel.ACKNOWLEDGED: 1.2,
            RewardLevel.REWARDED: 1.35,
            RewardLevel.PROMOTED: 1.5,
        }

    @property
    def penalty_reduction(self) -> dict[PenaltyLevel, float]:
        """Priority reduction per penalty level."""
        return {
            PenaltyLevel.NONE: 0.0,
            PenaltyLevel.WARNED: 0.1,
            PenaltyLevel.FINED: 0.3,
            PenaltyLevel.SUSPENDED: 0.5,
            PenaltyLevel.BANNED: 0.5,
        }

    @property
    def ttl_penalty_multiplier(self) -> dict[PenaltyLevel, float]:
        """TTL reduction multiplier per penalty level (smaller = faster decay)."""
        return {
            PenaltyLevel.NONE: 1.0,
            PenaltyLevel.WARNED: 0.8,
            PenaltyLevel.FINED: 0.5,
            PenaltyLevel.SUSPENDED: 0.5,
            PenaltyLevel.BANNED: 0.5,
        }

    def get(self, key: str) -> CacheEntry | None:
        """Get entry as CacheEntry wrapper. Returns None if expired or not found."""
        if key not in self._store:
            return None
        entry = self._store[key]
        meta = entry["meta"]
        if meta.is_expired():
            del self._store[key]
            if key in self._access_order:
                self._access_order.remove(key)
            return None
        meta.last_accessed = time.time()
        self._update_access_order(key)
        return CacheEntry(entry["value"], meta)

    def _update_access_order(self, key: str) -> None:
        """Update access order for LRU eviction."""
        if key in self._access_order:
            self._access_order.remove(key)
            self._access_order.append(key)

    def _evict_lru(self) -> None:
        """Evict least recently used item."""
        if self._access_order:
            key = self._access_order.pop(0)
            del self._store[key]

    def _apply_reward_boost(self, meta: CacheMeta) -> CacheMeta:
        """Apply priority boost based on reward level."""
        boost = self.priority_boost.get(meta.reward_level, 0.0)
        meta.priority = min(1.0, meta.priority + boost)
        return meta

    def _apply_ttl_extension(self, meta: CacheMeta) -> CacheMeta:
        """Extend TTL based on reward level."""
        multiplier = self.ttl_multiplier.get(meta.reward_level, 1.0)
        meta.ttl_seconds *= multiplier
        meta.soft_ttl_seconds *= multiplier
        return meta

    def _apply_penalty_reduction(self, meta: CacheMeta) -> CacheMeta:
        """Apply priority reduction and TTL reduction based on penalty level."""
        reduction = self.penalty_reduction.get(meta.penalty_level, 0.0)
        meta.priority = max(0.0, meta.priority - reduction)
        multiplier = self.ttl_penalty_multiplier.get(meta.penalty_level, 1.0)
        meta.ttl_seconds *= multiplier
        meta.soft_ttl_seconds *= multiplier
        return meta

    def apply_metadata_modifiers(self, meta: CacheMeta) -> CacheMeta:
        """Public method to apply reward boosts and penalty reductions to metadata."""
        meta = self._apply_reward_boost(meta)
        meta = self._apply_ttl_extension(meta)
        meta = self._apply_penalty_reduction(meta)
        return meta

    def store_entry(self, key: str, entry: dict[str, Any]) -> None:
        """Public method to store an entry."""
        self._store[key] = entry
        self._access_order.append(key)
        if len(self._store) > self.max_size:
            self._evict_lru()

    def clear_store(self) -> None:
        """Public method to clear internal storage."""
        self._store.clear()
        self._access_order.clear()

    def store_size(self) -> int:
        """Public method to get store size."""
        return len(self._store)


class CacheLayer:
    """Multi-level cache layer for The Chase with ADSR semantics."""

    def __init__(self, mem: MemoryTier | None = None, max_size: int = 1000):
        self.mem = mem or MemoryTier(max_size=max_size)
        self.l1: dict[str, Any] = {}
        self.l2: dict[str, Any] = {}

    def keys(self) -> list[str]:
        """Return keys in L1 cache."""
        return []

    def __contains__(self, key: str) -> bool:
        return key in self.l1

    def __setitem__(self, key: str, value: Any) -> None:
        if key in self.l1:
            self.l1[key] = value
        else:
            if len(self.l1) >= self.mem.max_size:
                self._evict_lru()
            self.l1[key] = value

    def __getitem__(self, key: str) -> Any:
        if key in self.l1:
            return self.l1[key]
        return None

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: float = 60.0,
        priority: float = 0.5,
        reward_level: str | RewardLevel | None = "neutral",
        soft_ttl_seconds: float | None = None,
        penalty_level: str | PenaltyLevel | None = "none",
        decay_rate: float = 0.0,
    ) -> None:
        """
        Set cache entry with metadata.

        Args:
            key: Cache key
            value: Cached value
            ttl_seconds: Hard TTL (decay/release phase duration)
            priority: Initial priority (ADSR amplitude)
            reward_level: Reward level for priority boost
            soft_ttl_seconds: Soft TTL (sustain phase duration), defaults to half of ttl_seconds
            penalty_level: Penalty level for priority reduction
            decay_rate: Priority decay rate during sustain (0 = no decay)
        """
        if reward_level is None:
            resolved_reward = RewardLevel.NEUTRAL
        elif isinstance(reward_level, RewardLevel):
            resolved_reward = reward_level
        else:
            resolved_reward = RewardLevel(reward_level)

        if penalty_level is None:
            resolved_penalty = PenaltyLevel.NONE
        elif isinstance(penalty_level, PenaltyLevel):
            resolved_penalty = penalty_level
        else:
            resolved_penalty = PenaltyLevel(penalty_level)

        meta = CacheMeta(
            priority=priority,
            ttl_seconds=ttl_seconds,
            soft_ttl_seconds=soft_ttl_seconds or (ttl_seconds / 2),
            reward_level=resolved_reward,
            penalty_level=resolved_penalty,
            decay_rate=decay_rate,
        )
        meta = self.mem.apply_metadata_modifiers(meta)

        entry: dict[str, Any] = {"value": value, "meta": meta}
        self.mem.store_entry(key, entry)

    def get(self, key: str) -> "CacheEntry | None":
        """Get entry with metadata."""
        return self.mem.get(key)

    def _evict_lru(self) -> None:
        """Evict least recently used item."""
        if self.l1:
            key = next(iter(self.l1))
            del self.l1[key]

    def clear(self) -> None:
        """Clear all cache levels."""
        self.l1.clear()
        self.l2.clear()
        self.mem.clear_store()

    def size(self) -> int:
        """Return total cache size."""
        return len(self.l1) + len(self.l2) + self.mem.store_size()
