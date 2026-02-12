"""
API v2 Package.

This version is reserved for future API changes that are backward-incompatible.
When v2 endpoints are implemented, follow these guidelines:

1. Create new Pydantic schemas in v2/schemas.py
2. Create new routers in v2/routers/
3. Document all breaking changes in CHANGELOG.md
4. Provide migration guide for API consumers

Breaking changes that warrant a v2:
- Removing or renaming fields in request/response schemas
- Changing endpoint paths or HTTP methods
- Altering authentication/authorization requirements
- Restructuring nested response objects
"""

from __future__ import annotations

from fastapi import APIRouter

# Placeholder router for v2 API
router = APIRouter(tags=["v2"])


@router.get("/status")
async def get_v2_status() -> dict:
    """
    V2 API status endpoint.

    Returns information about v2 API availability and migration status.
    """
    return {
        "version": "2.0.0-alpha",
        "status": "planned",
        "message": "V2 API is reserved for future breaking changes",
        "v1_deprecated_at": None,
        "v1_sunset_at": None,
    }


__all__ = ["router"]
