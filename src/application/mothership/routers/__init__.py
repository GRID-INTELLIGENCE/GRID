"""
Mothership Cockpit API Routers.

FastAPI routers implementing the REST API endpoints for the
Mothership Cockpit local integration backend.
"""

from __future__ import annotations

# Router imports will be added as modules are created
# from .cockpit import router as cockpit_router
# from .components import router as components_router
# from .tasks import router as tasks_router
# from .alerts import router as alerts_router
# from .sessions import router as sessions_router
# from .integrations import router as integrations_router
# from .websocket import router as websocket_router
# from .api_keys import router as api_keys_router
# from .auth import router as auth_router
# from .billing import router as billing_router
# from .payment import router as payment_router
import logging
from importlib import import_module
from pathlib import Path
from typing import Any

from fastapi import APIRouter

logger = logging.getLogger(__name__)


def _load_api_routes_config() -> dict[str, Any] | None:
    """
    Load API routes configuration from config/api_routes.yaml.

    Returns:
        Parsed configuration dictionary if the file exists and is valid YAML, otherwise None.
    """
    config_path = Path(__file__).resolve().parents[4] / "config" / "api_routes.yaml"
    if not config_path.exists():
        return None

    try:
        import yaml  # type: ignore[import-untyped]
    except Exception:  # pragma: no cover - PyYAML not installed
        return None

    try:
        raw_config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except Exception:
        return None

    return raw_config if isinstance(raw_config, dict) else None


def _import_router(module_path: str, attr_name: str) -> Any:
    """
    Import a router object from a module.

    Args:
        module_path: Module path (e.g., "application.mothership.routers.auth")
        attr_name: Attribute name to retrieve from the module (e.g., "router")

    Returns:
        The router object if import succeeds; otherwise raises ImportError or AttributeError.
    """
    module = import_module(module_path)
    return getattr(module, attr_name)


def _extract_module_and_attr(module_spec: str, default_attr: str = "router") -> tuple[str, str]:
    """
    Split a module specification of the form 'module.path:attr'.

    Args:
        module_spec: Module specification string.
        default_attr: Default attribute name if not provided.

    Returns:
        Tuple of (module_path, attribute_name).
    """
    if ":" in module_spec:
        module_path, attr_name = module_spec.split(":", maxsplit=1)
    else:
        module_path, attr_name = module_spec, default_attr
    return module_path, attr_name


def create_api_router(prefix: str = "/api/v1") -> APIRouter:
    """
    Create and configure the main API router.

    Aggregates all sub-routers into a single router with
    the specified prefix.

    Args:
        prefix: URL prefix for all API routes

    Returns:
        Configured APIRouter instance
    """
    config = _load_api_routes_config()

    route_specs: list[dict[str, Any]]
    effective_prefix = prefix

    if config:
        effective_prefix = config.get("prefix", prefix)
        route_specs = config.get("routers", []) or []
    else:
        # Fallback to existing hardcoded routes
        route_specs = [
            {"module": "application.mothership.routers.auth:router", "enabled": True},
            {"module": "application.mothership.routers.navigation_simple:router", "enabled": True},
            {"module": "application.mothership.routers.payment:router", "enabled": True},
            {"module": "application.mothership.routers.stripe_connect_demo:router", "enabled": True},
            {"module": "application.mothership.routers.api_keys:router", "enabled": True},
            {"module": "application.mothership.routers.billing:router", "enabled": True},
            {"module": "application.mothership.routers.inference:router", "enabled": True},
            {"module": "application.mothership.routers.privacy:router", "enabled": True},
            {
                "module": "application.resonance.api.router:router",
                "prefix": "/resonance",
                "tags": ["resonance"],
                "enabled": True,
            },
            {"module": "application.canvas.api:router", "enabled": True},
            {"module": "grid.AGENT.api.router:router", "enabled": True},
            {
                "module": "application.mothership.routers.intelligence:router",
                "prefix": "/intelligence",
                "enabled": True,
            },
        ]

    router = APIRouter(prefix=effective_prefix)

    for spec in route_specs:
        if not spec:
            continue

        enabled = spec.get("enabled", True)
        if not enabled:
            continue

        module_spec = spec.get("module")
        if not module_spec:
            continue

        module_path, attr_name = _extract_module_and_attr(module_spec, default_attr=spec.get("attr", "router"))

        try:
            imported_router = _import_router(module_path, attr_name)
        except Exception as exc:
            logger.warning("Failed to import router '%s' attr '%s': %s", module_path, attr_name, exc)
            continue

        router_kwargs: dict[str, Any] = {}
        if spec.get("prefix"):
            router_kwargs["prefix"] = spec["prefix"]
        if spec.get("tags"):
            router_kwargs["tags"] = spec["tags"]

        router.include_router(imported_router, **router_kwargs)

    return router


__all__ = [
    "create_api_router",
]
