"""Stripe Connect demo integration router.

This module intentionally contains detailed code comments for onboarding and
maintenance. It demonstrates how to:
1) Create and onboard Stripe Connect accounts (V2 accounts + V2 account links)
2) Create products on connected accounts
3) Render a simple storefront per connected account
4) Create direct-charge Checkout Sessions with an application fee
5) Create connected-account subscription sessions and billing portal sessions
6) Handle thin V2 account events and classic subscription/billing webhooks

IMPORTANT:
- This is a sample integration, not a complete production commerce system.
- For storefront URLs, this sample uses `acct_...` in the path for clarity.
  In production, use a non-sensitive merchant slug instead.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import UTC, datetime
from html import escape
from typing import Any

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy import select

from ..db.engine import get_async_sessionmaker
from ..db.models_billing import ConnectAccountMappingRow
from ..dependencies import RequiredAuth, Settings

try:
    from stripe import StripeClient
except ImportError:  # pragma: no cover - dependency availability is environment specific
    StripeClient = None  # type: ignore[assignment]

router = APIRouter(prefix="/connect-demo", tags=["stripe-connect-demo"])


# In-memory fallback when DB persistence is disabled.
# Keyed by user_id, values contain at least stripe_account_id.
_CONNECT_MAP_MEMORY: dict[str, dict[str, Any]] = {}


def _require_stripe_client(settings: Settings):
    """Build a Stripe Client and fail with clear configuration guidance if missing."""
    if StripeClient is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Stripe SDK is not installed. Set dependency placeholder in pyproject and install it. "
                "Expected package: stripe (latest stable)."
            ),
        )

    # Placeholder comment for operators:
    # TODO(you): set STRIPE_SECRET_KEY in environment or secrets manager.
    api_key = (settings.payment.stripe_secret_key or "").strip()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Missing STRIPE_SECRET_KEY. Please configure your Stripe secret key "
                "before using Connect demo endpoints."
            ),
        )

    return StripeClient(api_key)


def _base_url(request: Request) -> str:
    """Return a normalized origin URL used for redirects and hosted sessions."""
    # TODO(you): in production behind reverse proxies, ensure forwarded host/proto are trusted.
    return str(request.base_url).rstrip("/")


async def _get_mapping_by_user(user_id: str) -> dict[str, Any] | None:
    """Load local user -> connected account mapping from DB (if enabled) or memory fallback."""
    mode = os.getenv("MOTHERSHIP_PERSISTENCE_MODE", "memory").strip().lower()

    if mode != "db":
        return _CONNECT_MAP_MEMORY.get(user_id)

    sessionmaker = get_async_sessionmaker()
    async with sessionmaker() as session:
        row = (
            (await session.execute(select(ConnectAccountMappingRow).where(ConnectAccountMappingRow.user_id == user_id)))
            .scalars()
            .first()
        )
        if not row:
            return None

        return {
            "user_id": row.user_id,
            "stripe_account_id": row.stripe_account_id,
            "subscription_id": row.subscription_id,
            "subscription_status": row.subscription_status,
            "subscription_price_id": row.subscription_price_id,
            "meta": row.meta or {},
        }


async def _save_mapping(user_id: str, stripe_account_id: str, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    """Upsert user -> connected account mapping."""
    mode = os.getenv("MOTHERSHIP_PERSISTENCE_MODE", "memory").strip().lower()
    payload = {
        "user_id": user_id,
        "stripe_account_id": stripe_account_id,
        "subscription_id": None,
        "subscription_status": None,
        "subscription_price_id": None,
        "meta": meta or {},
    }

    if mode != "db":
        _CONNECT_MAP_MEMORY[user_id] = payload
        return payload

    sessionmaker = get_async_sessionmaker()
    async with sessionmaker() as session:
        row = (
            (await session.execute(select(ConnectAccountMappingRow).where(ConnectAccountMappingRow.user_id == user_id)))
            .scalars()
            .first()
        )
        if row is None:
            row = ConnectAccountMappingRow(
                id=f"cam_{uuid.uuid4().hex}",
                user_id=user_id,
                stripe_account_id=stripe_account_id,
                meta=meta or {},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            session.add(row)
        else:
            row.stripe_account_id = stripe_account_id
            row.meta = meta or {}
            row.updated_at = datetime.now(UTC)

        await session.commit()

    return payload


async def _save_subscription_state(
    account_id: str,
    subscription_id: str | None,
    subscription_status: str | None,
    subscription_price_id: str | None,
) -> None:
    """Persist connected-account subscription state when DB is enabled; use TODO fallback in memory mode."""
    mode = os.getenv("MOTHERSHIP_PERSISTENCE_MODE", "memory").strip().lower()

    if mode != "db":
        # TODO(you): if you disable DB persistence, replace this with your durable storage (Redis/Postgres/etc.).
        for key, value in _CONNECT_MAP_MEMORY.items():
            if value.get("stripe_account_id") == account_id:
                _CONNECT_MAP_MEMORY[key] = {
                    **value,
                    "subscription_id": subscription_id,
                    "subscription_status": subscription_status,
                    "subscription_price_id": subscription_price_id,
                }
        return

    sessionmaker = get_async_sessionmaker()
    async with sessionmaker() as session:
        row = (
            (
                await session.execute(
                    select(ConnectAccountMappingRow).where(ConnectAccountMappingRow.stripe_account_id == account_id)
                )
            )
            .scalars()
            .first()
        )
        if not row:
            # TODO(you): create an onboarding-first policy if webhook arrives before local mapping exists.
            return

        row.subscription_id = subscription_id
        row.subscription_status = subscription_status
        row.subscription_price_id = subscription_price_id
        row.updated_at = datetime.now(UTC)
        await session.commit()


async def _update_mapping_by_account(
    account_id: str,
    field_updates: dict[str, Any] | None = None,
    meta_updates: dict[str, Any] | None = None,
) -> bool:
    """Update a mapping row by connected account ID; returns False when mapping does not exist."""
    mode = os.getenv("MOTHERSHIP_PERSISTENCE_MODE", "memory").strip().lower()

    if mode != "db":
        for key, value in _CONNECT_MAP_MEMORY.items():
            if value.get("stripe_account_id") != account_id:
                continue

            merged = dict(value)
            if field_updates:
                merged.update(field_updates)

            merged_meta = dict(merged.get("meta") or {})
            if meta_updates:
                merged_meta.update(meta_updates)
            merged["meta"] = merged_meta

            _CONNECT_MAP_MEMORY[key] = merged
            return True
        return False

    sessionmaker = get_async_sessionmaker()
    async with sessionmaker() as session:
        row = (
            (
                await session.execute(
                    select(ConnectAccountMappingRow).where(ConnectAccountMappingRow.stripe_account_id == account_id)
                )
            )
            .scalars()
            .first()
        )
        if not row:
            return False

        if field_updates:
            if "subscription_id" in field_updates:
                row.subscription_id = field_updates.get("subscription_id")
            if "subscription_status" in field_updates:
                row.subscription_status = field_updates.get("subscription_status")
            if "subscription_price_id" in field_updates:
                row.subscription_price_id = field_updates.get("subscription_price_id")

        merged_meta = dict(row.meta or {})
        if meta_updates:
            merged_meta.update(meta_updates)
        row.meta = merged_meta
        row.updated_at = datetime.now(UTC)
        await session.commit()
        return True


async def _append_account_event(account_id: str, event_type: str, payload: dict[str, Any]) -> bool:
    """Append a compact event record to mapping metadata for audit/operational visibility."""
    mode = os.getenv("MOTHERSHIP_PERSISTENCE_MODE", "memory").strip().lower()
    event_record = {
        "at": datetime.now(UTC).isoformat(),
        "event_type": event_type,
        "payload": payload,
    }

    if mode != "db":
        for key, value in _CONNECT_MAP_MEMORY.items():
            if value.get("stripe_account_id") != account_id:
                continue

            merged = dict(value)
            meta = dict(merged.get("meta") or {})
            history = list(meta.get("events") or [])
            history.append(event_record)
            meta["events"] = history[-100:]
            merged["meta"] = meta
            _CONNECT_MAP_MEMORY[key] = merged
            return True
        return False

    sessionmaker = get_async_sessionmaker()
    async with sessionmaker() as session:
        row = (
            (
                await session.execute(
                    select(ConnectAccountMappingRow).where(ConnectAccountMappingRow.stripe_account_id == account_id)
                )
            )
            .scalars()
            .first()
        )
        if not row:
            return False

        meta = dict(row.meta or {})
        history = list(meta.get("events") or [])
        history.append(event_record)
        meta["events"] = history[-100:]
        row.meta = meta
        row.updated_at = datetime.now(UTC)
        await session.commit()
        return True


def _onboarding_flags(account: Any) -> tuple[bool, str | None, bool]:
    """Compute onboarding/payment readiness from a V2 account object."""
    merchant_cap = (
        account.get("configuration", {})
        .get("merchant", {})
        .get("capabilities", {})
        .get("card_payments", {})
        .get("status")
    )
    ready_to_process = merchant_cap == "active"

    requirements_status = account.get("requirements", {}).get("summary", {}).get("minimum_deadline", {}).get("status")
    onboarding_complete = requirements_status not in {"currently_due", "past_due"}
    return ready_to_process, requirements_status, onboarding_complete


def _html_page(title: str, body: str) -> str:
    """Simple consistent HTML wrapper for demo UI pages."""
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{escape(title)}</title>
  <style>
    body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin: 2rem; color: #1f2937; background: #f8fafc; }}
    .card {{ background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 1rem; margin-bottom: 1rem; }}
    h1, h2 {{ margin: 0 0 .75rem 0; }}
    label {{ display: block; margin-top: .5rem; font-weight: 600; }}
    input, textarea {{ width: 100%; padding: .6rem; margin-top: .25rem; border: 1px solid #d1d5db; border-radius: 8px; }}
    button {{ margin-top: .75rem; padding: .6rem .9rem; border: 0; border-radius: 8px; background: #0f766e; color: #fff; cursor: pointer; }}
    .muted {{ color: #64748b; font-size: .95rem; }}
    a {{ color: #0f766e; }}
    code {{ background: #f1f5f9; padding: .15rem .35rem; border-radius: 5px; }}
  </style>
</head>
<body>
{body}
</body>
</html>"""


