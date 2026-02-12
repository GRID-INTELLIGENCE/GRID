"""
Adaptive Percentile-Based Routing Engine.

Extends the existing ``CognitiveRouter`` with realtime percentile-based
tier classification.  Maintains a sliding window of recent request
complexity scores so that tier boundaries self-adapt to actual
workload characteristics rather than relying on static thresholds.

Processing tiers:

    * **fast**     — p0–p50: simple lookups, cached, low-token queries
    * **standard** — p50–p85: typical RAG queries, skill invocations
    * **deep**     — p85–p95: multi-hop reasoning, knowledge graph traversal
    * **expert**   — p95–p100: complex orchestration, cross-model fusion

Usage:
    from cognitive.adaptive_router import AdaptiveRouter, RoutingSignal

    router = AdaptiveRouter()
    signal = RoutingSignal.from_query("Compare X and Y step by step")
    decision = router.route(signal)
    # decision.strategy.tier == ProcessingTier.DEEP
"""

from __future__ import annotations

import logging
import math
import statistics
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# =============================================================================
# Enums & Constants
# =============================================================================


class ProcessingTier(str, Enum):
    """Processing tiers mapped to percentile ranges."""

    FAST = "fast"          # p0–p50
    STANDARD = "standard"  # p50–p85
    DEEP = "deep"          # p85–p95
    EXPERT = "expert"      # p95–p100


@dataclass(frozen=True)
class TierThresholds:
    """Percentile boundaries for tier classification."""

    fast_upper: float = 50.0
    standard_upper: float = 85.0
    deep_upper: float = 95.0
    # Everything above deep_upper is EXPERT


DEFAULT_THRESHOLDS = TierThresholds()


# =============================================================================
# Routing Signal
# =============================================================================


