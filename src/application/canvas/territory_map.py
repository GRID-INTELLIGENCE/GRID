r"""
GRID Territory Map - Satellite View Navigation System

This module provides a spatial map of GRID's codebase with path resolution intelligence.
Inspired by Google Maps tile pyramids and Google Earth Engine spatial hierarchy.

Territory Zones (aligned with wheel.py WheelZone):
- CORE: src/grid/ - Core intelligence, agentic systems, events
- COGNITIVE: src/cognitive/ - Cognitive processing
- APPLICATION: src/application/ - FastAPI apps (mothership, resonance, canvas)
- TOOLS: src/tools/ - Utilities, RAG, analysis
- ARENA: Arena/ - Simulation and penalty systems
- INTERFACES: src/grid/interfaces/ - Bridge layers
- AGENTIC: src/grid/agentic/ - Agentic system components

Map Layers (pyramid levels from satellite observation):
- L0: Root workspace (e:\grid)
- L1: Top-level packages (src/, tests/, config/)
- L2: Major modules (grid/, application/, tools/)
- L3: Sub-modules (mothership/, resonance/, canvas/)
- L4: Component files (routers/, models/, schemas/)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TerritoryZone(str, Enum):
    """Territory zones aligned with GRID's spatial structure."""

    CORE = "core"  # src/grid/
    COGNITIVE = "cognitive"  # src/cognitive/
    APPLICATION = "application"  # src/application/
    TOOLS = "tools"  # src/tools/
    ARENA = "arena"  # Arena/
    INTERFACES = "interfaces"  # src/grid/interfaces/
    AGENTIC = "agentic"  # src/grid/agentic/


class PyramidLevel(int, Enum):
    """Spatial pyramid levels for hierarchical navigation."""

    ROOT = 0  # e:\grid
    PACKAGES = 1  # src/, tests/, config/
    MODULES = 2  # grid/, application/, tools/
    SUBMODULES = 3  # mothership/, resonance/, canvas/
    COMPONENTS = 4  # routers/, models/, schemas/
    FILES = 5  # Individual .py files


@dataclass
class PathNode:
    """A node in the GRID territory map."""

    path: Path
    zone: TerritoryZone
    level: PyramidLevel
    import_path: str  # Python import path
    common_imports: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ImportPattern:
    """Common import pattern with resolution."""

    pattern: str  # e.g., "from application.mothership"
    from_zone: TerritoryZone
    to_zone: TerritoryZone
    resolution: str  # How to fix if broken
    examples: list[str] = field(default_factory=list)


