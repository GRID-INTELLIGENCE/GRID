"""
Activity Resonance API Dependencies.

Dependency injection functions for FastAPI endpoints providing
access to the ResonanceService.
"""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import Depends

from ..services import ResonanceService

logger = logging.getLogger(__name__)

# =============================================================================
# Auth & Rate Limiting (imported from Mothership)
# =============================================================================

# Try to import auth dependencies from Mothership; provide fallbacks for standalone use
try:
    from application.mothership.dependencies import (
        Auth as MothershipAuth,
    )
    from application.mothership.dependencies import (
        RateLimited as MothershipRateLimited,
    )

    Auth = MothershipAuth
    RateLimited = MothershipRateLimited
except ImportError:
    # Fallback for standalone testing or when Mothership is not available
    logger.warning("Mothership auth dependencies not available; using permissive fallbacks")

    async def _fallback_auth() -> dict[str, Any]:
        """Fallback auth that allows all requests (development only)."""
        return {
            "authenticated": False,
            "method": "fallback",
            "user_id": "anonymous",
            "permissions": {"read", "write"},
        }

    async def _fallback_rate_limit() -> bool:
        """Fallback rate limit that allows all requests."""
        return True

    Auth = Annotated[dict[str, Any], Depends(_fallback_auth)]
    RateLimited = Annotated[bool, Depends(_fallback_rate_limit)]

# =============================================================================
# Service Dependencies
# =============================================================================

# Global service instance (singleton pattern)
_resonance_service: ResonanceService | None = None


def get_resonance_service() -> ResonanceService:
    """
    Get the resonance service instance.

    Uses singleton pattern to ensure consistent state across requests.

    Returns:
        ResonanceService instance
    """
    global _resonance_service
    if _resonance_service is None:
        _resonance_service = ResonanceService()
    return _resonance_service


def reset_resonance_service() -> None:
    """Reset the resonance service (for testing)."""
    global _resonance_service
    _resonance_service = None


ResonanceServiceDep = Annotated[ResonanceService, Depends(get_resonance_service)]


__all__ = [
    "get_resonance_service",
    "reset_resonance_service",
    "ResonanceServiceDep",
    "Auth",
    "RateLimited",
]
