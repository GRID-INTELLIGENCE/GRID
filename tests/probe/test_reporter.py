"""Tests for grid.probe.reporter — ProbeReporter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from grid.probe.config import ProbeConfig
from grid.probe.models import (
    CoverageScore,
    CoverageStatus,
    DependencyEdge,
    Domain,
    Entity,
    EntityType,
    Finding,
    FindingCategory,
    ProbeReport,
    Severity,
)
from grid.probe.registry import EntityRegistry
from grid.probe.reporter import ProbeReporter


def _make_entity(
    eid: str,
    domain: Domain = Domain.GOVERNANCE,
    execution_order: int = 0,
    dependencies: tuple[str, ...] = (),
) -> Entity:
    return Entity(
        id=eid,
        label=f"Entity-{eid}",
        type=EntityType.GATE,
        domain=domain,
        source="src/test.py",
        execution_order=execution_order,
        dependencies=dependencies,
    )


def _make_finding(fid: str) -> Finding:
    return Finding(
        id=fid,
        severity=Severity.MEDIUM,
        category=FindingCategory.OBSERVATION,
        message=f"Finding {fid}",
    )


# =============================================================================
# Report generation
# =============================================================================


class TestReportGeneration:
    def test_generate_empty_report(self) -> None:
        config = ProbeConfig()
        registry = EntityRegistry()
        reporter = ProbeReporter(config, registry)

        report = reporter.generate_report()
        assert report.total_entities == 0
        assert report.total_findings == 0
        assert report.coverage == []
        assert report.dependency_edges == []

    def test_generate_report_with_entities(self) -> None:
        config = ProbeConfig(
            domain_weights={"governance": 1.5, "security": 1.2},
        )
        registry = EntityRegistry()
        registry.register(_make_entity("e1", Domain.GOVERNANCE))
        registry.register(_make_entity("e2", Domain.GOVERNANCE))
        registry.register(_make_entity("e3", Domain.SECURITY))

        reporter = ProbeReporter(config, registry)
        report = reporter.generate_report(scan_root="/test")

        assert report.total_entities == 3
        assert report.scan_root == "/test"
        assert len(report.coverage) == 2  # governance + security

    def test_generate_report_with_findings(self) -> None:
        config = ProbeConfig()
        registry = EntityRegistry()
        reporter = ProbeReporter(config, registry)

        findings = [_make_finding("f1"), _make_finding("f2")]
        report = reporter.generate_report(findings=findings)

        assert report.total_findings == 2

    def test_coverage_scoring(self) -> None:
        config = ProbeConfig(
            domain_weights={"governance": 1.5},
            threshold_healthy=0.8,
            threshold_degraded=0.5,
        )
        registry = EntityRegistry()
        # Many entities in one domain -> high score
        for i in range(10):
            registry.register(_make_entity(f"e{i}", Domain.GOVERNANCE))

        reporter = ProbeReporter(config, registry)
        report = reporter.generate_report()

        assert len(report.coverage) == 1
        score = report.coverage[0]
        assert score.domain == Domain.GOVERNANCE
        assert score.entity_count == 10
        assert score.weight == 1.5

    def test_dependency_edges_from_explicit_deps(self) -> None:
        config = ProbeConfig()
        registry = EntityRegistry()
        e1 = _make_entity("e1", dependencies=("e2",))
        e2 = _make_entity("e2")
        registry.register(e1)
        registry.register(e2)

        reporter = ProbeReporter(config, registry)
        report = reporter.generate_report()

        depends_on_edges = [e for e in report.dependency_edges if e.relation == "depends_on"]
        assert len(depends_on_edges) == 1
        assert depends_on_edges[0].from_id == "e1"
        assert depends_on_edges[0].to_id == "e2"

    def test_dependency_edges_from_execution_order(self) -> None:
        config = ProbeConfig()
        registry = EntityRegistry()
        e1 = _make_entity("e1", execution_order=1)
        e2 = _make_entity("e2", execution_order=2)
        e3 = _make_entity("e3", execution_order=3)
        registry.register_many([e1, e2, e3])

        reporter = ProbeReporter(config, registry)
        report = reporter.generate_report()

        precedes_edges = [e for e in report.dependency_edges if e.relation == "precedes"]
        assert len(precedes_edges) == 2
        assert precedes_edges[0].from_id == "e1"
        assert precedes_edges[0].to_id == "e2"
        assert precedes_edges[1].from_id == "e2"
        assert precedes_edges[1].to_id == "e3"


# =============================================================================
# File output
# =============================================================================


class TestFileOutput:
    def test_write_json_report(self, tmp_path: Path) -> None:
        config = ProbeConfig(project_root=tmp_path, data_dir="data/probe")
        registry = EntityRegistry()
        registry.register(_make_entity("e1"))
        reporter = ProbeReporter(config, registry)

        report = reporter.generate_report()
        output_path = reporter.write_json_report(report)

        assert output_path.exists()
        with open(output_path) as f:
            data = json.load(f)
        assert data["summary"]["total_entities"] == 1
        assert "report_id" in data

    def test_write_json_report_custom_path(self, tmp_path: Path) -> None:
        config = ProbeConfig()
        registry = EntityRegistry()
        reporter = ProbeReporter(config, registry)

        report = reporter.generate_report()
        custom_path = tmp_path / "custom" / "report.json"
        output_path = reporter.write_json_report(report, output_path=custom_path)

        assert output_path == custom_path
        assert custom_path.exists()

    def test_write_entity_map(self, tmp_path: Path) -> None:
        config = ProbeConfig(project_root=tmp_path, data_dir="data/probe")
        registry = EntityRegistry()
        registry.register(_make_entity("e1"))
        reporter = ProbeReporter(config, registry)

        output_path = reporter.write_entity_map()

        assert output_path.exists()
        with open(output_path) as f:
            data = json.load(f)
        assert data["entity_count"] == 1
        assert "e1" in data["entities"]

    def test_write_markdown_report(self, tmp_path: Path) -> None:
        config = ProbeConfig(project_root=tmp_path)
        registry = EntityRegistry()
        registry.register(_make_entity("e1"))
        reporter = ProbeReporter(config, registry)

        report = reporter.generate_report(
            findings=[_make_finding("f1")],
        )
        output_path = reporter.write_markdown_report(report)

        assert output_path.exists()
        md_content = output_path.read_text()
        assert "# Governance Probe Report" in md_content
        assert "e1" in md_content
        assert "f1" in md_content

    def test_markdown_includes_dependency_graph(self, tmp_path: Path) -> None:
        config = ProbeConfig(project_root=tmp_path)
        registry = EntityRegistry()
        e1 = _make_entity("e1", execution_order=1)
        e2 = _make_entity("e2", execution_order=2)
        registry.register_many([e1, e2])
        reporter = ProbeReporter(config, registry)

        report = reporter.generate_report()
        output_path = reporter.write_markdown_report(report)

        md_content = output_path.read_text()
        assert "Dependency Graph" in md_content
        assert "precedes" in md_content
