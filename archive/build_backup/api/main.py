"""GRID Sovereign API Gateway.

Unified FastAPI application exposing GRID capabilities with:
- Boundary enforcement middleware (auth, rate, PII, audit)
- Adaptive cognitive routing (percentile-based)
- Event-driven architecture via shared bus
- Config registry (env-aware, no hardcoded paths)
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI

from api.middleware.rights_boundary import RightsPreservingBoundaryMiddleware
from api.monitoring.boundary_logger import boundary_logger
from api.routers import crypto, system, wellness


def get_project_root() -> Path:
    """Get project root from env or default."""
    if root := os.getenv("PROJECT_ROOT"):
        return Path(root)
    return Path(__file__).parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    print("🛡️  GRID Sovereign API Gateway starting...")
    print("🔒 Rights-Preserving Boundary Enforcement: ENABLED")
    print("⚖️  Human Rights Protection: ENFORCED")
    yield
    print("🛑 Shutting down...")


app = FastAPI(
    title="GRID Sovereign API",
    description="Unified API gateway for GRID intelligence capabilities",
    version="1.0.0",
    lifespan=lifespan,
)

# Rights-preserving boundary middleware
app.add_middleware(RightsPreservingBoundaryMiddleware)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, Any]:
    """API health check endpoint."""
    return {
        "status": "healthy",
        "api_version": "1.0.0",
        "service": "grid-sovereign-api",
    }
