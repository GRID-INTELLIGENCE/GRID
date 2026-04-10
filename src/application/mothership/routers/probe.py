"""
Governance Probe API endpoints.

Provides endpoints to run the governance probe, retrieve entity maps,
view reports, query probe status, and execute the lumos 6-phase pipeline.
Uses the four-layer probe architecture:
YAML config -> Python execution -> JSON output -> Markdown documentation.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from application.mothership.dependencies import Auth, RateLimited, RequestContext
from application.mothership.schemas import ApiResponse, BaseSchema, ResponseMeta

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/probe", tags=["probe"])


# =============================================================================
# Pydantic Schemas (API layer only — domain uses dataclasses)
# =============================================================================


class ProbeEntitySchema(BaseSchema):
    """API representation of a governance entity."""

    id: str
    label: str
    type: str
    domain: str
    source: str
    class_name: str = ""
    line_number: int = 0
    description: str = ""
    execution_order: int = 0
    conditional: bool = False
    condition_flag: str = ""
    critical: bool = False
    discovered_by: str = "seed"
    dependencies: list[str] = Field(default_factory=list)


class ProbeFindingSchema(BaseSchema):
    """API representation of a probe finding."""

    id: str
    severity: str
    category: str
    message: str
    entity_id: str = ""
    source_file: str = ""
    line_number: int = 0


class CoverageScoreSchema(BaseSchema):
    """API representation of a domain coverage score."""

    domain: str
    entity_count: int
    tested_count: int
    score: float
    status: str
    weight: float = 1.0


class DependencyEdgeSchema(BaseSchema):
    """API representation of a dependency edge."""

    from_id: str
    to_id: str
    relation: str


class ProbeReportSummarySchema(BaseSchema):
    """Summary section of a probe report."""

    total_entities: int = 0
    total_findings: int = 0
    critical_findings: int = 0
    aggregate_score: float = 0.0
    aggregate_status: str = "failing"
    domains_scanned: int = 0


class ProbeReportSchema(BaseSchema):
    """Full probe report response."""

    report_id: str
    generated_at: datetime
    probe_version: str = "1.0.0"
    scan_root: str = ""
    entities: list[ProbeEntitySchema] = Field(default_factory=list)
    findings: list[ProbeFindingSchema] = Field(default_factory=list)
    coverage: list[CoverageScoreSchema] = Field(default_factory=list)
    dependency_graph: list[DependencyEdgeSchema] = Field(default_factory=list)
    summary: ProbeReportSummarySchema = Field(default_factory=ProbeReportSummarySchema)


class ProbeRunRequest(BaseSchema):
    """Request body for running the probe."""

    write_output: bool = False


class ProbeStatusSchema(BaseSchema):
    """Probe status response."""

    enabled: bool = True
    version: str = "1.0.0"
    entity_count: int = 0
    last_run: datetime | None = None


class EntityMapSchema(BaseSchema):
    """Entity map response."""

    schema_version: str = "probe-entities/1.0"
    generated_at: datetime
    entity_count: int = 0
    entities: dict[str, Any] = Field(default_factory=dict)
    domains: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# Module-level state (matches MCQ pattern for prototype)
# =============================================================================

_last_report: dict[str, Any] | None = None
_last_run: datetime | None = None


# =============================================================================
# Helper: build engine lazily
# =============================================================================


def _get_engine() -> Any:
    """Get a configured ProbeEngine instance."""
    try:
        from grid.probe.engine import ProbeEngine

        return ProbeEngine.from_config()
    except Exception as exc:
        logger.warning("Failed to create ProbeEngine from config, using defaults: %s", exc)
        from grid.probe.engine import ProbeEngine

        return ProbeEngine.with_defaults()


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/status", response_model=ApiResponse[ProbeStatusSchema])
async def probe_status(
    _: RateLimited,
    auth: Auth,
    request_context: RequestContext,
) -> ApiResponse[ProbeStatusSchema]:
    """
    Get the current probe status.

    Returns probe configuration state, entity count from last run,
    and last run timestamp.
    """
    request_id = request_context.get("request_id", "unknown")

    entity_count = 0
    version = "1.0.0"
    enabled = True

    if _last_report:
        summary = _last_report.get("summary", {})
        entity_count = summary.get("total_entities", 0)

    try:
        from grid.probe.config import ProbeConfig

        config = ProbeConfig.from_yaml()
        version = config.version
        enabled = config.enabled
    except Exception:  # noqa: S110
        pass

    return ApiResponse(
        success=True,
        data=ProbeStatusSchema(
            enabled=enabled,
            version=version,
            entity_count=entity_count,
            last_run=_last_run,
        ),
        meta=ResponseMeta(request_id=request_id),
    )


@router.post("/run", response_model=ApiResponse[ProbeReportSchema])
async def run_probe(
    _: RateLimited,
    auth: Auth,
    request_context: RequestContext,
    request: ProbeRunRequest | None = None,
) -> ApiResponse[ProbeReportSchema]:
    """
    Execute the governance probe pipeline.

    Runs the full pipeline: load seeds -> scan filesystem -> generate report.
    Optionally writes JSON and Markdown reports to disk.
    """
    global _last_report, _last_run
    request_id = request_context.get("request_id", "unknown")
    write_output = request.write_output if request else False

    try:
        engine = _get_engine()
        report = engine.run(write_output=write_output)
        report_dict = report.to_dict()

        _last_report = report_dict
        _last_run = datetime.now(UTC)

        # Convert to API schema
        response_data = _report_dict_to_schema(report_dict)

        logger.info(
            "Probe run complete: %d entities, %d findings, score=%.2f (request_id=%s)",
            report.total_entities,
            report.total_findings,
            report.aggregate_score,
            request_id,
        )

        return ApiResponse(
            success=True,
            data=response_data,
            message="Probe run completed successfully",
            meta=ResponseMeta(request_id=request_id),
        )
    except Exception as exc:
        logger.error("Probe run failed: %s (request_id=%s)", exc, request_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Probe execution failed: {exc}",
        ) from exc


@router.get("/report", response_model=ApiResponse[ProbeReportSchema])
async def get_report(
    _: RateLimited,
    auth: Auth,
    request_context: RequestContext,
) -> ApiResponse[ProbeReportSchema]:
    """
    Get the last probe report.

    Returns the cached report from the most recent probe run.
    Returns 404 if no probe has been run yet.
    """
    request_id = request_context.get("request_id", "unknown")

    if _last_report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No probe report available. Run the probe first via POST /probe/run",
        )

    response_data = _report_dict_to_schema(_last_report)

    return ApiResponse(
        success=True,
        data=response_data,
        meta=ResponseMeta(request_id=request_id),
    )


@router.get("/entities", response_model=ApiResponse[EntityMapSchema])
async def get_entities(
    _: RateLimited,
    auth: Auth,
    request_context: RequestContext,
    domain: str | None = Query(None, description="Filter by domain"),
    entity_type: str | None = Query(None, description="Filter by entity type"),
) -> ApiResponse[EntityMapSchema]:
    """
    Get the entity map from the last probe run.

    Optionally filter by domain or entity type.
    """
    request_id = request_context.get("request_id", "unknown")

    if _last_report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No entity map available. Run the probe first via POST /probe/run",
        )

    entities = _last_report.get("entities", [])
    now = datetime.now(UTC)

    # Apply filters
    if domain:
        entities = [e for e in entities if e.get("domain") == domain]
    if entity_type:
        entities = [e for e in entities if e.get("type") == entity_type]

    # Build entity map format
    entities_dict: dict[str, Any] = {}
    for entity in entities:
        eid = entity.get("id", "")
        entities_dict[eid] = {k: v for k, v in entity.items() if k != "id" and v}

    # Build domain summary
    domains_dict: dict[str, Any] = {}
    for entity in entities:
        d = entity.get("domain", "unknown")
        if d not in domains_dict:
            domains_dict[d] = {"entity_count": 0, "entity_ids": []}
        domains_dict[d]["entity_count"] += 1
        domains_dict[d]["entity_ids"].append(entity.get("id", ""))

    return ApiResponse(
        success=True,
        data=EntityMapSchema(
            generated_at=now,
            entity_count=len(entities),
            entities=entities_dict,
            domains=domains_dict,
        ),
        meta=ResponseMeta(request_id=request_id),
    )


@router.get("/findings", response_model=ApiResponse[list[ProbeFindingSchema]])
async def get_findings(
    _: RateLimited,
    auth: Auth,
    request_context: RequestContext,
    severity: str | None = Query(None, description="Filter by severity"),
    category: str | None = Query(None, description="Filter by category"),
) -> ApiResponse[list[ProbeFindingSchema]]:
    """
    Get findings from the last probe run.

    Optionally filter by severity or category.
    """
    request_id = request_context.get("request_id", "unknown")

    if _last_report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No findings available. Run the probe first via POST /probe/run",
        )

    findings = _last_report.get("findings", [])

    if severity:
        findings = [f for f in findings if f.get("severity") == severity]
    if category:
        findings = [f for f in findings if f.get("category") == category]

    result = [
        ProbeFindingSchema(
            id=f.get("id", ""),
            severity=f.get("severity", ""),
            category=f.get("category", ""),
            message=f.get("message", ""),
            entity_id=f.get("entity_id", ""),
            source_file=f.get("source_file", ""),
            line_number=f.get("line_number", 0),
        )
        for f in findings
    ]

    return ApiResponse(
        success=True,
        data=result,
        meta=ResponseMeta(request_id=request_id),
    )


@router.get("/coverage", response_model=ApiResponse[list[CoverageScoreSchema]])
async def get_coverage(
    _: RateLimited,
    auth: Auth,
    request_context: RequestContext,
) -> ApiResponse[list[CoverageScoreSchema]]:
    """
    Get coverage scores from the last probe run.
    """
    request_id = request_context.get("request_id", "unknown")

    if _last_report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No coverage data available. Run the probe first via POST /probe/run",
        )

    coverage = _last_report.get("coverage", [])
    result = [
        CoverageScoreSchema(
            domain=c.get("domain", ""),
            entity_count=c.get("entity_count", 0),
            tested_count=c.get("tested_count", 0),
            score=c.get("score", 0.0),
            status=c.get("status", "failing"),
            weight=c.get("weight", 1.0),
        )
        for c in coverage
    ]

    return ApiResponse(
        success=True,
        data=result,
        meta=ResponseMeta(request_id=request_id),
    )


# =============================================================================
# Lumos Schemas
# =============================================================================


class LumosPathScoreSchema(BaseSchema):
    """A single PATH dimension score."""

    dimension: str
    raw_value: float
    weight: float
    weighted: float
    evidence: list[str] = Field(default_factory=list)


class LumosScoredEntitySchema(BaseSchema):
    """An entity with its computed PATH score and tier."""

    name: str
    entity_type: str
    path_score: float
    tier: str
    dimensions: list[LumosPathScoreSchema] = Field(default_factory=list)
    sweep_protocol: str | None = None


class LumosSweepActionSchema(BaseSchema):
    """A concrete action from the GUIDE phase."""

    target: str
    protocol: str
    action: str
    priority: int
    depends_on: list[str] = Field(default_factory=list)


class LumosGateResultSchema(BaseSchema):
    """Result of a verification gate."""

    gate_name: str
    passed: bool
    message: str
    timestamp: str = ""


class LumosResultSchema(BaseSchema):
    """Full lumos pipeline result."""

    started_at: str
    completed_at: str
    phases_completed: list[str] = Field(default_factory=list)
    composite_score: float = 0.0
    verdict: str = "FAST_CLEAR"
    path_scores: list[LumosPathScoreSchema] = Field(default_factory=list)
    scored_entities: list[LumosScoredEntitySchema] = Field(default_factory=list)
    sweep_actions: list[LumosSweepActionSchema] = Field(default_factory=list)
    gate_results: list[LumosGateResultSchema] = Field(default_factory=list)
    execution_log: list[str] = Field(default_factory=list)
    evolution_eligible: bool = False
    evolution_message: str = ""
    ecosystem_state: dict[str, Any] = Field(default_factory=dict)


class LumosRunRequest(BaseSchema):
    """Request body for running the lumos pipeline."""

    include_probe: bool = True
    audit_limit: int = Field(default=100, ge=1, le=1000)


# =============================================================================
# Lumos Endpoint
# =============================================================================


@router.post("/lumos", response_model=ApiResponse[LumosResultSchema])
async def run_lumos(
    _: RateLimited,
    auth: Auth,
    request_context: RequestContext,
    request: LumosRunRequest | None = None,
) -> ApiResponse[LumosResultSchema]:
    """
    Execute the lumos 6-phase ecosystem illumination pipeline.

    Merges three data streams:
    1. Probe internal: governance entity map, coverage, findings
    2. Echoes process: audit events, enforcement state, precedent tracking
    3. Seeds process: repo health scores, ecosystem snapshots

    Returns a complete LumosResult with PATH scores, verdict, sweep actions,
    gate results, and evolution eligibility.
    """
    request_id = request_context.get("request_id", "unknown")
    include_probe = request.include_probe if request else True
    audit_limit = request.audit_limit if request else 100

    try:
        from grid.probe.ecosystem import EcosystemBridge
        from grid.probe.lumos import LumosOrchestrator

        bridge = EcosystemBridge()

        # Ingest echoes audit events from file
        raw_audit = EcosystemBridge.load_audit_from_ndjson(limit=audit_limit)
        if raw_audit:
            bridge.ingest_audit_events(raw_audit)
            logger.info("Lumos: ingested %d audit events (request_id=%s)", len(raw_audit), request_id)

        # Ingest seeds ecosystem snapshot from file
        raw_snapshot = EcosystemBridge.load_latest_snapshot()
        if raw_snapshot:
            bridge.ingest_ecosystem(raw_snapshot)
            logger.info("Lumos: ingested ecosystem snapshot (request_id=%s)", request_id)

        # Run probe if requested
        probe_report = None
        if include_probe:
            try:
                engine = _get_engine()
                probe_report = engine.run(write_output=False)
                logger.info("Lumos: probe report generated (request_id=%s)", request_id)
            except Exception as probe_exc:
                logger.warning("Lumos: probe run failed, continuing without it: %s", probe_exc)

        # Run the full 6-phase pipeline
        orchestrator = LumosOrchestrator(bridge)
        result = orchestrator.run_full(probe_report=probe_report)
        result_dict = result.to_dict()

        # Convert to API schema
        path_scores = [
            LumosPathScoreSchema(
                dimension=s.get("dimension", ""),
                raw_value=s.get("raw_value", 0.0),
                weight=s.get("weight", 0.0),
                weighted=s.get("weighted", 0.0),
                evidence=s.get("evidence", []),
            )
            for s in result_dict.get("path_scores", [])
        ]

        scored_entities = [
            LumosScoredEntitySchema(
                name=e.get("name", ""),
                entity_type=e.get("entity_type", ""),
                path_score=e.get("path_score", 0.0),
                tier=e.get("tier", ""),
                dimensions=[
                    LumosPathScoreSchema(
                        dimension=d.get("dimension", ""),
                        raw_value=d.get("raw_value", 0.0),
                        weight=d.get("weight", 0.0),
                        weighted=d.get("weighted", 0.0),
                        evidence=d.get("evidence", []),
                    )
                    for d in e.get("dimensions", [])
                ],
                sweep_protocol=e.get("sweep_protocol"),
            )
            for e in result_dict.get("scored_entities", [])
        ]

        sweep_actions = [
            LumosSweepActionSchema(
                target=a.get("target", ""),
                protocol=a.get("protocol", ""),
                action=a.get("action", ""),
                priority=a.get("priority", 0),
                depends_on=a.get("depends_on", []),
            )
            for a in result_dict.get("sweep_actions", [])
        ]

        gate_results = [
            LumosGateResultSchema(
                gate_name=g.get("gate_name", ""),
                passed=g.get("passed", False),
                message=g.get("message", ""),
                timestamp=g.get("timestamp", ""),
            )
            for g in result_dict.get("gate_results", [])
        ]

        response_data = LumosResultSchema(
            started_at=result_dict.get("started_at", ""),
            completed_at=result_dict.get("completed_at", ""),
            phases_completed=result_dict.get("phases_completed", []),
            composite_score=result_dict.get("composite_score", 0.0),
            verdict=result_dict.get("verdict", "FAST_CLEAR"),
            path_scores=path_scores,
            scored_entities=scored_entities,
            sweep_actions=sweep_actions,
            gate_results=gate_results,
            execution_log=result_dict.get("execution_log", []),
            evolution_eligible=result_dict.get("evolution_eligible", False),
            evolution_message=result_dict.get("evolution_message", ""),
            ecosystem_state=result_dict.get("ecosystem_state", {}),
        )

        logger.info(
            "Lumos complete: score=%.1f, verdict=%s, %d actions (request_id=%s)",
            result.composite_score,
            result.verdict.value,
            len(result.sweep_actions),
            request_id,
        )

        return ApiResponse(
            success=True,
            data=response_data,
            message=f"Lumos pipeline completed — verdict: {result.verdict.value}",
            meta=ResponseMeta(request_id=request_id),
        )
    except Exception as exc:
        logger.error("Lumos pipeline failed: %s (request_id=%s)", exc, request_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lumos execution failed: {exc}",
        ) from exc


# =============================================================================
# Helpers
# =============================================================================


def _report_dict_to_schema(report_dict: dict[str, Any]) -> ProbeReportSchema:
    """Convert a report dict (from ProbeReport.to_dict()) to the API schema."""
    entities = [
        ProbeEntitySchema(
            id=e.get("id", ""),
            label=e.get("label", ""),
            type=e.get("type", ""),
            domain=e.get("domain", ""),
            source=e.get("source", ""),
            class_name=e.get("class_name", ""),
            line_number=e.get("line_number", 0),
            description=e.get("description", ""),
            execution_order=e.get("execution_order", 0),
            conditional=e.get("conditional", False),
            condition_flag=e.get("condition_flag", ""),
            critical=e.get("critical", False),
            discovered_by=e.get("discovered_by", "seed"),
            dependencies=e.get("dependencies", []),
        )
        for e in report_dict.get("entities", [])
    ]

    findings = [
        ProbeFindingSchema(
            id=f.get("id", ""),
            severity=f.get("severity", ""),
            category=f.get("category", ""),
            message=f.get("message", ""),
            entity_id=f.get("entity_id", ""),
            source_file=f.get("source_file", ""),
            line_number=f.get("line_number", 0),
        )
        for f in report_dict.get("findings", [])
    ]

    coverage = [
        CoverageScoreSchema(
            domain=c.get("domain", ""),
            entity_count=c.get("entity_count", 0),
            tested_count=c.get("tested_count", 0),
            score=c.get("score", 0.0),
            status=c.get("status", "failing"),
            weight=c.get("weight", 1.0),
        )
        for c in report_dict.get("coverage", [])
    ]

    dep_graph = report_dict.get("dependency_graph", {})
    edges = [
        DependencyEdgeSchema(
            from_id=edge.get("from_id", ""),
            to_id=edge.get("to_id", ""),
            relation=edge.get("relation", ""),
        )
        for edge in dep_graph.get("edges", [])
    ]

    summary_data = report_dict.get("summary", {})
    summary = ProbeReportSummarySchema(
        total_entities=summary_data.get("total_entities", 0),
        total_findings=summary_data.get("total_findings", 0),
        critical_findings=summary_data.get("critical_findings", 0),
        aggregate_score=summary_data.get("aggregate_score", 0.0),
        aggregate_status=summary_data.get("aggregate_status", "failing"),
        domains_scanned=summary_data.get("domains_scanned", 0),
    )

    return ProbeReportSchema(
        report_id=report_dict.get("report_id", ""),
        generated_at=report_dict.get("generated_at", datetime.now(UTC).isoformat()),
        probe_version=report_dict.get("probe_version", "1.0.0"),
        scan_root=report_dict.get("scan_root", ""),
        entities=entities,
        findings=findings,
        coverage=coverage,
        dependency_graph=edges,
        summary=summary,
    )
