"""
MYCELIUM Jungle API — FastAPI endpoints exposing the high-altitude ecosystem.

Maps the 7 API architecture principles to the Jungle Engine:
1. Purpose         → Each endpoint has a single, clear responsibility.
2. Endpoint Design → RESTful resources: /domains, /concurrency, /walk.
3. Function Sigs   → Typed Query params with defaults and descriptions.
4. Query Functions  → Delegates to DomainResolver / JungleEngine.
5. Error Handling  → HTTPException with structured error bodies.
6. Security        → Input validation via SafetyGuard (local-first, no eval).
7. Performance     → Pagination, bounded results, Z-axis throttling.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from mycelium.concurrency import JungleEngine
from mycelium.domains import DomainResolver, DomainType
from mycelium.safety import SafetyGuard, SafetyVerdict

logger = logging.getLogger(__name__)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SINGLETONS — One engine, one resolver, one guard.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_engine = JungleEngine()
_guard = SafetyGuard()

router = APIRouter(prefix="/jungle", tags=["Jungle Ecosystem"])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  RESPONSE MODELS — Structured, typed responses.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class DomainResponse(BaseModel):
    path: str
    domain: str
    is_protected: bool
    accelerative_jump: str = ""


class SafetyResponse(BaseModel):
    node_id: str
    is_safe: bool
    z_axis: int = Field(description="Current concurrency altitude")
    reason: str = ""


class TelemetryResponse(BaseModel):
    z_axis: int = Field(description="Active concurrent node count")
    neighborhood_status: str


class WalkResponse(BaseModel):
    start: str
    end: str
    path_safe: bool
    nodes_traversed: list[str]
    z_axis_peak: int
    improvement_applied: bool


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  COLUMN ALPHA — Domain Resolution (User Context)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get("/domains/resolve", response_model=DomainResponse)
async def resolve_domain(
    path: str = Query(..., description="Filesystem path to resolve"),
    target_domain: str | None = Query(None, description="Target domain for jump calculation"),
):
    """Column Alpha: Resolve a path into its functional domain."""
    # Security: validate input through SafetyGuard
    report = _guard.validate_input(path)
    if report.verdict == SafetyVerdict.REJECT:
        raise HTTPException(status_code=422, detail=report.reasons)

    try:
        resolver = DomainResolver(root="e:\\GRID-main")
        resolved = resolver.resolve(path)

        jump = ""
        if target_domain:
            try:
                target = DomainType(target_domain)
                jump = resolver.get_accelerative_jump(resolved.domain, target)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid target_domain: '{target_domain}'. Use: static, dynamic, engine.",
                )

        return DomainResponse(
            path=str(resolved.path),
            domain=resolved.domain.value,
            is_protected=resolved.is_protected,
            accelerative_jump=jump,
        )
    except Exception as e:
        logger.exception("Domain resolution failed")
        raise HTTPException(status_code=500, detail=str(e))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  COLUMN BETA — Concurrency Safety (Ephemeral State)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get("/concurrency/check", response_model=SafetyResponse)
async def check_node_safety(
    node_id: str = Query(..., description="Node ID to evaluate"),
    dependencies: str = Query("", description="Comma-separated dependency node IDs"),
):
    """Column Beta: Check if a node can be safely entered."""
    report = _guard.validate_input(node_id)
    if report.verdict == SafetyVerdict.REJECT:
        raise HTTPException(status_code=422, detail=report.reasons)

    dep_list = [d.strip() for d in dependencies.split(",") if d.strip()]

    is_safe = _engine.is_path_safe(node_id, dep_list)
    z_axis = _engine.get_z_axis_telemetry()

    reason = ""
    if not is_safe:
        if node_id in dep_list:
            reason = "Direct circular dependency detected (Angular Momentum breach)"
        elif z_axis > 100:
            reason = "Altitude too high — thin air (concurrency depth exceeded)"

    return SafetyResponse(
        node_id=node_id,
        is_safe=is_safe,
        z_axis=z_axis,
        reason=reason,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  COLUMN GAMMA — Z-Axis Telemetry (Concurrency Depth)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get("/telemetry", response_model=TelemetryResponse)
async def get_telemetry():
    """Column Gamma: Current Z-axis altitude and neighborhood status."""
    z = _engine.get_z_axis_telemetry()
    status = "midnight-walk-friendly" if z < 100 else "high-altitude-warning"
    return TelemetryResponse(z_axis=z, neighborhood_status=status)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TAILING FUNCTION — The Midnight Walk (Composite Query)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get("/walk", response_model=WalkResponse)
async def midnight_walk(
    start: str = Query(..., description="Starting node ID"),
    end: str = Query(..., description="Destination node ID"),
    limit: int = Query(10, ge=1, le=100, description="Max nodes to traverse"),
):
    """
    The Tailing Function: Resolves a safe path through the ecosystem.

    This endpoint combines all three columns (Alpha, Beta, Gamma)
    to compute a composite walkable route. It is the calculated
    function call that tails the parallel identification blocks.
    """
    # Validate inputs
    for node_name, node_val in [("start", start), ("end", end)]:
        report = _guard.validate_input(node_val)
        if report.verdict == SafetyVerdict.REJECT:
            raise HTTPException(status_code=422, detail={node_name: report.reasons})

    from mycelium.locomotion import TracebackLocomotion

    # Create the planned sequence of steps (Traceback)
    path_nodes = [start, f"{start}_mid", end][:limit]

    # Engage the Locomotion Engine (which uses the Lamp internally)
    loco = TracebackLocomotion(engine=_engine)
    result = loco.traverse(path_nodes)

    path_safe = result["status"] == "Completed"

    warnings = []
    if not path_safe:
        warnings.append(result.get("abort_reason", "Unknown hazard."))

    return WalkResponse(
        start=start,
        end=end,
        path_safe=path_safe,
        nodes_traversed=result["walked_path"],
        z_axis_peak=min(100, len(result["walked_path"])), # Simplified abstraction
        improvement_applied=True, # The locomotion always attempts improvement if halted
    )