@dataclass
class RoutingSignal:
    """
    Input signal vector for routing decisions.

    Each field contributes to a composite complexity score that
    determines the processing tier.

    Attributes:
        query_length: Character count of the user query.
        estimated_tokens: Approximate token count (chars / 4).
        has_code: Whether the query contains code blocks.
        has_multi_hop: Whether the query implies multi-step reasoning.
        user_tier: Premium level of the requesting user (0=free, 3=enterprise).
        system_load: Current system load factor [0.0, 1.0].
        cache_hit: Whether a cached result is available.
    """

    query_length: int = 0
    estimated_tokens: int = 0
    has_code: bool = False
    has_multi_hop: bool = False
    user_tier: int = 0
    system_load: float = 0.0
    cache_hit: bool = False

    @classmethod
    def from_query(
        cls,
        query: str,
        user_tier: int = 0,
        system_load: float = 0.0,
    ) -> RoutingSignal:
        """Build a signal from a raw query string.

        Args:
            query: User query text.
            user_tier: User subscription tier.
            system_load: Current system load [0, 1].

        Returns:
            Populated RoutingSignal.
        """
        q = query.lower()
        has_code = "```" in query or "def " in q or "class " in q
        has_multi_hop = any(
            kw in q
            for kw in [
                "compare",
                "contrast",
                "step by step",
                "chain of thought",
                "multi-hop",
                "across",
                "relationship between",
            ]
        )
        return cls(
            query_length=len(query),
            estimated_tokens=max(1, len(query) // 4),
            has_code=has_code,
            has_multi_hop=has_multi_hop,
            user_tier=user_tier,
            system_load=system_load,
        )

    @property
    def complexity_score(self) -> float:
        """
        Compute a normalised complexity score in [0, 100].

        Scoring formula:
            base       = log2(estimated_tokens) * 10   (token mass)
            + 15       if has_code
            + 20       if has_multi_hop
            + load_penalty  (system_load * 10)
            - 30       if cache_hit
        Clamped to [0, 100].
        """
        base = math.log2(max(1, self.estimated_tokens)) * 10.0
        score = base
        if self.has_code:
            score += 15.0
        if self.has_multi_hop:
            score += 20.0
        score += self.system_load * 10.0
        if self.cache_hit:
            score -= 30.0
        return max(0.0, min(100.0, score))


# =============================================================================
# Processing Strategy
# =============================================================================


@dataclass(frozen=True)
class ProcessingStrategy:
    """
    Concrete processing parameters for a routing decision.

    Consumed by downstream processors (RAG engine, model orchestrator)
    to configure their behaviour.
    """

    tier: ProcessingTier
    timeout_ms: int
    max_retrieval_docs: int
    enable_reranking: bool
    enable_multi_model: bool
    max_reasoning_steps: int
    model_preference: str  # "fast", "balanced", "quality"

    @classmethod
    def for_tier(cls, tier: ProcessingTier) -> ProcessingStrategy:
        """Create the default strategy for a given tier."""
        strategies: dict[ProcessingTier, ProcessingStrategy] = {
            ProcessingTier.FAST: cls(
                tier=ProcessingTier.FAST,
                timeout_ms=2_000,
                max_retrieval_docs=3,
                enable_reranking=False,
                enable_multi_model=False,
                max_reasoning_steps=1,
                model_preference="fast",
            ),
            ProcessingTier.STANDARD: cls(
                tier=ProcessingTier.STANDARD,
                timeout_ms=10_000,
                max_retrieval_docs=8,
                enable_reranking=True,
                enable_multi_model=False,
                max_reasoning_steps=3,
                model_preference="balanced",
            ),
            ProcessingTier.DEEP: cls(
                tier=ProcessingTier.DEEP,
                timeout_ms=30_000,
                max_retrieval_docs=15,
                enable_reranking=True,
                enable_multi_model=True,
                max_reasoning_steps=5,
                model_preference="quality",
            ),
            ProcessingTier.EXPERT: cls(
                tier=ProcessingTier.EXPERT,
                timeout_ms=60_000,
                max_retrieval_docs=25,
                enable_reranking=True,
                enable_multi_model=True,
                max_reasoning_steps=10,
                model_preference="quality",
            ),
        }
        return strategies[tier]


# =============================================================================
# Routing Decision
# =============================================================================


@dataclass
class RoutingDecision:
    """Output of the adaptive router."""

    signal: RoutingSignal
    complexity_score: float
    percentile: float
    tier: ProcessingTier
    strategy: ProcessingStrategy
    decided_at: float = field(default_factory=time.monotonic)
    reason: str = ""


# =============================================================================
# Sliding Window
# =============================================================================


class SlidingWindow:
    """
    Fixed-size sliding window for recent complexity scores.

    Used to compute runtime percentiles so that tier boundaries
    adapt to actual workload characteristics.
    """

    def __init__(self, max_size: int = 1000) -> None:
        if max_size <= 0:
            raise ValueError(f"max_size must be positive, got {max_size}")
        self._scores: deque[float] = deque(maxlen=max_size)

    def push(self, score: float) -> None:
        """Record a new complexity score."""
        self._scores.append(score)

    @property
    def count(self) -> int:
        return len(self._scores)

    def percentile_of(self, score: float) -> float:
        """
        Compute the percentile rank of *score* relative to the window.

        Returns a value in [0, 100].  If the window is empty, assumes
        the score is at the 50th percentile (median).
        """
        if not self._scores:
            return 50.0
        below = sum(1 for s in self._scores if s < score)
        equal = sum(1 for s in self._scores if s == score)
        return ((below + 0.5 * equal) / len(self._scores)) * 100.0

    def quantile(self, q: float) -> float:
        """Return the value at quantile *q* (0–1) in the window."""
        if not self._scores:
            return 0.0
        sorted_scores = sorted(self._scores)
        idx = max(0, min(len(sorted_scores) - 1, int(q * len(sorted_scores))))
        return sorted_scores[idx]

    def stats(self) -> dict[str, float]:
        """Return summary statistics of the current window."""
        if not self._scores:
            return {"count": 0, "mean": 0.0, "p50": 0.0, "p85": 0.0, "p95": 0.0}
        return {
            "count": float(len(self._scores)),
            "mean": statistics.mean(self._scores),
            "p50": self.quantile(0.50),
            "p85": self.quantile(0.85),
            "p95": self.quantile(0.95),
        }


# =============================================================================
# Adaptive Router
# =============================================================================


class AdaptiveRouter:
    """
    Adaptive percentile-based request router.

    Maintains a sliding window of recent request complexity scores
    and classifies each new request into a processing tier based on
    its percentile rank within the window.

    Args:
        thresholds: Percentile boundaries for tiers.
        window_size: Number of recent scores to retain.
        cold_start_tier: Default tier when the window is too small
            for meaningful percentile calculation.
        cold_start_min_samples: Minimum window size before using percentiles.
    """

    def __init__(
        self,
        thresholds: TierThresholds | None = None,
        window_size: int = 1000,
        cold_start_tier: ProcessingTier = ProcessingTier.STANDARD,
        cold_start_min_samples: int = 20,
    ) -> None:
        self.thresholds = thresholds or DEFAULT_THRESHOLDS
        self.window = SlidingWindow(max_size=window_size)
        self.cold_start_tier = cold_start_tier
        self.cold_start_min_samples = cold_start_min_samples
        self._total_routed: int = 0

    def route(self, signal: RoutingSignal) -> RoutingDecision:
        """
        Route a signal to a processing tier and strategy.

        Args:
            signal: The incoming routing signal.

        Returns:
            A RoutingDecision with the selected tier and strategy.
        """
        score = signal.complexity_score

        # Fast path: cache hits always go to FAST tier
        if signal.cache_hit:
            tier = ProcessingTier.FAST
            percentile = 0.0
            reason = "cache_hit → fast"
        elif self.window.count < self.cold_start_min_samples:
            tier = self.cold_start_tier
            percentile = 50.0
            reason = f"cold_start (n={self.window.count}) → {tier.value}"
        else:
            percentile = self.window.percentile_of(score)
            tier = self._classify(percentile)
            reason = f"score={score:.1f} p={percentile:.1f} → {tier.value}"

        # Record score for future percentile calculations
        self.window.push(score)
        self._total_routed += 1

        strategy = ProcessingStrategy.for_tier(tier)

        decision = RoutingDecision(
            signal=signal,
            complexity_score=score,
            percentile=percentile,
            tier=tier,
            strategy=strategy,
            reason=reason,
        )

        logger.debug(
            "AdaptiveRouter: %s (score=%.1f, p=%.0f, tokens≈%d)",
            tier.value,
            score,
            percentile,
            signal.estimated_tokens,
        )

        return decision

    def _classify(self, percentile: float) -> ProcessingTier:
        """Map a percentile value to a processing tier."""
        if percentile <= self.thresholds.fast_upper:
            return ProcessingTier.FAST
        if percentile <= self.thresholds.standard_upper:
            return ProcessingTier.STANDARD
        if percentile <= self.thresholds.deep_upper:
            return ProcessingTier.DEEP
        return ProcessingTier.EXPERT

    @property
    def total_routed(self) -> int:
        """Total requests routed since creation."""
        return self._total_routed

    def get_stats(self) -> dict[str, Any]:
        """Return router statistics and window summary."""
        return {
            "total_routed": self._total_routed,
            "window": self.window.stats(),
            "thresholds": {
                "fast_upper": self.thresholds.fast_upper,
                "standard_upper": self.thresholds.standard_upper,
                "deep_upper": self.thresholds.deep_upper,
            },
        }


# =============================================================================
# Module-level singleton
# =============================================================================

_adaptive_router: AdaptiveRouter | None = None


def get_adaptive_router() -> AdaptiveRouter:
    """Get or create the global adaptive router singleton."""
    global _adaptive_router
    if _adaptive_router is None:
        _adaptive_router = AdaptiveRouter()
    return _adaptive_router


__all__ = [
    "AdaptiveRouter",
    "DEFAULT_THRESHOLDS",
    "ProcessingStrategy",
    "ProcessingTier",
    "RoutingDecision",
    "RoutingSignal",
    "SlidingWindow",
    "TierThresholds",
    "get_adaptive_router",
]
