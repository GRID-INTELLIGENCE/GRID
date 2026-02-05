"""
Integration helper for FastAPI applications.

Provides `add_parasite_guard()` function to easily integrate
the parasite guard into any FastAPI application.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

from .config import GuardMode, ParasiteGuardConfig
from .middleware import ParasiteGuardMiddleware

logger = logging.getLogger(__name__)


def add_parasite_guard(
    app: Any,
    config: Optional[ParasiteGuardConfig] = None,
    enable_components: Optional[list[str]] = None,
    mode: Optional[str] = None,
    enable_pruning: bool = False,
) -> ParasiteGuardMiddleware:
    """
    Add parasite guard middleware to a FastAPI application.

    This function:
    1. Creates or uses provided config
    2. Initializes the middleware
    3. Registers it with the FastAPI app
    4. Returns the middleware for advanced usage

    Args:
        app: FastAPI application instance
        config: Optional ParasiteGuardConfig (created from env vars if None)
        enable_components: List of components to enable (e.g., ["websocket", "eventbus"])
        mode: Global mode override ("disabled", "dry_run", "detect", "full")
        enable_pruning: Legacy parameter (sets all enabled components to FULL mode)

    Returns:
        ParasiteGuardMiddleware instance

    Usage:
        from infrastructure.parasite_guard import add_parasite_guard

        # Basic usage (uses env vars)
        add_parasite_guard(app)

        # Enable specific components
        add_parasite_guard(app, enable_components=["websocket", "eventbus"])

        # Set specific mode
        add_parasite_guard(app, mode="dry_run")

        # With custom config
        from infrastructure.parasite_guard import ParasiteGuardConfig
        config = ParasiteGuardConfig()
        config.enable_component("websocket", GuardMode.FULL)
        add_parasite_guard(app, config=config)
    """
    # Create config if not provided
    if config is None:
        config = ParasiteGuardConfig()

    # Apply mode override if specified
    if mode:
        mode_map = {
            "disabled": GuardMode.DISABLED,
            "dry_run": GuardMode.DRY_RUN,
            "detect": GuardMode.DETECT,
            "full": GuardMode.FULL,
        }
        if mode.lower() in mode_map:
            config.global_mode = mode_map[mode.lower()]
            logger.info(f"Parasite Guard global mode set to: {mode}")
        else:
            logger.warning(f"Invalid mode '{mode}', using config default")

    # Handle legacy enable_pruning parameter
    if enable_pruning:
        logger.info("enable_pruning=True: Setting all enabled components to FULL mode with sanitization")
        # Set all already-enabled components to FULL mode
        for name, comp_config in config.components.items():
            if comp_config.enabled:
                config.enable_component(name, GuardMode.FULL, sanitize=True)

    # Enable specific components if specified
    if enable_components:
        for component in enable_components:
            config.enable_component(
                component,
                mode=config.get_component_mode(component) or GuardMode.DRY_RUN,
                sanitize=False,  # Don't auto-enable sanitization
            )
        logger.info(f"Parasite Guard enabled components: {enable_components}")

    # Create middleware
    middleware = ParasiteGuardMiddleware(app, config)

    # Register as ASGI middleware
    # FastAPI 0.100+ uses middleware as a callable
    app.add_middleware(lambda app: middleware)

    # Alternative: For older FastAPI, use add_asgi_middleware
    # app.add_asgi_middleware(middleware)

    # Log configuration
    logger.info(
        "Parasite Guard installed",
        extra={
            "enabled": config.enabled,
            "disabled": config.disabled,
            "global_mode": config.global_mode.name if config.global_mode else None,
            "components_enabled": [name for name, cfg in config.components.items() if cfg.enabled],
        },
    )

    return middleware


def add_parasite_guard_to_lifespan(
    app: Any,
    config: Optional[ParasiteGuardConfig] = None,
) -> ParasiteGuardMiddleware:
    """
    Add parasite guard integrated into FastAPI lifespan.

    This is useful if you want parasite guard to be aware of
    app startup/shutdown events for proper cleanup.

    Args:
        app: FastAPI application instance
        config: Optional ParasiteGuardConfig

    Returns:
        ParasiteGuardMiddleware instance

    Usage:
        from infrastructure.parasite_guard import add_parasite_guard_to_lifespan

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            guard = add_parasite_guard_to_lifespan(app)

            yield

            # Shutdown
            await wait_for_sanitization(guard)
    """
    middleware = add_parasite_guard(app, config)
    return middleware


async def wait_for_sanitization(
    middleware: ParasiteGuardMiddleware,
    timeout: Optional[float] = 30.0,
) -> None:
    """
    Wait for all active sanitization tasks to complete.

    Useful during application shutdown to ensure all parasites
    have been properly sanitized before exit.

    Args:
        middleware: ParasiteGuardMiddleware instance
        timeout: Maximum time to wait (seconds)
    """
    try:
        if hasattr(middleware, "deferred_sanitizer"):
            await middleware.deferred_sanitizer.wait_all(timeout=timeout)
            logger.info("All parasite sanitizations completed before shutdown")
        else:
            logger.debug("Middleware does not support sanitization waiting")
    except asyncio.TimeoutError:
        logger.warning(f"Timeout waiting for sanitization after {timeout}s")
    except Exception as e:
        logger.error(f"Error waiting for sanitization: {e}", exc_info=True)


def create_middleware(
    app: Any,
    config: Optional[ParasiteGuardConfig] = None,
) -> ParasiteGuardMiddleware:
    """
    Create (but don't install) parasite guard middleware.

    Useful for custom middleware registration scenarios.

    Returns:
        ParasiteGuardMiddleware instance

    Usage:
        from infrastructure.parasite_guard import create_middleware

        guard_middleware = create_middleware(app)

        # Register manually
        app.add_middleware(guard_middleware)
    """
    if config is None:
        config = ParasiteGuardConfig()

    return ParasiteGuardMiddleware(app, config)
