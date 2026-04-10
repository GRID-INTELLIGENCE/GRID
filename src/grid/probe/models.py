"""Data models for the governance probe system.

Uses dataclasses (not Pydantic) for domain models, following the pattern
established by governance_gates.py and json_scanner.py. Pydantic models
are reserved for API request/response schemas in the router layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4


class EntityType(StrEnum):
    """Classification type of a governance entity."""

    MIDDLEWARE = "middleware"
    GATE = "gate"
    ENFORCER = "enforcer"
    AUTH_DEPENDENCY = "auth_dependency"
    ROUTER = "router"
    SCHEMA = "schema"
    RATE_LIMITER = "rate_limiter"
    SECURITY = "security"
    SAFETY = "safety"
    BOUNDARY = "boundary"
    CONTRACT = "contract"


class Domain(StrEnum):
    """Domain category an entity belongs to."""

    GOVERNANCE = "governance"
    SECURITY = "security"
    AUTHENTICATION = "authentication"
    REQUEST_PIPELINE = "request_pipeline"
    THROTTLING = "throttling"
    ROUTING = "routing"
    DATA_CONTRACT = "data_contract"
    SAFETY = "safety"


class FindingCategory(StrEnum):
    """Category of a probe finding."""

    GAP = "gap"
    ANOMALY = "anomaly"
    OBSERVATION = "observation"
    RECOMMENDATION = "recommendation"


class Severity(StrEnum):
    """Severity level of a finding."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CoverageStatus(StrEnum):
    """Health status based on coverage score."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILING = "failing"


class DiscoveryMethod(StrEnum):
    """How an entity was discovered."""

    SEED = "seed"
    AST_SCAN = "ast_scan"
    PATTERN_MATCH = "pattern_match"


@dataclass(frozen=True, slots=True)
class Entity:
    """A governance entity discovered by the probe."""

    id: str
    label: str
    type: EntityType
    domain: Domain
    source: str
    class_name: str = ""
    line_number: int = 0
    description: str = ""
    execution_order: int = 0
    conditional: bool = False
    condition_flag: str = ""
    critical: bool = False
    discovered_by: DiscoveryMethod = DiscoveryMethod.SEED
    dependencies: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for JSON output."""
        result: dict[str, Any] = {
            "id": self.id,
            "label": self.label,
            "type": self.type.value,
            "domain": self.domain.value,
            "source": self.source,
        }
        if self.class_name:
            result["class_name"] = self.class_name
        if self.line_number:
            result["line_number"] = self.line_number
        if self.description:
            result["description"] = self.description
        if self.execution_order:
            result["execution_order"] = self.execution_order
        if self.conditional:
            result["conditional"] = True
            if self.condition_flag:
                result["condition_flag"] = self.condition_flag
        if self.critical:
            result["critical"] = True
        result["discovered_by"] = self.discovered_by.value
        if self.dependencies:
            result["dependencies"] = list(self.dependencies)
        return result


@dataclass(frozen=True, slots=True)
class Finding:
    """A probe finding — gap, anomaly, or observation."""

    id: str
    severity: Severity
    category: FindingCategory
    message: str
    entity_id: str = ""
    source_file: str = ""
    line_number: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        result: dict[str, Any] = {
            "id": self.id,
            "severity": self.severity.value,
            "category": self.category.value,
            "message": self.message,
        }
        if self.entity_id:
            result["entity_id"] = self.entity_id
        if self.source_file:
            result["source_file"] = self.source_file
        if self.line_number:
            result["line_number"] = self.line_number
        if self.metadata:
            result["metadata"] = self.metadata
        return result


@dataclass(frozen=True, slots=True)
class CoverageScore:
    """Coverage score for a single domain."""

    domain: Domain
    entity_count: int
    tested_count: int
    score: float
    status: CoverageStatus
    weight: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "domain": self.domain.value,
            "entity_count": self.entity_count,
            "tested_count": self.tested_count,
            "score": self.score,
            "status": self.status.value,
            "weight": self.weight,
        }


@dataclass(frozen=True, slots=True)
class DependencyEdge:
    """A directed dependency between two entities."""

    from_id: str
    to_id: str
    relation: str  # depends_on, precedes, enforces, validates, wraps, delegates_to

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "from_id": self.from_id,
            "to_id": self.to_id,
            "relation": self.relation,
        }


@dataclass(slots=True)
class ProbeReport:
    """Complete probe report."""

    report_id: str = field(default_factory=lambda: f"probe-{uuid4().hex[:12]}")
    generated_at: datetime = field(default_factory=datetime.now)
    probe_version: str = "1.0.0"
    scan_root: str = ""
    entities: list[Entity] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    coverage: list[CoverageScore] = field(default_factory=list)
    dependency_edges: list[DependencyEdge] = field(default_factory=list)

    @property
    def total_entities(self) -> int:
        """Total entity count."""
        return len(self.entities)

    @property
    def total_findings(self) -> int:
        """Total findings count."""
        return len(self.findings)

    @property
    def critical_findings(self) -> int:
        """Count of critical findings."""
        return sum(1 for f in self.findings if f.severity == Severity.CRITICAL)

    @property
    def aggregate_score(self) -> float:
        """Weighted aggregate coverage score."""
        if not self.coverage:
            return 0.0
        total_weight = sum(c.weight for c in self.coverage)
        if total_weight == 0:
            return 0.0
        return sum(c.score * c.weight for c in self.coverage) / total_weight

    @property
    def aggregate_status(self) -> CoverageStatus:
        """Overall status based on aggregate score."""
        score = self.aggregate_score
        if score >= 0.8:
            return CoverageStatus.HEALTHY
        if score >= 0.5:
            return CoverageStatus.DEGRADED
        return CoverageStatus.FAILING

    def to_dict(self) -> dict[str, Any]:
        """Serialize to full report dictionary matching probe-report.schema.json."""
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at.isoformat(),
            "probe_version": self.probe_version,
            "scan_root": self.scan_root,
            "entities": [e.to_dict() for e in self.entities],
            "findings": [f.to_dict() for f in self.findings],
            "coverage": [c.to_dict() for c in self.coverage],
            "dependency_graph": {
                "edges": [e.to_dict() for e in self.dependency_edges],
            },
            "summary": {
                "total_entities": self.total_entities,
                "total_findings": self.total_findings,
                "critical_findings": self.critical_findings,
                "aggregate_score": round(self.aggregate_score, 4),
                "aggregate_status": self.aggregate_status.value,
                "domains_scanned": len(self.coverage),
            },
        }
