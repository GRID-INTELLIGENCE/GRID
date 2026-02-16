"""
GUARDIAN - Unified Rule Engine
Project GUARDIAN: Phase 1 - Unified Rule Orchestration

This module provides a high-performance, unified rule engine for safety enforcement.
Uses hybrid approach: Aho-Corasick Trie for keywords + Compiled RegexSet for patterns.
Optimized for <50ms pre-check budget.

Architecture:
- RuleRegistry: Unified source of truth for all rules
- TrieMatcher: Blazing-fast Aho-Corasick for keyword matching
- RegexSetMatcher: Compiled regex patterns for complex matching
- DynamicRuleLoader: Hot-reload capability from YAML/JSON
- RuleEngine: Orchestrates all matchers and provides unified API
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import threading
import time
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum, auto
from typing import Any

# Try to import optional performance libraries
try:
    import ahocorasick  # pyright: ignore[reportMissingImports]

    AHO_AVAILABLE = True
except ImportError:
    AHO_AVAILABLE = False

try:
    import yaml  # noqa: F401

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

logger = logging.getLogger(__name__)


class MatchType(Enum):
    """Types of pattern matching supported."""

    KEYWORD = auto()  # Simple substring matching (Trie)
    REGEX = auto()  # Regular expression matching
    SEMANTIC = auto()  # Semantic/context-aware matching
    COMPOSITE = auto()  # Combination of multiple patterns


class Severity(Enum):
    """Severity levels for rule matches."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RuleAction(Enum):
    """Actions to take when rule matches."""

    BLOCK = "block"
    ESCALATE = "escalate"
    LOG = "log"
    WARN = "warn"
    CANARY = "canary"  # Phase 3: Inject canary tokens


@dataclass(frozen=True)
class RuleMatch:
    """Result of a rule match."""

    rule_id: str
    rule_name: str
    category: str
    severity: Severity
    action: RuleAction
    confidence: float
    matched_text: str
    position: tuple[int, int]  # Start, end position
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "category": self.category,
            "severity": self.severity.value,
            "action": self.action.value,
            "confidence": self.confidence,
            "matched_text": self.matched_text,
            "position": self.position,
            "metadata": self.metadata,
        }


@dataclass
class SafetyRule:
    """Definition of a safety rule."""

    id: str
    name: str
    description: str
    category: str
    severity: Severity
    action: RuleAction
    match_type: MatchType

    # Match criteria
    keywords: list[str] = field(default_factory=list)  # For KEYWORD type
    patterns: list[str] = field(default_factory=list)  # For REGEX type
    composite_rules: list[str] = field(default_factory=list)  # For COMPOSITE type

    # Configuration
    confidence: float = 0.8
    case_sensitive: bool = False
    enabled: bool = True
    priority: int = 100  # Lower = higher priority
    version: str = "1.0.0"

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    author: str = "system"
    tags: list[str] = field(default_factory=list)

    # Performance hints
    cache_results: bool = False
    max_matches: int = 10

    def get_match_signature(self) -> str:
        """Generate unique signature for rule matching logic."""
        sig_data = {
            "id": self.id,
            "match_type": self.match_type.name,
            "keywords": sorted(self.keywords) if self.keywords else [],
            "patterns": sorted(self.patterns) if self.patterns else [],
            "case_sensitive": self.case_sensitive,
        }
        return hashlib.sha256(json.dumps(sig_data, sort_keys=True).encode()).hexdigest()[:16]