@router.get("/dashboard", response_class=HTMLResponse)
async def connect_dashboard(request: Request, auth: RequiredAuth, settings: Settings):
    """Dashboard for merchants to create/onboard a connected account and manage catalog/subscriptions."""
    stripe_client = _require_stripe_client(settings)
    user_id = str(auth.get("user_id") or "")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authenticated user_id")

    mapping = await _get_mapping_by_user(user_id)
    account_id = mapping.get("stripe_account_id") if mapping else None

    account_status_html = "<p class='muted'>No connected account mapped yet.</p>"
    storefront_url_html = ""

    if account_id:
        # Requirement: status must be fetched directly from Stripe API each time (not cached DB status).
        account = stripe_client.v2.core.accounts.retrieve(
            account_id,
            {"include": ["configuration.merchant", "requirements"]},
        )
        ready, req_status, onboarding_complete = _onboarding_flags(account)
        account_status_html = f"""
        <p><strong>Connected account:</strong> <code>{escape(account_id)}</code></p>
        <p><strong>Card payments capability:</strong> {escape(str(ready))}</p>
        <p><strong>Requirements status:</strong> {escape(str(req_status))}</p>
        <p><strong>Onboarding complete:</strong> {escape(str(onboarding_complete))}</p>
        """
        storefront_url_html = f"<p><a href='/api/v1/connect-demo/storefront/{escape(account_id)}' target='_blank'>Open storefront page</a></p>"

    base = _base_url(request)

    body = f"""
    <h1>Stripe Connect Demo Dashboard</h1>
    <p class='muted'>This sample uses <code>StripeClient</code> for all Stripe API requests.</p>

    <div class='card'>
      <h2>Account status</h2>
      {account_status_html}
      {storefront_url_html}
    </div>

    <div class='card'>
      <h2>Create connected account</h2>
      <form method='post' action='/api/v1/connect-demo/accounts/create'>
        <label>Display name</label>
        <input name='display_name' placeholder='Acme Merchant LLC' required />
        <label>Contact email</label>
        <input name='contact_email' type='email' placeholder='owner@example.com' required />
        <button type='submit'>Create connected account</button>
      </form>
    </div>

    <div class='card'>
      <h2>Onboard to collect payments</h2>
      <form method='post' action='/api/v1/connect-demo/accounts/onboarding-link'>
        <button type='submit'>Onboard to collect payments</button>
      </form>
      <p class='muted'>Creates a V2 account link and redirects to Stripe onboarding.</p>
    </div>

    <div class='card'>
      <h2>Create product on connected account</h2>
      <form method='post' action='/api/v1/connect-demo/products/create'>
        <label>Name</label>
        <input name='name' placeholder='Demo Product' required />
        <label>Description</label>
        <textarea name='description' placeholder='What this product includes'></textarea>
        <label>Price in cents</label>
        <input name='price_in_cents' type='number' min='1' value='499' required />
        <label>Currency</label>
        <input name='currency' value='usd' required />
        <button type='submit'>Create product</button>
      </form>
    </div>

    <div class='card'>
      <h2>Connected account subscription (platform billing)</h2>
      <form method='post' action='/api/v1/connect-demo/subscriptions/checkout'>
        <button type='submit'>Start subscription checkout</button>
      </form>
      <form method='post' action='/api/v1/connect-demo/subscriptions/portal'>
        <button type='submit'>Open billing portal</button>
      </form>
      <p class='muted'>Uses <code>customer_account = acct_...</code> per V2 account billing model.</p>
    </div>

    <div class='card'>
      <h2>Webhook setup help</h2>
      <p>Thin V2 endpoint: <code>{escape(base)}/api/v1/connect-demo/webhooks/thin</code></p>
      <p>Snapshot billing endpoint: <code>{escape(base)}/api/v1/connect-demo/webhooks/billing</code></p>
      <p><a href='/api/v1/connect-demo/events'>View recent Connect webhook events</a></p>
    </div>
    """
    return HTMLResponse(_html_page("Stripe Connect Demo Dashboard", body))


