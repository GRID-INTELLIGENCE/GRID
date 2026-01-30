"""Terrain mapping engine for indexing codebase relationships."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


class TerrainMapper:
    """Maps the repository terrain, identifying package relationships and boundaries."""

    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.map_data: dict[str, Any] = {}

    def map_terrain(self) -> dict[str, Any]:
        """Index the repository and identify relationships."""
        terrain = {"packages": {}, "relationships": [], "boundaries": {}}

        for p in self.root_path.rglob("*.py"):
            try:
                rel_path = p.relative_to(self.root_path)
                component = str(rel_path.parts[0]) if rel_path.parts else "root"

                if component not in terrain["packages"]:
                    terrain["packages"][component] = {"files": [], "dependencies": set()}

                terrain["packages"][component]["files"].append(str(rel_path))

                # Extract imports to find dependencies
                deps = self._extract_imports(p)
                terrain["packages"][component]["dependencies"].update(deps)
            except Exception:
                continue

        # Convert sets to lists for JSON serialization
        for comp in terrain["packages"]:
            terrain["packages"][comp]["dependencies"] = list(terrain["packages"][comp]["dependencies"])

        self.map_data = terrain
        return terrain

    def _extract_imports(self, file_path: Path) -> set[str]:
        """Extract import statements from a python file."""
        imports = set()
        try:
            with open(file_path, encoding="utf-8") as f:
                tree = ast.parse(f.read())
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for name in node.names:
                            imports.add(name.name.split(".")[0])
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        imports.add(node.module.split(".")[0])
        except Exception:
            pass
        return imports
