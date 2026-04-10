"""Probe engine — orchestrates the full probe pipeline.

This is the main entry point for running the governance probe.
It wires together config, scanner, registry, and reporter to
execute the full scan-and-report cycle.
"""

from __future__ import annotations

import logging
from pathlib import Path

from grid.probe.config import ProbeConfig
from grid.probe.models import ProbeReport
from grid.probe.registry import EntityRegistry
from grid.probe.reporter import ProbeReporter
from grid.probe.scanner import EntityScanner

logger = logging.getLogger(__name__)


class ProbeEngine:
    """Orchestrates the governance probe pipeline.

    Pipeline steps:
    1. Load config (YAML or defaults)
    2. Load seed entities from entity catalog
    3. Scan filesystem for additional entities (AST + pattern matching)
    4. Generate coverage scores and dependency graph
    5. Produce report (JSON + Markdown)

    Usage:
        engine = ProbeEngine.from_config()
        report = engine.run()
        # or step-by-step:
        engine.load_seeds()
        engine.scan()
        report = engine.report()
    """

    def __init__(self, config: ProbeConfig) -> None:
        self.config = config
        self.registry = EntityRegistry()
        self.scanner = EntityScanner(config, self.registry)
        self.reporter = ProbeReporter(config, self.registry)

    @classmethod
    def from_config(cls, project_root: Path | None = None) -> ProbeEngine:
        """Create engine by loading YAML config.

        Args:
            project_root: Override project root. Defaults to auto-detection.

        Returns:
            Configured ProbeEngine instance.
        """
        config = ProbeConfig.from_yaml(project_root)
        return cls(config)

    @classmethod
    def with_defaults(cls, project_root: Path | None = None) -> ProbeEngine:
        """Create engine with default config (no YAML needed).

        Args:
            project_root: Override project root.

        Returns:
            ProbeEngine with sensible defaults.
        """
        config = ProbeConfig.default(project_root)
        return cls(config)

    def load_seeds(self) -> int:
        """Load seed entities from the entity catalog.

        Returns:
            Number of seed entities loaded.
        """
        return self.scanner.load_seed_entities()

    def scan(self) -> int:
        """Run entity discovery scan.

        Returns:
            Number of new entities discovered.
        """
        if not self.config.enabled:
            logger.info("Probe is disabled, skipping scan")
            return 0

        return self.scanner.scan_all()

    def report(self, *, write_output: bool = False) -> ProbeReport:
        """Generate the probe report.

        Args:
            write_output: If True, write JSON and Markdown reports to disk.

        Returns:
            The generated ProbeReport.
        """
        probe_report = self.reporter.generate_report(
            findings=self.scanner.findings,
            scan_root=str(self.config.project_root),
        )

        if write_output and self.config.report_generation:
            self.reporter.write_json_report(probe_report)
            self.reporter.write_entity_map()

            if self.config.output_format in ("both", "markdown"):
                self.reporter.write_markdown_report(probe_report)

        return probe_report

    def run(self, *, write_output: bool = False) -> ProbeReport:
        """Execute the full probe pipeline: seeds -> scan -> report.

        This is the primary entry point for running a complete probe.

        Args:
            write_output: If True, write reports to disk.

        Returns:
            The complete ProbeReport.
        """
        logger.info("Starting governance probe v%s", self.config.version)

        seed_count = self.load_seeds()
        logger.info("Loaded %d seed entities", seed_count)

        discovered = self.scan()
        logger.info("Discovered %d new entities", discovered)

        report = self.report(write_output=write_output)
        logger.info(
            "Probe complete: %d entities, %d findings, score=%.2f (%s)",
            report.total_entities,
            report.total_findings,
            report.aggregate_score,
            report.aggregate_status.value,
        )

        return report