@router.post("/accounts/create")
async def create_connected_account(
    request: Request,
    auth: RequiredAuth,
    settings: Settings,
    display_name: str = Form(...),
    contact_email: str = Form(...),
):
    """Create a Stripe Connected Account using V2 API with the required property set.

    Idempotency behavior for this sample:
    - If the current user already has a mapped connected account and Stripe can retrieve it,
      we reuse it rather than creating a duplicate account.
    - If mapping exists but account retrieval fails, we create a fresh account and remap.
    """
    _ = request
    stripe_client = _require_stripe_client(settings)
    user_id = str(auth.get("user_id") or "")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authenticated user_id")

    existing = await _get_mapping_by_user(user_id)
    if existing and isinstance(existing.get("stripe_account_id"), str):
        existing_account_id = existing["stripe_account_id"]
        try:
            _ = stripe_client.v2.core.accounts.retrieve(existing_account_id)
            await _update_mapping_by_account(
                existing_account_id,
                meta_updates={
                    "display_name": display_name,
                    "contact_email": contact_email,
                    "last_account_create_attempt_at": datetime.now(UTC).isoformat(),
                    "idempotent_reuse": True,
                },
            )
            return RedirectResponse(url="/api/v1/connect-demo/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        except Exception:
            # Mapping is stale or account inaccessible; continue to create a new account.
            pass

    # Required shape per user request: do not pass top-level type.
    account = stripe_client.v2.core.accounts.create(
        {
            "display_name": display_name,
            "contact_email": contact_email,
            "identity": {"country": "us"},
            "dashboard": "full",
            "defaults": {
                "responsibilities": {
                    "fees_collector": "stripe",
                    "losses_collector": "stripe",
                }
            },
            "configuration": {
                "customer": {},
                "merchant": {
                    "capabilities": {
                        "card_payments": {
                            "requested": True,
                        }
                    }
                },
            },
        }
    )

    account_id = account.get("id")
    if not isinstance(account_id, str) or not account_id.startswith("acct_"):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unexpected Stripe account response: {account}",
        )

    await _save_mapping(
        user_id=user_id,
        stripe_account_id=account_id,
        meta={
            "display_name": display_name,
            "contact_email": contact_email,
            "created_account_at": datetime.now(UTC).isoformat(),
            "idempotent_reuse": False,
        },
    )

    return RedirectResponse(url="/api/v1/connect-demo/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/accounts/onboarding-link")
