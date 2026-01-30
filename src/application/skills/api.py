"""
Skills Health API endpoints for monitoring and observability.
Integrates with persistence layer, performance guard, and NSR tracking.
"""

import time
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from grid.skills.execution_tracker import SkillExecutionTracker
from grid.skills.intelligence_inventory import IntelligenceInventory
from grid.skills.intelligence_tracker import IntelligenceTracker
from grid.skills.nsr_tracker import NSRTracker
from grid.skills.registry import default_registry

router = APIRouter(prefix="/skills", tags=["skills"])


class SkillHealthMetrics(BaseModel):
    """Performance metrics for skill health."""

    total_executions: int = Field(description="Total number of executions")
    success_rate: float = Field(description="Success rate (0-1)")
    avg_latency_ms: float = Field(description="Average execution time in ms")
    p50_latency_ms: float = Field(description="P50 latency in ms")
    p95_latency_ms: float = Field(description="P95 latency in ms")
    p99_latency_ms: float = Field(description="P99 latency in ms")
    avg_confidence: float = Field(description="Average confidence score")


class SkillIntelligenceMetrics(BaseModel):
    """Intelligence metrics for skill."""

    total_decisions: int = Field(description="Total intelligence decisions")
    avg_confidence: float = Field(description="Average confidence score")
    common_rationales: list[str] = Field(description="Most common decision rationales")


class SkillSignalQuality(BaseModel):
    """Signal vs noise quality metrics."""

    nsr_ratio: float = Field(description="Noise-to-Signal Ratio")
    noise_count: int = Field(description="Total noise events in current window")
    signal_count: int = Field(description="Total signal events in current window")
    threshold: float = Field(description="Current threshold")


class SkillHealthResponse(BaseModel):
    """Complete health response for a skill."""

    skill_id: str
    name: str
    status: str = Field(description="healthy/degraded/unhealthy/unknown")
    total_executions: int
    success_rate: float
    avg_confidence: float
    latency_metrics: SkillHealthMetrics
    regression_detected: bool
    last_execution: float | None
    uptime_percentage: float = Field(description="Uptime in recent history")


@router.get("/health")
async def get_skills_health(
    status_filter: str | None = None, min_executions: int = 1
) -> dict[str, list[SkillHealthResponse]]:
    """
    Get health status of all skills with filtering options.
    """
    inventory = IntelligenceInventory()
    tracker = SkillExecutionTracker.get_instance()

    health_data = []

    for skill in default_registry.list():
        summary = inventory.get_skill_summary(skill.id)

        if not summary:
            continue

        if summary.total_executions < min_executions:
            continue

        # Check for regression
        current_metrics = {
            "p50_ms": summary.p50_latency_ms,
            "p95_ms": summary.p95_latency_ms,
            "p99_ms": summary.p99_latency_ms,
        }
        regression = inventory.check_regression(skill.id, current_metrics)

        # Calculate uptime (success rate in recent history)
        history = tracker.get_execution_history(skill.id, limit=100)
        if history:
            successes = len([e for e in history if e.status.value == "success"])
            uptime_percentage = (successes / len(history)) * 100
        else:
            uptime_percentage = 0.0

        # Determine status
        if summary.success_rate > 0.95:
            status = "healthy"
        elif summary.success_rate > 0.80:
            status = "degraded"
        else:
            status = "unhealthy"

        if status_filter and status != status_filter:
            continue

        health_data.append(
            SkillHealthResponse(
                skill_id=skill.id,
                name=skill.name,
                status=status,
                total_executions=summary.total_executions,
                success_rate=summary.success_rate,
                avg_confidence=summary.avg_confidence,
                latency_metrics=SkillHealthMetrics(
                    total_executions=summary.total_executions,
                    success_rate=summary.success_rate,
                    avg_latency_ms=summary.avg_latency_ms,
                    p50_latency_ms=summary.p50_latency_ms,
                    p95_latency_ms=summary.p95_latency_ms,
                    p99_latency_ms=summary.p99_latency_ms,
                    avg_confidence=summary.avg_confidence,
                ),
                regression_detected=regression is not None,
                last_execution=summary.last_updated,
                uptime_percentage=uptime_percentage,
            )
        )

    return {"skills": health_data}


@router.get("/intelligence/{skill_id}")
async def get_skill_intelligence_detail(skill_id: str) -> dict[str, Any]:
    """Get detailed intelligence for a specific skill."""
    inventory = IntelligenceInventory()
    intel_tracker = IntelligenceTracker.get_instance()

    summary = inventory.get_skill_summary(skill_id)
    if not summary:
        raise HTTPException(status_code=404, detail=f"Skill {skill_id} not found")

    patterns = intel_tracker.get_intelligence_patterns(skill_id)

    return {
        "skill_id": skill_id,
        "summary": summary.__dict__ if hasattr(summary, "__dict__") else str(summary),
        "patterns": patterns,
        "timestamp": time.time(),
    }


@router.get("/signal-quality")
async def get_signal_quality_overview() -> dict[str, Any]:
    """Get overall signal quality metrics."""
    nsr_tracker = NSRTracker()
    details = nsr_tracker.get_current_nsr_details()

    return details


@router.get("/diagnostics")
async def get_system_diagnostics() -> dict[str, Any]:
    """Get comprehensive system diagnostics."""
    from grid.skills.diagnostics import SkillsDiagnostics

    diagnostics = SkillsDiagnostics()
    report = diagnostics.run_full_diagnostics()

    return report.__dict__
