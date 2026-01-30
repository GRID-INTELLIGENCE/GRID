"""
Billing API router.

Endpoints for usage statistics and billing information.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query, status

from ..dependencies import RequiredAuth, UoW
from ..exceptions import ResourceNotFoundError
from ..schemas.payment import InvoiceResponse
from ..services.billing import BillingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/usage", summary="Get Usage Summary")
async def get_usage_summary(
    auth: RequiredAuth,
    uow: UoW,
    period_days: int = Query(default=30, ge=1, le=365, description="Period in days"),
) -> dict:
    """
    Get usage summary for the current user.

    Returns usage statistics, tier limits, and current consumption.
    """
    user_id = auth.get("user_id", "unknown")
    billing_service = BillingService(
        subscription_repo=uow.subscriptions,
        invoice_repo=uow.invoices,
        usage_repo=uow.usage,
    )
    summary = await billing_service.get_usage_summary(user_id, period_days)
    return summary


@router.get("/invoices", response_model=list[InvoiceResponse])
async def list_invoices(
    auth: RequiredAuth,
    uow: UoW,
) -> list[InvoiceResponse]:
    """List all invoices for the current user."""
    user_id = auth.get("user_id", "unknown")
    invoices = await uow.invoices.get_by_user(user_id)
    return [InvoiceResponse(**invoice.to_dict()) for invoice in invoices]


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: str,
    auth: RequiredAuth,
    uow: UoW,
) -> InvoiceResponse:
    """Get invoice details."""
    invoice = await uow.invoices.get(invoice_id)
    if not invoice:
        raise ResourceNotFoundError("invoice", invoice_id)

    user_id = auth.get("user_id", "unknown")
    if invoice.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return InvoiceResponse(**invoice.to_dict())
