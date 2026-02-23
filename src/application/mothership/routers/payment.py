"""
Payment API router.

Endpoints for payment processing, subscriptions, and billing.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..dependencies import RequiredAuth, Settings, UoW
from ..exceptions import IntegrationError, ResourceNotFoundError
from ..models.payment import PaymentGateway as PaymentGatewayEnum
from ..models.payment import (
    PaymentStatus,
    PaymentTransaction,
    PaymentWebhookEvent,
    Subscription,
    SubscriptionStatus,
    SubscriptionTier,
    WebhookEventStatus,
)
from ..schemas.payment import (
    CancelSubscriptionRequest,
    CreatePaymentRequest,
    CreatePaymentResponse,
    CreateSubscriptionRequest,
    PaymentTransactionResponse,
    RefundPaymentRequest,
    RefundResponse,
    SubscriptionResponse,
)
from ..services.payment import PaymentGateway as PaymentGatewayBase
from ..services.payment import PaymentReconciliationService, StripeGateway

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payment", tags=["payment"])


# =============================================================================
# Dependency Injection
# =============================================================================


def get_payment_gateway(settings: Settings) -> PaymentGatewayBase:
    """
    Get the configured payment gateway instance.

    Args:
        settings: Application settings

    Returns:
        Payment gateway instance
    """
    gateway_name = settings.payment.default_gateway.lower()

    if gateway_name == "stripe":
        if not settings.payment.stripe_enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Stripe payment gateway is not enabled",
            )
        return StripeGateway(
            secret_key=settings.payment.stripe_secret_key,
            webhook_secret=settings.payment.stripe_webhook_secret,
            publishable_key=settings.payment.stripe_publishable_key,
        )
    elif gateway_name == "bkash":
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="bKash integration has been decommissioned. Please use Stripe.",
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unknown or unsupported payment gateway: {gateway_name}",
        )


# =============================================================================
# Payment Helpers
# =============================================================================


def _resolve_expected_livemode(settings: Settings) -> bool | None:
    """Resolve expected Stripe livemode from configuration."""
    payment_settings = getattr(settings, "payment", None)
    mode = str(getattr(payment_settings, "stripe_livemode_enforcement", "auto")).strip().lower()
    if mode == "off":
        return None
    if mode == "live":
        return True
    if mode == "test":
        return False
    # auto mode
    if hasattr(settings, "is_production"):
        return bool(settings.is_production)
    return None


def _is_pending_like(status: PaymentStatus) -> bool:
    return status in {PaymentStatus.PENDING, PaymentStatus.PROCESSING}


# =============================================================================
# Payment Endpoints
# =============================================================================


@router.post("/create", response_model=CreatePaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    request: CreatePaymentRequest,
    auth: RequiredAuth,
    settings: Settings,
    uow: UoW,
    gateway: PaymentGatewayBase = Depends(get_payment_gateway),
):
    """
    Create a payment transaction.

    Creates a payment intent with the configured payment gateway.
    """
    try:
        import uuid

        # Check for duplicate idempotency key
        idempotency_key_from_request = request.metadata.get("idempotency_key") if request.metadata else None
        idempotency_key: str = (
            idempotency_key_from_request if isinstance(idempotency_key_from_request, str) else str(uuid.uuid4())
        )
        if idempotency_key:
            existing = await uow.payment_transactions.get_by_idempotency_key(idempotency_key)
            if existing:
                return CreatePaymentResponse(
                    transaction=PaymentTransactionResponse(**existing.to_dict()),
                    client_secret=(
                        existing.gateway_response.get("client_secret")
                        if hasattr(existing, "gateway_response")
                        else None
                    ),
                    payment_url=(
                        existing.gateway_response.get("payment_url") if hasattr(existing, "gateway_response") else None
                    ),
                )

        # Create payment with gateway
        gateway_result = await gateway.create_payment(
            amount_cents=request.amount_cents,
            currency=request.currency,
            description=request.description,
            metadata=request.metadata,
            idempotency_key=idempotency_key,
        )

        # Create transaction record
        user_id = auth.get("user_id", "unknown")
        transaction = PaymentTransaction(
            user_id=user_id,
            amount_cents=request.amount_cents,
            currency=request.currency,
            status=PaymentStatus.PENDING,
            gateway=PaymentGatewayEnum(settings.payment.default_gateway.lower()),
            gateway_transaction_id=gateway_result.get("gateway_transaction_id"),
            gateway_response=gateway_result,
            description=request.description,
            metadata=request.metadata or {},
            idempotency_key=idempotency_key,
        )

        async with uow.transaction():
            await uow.payment_transactions.add(transaction)

        return CreatePaymentResponse(
            transaction=PaymentTransactionResponse(**transaction.to_dict()),
            client_secret=gateway_result.get("client_secret"),
            payment_url=gateway_result.get("payment_url"),
        )
    except IntegrationError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Payment gateway error: {e.message}",
        ) from e
    except Exception as e:
        logger.exception("Payment creation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment creation failed: {str(e)}",
        ) from e


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def payment_webhook(
    request: Request,
    settings: Settings,
    uow: UoW,
    gateway: PaymentGatewayBase = Depends(get_payment_gateway),
):
    """
    Handle payment webhook events from payment gateway.

    Verifies webhook signature and processes payment status updates.
    """
    try:
        signature = request.headers.get("stripe-signature") or request.headers.get("x-bkash-signature")
        if not signature:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing webhook signature",
            )

        payload = await request.body()

        # Verify and parse webhook
        event = await gateway.verify_webhook(signature, payload)

        # Enforce Stripe livemode consistency to avoid test/live cross-contamination.
        if gateway.get_name() == "stripe":
            expected_livemode = _resolve_expected_livemode(settings)
            event_livemode = event.get("livemode")
            if (
                expected_livemode is not None
                and isinstance(event_livemode, bool)
                and event_livemode != expected_livemode
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Stripe webhook livemode mismatch: expected {'live' if expected_livemode else 'test'} "
                        f"but received {'live' if event_livemode else 'test'}"
                    ),
                )

        event_id = str(event.get("id") or "").strip()
        if not event_id:
            event_id = hashlib.sha256(payload).hexdigest()

        event_type = str(event.get("type") or event.get("statusCode", ""))
        success_events = {"payment_intent.succeeded", "checkout.session.completed"}
        failure_events = {"payment_intent.payment_failed", "payment_intent.canceled", "payment_intent.cancelled"}

        gateway_name = gateway.get_name()
        existing_event = await uow.webhook_events.get_by_gateway_event_id(event_id, gateway=gateway_name)
        if existing_event and existing_event.status in {WebhookEventStatus.PROCESSED, WebhookEventStatus.IGNORED}:
            return {
                "processed": True,
                "duplicate": True,
                "event_id": event_id,
                "event_type": existing_event.event_type or event_type,
            }

        webhook_event = existing_event or PaymentWebhookEvent(
            gateway=PaymentGatewayEnum(gateway_name),
            gateway_event_id=event_id,
            event_type=event_type,
            status=WebhookEventStatus.RECEIVED,
            signature_hash=hashlib.sha256(signature.encode("utf-8")).hexdigest(),
            payload_hash=hashlib.sha256(payload).hexdigest(),
        )

        data = event.get("data", {})
        event_data = data.get("object", data) if isinstance(data, dict) else {}
        gateway_transaction_id = (
            event_data.get("payment_intent") or event_data.get("id") or event_data.get("paymentID")
            if isinstance(event_data, dict)
            else None
        )
        if gateway_transaction_id:
            webhook_event.gateway_transaction_id = gateway_transaction_id

        if event_type not in success_events and event_type not in failure_events:
            webhook_event.mark_ignored()
            async with uow.transaction():
                if existing_event:
                    await uow.webhook_events.update(webhook_event)
                else:
                    await uow.webhook_events.add(webhook_event)
            return {
                "processed": False,
                "event_id": event_id,
                "event_type": event_type,
                "reason": "ignored_non_terminal_event",
            }

        if not gateway_transaction_id:
            webhook_event.mark_failed("missing_transaction_reference")
            async with uow.transaction():
                if existing_event:
                    await uow.webhook_events.update(webhook_event)
                else:
                    await uow.webhook_events.add(webhook_event)
            return {
                "processed": False,
                "event_id": event_id,
                "event_type": event_type,
                "reason": "missing_transaction_reference",
            }

        # Find transaction
        transactions = await uow.payment_transactions.get_all()
        transaction = next(
            (t for t in transactions if t.gateway_transaction_id == gateway_transaction_id),
            None,
        )
        if not transaction:
            webhook_event.mark_failed("transaction_not_found")
            async with uow.transaction():
                if existing_event:
                    await uow.webhook_events.update(webhook_event)
                else:
                    await uow.webhook_events.add(webhook_event)
            return {
                "processed": False,
                "event_id": event_id,
                "event_type": event_type,
                "reason": "transaction_not_found",
            }

        if event_type in success_events:
            transaction.mark_completed(gateway_transaction_id)
        else:
            transaction.mark_failed(f"Gateway reported event: {event_type}")

        webhook_event.mark_processed(payment_transaction_id=transaction.id)

        async with uow.transaction():
            await uow.payment_transactions.update(transaction)
            if existing_event:
                await uow.webhook_events.update(webhook_event)
            else:
                await uow.webhook_events.add(webhook_event)

        return {"processed": True, "duplicate": False, "event_id": event_id, "event_type": event_type}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid webhook: {str(e)}",
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Webhook processing failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}",
        ) from e


@router.get("/transaction/{transaction_id}", response_model=PaymentTransactionResponse)
async def get_transaction(
    transaction_id: str,
    auth: RequiredAuth,
    uow: UoW,
):
    """Get payment transaction details."""
    transaction = await uow.payment_transactions.get(transaction_id)
    if not transaction:
        raise ResourceNotFoundError("transaction", transaction_id)

    user_id = auth.get("user_id", "unknown")
    if transaction.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return PaymentTransactionResponse(**transaction.to_dict())


@router.post("/refund", response_model=RefundResponse, status_code=status.HTTP_201_CREATED)
async def refund_payment(
    request: RefundPaymentRequest,
    auth: RequiredAuth,
    settings: Settings,
    uow: UoW,
    gateway: PaymentGatewayBase = Depends(get_payment_gateway),
):
    """Refund a payment (full or partial)."""
    transaction = await uow.payment_transactions.get(request.transaction_id)
    if not transaction:
        raise ResourceNotFoundError("transaction", request.transaction_id)

    user_id = auth.get("user_id", "unknown")
    if transaction.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    if not transaction.gateway_transaction_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction has no gateway transaction ID",
        )

    try:
        refund_result = await gateway.refund(
            gateway_transaction_id=transaction.gateway_transaction_id,
            amount_cents=request.amount_cents,
            reason=request.reason,
        )

        # Update transaction status
        transaction.status = PaymentStatus.REFUNDED
        async with uow.transaction():
            await uow.payment_transactions.update(transaction)

        return RefundResponse(
            refund_id=refund_result.get("gateway_refund_id", ""),
            transaction_id=transaction.id,
            amount_cents=refund_result.get("amount", request.amount_cents or transaction.amount_cents),
            status=refund_result.get("status", "completed"),
            created_at=datetime.now(UTC),
        )
    except IntegrationError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Refund failed: {e.message}",
        ) from e


@router.post("/reconciliation/run", status_code=status.HTTP_200_OK)
async def run_reconciliation(
    auth: RequiredAuth,
    settings: Settings,
    uow: UoW,
    gateway: PaymentGatewayBase = Depends(get_payment_gateway),
):
    """Trigger an immediate payment reconciliation run."""
    _ = auth
    service = PaymentReconciliationService(uow=uow, gateway=gateway)
    async with uow.transaction():
        result = await service.run_once(lookback_hours=settings.payment.reconciliation_lookback_hours)
    return result


@router.get("/reconciliation/runs", status_code=status.HTTP_200_OK)
async def list_reconciliation_runs(
    auth: RequiredAuth,
    uow: UoW,
    limit: int = 20,
):
    """List recent reconciliation runs for accounting visibility."""
    _ = auth
    if hasattr(uow.reconciliation_runs, "get_recent"):
        runs = await uow.reconciliation_runs.get_recent(limit=max(1, min(limit, 200)))
    else:
        all_runs = await uow.reconciliation_runs.get_all()
        runs = sorted(all_runs, key=lambda run: run.started_at, reverse=True)[: max(1, min(limit, 200))]
    return [run.to_dict() for run in runs]


@router.get("/reconciliation/stuck-pending", status_code=status.HTTP_200_OK)
async def list_stuck_pending_payments(
    auth: RequiredAuth,
    uow: UoW,
    older_than_minutes: int = 30,
    limit: int = 200,
):
    """Report pending/processing transactions older than threshold."""
    _ = auth
    threshold_minutes = max(1, min(older_than_minutes, 60 * 24 * 30))
    max_limit = max(1, min(limit, 1000))
    cutoff = datetime.now(UTC) - timedelta(minutes=threshold_minutes)

    transactions = await uow.payment_transactions.get_all()
    stuck = [tx for tx in transactions if _is_pending_like(tx.status) and tx.created_at <= cutoff]
    stuck.sort(key=lambda tx: tx.created_at)
    stuck = stuck[:max_limit]

    return {
        "threshold_minutes": threshold_minutes,
        "count": len(stuck),
        "transactions": [
            {
                "transaction_id": tx.id,
                "user_id": tx.user_id,
                "status": tx.status.value,
                "gateway": tx.gateway.value,
                "amount_cents": tx.amount_cents,
                "currency": tx.currency,
                "gateway_transaction_id": tx.gateway_transaction_id,
                "created_at": tx.created_at.isoformat(),
                "updated_at": tx.updated_at.isoformat(),
            }
            for tx in stuck
        ],
    }


# =============================================================================
# Subscription Endpoints
# =============================================================================


@router.post("/subscription/create", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    request: CreateSubscriptionRequest,
    auth: RequiredAuth,
    settings: Settings,
    uow: UoW,
    gateway: PaymentGatewayBase = Depends(get_payment_gateway),
):
    """Create a subscription."""
    try:
        user_id = auth.get("user_id", "unknown")
        gateway_result = await gateway.create_subscription(
            user_id=user_id,
            tier=request.tier.value,
            payment_method_id=request.payment_method_id,
            metadata=request.metadata,
        )

        # Calculate period dates
        now = datetime.now(UTC)
        period_end = now + timedelta(days=settings.billing.billing_cycle_days)

        subscription = Subscription(
            user_id=user_id,
            tier=SubscriptionTier[request.tier.value.upper()],
            status=SubscriptionStatus.ACTIVE,
            current_period_start=now,
            current_period_end=period_end,
            gateway=PaymentGatewayEnum(settings.payment.default_gateway.lower()),
            gateway_subscription_id=gateway_result.get("gateway_subscription_id"),
            payment_method_id=request.payment_method_id,
            metadata={
                **(request.metadata or {}),
                "stripe_customer_id": gateway_result.get("stripe_customer_id"),
                "stripe_price_id": gateway_result.get("stripe_price_id"),
            },
        )

        async with uow.transaction():
            await uow.subscriptions.add(subscription)

        return SubscriptionResponse(**subscription.to_dict())
    except IntegrationError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Subscription creation failed: {e.message}",
        ) from e


@router.post("/subscription/cancel", response_model=SubscriptionResponse)
async def cancel_subscription(
    request: CancelSubscriptionRequest,
    auth: RequiredAuth,
    uow: UoW,
    gateway: PaymentGatewayBase = Depends(get_payment_gateway),
):
    """Cancel a subscription."""
    user_id = auth.get("user_id", "unknown")
    subscription = await uow.subscriptions.get(request.subscription_id)
    if not subscription:
        raise ResourceNotFoundError("subscription", request.subscription_id)

    if subscription.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    if not subscription.gateway_subscription_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subscription has no gateway subscription ID",
        )

    try:
        cancelled = await gateway.cancel_subscription(
            gateway_subscription_id=subscription.gateway_subscription_id,
            immediately=request.immediately,
        )
        if not cancelled:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Gateway failed to cancel subscription",
            )

        if request.immediately:
            subscription.mark_cancelled()
        else:
            subscription.cancel()

        async with uow.transaction():
            await uow.subscriptions.update(subscription)

        return SubscriptionResponse(**subscription.to_dict())
    except IntegrationError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Subscription cancellation failed: {e.message}",
        ) from e


@router.get("/subscription/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: str,
    auth: RequiredAuth,
    uow: UoW,
):
    """Get subscription details."""
    user_id = auth.get("user_id", "unknown")
    subscription = await uow.subscriptions.get(subscription_id)
    if not subscription:
        raise ResourceNotFoundError("subscription", subscription_id)

    if subscription.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return SubscriptionResponse(**subscription.to_dict())


@router.get("/subscriptions", response_model=list[SubscriptionResponse])
async def list_subscriptions(
    auth: RequiredAuth,
    uow: UoW,
):
    """List all subscriptions for the current user."""
    user_id = auth.get("user_id", "unknown")
    subscriptions = await uow.subscriptions.get_by_user(user_id)
    return [SubscriptionResponse(**sub.to_dict()) for sub in subscriptions]
