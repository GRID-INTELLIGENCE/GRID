"""
GRID Mothership API Package.

This package provides versioned API structure for the Mothership application.
Each version (v1, v2) contains its own routers and schemas to ensure
backward compatibility when introducing breaking changes.

API Versioning Strategy:
    - v1: Current stable API (routes in routers/)
    - v2: Reserved for future breaking changes

Usage:
    from application.mothership.api import v1_router, v2_router

    app.include_router(v1_router, prefix="/api/v1")
    app.include_router(v2_router, prefix="/api/v2")
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import APIRouter


def get_v1_router() -> APIRouter:
    """
    Get the v1 API router.

    Currently delegates to the existing routers module for backward compatibility.
    """
    from application.mothership.routers import create_api_router

    return create_api_router(prefix="")


def get_v2_router() -> APIRouter:
    """
    Get the v2 API router.

    Reserved for future API version with breaking changes.
    """
    from application.mothership.api.v2 import router

    return router.router


__all__ = [
    "get_v1_router",
    "get_v2_router",
]
