"""Canvas API - FastAPI router for canvas routing endpoints."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .canvas import Canvas

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/canvas", tags=["canvas"])


class RoutingRequest(BaseModel):
    """Request model for routing query."""

    query: str = Field(..., description="Query string to route")
    context: dict[str, Any] | None = Field(None, description="Optional context dictionary")
    max_results: int = Field(5, ge=1, le=20, description="Maximum number of results")
    enable_motivation: bool = Field(True, description="Whether to enable motivational adaptation")


class RoutingResponse(BaseModel):
    """Response model for routing query."""

    query: str
    routes: list[dict[str, Any]]
    relevance_scores: list[dict[str, Any]]
    confidence: float = Field(ge=0.0, le=1.0)
    integration_alignment: float = Field(ge=0.0, le=1.0)
    motivated_routing: dict[str, Any] | None = None


class IntegrationStateResponse(BaseModel):
    """Response model for integration state."""

    state: dict[str, Any]


@router.post("/route", response_model=RoutingResponse)
async def route_query(request: RoutingRequest) -> RoutingResponse:
    """Route query through GRID's multi-directory structure.

    Uses similarity matching and metrics-driven relevance to find
    the most relevant routes, with optional motivational adaptation.

    Args:
        request: Routing request with query and options

    Returns:
        RoutingResponse with routes, relevance scores, and motivation

    Raises:
        HTTPException: If routing fails
    """
    try:
        workspace_root = Path.cwd()
        canvas = Canvas(workspace_root)

        result = await canvas.route(
            query=request.query,
            context=request.context,
            max_results=request.max_results,
            enable_motivation=request.enable_motivation,
        )

        return RoutingResponse(
            query=result.query,
            routes=[route.model_dump() for route in result.routes],
            relevance_scores=[score.model_dump() for score in result.relevance_scores],
            confidence=result.confidence,
            integration_alignment=result.integration_alignment,
            motivated_routing=result.motivated_routing.model_dump() if result.motivated_routing else None,
        )
    except Exception as e:
        logger.error(f"Routing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Routing failed: {str(e)}") from e


@router.get("/integration-state", response_model=IntegrationStateResponse)
async def get_integration_state() -> IntegrationStateResponse:
    """Get current integration state.

    Returns:
        IntegrationStateResponse with current state

    Raises:
        HTTPException: If state retrieval fails
    """
    try:
        workspace_root = Path.cwd()
        canvas = Canvas(workspace_root)

        state = canvas.get_integration_state()

        return IntegrationStateResponse(state=state)
    except Exception as e:
        logger.error(f"Failed to get integration state: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get integration state: {str(e)}") from e


@router.get("/wheel")
async def get_wheel_visualization(format: str = "json") -> dict[str, Any]:
    """Get environment wheel visualization.

    Shows the spinning wheel representation of agent movement
    through GRID's environment structure.

    Args:
        format: Output format - "json" (default), "text" (ASCII), or "state" (raw)

    Returns:
        Wheel visualization data

    Raises:
        HTTPException: If visualization fails
    """
    try:
        workspace_root = Path.cwd()
        canvas = Canvas(workspace_root)

        # Spin the wheel to update state
        canvas.spin_wheel()

        visualization = canvas.get_wheel_visualization(format=format)

        if format == "text":
            return {"format": "text", "visualization": visualization}
        elif format == "state":
            # Convert state to dict
            return {
                "format": "state",
                "rotation_angle": visualization.rotation_angle,
                "rotation_velocity": visualization.rotation_velocity,
                "total_agents": len(visualization.agents),
                "update_count": visualization.update_count,
            }
        else:
            return {"format": "json", **visualization}

    except Exception as e:
        logger.error(f"Failed to get wheel visualization: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get wheel visualization: {str(e)}") from e