class TrieMatcher:
    """
    High-performance Aho-Corasick trie matcher for keyword detection.

    Time complexity: O(n + m + z) where:
    - n = text length
    - m = total pattern length
    - z = number of matches

    Much faster than regex for simple keyword matching.
    """

    def __init__(self):
        self._automaton = None
        self._keywords: set[str] = set()
        self._rule_map: dict[str, list[str]] = defaultdict(list)  # keyword -> rule_ids
        self._lock = threading.RLock()
        self._built = False

    def add_rule(self, rule: SafetyRule) -> None:
        """Add a keyword rule to the trie."""
        with self._lock:
            if rule.match_type != MatchType.KEYWORD:
                return

            for keyword in rule.keywords:
                normalized = keyword.lower() if not rule.case_sensitive else keyword
                self._keywords.add(normalized)
                self._rule_map[normalized].append(rule.id)

            self._built = False  # Mark for rebuild

    def build(self) -> None:
        """Build the automaton. Must be called before matching."""
        with self._lock:
            if AHO_AVAILABLE:
                self._automaton = ahocorasick.Automaton()
                for idx, keyword in enumerate(self._keywords):
                    self._automaton.add_word(keyword, (keyword, idx))
                self._automaton.make_automaton()
            else:
                # Fallback: use simple string search
                self._automaton = list(self._keywords)

            self._built = True
            logger.info(f"TrieMatcher built with {len(self._keywords)} keywords")

    def match(self, text: str) -> list[tuple[str, int, int]]:
        """
        Match text against all keywords.

        Returns: List of (matched_keyword, start_pos, end_pos)
        """
        if not self._built:
            self.build()

        if not text:
            return []

        matches = []
        text_lower = text.lower()

        if AHO_AVAILABLE and self._automaton:
            for end_pos, (keyword, _) in (
                self._automaton.iter(text_lower) or []  # pyright: ignore[reportAttributeAccessIssue]
            ):  # pyright: ignore[reportAttributeAccessIssue]
                start_pos = end_pos - len(keyword) + 1
                matches.append((keyword, start_pos, end_pos + 1))
        else:
            # Fallback implementation
            for keyword in self._automaton or []:
                pos = 0
                while True:
                    pos = text_lower.find(keyword, pos)
                    if pos == -1:
                        break
                    matches.append((keyword, pos, pos + len(keyword)))
                    pos += 1

        return matches

    def get_rule_ids_for_match(self, matched_keyword: str) -> list[str]:
        """Get rule IDs associated with a matched keyword."""
        return self._rule_map.get(matched_keyword.lower(), [])

    def clear(self) -> None:
        """Clear all keywords and rebuild."""
        with self._lock:
            self._keywords.clear()
            self._rule_map.clear()
            self._automaton = None
            self._built = False


class RegexSetMatcher:
    """
    Compiled regex pattern matcher with optimization.

    Uses Python's re module with compiled patterns for speed.
    Groups patterns by flags for efficiency.
    """

    def __init__(self):
        self._patterns: dict[str, re.Pattern] = {}  # rule_id -> compiled pattern
        self._rule_map: dict[str, SafetyRule] = {}  # rule_id -> rule
        self._lock = threading.RLock()

    def add_rule(self, rule: SafetyRule) -> None:
        """Add a regex rule."""
        with self._lock:
            if rule.match_type != MatchType.REGEX:
                return

            # Combine all patterns with OR
            if rule.patterns:
                flags = 0 if rule.case_sensitive else re.IGNORECASE
                combined = "|".join(f"({p})" for p in rule.patterns)
                self._patterns[rule.id] = re.compile(combined, flags)
                self._rule_map[rule.id] = rule

                logger.debug(f"Added regex rule {rule.id} with {len(rule.patterns)} patterns")

    def match(self, text: str) -> list[tuple[str, str, int, int]]:
        """
        Match text against all regex patterns.

        Returns: List of (rule_id, matched_text, start_pos, end_pos)
        """
        if not text:
            return []

        matches = []

        with self._lock:
            for rule_id, pattern in self._patterns.items():
                for match in pattern.finditer(text):
                    matches.append((rule_id, match.group(), match.start(), match.end()))

        return matches

    def clear(self) -> None:
        """Clear all patterns."""
        with self._lock:
            self._patterns.clear()
            self._rule_map.clear()


