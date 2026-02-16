"""Safety enforcement router for the Mothership application.

Re-exports the observation and privacy routers from the standalone safety API
so they can be mounted inside the Mothership FastAPI app.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/safety", tags=["safety"])


def _ensure_safety_on_path() -> None:
    """Add the safety package root to sys.path if not already present."""
    safety_dir = Path(__file__).resolve().parents[4] / "safety"
    if safety_dir.is_dir() and str(safety_dir.parent) not in sys.path:
        sys.path.insert(0, str(safety_dir.parent))


_ensure_safety_on_path()

try:
    from safety.api.observation_endpoints import router as observation_router
    from safety.api.privacy_endpoints import router as privacy_router

    router.include_router(observation_router)
    router.include_router(privacy_router)
    logger.info("Safety sub-routers (observation, privacy) loaded")
except Exception as exc:  # noqa: BLE001
    logger.warning("Safety sub-routers unavailable: %s", exc)
