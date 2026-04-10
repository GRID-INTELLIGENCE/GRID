"""Tests for grid.probe.models — domain model dataclasses."""

from __future__ import annotations

from datetime import datetime

import pytest

from grid.probe.models import (
    CoverageScore,
    CoverageStatus,
    DependencyEdge,
    DiscoveryMethod,
    Domain,
    Entity,
    EntityType,
    Finding,
    FindingCategory,
    ProbeReport,
    Severity,
)

# =============================================================================
# EntityType enum
# =============================================================================


class TestEntityType:
    def test_all_values(self) -> None:
        assert EntityType.MIDDLEWARE == "middleware"
        assert EntityType.GATE == "gate"
        assert EntityType.AUTH_DEPENDENCY == "auth_dependency"
        assert EntityType.ROUTER == "router"
        assert EntityType.SECURITY == "security"

    def test_is_str_enum(self) -> None:
        assert isinstance(EntityType.MIDDLEWARE, str)
        assert f"{EntityType.GATE}" == "gate"


# =============================================================================
# Domain enum
# =============================================================================


class TestDomain:
    def test_all_values(self) -> None:
        assert Domain.GOVERNANCE == "governance"
        assert Domain.SECURITY == "security"
        assert Domain.AUTHENTICATION == "authentication"
        assert Domain.REQUEST_PIPELINE == "request_pipeline"
        assert Domain.SAFETY == "safety"


# =============================================================================
# Severity / FindingCategory / CoverageStatus / DiscoveryMethod
# =============================================================================


class TestEnums:
    def test_severity_ordering(self) -> None:
        values = [s.value for s in Severity]
        assert "critical" in values
        assert "low" in values

    def test_finding_category(self) -> None:
        assert FindingCategory.GAP == "gap"
        assert FindingCategory.RECOMMENDATION == "recommendation"

    def test_coverage_status(self) -> None:
        assert CoverageStatus.HEALTHY == "healthy"
        assert CoverageStatus.FAILING == "failing"

    def test_discovery_method(self) -> None:
        assert DiscoveryMethod.SEED == "seed"
        assert DiscoveryMethod.AST_SCAN == "ast_scan"
        assert DiscoveryMethod.PATTERN_MATCH == "pattern_match"


# =============================================================================
# Entity dataclass
# =============================================================================


class TestEntity:
    def _make_entity(self, **overrides: object) -> Entity:
        defaults = {
            "id": "ent-test-001",
            "label": "TestMiddleware",
            "type": EntityType.MIDDLEWARE,
            "domain": Domain.REQUEST_PIPELINE,
            "source": "src/test.py",
        }
        defaults.update(overrides)
        return Entity(**defaults)  # type: ignore[arg-type]

    def test_minimal_creation(self) -> None:
        entity = self._make_entity()
        assert entity.id == "ent-test-001"
        assert entity.label == "TestMiddleware"
        assert entity.type == EntityType.MIDDLEWARE
        assert entity.domain == Domain.REQUEST_PIPELINE
        assert entity.source == "src/test.py"
        assert entity.class_name == ""
        assert entity.line_number == 0
        assert entity.discovered_by == DiscoveryMethod.SEED

    def test_full_creation(self) -> None:
        entity = self._make_entity(
            class_name="TestMiddleware",
            line_number=42,
            description="A test middleware",
            execution_order=3,
            conditional=True,
            condition_flag="test_enabled",
            critical=True,
            discovered_by=DiscoveryMethod.AST_SCAN,
            dependencies=("dep-001", "dep-002"),
        )
        assert entity.class_name == "TestMiddleware"
        assert entity.execution_order == 3
        assert entity.conditional is True
        assert entity.condition_flag == "test_enabled"
        assert entity.critical is True
        assert entity.dependencies == ("dep-001", "dep-002")

    def test_frozen(self) -> None:
        entity = self._make_entity()
        with pytest.raises(AttributeError):
            entity.id = "changed"  # type: ignore[misc]

    def test_to_dict_minimal(self) -> None:
        entity = self._make_entity()
        d = entity.to_dict()
        assert d["id"] == "ent-test-001"
        assert d["type"] == "middleware"
        assert d["domain"] == "request_pipeline"
        assert d["discovered_by"] == "seed"
        assert "class_name" not in d  # empty string omitted
        assert "line_number" not in d  # zero omitted

    def test_to_dict_full(self) -> None:
        entity = self._make_entity(
            class_name="TestMW",
            line_number=10,
            execution_order=1,
            conditional=True,
            condition_flag="flag",
            critical=True,
            dependencies=("a", "b"),
        )
        d = entity.to_dict()
        assert d["class_name"] == "TestMW"
        assert d["line_number"] == 10
        assert d["execution_order"] == 1
        assert d["conditional"] is True
        assert d["condition_flag"] == "flag"
        assert d["critical"] is True
        assert d["dependencies"] == ["a", "b"]


# =============================================================================
# Finding dataclass
# =============================================================================


