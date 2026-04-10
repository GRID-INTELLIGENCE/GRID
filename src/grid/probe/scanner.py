"""Entity scanner — discovers governance entities from the filesystem.

Two discovery strategies:
1. AST scanning: Parses Python files to find class definitions matching
   classification patterns (Middleware, Gate, Auth, Router, etc.)
2. Pattern matching: Regex search over file contents for governance markers.

Discovered entities are registered in the EntityRegistry.
"""

from __future__ import annotations

import ast
import logging
import re
from pathlib import Path
from typing import Any

from grid.probe.config import ClassificationPattern, ProbeConfig, ScanTarget, SeedEntity
from grid.probe.models import (
    DiscoveryMethod,
    Domain,
    Entity,
    EntityType,
    Finding,
    FindingCategory,
    Severity,
)
from grid.probe.registry import EntityRegistry

logger = logging.getLogger(__name__)


def _safe_entity_type(value: str) -> EntityType:
    """Convert a string to EntityType, falling back to SECURITY."""
    try:
        return EntityType(value)
    except ValueError:
        return EntityType.SECURITY


def _safe_domain(value: str) -> Domain:
    """Convert a string to Domain, falling back to SECURITY."""
    try:
        return Domain(value)
    except ValueError:
        return Domain.SECURITY


class EntityScanner:
    """Discovers governance entities from the filesystem.

    Uses AST parsing and regex pattern matching to find classes,
    functions, and configuration that constitute governance entities.
    """

    def __init__(self, config: ProbeConfig, registry: EntityRegistry) -> None:
        self.config = config
        self.registry = registry
        self._findings: list[Finding] = []
        self._finding_counter = 0

    @property
    def findings(self) -> list[Finding]:
        """Findings generated during scanning."""
        return list(self._findings)

    def load_seed_entities(self) -> int:
        """Load pre-seeded entities from config into the registry.

        Returns:
            Number of seed entities loaded.
        """
        entities = [self._seed_to_entity(s) for s in self.config.seed_entities]
        count = self.registry.register_many(entities)
        logger.info("Loaded %d seed entities", count)
        return count

    def scan_all(self) -> int:
        """Run all scan strategies across configured targets.

        Returns:
            Total number of new entities discovered.
        """
        total = 0

        for target in self.config.scan_targets:
            target_path = self.config.project_root / target.path
            if not target_path.exists():
                self._add_finding(
                    Severity.MEDIUM,
                    FindingCategory.GAP,
                    f"Scan target does not exist: {target.path}",
                    source_file=target.path,
                )
                continue

            if self.config.ast_scanning:
                total += self._ast_scan(target_path, target)

            if self.config.pattern_matching:
                total += self._pattern_scan(target_path, target)

        logger.info("Discovered %d new entities across %d targets", total, len(self.config.scan_targets))
        return total

    def _ast_scan(self, target_path: Path, target: ScanTarget) -> int:
        """Scan Python files using AST parsing.

        Args:
            target_path: Absolute path to scan directory.
            target: Scan target configuration.

        Returns:
            Number of new entities discovered.
        """
        count = 0
        py_files = list(target_path.rglob("*.py"))

        for py_file in py_files:
            if self._should_exclude(py_file):
                continue

            try:
                source_code = py_file.read_text(encoding="utf-8")
                tree = ast.parse(source_code, filename=str(py_file))
            except (SyntaxError, UnicodeDecodeError) as exc:
                logger.debug("Skipping %s: %s", py_file, exc)
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    entity = self._classify_class(node, py_file, target)
                    if entity and self.registry.register(entity):
                        count += 1

        return count

    def _pattern_scan(self, target_path: Path, target: ScanTarget) -> int:
        """Scan files using regex pattern matching.

        Args:
            target_path: Absolute path to scan directory.
            target: Scan target configuration.

        Returns:
            Number of new entities discovered.
        """
        count = 0
        py_files = list(target_path.rglob("*.py"))

        for py_file in py_files:
            if self._should_exclude(py_file):
                continue

            try:
                content = py_file.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue

            for pattern in self.config.classification_patterns:
                for match in re.finditer(pattern.match, content):
                    line_number = content[: match.start()].count("\n") + 1
                    entity_id = self._generate_entity_id(pattern, py_file, line_number)

                    entity = Entity(
                        id=entity_id,
                        label=match.group(0),
                        type=_safe_entity_type(pattern.entity_type),
                        domain=_safe_domain(pattern.domain),
                        source=str(py_file.relative_to(self.config.project_root)),
                        class_name=match.group(0),
                        line_number=line_number,
                        discovered_by=DiscoveryMethod.PATTERN_MATCH,
                    )

                    if self.registry.register(entity):
                        count += 1

        return count

    def _classify_class(
        self,
        node: ast.ClassDef,
        py_file: Path,
        target: ScanTarget,
    ) -> Entity | None:
        """Classify an AST class definition against known patterns.

        Args:
            node: AST ClassDef node.
            py_file: Source file path.
            target: Scan target for context.

        Returns:
            Entity if classified, None otherwise.
        """
        class_name = node.name

        for pattern in self.config.classification_patterns:
            if re.search(pattern.match, class_name):
                relative_path = str(py_file.relative_to(self.config.project_root))
                entity_id = f"ent-ast-{relative_path.replace('/', '-').replace('.py', '')}-{class_name}".lower()

                # Extract docstring
                docstring = ""
                if (
                    node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)
                ):
                    docstring = node.body[0].value.value.strip().split("\n")[0]

                return Entity(
                    id=entity_id,
                    label=class_name,
                    type=_safe_entity_type(pattern.entity_type),
                    domain=_safe_domain(pattern.domain),
                    source=relative_path,
                    class_name=class_name,
                    line_number=node.lineno,
                    description=docstring,
                    discovered_by=DiscoveryMethod.AST_SCAN,
                )

        return None

    def _should_exclude(self, path: Path) -> bool:
        """Check if a path matches exclusion patterns."""
        path_str = str(path)
        return any(pattern in path_str for pattern in self.config.exclude_patterns)

    def _generate_entity_id(self, pattern: ClassificationPattern, py_file: Path, line: int) -> str:
        """Generate a unique entity ID for a pattern match."""
        relative = str(py_file.relative_to(self.config.project_root))
        return f"ent-pat-{relative.replace('/', '-').replace('.py', '')}-L{line}-{pattern.id}".lower()

    def _seed_to_entity(self, seed: SeedEntity) -> Entity:
        """Convert a SeedEntity config to a domain Entity."""
        return Entity(
            id=seed.id,
            label=seed.label,
            type=_safe_entity_type(seed.type),
            domain=_safe_domain(seed.domain),
            source=seed.source,
            class_name=seed.class_name,
            execution_order=seed.execution_order,
            description=seed.description,
            conditional=seed.conditional,
            condition_flag=seed.condition_flag,
            critical=seed.critical,
            discovered_by=DiscoveryMethod.SEED,
        )

    def _add_finding(
        self,
        severity: Severity,
        category: FindingCategory,
        message: str,
        *,
        entity_id: str = "",
        source_file: str = "",
        line_number: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record a finding."""
        self._finding_counter += 1
        self._findings.append(
            Finding(
                id=f"find-scan-{self._finding_counter:04d}",
                severity=severity,
                category=category,
                message=message,
                entity_id=entity_id,
                source_file=source_file,
                line_number=line_number,
                metadata=metadata or {},
            )
        )