async def create_onboarding_link(request: Request, auth: RequiredAuth, settings: Settings):
    """Create V2 Account Link for onboarding and redirect merchant to Stripe-hosted flow."""
    stripe_client = _require_stripe_client(settings)
    user_id = str(auth.get("user_id") or "")
    mapping = await _get_mapping_by_user(user_id)
    if not mapping:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Create connected account first")

    account_id = mapping["stripe_account_id"]
    base = _base_url(request)

    account_link = stripe_client.v2.core.account_links.create(
        {
            "account": account_id,
            "use_case": {
                "type": "account_onboarding",
                "account_onboarding": {
                    "configurations": ["merchant", "customer"],
                    "refresh_url": f"{base}/api/v1/connect-demo/dashboard",
                    "return_url": f"{base}/api/v1/connect-demo/dashboard?accountId={account_id}",
                },
            },
        }
    )

    onboarding_url = account_link.get("url")
    if not onboarding_url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Invalid account link response: {account_link}"
        )

    return RedirectResponse(url=onboarding_url, status_code=status.HTTP_303_SEE_OTHER)


@router.post("/products/create")
async def create_product(
    auth: RequiredAuth,
    settings: Settings,
    name: str = Form(...),
    description: str = Form(""),
    price_in_cents: int = Form(...),
    currency: str = Form("usd"),
):
    """Create product + default price on connected account via Stripe-Account header."""
    stripe_client = _require_stripe_client(settings)
    user_id = str(auth.get("user_id") or "")
    mapping = await _get_mapping_by_user(user_id)
    if not mapping:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Create connected account first")

    account_id = mapping["stripe_account_id"]

    _ = stripe_client.v1.products.create(
        {
            "name": name,
            "description": description,
            "default_price_data": {
                "unit_amount": int(price_in_cents),
                "currency": currency.lower(),
            },
        },
        {"stripe_account": account_id},
    )

    return RedirectResponse(
        url=f"/api/v1/connect-demo/storefront/{account_id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/storefront/{account_id}", response_class=HTMLResponse)
