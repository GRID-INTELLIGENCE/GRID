"""
Payment repositories.

Repository implementations for payment-related entities using in-memory StateStore.
Will be migrated to database in Phase 2.
"""

from __future__ import annotations

import logging

from ..models.payment import (
    Invoice,
    PaymentStatus,
    PaymentTransaction,
    Subscription,
    SubscriptionStatus,
    SubscriptionTier,
)
from . import BaseRepository, StateStore, get_state_store

logger = logging.getLogger(__name__)


class PaymentTransactionRepository(BaseRepository[PaymentTransaction]):
    """Repository for payment transactions."""

    def __init__(self, store: StateStore | None = None):
        self._store = store or get_state_store()

    async def get(self, id: str) -> PaymentTransaction | None:
        """Get transaction by ID."""
        return self._store.payment_transactions.get(id)

    async def get_all(self) -> list[PaymentTransaction]:
        """Get all transactions."""
        return list(self._store.payment_transactions.values())

    async def add(self, entity: PaymentTransaction) -> PaymentTransaction:
        """Add a new transaction."""
        async with self._store.transaction():
            self._store.payment_transactions[entity.id] = entity
        return entity

    async def update(self, entity: PaymentTransaction) -> PaymentTransaction:
        """Update an existing transaction."""
        from ..models.payment import utc_now

        async with self._store.transaction():
            if entity.id not in self._store.payment_transactions:
                raise ValueError(f"Transaction not found: {entity.id}")
            entity.updated_at = utc_now()
            self._store.payment_transactions[entity.id] = entity
        return entity

    async def delete(self, id: str) -> bool:
        """Delete a transaction."""
        async with self._store.transaction():
            if id in self._store.payment_transactions:
                del self._store.payment_transactions[id]
                return True
        return False

    async def exists(self, id: str) -> bool:
        """Check if transaction exists."""
        return id in self._store.payment_transactions

    async def count(self) -> int:
        """Count all transactions."""
        return len(self._store.payment_transactions)

    async def get_by_user(self, user_id: str) -> list[PaymentTransaction]:
        """Get all transactions for a user."""
        return [t for t in self._store.payment_transactions.values() if t.user_id == user_id]

    async def get_by_status(self, status: PaymentStatus) -> list[PaymentTransaction]:
        """Get transactions by status."""
        return [t for t in self._store.payment_transactions.values() if t.status == status]

    async def get_by_idempotency_key(self, idempotency_key: str) -> PaymentTransaction | None:
        """Get transaction by idempotency key (prevent duplicates)."""
        for t in self._store.payment_transactions.values():
            if t.idempotency_key == idempotency_key:
                return t
        return None


class SubscriptionRepository(BaseRepository[Subscription]):
    """Repository for subscriptions."""

    def __init__(self, store: StateStore | None = None):
        self._store = store or get_state_store()

    async def get(self, id: str) -> Subscription | None:
        """Get subscription by ID."""
        return self._store.subscriptions.get(id)

    async def get_all(self) -> list[Subscription]:
        """Get all subscriptions."""
        return list(self._store.subscriptions.values())

    async def add(self, entity: Subscription) -> Subscription:
        """Add a new subscription."""
        async with self._store.transaction():
            self._store.subscriptions[entity.id] = entity
        return entity

    async def update(self, entity: Subscription) -> Subscription:
        """Update an existing subscription."""
        from ..models.payment import utc_now

        async with self._store.transaction():
            if entity.id not in self._store.subscriptions:
                raise ValueError(f"Subscription not found: {entity.id}")
            entity.updated_at = utc_now()
            self._store.subscriptions[entity.id] = entity
        return entity

    async def delete(self, id: str) -> bool:
        """Delete a subscription."""
        async with self._store.transaction():
            if id in self._store.subscriptions:
                del self._store.subscriptions[id]
                return True
        return False

    async def exists(self, id: str) -> bool:
        """Check if subscription exists."""
        return id in self._store.subscriptions

    async def count(self) -> int:
        """Count all subscriptions."""
        return len(self._store.subscriptions)

    async def get_by_user(self, user_id: str) -> list[Subscription]:
        """Get all subscriptions for a user."""
        return [s for s in self._store.subscriptions.values() if s.user_id == user_id]

    async def get_active_by_user(self, user_id: str) -> Subscription | None:
        """Get active subscription for a user."""
        for sub in self._store.subscriptions.values():
            if sub.user_id == user_id and sub.is_active():
                return sub
        return None

    async def get_by_tier(self, tier: SubscriptionTier) -> list[Subscription]:
        """Get subscriptions by tier."""
        return [s for s in self._store.subscriptions.values() if s.tier == tier]

    async def get_by_status(self, status: SubscriptionStatus) -> list[Subscription]:
        """Get subscriptions by status."""
        return [s for s in self._store.subscriptions.values() if s.status == status]


class InvoiceRepository(BaseRepository[Invoice]):
    """Repository for invoices."""

    def __init__(self, store: StateStore | None = None):
        self._store = store or get_state_store()

    async def get(self, id: str) -> Invoice | None:
        """Get invoice by ID."""
        return self._store.invoices.get(id)

    async def get_all(self) -> list[Invoice]:
        """Get all invoices."""
        return list(self._store.invoices.values())

    async def add(self, entity: Invoice) -> Invoice:
        """Add a new invoice."""
        async with self._store.transaction():
            self._store.invoices[entity.id] = entity
        return entity

    async def update(self, entity: Invoice) -> Invoice:
        """Update an existing invoice."""
        from ..models.payment import utc_now

        async with self._store.transaction():
            if entity.id not in self._store.invoices:
                raise ValueError(f"Invoice not found: {entity.id}")
            entity.updated_at = utc_now()
            self._store.invoices[entity.id] = entity
        return entity

    async def delete(self, id: str) -> bool:
        """Delete an invoice."""
        async with self._store.transaction():
            if id in self._store.invoices:
                del self._store.invoices[id]
                return True
        return False

    async def exists(self, id: str) -> bool:
        """Check if invoice exists."""
        return id in self._store.invoices

    async def count(self) -> int:
        """Count all invoices."""
        return len(self._store.invoices)

    async def get_by_user(self, user_id: str) -> list[Invoice]:
        """Get all invoices for a user."""
        return [i for i in self._store.invoices.values() if i.user_id == user_id]

    async def get_by_subscription(self, subscription_id: str) -> list[Invoice]:
        """Get invoices for a subscription."""
        return [i for i in self._store.invoices.values() if i.subscription_id == subscription_id]