class TestFinding:
    def test_creation(self) -> None:
        finding = Finding(
            id="find-001",
            severity=Severity.HIGH,
            category=FindingCategory.GAP,
            message="Missing gate",
        )
        assert finding.id == "find-001"
        assert finding.severity == Severity.HIGH
        assert finding.message == "Missing gate"

    def test_to_dict(self) -> None:
        finding = Finding(
            id="find-002",
            severity=Severity.CRITICAL,
            category=FindingCategory.ANOMALY,
            message="Critical issue",
            entity_id="ent-001",
            source_file="src/foo.py",
            line_number=99,
        )
        d = finding.to_dict()
        assert d["id"] == "find-002"
        assert d["severity"] == "critical"
        assert d["category"] == "anomaly"
        assert d["entity_id"] == "ent-001"
        assert d["source_file"] == "src/foo.py"
        assert d["line_number"] == 99

    def test_to_dict_omits_empty(self) -> None:
        finding = Finding(
            id="find-003",
            severity=Severity.LOW,
            category=FindingCategory.OBSERVATION,
            message="Note",
        )
        d = finding.to_dict()
        assert "entity_id" not in d
        assert "source_file" not in d
        assert "metadata" not in d


# =============================================================================
# CoverageScore dataclass
# =============================================================================


class TestCoverageScore:
    def test_creation_and_dict(self) -> None:
        score = CoverageScore(
            domain=Domain.GOVERNANCE,
            entity_count=10,
            tested_count=8,
            score=0.85,
            status=CoverageStatus.HEALTHY,
            weight=1.5,
        )
        d = score.to_dict()
        assert d["domain"] == "governance"
        assert d["score"] == 0.85
        assert d["weight"] == 1.5


# =============================================================================
# DependencyEdge dataclass
# =============================================================================


class TestDependencyEdge:
    def test_creation_and_dict(self) -> None:
        edge = DependencyEdge(from_id="a", to_id="b", relation="precedes")
        d = edge.to_dict()
        assert d == {"from_id": "a", "to_id": "b", "relation": "precedes"}


# =============================================================================
# ProbeReport dataclass
# =============================================================================


class TestProbeReport:
    def _make_entity(self, eid: str, domain: Domain = Domain.GOVERNANCE) -> Entity:
        return Entity(
            id=eid,
            label=f"Entity-{eid}",
            type=EntityType.GATE,
            domain=domain,
            source="src/test.py",
        )

    def _make_finding(self, fid: str, severity: Severity = Severity.MEDIUM) -> Finding:
        return Finding(
            id=fid,
            severity=severity,
            category=FindingCategory.OBSERVATION,
            message=f"Finding {fid}",
        )

    def test_empty_report(self) -> None:
        report = ProbeReport()
        assert report.total_entities == 0
        assert report.total_findings == 0
        assert report.critical_findings == 0
        assert report.aggregate_score == 0.0
        assert report.aggregate_status == CoverageStatus.FAILING

    def test_with_entities(self) -> None:
        report = ProbeReport(
            entities=[self._make_entity("e1"), self._make_entity("e2")],
        )
        assert report.total_entities == 2

    def test_critical_findings_count(self) -> None:
        report = ProbeReport(
            findings=[
                self._make_finding("f1", Severity.CRITICAL),
                self._make_finding("f2", Severity.LOW),
                self._make_finding("f3", Severity.CRITICAL),
            ],
        )
        assert report.critical_findings == 2

    def test_aggregate_score_with_coverage(self) -> None:
        report = ProbeReport(
            coverage=[
                CoverageScore(Domain.GOVERNANCE, 5, 5, 0.9, CoverageStatus.HEALTHY, weight=2.0),
                CoverageScore(Domain.SECURITY, 3, 3, 0.7, CoverageStatus.DEGRADED, weight=1.0),
            ],
        )
        expected = (0.9 * 2.0 + 0.7 * 1.0) / 3.0
        assert abs(report.aggregate_score - expected) < 1e-6
        assert report.aggregate_status == CoverageStatus.HEALTHY

    def test_aggregate_status_degraded(self) -> None:
        report = ProbeReport(
            coverage=[
                CoverageScore(Domain.GOVERNANCE, 5, 5, 0.6, CoverageStatus.DEGRADED, weight=1.0),
            ],
        )
        assert report.aggregate_status == CoverageStatus.DEGRADED

    def test_to_dict(self) -> None:
        report = ProbeReport(
            scan_root="/test",
            entities=[self._make_entity("e1")],
            findings=[self._make_finding("f1")],
            coverage=[
                CoverageScore(Domain.GOVERNANCE, 1, 1, 0.85, CoverageStatus.HEALTHY),
            ],
            dependency_edges=[DependencyEdge("e1", "e2", "depends_on")],
        )
        d = report.to_dict()

        assert d["scan_root"] == "/test"
        assert len(d["entities"]) == 1
        assert len(d["findings"]) == 1
        assert len(d["coverage"]) == 1
        assert len(d["dependency_graph"]["edges"]) == 1
        assert d["summary"]["total_entities"] == 1
        assert d["summary"]["total_findings"] == 1
        assert "report_id" in d
        assert "generated_at" in d