async def storefront_page(account_id: str, settings: Settings):
    """Public storefront page for a single connected account.

    NOTE: This demo uses account_id in URL directly for simplicity.
    In production, replace with merchant slug/opaque ID and resolve internally.
    """
    stripe_client = _require_stripe_client(settings)

    products = stripe_client.v1.products.list(
        {
            "limit": 20,
            "active": True,
            "expand": ["data.default_price"],
        },
        {"stripe_account": account_id},
    )

    rows: list[str] = []
    for product in products.get("data", []):
        price = product.get("default_price") or {}
        unit_amount = price.get("unit_amount")
        currency = (price.get("currency") or "usd").upper()

        if unit_amount is None:
            continue

        rows.append(
            f"""
            <div class='card'>
              <h2>{escape(product.get("name") or "Unnamed product")}</h2>
              <p class='muted'>{escape(product.get("description") or "")}</p>
              <p><strong>Price:</strong> {unit_amount / 100:.2f} {escape(currency)}</p>
              <form method='post' action='/api/v1/connect-demo/storefront/{escape(account_id)}/checkout'>
                <input type='hidden' name='product_id' value='{escape(product.get("id") or "")}' />
                <input type='hidden' name='unit_amount' value='{escape(str(unit_amount))}' />
                <input type='hidden' name='currency' value='{escape(price.get("currency") or "usd")}' />
                <button type='submit'>Buy now</button>
              </form>
            </div>
            """
        )

    if not rows:
        rows.append("<p class='muted'>No active products yet for this connected account.</p>")

    body = f"""
    <h1>Storefront</h1>
    <p class='muted'>Merchant account: <code>{escape(account_id)}</code></p>
    {"".join(rows)}
    """
    return HTMLResponse(_html_page("Storefront", body))


@router.post("/storefront/{account_id}/checkout")
async def checkout_direct_charge(
    request: Request,
    account_id: str,
    settings: Settings,
    product_id: str = Form(...),
    unit_amount: int = Form(...),
    currency: str = Form("usd"),
):
    """Create direct-charge Checkout Session on connected account with application fee."""
    stripe_client = _require_stripe_client(settings)
    base = _base_url(request)

    # TODO(you): set STRIPE_CONNECT_APPLICATION_FEE_AMOUNT in env if you want non-default fee.
    fee_amount = int(os.getenv("STRIPE_CONNECT_APPLICATION_FEE_AMOUNT", "123"))

    session = stripe_client.v1.checkout.sessions.create(
        {
            "line_items": [
                {
                    "price_data": {
                        "currency": currency.lower(),
                        "product": product_id,
                        "unit_amount": int(unit_amount),
                    },
                    "quantity": 1,
                }
            ],
            "payment_intent_data": {
                "application_fee_amount": fee_amount,
            },
            "mode": "payment",
            "success_url": f"{base}/api/v1/connect-demo/success?session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": f"{base}/api/v1/connect-demo/storefront/{account_id}",
        },
        {"stripe_account": account_id},
    )

    checkout_url = session.get("url")
    if not checkout_url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Invalid Checkout Session response: {session}"
        )

    return RedirectResponse(url=checkout_url, status_code=status.HTTP_303_SEE_OTHER)


@router.get("/success", response_class=HTMLResponse)
async def checkout_success(session_id: str | None = None):
    """Basic success landing page for hosted checkout."""
    sid = escape(session_id or "")
    return HTMLResponse(
        _html_page(
            "Payment success",
            f"<h1>Payment successful</h1><p>Session ID: <code>{sid}</code></p>",
        )
    )


