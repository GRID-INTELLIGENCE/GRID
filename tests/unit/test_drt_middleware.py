"""Tests for ComprehensiveDRTMiddleware (DRT behavioral monitoring).

Focuses on the pure-logic surface (signature building, normalization, similarity
scoring, escalation bookkeeping, status) which needs no database. Dispatch is
exercised with async stubs, short-circuiting DB initialization.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from starlette.requests import Request

from application.mothership.middleware.drt_middleware import (
    BehavioralSignature,
    ComprehensiveDRTMiddleware,
)


def _mw(**kwargs: object) -> ComprehensiveDRTMiddleware:
    return ComprehensiveDRTMiddleware(app=None, **kwargs)


def _request(method: str = "GET", path: str = "/api/test", query: str = "", headers: dict | None = None) -> Request:
    raw_headers = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "query_string": query.encode(),
        "headers": raw_headers,
        "client": ("127.0.0.1", 12345),
    }
    return Request(scope)


# ---------------------------------------------------------------------------
# BehavioralSignature
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestBehavioralSignature:
    def test_to_dict_round_trips_fields(self) -> None:
        sig = BehavioralSignature(
            path_pattern="/api/{ID}",
            method="POST",
            headers=("accept", "content-type"),
            body_pattern="json",
            query_pattern="a&b",
        )
        d = sig.to_dict()
        assert d["path_pattern"] == "/api/{ID}"
        assert d["method"] == "POST"
        assert d["headers"] == ("accept", "content-type")
        assert d["request_count"] == 0
        assert "timestamp" in d


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestNormalization:
    def test_normalize_path_replaces_numeric_id(self) -> None:
        mw = _mw()
        assert mw._normalize_path("/api/users/123") == "/api/users/{ID}"

    def test_normalize_path_replaces_uuid(self) -> None:
        mw = _mw()
        uuid = "abcdef01-2345-6789-abcd-ef0123456789"
        assert mw._normalize_path(f"/api/items/{uuid}") == "/api/items/{UUID}"

    def test_normalize_path_leaves_plain_path(self) -> None:
        mw = _mw()
        assert mw._normalize_path("/api/health") == "/api/health"

    def test_normalize_query_sorts_keys(self) -> None:
        mw = _mw()
        assert mw._normalize_query("b=2&a=1") == "a&b"


# ---------------------------------------------------------------------------
# Similarity scoring
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSimilarity:
    def _sig(self, method: str = "GET", path: str = "/api/x", headers: tuple[str, ...] = ()) -> BehavioralSignature:
        return BehavioralSignature(path_pattern=path, method=method, headers=headers)

    def test_different_method_is_zero(self) -> None:
        mw = _mw()
        a = self._sig(method="GET")
        b = self._sig(method="POST")
        assert mw._calculate_similarity(a, b) == 0.0

    def test_different_path_is_zero(self) -> None:
        mw = _mw()
        a = self._sig(path="/api/a")
        b = self._sig(path="/api/b")
        assert mw._calculate_similarity(a, b) == 0.0

    def test_no_headers_both_sides_is_full_similarity(self) -> None:
        mw = _mw()
        a = self._sig(headers=())
        b = self._sig(headers=())
        assert mw._calculate_similarity(a, b) == 1.0

    def test_one_empty_header_set_is_zero(self) -> None:
        mw = _mw()
        a = self._sig(headers=("accept",))
        b = self._sig(headers=())
        assert mw._calculate_similarity(a, b) == 0.0

    def test_jaccard_header_overlap(self) -> None:
        mw = _mw()
        a = self._sig(headers=("accept", "content-type"))
        b = self._sig(headers=("accept", "x-custom"))
        # intersection {accept}=1, union {accept,content-type,x-custom}=3
        assert mw._calculate_similarity(a, b) == pytest.approx(1 / 3)

    def test_check_similarity_returns_best_match(self) -> None:
        mw = _mw()
        target = self._sig(headers=("accept", "content-type"))
        mw.attack_vectors = [
            self._sig(headers=("x-other",)),
            self._sig(headers=("accept", "content-type")),
        ]
        score, matched = mw._check_similarity(target)
        assert score == 1.0
        assert matched is not None

    def test_check_similarity_empty_vectors(self) -> None:
        mw = _mw()
        score, matched = mw._check_similarity(self._sig())
        assert score == 0.0
        assert matched is None


# ---------------------------------------------------------------------------
# Signature building (filters sensitive headers)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestBuildSignature:
    def test_strips_sensitive_headers(self) -> None:
        mw = _mw()
        req = _request(
            headers={
                "Authorization": "Bearer x",
                "Cookie": "a=b",
                "X-API-Key": "secret",
                "X-Request-ID": "rid",
                "Accept": "application/json",
            }
        )
        sig = mw._build_signature(req)
        assert "accept" in sig.headers
        assert "authorization" not in sig.headers
        assert "cookie" not in sig.headers
        assert "x-api-key" not in sig.headers

    def test_normalizes_path_in_signature(self) -> None:
        mw = _mw()
        req = _request(path="/api/users/42")
        sig = mw._build_signature(req)
        assert sig.path_pattern == "/api/users/{ID}"

    def test_query_pattern_extracted(self) -> None:
        mw = _mw()
        req = _request(query="z=1&a=2")
        sig = mw._build_signature(req)
        assert sig.query_pattern == "a&z"

    def test_body_pattern_none_for_get(self) -> None:
        mw = _mw()
        req = _request(method="GET")
        assert mw._build_signature(req).body_pattern is None


# ---------------------------------------------------------------------------
# Escalation / status / cleanup
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestEscalationAndStatus:
    def test_escalate_endpoint_records_path(self) -> None:
        mw = _mw(escalation_timeout_minutes=30)
        mw._escalate_endpoint("/api/target")
        assert "/api/target" in mw.ESCALATED_ENDPOINTS
        assert mw.ESCALATED_ENDPOINTS["/api/target"] > datetime.now(UTC)

    def test_get_status_reports_counts(self) -> None:
        mw = _mw()
        mw.ESCALATED_ENDPOINTS["/a"] = datetime.now(UTC)
        mw.behavioral_history.append(BehavioralSignature("/a", "GET", ()))
        status = mw.get_status()
        assert status["enabled"] is True
        assert status["escalated_endpoints"] == 1
        assert status["behavioral_history_count"] == 1

    def test_cleanup_removes_old_history(self) -> None:
        mw = _mw(retention_hours=1)
        old = BehavioralSignature("/a", "GET", ())
        old.timestamp = datetime.now(UTC) - timedelta(hours=5)
        fresh = BehavioralSignature("/b", "GET", ())
        mw.behavioral_history = [old, fresh]
        mw._cleanup_old_entries()
        assert old not in mw.behavioral_history
        assert fresh in mw.behavioral_history


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
class TestDispatch:
    async def test_disabled_passes_through(self) -> None:
        mw = _mw(enabled=False)
        sentinel = object()

        async def call_next(_req: Request) -> object:
            return sentinel

        result = await mw.dispatch(_request(), call_next)
        assert result is sentinel

    async def test_enabled_no_vectors_passes_through_and_records(self) -> None:
        mw = _mw(enabled=True)
        mw._initialized = True  # skip DB init

        class _SigRepo:
            async def save(self, *args: object, **kwargs: object) -> None:
                return None

        mw._sig_repo = _SigRepo()  # absorb the fire-and-forget persist task cleanly
        sentinel = object()

        async def call_next(_req: Request) -> object:
            return sentinel

        result = await mw.dispatch(_request(path="/api/users/7"), call_next)
        assert result is sentinel
        assert len(mw.behavioral_history) == 1
