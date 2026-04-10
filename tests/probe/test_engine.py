"""Tests for grid.probe.engine — ProbeEngine."""

from __future__ import annotations

from pathlib import Path

import pytest

from grid.probe.config import ClassificationPattern, ProbeConfig, ScanTarget, SeedEntity
from grid.probe.engine import ProbeEngine
from grid.probe.models import CoverageStatus, DiscoveryMethod

# =============================================================================
# Engine construction
# =============================================================================


class TestEngineConstruction:
    def test_with_defaults(self) -> None:
        engine = ProbeEngine.with_defaults()
        assert engine.config.enabled is True
        assert engine.registry.count == 0
        assert len(engine.config.scan_targets) > 0

    def test_with_config(self) -> None:
        config = ProbeConfig(
            enabled=True,
            version="2.0.0",
            scan_targets=[],
        )
        engine = ProbeEngine(config)
        assert engine.config.version == "2.0.0"

    def test_from_config_missing_yaml(self, tmp_path: Path) -> None:
        """from_config should work even when YAML files don't exist."""
        engine = ProbeEngine.from_config(project_root=tmp_path)
        assert engine.config.project_root == tmp_path
        # Should still function with empty config
        assert engine.config.enabled is True


# =============================================================================
# Seed loading
# =============================================================================


class TestSeedLoading:
    def test_load_seeds(self) -> None:
        config = ProbeConfig(
            seed_entities=[
                SeedEntity(
                    id="ent-seed-001",
                    label="TestGate",
                    type="gate",
                    domain="governance",
                    source="src/gates.py",
                ),
                SeedEntity(
                    id="ent-seed-002",
                    label="TestMiddleware",
                    type="middleware",
                    domain="request_pipeline",
                    source="src/middleware.py",
                ),
            ],
        )
        engine = ProbeEngine(config)
        count = engine.load_seeds()
        assert count == 2
        assert engine.registry.count == 2

    def test_load_seeds_empty(self) -> None:
        config = ProbeConfig(seed_entities=[])
        engine = ProbeEngine(config)
        assert engine.load_seeds() == 0


# =============================================================================
# Scanning
# =============================================================================


class TestScanning:
    def test_scan_disabled(self) -> None:
        config = ProbeConfig(enabled=False)
        engine = ProbeEngine(config)
        assert engine.scan() == 0

    def test_scan_with_filesystem(self, tmp_path: Path) -> None:
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "middleware.py").write_text("class SafetyMiddleware:\n    pass\n")

        config = ProbeConfig(
            project_root=tmp_path,
            scan_targets=[ScanTarget("src", ("middleware",))],
            classification_patterns=[
                ClassificationPattern("cls-mw", ".*Middleware", "middleware", "request_pipeline"),
            ],
        )
        engine = ProbeEngine(config)
        count = engine.scan()
        assert count >= 1


# =============================================================================
# Report generation
# =============================================================================


class TestReporting:
    def test_report_empty(self) -> None:
        config = ProbeConfig()
        engine = ProbeEngine(config)
        report = engine.report()
        assert report.total_entities == 0
        assert report.total_findings == 0

    def test_report_after_seeds(self) -> None:
        config = ProbeConfig(
            seed_entities=[
                SeedEntity(
                    id="ent-001",
                    label="Gate",
                    type="gate",
                    domain="governance",
                    source="src/gate.py",
                ),
            ],
        )
        engine = ProbeEngine(config)
        engine.load_seeds()
        report = engine.report()
        assert report.total_entities == 1

    def test_report_write_output(self, tmp_path: Path) -> None:
        config = ProbeConfig(
            project_root=tmp_path,
            data_dir="data/probe",
            output_format="both",
            seed_entities=[
                SeedEntity(
                    id="ent-001",
                    label="Gate",
                    type="gate",
                    domain="governance",
                    source="src/gate.py",
                ),
            ],
        )
        engine = ProbeEngine(config)
        engine.load_seeds()
        report = engine.report(write_output=True)

        assert report.total_entities == 1
        assert (tmp_path / "data" / "probe" / "probe-report.json").exists()
        assert (tmp_path / "data" / "probe" / "entity-map.json").exists()
        assert (tmp_path / "docs" / "probe" / "PROBE_REPORT.md").exists()


# =============================================================================
# Full pipeline (run)
# =============================================================================


class TestFullPipeline:
    def test_run_empty(self) -> None:
        config = ProbeConfig(
            scan_targets=[],
            seed_entities=[],
        )
        engine = ProbeEngine(config)
        report = engine.run()
        assert report.total_entities == 0
        assert report.aggregate_score == 0.0

    def test_run_with_seeds(self) -> None:
        config = ProbeConfig(
            scan_targets=[],
            seed_entities=[
                SeedEntity(
                    id="ent-001",
                    label="SafetyMiddleware",
                    type="middleware",
                    domain="request_pipeline",
                    source="src/middleware.py",
                    execution_order=3,
                    critical=True,
                ),
                SeedEntity(
                    id="ent-002",
                    label="GovernanceGate",
                    type="gate",
                    domain="governance",
                    source="src/gates.py",
                    execution_order=1,
                ),
            ],
        )
        engine = ProbeEngine(config)
        report = engine.run()

        assert report.total_entities == 2
        assert len(report.coverage) > 0
        # Two entities with execution_order -> should have precedes edge
        precedes_edges = [e for e in report.dependency_edges if e.relation == "precedes"]
        assert len(precedes_edges) == 1

    def test_run_with_filesystem(self, tmp_path: Path) -> None:
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "middleware.py").write_text("class TestMiddleware:\n    '''Test.'''\n    pass\n")

        config = ProbeConfig(
            project_root=tmp_path,
            scan_targets=[ScanTarget("src", ("middleware",))],
            classification_patterns=[
                ClassificationPattern("cls-mw", ".*Middleware", "middleware", "request_pipeline"),
            ],
            seed_entities=[
                SeedEntity(
                    id="ent-seed-001",
                    label="PreSeed",
                    type="gate",
                    domain="governance",
                    source="src/pre.py",
                ),
            ],
        )
        engine = ProbeEngine(config)
        report = engine.run()

        # At least the seed + discovered entity
        assert report.total_entities >= 2

    def test_run_write_output(self, tmp_path: Path) -> None:
        config = ProbeConfig(
            project_root=tmp_path,
            data_dir="data/probe",
            output_format="both",
            scan_targets=[],
            seed_entities=[
                SeedEntity(
                    id="ent-001",
                    label="Gate",
                    type="gate",
                    domain="governance",
                    source="src/gate.py",
                ),
            ],
        )
        engine = ProbeEngine(config)
        engine.run(write_output=True)

        assert (tmp_path / "data" / "probe" / "probe-report.json").exists()
        assert (tmp_path / "data" / "probe" / "entity-map.json").exists()
        assert (tmp_path / "docs" / "probe" / "PROBE_REPORT.md").exists()