@router.post("/subscriptions/checkout")
async def connected_account_subscription_checkout(request: Request, auth: RequiredAuth, settings: Settings):
    """Create platform-level hosted subscription checkout using connected account ID as customer_account."""
    stripe_client = _require_stripe_client(settings)
    user_id = str(auth.get("user_id") or "")
    mapping = await _get_mapping_by_user(user_id)
    if not mapping:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Create connected account first")

    account_id = mapping["stripe_account_id"]
    base = _base_url(request)

    # TODO(you): configure STRIPE_CONNECT_SUBSCRIPTION_PRICE_ID with a real recurring Price ID (price_...).
    price_id = (os.getenv("STRIPE_CONNECT_SUBSCRIPTION_PRICE_ID") or "").strip()
    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Missing STRIPE_CONNECT_SUBSCRIPTION_PRICE_ID. Set a recurring price ID before subscription checkout.",
        )

    session = stripe_client.v1.checkout.sessions.create(
        {
            "customer_account": account_id,
            "mode": "subscription",
            "line_items": [{"price": price_id, "quantity": 1}],
            "success_url": f"{base}/api/v1/connect-demo/success?session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": f"{base}/api/v1/connect-demo/dashboard",
        }
    )

    checkout_url = session.get("url")
    if not checkout_url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Invalid Checkout Session response: {session}"
        )

    return RedirectResponse(url=checkout_url, status_code=status.HTTP_303_SEE_OTHER)


@router.post("/subscriptions/portal")
async def connected_account_billing_portal(request: Request, auth: RequiredAuth, settings: Settings):
    """Create billing portal session for connected account billing management."""
    stripe_client = _require_stripe_client(settings)
    user_id = str(auth.get("user_id") or "")
    mapping = await _get_mapping_by_user(user_id)
    if not mapping:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Create connected account first")

    account_id = mapping["stripe_account_id"]
    base = _base_url(request)

    portal_session = stripe_client.v1.billing_portal.sessions.create(
        {
            "customer_account": account_id,
            "return_url": f"{base}/api/v1/connect-demo/dashboard",
        }
    )

    portal_url = portal_session.get("url")
    if not portal_url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Invalid billing portal response: {portal_session}",
        )

    return RedirectResponse(url=portal_url, status_code=status.HTTP_303_SEE_OTHER)


def _event_type(event: Any) -> str:
    """Extract event type from Stripe event payload variants."""
    if isinstance(event, dict):
        return str(event.get("type") or "")
    return str(getattr(event, "type", ""))


def _event_data_object(event: Any) -> dict[str, Any]:
    """Extract a normalized event data object from either dict or SDK object."""
    if isinstance(event, dict):
        data = event.get("data") or {}
        if isinstance(data, dict):
            obj = data.get("object")
            if isinstance(obj, dict):
                return obj
            if isinstance(data, dict):
                return data
        return {}

    data = getattr(event, "data", None)
    obj = getattr(data, "object", None) if data is not None else None
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if isinstance(obj, dict):
        return obj
    return {}


def _extract_account_id_from_v2_event_object(obj: dict[str, Any]) -> str | None:
    """Best-effort extraction for account ID from V2 event object payload."""
    for key in ("id", "account", "account_id", "customer_account"):
        value = obj.get(key)
        if isinstance(value, str) and value.startswith("acct_"):
            return value
    return None


async def _handle_v2_requirements_updated(event: Any) -> dict[str, Any]:
    obj = _event_data_object(event)
    account_id = _extract_account_id_from_v2_event_object(obj)

    persisted = False
    if account_id:
        requirements_summary = (obj.get("requirements") or {}).get("summary") if isinstance(obj, dict) else None
        minimum_deadline = (requirements_summary or {}).get("minimum_deadline") if isinstance(requirements_summary, dict) else None
        persisted = await _update_mapping_by_account(
            account_id,
            meta_updates={
                "last_requirements_update": {
                    "at": datetime.now(UTC).isoformat(),
                    "summary": requirements_summary,
                    "minimum_deadline": minimum_deadline,
                }
            },
        )
        await _append_account_event(
            account_id,
            "v2.core.account[requirements].updated",
            {"requirements_summary": requirements_summary, "minimum_deadline": minimum_deadline},
        )

    return {
        "handled": True,
        "event_type": "v2.core.account[requirements].updated",
        "account_id": account_id,
        "persisted": persisted,
    }


async def _handle_v2_recipient_capability_status_updated(event: Any) -> dict[str, Any]:
    obj = _event_data_object(event)
    account_id = _extract_account_id_from_v2_event_object(obj)
    persisted = False
    if account_id:
        capability_payload = obj.get("configuration") if isinstance(obj, dict) else None
        persisted = await _update_mapping_by_account(
            account_id,
            meta_updates={"last_recipient_capability_update": capability_payload},
        )
        await _append_account_event(
            account_id,
            "v2.core.account[.recipient].capability_status_updated",
            {"configuration": capability_payload},
        )
    return {
        "handled": True,
        "event_type": "v2.core.account[.recipient].capability_status_updated",
        "account_id": account_id,
        "persisted": persisted,
    }


