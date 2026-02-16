"""Asynchronous bridge between the legal agent and the accounting department.

Messages are exchanged via the unified-fabric event bus so that the legal
agent and accounting services remain decoupled.  The bridge supports
request-reply for synchronous needs (e.g. budget approval) and
fire-and-forget for notifications (e.g. compliance-cost reporting).
"""

from __future__ import annotations

import logging
from typing import Any

from .models import AccountingEventType, AccountingMessage

logger = logging.getLogger(__name__)


class AccountingBridge:
    """Async interface between the legal agent and accounting services.

    Uses the unified-fabric ``DynamicEventBus`` when available, falling
    back to an in-memory queue for testing and offline operation.
    """

    def __init__(self) -> None:
        self._outbox: list[AccountingMessage] = []
        self._inbox: list[AccountingMessage] = []
        self._event_bus: Any | None = None

    def connect_event_bus(self, event_bus: Any) -> None:
        """Attach the unified-fabric event bus for cross-service messaging."""
        self._event_bus = event_bus
        logger.info("accounting_bridge_connected_to_event_bus")

    # -- Sending messages to accounting --------------------------------------

    async def send_message(self, message: AccountingMessage) -> None:
        """Dispatch a message to the accounting department.

        If an event bus is connected the message is published as a
        ``legal.accounting.*`` event.  Otherwise it is stored in the
        local outbox for later retrieval.
        """
        self._outbox.append(message)

        if self._event_bus is not None:
            await self._publish_to_bus(message)
        else:
            logger.info(
                "accounting_message_queued_locally",
                extra={"message_id": message.message_id, "type": message.event_type.value},
            )

    async def notify_compliance_cost(
        self,
        subject: str,
        amount: float,
        currency: str = "USD",
        user_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AccountingMessage:
        """Convenience: send a compliance-cost notification."""
        msg = AccountingMessage(
            event_type=AccountingEventType.COMPLIANCE_COST,
            subject=subject,
            amount=amount,
            currency=currency,
            user_id=user_id,
            details=details or {},
        )
        await self.send_message(msg)
        return msg

    async def notify_penalty_risk(
        self,
        subject: str,
        estimated_amount: float,
        currency: str = "USD",
        details: dict[str, Any] | None = None,
    ) -> AccountingMessage:
        """Convenience: alert accounting about a potential penalty."""
        msg = AccountingMessage(
            event_type=AccountingEventType.PENALTY_RISK,
            subject=subject,
            amount=estimated_amount,
            currency=currency,
            details=details or {},
            requires_response=True,
        )
        await self.send_message(msg)
        return msg

    async def request_audit(
        self,
        subject: str,
        details: dict[str, Any] | None = None,
    ) -> AccountingMessage:
        """Request an audit from the accounting department."""
        msg = AccountingMessage(
            event_type=AccountingEventType.AUDIT_REQUEST,
            subject=subject,
            details=details or {},
            requires_response=True,
        )
        await self.send_message(msg)
        return msg

    async def notify_tax_obligation(
        self,
        subject: str,
        amount: float,
        currency: str = "USD",
        user_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AccountingMessage:
        """Notify accounting about a tax obligation."""
        msg = AccountingMessage(
            event_type=AccountingEventType.TAX_OBLIGATION,
            subject=subject,
            amount=amount,
            currency=currency,
            user_id=user_id,
            details=details or {},
        )
        await self.send_message(msg)
        return msg

    # -- Receiving messages from accounting ----------------------------------

    async def receive_message(self, message: AccountingMessage) -> None:
        """Handle an inbound message from the accounting department."""
        self._inbox.append(message)
        logger.info(
            "accounting_message_received",
            extra={"message_id": message.message_id, "type": message.event_type.value},
        )

    # -- Query helpers -------------------------------------------------------

    def get_outbox(self) -> list[AccountingMessage]:
        """Return all messages sent to accounting (most recent last)."""
        return list(self._outbox)

    def get_inbox(self) -> list[AccountingMessage]:
        """Return all messages received from accounting."""
        return list(self._inbox)

    def get_pending_responses(self) -> list[AccountingMessage]:
        """Return outbox messages that require a response but haven't received one."""
        responded_ids = {m.correlation_id for m in self._inbox if m.correlation_id}
        return [m for m in self._outbox if m.requires_response and m.message_id not in responded_ids]

    # -- Event bus integration -----------------------------------------------

    async def _publish_to_bus(self, message: AccountingMessage) -> None:
        """Publish an accounting message as a unified-fabric event."""
        try:
            from unified_fabric import Event

            event = Event(
                event_type=f"legal.accounting.{message.event_type.value}",
                payload=message.model_dump(mode="json"),
                source_domain="grid",
                target_domains=["grid"],
            )
            await self._event_bus.publish(event)
            logger.info(
                "accounting_message_published",
                extra={"message_id": message.message_id, "event_type": event.event_type},
            )
        except Exception:
            logger.exception("accounting_bridge_publish_failed", extra={"message_id": message.message_id})
