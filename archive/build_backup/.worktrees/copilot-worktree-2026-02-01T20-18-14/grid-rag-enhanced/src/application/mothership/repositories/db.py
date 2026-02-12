from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from ..db.engine import get_async_sessionmaker
from .db_repos import (
    DbAPIKeyRepository,
    DbInvoiceRepository,
    DbPaymentTransactionRepository,
    DbSubscriptionRepository,
    DbUsageRepository,
)


class DbUnitOfWork:
    def __init__(self, session: AsyncSession | None = None):
        self._external_session = session
        self._session: AsyncSession | None = session

        # Initialize repositories as Optional to allow None assignment
        self.api_keys: DbAPIKeyRepository | None = None
        self.usage: DbUsageRepository | None = None
        self.payment_transactions: DbPaymentTransactionRepository | None = None
        self.subscriptions: DbSubscriptionRepository | None = None
        self.invoices: DbInvoiceRepository | None = None

        if self._session is not None:
            self.api_keys = DbAPIKeyRepository(self._session)
            self.usage = DbUsageRepository(self._session)
            self.payment_transactions = DbPaymentTransactionRepository(self._session)
            self.subscriptions = DbSubscriptionRepository(self._session)
            self.invoices = DbInvoiceRepository(self._session)

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[DbUnitOfWork]:
        if self._external_session is not None:
            yield self
            return

        sessionmaker = get_async_sessionmaker()
        async with sessionmaker() as session:
            self._session = session
            self.api_keys = DbAPIKeyRepository(session)
            self.usage = DbUsageRepository(session)
            self.payment_transactions = DbPaymentTransactionRepository(session)
            self.subscriptions = DbSubscriptionRepository(session)
            self.invoices = DbInvoiceRepository(session)
            try:
                yield self
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                self._session = None
                self.api_keys = None
                self.usage = None
                self.payment_transactions = None
                self.subscriptions = None
                self.invoices = None

    @property
    def session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError("DbUnitOfWork has no active session (use within transaction())")
        return self._session