async def _handle_v2_merchant_capability_status_updated(event: Any) -> dict[str, Any]:
    obj = _event_data_object(event)
    account_id = _extract_account_id_from_v2_event_object(obj)
    persisted = False
    if account_id:
        merchant_payload = (obj.get("configuration") or {}).get("merchant") if isinstance(obj, dict) else None
        persisted = await _update_mapping_by_account(
            account_id,
            meta_updates={"last_merchant_capability_update": merchant_payload},
        )
        await _append_account_event(
            account_id,
            "v2.core.account[configuration.merchant].capability_status_updated",
            {"merchant": merchant_payload},
        )
    return {
        "handled": True,
        "event_type": "v2.core.account[configuration.merchant].capability_status_updated",
        "account_id": account_id,
        "persisted": persisted,
    }


async def _handle_v2_customer_capability_status_updated(event: Any) -> dict[str, Any]:
    obj = _event_data_object(event)
    account_id = _extract_account_id_from_v2_event_object(obj)
    persisted = False
    if account_id:
        customer_payload = (obj.get("configuration") or {}).get("customer") if isinstance(obj, dict) else None
        persisted = await _update_mapping_by_account(
            account_id,
            meta_updates={"last_customer_capability_update": customer_payload},
        )
        await _append_account_event(
            account_id,
            "v2.core.account[configuration.customer].capability_status_updated",
            {"customer": customer_payload},
        )
    return {
        "handled": True,
        "event_type": "v2.core.account[configuration.customer].capability_status_updated",
        "account_id": account_id,
        "persisted": persisted,
    }


@router.post("/webhooks/thin")
async def webhook_thin_v2(request: Request, settings: Settings):
    """Handle thin V2 account update events.

    This uses Stripe Client thin parsing + event retrieval flow:
      thin_event = stripe_client.parse_thin_event(...)
      event = stripe_client.v2.core.events.retrieve(thin_event.id)
    """
    stripe_client = _require_stripe_client(settings)

    # TODO(you): set STRIPE_CONNECT_THIN_WEBHOOK_SECRET from your webhook destination.
    webhook_secret = (os.getenv("STRIPE_CONNECT_THIN_WEBHOOK_SECRET") or "").strip()
    if not webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Missing STRIPE_CONNECT_THIN_WEBHOOK_SECRET for thin webhook verification.",
        )

    signature = request.headers.get("stripe-signature")
    if not signature:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Stripe signature header")

    payload = await request.body()

    if not hasattr(stripe_client, "parse_thin_event"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Current Stripe SDK does not expose parse_thin_event. Upgrade to latest Stripe SDK.",
        )

    # parse_thin_event is the Python equivalent for JS parseThinEvent in Stripe docs.
    thin_event = stripe_client.parse_thin_event(payload, signature, webhook_secret)
    thin_event_id = thin_event.get("id") if isinstance(thin_event, dict) else getattr(thin_event, "id", None)
    if not thin_event_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid thin event envelope: {thin_event}"
        )

    full_event = stripe_client.v2.core.events.retrieve(thin_event_id)
    event_type = _event_type(full_event)

    if event_type == "v2.core.account[requirements].updated":
        result = await _handle_v2_requirements_updated(full_event)
    elif event_type == "v2.core.account[.recipient].capability_status_updated":
        result = await _handle_v2_recipient_capability_status_updated(full_event)
    elif event_type == "v2.core.account[configuration.merchant].capability_status_updated":
        result = await _handle_v2_merchant_capability_status_updated(full_event)
    elif event_type == "v2.core.account[configuration.customer].capability_status_updated":
        result = await _handle_v2_customer_capability_status_updated(full_event)
    else:
        result = {"handled": False, "reason": "unmapped_event_type", "event_type": event_type}

    return JSONResponse({"ok": True, "event_type": event_type, "result": result})


async def _handle_subscription_event(event: Any) -> dict[str, Any]:
    """Handle subscription update/delete events and persist status by connected account ID."""
    obj = _event_data_object(event)

    account_id = obj.get("customer_account")
    if not isinstance(account_id, str) or not account_id.startswith("acct_"):
        return {"handled": False, "reason": "missing_customer_account"}

    subscription_id = obj.get("id") if isinstance(obj.get("id"), str) else None
    subscription_status = obj.get("status") if isinstance(obj.get("status"), str) else None
    subscription_price_id = None

    items = obj.get("items", {}).get("data", []) if isinstance(obj.get("items"), dict) else []
    if items and isinstance(items[0], dict):
        price = items[0].get("price")
        if isinstance(price, dict) and isinstance(price.get("id"), str):
            subscription_price_id = price["id"]

    await _save_subscription_state(account_id, subscription_id, subscription_status, subscription_price_id)
    await _append_account_event(
        account_id,
        "subscription.state_changed",
        {
            "subscription_id": subscription_id,
            "subscription_status": subscription_status,
            "subscription_price_id": subscription_price_id,
        },
    )

    return {
        "handled": True,
        "account_id": account_id,
        "subscription_id": subscription_id,
        "subscription_status": subscription_status,
        "subscription_price_id": subscription_price_id,
    }


