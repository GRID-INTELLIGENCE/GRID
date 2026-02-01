"""AI Safety Actions Skill.

Executes remediation actions (BLOCK, ESCALATE, REVIEW, LOG).
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from grid.skills.base import SimpleSkill

from .base import ActionResult, ActionType, SafetyCategory, SafetyViolation, ThreatLevel
from .config import get_config

logger = logging.getLogger(__name__)


def generate_content_hash(content: str) -> str:
    """Generate hash for content identification.

    Args:
        content: Content to hash.

    Returns:
        SHA-256 hash (first 16 characters).
    """
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def log_violation(violation: SafetyViolation, content_hash: str, action_taken: str) -> bool:
    """Log violation to file.

    Args:
        violation: The violation to log.
        content_hash: Hash of the content.
        action_taken: Action that was taken.

    Returns:
        True if logged successfully.
    """
    try:
        config = get_config()
        if not config.monitoring_enabled:
            return True

        # Create logs directory if needed
        log_dir = Path(".rag_logs/safety")
        log_dir.mkdir(parents=True, exist_ok=True)

        # Create log entry
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "content_hash": content_hash,
            "action": action_taken,
            "violation": violation.to_dict(),
        }

        # Append to daily log file
        log_file = log_dir / f"violations_{datetime.now(UTC).strftime('%Y-%m-%d')}.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

        return True

    except Exception as e:
        logger.error(f"Failed to log violation: {e}")
        return False


def execute_block_action(
    violation: SafetyViolation,
    content: str,
    context: dict[str, Any],
) -> ActionResult:
    """Execute BLOCK action.

    Args:
        violation: The violation that triggered the action.
        content: The content being evaluated.
        context: Additional context.

    Returns:
        Action result.
    """
    content_hash = generate_content_hash(content)

    # Log the block action
    log_violation(violation, content_hash, "BLOCK")

    logger.warning(f"Content blocked due to {violation.category.value}")

    return ActionResult(
        action=ActionType.BLOCK,
        success=True,
        message="Content blocked due to safety violation",
        details={
            "content_hash": content_hash,
            "category": violation.category.value,
            "severity": violation.severity.value,
            "blocked_at": datetime.now(UTC).isoformat(),
        },
    )


def execute_escalate_action(
    violation: SafetyViolation,
    content: str,
    context: dict[str, Any],
) -> ActionResult:
    """Execute ESCALATE action.

    Args:
        violation: The violation that triggered the action.
        content: The content being evaluated.
        context: Additional context.

    Returns:
        Action result.
    """
    content_hash = generate_content_hash(content)

    # Log the escalation
    log_violation(violation, content_hash, "ESCALATE")

    # Create escalation record
    escalation = {
        "timestamp": datetime.now(UTC).isoformat(),
        "content_hash": content_hash,
        "violation": violation.to_dict(),
        "context": context,
        "escalation_id": f"ESC_{int(time.time())}_{content_hash[:8]}",
    }

    # Save escalation for review
    try:
        escalation_dir = Path(".rag_logs/safety/escalations")
        escalation_dir.mkdir(parents=True, exist_ok=True)

        escalation_file = escalation_dir / f"{escalation['escalation_id']}.json"
        with open(escalation_file, "w", encoding="utf-8") as f:
            json.dump(escalation, f, indent=2)

    except Exception as e:
        logger.error(f"Failed to save escalation: {e}")

    logger.warning(f"Violation escalated: {escalation['escalation_id']}")

    return ActionResult(
        action=ActionType.ESCALATE,
        success=True,
        message="Violation escalated for human review",
        details={
            "escalation_id": escalation["escalation_id"],
            "content_hash": content_hash,
            "category": violation.category.value,
            "severity": violation.severity.value,
        },
    )


def execute_review_action(
    violation: SafetyViolation,
    content: str,
    context: dict[str, Any],
) -> ActionResult:
    """Execute REVIEW action.

    Args:
        violation: The violation that triggered the action.
        content: The content being evaluated.
        context: Additional context.

    Returns:
        Action result.
    """
    content_hash = generate_content_hash(content)

    # Log for review queue
    log_violation(violation, content_hash, "REVIEW")

    logger.info(f"Content flagged for review: {violation.category.value}")

    return ActionResult(
        action=ActionType.REVIEW,
        success=True,
        message="Content flagged for review",
        details={
            "content_hash": content_hash,
            "category": violation.category.value,
            "severity": violation.severity.value,
            "confidence": violation.confidence,
            "review_priority": "medium",
        },
    )


def execute_log_action(
    violation: SafetyViolation,
    content: str,
    context: dict[str, Any],
) -> ActionResult:
    """Execute LOG action.

    Args:
        violation: The violation that triggered the action.
        content: The content being evaluated.
        context: Additional context.

    Returns:
        Action result.
    """
    content_hash = generate_content_hash(content)

    # Just log the violation
    success = log_violation(violation, content_hash, "LOG")

    logger.debug(f"Violation logged: {violation.category.value}")

    return ActionResult(
        action=ActionType.LOG,
        success=success,
        message="Violation logged for audit trail",
        details={
            "content_hash": content_hash,
            "category": violation.category.value,
            "severity": violation.severity.value,
            "logged_at": datetime.now(UTC).isoformat(),
        },
    )


def determine_action_type(violation: SafetyViolation) -> ActionType:
    """Determine appropriate action based on violation severity.

    Args:
        violation: The detected violation.

    Returns:
        Recommended action type.
    """
    severity_actions = {
        "critical": ActionType.BLOCK,
        "high": ActionType.ESCALATE,
        "medium": ActionType.REVIEW,
        "low": ActionType.LOG,
        "none": ActionType.ALLOW,
    }

    return severity_actions.get(violation.severity.value, ActionType.LOG)


def actions_handler(args: dict[str, Any]) -> dict[str, Any]:
    """Handle safety action execution.

    Args:
        args: Dictionary containing:
            - violation: dict, required (SafetyViolation as dict)
            - action_type: str, optional (BLOCK, ESCALATE, REVIEW, LOG, ALLOW)
            - content: str, required
            - context: dict, optional

    Returns:
        Dictionary with action result.
    """
    violation_dict = args.get("violation")
    if not violation_dict:
        return {
            "success": False,
            "error": "No violation provided",
        }

    content = args.get("content", "")
    if not content:
        return {
            "success": False,
            "error": "No content provided",
        }

    context = args.get("context", {})

    # Reconstruct violation object
    try:
        # Convert string values to enums
        category_str = violation_dict.get("category", "harmful_content")
        severity_str = violation_dict.get("severity", "medium")

        # Map string to enum
        category = SafetyCategory.HARMFUL_CONTENT
        for cat in SafetyCategory:
            if cat.value == category_str:
                category = cat
                break

        severity = ThreatLevel.MEDIUM
        for sev in ThreatLevel:
            if sev.value == severity_str:
                severity = sev
                break

        violation = SafetyViolation(
            category=category,
            severity=severity,
            confidence=violation_dict.get("confidence", 0.7),
            description=violation_dict.get("description", ""),
            evidence=violation_dict.get("evidence", {}),
            provider=violation_dict.get("provider", "unknown"),
        )
    except Exception as e:
        return {
            "success": False,
            "error": f"Invalid violation format: {e}",
        }

    # Determine action type
    action_type_str = args.get("action_type")
    if action_type_str:
        try:
            action_type = ActionType(action_type_str.lower())
        except ValueError:
            action_type = determine_action_type(violation)
    else:
        action_type = determine_action_type(violation)

    # Execute action
    if action_type == ActionType.BLOCK:
        result = execute_block_action(violation, content, context)
    elif action_type == ActionType.ESCALATE:
        result = execute_escalate_action(violation, content, context)
    elif action_type == ActionType.REVIEW:
        result = execute_review_action(violation, content, context)
    elif action_type == ActionType.LOG:
        result = execute_log_action(violation, content, context)
    elif action_type == ActionType.ALLOW:
        result = ActionResult(
            action=ActionType.ALLOW,
            success=True,
            message="Content allowed",
            details={"content_hash": generate_content_hash(content)},
        )
    else:
        result = execute_log_action(violation, content, context)

    return {
        "success": result.success,
        "action": result.action.value,
        "message": result.message,
        "details": result.details,
        "timestamp": result.timestamp.isoformat(),
    }


# Skill instance
ai_safety_actions = SimpleSkill(
    id="ai_safety_actions",
    name="AI Safety Actions",
    description="Executes remediation actions (BLOCK, ESCALATE, REVIEW, LOG)",
    handler=actions_handler,
    version="1.0.0",
)