class RuleRegistry:
    """
    Unified source of truth for all safety rules.

    Maintains rule definitions and provides efficient lookup.
    Thread-safe for concurrent access.
    """

    def __init__(self):
        self._rules: dict[str, SafetyRule] = {}
        self._categories: dict[str, set[str]] = defaultdict(set)
        self._severity_index: dict[Severity, set[str]] = defaultdict(set)
        self._action_index: dict[RuleAction, set[str]] = defaultdict(set)
        self._lock = threading.RLock()
        self._version = "0.0.0"
        self._last_updated = datetime.now(UTC).isoformat()

    def register(self, rule: SafetyRule) -> bool:
        """Register a new rule."""
        with self._lock:
            if rule.id in self._rules:
                logger.warning(f"Rule {rule.id} already exists, updating")

            self._rules[rule.id] = rule
            self._categories[rule.category].add(rule.id)
            self._severity_index[rule.severity].add(rule.id)
            self._action_index[rule.action].add(rule.id)

            logger.info(f"Registered rule: {rule.id} ({rule.name})")
            return True

    def unregister(self, rule_id: str) -> bool:
        """Remove a rule."""
        with self._lock:
            if rule_id not in self._rules:
                return False

            rule = self._rules[rule_id]
            del self._rules[rule_id]
            self._categories[rule.category].discard(rule_id)
            self._severity_index[rule.severity].discard(rule_id)
            self._action_index[rule.action].discard(rule_id)

            logger.info(f"Unregistered rule: {rule_id}")
            return True

    def get(self, rule_id: str) -> SafetyRule | None:
        """Get rule by ID."""
        with self._lock:
            return self._rules.get(rule_id)

    def get_all(self) -> list[SafetyRule]:
        """Get all registered rules."""
        with self._lock:
            return list(self._rules.values())

    def get_by_category(self, category: str) -> list[SafetyRule]:
        """Get rules by category."""
        with self._lock:
            return [self._rules[r] for r in self._categories.get(category, [])]

    def get_by_severity(self, severity: Severity) -> list[SafetyRule]:
        """Get rules by severity."""
        with self._lock:
            return [self._rules[r] for r in self._severity_index.get(severity, [])]

    def get_enabled(self) -> list[SafetyRule]:
        """Get all enabled rules."""
        with self._lock:
            return [r for r in self._rules.values() if r.enabled]

    def update_version(self, version: str) -> None:
        """Update registry version."""
        with self._lock:
            self._version = version
            self._last_updated = datetime.now(UTC).isoformat()

    def get_stats(self) -> dict[str, Any]:
        """Get registry statistics."""
        with self._lock:
            return {
                "total_rules": len(self._rules),
                "enabled_rules": sum(1 for r in self._rules.values() if r.enabled),
                "categories": {cat: len(rules) for cat, rules in self._categories.items()},
                "by_severity": {sev.value: len(rules) for sev, rules in self._severity_index.items()},
                "version": self._version,
                "last_updated": self._last_updated,
            }

    def clear(self) -> None:
        """Clear all rules."""
        with self._lock:
            self._rules.clear()
            self._categories.clear()
            self._severity_index.clear()
            self._action_index.clear()
            logger.info("Rule registry cleared")