async def _handle_payment_method_event(event: Any) -> dict[str, Any]:
    obj = _event_data_object(event)
    customer_account = obj.get("customer_account")
    return {"handled": True, "customer_account": customer_account}


async def _handle_customer_updated_event(event: Any) -> dict[str, Any]:
    obj = _event_data_object(event)
    customer_account = obj.get("customer_account")
    default_pm = (obj.get("invoice_settings") or {}).get("default_payment_method") if isinstance(obj, dict) else None
    return {"handled": True, "customer_account": customer_account, "default_payment_method": default_pm}


async def _handle_tax_id_event(event: Any) -> dict[str, Any]:
    obj = _event_data_object(event)
    customer_account = obj.get("customer_account")
    return {"handled": True, "customer_account": customer_account}


@router.post("/webhooks/billing")
async def webhook_billing_snapshot(request: Request, settings: Settings):
    """Handle classic (non-thin) subscription/billing webhook events for connected-account subscriptions."""
    stripe_client = _require_stripe_client(settings)

    # TODO(you): set STRIPE_CONNECT_BILLING_WEBHOOK_SECRET from webhook endpoint settings.
    webhook_secret = (os.getenv("STRIPE_CONNECT_BILLING_WEBHOOK_SECRET") or "").strip()
    if not webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Missing STRIPE_CONNECT_BILLING_WEBHOOK_SECRET for billing webhook verification.",
        )

    signature = request.headers.get("stripe-signature")
    if not signature:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Stripe signature header")

    payload = await request.body()

    # We prefer SDK-based parser to keep all Stripe calls through StripeClient.
    if not hasattr(stripe_client, "parse_event_notification"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Current Stripe SDK does not expose parse_event_notification. Upgrade Stripe SDK.",
        )

    event_notification = stripe_client.parse_event_notification(payload, signature, webhook_secret)
    event_id = (
        event_notification.get("id")
        if isinstance(event_notification, dict)
        else getattr(event_notification, "id", None)
    )

    # Retrieve canonical event payload for deterministic handling.
    event = stripe_client.v1.events.retrieve(event_id) if event_id else json.loads(payload.decode("utf-8"))
    event_type = _event_type(event)

    if event_type in {"customer.subscription.updated", "customer.subscription.deleted"}:
        result = await _handle_subscription_event(event)
    elif event_type in {"payment_method.attached", "payment_method.detached"}:
        result = await _handle_payment_method_event(event)
    elif event_type == "customer.updated":
        result = await _handle_customer_updated_event(event)
    elif event_type in {"customer.tax_id.created", "customer.tax_id.deleted", "customer.tax_id.updated"}:
        result = await _handle_tax_id_event(event)
    elif event_type in {
        "billing_portal.configuration.created",
        "billing_portal.configuration.updated",
        "billing_portal.session.created",
    }:
        result = {"handled": True, "event_type": event_type}
    else:
        result = {"handled": False, "reason": "unmapped_event_type", "event_type": event_type}

    return JSONResponse({"ok": True, "event_type": event_type, "result": result})


@router.get("/events")
async def list_recent_connect_events(auth: RequiredAuth):
    """Return recent Connect-related webhook events from mapping metadata for the authenticated user."""
    user_id = str(auth.get("user_id") or "")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authenticated user_id")

    mapping = await _get_mapping_by_user(user_id)
    if not mapping:
        return {"events": []}

    meta = mapping.get("meta") or {}
    events = list(meta.get("events") or [])
    # Most recent first for faster operational triage.
    events.reverse()
    return {
        "stripe_account_id": mapping.get("stripe_account_id"),
        "event_count": len(events),
        "events": events[:100],
    }


@router.get("/account/{account_id}")
async def get_connect_account_status(account_id: str, settings: Settings):
    """JSON helper to fetch current account status directly from Stripe API."""
    stripe_client = _require_stripe_client(settings)
    account = stripe_client.v2.core.accounts.retrieve(
        account_id,
        {"include": ["configuration.merchant", "requirements"]},
    )
    ready, req_status, onboarding_complete = _onboarding_flags(account)
    return {
        "account_id": account_id,
        "ready_to_process_payments": ready,
        "requirements_status": req_status,
        "onboarding_complete": onboarding_complete,
    }
