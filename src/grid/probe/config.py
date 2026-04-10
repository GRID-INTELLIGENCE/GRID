"""Probe configuration loader.

Reads YAML config from config/probe/probe.yaml and config/probe/entities.yaml,
providing typed access to scan targets, classification rules, scoring weights,
and feature flags.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Default project root: 4 levels up from this file (src/grid/probe/config.py -> project root)
_DEFAULT_ROOT = Path(__file__).parent.parent.parent.parent


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file, returning empty dict on failure."""
    try:
        import yaml  # noqa: PLC0415 — lazy import, yaml is optional at import time
    except ImportError:
        logger.warning("PyYAML not installed; using empty config for %s", path)
        return {}

    if not path.exists():
        logger.warning("Config file not found: %s", path)
        return {}

    with open(path) as f:
        data = yaml.safe_load(f) or {}
    return data


@dataclass(frozen=True, slots=True)
class ScanTarget:
    """A directory to scan for entities."""

    path: str
    entity_types: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ClassificationPattern:
    """A regex pattern for auto-classifying entities."""

    id: str
    match: str
    entity_type: str
    domain: str


@dataclass(frozen=True, slots=True)
class SeedEntity:
    """A pre-seeded entity from the entities.yaml catalog."""

    id: str
    label: str
    type: str
    domain: str
    source: str
    class_name: str = ""
    execution_order: int = 0
    description: str = ""
    conditional: bool = False
    condition_flag: str = ""
    critical: bool = False


@dataclass(slots=True)
class ProbeConfig:
    """Typed probe configuration."""

    enabled: bool = True
    version: str = "1.0.0"
    project_root: Path = _DEFAULT_ROOT

    # Scan configuration
    scan_targets: list[ScanTarget] = field(default_factory=list)
    exclude_patterns: list[str] = field(default_factory=list)

    # Classification
    classification_patterns: list[ClassificationPattern] = field(default_factory=list)

    # Scoring
    domain_weights: dict[str, float] = field(default_factory=dict)
    threshold_healthy: float = 0.8
    threshold_degraded: float = 0.5

    # Feature flags
    ast_scanning: bool = True
    pattern_matching: bool = True
    dependency_graph: bool = True
    coverage_scoring: bool = True
    report_generation: bool = True
    api_endpoint: bool = True

    # Output
    data_dir: str = "data/probe"
    output_format: str = "both"
    max_entities: int = 500

    # Seed entities
    seed_entities: list[SeedEntity] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, project_root: Path | None = None) -> ProbeConfig:
        """Load config from YAML files.

        Args:
            project_root: Project root directory. Defaults to auto-detected root.

        Returns:
            Fully populated ProbeConfig instance.
        """
        root = Path(project_root) if project_root else _DEFAULT_ROOT
        config_dir = root / "config" / "probe"

        # Load main config
        probe_data = _load_yaml(config_dir / "probe.yaml")
        # Load entity seed catalog
        entity_data = _load_yaml(config_dir / "entities.yaml")

        return cls._parse(probe_data, entity_data, root)

    @classmethod
    def _parse(
        cls,
        probe_data: dict[str, Any],
        entity_data: dict[str, Any],
        project_root: Path,
    ) -> ProbeConfig:
        """Parse raw YAML dicts into typed config."""
        probe = probe_data.get("probe", {})
        scan = probe_data.get("scan", {})
        classification = probe_data.get("classification", {})
        scoring = probe_data.get("scoring", {})
        features = probe_data.get("features", {})
        output = probe_data.get("output", {})

        # Parse scan targets
        scan_targets = [
            ScanTarget(
                path=t.get("path", ""),
                entity_types=tuple(t.get("entity_types", [])),
            )
            for t in scan.get("roots", [])
        ]

        # Parse classification patterns
        patterns = [
            ClassificationPattern(
                id=p.get("id", ""),
                match=p.get("match", ""),
                entity_type=p.get("entity_type", ""),
                domain=p.get("domain", ""),
            )
            for p in classification.get("patterns", [])
        ]

        # Parse seed entities
        seed_entities = [
            SeedEntity(
                id=e.get("id", ""),
                label=e.get("label", ""),
                type=e.get("type", ""),
                domain=e.get("domain", ""),
                source=e.get("source", ""),
                class_name=e.get("class_name", ""),
                execution_order=e.get("execution_order", 0),
                description=e.get("description", ""),
                conditional=e.get("conditional", False),
                condition_flag=e.get("condition_flag", ""),
                critical=e.get("critical", False),
            )
            for e in entity_data.get("entities", [])
        ]

        return cls(
            enabled=probe.get("enabled", True),
            version=probe.get("version", "1.0.0"),
            project_root=project_root,
            scan_targets=scan_targets,
            exclude_patterns=scan.get("exclude_patterns", []),
            classification_patterns=patterns,
            domain_weights=scoring.get("domain_weights", {}),
            threshold_healthy=scoring.get("thresholds", {}).get("healthy", 0.8),
            threshold_degraded=scoring.get("thresholds", {}).get("degraded", 0.5),
            ast_scanning=features.get("ast_scanning", True),
            pattern_matching=features.get("pattern_matching", True),
            dependency_graph=features.get("dependency_graph", True),
            coverage_scoring=features.get("coverage_scoring", True),
            report_generation=features.get("report_generation", True),
            api_endpoint=features.get("api_endpoint", True),
            data_dir=output.get("data_dir", "data/probe"),
            output_format=output.get("format", "both"),
            max_entities=output.get("max_entities", 500),
            seed_entities=seed_entities,
        )

    @classmethod
    def default(cls, project_root: Path | None = None) -> ProbeConfig:
        """Create a config with sensible defaults (no YAML required).

        Useful for testing or when YAML files are not yet available.
        """
        root = Path(project_root) if project_root else _DEFAULT_ROOT
        return cls(
            project_root=root,
            scan_targets=[
                ScanTarget("src/application/mothership/middleware", ("middleware", "gate", "enforcer")),
                ScanTarget("src/application/mothership/security", ("auth", "jwt", "merit")),
                ScanTarget("src/grid/core_modules", ("gate", "governance")),
                ScanTarget("src/grid/security", ("security", "audit")),
            ],
            exclude_patterns=["__pycache__", "*.pyc", ".git", "node_modules"],
            classification_patterns=[
                ClassificationPattern("cls-middleware", "class.*Middleware", "middleware", "request_pipeline"),
                ClassificationPattern("cls-gate", "(GovernanceGate|GateKeeper|AdmissionGate)", "gate", "governance"),
                ClassificationPattern(
                    "cls-auth", "(Auth|RequiredAuth|AdminAuth|WriteAuth)", "auth_dependency", "authentication"
                ),
                ClassificationPattern("cls-router", "APIRouter", "router", "routing"),
                ClassificationPattern("cls-enforcer", "(Enforcer|Detector|Monitor|Guard)", "enforcer", "security"),
            ],
            domain_weights={
                "governance": 1.5,
                "security": 1.4,
                "authentication": 1.3,
                "request_pipeline": 1.2,
                "throttling": 1.1,
                "routing": 1.0,
                "data_contract": 0.9,
                "safety": 1.3,
            },
        )
