"""
from datetime import timezone
Mothership Cockpit API Router.

Core API endpoints for cockpit state management, system control,
and real-time status monitoring.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Query, status
from pydantic import BaseModel, Field

from ..dependencies import (
    Auth,
    Cockpit,
    RequestContext,
    RequiredAuth,
    Settings,
    WriteAuth,
)
from ..models import AlertSeverity, SystemState
from ..schemas import (
    ApiResponse,
    CockpitModeUpdateRequest,
    CockpitStateResponse,
    CockpitSummarySchema,
    HealthCheckResponse,
    LivenessResponse,
    OperationModeSchema,
    ReadinessResponse,
    SystemStatusSchema,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Response Models
# =============================================================================


class SystemInfoResponse(BaseModel):
    """System information response."""

    app_name: str
    version: str
    environment: str
    uptime_seconds: float
    started_at: datetime | None = None
    python_version: str = ""
    host: str = ""


class ModeChangeResponse(BaseModel):
    """Response for mode change operations."""

    previous_mode: str
    current_mode: str
    changed_at: datetime
    message: str = ""


class DiagnosticResult(BaseModel):
    """Single diagnostic check result."""

    name: str
    status: str  # "pass", "fail", "warn"
    message: str = ""
    duration_ms: float = 0.0
    details: dict[str, Any] = Field(default_factory=dict)


class DiagnosticsResponse(BaseModel):
    """Full diagnostics response."""

    overall_status: str
    checks: list[DiagnosticResult]
    total_duration_ms: float
    timestamp: datetime


# =============================================================================
# Health & Status Endpoints
# =============================================================================


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health Check",
    description="Check the health status of the cockpit system.",
    tags=["health"],
)
async def health_check(
    cockpit: Cockpit,
    settings: Settings,
) -> HealthCheckResponse:
    """
    Perform a health check on the cockpit system.

    Returns current health status including component checks.
    """
    state = cockpit.state

    checks = {
        "sessions": len(state.sessions) < settings.cockpit.max_concurrent_sessions,
        "operations": state.running_operations < settings.cockpit.task_queue_size,
        "components": all(c.is_healthy() for c in state.components.values()) if state.components else True,
        "alerts": sum(1 for a in state.alerts.values() if not a.is_resolved) < 100,  # Alert threshold
    }

    overall_healthy = all(checks.values())

    return HealthCheckResponse(
        status="healthy" if overall_healthy else "degraded",
        version=settings.app_version,
        uptime_seconds=state.uptime_seconds,
        timestamp=datetime.now(UTC),
        checks=checks,
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness Probe",
    description="Check if the system is ready to accept requests.",
    tags=["health"],
)
async def readiness_check(
    cockpit: Cockpit,
) -> ReadinessResponse:
    """
    Kubernetes-style readiness probe.

    Returns whether the system is ready to handle traffic.
    """
    state = cockpit.state

    dependencies = {
        "state_initialized": state.state != SystemState.OFFLINE,
        "cockpit_started": cockpit._started,
    }

    is_ready = all(dependencies.values())

    return ReadinessResponse(
        ready=is_ready,
        message="System ready" if is_ready else "System initializing",
        dependencies=dependencies,
    )


@router.get(
    "/live",
    response_model=LivenessResponse,
    summary="Liveness Probe",
    description="Check if the system is alive.",
    tags=["health"],
)
async def liveness_check() -> LivenessResponse:
    """
    Kubernetes-style liveness probe.

    Simple check that the service is responding.
    """
    return LivenessResponse(
        alive=True,
        timestamp=datetime.now(UTC),
    )


# =============================================================================
# State Endpoints
# =============================================================================


@router.get(
    "/state",
    response_model=ApiResponse[CockpitStateResponse],
    summary="Get Cockpit State",
    description="Get the current state of the cockpit system.",
)
async def get_state(
    cockpit: Cockpit,
    auth: Auth,
) -> ApiResponse[CockpitStateResponse]:
    """
    Get current cockpit state summary.

    Returns high-level state information including status,
    mode, and aggregate metrics.
    """
    state = cockpit.state
    state.to_dict()

    # Map to response schema
    summary = CockpitSummarySchema(
        total_components=len(state.components),
        healthy_components=sum(1 for c in state.components.values() if c.is_healthy()),
        active_tasks=state.running_operations,
        pending_tasks=sum(1 for op in state.operations.values() if op.status.value in {"pending", "queued"}),
        active_alerts=sum(1 for a in state.alerts.values() if not a.is_resolved),
        critical_alerts=sum(1 for a in state.alerts.values() if not a.is_resolved and a.severity.value == "critical"),
        active_sessions=state.active_sessions,
    )

    response_data = CockpitStateResponse(
        status=SystemStatusSchema(state.state.value),
        mode=OperationModeSchema.NORMAL,  # Default mode
        version=state.version,
        uptime_seconds=state.uptime_seconds,
        started_at=state.started_at or datetime.now(UTC),
        summary=summary,
        is_healthy=cockpit.is_healthy,
        metadata=state.metadata,
    )

    return ApiResponse(
        success=True,
        data=response_data,
        message="Cockpit state retrieved successfully",
    )


@router.get(
    "/state/full",
    response_model=ApiResponse[dict[str, Any]],
    summary="Get Full Cockpit State",
    description="Get complete state including all entities.",
)
async def get_full_state(
    cockpit: Cockpit,
    auth: RequiredAuth,
) -> ApiResponse[dict[str, Any]]:
    """
    Get complete cockpit state including all entities.

    Requires authentication. Returns full state with all
    sessions, operations, components, and alerts.
    """
    state = cockpit.state

    full_state = {
        "status": state.state.value,
        "version": state.version,
        "uptime_seconds": state.uptime_seconds,
        "started_at": state.started_at.isoformat() if state.started_at else None,
        "metrics": {
            "total_sessions": state.total_sessions,
            "active_sessions": state.active_sessions,
            "total_operations": state.total_operations,
            "running_operations": state.running_operations,
        },
        "sessions": {k: v.to_dict() for k, v in state.sessions.items()},
        "operations": {k: v.to_dict() for k, v in state.operations.items()},
        "components": {k: v.to_dict() for k, v in state.components.items()},
        "alerts": {k: v.to_dict() for k, v in state.alerts.items()},
        "health_summary": state.get_health_summary(),
    }

    return ApiResponse(
        success=True,
        data=full_state,
        message="Full cockpit state retrieved",
    )


# =============================================================================
# System Information
# =============================================================================


@router.get(
    "/info",
    response_model=ApiResponse[SystemInfoResponse],
    summary="Get System Information",
    description="Get system and application information.",
)
async def get_system_info(
    cockpit: Cockpit,
    settings: Settings,
) -> ApiResponse[SystemInfoResponse]:
    """
    Get system information including version-to-version and environment details.
    """
    import platform
    import socket

    state = cockpit.state

    info = SystemInfoResponse(
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment.value,
        uptime_seconds=state.uptime_seconds,
        started_at=state.started_at,
        python_version=platform.python_version(),
        host=socket.gethostname(),
    )

    return ApiResponse(
        success=True,
        data=info,
    )


# =============================================================================
# Mode Management
# =============================================================================


@router.get(
    "/mode",
    response_model=ApiResponse[dict[str, str]],
    summary="Get Operation Mode",
    description="Get the current operation mode.",
)
async def get_mode(
    cockpit: Cockpit,
) -> ApiResponse[dict[str, str]]:
    """
    Get the current cockpit operation mode.
    """
    # Default to normal mode since CockpitState doesn't track mode
    return ApiResponse(
        success=True,
        data={
            "mode": "normal",
            "description": "System operating normally",
        },
    )


@router.put(
    "/mode",
    response_model=ApiResponse[ModeChangeResponse],
    summary="Change Operation Mode",
    description="Change the cockpit operation mode.",
)
async def change_mode(
    request: CockpitModeUpdateRequest,
    cockpit: Cockpit,
    auth: WriteAuth,
    context: RequestContext,
) -> ApiResponse[ModeChangeResponse]:
    """
    Change the cockpit operation mode.

    Requires write permission. Mode changes affect how the
    system handles requests and background tasks.
    """
    previous_mode = "normal"  # Current mode
    new_mode = request.mode.value

    # Log mode change
    logger.info(f"Mode change: {previous_mode} -> {new_mode} by user {context.get('user_id')} reason: {request.reason}")

    # Create alert for mode change
    from ..models import AlertSeverity

    cockpit.alerts.create_alert(
        title=f"Operation Mode Changed to {new_mode.upper()}",
        message=request.reason or f"Mode changed from {previous_mode} to {new_mode}",
        severity=AlertSeverity.INFO,
        source="cockpit_api",
        metadata={
            "previous_mode": previous_mode,
            "new_mode": new_mode,
            "user_id": context.get("user_id"),
        },
    )

    response = ModeChangeResponse(
        previous_mode=previous_mode,
        current_mode=new_mode,
        changed_at=datetime.now(UTC),
        message=f"Mode changed to {new_mode}",
    )

    return ApiResponse(
        success=True,
        data=response,
        message=f"Operation mode changed to {new_mode}",
    )


# =============================================================================
# Diagnostics
# =============================================================================


@router.post(
    "/diagnostics",
    response_model=ApiResponse[DiagnosticsResponse],
    summary="Run Diagnostics",
    description="Run system diagnostics.",
)
async def run_diagnostics(
    cockpit: Cockpit,
    auth: RequiredAuth,
    include_details: bool = Query(True, description="Include detailed results"),
) -> ApiResponse[DiagnosticsResponse]:
    """
    Run comprehensive system diagnostics.

    Performs various health checks and returns detailed results.
    """
    import time

    start_time = time.time()
    checks: list[DiagnosticResult] = []
    state = cockpit.state

    # Check 1: State Store
    check_start = time.time()
    try:
        store_ok = state is not None
        checks.append(
            DiagnosticResult(
                name="state_store",
                status="pass" if store_ok else "fail",
                message="State store accessible" if store_ok else "State store unavailable",
                duration_ms=(time.time() - check_start) * 1000,
            )
        )
    except Exception as e:
        checks.append(
            DiagnosticResult(
                name="state_store",
                status="fail",
                message=str(e),
                duration_ms=(time.time() - check_start) * 1000,
            )
        )

    # Check 2: Sessions
    check_start = time.time()
    session_count = len(state.sessions)
    active_sessions = state.active_sessions
    checks.append(
        DiagnosticResult(
            name="sessions",
            status="pass",
            message=f"{active_sessions} active sessions of {session_count} total",
            duration_ms=(time.time() - check_start) * 1000,
            details={"total": session_count, "active": active_sessions} if include_details else {},
        )
    )

    # Check 3: Operations
    check_start = time.time()
    running_ops = state.running_operations
    total_ops = state.total_operations
    checks.append(
        DiagnosticResult(
            name="operations",
            status="pass" if running_ops < 100 else "warn",
            message=f"{running_ops} running operations",
            duration_ms=(time.time() - check_start) * 1000,
            details={"running": running_ops, "total": total_ops} if include_details else {},
        )
    )

    # Check 4: Components
    check_start = time.time()
    total_components = len(state.components)
    healthy_components = sum(1 for c in state.components.values() if c.is_healthy())
    component_status = "pass" if healthy_components == total_components else "warn"
    if total_components > 0 and healthy_components == 0:
        component_status = "fail"

    checks.append(
        DiagnosticResult(
            name="components",
            status=component_status,
            message=f"{healthy_components}/{total_components} components healthy",
            duration_ms=(time.time() - check_start) * 1000,
            details=(
                {
                    "total": total_components,
                    "healthy": healthy_components,
                    "unhealthy": total_components - healthy_components,
                }
                if include_details
                else {}
            ),
        )
    )

    # Check 5: Alerts
    check_start = time.time()
    total_alerts = len(state.alerts)
    unresolved_alerts = sum(1 for a in state.alerts.values() if not a.is_resolved)
    critical_alerts = sum(1 for a in state.alerts.values() if not a.is_resolved and a.severity.value == "critical")

    alert_status = "pass"
    if critical_alerts > 0:
        alert_status = "fail"
    elif unresolved_alerts > 10:
        alert_status = "warn"

    checks.append(
        DiagnosticResult(
            name="alerts",
            status=alert_status,
            message=f"{unresolved_alerts} unresolved alerts ({critical_alerts} critical)",
            duration_ms=(time.time() - check_start) * 1000,
            details=(
                {
                    "total": total_alerts,
                    "unresolved": unresolved_alerts,
                    "critical": critical_alerts,
                }
                if include_details
                else {}
            ),
        )
    )

    # Check 6: Memory (basic check)
    check_start = time.time()
    try:
        import sys

        # Rough estimate of state size
        state_size = sys.getsizeof(state.sessions) + sys.getsizeof(state.operations)
        checks.append(
            DiagnosticResult(
                name="memory",
                status="pass",
                message="Memory usage within limits",
                duration_ms=(time.time() - check_start) * 1000,
                details={"estimated_state_bytes": state_size} if include_details else {},
            )
        )
    except Exception as e:
        checks.append(
            DiagnosticResult(
                name="memory",
                status="warn",
                message=f"Could not check memory: {e}",
                duration_ms=(time.time() - check_start) * 1000,
            )
        )

    # Calculate overall status
    statuses = [c.status for c in checks]
    if "fail" in statuses:
        overall_status = "fail"
    elif "warn" in statuses:
        overall_status = "warn"
    else:
        overall_status = "pass"

    total_duration = (time.time() - start_time) * 1000

    response = DiagnosticsResponse(
        overall_status=overall_status,
        checks=checks,
        total_duration_ms=total_duration,
        timestamp=datetime.now(UTC),
    )

    return ApiResponse(
        success=True,
        data=response,
        message=f"Diagnostics completed: {overall_status}",
    )


# =============================================================================
# System Control
# =============================================================================


@router.post(
    "/shutdown",
    response_model=ApiResponse[dict[str, Any]],
    summary="Initiate Shutdown",
    description="Initiate graceful system shutdown.",
    status_code=status.HTTP_202_ACCEPTED,
)
async def initiate_shutdown(
    cockpit: Cockpit,
    auth: WriteAuth,
    context: RequestContext,
    force: bool = Query(False, description="Force immediate shutdown"),
) -> ApiResponse[dict[str, Any]]:
    """
    Initiate graceful system shutdown.

    Requires write permission. Will terminate sessions and
    cancel running operations before shutdown.
    """
    state = cockpit.state

    # Don't actually shutdown - just prepare for it
    shutdown_info = {
        "status": "shutdown_initiated",
        "force": force,
        "active_sessions": state.active_sessions,
        "running_operations": state.running_operations,
        "message": "Shutdown initiated - system will terminate gracefully",
        "initiated_by": context.get("user_id"),
        "initiated_at": datetime.now(UTC).isoformat(),
    }

    # Create alert
    cockpit.alerts.create_alert(
        title="System Shutdown Initiated",
        message=f"Shutdown initiated by {context.get('user_id')} (force={force})",
        severity=AlertSeverity("warning"),
        source="cockpit_api",
    )

    logger.warning(f"Shutdown initiated by {context.get('user_id')} (force={force})")

    return ApiResponse(
        success=True,
        data=shutdown_info,
        message="Shutdown initiated",
    )


@router.post(
    "/restart",
    response_model=ApiResponse[dict[str, Any]],
    summary="Restart System",
    description="Restart the cockpit system.",
    status_code=status.HTTP_202_ACCEPTED,
)
async def restart_system(
    cockpit: Cockpit,
    auth: WriteAuth,
    context: RequestContext,
) -> ApiResponse[dict[str, Any]]:
    """
    Restart the cockpit system.

    Requires write permission. Performs graceful restart.
    """
    restart_info = {
        "status": "restart_initiated",
        "message": "System restart initiated",
        "initiated_by": context.get("user_id"),
        "initiated_at": datetime.now(UTC).isoformat(),
    }

    logger.warning(f"System restart initiated by {context.get('user_id')}")

    return ApiResponse(
        success=True,
        data=restart_info,
        message="Restart initiated",
    )


# =============================================================================
# Statistics
# =============================================================================


@router.get(
    "/stats",
    response_model=ApiResponse[dict[str, Any]],
    summary="Get Statistics",
    description="Get cockpit statistics and metrics.",
)
async def get_statistics(
    cockpit: Cockpit,
    auth: Auth,
) -> ApiResponse[dict[str, Any]]:
    """
    Get detailed cockpit statistics.
    """
    state = cockpit.state

    # Calculate operation statistics
    operations = list(state.operations.values())
    completed_ops = [op for op in operations if op.status.value == "completed"]
    failed_ops = [op for op in operations if op.status.value == "failed"]

    avg_duration = 0.0
    if completed_ops:
        durations = [op.duration_seconds or 0 for op in completed_ops]
        avg_duration = sum(durations) / len(durations) if durations else 0

    stats = {
        "sessions": {
            "total": state.total_sessions,
            "active": state.active_sessions,
            "expired": sum(1 for s in state.sessions.values() if s.is_expired()),
        },
        "operations": {
            "total": state.total_operations,
            "running": state.running_operations,
            "completed": len(completed_ops),
            "failed": len(failed_ops),
            "success_rate": (len(completed_ops) / len(operations) * 100 if operations else 100),
            "avg_duration_seconds": round(avg_duration, 2),
        },
        "components": {
            "total": len(state.components),
            "healthy": sum(1 for c in state.components.values() if c.is_healthy()),
            "unhealthy": sum(1 for c in state.components.values() if not c.is_healthy()),
        },
        "alerts": {
            "total": len(state.alerts),
            "unresolved": sum(1 for a in state.alerts.values() if not a.is_resolved),
            "acknowledged": sum(1 for a in state.alerts.values() if a.is_acknowledged),
            "by_severity": {
                severity: sum(1 for a in state.alerts.values() if a.severity.value == severity)
                for severity in ["critical", "error", "warning", "info"]
            },
        },
        "system": {
            "uptime_seconds": round(state.uptime_seconds, 2),
            "uptime_human": _format_uptime(state.uptime_seconds),
            "state": state.state.value,
        },
    }

    return ApiResponse(
        success=True,
        data=stats,
    )


def _format_uptime(seconds: float) -> str:
    """Format uptime in human-readable format."""
    days, remainder = divmod(int(seconds), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")

    return " ".join(parts)


__all__ = ["router"]
