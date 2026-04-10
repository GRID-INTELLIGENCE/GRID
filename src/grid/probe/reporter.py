"""Probe reporter — generates structured reports and markdown summaries.

Consumes the entity registry and findings to produce:
- JSON report matching probe-report.schema.json
- Markdown summary for docs/probe/
- Coverage scores by domain
- Dependency graph edges
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from grid.probe.config import ProbeConfig
from grid.probe.models import (
    CoverageScore,
    CoverageStatus,
    DependencyEdge,
    Domain,
    Entity,
    Finding,
    ProbeReport,
)
from grid.probe.registry import EntityRegistry

logger = logging.getLogger(__name__)


class ProbeReporter:
    """Generates probe reports in JSON and Markdown formats."""

    def __init__(self, config: ProbeConfig, registry: EntityRegistry) -> None:
        self.config = config
        self.registry = registry

    def generate_report(
        self,
        findings: list[Finding] | None = None,
        *,
        scan_root: str = "",
    ) -> ProbeReport:
        """Generate a complete probe report.

        Args:
            findings: Findings from the scanner. Defaults to empty.
            scan_root: Root path that was scanned.

        Returns:
            A fully populated ProbeReport.
        """
        entities = self.registry.all_entities()
        coverage = self._calculate_coverage(entities)
        edges = self._build_dependency_edges(entities)

        report = ProbeReport(
            generated_at=datetime.now(),
            probe_version=self.config.version,
            scan_root=scan_root or str(self.config.project_root),
            entities=entities,
            findings=findings or [],
            coverage=coverage,
            dependency_edges=edges,
        )

        logger.info(
            "Report generated: %d entities, %d findings, score=%.2f (%s)",
            report.total_entities,
            report.total_findings,
            report.aggregate_score,
            report.aggregate_status.value,
        )

        return report

    def write_json_report(self, report: ProbeReport, output_path: Path | None = None) -> Path:
        """Write the report as JSON.

        Args:
            report: The probe report to write.
            output_path: Override output path. Defaults to data_dir/probe-report.json.

        Returns:
            Path to the written file.
        """
        if output_path is None:
            data_dir = self.config.project_root / self.config.data_dir
            data_dir.mkdir(parents=True, exist_ok=True)
            output_path = data_dir / "probe-report.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(report.to_dict(), f, indent=2)

        logger.info("JSON report written to %s", output_path)
        return output_path

    def write_entity_map(self, output_path: Path | None = None) -> Path:
        """Write the entity map as JSON.

        Args:
            output_path: Override output path. Defaults to data_dir/entity-map.json.

        Returns:
            Path to the written file.
        """
        if output_path is None:
            data_dir = self.config.project_root / self.config.data_dir
            data_dir.mkdir(parents=True, exist_ok=True)
            output_path = data_dir / "entity-map.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        entity_map = self.registry.to_entity_map()
        with open(output_path, "w") as f:
            json.dump(entity_map, f, indent=2)

        logger.info("Entity map written to %s", output_path)
        return output_path

    def write_markdown_report(self, report: ProbeReport, output_path: Path | None = None) -> Path:
        """Write a human-readable Markdown summary.

        Args:
            report: The probe report.
            output_path: Override output path. Defaults to docs/probe/PROBE_REPORT.md.

        Returns:
            Path to the written file.
        """
        if output_path is None:
            docs_dir = self.config.project_root / "docs" / "probe"
            docs_dir.mkdir(parents=True, exist_ok=True)
            output_path = docs_dir / "PROBE_REPORT.md"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        md = self._render_markdown(report)
        output_path.write_text(md)

        logger.info("Markdown report written to %s", output_path)
        return output_path

    def _calculate_coverage(self, entities: list[Entity]) -> list[CoverageScore]:
        """Calculate coverage scores per domain.

        Coverage is based on entity count relative to the total,
        weighted by domain importance from config.
        """
        if not entities:
            return []

        domain_counts: dict[Domain, int] = {}
        for entity in entities:
            domain_counts[entity.domain] = domain_counts.get(entity.domain, 0) + 1

        total = len(entities)
        scores: list[CoverageScore] = []

        for domain, count in domain_counts.items():
            # Score: proportion of entities in this domain relative to expected coverage
            # This is a simple heuristic — in production you'd compare against a baseline
            score = min(1.0, count / max(1, total * 0.15))  # expect ~15% per domain
            weight = self.config.domain_weights.get(domain.value, 1.0)

            if score >= self.config.threshold_healthy:
                status = CoverageStatus.HEALTHY
            elif score >= self.config.threshold_degraded:
                status = CoverageStatus.DEGRADED
            else:
                status = CoverageStatus.FAILING

            scores.append(
                CoverageScore(
                    domain=domain,
                    entity_count=count,
                    tested_count=count,  # In a real probe, this would check test coverage
                    score=round(score, 4),
                    status=status,
                    weight=weight,
                )
            )

        return sorted(scores, key=lambda s: s.weight, reverse=True)

    def _build_dependency_edges(self, entities: list[Entity]) -> list[DependencyEdge]:
        """Build dependency graph edges from entity metadata.

        Infers edges from:
        1. Explicit dependencies in entity.dependencies
        2. Execution order (middleware chain: each precedes the next)
        """
        edges: list[DependencyEdge] = []

        # Explicit dependencies
        for entity in entities:
            edges.extend(
                DependencyEdge(
                    from_id=entity.id,
                    to_id=dep_id,
                    relation="depends_on",
                )
                for dep_id in entity.dependencies
                if self.registry.get(dep_id)
            )

        # Middleware chain ordering (precedes relation)
        middlewares = sorted(
            [e for e in entities if e.execution_order > 0],
            key=lambda e: e.execution_order,
        )
        edges.extend(
            DependencyEdge(
                from_id=middlewares[i].id,
                to_id=middlewares[i + 1].id,
                relation="precedes",
            )
            for i in range(len(middlewares) - 1)
        )

        return edges

    def _render_markdown(self, report: ProbeReport) -> str:
        """Render the report as Markdown."""
        lines: list[str] = [
            "# Governance Probe Report",
            "",
            f"**Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Probe Version:** {report.probe_version}",
            f"**Scan Root:** `{report.scan_root}`",
            "",
            "## Summary",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Total Entities | {report.total_entities} |",
            f"| Total Findings | {report.total_findings} |",
            f"| Critical Findings | {report.critical_findings} |",
            f"| Aggregate Score | {report.aggregate_score:.2%} |",
            f"| Status | **{report.aggregate_status.value.upper()}** |",
            f"| Domains Scanned | {len(report.coverage)} |",
            "",
            "## Coverage by Domain",
            "",
            "| Domain | Entities | Score | Status | Weight |",
            "|--------|----------|-------|--------|--------|",
        ]

        lines.extend(
            f"| {cs.domain.value} | {cs.entity_count} | {cs.score:.2%} | {cs.status.value} | {cs.weight} |"
            for cs in report.coverage
        )

        lines.extend(
            [
                "",
                "## Entity Catalog",
                "",
                "| ID | Label | Type | Domain | Source |",
                "|----|-------|------|--------|--------|",
            ]
        )

        lines.extend(
            f"| `{entity.id}` | {entity.label} | {entity.type.value} | {entity.domain.value} | `{entity.source}` |"
            for entity in sorted(report.entities, key=lambda e: (e.domain.value, e.execution_order))
        )

        if report.findings:
            lines.extend(
                [
                    "",
                    "## Findings",
                    "",
                    "| ID | Severity | Category | Message |",
                    "|----|----------|----------|---------|",
                ]
            )
            lines.extend(
                f"| `{finding.id}` | {finding.severity.value} | {finding.category.value} | {finding.message} |"
                for finding in report.findings
            )

        if report.dependency_edges:
            lines.extend(
                [
                    "",
                    "## Dependency Graph",
                    "",
                    "| From | Relation | To |",
                    "|------|----------|----|",
                ]
            )
            lines.extend(f"| `{edge.from_id}` | {edge.relation} | `{edge.to_id}` |" for edge in report.dependency_edges)

        lines.append("")
        return "\n".join(lines)
