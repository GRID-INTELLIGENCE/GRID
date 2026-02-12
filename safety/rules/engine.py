"""
Project GUARDIAN: Unified Rule Engine.
High-performance safety rule evaluation with dynamic orchestration support.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any

import redis

from safety.observability.security_monitoring import (
    SecurityEventSeverity,
    SecurityEventType,
)

logger = logging.getLogger(__name__)

@dataclass
class SafetyRule:
    """Enhanced safety rule with GUARDIAN metadata."""
    id: str
    name: str = "Unknown Rule"
    patterns: list[str] = field(default_factory=list)
    reason_code: str = "RULE_TRIGGERED"
    severity: SecurityEventSeverity = SecurityEventSeverity.MEDIUM
    event_type: SecurityEventType = SecurityEventType.AI_INPUT_BLOCKED
    description: str = ""
    
    # Internal compiled regexes
    _compiled: list[re.Pattern] = field(default_factory=list, init=False)

    def compile(self):
        self._compiled = [re.compile(p, re.IGNORECASE) for p in self.patterns]

    def matches(self, text: str) -> bool:
        return any(p.search(text) for p in self._compiled)


class RuleEngine:
    """High-performance rule engine for Project GUARDIAN with dynamic support."""

    def __init__(self):
        self.rules: list[SafetyRule] = []
        self._redis_client: redis.Redis | None = None
        self._last_dynamic_refresh = 0.0
        self._REFRESH_INTERVAL = 30.0  # seconds

    def _get_redis(self) -> redis.Redis | None:
        if self._redis_client is None:
            try:
                url = os.getenv("REDIS_URL", "redis://localhost:6379")
                self._redis_client = redis.Redis.from_url(
                    url, decode_responses=True, socket_connect_timeout=0.5
                )
            except Exception:
                return None
        return self._redis_client

    def load_rules(self, rule_file_path: str | None = None) -> None:
        """Load and compile base safety rules."""
        from .loader import load_rules
        raw_rules = load_rules(rule_file_path)
        self.rules = []
        for r in raw_rules:
            self._add_rule_from_dict(r)
        
        # Initial dynamic load
        self.refresh_dynamic_rules()

    def _add_rule_from_dict(self, r: dict[str, Any]):
        """Helper to parse and add a rule."""
        try:
            # Ensure enums are resolved
            severity_val = r.get("severity", "medium")
            event_type_val = r.get("event_type", "ai_input_blocked")
            
            # Handle string or Enum
            if isinstance(severity_val, str):
                sev = SecurityEventSeverity(severity_val.lower())
            else:
                sev = severity_val
                
            if isinstance(event_type_val, str):
                etype = SecurityEventType(event_type_val.lower())
            else:
                etype = event_type_val
            
            rule = SafetyRule(
                id=r.get("id", "unknown"),
                name=r.get("name", "Unknown Rule"),
                patterns=r.get("patterns", [r.get("pattern")]) if "patterns" in r or "pattern" in r else [],
                reason_code=r.get("reason_code", r.get("id", "RULE_TRIGGERED")),
                severity=sev,
                event_type=etype,
                description=r.get("description", "")
            )
            rule.compile()
            # If a rule with this ID already exists, replace it
            for i, existing in enumerate(self.rules):
                if existing.id == rule.id:
                    self.rules[i] = rule
                    return
            self.rules.append(rule)
        except Exception as e:
            logger.error(f"Failed to process rule {r.get('id')}: {e}")

    def refresh_dynamic_rules(self):
        """Fetch dynamic rules from Redis."""
        now = time.time()
        if now - self._last_dynamic_refresh < self._REFRESH_INTERVAL:
            return

        client = self._get_redis()
        if not client:
            return

        try:
            raw_rules = client.smembers("guardian:dynamic_rules")
            if not raw_rules:
                self._last_dynamic_refresh = now
                return
            
            for raw in raw_rules:
                try:
                    r = json.loads(raw)
                    self._add_rule_from_dict(r)
                except json.JSONDecodeError:
                    continue
            
            self._last_dynamic_refresh = now
        except Exception as e:
            logger.warning(f"Failed to refresh dynamic rules: {e}")

    # TODO: Add evaluation metrics (match count, latency histogram) to track
    #       rule engine performance in production and detect rule regression.
    def evaluate(self, text: str) -> tuple[bool, str | None, SafetyRule | None]:
        """
        Evaluate text against rules. Periodically refreshes dynamic rules.
        Returns: (blocked, reason_code, matched_rule_object)
        """
        self.refresh_dynamic_rules()
        
        if not text or not text.strip():
            return False, None, None

        for rule in self.rules:
            if rule.matches(text):
                return True, rule.reason_code, rule

        return False, None, None


# Global engine instance
_engine = RuleEngine()

def get_rule_engine() -> RuleEngine:
    """Get the global rule engine instance."""
    return _engine
