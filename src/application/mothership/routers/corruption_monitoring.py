"""API endpoints for data corruption monitoring and accountability.

This module provides REST endpoints for monitoring data corruption events,
viewing penalty scores, and managing endpoint accountability.
"""
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from grid.resilience.data_corruption_penalty import (
    CorruptionSeverity,
    CorruptionType,
    corruption_tracker,
    record_corruption_event,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/corruption", tags=["Data Corruption Monitoring"])

class CorruptionEventRequest(BaseModel):
    """Request model for manually reporting a corruption event."""
    endpoint: str = Field(..., description="The endpoint where corruption was detected")
    severity: str = Field(..., description="Severity level (LOW, MEDIUM, HIGH, CRITICAL)")
    corruption_type: str = Field(..., description="Type of corruption")
    description: str = Field(..., description="Description of the corruption event")
    affected_resources: List[str] = Field(default_factory=list, description="Resources affected")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    correlation_id: Optional[str] = Field(None, description="Optional correlation ID")

class CorruptionEventResponse(BaseModel):
    """Response model for corruption event reporting."""
    success: bool
    penalty_applied: float
    endpoint: str
    correlation_id: str
    message: str

class EndpointHealthResponse(BaseModel):
    """Response model for endpoint health status."""
    endpoint: str
    penalty_score: float
    is_critical: bool
    severity: str
    recommendation: str
    last_updated: str

class CriticalEndpointsResponse(BaseModel):
    """Response model for critical endpoints list."""
    critical_count: int
    endpoints: List[EndpointHealthResponse]
    system_health: str

class CorruptionStatsResponse(BaseModel):
    """Response model for corruption statistics."""
    total_endpoints_monitored: int
    critical_endpoints: int
    total_penalty_score: float
    average_penalty: float
    highest_penalty_endpoint: Optional[str]
    system_status: str

@router.post(
    "/report",
    response_model=CorruptionEventResponse,
    summary="Report a data corruption event",
    description="Manually report a data corruption event for tracking and penalty calculation"
)
async def report_corruption_event(
    request: Request,
    event: CorruptionEventRequest,
) -> CorruptionEventResponse:
    """Report a data corruption event.
    
    This endpoint allows manual reporting of corruption events that may not be
    automatically detected by the middleware.
    """
    try:
        severity = CorruptionSeverity[event.severity.upper()]
    except KeyError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid severity level: {event.severity}. Must be one of: LOW, MEDIUM, HIGH, CRITICAL"
        )
    
    try:
        corruption_type = CorruptionType(event.corruption_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid corruption type: {event.corruption_type}"
        )
    
    correlation_id = event.correlation_id or str(id(request))
    
    penalty = record_corruption_event(
        endpoint=event.endpoint,
        severity=severity,
        corruption_type=corruption_type,
        description=event.description,
        correlation_id=correlation_id,
        affected_resources=event.affected_resources,
        metadata=event.metadata,
    )
    
    is_critical = corruption_tracker.is_endpoint_critical(event.endpoint)
    message = f"Corruption event recorded. Penalty: {penalty:.2f}"
    if is_critical:
        message += " ENDPOINT IS NOW CRITICAL - immediate action required"
    
    return CorruptionEventResponse(
        success=True,
        penalty_applied=penalty,
        endpoint=event.endpoint,
        correlation_id=correlation_id,
        message=message,
    )

@router.get(
    "/health/{endpoint:path}",
    response_model=EndpointHealthResponse,
    summary="Get health status for a specific endpoint",
    description="Retrieve the current corruption penalty score and health status for an endpoint"
)
async def get_endpoint_health(endpoint: str) -> EndpointHealthResponse:
    """Get the health status and penalty score for a specific endpoint."""
    health = corruption_tracker.get_endpoint_health(endpoint)
    
    if health["penalty_score"] == 0.0:
        raise HTTPException(
            status_code=404,
            detail=f"No corruption data found for endpoint: {endpoint}"
        )
    
    from datetime import datetime, timezone
    
    return EndpointHealthResponse(
        endpoint=health["endpoint"],
        penalty_score=health["penalty_score"],
        is_critical=health["is_critical"],
        severity=health["severity"],
        recommendation=health["recommendation"],
        last_updated=datetime.now(timezone.utc).isoformat(),
    )