class GuardianEngine:
    """
    Main orchestrator for the GUARDIAN rule engine.

    Coordinates TrieMatcher, RegexSetMatcher, and RuleRegistry
    to provide unified, blazing-fast rule evaluation.
    """

    def __init__(self, enable_cache: bool = True):
        self.registry = RuleRegistry()
        self.trie = TrieMatcher()
        self.regex_set = RegexSetMatcher()

        self._enable_cache = enable_cache
        self._cache: OrderedDict[str, tuple[list[RuleMatch], float]] = OrderedDict()
        self._cache_lock = threading.RLock()
        self._max_cache_size = 10000

        self._stats = {
            "total_evaluations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_matches": 0,
            "avg_latency_ms": 0.0,
        }
        self._stats_lock = threading.Lock()

    def load_rules(self, rules: list[SafetyRule], rebuild: bool = True) -> None:
        """
        Load rules into the engine.

        Args:
            rules: List of safety rules to load
            rebuild: Whether to rebuild matchers immediately
        """
        start_time = time.perf_counter()

        # Clear existing rules
        self.registry.clear()
        self.trie.clear()
        self.regex_set.clear()
        self._cache.clear()

        # Register rules
        for rule in rules:
            self.registry.register(rule)

            # Add to appropriate matcher
            if rule.match_type == MatchType.KEYWORD:
                self.trie.add_rule(rule)
            elif rule.match_type == MatchType.REGEX:
                self.regex_set.add_rule(rule)

        # Build matchers
        if rebuild:
            self.trie.build()

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(f"Loaded {len(rules)} rules in {elapsed_ms:.2f}ms")

    def evaluate(
        self, text: str, context: dict[str, Any] | None = None, use_cache: bool = True
    ) -> tuple[list[RuleMatch], float]:
        """
        Evaluate text against all loaded rules.

        Args:
            text: Text to evaluate
            context: Optional context for evaluation
            use_cache: Whether to use result caching

        Returns:
            Tuple of (list of matches, evaluation latency in ms)
        """
        start_time = time.perf_counter()
        context = context or {}

        # Check cache
        cache_key = None
        if use_cache and self._enable_cache and text:
            cache_key = self._get_cache_key(text, context)
            with self._cache_lock:
                if cache_key in self._cache:
                    result = self._cache[cache_key]
                    # LRU: move to end to mark as most recently used
                    self._cache.move_to_end(cache_key)
                    self._update_stats(cache_hit=True)
                    return result

        matches = []

        # Trie matching (fast path)
        trie_matches = self.trie.match(text)
        for keyword, start, end in trie_matches:
            rule_ids = self.trie.get_rule_ids_for_match(keyword)
            for rule_id in rule_ids:
                rule = self.registry.get(rule_id)
                if rule and rule.enabled:
                    matches.append(
                        RuleMatch(
                            rule_id=rule.id,
                            rule_name=rule.name,
                            category=rule.category,
                            severity=rule.severity,
                            action=rule.action,
                            confidence=rule.confidence,
                            matched_text=text[start:end],
                            position=(start, end),
                            metadata={"match_type": "keyword", "keyword": keyword},
                        )
                    )

        # Regex matching
        regex_matches = self.regex_set.match(text)
        for rule_id, matched_text, start, end in regex_matches:
            rule = self.registry.get(rule_id)
            if rule and rule.enabled:
                matches.append(
                    RuleMatch(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        category=rule.category,
                        severity=rule.severity,
                        action=rule.action,
                        confidence=rule.confidence,
                        matched_text=matched_text,
                        position=(start, end),
                        metadata={"match_type": "regex"},
                    )
                )

        # Sort by priority and severity
        def _get_priority(rule_id: str) -> int:
            rule = self.registry.get(rule_id)
            return rule.priority if rule else 0

        matches.sort(
            key=lambda m: (
                (
                    0
                    if m.severity == Severity.CRITICAL
                    else 1
                    if m.severity == Severity.HIGH
                    else 2
                    if m.severity == Severity.MEDIUM
                    else 3
                ),
                -_get_priority(m.rule_id),
            )
        )

        # Limit matches per rule
        seen_rules = set()
        filtered_matches = []
        for match in matches:
            if match.rule_id not in seen_rules:
                seen_rules.add(match.rule_id)
                filtered_matches.append(match)

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Update cache
        if use_cache and self._enable_cache and text and cache_key is not None:
            self._update_cache(cache_key, (filtered_matches, elapsed_ms))

        # Update stats
        self._update_stats(cache_hit=False, latency_ms=elapsed_ms, match_count=len(filtered_matches))

        return filtered_matches, elapsed_ms

    def quick_check(self, text: str) -> tuple[bool, str | None, RuleAction | None]:
        """
        Quick check for blocking rules.

        Returns: (should_block, reason_code, action)
        """
        matches, _ = self.evaluate(text, use_cache=True)

        for match in matches:
            if match.action in (RuleAction.BLOCK, RuleAction.CANARY):
                return True, f"{match.category.upper()}_{match.severity.value.upper()}", match.action
            elif match.action == RuleAction.ESCALATE and match.severity in (Severity.HIGH, Severity.CRITICAL):
                return True, f"ESCALATE_{match.category.upper()}", match.action

        return False, None, None

    def _get_cache_key(self, text: str, context: dict[str, Any]) -> str:
        """Generate cache key for text evaluation."""
        key_data = f"{text}:{json.dumps(context, sort_keys=True)}:{self.registry._version}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _update_cache(self, key: str, value: tuple[list[RuleMatch], float]) -> None:
        """Update cache with LRU eviction."""
        with self._cache_lock:
            # If key already in cache, remove it first to re-insert at end
            if key in self._cache:
                del self._cache[key]
            elif len(self._cache) >= self._max_cache_size:
                # LRU: remove first entry (least recently used)
                self._cache.popitem(last=False)
            self._cache[key] = value

    def _update_stats(self, cache_hit: bool = False, latency_ms: float = 0.0, match_count: int = 0) -> None:
        """Update engine statistics."""
        with self._stats_lock:
            self._stats["total_evaluations"] += 1
            if cache_hit:
                self._stats["cache_hits"] += 1
            else:
                self._stats["cache_misses"] += 1
                self._stats["total_matches"] += match_count

                # Update running average
                n = self._stats["cache_misses"]
                self._stats["avg_latency_ms"] = ((self._stats["avg_latency_ms"] * (n - 1)) + latency_ms) / n

    def get_stats(self) -> dict[str, Any]:
        """Get engine statistics."""
        with self._stats_lock:
            stats = self._stats.copy()
            stats["cache_hit_rate"] = stats["cache_hits"] / max(stats["total_evaluations"], 1)
            stats["registry_stats"] = self.registry.get_stats()
            return stats

    def clear_cache(self) -> None:
        """Clear evaluation cache."""
        with self._cache_lock:
            self._cache.clear()
            logger.info("Evaluation cache cleared")


# Singleton instance for global use
_guardian_engine: GuardianEngine | None = None
_guardian_engine_lock = threading.RLock()


def get_guardian_engine() -> GuardianEngine:
    """Get global GUARDIAN engine instance (thread-safe)."""
    global _guardian_engine
    if _guardian_engine is None:
        with _guardian_engine_lock:
            if _guardian_engine is None:
                _guardian_engine = GuardianEngine()
    return _guardian_engine


def init_guardian(rules: list[SafetyRule] | None = None) -> GuardianEngine:
    """Initialize GUARDIAN with optional rules."""
    engine = get_guardian_engine()
    if rules:
        engine.load_rules(rules)
    return engine
