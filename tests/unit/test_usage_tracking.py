"""Tests for UsageTrackingMiddleware and UsageMeter cost logic.

The middleware constructs a real UsageMeter (repository + settings), so the
pure-logic and passthrough paths are tested by bypassing __init__ and injecting
a stub meter. record_usage is never reached on excluded or unauthenticated
requests, so no database is required.
"""

from __future__ import annotations

import pytest
from starlette.requests import Request

from application.mothership.middleware.usage_tracking import UsageTrackingMiddleware
from application.mothership.services.billing.meter import UsageMeter


def _request(path: str = "/api/data", method: str = "GET", user_id: str | None = None) -> Request:
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 9999),
    }
    req = Request(scope)
    if user_id is not None:
        req.state.user_id = user_id
    return req


def _middleware(exclude_paths: list[str] | None = None) -> UsageTrackingMiddleware:
    mw = UsageTrackingMiddleware.__new__(UsageTrackingMiddleware)
    mw.exclude_paths = exclude_paths or ["/health", "/ping", "/docs", "/openapi.json", "/redoc", "/metrics"]
    mw.usage_meter = _StubMeter()
    return mw


class _StubMeter:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def record_usage(self, **kwargs: object) -> None:
        self.calls.append(dict(kwargs))


# ---------------------------------------------------------------------------
# _should_track
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestShouldTrack:
    def test_excluded_path_not_tracked(self) -> None:
        mw = _middleware()
        assert mw._should_track("/health") is False
        assert mw._should_track("/metrics") is False

    def test_regular_path_tracked(self) -> None:
        mw = _middleware()
        assert mw._should_track("/api/data") is True

    def test_prefix_match_excludes(self) -> None:
        mw = _middleware()
        assert mw._should_track("/health/live") is False


# ---------------------------------------------------------------------------
# dispatch
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
class TestDispatch:
    async def test_excluded_path_skips_metering(self) -> None:
        mw = _middleware()
        sentinel = object()

        async def call_next(_req: Request) -> object:
            return sentinel

        result = await mw.dispatch(_request(path="/health"), call_next)
        assert result is sentinel
        assert mw.usage_meter.calls == []

    async def test_unauthenticated_request_skips_metering(self) -> None:
        mw = _middleware()
        sentinel = object()

        async def call_next(_req: Request) -> object:
            return sentinel

        result = await mw.dispatch(_request(path="/api/data", user_id=None), call_next)
        assert result is sentinel
        assert mw.usage_meter.calls == []

    async def test_authenticated_success_records_usage(self) -> None:
        mw = _middleware()

        class _Resp:
            status_code = 200

        resp = _Resp()

        async def call_next(_req: Request) -> _Resp:
            return resp

        result = await mw.dispatch(_request(path="/api/data", user_id="user-1"), call_next)
        assert result is resp
        assert len(mw.usage_meter.calls) == 1
        assert mw.usage_meter.calls[0]["user_id"] == "user-1"

    async def test_authenticated_error_response_not_metered(self) -> None:
        mw = _middleware()

        class _Resp:
            status_code = 500

        async def call_next(_req: Request) -> _Resp:
            return _Resp()

        await mw.dispatch(_request(path="/api/data", user_id="user-1"), call_next)
        assert mw.usage_meter.calls == []

    async def test_metering_failure_does_not_break_request(self) -> None:
        mw = _middleware()

        class _BoomMeter:
            async def record_usage(self, **kwargs: object) -> None:
                raise RuntimeError("db down")

        mw.usage_meter = _BoomMeter()

        class _Resp:
            status_code = 200

        resp = _Resp()

        async def call_next(_req: Request) -> _Resp:
            return resp

        # Should swallow the meter error and still return the response
        result = await mw.dispatch(_request(path="/api/data", user_id="user-1"), call_next)
        assert result is resp


# ---------------------------------------------------------------------------
# UsageMeter.get_cost_units (pure)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestUsageMeterCosts:
    def _meter(self) -> UsageMeter:
        # Inject a stub repo to avoid touching the real repository / database
        return UsageMeter(usage_repo=object())  # type: ignore[arg-type]

    def test_batch_endpoint_costs_more(self) -> None:
        assert self._meter().get_cost_units("/api/batch_analysis") == 10

    def test_relationship_endpoint_cost(self) -> None:
        assert self._meter().get_cost_units("/api/relationship_analysis") == 1

    def test_scenario_endpoint_cost(self) -> None:
        assert self._meter().get_cost_units("/api/scenario_analysis") == 5

    def test_unknown_endpoint_default_cost(self) -> None:
        assert self._meter().get_cost_units("/api/something_else") == 1
