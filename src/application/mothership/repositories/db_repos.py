from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models_billing import APIKeyRow, InvoiceRow, PaymentTransactionRow, SubscriptionRow, UsageRecordRow
from ..models.api_key import APIKey
from ..models.payment import (
    Invoice,
    PaymentGateway,
    PaymentStatus,
    PaymentTransaction,
    Subscription,
    SubscriptionStatus,
    SubscriptionTier,
)
from ..models.subscription import UsageRecord


def _row_to_api_key(row: APIKeyRow) -> APIKey:
    return APIKey(
        id=row.id,
        user_id=row.user_id,
        key_hash=row.key_hash,
        key_prefix=row.key_prefix,
        tier=SubscriptionTier(row.tier),
        name=row.name,
        last_used_at=row.last_used_at,
        expires_at=row.expires_at,
        is_active=row.is_active,
        metadata=row.meta or {},
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _api_key_to_row(entity: APIKey) -> APIKeyRow:
    return APIKeyRow(
        id=entity.id,
        user_id=entity.user_id,
        key_hash=entity.key_hash,
        key_prefix=entity.key_prefix,
        tier=entity.tier.value,
        name=entity.name,
        last_used_at=entity.last_used_at,
        expires_at=entity.expires_at,
        is_active=entity.is_active,
        meta=entity.metadata or {},
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


class DbAPIKeyRepository:
    def __init__(self, session: AsyncSession):
        self._db = session

    async def get(self, id: str) -> APIKey | None:
        row = await self._db.get(APIKeyRow, id)
        return _row_to_api_key(row) if row else None

    async def get_all(self) -> list[APIKey]:
        rows = (await self._db.execute(select(APIKeyRow))).scalars().all()
        return [_row_to_api_key(r) for r in rows]

    async def add(self, entity: APIKey) -> APIKey:
        self._db.add(_api_key_to_row(entity))
        return entity

    async def update(self, entity: APIKey) -> APIKey:
        row = await self._db.get(APIKeyRow, entity.id)
        if not row:
            raise ValueError(f"API key not found: {entity.id}")
        row.user_id = entity.user_id
        row.key_hash = entity.key_hash
        row.key_prefix = entity.key_prefix
        row.tier = entity.tier.value
        row.name = entity.name
        row.last_used_at = entity.last_used_at
        row.expires_at = entity.expires_at
        row.is_active = entity.is_active
        row.meta = entity.metadata or {}
        row.updated_at = datetime.now(UTC)
        return entity

    async def delete(self, id: str) -> bool:
        row = await self._db.get(APIKeyRow, id)
        if not row:
            return False
        await self._db.delete(row)
        return True

    async def exists(self, id: str) -> bool:
        return (await self._db.get(APIKeyRow, id)) is not None

    async def count(self) -> int:
        return int((await self._db.execute(select(func.count()).select_from(APIKeyRow))).scalar_one())

    async def get_by_user(self, user_id: str) -> list[APIKey]:
        rows = (await self._db.execute(select(APIKeyRow).where(APIKeyRow.user_id == user_id))).scalars().all()
        return [_row_to_api_key(r) for r in rows]

    async def get_by_key_hash(self, key_hash: str) -> APIKey | None:
        row = (await self._db.execute(select(APIKeyRow).where(APIKeyRow.key_hash == key_hash))).scalars().first()
        return _row_to_api_key(row) if row else None


def _row_to_usage(row: UsageRecordRow) -> UsageRecord:
    return UsageRecord(
        id=row.id,
        user_id=row.user_id,
        api_key_id=row.api_key_id,
        endpoint=row.endpoint,
        cost_units=row.cost_units,
        metadata=row.meta or {},
        timestamp=row.timestamp,
    )


class DbUsageRepository:
    def __init__(self, session: AsyncSession):
        self._db = session

    async def get(self, id: str) -> UsageRecord | None:
        row = await self._db.get(UsageRecordRow, id)
        return _row_to_usage(row) if row else None

    async def get_all(self) -> list[UsageRecord]:
        rows = (await self._db.execute(select(UsageRecordRow))).scalars().all()
        return [_row_to_usage(r) for r in rows]

    async def add(self, entity: UsageRecord) -> UsageRecord:
        self._db.add(
            UsageRecordRow(
                id=entity.id,
                user_id=entity.user_id,
                api_key_id=entity.api_key_id,
                endpoint=entity.endpoint,
                cost_units=entity.cost_units,
                meta=entity.metadata or {},
                timestamp=entity.timestamp,
            )
        )
        return entity

    async def update(self, entity: UsageRecord) -> UsageRecord:
        row = await self._db.get(UsageRecordRow, entity.id)
        if not row:
            raise ValueError(f"Usage record not found: {entity.id}")
        row.user_id = entity.user_id
        row.api_key_id = entity.api_key_id
        row.endpoint = entity.endpoint
        row.cost_units = entity.cost_units
        row.meta = entity.metadata or {}
        row.timestamp = entity.timestamp
        return entity

    async def delete(self, id: str) -> bool:
        row = await self._db.get(UsageRecordRow, id)
        if not row:
            return False
        await self._db.delete(row)
        return True

    async def exists(self, id: str) -> bool:
        return (await self._db.get(UsageRecordRow, id)) is not None

    async def count(self) -> int:
        return int((await self._db.execute(select(func.count()).select_from(UsageRecordRow))).scalar_one())

    async def get_by_user(
        self, user_id: str, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> list[UsageRecord]:
        stmt = select(UsageRecordRow).where(UsageRecordRow.user_id == user_id)
        if start_date:
            stmt = stmt.where(UsageRecordRow.timestamp >= start_date)
        if end_date:
            stmt = stmt.where(UsageRecordRow.timestamp <= end_date)
        rows = (await self._db.execute(stmt)).scalars().all()
        return [_row_to_usage(r) for r in rows]

    async def get_usage_by_endpoint(self, user_id: str, endpoint: str, period_days: int = 30) -> int:
        start_date = datetime.now(UTC) - timedelta(days=period_days)
        stmt = (
            select(func.coalesce(func.sum(UsageRecordRow.cost_units), 0))
            .where(UsageRecordRow.user_id == user_id)
            .where(UsageRecordRow.endpoint == endpoint)
            .where(UsageRecordRow.timestamp >= start_date)
        )
        return int((await self._db.execute(stmt)).scalar_one())

    async def get_total_usage(self, user_id: str, period_days: int = 30) -> dict[str, int]:
        start_date = datetime.now(UTC) - timedelta(days=period_days)
        rows = (
            (
                await self._db.execute(
                    select(UsageRecordRow)
                    .where(UsageRecordRow.user_id == user_id)
                    .where(UsageRecordRow.timestamp >= start_date)
                )
            )
            .scalars()
            .all()
        )
        usage: dict[str, int] = {}
        for row in rows:
            endpoint_type = row.endpoint.split("/")[0] if "/" in row.endpoint else row.endpoint
            usage[endpoint_type] = usage.get(endpoint_type, 0) + int(row.cost_units)
        return usage


def _row_to_payment(row: PaymentTransactionRow) -> PaymentTransaction:
    return PaymentTransaction(
        id=row.id,
        user_id=row.user_id,
        amount_cents=row.amount_cents,
        currency=row.currency,
        status=PaymentStatus(row.status),
        gateway=PaymentGateway(row.gateway),
        gateway_transaction_id=row.gateway_transaction_id,
        gateway_response=row.gateway_response or {},
        description=row.description,
        metadata=row.meta or {},
        idempotency_key=row.idempotency_key,
        created_at=row.created_at,
        updated_at=row.updated_at,
        completed_at=row.completed_at,
        failure_reason=row.failure_reason,
    )


class DbPaymentTransactionRepository:
    def __init__(self, session: AsyncSession):
        self._db = session

    async def get(self, id: str) -> PaymentTransaction | None:
        row = await self._db.get(PaymentTransactionRow, id)
        return _row_to_payment(row) if row else None

    async def get_all(self) -> list[PaymentTransaction]:
        rows = (await self._db.execute(select(PaymentTransactionRow))).scalars().all()
        return [_row_to_payment(r) for r in rows]

    async def add(self, entity: PaymentTransaction) -> PaymentTransaction:
        self._db.add(
            PaymentTransactionRow(
                id=entity.id,
                user_id=entity.user_id,
                amount_cents=entity.amount_cents,
                currency=entity.currency,
                status=entity.status.value,
                gateway=entity.gateway.value,
                gateway_transaction_id=entity.gateway_transaction_id,
                gateway_response=entity.gateway_response or {},
                description=entity.description,
                meta=entity.metadata or {},
                idempotency_key=entity.idempotency_key,
                created_at=entity.created_at,
                updated_at=entity.updated_at,
                completed_at=entity.completed_at,
                failure_reason=entity.failure_reason,
            )
        )
        return entity

    async def update(self, entity: PaymentTransaction) -> PaymentTransaction:
        row = await self._db.get(PaymentTransactionRow, entity.id)
        if not row:
            raise ValueError(f"Transaction not found: {entity.id}")
        row.user_id = entity.user_id
        row.amount_cents = entity.amount_cents
        row.currency = entity.currency
        row.status = entity.status.value
        row.gateway = entity.gateway.value
        row.gateway_transaction_id = entity.gateway_transaction_id
        row.gateway_response = entity.gateway_response or {}
        row.description = entity.description
        row.meta = entity.metadata or {}
        row.idempotency_key = entity.idempotency_key
        row.updated_at = datetime.now(UTC)
        row.completed_at = entity.completed_at
        row.failure_reason = entity.failure_reason
        return entity

    async def delete(self, id: str) -> bool:
        row = await self._db.get(PaymentTransactionRow, id)
        if not row:
            return False
        await self._db.delete(row)
        return True

    async def exists(self, id: str) -> bool:
        return (await self._db.get(PaymentTransactionRow, id)) is not None

    async def count(self) -> int:
        return int((await self._db.execute(select(func.count()).select_from(PaymentTransactionRow))).scalar_one())

    async def get_by_user(self, user_id: str) -> list[PaymentTransaction]:
        rows = (
            (await self._db.execute(select(PaymentTransactionRow).where(PaymentTransactionRow.user_id == user_id)))
            .scalars()
            .all()
        )
        return [_row_to_payment(r) for r in rows]

    async def get_by_status(self, status: PaymentStatus) -> list[PaymentTransaction]:
        rows = (
            (await self._db.execute(select(PaymentTransactionRow).where(PaymentTransactionRow.status == status.value)))
            .scalars()
            .all()
        )
        return [_row_to_payment(r) for r in rows]

    async def get_by_idempotency_key(self, idempotency_key: str) -> PaymentTransaction | None:
        row = (
            (
                await self._db.execute(
                    select(PaymentTransactionRow).where(PaymentTransactionRow.idempotency_key == idempotency_key)
                )
            )
            .scalars()
            .first()
        )
        return _row_to_payment(row) if row else None


def _row_to_subscription(row: SubscriptionRow) -> Subscription:
    return Subscription(
        id=row.id,
        user_id=row.user_id,
        tier=SubscriptionTier(row.tier),
        status=SubscriptionStatus(row.status),
        current_period_start=row.current_period_start,
        current_period_end=row.current_period_end,
        cancel_at_period_end=row.cancel_at_period_end,
        cancelled_at=row.cancelled_at,
        gateway=PaymentGateway(row.gateway),
        gateway_subscription_id=row.gateway_subscription_id,
        payment_method_id=row.payment_method_id,
        metadata=row.meta or {},
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class DbSubscriptionRepository:
    def __init__(self, session: AsyncSession):
        self._db = session

    async def get(self, id: str) -> Subscription | None:
        row = await self._db.get(SubscriptionRow, id)
        return _row_to_subscription(row) if row else None

    async def get_all(self) -> list[Subscription]:
        rows = (await self._db.execute(select(SubscriptionRow))).scalars().all()
        return [_row_to_subscription(r) for r in rows]

    async def add(self, entity: Subscription) -> Subscription:
        self._db.add(
            SubscriptionRow(
                id=entity.id,
                user_id=entity.user_id,
                tier=entity.tier.value,
                status=entity.status.value,
                current_period_start=entity.current_period_start,
                current_period_end=entity.current_period_end,
                cancel_at_period_end=entity.cancel_at_period_end,
                cancelled_at=entity.cancelled_at,
                gateway=entity.gateway.value,
                gateway_subscription_id=entity.gateway_subscription_id,
                payment_method_id=entity.payment_method_id,
                meta=entity.metadata or {},
                created_at=entity.created_at,
                updated_at=entity.updated_at,
            )
        )
        return entity

    async def update(self, entity: Subscription) -> Subscription:
        row = await self._db.get(SubscriptionRow, entity.id)
        if not row:
            raise ValueError(f"Subscription not found: {entity.id}")
        row.user_id = entity.user_id
        row.tier = entity.tier.value
        row.status = entity.status.value
        row.current_period_start = entity.current_period_start
        row.current_period_end = entity.current_period_end
        row.cancel_at_period_end = entity.cancel_at_period_end
        row.cancelled_at = entity.cancelled_at
        row.gateway = entity.gateway.value
        row.gateway_subscription_id = entity.gateway_subscription_id
        row.payment_method_id = entity.payment_method_id
        row.meta = entity.metadata or {}
        row.updated_at = datetime.now(UTC)
        return entity

    async def delete(self, id: str) -> bool:
        row = await self._db.get(SubscriptionRow, id)
        if not row:
            return False
        await self._db.delete(row)
        return True

    async def exists(self, id: str) -> bool:
        return (await self._db.get(SubscriptionRow, id)) is not None

    async def count(self) -> int:
        return int((await self._db.execute(select(func.count()).select_from(SubscriptionRow))).scalar_one())

    async def get_by_user(self, user_id: str) -> list[Subscription]:
        rows = (
            (await self._db.execute(select(SubscriptionRow).where(SubscriptionRow.user_id == user_id))).scalars().all()
        )
        return [_row_to_subscription(r) for r in rows]

    async def get_active_by_user(self, user_id: str) -> Subscription | None:
        row = (
            (
                await self._db.execute(
                    select(SubscriptionRow)
                    .where(SubscriptionRow.user_id == user_id)
                    .where(SubscriptionRow.status == SubscriptionStatus.ACTIVE.value)
                )
            )
            .scalars()
            .first()
        )
        return _row_to_subscription(row) if row else None

    async def get_by_tier(self, tier: SubscriptionTier) -> list[Subscription]:
        rows = (
            (await self._db.execute(select(SubscriptionRow).where(SubscriptionRow.tier == tier.value))).scalars().all()
        )
        return [_row_to_subscription(r) for r in rows]

    async def get_by_status(self, status: SubscriptionStatus) -> list[Subscription]:
        rows = (
            (await self._db.execute(select(SubscriptionRow).where(SubscriptionRow.status == status.value)))
            .scalars()
            .all()
        )
        return [_row_to_subscription(r) for r in rows]


def _row_to_invoice(row: InvoiceRow) -> Invoice:
    return Invoice(
        id=row.id,
        user_id=row.user_id,
        subscription_id=row.subscription_id,
        amount_cents=row.amount_cents,
        currency=row.currency,
        status=row.status,
        period_start=row.period_start,
        period_end=row.period_end,
        due_date=row.due_date,
        paid_at=row.paid_at,
        gateway_invoice_id=row.gateway_invoice_id,
        payment_transaction_id=row.payment_transaction_id,
        line_items=row.line_items or [],
        metadata=row.meta or {},
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class DbInvoiceRepository:
    def __init__(self, session: AsyncSession):
        self._db = session

    async def get(self, id: str) -> Invoice | None:
        row = await self._db.get(InvoiceRow, id)
        return _row_to_invoice(row) if row else None

    async def get_all(self) -> list[Invoice]:
        rows = (await self._db.execute(select(InvoiceRow))).scalars().all()
        return [_row_to_invoice(r) for r in rows]

    async def add(self, entity: Invoice) -> Invoice:
        self._db.add(
            InvoiceRow(
                id=entity.id,
                user_id=entity.user_id,
                subscription_id=entity.subscription_id,
                amount_cents=entity.amount_cents,
                currency=entity.currency,
                status=entity.status,
                period_start=entity.period_start,
                period_end=entity.period_end,
                due_date=entity.due_date,
                paid_at=entity.paid_at,
                gateway_invoice_id=entity.gateway_invoice_id,
                payment_transaction_id=entity.payment_transaction_id,
                line_items=entity.line_items or [],
                meta=entity.metadata or {},
                created_at=entity.created_at,
                updated_at=entity.updated_at,
            )
        )
        return entity

    async def update(self, entity: Invoice) -> Invoice:
        row = await self._db.get(InvoiceRow, entity.id)
        if not row:
            raise ValueError(f"Invoice not found: {entity.id}")
        row.user_id = entity.user_id
        row.subscription_id = entity.subscription_id
        row.amount_cents = entity.amount_cents
        row.currency = entity.currency
        row.status = entity.status
        row.period_start = entity.period_start
        row.period_end = entity.period_end
        row.due_date = entity.due_date
        row.paid_at = entity.paid_at
        row.gateway_invoice_id = entity.gateway_invoice_id
        row.payment_transaction_id = entity.payment_transaction_id
        row.line_items = entity.line_items or []
        row.meta = entity.metadata or {}
        row.updated_at = datetime.now(UTC)
        return entity

    async def delete(self, id: str) -> bool:
        row = await self._db.get(InvoiceRow, id)
        if not row:
            return False
        await self._db.delete(row)
        return True

    async def exists(self, id: str) -> bool:
        return (await self._db.get(InvoiceRow, id)) is not None

    async def count(self) -> int:
        return int((await self._db.execute(select(func.count()).select_from(InvoiceRow))).scalar_one())

    async def get_by_user(self, user_id: str) -> list[Invoice]:
        rows = (await self._db.execute(select(InvoiceRow).where(InvoiceRow.user_id == user_id))).scalars().all()
        return [_row_to_invoice(r) for r in rows]

    async def get_by_subscription(self, subscription_id: str) -> list[Invoice]:
        rows = (
            (await self._db.execute(select(InvoiceRow).where(InvoiceRow.subscription_id == subscription_id)))
            .scalars()
            .all()
        )
        return [_row_to_invoice(r) for r in rows]