class GRIDTerritoryMap:
    """
    Satellite-view navigation system for GRID codebase.

    Provides path resolution intelligence using spatial hierarchy
    and zone-based navigation patterns.
    """

    def __init__(self, workspace_root: Path):
        """Initialize territory map.

        Args:
            workspace_root: Root path of GRID workspace
        """
        self.root = Path(workspace_root)
        self.nodes: dict[str, PathNode] = {}
        self.import_patterns: list[ImportPattern] = []
        self._build_map()

    def _build_map(self) -> None:
        """Build the territory map from satellite observation."""

        # Level 0: Root
        self._register_node(
            self.root,
            TerritoryZone.CORE,
            PyramidLevel.ROOT,
            "",
            "GRID workspace root",
        )

        # Level 1: Top-level packages
        for pkg in ["src", "tests", "config", "scripts", "docs"]:
            pkg_path = self.root / pkg
            if pkg_path.exists():
                self._register_node(
                    pkg_path,
                    TerritoryZone.CORE,
                    PyramidLevel.PACKAGES,
                    pkg,
                    f"Top-level {pkg} package",
                )

        # Level 2: Major modules in src/
        src = self.root / "src"
        if src.exists():
            # CORE zone: grid/
            grid_path = src / "grid"
            if grid_path.exists():
                self._register_node(
                    grid_path,
                    TerritoryZone.CORE,
                    PyramidLevel.MODULES,
                    "grid",
                    "Core GRID intelligence layer",
                    common_imports=["from grid.agentic import", "from grid.events import"],
                )

            # APPLICATION zone: application/
            app_path = src / "application"
            if app_path.exists():
                self._register_node(
                    app_path,
                    TerritoryZone.APPLICATION,
                    PyramidLevel.MODULES,
                    "application",
                    "FastAPI applications layer",
                    common_imports=["from application.mothership import", "from application.canvas import"],
                )

            # TOOLS zone: tools/
            tools_path = src / "tools"
            if tools_path.exists():
                self._register_node(
                    tools_path,
                    TerritoryZone.TOOLS,
                    PyramidLevel.MODULES,
                    "tools",
                    "Utilities and tools layer",
                    common_imports=["from tools.integration import", "from tools.rag import"],
                )

            # COGNITIVE zone: cognitive/
            cog_path = src / "cognitive"
            if cog_path.exists():
                self._register_node(
                    cog_path,
                    TerritoryZone.COGNITIVE,
                    PyramidLevel.MODULES,
                    "cognitive",
                    "Cognitive processing layer",
                )

        # Level 3: Application sub-modules
        app_src = src / "application"
        if app_src.exists():
            for submod in ["mothership", "resonance", "canvas"]:
                submod_path = app_src / submod
                if submod_path.exists():
                    self._register_node(
                        submod_path,
                        TerritoryZone.APPLICATION,
                        PyramidLevel.SUBMODULES,
                        f"application.{submod}",
                        f"{submod.capitalize()} application module",
                        common_imports=[
                            f"from application.{submod}.main import",
                            f"from application.{submod}.routers import",
                        ],
                    )

        # Register common import patterns
        self._register_import_patterns()

    def _register_node(
        self,
        path: Path,
        zone: TerritoryZone,
        level: PyramidLevel,
        import_path: str,
        description: str,
        common_imports: list[str] | None = None,
    ) -> None:
        """Register a path node in the map."""
        node = PathNode(
            path=path,
            zone=zone,
            level=level,
            import_path=import_path,
            common_imports=common_imports or [],
            description=description,
        )
        self.nodes[str(path)] = node

    def _register_import_patterns(self) -> None:
        """Register common import patterns with resolutions."""

        # Pattern 1: Relative imports within same module
        self.import_patterns.append(
            ImportPattern(
                pattern="from . import utils",
                from_zone=TerritoryZone.APPLICATION,
                to_zone=TerritoryZone.APPLICATION,
                resolution="Ensure __init__.py exists and parent is a package",
                examples=[
                    "from . import routers  # In application/mothership/__init__.py",
                    "from .config import settings  # In application/mothership/main.py",
                ],
            )
        )

        # Pattern 2: Absolute imports from src/
        self.import_patterns.append(
            ImportPattern(
                pattern="from application.mothership import main",
                from_zone=TerritoryZone.CORE,
                to_zone=TerritoryZone.APPLICATION,
                resolution="Ensure PYTHONPATH includes src/ directory",
                examples=[
                    "from application.mothership.main import create_app",
                    "from application.canvas.router import router",
                ],
            )
        )

        # Pattern 3: Cross-zone imports
        self.import_patterns.append(
            ImportPattern(
                pattern="from grid.agentic import AgenticSystem",
                from_zone=TerritoryZone.APPLICATION,
                to_zone=TerritoryZone.CORE,
                resolution="Use absolute imports from src/, not relative",
                examples=[
                    "from grid.agentic.agentic_system import AgenticSystem",
                    "from grid.events.core import EventBus",
                ],
            )
        )

        # Pattern 4: Tools imports
        self.import_patterns.append(
            ImportPattern(
                pattern="from tools.integration import get_tools_integration",
                from_zone=TerritoryZone.APPLICATION,
                to_zone=TerritoryZone.TOOLS,
                resolution="Import from tools module, ensure src/ in PYTHONPATH",
                examples=[
                    "from tools.integration import ToolsProvider",
                    "from tools.rag import RAGEngine",
                ],
            )
        )

    def resolve_import_path(self, from_file: Path, import_statement: str) -> str | None:
        """Resolve an import statement to a file path.

        Args:
            from_file: File where import is used
            import_statement: Import statement (e.g., "from application.mothership import main")

        Returns:
            Suggested fix or None if import looks valid
        """
        # Extract module path from import
        if "from " in import_statement and " import " in import_statement:
            parts = import_statement.split(" import ")
            module_path = parts[0].replace("from ", "").strip()

            # Check if it's a relative import
            if module_path.startswith("."):
                return self._resolve_relative_import(from_file, module_path)
            else:
                return self._resolve_absolute_import(module_path)

        return None

    def _resolve_relative_import(self, from_file: Path, module_path: str) -> str | None:
        """Resolve relative import."""
        # Count dots to determine parent level
        dots = len(module_path) - len(module_path.lstrip("."))

        # Navigate up the directory tree
        current = from_file.parent
        for _ in range(dots):
            current = current.parent

        # Check if __init__.py exists
        init_file = current / "__init__.py"
        if not init_file.exists():
            return f"Missing __init__.py in {current}. Create it to make this a package."

        return None  # Relative import looks valid

    def _resolve_absolute_import(self, module_path: str) -> str | None:
        """Resolve absolute import."""
        # Convert module path to file path
        parts = module_path.split(".")

        # Check if it starts with known top-level modules
        known_roots = ["grid", "application", "tools", "cognitive"]
        if parts[0] not in known_roots:
            return f"Unknown top-level module '{parts[0]}'. Did you mean one of: {', '.join(known_roots)}?"

        # Build expected path
        expected_path = self.root / "src" / Path(*parts)

        # Check if path exists (as directory or .py file)
        if not expected_path.exists() and not expected_path.with_suffix(".py").exists():
            return f"Module {module_path} not found. Expected at {expected_path}"

        return None  # Import looks valid

    def get_zone_map(self) -> dict[str, Any]:
        """Get visual representation of territory zones.

        Returns:
            Dictionary with zone hierarchy
        """
        zone_map = {}

        for zone in TerritoryZone:
            zone_nodes = [
                {
                    "path": str(node.path.relative_to(self.root)),
                    "import": node.import_path,
                    "level": node.level.name,
                    "description": node.description,
                }
                for node in self.nodes.values()
                if node.zone == zone
            ]
            zone_map[zone.value] = {
                "nodes": zone_nodes,
                "count": len(zone_nodes),
            }

        return zone_map

    def get_import_guide(self, from_zone: TerritoryZone | None = None) -> list[dict[str, Any]]:
        """Get import pattern guide.

        Args:
            from_zone: Optional zone to filter patterns

        Returns:
            List of import patterns with examples
        """
        patterns = self.import_patterns
        if from_zone:
            patterns = [p for p in patterns if p.from_zone == from_zone]

        return [
            {
                "pattern": p.pattern,
                "from": p.from_zone.value,
                "to": p.to_zone.value,
                "resolution": p.resolution,
                "examples": p.examples,
            }
            for p in patterns
        ]

    def diagnose_import_error(self, error_message: str) -> str:
        """Diagnose an import error and suggest fix.

        Args:
            error_message: Import error message

        Returns:
            Suggested fix
        """
        error_lower = error_message.lower()

        if "no module named" in error_lower:
            # Extract module name
            if "'" in error_message:
                module_name = error_message.split("'")[1]
                return self._suggest_module_fix(module_name)

        elif "cannot import name" in error_lower:
            return "Check that the imported name exists in the target module. Use grep_search to verify."

        elif "attempted relative import" in error_lower:
            return "Relative imports require the parent to be a package. Ensure __init__.py exists and run with 'python -m' syntax."

        return "Run: python -c 'import sys; print(sys.path)' to check PYTHONPATH. Ensure src/ is included."

    def _suggest_module_fix(self, module_name: str) -> str:
        """Suggest fix for missing module."""
        parts = module_name.split(".")

        if parts[0] in ["grid", "application", "tools", "cognitive"]:
            return "PYTHONPATH issue: Run from src/ or set PYTHONPATH to your project's src directory"

        elif module_name in ["numpy", "fastapi", "pydantic"]:
            return f"Missing dependency: Run 'python -m pip install {module_name}'"

        else:
            return f"Module '{module_name}' not found in workspace. Check spelling or create the module."


# Global instance for convenience
_grid_map: GRIDTerritoryMap | None = None


def get_grid_map(workspace_root: Path | None = None) -> GRIDTerritoryMap:
    r"""Get or create the global GRID territory map.

    Args:
        workspace_root: Optional workspace root (defaults to e:\grid)

    Returns:
        GRIDTerritoryMap instance
    """
    global _grid_map
    if _grid_map is None:
        # Use environment variable or auto-detect project root
        if workspace_root:
            root = workspace_root
        elif env_root := os.environ.get("GRID_PROJECT_ROOT"):
            root = Path(env_root)
        else:
            # Auto-detect: walk up from this file to find project root
            current = Path(__file__).resolve()
            for parent in current.parents:
                if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
                    root = parent
                    break
            else:
                root = Path.cwd()
        _grid_map = GRIDTerritoryMap(root)
    return _grid_map


__all__ = [
    "TerritoryZone",
    "PyramidLevel",
    "PathNode",
    "ImportPattern",
    "GRIDTerritoryMap",
    "get_grid_map",
]
