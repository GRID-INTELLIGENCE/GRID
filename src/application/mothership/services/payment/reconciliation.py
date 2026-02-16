"""Payment reconciliation service and scheduler wiring helpers."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from ...models.payment import PaymentGateway, PaymentReconciliationRun, PaymentStatus
from .gateway import PaymentGateway as PaymentGatewayBase

logger = logging.getLogger(__name__)


class PaymentReconciliationService:
    """Compares local transaction state with gateway state and records mismatches."""

    def __init__(self, uow: Any, gateway: PaymentGatewayBase):
        self.uow = uow
        self.gateway = gateway

    async def run_once(self, lookback_hours: int = 168) -> dict[str, Any]:
        cutoff = datetime.now(UTC) - timedelta(hours=lookback_hours)
        run = PaymentReconciliationRun(
            gateway=PaymentGateway(self.gateway.get_name()),
            metadata={"lookback_hours": lookback_hours},
        )

        transactions = await self.uow.payment_transactions.get_all()
        candidates = [tx for tx in transactions if tx.gateway_transaction_id and tx.created_at >= cutoff]

        mismatches: list[dict[str, Any]] = []
        auto_reconciled = 0

        for tx in candidates:
            remote_status = await self.gateway.get_transaction_status(tx.gateway_transaction_id)
            local_status = tx.status

            if local_status == remote_status:
                continue

            issue = {
                "transaction_id": tx.id,
                "gateway_transaction_id": tx.gateway_transaction_id,
                "local_status": local_status.value,
                "gateway_status": remote_status.value,
                "created_at": tx.created_at.isoformat(),
            }
            mismatches.append(issue)

            if local_status in {PaymentStatus.PENDING, PaymentStatus.PROCESSING} and remote_status in {
                PaymentStatus.COMPLETED,
                PaymentStatus.FAILED,
                PaymentStatus.CANCELLED,
            }:
                tx.status = remote_status
                if remote_status == PaymentStatus.COMPLETED:
                    tx.completed_at = datetime.now(UTC)
                if remote_status in {PaymentStatus.FAILED, PaymentStatus.CANCELLED}:
                    tx.failure_reason = f"reconciled_from_gateway:{remote_status.value}"
                await self.uow.payment_transactions.update(tx)
                auto_reconciled += 1

        run.scanned_transactions = len(candidates)
        run.mismatched_transactions = len(mismatches)
        run.auto_reconciled_transactions = auto_reconciled
        run.issues = mismatches
        run.finish()

        await self.uow.reconciliation_runs.add(run)

        return {
            "run_id": run.id,
            "scanned_transactions": run.scanned_transactions,
            "mismatched_transactions": run.mismatched_transactions,
            "auto_reconciled_transactions": run.auto_reconciled_transactions,
            "issues": run.issues,
        }


async def reconciliation_loop(
    settings: Any,
    uow_factory: Any,
    gateway_factory: Any,
    stop_event: asyncio.Event,
) -> None:
    """Periodically execute payment reconciliation until stop_event is set."""
    interval = max(60, int(settings.payment.reconciliation_interval_seconds))

    while not stop_event.is_set():
        try:
            uow = await uow_factory()
            gateway = gateway_factory(settings)
            if gateway is None:
                logger.info("Payment reconciliation skipped: gateway unavailable")
            else:
                service = PaymentReconciliationService(uow=uow, gateway=gateway)
                async with uow.transaction():
                    result = await service.run_once(lookback_hours=settings.payment.reconciliation_lookback_hours)
                logger.info(
                    "Payment reconciliation run=%s scanned=%s mismatches=%s auto_reconciled=%s",
                    result["run_id"],
                    result["scanned_transactions"],
                    result["mismatched_transactions"],
                    result["auto_reconciled_transactions"],
                )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception("Payment reconciliation loop failed: %s", exc)

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
        except TimeoutError:
            continue
