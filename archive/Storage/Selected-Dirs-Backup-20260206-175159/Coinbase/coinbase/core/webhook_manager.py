"""
Webhook System for Real-Time Updates
=====================================
Configurable webhooks for price changes, portfolio alerts, and system events.

Usage:
    from coinbase.core.webhook_manager import WebhookManager, WebhookConfig

    config = WebhookConfig(
        url="https://api.example.com/webhook",
        events=["price_change", "portfolio_alert"]
    )

    manager = WebhookManager()
    manager.register_webhook(config)
"""

import hashlib
import hmac
import json
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from urllib.parse import urlparse

try:
    import requests  # type: ignore
except ImportError:
    requests = None

logger = logging.getLogger(__name__)


class WebhookEvent(Enum):
    """Types of webhook events."""

    PRICE_CHANGE = "price_change"
    PORTFOLIO_ALERT = "portfolio_alert"
    SYSTEM_EVENT = "system_event"
    TRADE_EXECUTED = "trade_executed"
    RISK_THRESHOLD = "risk_threshold"
    BACKUP_COMPLETED = "backup_completed"


@dataclass
class WebhookConfig:
    """Configuration for a webhook endpoint."""

    id: str
    url: str
    events: list[WebhookEvent]
    secret: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    retry_count: int = 3
    timeout_seconds: int = 30
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        # Validate URL
        parsed = urlparse(self.url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid webhook URL: {self.url}")
        if parsed.scheme not in ["http", "https"]:
            raise ValueError(f"URL scheme must be http or https: {self.url}")

        # Validate retry_count
        if not isinstance(self.retry_count, int) or self.retry_count < 0 or self.retry_count > 10:
            raise ValueError(f"retry_count must be between 0 and 10, got {self.retry_count}")

        # Validate timeout
        if (
            not isinstance(self.timeout_seconds, int)
            or self.timeout_seconds < 1
            or self.timeout_seconds > 300
        ):
            raise ValueError(
                f"timeout_seconds must be between 1 and 300, got {self.timeout_seconds}"
            )

        # Validate id
        if not self.id or len(self.id) > 256:
            raise ValueError("id must be non-empty and max 256 characters")


@dataclass
class WebhookPayload:
    """Payload for webhook requests."""

    event: WebhookEvent
    timestamp: datetime
    data: dict[str, Any]
    signature: str | None = None


class WebhookManager:
    """
    Manager for webhook registrations and event delivery.

    Features:
    - Event filtering
    - Signature verification
    - Retry logic
    - Batch processing
    """

    def __init__(self) -> None:
        """Initialize webhook manager."""
        self._webhooks: dict[str, WebhookConfig] = {}
        self._event_handlers: dict[WebhookEvent, list[str]] = {}
        self._delivery_history: list[dict[str, Any]] = []
        self._max_history = 1000
        self._lock = threading.Lock()
        self._session = None

    def _get_session(self) -> Any:
        """Get or create HTTP session."""
        if self._session is None:
            if requests is None:
                raise ImportError("requests library is required for webhooks")
            self._session = requests.Session()
        return self._session

    def register_webhook(self, config: WebhookConfig) -> bool:
        """
        Register a new webhook.

        Args:
            config: Webhook configuration

        Returns:
            True if registered successfully
        """
        with self._lock:
            self._webhooks[config.id] = config

            # Index by event type
            for event in config.events:
                if event not in self._event_handlers:
                    self._event_handlers[event] = []
                if config.id not in self._event_handlers[event]:
                    self._event_handlers[event].append(config.id)

            logger.info(f"Webhook registered: {config.id}")
            return True

    def unregister_webhook(self, webhook_id: str) -> bool:
        """
        Unregister a webhook.

        Args:
            webhook_id: Webhook ID to remove

        Returns:
            True if removed
        """
        with self._lock:
            if webhook_id not in self._webhooks:
                return False

            config = self._webhooks[webhook_id]

            # Remove from event handlers
            for event in config.events:
                if event in self._event_handlers:
                    if webhook_id in self._event_handlers[event]:
                        self._event_handlers[event].remove(webhook_id)

            del self._webhooks[webhook_id]
            logger.info(f"Webhook unregistered: {webhook_id}")
            return True

    def trigger_event(
        self, event: WebhookEvent, data: dict[str, Any], delay_seconds: int = 0
    ) -> list[dict[str, Any]]:
        """
        Trigger webhook event.

        Args:
            event: Event type
            data: Event data
            delay_seconds: Optional delay before sending

        Returns:
            List of delivery results
        """
        if delay_seconds > 0:
            import threading

            timer = threading.Timer(delay_seconds, lambda: self._send_event(event, data))
            timer.start()
            return [{"status": "scheduled", "delay": delay_seconds}]

        return self._send_event(event, data)

    def _send_event(self, event: WebhookEvent, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Send event to all registered webhooks."""
        with self._lock:
            webhook_ids = self._event_handlers.get(event, [])
            results = []

            for webhook_id in webhook_ids:
                config = self._webhooks.get(webhook_id)
                if not config or not config.active:
                    continue

                result = self._deliver_webhook(config, event, data)
                results.append(result)

                # Record delivery
                self._record_delivery(webhook_id, event, result)

            return results

    def _deliver_webhook(
        self, config: WebhookConfig, event: WebhookEvent, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Deliver webhook to single endpoint."""
        # Prepare payload
        payload = WebhookPayload(event=event, timestamp=datetime.now(), data=data)

        # Convert to dict
        payload_dict = {
            "event": payload.event.value,
            "timestamp": payload.timestamp.isoformat(),
            "data": payload.data,
        }

        # Sign payload if secret provided
        if config.secret:
            signature = self._sign_payload(json.dumps(payload_dict), config.secret)
            payload_dict["signature"] = signature

        # Send with retries
        for attempt in range(config.retry_count):
            try:
                session = self._get_session()

                headers = {
                    "Content-Type": "application/json",
                    "User-Agent": "CoinbasePlatform/1.0",
                    **config.headers,
                }

                response = session.post(
                    config.url, json=payload_dict, headers=headers, timeout=config.timeout_seconds
                )

                if response.status_code in [200, 201, 202, 204]:
                    return {
                        "webhook_id": config.id,
                        "status": "success",
                        "status_code": response.status_code,
                        "attempt": attempt + 1,
                    }

                # Retry on server errors
                if response.status_code >= 500:
                    if attempt < config.retry_count - 1:
                        import time

                        time.sleep(2**attempt)  # Exponential backoff
                        continue

                # Client error, don't retry
                return {
                    "webhook_id": config.id,
                    "status": "failed",
                    "status_code": response.status_code,
                    "error": f"HTTP {response.status_code}",
                }

            except Exception as e:
                if attempt < config.retry_count - 1:
                    import time

                    time.sleep(2**attempt)
                    continue

                return {
                    "webhook_id": config.id,
                    "status": "failed",
                    "error": str(e),
                    "attempt": attempt + 1,
                }

        return {"webhook_id": config.id, "status": "failed", "error": "Max retries exceeded"}

    def _sign_payload(self, payload: str, secret: str) -> str:
        """Sign payload with HMAC."""
        return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()

    def _record_delivery(
        self, webhook_id: str, event: WebhookEvent, result: dict[str, Any]
    ) -> None:
        """Record delivery attempt."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "webhook_id": webhook_id,
            "event": event.value,
            "status": result.get("status"),
            "status_code": result.get("status_code"),
            "error": result.get("error"),
        }

        self._delivery_history.append(record)

        # Limit history size
        if len(self._delivery_history) > self._max_history:
            self._delivery_history = self._delivery_history[-self._max_history :]

    def verify_signature(self, payload: str, signature: str, secret: str) -> bool:
        """
        Verify webhook signature.

        Args:
            payload: Request payload
            signature: Provided signature
            secret: Webhook secret

        Returns:
            True if signature valid
        """
        expected = self._sign_payload(payload, secret)
        return hmac.compare_digest(expected, signature)

    def get_webhooks(self, event: WebhookEvent | None = None) -> list[WebhookConfig]:
        """
        Get registered webhooks.

        Args:
            event: Optional event filter

        Returns:
            List of webhook configs
        """
        with self._lock:
            if event:
                webhook_ids = self._event_handlers.get(event, [])
                return [self._webhooks[w] for w in webhook_ids if w in self._webhooks]
            return list(self._webhooks.values())

    def get_delivery_history(
        self, webhook_id: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        Get delivery history.

        Args:
            webhook_id: Optional webhook filter
            limit: Maximum records to return

        Returns:
            List of delivery records
        """
        history = self._delivery_history

        if webhook_id:
            history = [h for h in history if h["webhook_id"] == webhook_id]

        return history[-limit:]

    def get_stats(self) -> dict[str, Any]:
        """Get webhook statistics."""
        with self._lock:
            total_webhooks = len(self._webhooks)
            active_webhooks = sum(1 for w in self._webhooks.values() if w.active)

            by_event = {}
            for event, webhook_ids in self._event_handlers.items():
                by_event[event.value] = len(webhook_ids)

            # Calculate success rate from recent history
            recent = self._delivery_history[-100:]
            if recent:
                success_count = sum(1 for r in recent if r["status"] == "success")
                success_rate = success_count / len(recent)
            else:
                success_rate = 0.0

            return {
                "total_webhooks": total_webhooks,
                "active_webhooks": active_webhooks,
                "by_event": by_event,
                "delivery_success_rate": round(success_rate, 2),
                "total_deliveries": len(self._delivery_history),
            }

    def create_price_alert_webhook(
        self,
        url: str,
        symbol: str,
        price_threshold: float,
        condition: str = "above",  # "above" or "below"
    ) -> WebhookConfig:
        """
        Create price alert webhook.

        Args:
            url: Webhook URL
            symbol: Cryptocurrency symbol
            price_threshold: Price threshold
            condition: "above" or "below"

        Returns:
            WebhookConfig
        """
        import secrets

        config = WebhookConfig(
            id=f"price_alert_{symbol.lower()}_{secrets.token_hex(8)}",
            url=url,
            events=[WebhookEvent.PRICE_CHANGE],
            headers={
                "X-Alert-Type": "price",
                "X-Symbol": symbol,
                "X-Threshold": str(price_threshold),
                "X-Condition": condition,
            },
        )

        self.register_webhook(config)
        return config

    def create_portfolio_alert_webhook(
        self,
        url: str,
        portfolio_id: str,
        alert_types: list[str],  # ["value_drop", "value_gain", "rebalance_needed"]
    ) -> WebhookConfig:
        """
        Create portfolio alert webhook.

        Args:
            url: Webhook URL
            portfolio_id: Portfolio identifier
            alert_types: List of alert types

        Returns:
            WebhookConfig
        """
        import secrets

        config = WebhookConfig(
            id=f"portfolio_alert_{portfolio_id}_{secrets.token_hex(8)}",
            url=url,
            events=[WebhookEvent.PORTFOLIO_ALERT],
            headers={
                "X-Alert-Type": "portfolio",
                "X-Portfolio-ID": portfolio_id,
                "X-Alert-Types": ",".join(alert_types),
            },
        )

        self.register_webhook(config)
        return config


# Global webhook manager instance
_global_webhook_manager: WebhookManager | None = None


def get_webhook_manager() -> WebhookManager:
    """Get global webhook manager instance."""
    global _global_webhook_manager
    if _global_webhook_manager is None:
        _global_webhook_manager = WebhookManager()
    return _global_webhook_manager


# Convenience functions
def register_price_webhook(url: str, symbol: str, threshold: float) -> str:
    """Quick function to register price webhook."""
    manager = get_webhook_manager()
    config = manager.create_price_alert_webhook(url, symbol, threshold)
    return config.id


def trigger_price_alert(symbol: str, price: float, change_percent: float) -> None:
    """Trigger price alert event."""
    manager = get_webhook_manager()
    manager.trigger_event(
        WebhookEvent.PRICE_CHANGE,
        {
            "symbol": symbol,
            "price": price,
            "change_percent": change_percent,
            "timestamp": datetime.now().isoformat(),
        },
    )
