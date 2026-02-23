"""Validates skill dependencies before registration.

Features:
- Module availability checking with caching
- Skill-to-skill dependency detection
- Circular dependency detection (DFS)
- Validation result with errors and warnings
"""

from __future__ import annotations

import ast
import importlib
import importlib.util
import logging
import os
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of dependency validation."""

    skill_id: str
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    skill_dependencies: list[str] = field(default_factory=list)


class DependencyValidator:
    """Validates skill dependencies before registration.

    Uses AST to extract imports and check availability without executing code.
    Caches module availability for 5 minutes to avoid repeated checks.
    """

    _CACHE_TTL = 300  # 5 minutes

    def __init__(self):
        self._module_cache: dict[str, tuple[bool, float]] = {}
        self._skill_graph: dict[str, set[str]] = {}  # skill_id -> set of dependency skill_ids
        self._discovery_timeout = int(os.getenv("GRID_SKILLS_DISCOVERY_TIMEOUT", "30"))

    def validate_dependencies(self, skill_file_path: str, skill_id: str) -> ValidationResult:
        """Validate all dependencies for a skill file.

        Args:
            skill_file_path: Path to the skill source file
            skill_id: Skill identifier

        Returns:
            ValidationResult with errors, warnings, and dependency lists
        """
        result = ValidationResult(skill_id=skill_id, valid=True)

        try:
            with open(skill_file_path, encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)

            # Extract module imports
            imports = self._extract_imports(tree)
            result.dependencies = imports

            # Check module availability
            for imp in imports:
                # Skip standard library and grid internals
                if imp.startswith("grid"):
                    continue
                if imp in (
                    "os",
                    "sys",
                    "json",
                    "time",
                    "logging",
                    "pathlib",
                    "re",
                    "typing",
                    "dataclasses",
                    "enum",
                    "abc",
                    "functools",
                    "collections",
                    "hashlib",
                    "inspect",
                    "ast",
                    "importlib",
                    "base",
                    "dataclass",
                    "sqlite3",
                    "threading",
                    "asyncio",
                ):
                    continue
                # Skip relative imports (these are internal)
                if not imp or imp.startswith("."):
                    continue

                if not self._is_module_available(imp):
                    result.warnings.append(f"External module '{imp}' may not be available")

            # Extract skill dependencies from @depends_on decorator or docstring
            skill_deps = self._extract_skill_dependencies(tree, source)
            result.skill_dependencies = skill_deps

            if skill_deps:
                # Check if skill dependencies are registered
                try:
                    from .registry import default_registry

                    for dep_id in skill_deps:
                        if not default_registry.get(dep_id):
                            result.warnings.append(
                                f"Skill dependency '{dep_id}' is not yet registered. "
                                "Ensure it's registered before '{skill_id}'"
                            )
                except ImportError:
                    pass  # Registry not available during early bootstrap

            # Update dependency graph and check for cycles
            self._skill_graph[skill_id] = set(skill_deps)

            cycle = self._detect_circular_dependencies(skill_id)
            if cycle:
                result.valid = False
                result.errors.append(f"Circular dependency detected: {' -> '.join(cycle)}")

        except SyntaxError as e:
            result.valid = False
            result.errors.append(f"Syntax error in skill file: {e}")
        except Exception as e:
            result.valid = False
            result.errors.append(f"Validation failed: {type(e).__name__}: {e}")

        return result

    def _extract_imports(self, tree: ast.AST) -> list[str]:
        """Extract all module imports from AST."""
        imports = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # Get root module
                    root = alias.name.split(".")[0]
                    imports.add(root)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root = node.module.split(".")[0]
                    imports.add(root)

        return sorted(imports)

    def _extract_skill_dependencies(self, tree: ast.AST, source: str) -> list[str]:
        """Extract skill dependencies from decorators or docstrings."""
        deps = []

        # Look for @depends_on decorator
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.decorator_list:
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call):
                        func = decorator.func
                        if isinstance(func, ast.Name) and func.id == "depends_on":
                            # Parse keyword arguments
                            deps.extend(
                                kw.value.value
                                for kw in decorator.keywords
                                if kw.arg == "skill_id" and isinstance(kw.value, ast.Constant)
                            )
                            # Parse positional arguments
                            deps.extend(arg.value for arg in decorator.args if isinstance(arg, ast.Constant))

        # Also check docstrings for @requires: skill_id pattern
        docstring = ast.get_docstring(tree)
        if docstring:
            import re

            requires_pattern = re.findall(r"@requires:\s*(\w+)", docstring)
            deps.extend(requires_pattern)

        return list(set(deps))

    def _is_module_available(self, module_path: str) -> bool:
        """Check if module can be imported (with caching)."""
        now = time.time()

        # Check cache
        if module_path in self._module_cache:
            available, cached_at = self._module_cache[module_path]
            if now - cached_at < self._CACHE_TTL:
                return available

        # Try to find module spec (faster than importing)
        try:
            spec = importlib.util.find_spec(module_path)
            available = spec is not None
        except (ModuleNotFoundError, ImportError, ValueError):
            available = False

        self._module_cache[module_path] = (available, now)
        return available

    def _detect_circular_dependencies(self, skill_id: str) -> list[str] | None:
        """Detect circular dependencies using DFS.

        Returns:
            List representing the cycle if found, None otherwise
        """
        visited: set[str] = set()
        path: list[str] = []

        def dfs(current: str) -> list[str] | None:
            if current in path:
                # Found cycle - return the cycle portion
                cycle_start = path.index(current)
                return path[cycle_start:] + [current]

            if current in visited:
                return None

            visited.add(current)
            path.append(current)

            for dep in self._skill_graph.get(current, set()):
                result = dfs(dep)
                if result:
                    return result

            path.pop()
            return None

        return dfs(skill_id)

    def get_dependency_order(self) -> list[str]:
        """Get skills in topological order (dependencies first).

        Returns:
            List of skill_ids in order they should be loaded
        """
        in_degree: dict[str, int] = dict.fromkeys(self._skill_graph, 0)

        for skill_id, deps in self._skill_graph.items():
            for dep in deps:
                if dep in in_degree:
                    in_degree[skill_id] = in_degree.get(skill_id, 0) + 1

        # Kahn's algorithm
        queue = [s for s, d in in_degree.items() if d == 0]
        result = []

        while queue:
            skill_id = queue.pop(0)
            result.append(skill_id)

            for other, deps in self._skill_graph.items():
                if skill_id in deps:
                    in_degree[other] -= 1
                    if in_degree[other] == 0:
                        queue.append(other)

        return result

    def clear_cache(self) -> None:
        """Clear module availability cache."""
        self._module_cache.clear()
        logger.debug("Dependency validator cache cleared")
