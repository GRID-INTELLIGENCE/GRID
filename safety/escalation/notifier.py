"""
Notification channels for escalation events.

Supports Slack webhook, PagerDuty, and email (via SMTP).
All channels are optional; configure via environment variables.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from typing import Any

import httpx

from safety.observability.logging_setup import get_logger

logger = get_logger("escalation.notifier")

_SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK", "")
_PAGERDUTY_KEY = os.getenv("PAGERDUTY_ROUTING_KEY", "")
_http_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=httpx.Timeout(10.0))
    return _http_client


def _truncate(text: str, max_len: int = 500) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


async def notify_slack(
    *,
    audit_id: str,
    request_id: str,
    user_id: str,
    trust_tier: str,
    reason_code: str,
    severity: str,
    input_text: str,
    detector_scores: dict[str, Any],
    created_at: str | None = None,
) -> bool:
    """
    Post an escalation notification to Slack.

    Returns True if successful.
    """
    if not _SLACK_WEBHOOK_URL:
        logger.warning("slack_webhook_not_configured")
        return False

    now = created_at or datetime.now(UTC).isoformat()
    severity_emoji = {
        "critical": ":rotating_light:",
        "high": ":warning:",
        "medium": ":large_yellow_circle:",
        "low": ":white_circle:",
    }.get(severity, ":question:")

    payload = {
        "text": f"{severity_emoji} Safety Escalation [{severity.upper()}]",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{severity_emoji} Safety Escalation: {reason_code}",
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Audit ID:*\n`{audit_id}`"},
                    {"type": "mrkdwn", "text": f"*Request ID:*\n`{request_id}`"},
                    {"type": "mrkdwn", "text": f"*User ID:*\n`{user_id}`"},
                    {"type": "mrkdwn", "text": f"*Trust Tier:*\n{trust_tier}"},
                    {"type": "mrkdwn", "text": f"*Severity:*\n{severity.upper()}"},
                    {"type": "mrkdwn", "text": f"*Reason:*\n{reason_code}"},
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Input (truncated):*\n```{_truncate(input_text)}```",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Detector Scores:*\n```{json.dumps(detector_scores, indent=2)[:500]}```",
                },
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"Created at: {now}"},
                ],
            },
        ],
    }

    try:
        client = _get_client()
        resp = await client.post(_SLACK_WEBHOOK_URL, json=payload)
        resp.raise_for_status()
        logger.info("slack_notification_sent", audit_id=audit_id)
        return True
    except Exception as exc:
        logger.error("slack_notification_failed", audit_id=audit_id, error=str(exc))
        return False


async def notify_pagerduty(
    *,
    audit_id: str,
    reason_code: str,
    severity: str,
    summary: str,
) -> bool:
    """
    Trigger a PagerDuty incident for critical escalations.

    Returns True if successful.
    """
    if not _PAGERDUTY_KEY:
        logger.info("pagerduty_not_configured")
        return False

    pd_severity = {
        "critical": "critical",
        "high": "error",
        "medium": "warning",
        "low": "info",
    }.get(severity, "warning")

    payload = {
        "routing_key": _PAGERDUTY_KEY,
        "event_action": "trigger",
        "dedup_key": f"safety-{audit_id}",
        "payload": {
            "summary": f"[Safety] {reason_code}: {_truncate(summary, 200)}",
            "severity": pd_severity,
            "source": "safety-enforcement-pipeline",
            "component": "post-check-detector",
            "custom_details": {
                "audit_id": audit_id,
                "reason_code": reason_code,
            },
        },
    }

    try:
        client = _get_client()
        resp = await client.post(
            "https://events.pagerduty.com/v2/enqueue", json=payload
        )
        resp.raise_for_status()
        logger.info("pagerduty_incident_triggered", audit_id=audit_id)
        return True
    except Exception as exc:
        logger.error("pagerduty_notification_failed", audit_id=audit_id, error=str(exc))
        return False


async def close_notifier() -> None:
    """Close the HTTP client."""
    global _http_client
    if _http_client:
        await _http_client.aclose()
        _http_client = None
