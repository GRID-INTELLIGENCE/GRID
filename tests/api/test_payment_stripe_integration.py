"""Tests for Stripe payment router and gateway behavior."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from application.mothership.config import PaymentSettings
from application.mothership.exceptions import IntegrationError
from application.mothership.models.payment import (
    PaymentReconciliationRun,
    PaymentStatus,
    PaymentTransaction,
    PaymentWebhookEvent,
    Subscription,
    SubscriptionTier,
    WebhookEventStatus,
)
from application.mothership.routers.payment import (
    cancel_subscription,
    get_payment_gateway,
    list_stuck_pending_payments,
    payment_webhook,
)
from application.mothership.schemas.payment import CancelSubscriptionRequest
from application.mothership.services.payment import PaymentReconciliationService
from application.mothership.services.payment import stripe_gateway as stripe_gateway_module


class _StubPaymentRepo:
    def __init__(self):
        self._tx = {}

    async def get_all(self):
        return list(self._tx.values())

    async def update(self, transaction):
        self._tx[transaction.id] = transaction


class _StubWebhookRepo:
    def __init__(self):
        self._events = {}

    async def get_by_gateway_event_id(self, gateway_event_id: str, gateway: str | None = None):
        for event in self._events.values():
            if event.gateway_event_id != gateway_event_id:
                continue
            if gateway and event.gateway.value != gateway:
                continue
            return event
        return None

    async def add(self, event: PaymentWebhookEvent):
        self._events[event.id] = event

    async def update(self, event: PaymentWebhookEvent):
        self._events[event.id] = event


class _StubReconciliationRepo:
    def __init__(self):
        self._runs = {}

    async def add(self, run: PaymentReconciliationRun):
        self._runs[run.id] = run

    async def get_all(self):
        return list(self._runs.values())

    async def get_recent(self, limit: int = 20):
        runs = list(self._runs.values())
        runs.sort(key=lambda run: run.started_at, reverse=True)
        return runs[:limit]


class _StubSubscriptionRepo:
    def __init__(self, subscription: Subscription):
        self._subscription = subscription
        self.updated = False

    async def get(self, _id: str):
        return self._subscription

    async def update(self, subscription: Subscription):
        self._subscription = subscription
        self.updated = True


class _StubUoW:
    def __init__(self, subscriptions: _StubSubscriptionRepo | None = None):
        self.payment_transactions = _StubPaymentRepo()
        self.webhook_events = _StubWebhookRepo()
        self.reconciliation_runs = _StubReconciliationRepo()
        self.subscriptions = subscriptions

    @asynccontextmanager
    async def transaction(self):
        yield self


class _StubGateway:
    def __init__(self, event: dict, cancel_result: bool = True):
        self._event = event
        self._cancel_result = cancel_result

    async def verify_webhook(self, signature: str, payload: bytes):
        assert signature
        assert payload
        return self._event

    async def cancel_subscription(self, gateway_subscription_id: str, immediately: bool = False) -> bool:
        assert gateway_subscription_id
        return self._cancel_result

    def get_name(self) -> str:
        return "stripe"


class _StubStatusGateway(_StubGateway):
    def __init__(self, status: PaymentStatus):
        super().__init__(event={})
        self._status = status

    async def get_transaction_status(self, gateway_transaction_id: str) -> PaymentStatus:
        assert gateway_transaction_id
        return self._status

    def get_name(self) -> str:
        return "stripe"


def _request_with_signature(body: bytes) -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "headers": [(b"stripe-signature", b"sig")],
    }
    sent = False

    async def receive():
        nonlocal sent
        if sent:
            return {"type": "http.request", "body": b"", "more_body": False}
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    return Request(scope, receive)


class TestPaymentSettingsValidation:
    def test_requires_stripe_prices_when_enabled(self):
        settings = PaymentSettings(
            stripe_enabled=True,
            stripe_secret_key="sk_test_123",
            stripe_webhook_secret="whsec_123",
            stripe_price_starter="",
            stripe_price_professional="",
            stripe_price_enterprise="",
            default_gateway="stripe",
        )
        issues = settings.validate()
        assert any("STRIPE_PRICE_STARTER" in issue for issue in issues)
        assert any("STRIPE_PRICE_PROFESSIONAL" in issue for issue in issues)
        assert any("STRIPE_PRICE_ENTERPRISE" in issue for issue in issues)


class TestGatewaySelection:
    def test_bkash_gateway_is_rejected(self):
        payment = SimpleNamespace(
            default_gateway="bkash",
            stripe_enabled=False,
            stripe_secret_key="",
            stripe_webhook_secret="",
            stripe_publishable_key="",
            stripe_price_starter="",
            stripe_price_professional="",
            stripe_price_enterprise="",
            stripe_customer_creation_enabled=True,
        )
        settings = SimpleNamespace(payment=payment)

        with pytest.raises(HTTPException) as exc:
            get_payment_gateway(settings)

        assert exc.value.status_code == 410


class TestWebhookProcessing:
    @pytest.mark.asyncio
    async def test_non_terminal_event_is_ignored(self):
        request = _request_with_signature(b'{"id":"evt_1"}')
        uow = _StubUoW()
        gateway = _StubGateway(event={"id": "evt_1", "type": "payment_intent.processing", "data": {"id": "pi_123"}})

        result = await payment_webhook(request=request, settings=SimpleNamespace(), uow=uow, gateway=gateway)

        assert result["processed"] is False
        assert result["reason"] == "ignored_non_terminal_event"

    @pytest.mark.asyncio
    async def test_duplicate_event_is_short_circuited(self):
        request = _request_with_signature(b'{"id":"evt_dup"}')
        uow = _StubUoW()
        existing = PaymentWebhookEvent(
            gateway_event_id="evt_dup",
            event_type="payment_intent.succeeded",
            status=WebhookEventStatus.PROCESSED,
        )
        await uow.webhook_events.add(existing)
        gateway = _StubGateway(event={"id": "evt_dup", "type": "payment_intent.succeeded", "data": {"id": "pi_123"}})

        result = await payment_webhook(request=request, settings=SimpleNamespace(), uow=uow, gateway=gateway)

        assert result["processed"] is True
        assert result["duplicate"] is True




    @pytest.mark.asyncio
    async def test_livemode_mismatch_is_rejected(self):
        request = _request_with_signature(b'{"id":"evt_live"}')
        uow = _StubUoW()
        gateway = _StubGateway(
            event={"id": "evt_live", "type": "payment_intent.processing", "livemode": False, "data": {"id": "pi_123"}}
        )
        settings = SimpleNamespace(
            is_production=True,
            payment=SimpleNamespace(stripe_livemode_enforcement="auto"),
        )

        with pytest.raises(HTTPException) as exc:
            await payment_webhook(request=request, settings=settings, uow=uow, gateway=gateway)

        assert exc.value.status_code == 400
        assert "livemode mismatch" in str(exc.value.detail).lower()


class TestCancelSubscription:
    @pytest.mark.asyncio
    async def test_gateway_cancel_failure_returns_502(self):
        subscription = Subscription(
            user_id="user_1",
            tier=SubscriptionTier.STARTER,
            gateway_subscription_id="sub_123",
        )
        sub_repo = _StubSubscriptionRepo(subscription)
        uow = _StubUoW(subscriptions=sub_repo)

        with pytest.raises(HTTPException) as exc:
            await cancel_subscription(
                request=CancelSubscriptionRequest(subscription_id=subscription.id, immediately=True),
                auth={"user_id": "user_1"},
                uow=uow,
                gateway=_StubGateway(event={}, cancel_result=False),
            )

        assert exc.value.status_code == 502
        assert sub_repo.updated is False


class TestReconciliation:
    @pytest.mark.asyncio
    async def test_auto_reconcile_pending_transaction(self):
        tx = PaymentTransaction(
            user_id="user_1",
            amount_cents=1000,
            status=PaymentStatus.PENDING,
            gateway_transaction_id="pi_123",
        )
        uow = _StubUoW()
        uow.payment_transactions._tx[tx.id] = tx
        gateway = _StubStatusGateway(status=PaymentStatus.COMPLETED)

        service = PaymentReconciliationService(uow=uow, gateway=gateway)
        result = await service.run_once(lookback_hours=24)

        assert result["mismatched_transactions"] == 1
        assert result["auto_reconciled_transactions"] == 1
        assert uow.payment_transactions._tx[tx.id].status == PaymentStatus.COMPLETED
        assert len(uow.reconciliation_runs._runs) == 1


class TestStripeGateway:
    @pytest.mark.asyncio
    async def test_create_subscription_missing_price_id_raises_integration_error(self, monkeypatch):
        class _FakeStripe:
            class error:
                class StripeError(Exception):
                    pass

                class SignatureVerificationError(Exception):
                    pass

        monkeypatch.setattr(stripe_gateway_module, "stripe", _FakeStripe())
        gateway = stripe_gateway_module.StripeGateway(
            secret_key="sk_test_123",
            webhook_secret="whsec_123",
            price_starter="",
            price_professional="",
            price_enterprise="",
        )

        with pytest.raises(IntegrationError):
            await gateway.create_subscription(user_id="u1", tier="starter")


class TestStuckPendingReport:
    @pytest.mark.asyncio
    async def test_reports_only_old_pending_transactions(self):
        old_pending = PaymentTransaction(
            user_id="user_1",
            amount_cents=1000,
            status=PaymentStatus.PENDING,
            gateway_transaction_id="pi_old",
            created_at=datetime.now(UTC) - timedelta(minutes=90),
            updated_at=datetime.now(UTC) - timedelta(minutes=90),
        )
        new_pending = PaymentTransaction(
            user_id="user_1",
            amount_cents=2000,
            status=PaymentStatus.PENDING,
            gateway_transaction_id="pi_new",
            created_at=datetime.now(UTC) - timedelta(minutes=5),
            updated_at=datetime.now(UTC) - timedelta(minutes=5),
        )
        completed = PaymentTransaction(
            user_id="user_1",
            amount_cents=3000,
            status=PaymentStatus.COMPLETED,
            gateway_transaction_id="pi_done",
            created_at=datetime.now(UTC) - timedelta(minutes=180),
            updated_at=datetime.now(UTC) - timedelta(minutes=180),
        )

        uow = _StubUoW()
        uow.payment_transactions._tx[old_pending.id] = old_pending
        uow.payment_transactions._tx[new_pending.id] = new_pending
        uow.payment_transactions._tx[completed.id] = completed

        result = await list_stuck_pending_payments(
            auth={"user_id": "user_1"},
            uow=uow,
            older_than_minutes=30,
            limit=100,
        )

        assert result["count"] == 1
        assert result["transactions"][0]["transaction_id"] == old_pending.id
