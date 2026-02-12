"""
GUARDIAN - Unified Rule Engine for Safety & Security
Project GUARDIAN: High-Performance Rule Orchestration

Provides blazing-fast (<50ms) rule evaluation using hybrid Trie + RegexSet approach.
"""

from .engine import (
    GuardianEngine,
    MatchType,
    RuleAction,
    RuleMatch,
    RuleRegistry,
    SafetyRule,
    Severity,
    TrieMatcher,
    RegexSetMatcher,
    get_guardian_engine,
    init_guardian,
)

from .loader import (
    RuleLoader,
    RuleValidationError,
    DynamicRuleManager,
    get_rule_loader,
    get_dynamic_manager,
    init_guardian_rules,
)

__all__ = [
    # Core Engine
    "GuardianEngine",
    "RuleRegistry",
    "SafetyRule",
    "RuleMatch",
    "Severity",
    "RuleAction",
    "MatchType",
    "TrieMatcher",
    "RegexSetMatcher",
    "get_guardian_engine",
    "init_guardian",
    # Loader
    "RuleLoader",
    "RuleValidationError",
    "DynamicRuleManager",
    "get_rule_loader",
    "get_dynamic_manager",
    "init_guardian_rules",
]

__version__ = "1.0.0"
