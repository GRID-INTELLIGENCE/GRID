"""
Unified DRT (Don't Repeat Themselves) Monitoring Router.
Uses core DRTMonitor engine as single source of truth.
"""

import logging
from datetime import UTC, datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..middleware.drt_middleware_unified import UnifiedDRTMiddleware, get_unified_drt_middleware

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/drt", tags=["DRT Monitoring"])


class AttackVectorAddRequest(BaseModel):
    endpoint: str
    method: str
    client_ip: str
    user_agent: str
    attack_type: str
    severity: str


class StatusResponse(BaseModel):
    enabled: bool
    enforcement_mode: str
    similarity_threshold: float
    retention_hours: int
    auto_escalate: bool
    escalated_endpoints: int
    behavioral_history_count: int
    attack_vectors_count: int
    sampling_rate: float
    rate_limit_multiplier: float
    core_total_monitored_endpoints: int
    core_escalated_endpoints: int
    core_escalation_rate: float
    core_known_attack_vectors: int
    timestamp: str


class EndpointSummaryResponse(BaseModel):
    endpoint: str
    behavior_count: int
    time_range: dict[str, str]
    method_distribution: dict[str, int]
    user_agent_distribution: dict[str, int]
    hourly_distribution: dict[str, int]
    escalated: bool
    websocket_overheads: list[str]


@router.get("/status", response_model=StatusResponse)
async def get_drt_status(middleware: UnifiedDRTMiddleware = Depends(get_unified_drt_middleware)) -> StatusResponse:
    """Get unified DRT system status from core engine."""
    status = middleware.get_status()
    return StatusResponse(timestamp=datetime.now(UTC).isoformat(), **status)


@router.post("/attack-vectors")
async def add_attack_vector(
    request: AttackVectorAddRequest, middleware: UnifiedDRTMiddleware = Depends(get_unified_drt_middleware)
) -> dict[str, str]:
    """Add attack vector to core DRT monitor."""
    middleware.add_attack_vector(
        endpoint=request.endpoint,
        method=request.method,
        client_ip=request.client_ip,
        user_agent=request.user_agent,
        attack_type=request.attack_type,
        severity=request.severity,
    )
    return {"status": "success", "message": f"Attack vector added: {request.method} {request.endpoint}"}


@router.get("/escalated-endpoints")
async def get_escalated_endpoints(
    middleware: UnifiedDRTMiddleware = Depends(get_unified_drt_middleware),
) -> dict[str, Any]:
    """Get list of currently escalated endpoints."""
    now = datetime.now(UTC)
    escalated = {path: expires.isoformat() for path, expires in middleware.escalated_endpoints.items() if expires > now}
    return {"escalated_endpoints": escalated}


@router.post("/escalate/{path:path}")
async def escalate_endpoint(
    path: str, middleware: UnifiedDRTMiddleware = Depends(get_unified_drt_middleware)
) -> dict[str, str]:
    """Manually escalate an endpoint."""
    # Create a mock monitoring result for manual escalation
    monitoring_result = {
        "endpoint": path,
        "escalation_applied": True,
        "escalation_config": {
            "attack_type": "manual",
            "similarity_score": 1.0,
            "threat_level": "medium",
        },
    }

    # Handle escalation through middleware
    from fastapi import Request

    mock_request = Request({"type": "http", "method": "GET", "url": {"path": path}})
    await middleware._handle_escalation(mock_request, monitoring_result)

    return {"status": "success", "message": f"Endpoint escalated: {path}"}


@router.post("/de-escalate/{path:path}")
async def de_escalate_endpoint(
    path: str, middleware: UnifiedDRTMiddleware = Depends(get_unified_drt_middleware)
) -> dict[str, str]:
    """De-escalate an endpoint."""
    if path in middleware.escalated_endpoints:
        del middleware.escalated_endpoints[path]
        return {"status": "success", "message": f"Endpoint de-escalated: {path}"}
    return {"status": "warning", "message": f"Endpoint not found in escalated list: {path}"}


@router.get("/behavioral-history")
async def get_behavioral_history(
    middleware: UnifiedDRTMiddleware = Depends(get_unified_drt_middleware),
) -> dict[str, Any]:
    """Get behavioral history from core DRT monitor."""
    # Get all endpoint summaries and extract history
    all_summaries = {}
    for endpoint in middleware.drt_monitor.behavioral_history.keys():
        summary = middleware.get_endpoint_summary(endpoint)
        all_summaries[endpoint] = summary

    return {"behavioral_summaries": all_summaries}


@router.get("/endpoint/{path:path}/summary")
async def get_endpoint_summary(
    path: str, middleware: UnifiedDRTMiddleware = Depends(get_unified_drt_middleware)
) -> EndpointSummaryResponse:
    """Get detailed summary for a specific endpoint."""
    summary = middleware.get_endpoint_summary(path)

    return EndpointSummaryResponse(
        endpoint=summary.get("endpoint", path),
        behavior_count=summary.get("behavior_count", 0),
        time_range=summary.get("time_range", {}),
        method_distribution=summary.get("method_distribution", {}),
        user_agent_distribution=summary.get("user_agent_distribution", {}),
        hourly_distribution=summary.get("hourly_distribution", {}),
        escalated=summary.get("escalated", False),
        websocket_overheads=summary.get("websocket_overheads", []),
    )


@router.get("/system-overview")
async def get_system_overview(middleware: UnifiedDRTMiddleware = Depends(get_unified_drt_middleware)) -> dict[str, Any]:
    """Get comprehensive system overview."""
    status = middleware.get_status()

    # Get endpoint summaries
    endpoint_summaries = {}
    for endpoint in list(middleware.drt_monitor.behavioral_history.keys())[:10]:  # Limit to 10 for performance
        endpoint_summaries[endpoint] = middleware.get_endpoint_summary(endpoint)

    return {
        "system_status": status,
        "endpoint_summaries": endpoint_summaries,
        "timestamp": datetime.now(UTC).isoformat(),
    }
