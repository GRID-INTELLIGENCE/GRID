"""Tests for Stripe Connect demo router behavior."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request

from application.mothership import dependencies as mothership_dependencies
from application.mothership.routers import stripe_connect_demo
from application.mothership.routers.stripe_connect_demo import _generate_csrf_token


class _FakeAccountsAPI:
    def __init__(self):
        self.created_payloads = []
        self._accounts: dict[str, dict] = {}
        self._counter = 0

    def create(self, payload: dict):
        self.created_payloads.append(payload)
        self._counter += 1
        account_id = f"acct_test_{self._counter}"
        account = {
            "id": account_id,
            "configuration": {"merchant": {"capabilities": {"card_payments": {"status": "active"}}}},
            "requirements": {"summary": {"minimum_deadline": {"status": "none"}}},
        }
        self._accounts[account_id] = account
        return account

    def retrieve(self, account_id: str, _params: dict | None = None):
        account = self._accounts.get(account_id)
        if account is None:
            raise ValueError("account_not_found")
        return account


class _FakeAccountLinksAPI:
    def create(self, payload: dict):
        account_id = payload.get("account", "acct_unknown")
        return {"url": f"https://connect.stripe.test/onboard/{account_id}"}


class _FakeEventsAPI:
    def __init__(self):
        self._events: dict[str, dict] = {}

    def set_event(self, event_id: str, event_payload: dict):
        self._events[event_id] = event_payload

    def retrieve(self, event_id: str):
        return self._events[event_id]


class _FakeProductsAPI:
    def __init__(self):
        self.products = []

    def create(self, payload: dict, _opts: dict):
        product_id = f"prod_{len(self.products) + 1}"
        product = {
            "id": product_id,
            "name": payload.get("name", ""),
            "description": payload.get("description", ""),
            "default_price": {
                "unit_amount": payload.get("default_price_data", {}).get("unit_amount", 100),
                "currency": payload.get("default_price_data", {}).get("currency", "usd"),
            },
        }
        self.products.append(product)
        return product

    def list(self, _params: dict, _opts: dict):
        return {"data": self.products}


class _FakeCheckoutSessionsAPI:
    def create(self, _payload: dict, _opts: dict | None = None):
        return {"url": "https://checkout.stripe.test/session_123"}


class _FakeBillingPortalSessionsAPI:
    def create(self, _payload: dict):
        return {"url": "https://billing.stripe.test/session_123"}


class _FakeV1:
    def __init__(self):
        self.products = _FakeProductsAPI()
        self.checkout = SimpleNamespace(sessions=_FakeCheckoutSessionsAPI())
        self.billing_portal = SimpleNamespace(sessions=_FakeBillingPortalSessionsAPI())
        self.events = _FakeEventsAPI()


class _FakeV2:
    def __init__(self):
        self.core = SimpleNamespace(
            accounts=_FakeAccountsAPI(),
            account_links=_FakeAccountLinksAPI(),
            events=_FakeEventsAPI(),
        )


class _FakeStripeClient:
    def __init__(self, _api_key: str):
        self.v1 = _FakeV1()
        self.v2 = _FakeV2()

    def parse_thin_event(self, _payload: bytes, _signature: str, _secret: str):
        return {"id": "evt_thin_123"}

    def parse_event_notification(self, _payload: bytes, _signature: str, _secret: str):
        return {"id": "evt_snapshot_123"}


@pytest.fixture
def connect_env(monkeypatch):
    monkeypatch.setenv("MOTHERSHIP_PERSISTENCE_MODE", "memory")
    monkeypatch.setenv("STRIPE_CONNECT_THIN_WEBHOOK_SECRET", "whsec_thin_test")
    monkeypatch.setenv("STRIPE_CONNECT_BILLING_WEBHOOK_SECRET", "whsec_snap_test")
    monkeypatch.setenv("STRIPE_CONNECT_SUBSCRIPTION_PRICE_ID", "price_test_sub")
    monkeypatch.setenv("STRIPE_CONNECT_APPLICATION_FEE_AMOUNT", "123")
    monkeypatch.setenv("CSRF_SECRET", "test_csrf_secret_for_stripe_connect_demo")
    stripe_connect_demo._CONNECT_MAP_MEMORY.clear()


@pytest.fixture
def fake_client(monkeypatch):
    client = _FakeStripeClient("sk_test_123")

    def _factory(_api_key: str):
        return client

    monkeypatch.setattr(stripe_connect_demo, "StripeClient", _factory)
    return client


@pytest.fixture
def settings():
    return SimpleNamespace(payment=SimpleNamespace(stripe_secret_key="sk_test_123"))


def _dummy_request() -> Request:
    scope = {"type": "http", "method": "POST", "headers": []}

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    return Request(scope, receive)


def _request_with_signature(body: bytes) -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "headers": [(b"stripe-signature", b"sig_test")],
    }
    sent = False

    async def receive():
        nonlocal sent
        if sent:
            return {"type": "http.request", "body": b"", "more_body": False}
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    return Request(scope, receive)


class TestConnectIdempotency:
    @pytest.mark.asyncio
    async def test_create_connected_account_is_idempotent_per_user(self, connect_env, fake_client, settings):
        auth = {"user_id": "user_123"}

        response1 = await stripe_connect_demo.create_connected_account(
            request=_dummy_request(),
            auth=auth,
            settings=settings,
            display_name="Merchant One",
            contact_email="merchant@example.com",
            csrf_token=_generate_csrf_token(),
        )
        assert response1.status_code == 303
        assert len(fake_client.v2.core.accounts.created_payloads) == 1

        response2 = await stripe_connect_demo.create_connected_account(
            request=_dummy_request(),
            auth=auth,
            settings=settings,
            display_name="Merchant One Updated",
            contact_email="merchant2@example.com",
            csrf_token=_generate_csrf_token(),
        )
        assert response2.status_code == 303
        assert len(fake_client.v2.core.accounts.created_payloads) == 1

        mapping = stripe_connect_demo._CONNECT_MAP_MEMORY["user_123"]
        assert mapping["stripe_account_id"] == "acct_test_1"
        assert mapping["meta"]["idempotent_reuse"] is True


class TestThinWebhookPersistence:
    @pytest.mark.asyncio
    async def test_thin_requirements_update_persists_meta_and_event(self, connect_env, fake_client, settings):
        auth = {"user_id": "user_abc"}
        await stripe_connect_demo.create_connected_account(
            request=_dummy_request(),
            auth=auth,
            settings=settings,
            display_name="Merchant ABC",
            contact_email="abc@example.com",
            csrf_token=_generate_csrf_token(),
        )

        fake_client.v2.core.events.set_event(
            "evt_thin_123",
            {
                "type": "v2.core.account[requirements].updated",
                "data": {
                    "object": {
                        "id": "acct_test_1",
                        "requirements": {
                            "summary": {
                                "minimum_deadline": {"status": "currently_due"},
                                "pending_verification": ["business_profile.mcc"],
                            }
                        },
                    }
                },
            },
        )

        result = await stripe_connect_demo.webhook_thin_v2(
            request=_request_with_signature(b'{"id":"evt_thin_123"}'),
            settings=settings,
        )
        assert result.status_code == 200

        mapping = stripe_connect_demo._CONNECT_MAP_MEMORY["user_abc"]
        assert "last_requirements_update" in mapping["meta"]
        assert mapping["meta"]["last_requirements_update"]["minimum_deadline"]["status"] == "currently_due"

        events = mapping["meta"].get("events", [])
        assert len(events) >= 1
        assert events[-1]["event_type"] == "v2.core.account[requirements].updated"


class TestConnectEventsEndpoint:
    @pytest.mark.asyncio
    async def test_events_endpoint_returns_most_recent_first(self, connect_env, fake_client, settings):
        auth = {"user_id": "user_evt"}
        await stripe_connect_demo.create_connected_account(
            request=_dummy_request(),
            auth=auth,
            settings=settings,
            display_name="Merchant EVT",
            contact_email="evt@example.com",
            csrf_token=_generate_csrf_token(),
        )

        # Seed two timeline events and ensure endpoint reverses to most-recent-first.
        await stripe_connect_demo._append_account_event("acct_test_1", "event.old", {"n": 1})
        await stripe_connect_demo._append_account_event("acct_test_1", "event.new", {"n": 2})

        data = await stripe_connect_demo.list_recent_connect_events(auth=auth)

        assert data["event_count"] == 2
        assert data["events"][0]["event_type"] == "event.new"
        assert data["events"][1]["event_type"] == "event.old"


@pytest.fixture
def connect_route_client(connect_env, fake_client, settings):
    app = FastAPI()
    app.include_router(stripe_connect_demo.router, prefix="/api/v1")

    async def _auth_override():
        return {"authenticated": True, "user_id": "user_route"}

    def _settings_override():
        return settings

    app.dependency_overrides[mothership_dependencies.require_authentication] = _auth_override
    app.dependency_overrides[mothership_dependencies.get_config] = _settings_override
    with TestClient(app) as client:
        yield client


class TestConnectRouteIntegration:
    def test_dashboard_renders_when_no_mapping_exists(self, connect_route_client):
        response = connect_route_client.get("/api/v1/connect-demo/dashboard")
        assert response.status_code == 200
        assert "Stripe Connect Demo Dashboard" in response.text
        assert "No connected account mapped yet." in response.text

    def test_create_account_route_then_dashboard_shows_connected_account(self, connect_route_client, fake_client):
        create_response = connect_route_client.post(
            "/api/v1/connect-demo/accounts/create",
            data={
                "display_name": "Route Merchant",
                "contact_email": "route@example.com",
                "csrf_token": _generate_csrf_token(),
            },
            follow_redirects=False,
        )
        assert create_response.status_code == 303
        assert create_response.headers["location"] == "/api/v1/connect-demo/dashboard"
        assert len(fake_client.v2.core.accounts.created_payloads) == 1

        dashboard_response = connect_route_client.get("/api/v1/connect-demo/dashboard")
        assert dashboard_response.status_code == 200
        assert "acct_test_1" in dashboard_response.text
        assert "Open storefront page" in dashboard_response.text

    def test_events_route_returns_most_recent_first(self, connect_route_client):
        stripe_connect_demo._CONNECT_MAP_MEMORY["user_route"] = {
            "user_id": "user_route",
            "stripe_account_id": "acct_test_route",
            "subscription_id": None,
            "subscription_status": None,
            "subscription_price_id": None,
            "meta": {
                "events": [
                    {
                        "at": datetime(2026, 2, 12, tzinfo=UTC).isoformat(),
                        "event_type": "event.old",
                        "payload": {"n": 1},
                    },
                    {
                        "at": datetime(2026, 2, 13, tzinfo=UTC).isoformat(),
                        "event_type": "event.new",
                        "payload": {"n": 2},
                    },
                ]
            },
        }

        response = connect_route_client.get("/api/v1/connect-demo/events")
        assert response.status_code == 200
        payload = response.json()
        assert payload["event_count"] == 2
        assert payload["events"][0]["event_type"] == "event.new"
        assert payload["events"][1]["event_type"] == "event.old"

    def test_account_status_route_returns_expected_shape(self, connect_route_client, fake_client):
        fake_client.v2.core.accounts._accounts["acct_test_status"] = {
            "id": "acct_test_status",
            "configuration": {"merchant": {"capabilities": {"card_payments": {"status": "active"}}}},
            "requirements": {"summary": {"minimum_deadline": {"status": "none"}}},
        }

        response = connect_route_client.get("/api/v1/connect-demo/account/acct_test_status")
        assert response.status_code == 200
        payload = response.json()
        assert payload["account_id"] == "acct_test_status"
        assert payload["ready_to_process_payments"] is True
        assert payload["requirements_status"] == "none"
        assert payload["onboarding_complete"] is True
