"""AI Safety Rules Skill.

Loads and evaluates YAML/JSON safety rule definitions.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from grid.skills.base import SimpleSkill

from .base import SafetyCategory, SafetyViolation, ThreatLevel

logger = logging.getLogger(__name__)


def load_rules(rule_set_path: str | None = None) -> list[dict[str, Any]]:
    """Load safety rules from file or use defaults.

    Args:
        rule_set_path: Path to rule definition file (JSON or YAML).

    Returns:
        List of rule definitions.
    """
    default_rules = [
        {
            "id": "harmful_content",
            "category": "harmful_content",
            "severity": "medium",
            "patterns": ["violence", "kill", "hurt", "attack", "weapon"],
            "confidence": 0.7,
        },
        {
            "id": "privacy_violation_email",
            "category": "privacy_violation",
            "severity": "medium",
            "pattern": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "confidence": 0.8,
        },
        {
            "id": "mental_health_risk",
            "category": "mental_health_risk",
            "severity": "high",
            "patterns": ["suicide", "kill myself", "end my life", "want to die"],
            "confidence": 0.9,
        },
        {
            "id": "harassment",
            "category": "harassment",
            "severity": "medium",
            "patterns": ["stupid", "idiot", "loser", "hate you"],
            "confidence": 0.6,
        },
    ]

    if not rule_set_path:
        return default_rules

    try:
        rule_path = Path(rule_set_path)
        if not rule_path.exists():
            logger.warning(f"Rule file not found: {rule_set_path}")
            return default_rules

        with open(rule_path, "r", encoding="utf-8") as f:
            if rule_path.suffix.lower() == ".json":
                rules = json.load(f)
            else:
                # For YAML, we'd need PyYAML - use JSON for now
                logger.warning("YAML support not available, using default rules")
                return default_rules

        logger.info(f"Loaded {len(rules)} rules from {rule_set_path}")
        return rules

    except Exception as e:
        logger.error(f"Failed to load rules from {rule_set_path}: {e}")
        return default_rules


def evaluate_rules(
    content: str,
    rules: list[dict[str, Any]],
    context: dict[str, Any] | None = None,
) -> list[SafetyViolation]:
    """Evaluate content against safety rules.

    Args:
        content: Content to evaluate.
        rules: List of rule definitions.
        context: Optional context for evaluation.

    Returns:
        List of triggered violations.
    """
    violations = []
    normalized_content = content.lower()
    context = context or {}

    for rule in rules:
        try:
            rule_id = rule.get("id", "unknown")
            category = SafetyCategory(rule.get("category", "harmful_content"))
            severity = ThreatLevel(rule.get("severity", "medium"))
            confidence = rule.get("confidence", 0.7)

            triggered = False
            evidence = {"rule_id": rule_id}

            # Check pattern (regex)
            if "pattern" in rule:
                pattern = rule["pattern"]
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    triggered = True
                    evidence["pattern"] = pattern
                    evidence["matches"] = matches[:5]  # Limit matches

            # Check patterns (list)
            if "patterns" in rule:
                patterns = rule["patterns"]
                matched_patterns = [p for p in patterns if p.lower() in normalized_content]
                if matched_patterns:
                    triggered = True
                    evidence["matched_patterns"] = matched_patterns

            # Check keywords
            if "keywords" in rule:
                keywords = rule["keywords"]
                matched_keywords = [k for k in keywords if k.lower() in normalized_content]
                if matched_keywords:
                    triggered = True
                    evidence["matched_keywords"] = matched_keywords

            if triggered:
                violation = SafetyViolation(
                    category=category,
                    severity=severity,
                    confidence=confidence,
                    description=f"Rule triggered: {rule_id}",
                    evidence=evidence,
                    provider="ai_safety_rules",
                )
                violations.append(violation)
                logger.debug(f"Rule {rule_id} triggered")

        except Exception as e:
            logger.error(f"Error evaluating rule {rule.get('id', 'unknown')}: {e}")
            continue

    return violations


def rules_handler(args: dict[str, Any]) -> dict[str, Any]:
    """Handle safety rules evaluation.

    Args:
        args: Dictionary containing:
            - content: str, required
            - rule_set_path: str, optional
            - context: dict, optional

    Returns:
        Dictionary with triggered rules and violations.
    """
    content = args.get("content", "")
    if not content:
        return {
            "success": True,
            "violations": [],
            "message": "No content provided",
        }

    rule_set_path = args.get("rule_set_path")
    context = args.get("context", {})

    # Load rules
    rules = load_rules(rule_set_path)

    # Evaluate content
    violations = evaluate_rules(content, rules, context)

    return {
        "success": True,
        "violations": [v.to_dict() for v in violations],
        "violation_count": len(violations),
        "rules_evaluated": len(rules),
        "content_length": len(content),
    }


# Skill instance
ai_safety_rules = SimpleSkill(
    id="ai_safety_rules",
    name="AI Safety Rules",
    description="Loads and evaluates YAML/JSON safety rule definitions",
    handler=rules_handler,
    version="1.0.0",
)
