"""Tests for API versioning middleware and version metadata.

Covers:
- application.mothership.api.versioning (VersionMetadata, get_version_metadata, registry)
- application.mothership.middleware.versioning.VersioningMiddleware (header injection)
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi import FastAPI, Response
from fastapi.testclient import TestClient

from application.mothership.api.versioning import (
    ApiVersion,
    VersionMetadata,
    VersionStatus,
    get_version_metadata,
)
from application.mothership.middleware.versioning import VersioningMiddleware

# ---------------------------------------------------------------------------
# get_version_metadata / registry
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGetVersionMetadata:
    def test_known_string_version_resolves(self) -> None:
        meta = get_version_metadata("v1")
        assert meta is not None
        assert meta.version == ApiVersion.V1

    def test_case_insensitive_lookup(self) -> None:
        meta = get_version_metadata("V1")
        assert meta is not None
        assert meta.version == ApiVersion.V1

    def test_enum_version_resolves(self) -> None:
        meta = get_version_metadata(ApiVersion.V2)
        assert meta is not None
        assert meta.version == ApiVersion.V2

    def test_unknown_version_returns_none(self) -> None:
        assert get_version_metadata("v99") is None

    def test_v2_marked_experimental(self) -> None:
        meta = get_version_metadata("v2")
        assert meta is not None
        assert meta.status == VersionStatus.EXPERIMENTAL


# ---------------------------------------------------------------------------
# VersionMetadata.inject_headers
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestVersionMetadataHeaders:
    def test_injects_version_and_status(self) -> None:
        meta = VersionMetadata(version=ApiVersion.V1, status=VersionStatus.STABLE)
        resp = Response()
        meta.inject_headers(resp)
        assert resp.headers["X-API-Version"] == "v1"
        assert resp.headers["X-API-Status"] == "stable"

    def test_deprecation_header_when_deprecated(self) -> None:
        deprecated_at = datetime(2025, 1, 1, tzinfo=UTC)
        meta = VersionMetadata(
            version=ApiVersion.V1,
            status=VersionStatus.DEPRECATED,
            deprecated_at=deprecated_at,
            migration_guide_url="https://example.com/migrate",
        )
        resp = Response()
        meta.inject_headers(resp)
        assert "Deprecation" in resp.headers
        assert resp.headers["Deprecation"] == f"@{int(deprecated_at.timestamp())}"
        assert "deprecation-guide" in resp.headers["Link"]

    def test_no_deprecation_header_when_stable(self) -> None:
        meta = VersionMetadata(version=ApiVersion.V1, status=VersionStatus.STABLE)
        resp = Response()
        meta.inject_headers(resp)
        assert "Deprecation" not in resp.headers

    def test_sunset_header_when_set(self) -> None:
        sunset_at = datetime(2026, 12, 31, 23, 59, 59, tzinfo=UTC)
        meta = VersionMetadata(
            version=ApiVersion.V1,
            status=VersionStatus.SUNSET,
            sunset_at=sunset_at,
        )
        resp = Response()
        meta.inject_headers(resp)
        assert "Sunset" in resp.headers
        assert "2026" in resp.headers["Sunset"]


# ---------------------------------------------------------------------------
# VersioningMiddleware
# ---------------------------------------------------------------------------


def _make_app(default_version: str = "v1") -> FastAPI:
    app = FastAPI()

    @app.get("/api/v1/resource")
    def v1_resource():
        return {"ok": True}

    @app.get("/api/v2/resource")
    def v2_resource():
        return {"ok": True}

    @app.get("/other")
    def other():
        return {"ok": True}

    app.add_middleware(VersioningMiddleware, default_version=default_version)
    return app


@pytest.mark.unit
class TestVersioningMiddleware:
    def test_v1_path_gets_v1_headers(self) -> None:
        client = TestClient(_make_app(), raise_server_exceptions=False)
        r = client.get("/api/v1/resource")
        assert r.headers.get("X-API-Version") == "v1"
        assert r.headers.get("X-API-Status") == "stable"

    def test_v2_path_gets_v2_headers(self) -> None:
        client = TestClient(_make_app(), raise_server_exceptions=False)
        r = client.get("/api/v2/resource")
        assert r.headers.get("X-API-Version") == "v2"
        assert r.headers.get("X-API-Status") == "experimental"

    def test_non_versioned_path_falls_back_to_default(self) -> None:
        client = TestClient(_make_app(default_version="v1"), raise_server_exceptions=False)
        r = client.get("/other")
        # default_version v1 is registered, so headers are injected
        assert r.headers.get("X-API-Version") == "v1"

    def test_unregistered_default_version_injects_no_headers(self) -> None:
        client = TestClient(_make_app(default_version="experimental"), raise_server_exceptions=False)
        r = client.get("/other")
        # "experimental" is not in the registry → get_version_metadata returns None
        assert "X-API-Version" not in r.headers