@router.get(
    "/critical",
    response_model=CriticalEndpointsResponse,
    summary="List critical endpoints",
    description="Get a list of all endpoints that have exceeded the critical penalty threshold"
)
async def get_critical_endpoints() -> CriticalEndpointsResponse:
    """Get a list of all critical endpoints with their penalty scores."""
    critical = corruption_tracker.get_critical_endpoints()
    
    endpoints = []
    for endpoint, penalty in critical:
        health = corruption_tracker.get_endpoint_health(endpoint)
        from datetime import datetime, timezone
        
        endpoints.append(EndpointHealthResponse(
            endpoint=endpoint,
            penalty_score=health["penalty_score"],
            is_critical=True,
            severity=health["severity"],
            recommendation=health["recommendation"],
            last_updated=datetime.now(timezone.utc).isoformat(),
        ))
    
    # Determine system health
    if len(endpoints) == 0:
        system_health = "HEALTHY"
    elif len(endpoints) <= 2:
        system_health = "DEGRADED"
    else:
        system_health = "CRITICAL"
    
    return CriticalEndpointsResponse(
        critical_count=len(endpoints),
        endpoints=endpoints,
        system_health=system_health,
    )

@router.get(
    "/stats",
    response_model=CorruptionStatsResponse,
    summary="Get corruption statistics",
    description="Get overall corruption statistics and system health metrics"
)
async def get_corruption_stats() -> CorruptionStatsResponse:
    """Get overall corruption statistics."""
    total_endpoints = len(corruption_tracker._endpoint_penalties)
    critical_count = len(corruption_tracker._critical_endpoints)
    
    total_penalty = sum(corruption_tracker._endpoint_penalties.values())
    average_penalty = total_penalty / total_endpoints if total_endpoints > 0 else 0.0
    
    highest_penalty_endpoint = None
    highest_penalty = 0.0
    for endpoint, penalty in corruption_tracker._endpoint_penalties.items():
        if penalty > highest_penalty:
            highest_penalty = penalty
            highest_penalty_endpoint = endpoint
    
    # Determine system status
    if critical_count == 0 and total_penalty < 10:
        system_status = "HEALTHY"
    elif critical_count <= 2 and total_penalty < 50:
        system_status = "DEGRADED"
    else:
        system_status = "CRITICAL"
    
    return CorruptionStatsResponse(
        total_endpoints_monitored=total_endpoints,
        critical_endpoints=critical_count,
        total_penalty_score=total_penalty,
        average_penalty=average_penalty,
        highest_penalty_endpoint=highest_penalty_endpoint,
        system_status=system_status,
    )

@router.post(
    "/reset/{endpoint:path}",
    response_model=Dict[str, Any],
    summary="Reset endpoint penalties",
    description="Reset all corruption penalties for a specific endpoint (admin only)"
)
async def reset_endpoint_penalties(
    endpoint: str,
    reason: str = Query(..., description="Reason for resetting penalties"),
) -> Dict[str, Any]:
    """Reset all penalties for a specific endpoint.
    
    This is an admin-only operation that should be used after fixing
    the underlying issues that caused the corruption.
    """
    # In a real implementation, you'd want to add authentication here
    if endpoint in corruption_tracker._penalties:
        del corruption_tracker._penalties[endpoint]
        corruption_tracker._endpoint_penalties.pop(endpoint, None)
        corruption_tracker._critical_endpoints.discard(endpoint)
        
        logger.info(
            "Corruption penalties reset for endpoint %s. Reason: %s",
            endpoint, reason
        )
        
        return {
            "success": True,
            "endpoint": endpoint,
            "message": "Penalties have been reset",
            "reason": reason,
        }
    else:
        return {
            "success": False,
            "endpoint": endpoint,
            "message": "No penalties found for this endpoint",
            "reason": reason,
        }

@router.get(
    "/penalties",
    response_model=Dict[str, float],
    summary="Get all endpoint penalties",
    description="Get a mapping of all endpoints to their current penalty scores"
)
async def get_all_penalties() -> Dict[str, float]:
    """Get the current penalty score for all monitored endpoints."""
    return dict(corruption_tracker._endpoint_penalties)
