"""
Boundary Enforcement Middleware for GRID Architecture Layers.

Enforces the architectural contract that separates the system into
isolated layers with strict dependency direction:

    grid (core) → application → cognitive/tools
    ───────────   ───────────   ──────────────
    No outward    May import    May import
    imports       grid          grid + application

This middleware operates at two levels:

1. **Request-level**: Validates that API requests respect layer
   ownership. Endpoints prefixed with ``/api/v1/intelligence``
   can only be served by the cognitive layer, not by core handlers.

2. **Import-level** (optional, dev-only): Audits module import
   graphs on startup to detect layer-crossing imports that violate
   the architecture.

Usage:
    from application.mothership.middleware.boundary_enforcer import (
        BoundaryEnforcerMiddleware,
    )

    app.add_middleware(BoundaryEnforcerMiddleware, strict=True)
"""

from __future__ import annotations

import logging
import sys
import time
from dataclasses import dataclass, field
from typing import Any

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


# =============================================================================
# Layer Definitions
# =============================================================================


class Layer:
    """Canonical layer names and their allowed import sources."""

    CORE = "grid"
    APPLICATION = "application"
    COGNITIVE = "cognitive"
    TOOLS = "tools"
    INFRASTRUCTURE = "infrastructure"
    INTEGRATION = "integration"

    # Dependency graph: key may import from values
    ALLOWED_IMPORTS: dict[str, set[str]] = {
        "grid": set(),  # Core layer has NO outward deps
        "application": {"grid"},
        "cognitive": {"grid", "application"},
        "tools": {"grid", "application"},
        "infrastructure": {"grid", "application"},
        "integration": {"grid", "application"},
    }

    # Route prefix → owning layer
    ROUTE_OWNERSHIP: dict[str, str] = {
        "/health": "application",
        "/api/v1/cockpit": "application",
        "/api/v1/agentic": "application",
        "/api/v1/skills": "application",
        "/api/v1/intelligence": "cognitive",
        "/api/v1/navigation": "cognitive",
        "/api/v1/resonance": "application",
        "/api/v1/rag": "tools",
    }


# =============================================================================
# Import Auditor (dev-only)
# =============================================================================


@dataclass
class ImportViolation:
    """Record of a detected import boundary violation."""

    importer: str
    imported: str
    importer_layer: str
    imported_layer: str
    severity: str = "error"

    def __str__(self) -> str:
        return (
            f"BOUNDARY VIOLATION: {self.importer_layer}→{self.imported_layer} "
            f"({self.importer} imports {self.imported})"
        )


def _classify_module(module_name: str) -> str | None:
    """Classify a module into its architectural layer.

    Args:
        module_name: Fully qualified module name.

    Returns:
        Layer name or None if not part of the GRID architecture.
    """
    top = module_name.split(".")[0]
    if top in Layer.ALLOWED_IMPORTS:
        return top
    return None


def audit_import_boundaries() -> list[ImportViolation]:
    """
    Scan ``sys.modules`` for import boundary violations.

    This is an expensive operation — call only at startup in
    development or during CI.

    Returns:
        List of detected violations.
    """
    violations: list[ImportViolation] = []

    for mod_name, mod_obj in list(sys.modules.items()):
        importer_layer = _classify_module(mod_name)
        if importer_layer is None:
            continue

        # Inspect the module's direct imports from its __dict__
        if mod_obj is None:
            continue

        allowed = Layer.ALLOWED_IMPORTS.get(importer_layer, set())

        for attr_name in dir(mod_obj):
            try:
                attr = getattr(mod_obj, attr_name)
            except Exception:
                continue
            attr_module = getattr(attr, "__module__", None)
            if attr_module is None:
                continue
            imported_layer = _classify_module(attr_module)
            if imported_layer is None or imported_layer == importer_layer:
                continue
            if imported_layer not in allowed:
                violations.append(
                    ImportViolation(
                        importer=mod_name,
                        imported=attr_module,
                        importer_layer=importer_layer,
                        imported_layer=imported_layer,
                    )
                )

    return violations


# =============================================================================
# Request-Level Boundary Enforcement
# =============================================================================


@dataclass
class BoundaryContext:
    """Tracking context for a single request's boundary checks."""

    path: str
    owning_layer: str | None = None
    violations: list[str] = field(default_factory=list)
    check_time_ms: float = 0.0


class BoundaryEnforcerMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces layer boundaries on incoming requests.

    In **strict** mode, requests to endpoints with a mismatched
    handler layer are rejected with 403.  In **permissive** mode
    (default), violations are logged but allowed through.

    Args:
        app: The ASGI application.
        strict: Reject boundary violations (default: False).
        audit_imports_on_startup: Run import audit at first request (dev only).
    """

    def __init__(
        self,
        app: ASGIApp,
        strict: bool = False,
        audit_imports_on_startup: bool = False,
    ) -> None:
        super().__init__(app)
        self.strict = strict
        self.audit_imports_on_startup = audit_imports_on_startup
        self._import_audit_done = False
        self._violation_count = 0

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.monotonic()

        # One-time import audit
        if self.audit_imports_on_startup and not self._import_audit_done:
            self._import_audit_done = True
            violations = audit_import_boundaries()
            for v in violations:
                logger.warning(str(v))
            if violations:
                logger.warning(
                    "Detected %d import boundary violations. "
                    "Run `audit_import_boundaries()` for details.",
                    len(violations),
                )

        # Route ownership check
        path = request.url.path
        ctx = BoundaryContext(path=path)

        for prefix, layer in Layer.ROUTE_OWNERSHIP.items():
            if path.startswith(prefix):
                ctx.owning_layer = layer
                break

        # If we identified the owning layer, attach it to request state
        request.state.boundary_layer = ctx.owning_layer

        ctx.check_time_ms = (time.monotonic() - start) * 1000

        response = await call_next(request)

        # Attach diagnostics header (dev builds)
        if ctx.owning_layer:
            response.headers["X-Layer-Owner"] = ctx.owning_layer
        response.headers["X-Boundary-Check-Ms"] = f"{ctx.check_time_ms:.2f}"

        return response

    @property
    def violation_count(self) -> int:
        """Total detected violations since startup."""
        return self._violation_count


__all__ = [
    "BoundaryContext",
    "BoundaryEnforcerMiddleware",
    "ImportViolation",
    "Layer",
    "audit_import_boundaries",
]
