"""Route map regression tests for the canonical Mothership app."""

from __future__ import annotations

from application.mothership.main import app as canonical_app
from application.mothership.main import create_app
from application.mothership.main_unified import app as unified_app


def test_canonical_route_map_has_single_prefixed_public_paths() -> None:
    """Public routers should be versioned once, not double-prefixed."""
    app = create_app()
    paths = set(app.openapi()["paths"])

    assert "/api/v1/canvas/route" in paths
    assert "/api/v1/rag/query/stream" in paths
    assert "/api/v1/rag/query/batch" in paths

    assert "/api/v1/api/v1/canvas/route" not in paths
    assert "/rag/rag/query/stream" not in paths


def test_metrics_endpoint_is_not_registered_multiple_times() -> None:
    """The canonical app should expose at most one /metrics route."""
    app = create_app()
    paths = [route.path for route in app.routes if hasattr(route, "path")]

    assert paths.count("/metrics") <= 1


def test_main_unified_delegates_to_canonical_app() -> None:
    """The compatibility shim should point at the canonical app object."""
    assert unified_app is canonical_app


def test_product_routers_are_versioned_under_api_v1() -> None:
    """Product routers (corruption, admission, drt, safety) must be under /api/v1, not root."""
    app = create_app()
    paths = set(app.openapi()["paths"])

    # Versioned paths exist
    assert any(p.startswith("/api/v1/corruption") for p in paths)
    assert any(p.startswith("/api/v1/admission") for p in paths)
    assert any(p.startswith("/api/v1/drt") for p in paths)
    assert any(p.startswith("/api/v1/safety") for p in paths)

    # Root-level product paths are gone
    assert not any(p.startswith("/corruption") and not p.startswith("/api/") for p in paths)
    assert not any(p.startswith("/admission") and not p.startswith("/api/") for p in paths)
    assert not any(p.startswith("/drt") and not p.startswith("/api/") for p in paths)
    assert not any(p.startswith("/safety") and not p.startswith("/api/") for p in paths)


def test_operational_endpoints_remain_at_root() -> None:
    """Health probes, ping, and security status must stay root-level (no /api/v1 prefix)."""
    app = create_app()
    paths = set(app.openapi()["paths"])

    # K8s probes
    assert "/health" in paths or any(p.startswith("/health") for p in paths)
    assert "/ping" in paths
    assert "/security/status" in paths
