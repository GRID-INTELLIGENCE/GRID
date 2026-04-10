"""Tests for grid.probe.scanner — EntityScanner."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from grid.probe.config import ClassificationPattern, ProbeConfig, ScanTarget, SeedEntity
from grid.probe.models import (
    DiscoveryMethod,
    Domain,
    Entity,
    EntityType,
    FindingCategory,
    Severity,
)
from grid.probe.registry import EntityRegistry
from grid.probe.scanner import EntityScanner, _safe_domain, _safe_entity_type

# =============================================================================
# Helper converters
# =============================================================================


class TestSafeConverters:
    def test_safe_entity_type_valid(self) -> None:
        assert _safe_entity_type("middleware") == EntityType.MIDDLEWARE
        assert _safe_entity_type("gate") == EntityType.GATE

    def test_safe_entity_type_invalid(self) -> None:
        assert _safe_entity_type("not_real") == EntityType.SECURITY

    def test_safe_domain_valid(self) -> None:
        assert _safe_domain("governance") == Domain.GOVERNANCE
        assert _safe_domain("authentication") == Domain.AUTHENTICATION

    def test_safe_domain_invalid(self) -> None:
        assert _safe_domain("not_real") == Domain.SECURITY


# =============================================================================
# Seed entity loading
# =============================================================================


class TestSeedLoading:
    def test_load_seed_entities(self) -> None:
        config = ProbeConfig(
            seed_entities=[
                SeedEntity(
                    id="ent-seed-001",
                    label="SafetyMiddleware",
                    type="middleware",
                    domain="request_pipeline",
                    source="src/middleware.py",
                    class_name="SafetyMiddleware",
                    execution_order=3,
                    description="Safety layer",
                    conditional=False,
                    critical=True,
                ),
                SeedEntity(
                    id="ent-seed-002",
                    label="GovernanceGate",
                    type="gate",
                    domain="governance",
                    source="src/gates.py",
                ),
            ],
        )
        registry = EntityRegistry()
        scanner = EntityScanner(config, registry)

        count = scanner.load_seed_entities()
        assert count == 2
        assert registry.count == 2

        entity = registry.get("ent-seed-001")
        assert entity is not None
        assert entity.label == "SafetyMiddleware"
        assert entity.type == EntityType.MIDDLEWARE
        assert entity.domain == Domain.REQUEST_PIPELINE
        assert entity.discovered_by == DiscoveryMethod.SEED
        assert entity.critical is True

    def test_load_seed_entities_empty(self) -> None:
        config = ProbeConfig(seed_entities=[])
        registry = EntityRegistry()
        scanner = EntityScanner(config, registry)
        assert scanner.load_seed_entities() == 0
        assert registry.count == 0

    def test_load_seed_entities_with_invalid_type(self) -> None:
        """Invalid type/domain strings should fall back to SECURITY."""
        config = ProbeConfig(
            seed_entities=[
                SeedEntity(
                    id="ent-bad-type",
                    label="Bad",
                    type="nonexistent_type",
                    domain="nonexistent_domain",
                    source="src/bad.py",
                ),
            ],
        )
        registry = EntityRegistry()
        scanner = EntityScanner(config, registry)
        scanner.load_seed_entities()

        entity = registry.get("ent-bad-type")
        assert entity is not None
        assert entity.type == EntityType.SECURITY
        assert entity.domain == Domain.SECURITY


# =============================================================================
# AST scanning
# =============================================================================


class TestASTScanning:
    def test_ast_scan_discovers_middleware(self, tmp_path: Path) -> None:
        """AST scan should discover classes matching classification patterns."""
        src_dir = tmp_path / "src" / "middleware"
        src_dir.mkdir(parents=True)
        (src_dir / "test_middleware.py").write_text(
            textwrap.dedent("""\
                class SafetyMiddleware:
                    \"\"\"Safety enforcement layer.\"\"\"
                    pass

                class HelperUtil:
                    \"\"\"Not a governance entity.\"\"\"
                    pass
            """)
        )

        config = ProbeConfig(
            project_root=tmp_path,
            scan_targets=[
                ScanTarget("src/middleware", ("middleware",)),
            ],
            classification_patterns=[
                ClassificationPattern("cls-mw", ".*Middleware", "middleware", "request_pipeline"),
            ],
            ast_scanning=True,
            pattern_matching=False,
        )
        registry = EntityRegistry()
        scanner = EntityScanner(config, registry)

        count = scanner.scan_all()
        assert count == 1
        assert registry.count == 1

        entities = registry.get_by_type(EntityType.MIDDLEWARE)
        assert len(entities) == 1
        assert entities[0].class_name == "SafetyMiddleware"
        assert entities[0].discovered_by == DiscoveryMethod.AST_SCAN

    def test_ast_scan_missing_target(self, tmp_path: Path) -> None:
        """Missing scan target should produce a GAP finding."""
        config = ProbeConfig(
            project_root=tmp_path,
            scan_targets=[
                ScanTarget("nonexistent/path", ("middleware",)),
            ],
        )
        registry = EntityRegistry()
        scanner = EntityScanner(config, registry)

        count = scanner.scan_all()
        assert count == 0
        assert len(scanner.findings) == 1
        assert scanner.findings[0].category == FindingCategory.GAP

    def test_ast_scan_syntax_error(self, tmp_path: Path) -> None:
        """Files with syntax errors should be skipped without crashing."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "bad.py").write_text("def broken(\n")

        config = ProbeConfig(
            project_root=tmp_path,
            scan_targets=[ScanTarget("src", ("middleware",))],
            classification_patterns=[
                ClassificationPattern("cls-mw", ".*Middleware", "middleware", "request_pipeline"),
            ],
            ast_scanning=True,
            pattern_matching=False,
        )
        registry = EntityRegistry()
        scanner = EntityScanner(config, registry)

        count = scanner.scan_all()
        assert count == 0  # no crash

    def test_ast_scan_exclude_patterns(self, tmp_path: Path) -> None:
        """Files matching exclude patterns should be skipped."""
        src_dir = tmp_path / "src"
        cache_dir = src_dir / "__pycache__"
        cache_dir.mkdir(parents=True)
        (cache_dir / "cached.py").write_text("class CachedMiddleware: pass\n")

        config = ProbeConfig(
            project_root=tmp_path,
            scan_targets=[ScanTarget("src", ("middleware",))],
            classification_patterns=[
                ClassificationPattern("cls-mw", ".*Middleware", "middleware", "request_pipeline"),
            ],
            exclude_patterns=["__pycache__"],
            ast_scanning=True,
            pattern_matching=False,
        )
        registry = EntityRegistry()
        scanner = EntityScanner(config, registry)

        count = scanner.scan_all()
        assert count == 0


# =============================================================================
# Pattern scanning
# =============================================================================


class TestPatternScanning:
    def test_pattern_scan_discovers_entities(self, tmp_path: Path) -> None:
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "gates.py").write_text(
            textwrap.dedent("""\
                # GovernanceGate implementation
                class GovernanceGate:
                    pass

                class GateKeeper:
                    pass
            """)
        )

        config = ProbeConfig(
            project_root=tmp_path,
            scan_targets=[ScanTarget("src", ("gate",))],
            classification_patterns=[
                ClassificationPattern("cls-gate", "(GovernanceGate|GateKeeper)", "gate", "governance"),
            ],
            ast_scanning=False,
            pattern_matching=True,
        )
        registry = EntityRegistry()
        scanner = EntityScanner(config, registry)

        count = scanner.scan_all()
        assert count >= 2  # at least GovernanceGate and GateKeeper
        assert all(e.discovered_by == DiscoveryMethod.PATTERN_MATCH for e in registry.all_entities())

    def test_pattern_scan_disabled(self, tmp_path: Path) -> None:
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "gates.py").write_text("class GovernanceGate: pass\n")

        config = ProbeConfig(
            project_root=tmp_path,
            scan_targets=[ScanTarget("src", ("gate",))],
            classification_patterns=[
                ClassificationPattern("cls-gate", "GovernanceGate", "gate", "governance"),
            ],
            ast_scanning=False,
            pattern_matching=False,
        )
        registry = EntityRegistry()
        scanner = EntityScanner(config, registry)

        count = scanner.scan_all()
        assert count == 0


# =============================================================================
# Findings
# =============================================================================


class TestFindings:
    def test_findings_property_returns_copy(self) -> None:
        config = ProbeConfig()
        registry = EntityRegistry()
        scanner = EntityScanner(config, registry)

        findings_ref_1 = scanner.findings
        findings_ref_2 = scanner.findings
        assert findings_ref_1 is not findings_ref_2

    def test_probe_disabled(self) -> None:
        config = ProbeConfig(enabled=False)
        registry = EntityRegistry()
        scanner = EntityScanner(config, registry)
        # scan_all respects enabled flag (tested via engine)
        # scanner itself doesn't check — engine does
        assert scanner.findings == []
