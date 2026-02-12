"""Discovers and registers skills across the codebase."""

import importlib
import importlib.util
import inspect
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class SkillMetadata:
    id: str
    name: str
    description: str
    version: str
    category: str  # "high-level" or "low-level"
    handler: Any
    file_path: str
    line_number: int


class SkillDiscoveryEngine:
    """Discovers and registers skills across the codebase."""

    def __init__(self):
        self._skills: dict[str, SkillMetadata] = {}
        self._logger = logging.getLogger(__name__)

    def discover_skills(self, base_package: str = "grid.skills") -> int:
        """Discover skills in the specified package."""
        discovered = 0

        try:
            # Try to find the package's filesystem path
            spec = importlib.util.find_spec(base_package)
            if not spec or not spec.origin:
                self._logger.warning(f"Could not find path for package: {base_package}")
                return 0

            base_path = Path(spec.origin).parent
        except Exception as e:
            self._logger.error(f"Error locating base package {base_package}: {e}")
            return 0

        if not base_path.exists():
            self._logger.warning(f"Skills directory not found: {base_path}")
            return 0

        # Skip non-skill modules
        skip_modules = {
            "__init__",
            "base",
            "registry",
            "discovery_engine",
            "extraction_engine",
            "dependency_validator",
            "intelligence_inventory",
            "execution_tracker",
            "intelligence_tracker",
            "behavioral_analyzer",
            "calling_engine",
            "decorators",
            "performance_guard",
            "hot_reload_manager",
            "version_manager",
        }

        for skill_file in base_path.glob("*.py"):
            if skill_file.stem.startswith("_") or skill_file.stem in skip_modules:
                continue

            try:
                module_name = f"{base_package}.{skill_file.stem}"
                module = importlib.import_module(module_name)

                # Look for instances (SimpleSkill) or classes with 'id' and 'run'
                for name, obj in inspect.getmembers(module):
                    # Skip private, imports, and base classes
                    if name.startswith("_"):
                        continue

                    # Check for skill-like object (instance with id and run)
                    skill_obj = None

                    if hasattr(obj, "id") and hasattr(obj, "run") and callable(getattr(obj, "run", None)):
                        # It's either a class or an instance
                        if inspect.isclass(obj):
                            # Try to instantiate
                            try:
                                skill_obj = obj()
                            except Exception:
                                continue
                        else:
                            # It's already an instance
                            skill_obj = obj

                    if skill_obj and hasattr(skill_obj, "id") and skill_obj.id:
                        # Avoid duplicates
                        if skill_obj.id in self._skills:
                            continue

                        metadata = SkillMetadata(
                            id=skill_obj.id,
                            name=getattr(skill_obj, "name", skill_obj.id),
                            description=getattr(skill_obj, "description", ""),
                            version=getattr(skill_obj, "version", "1.0.0"),
                            category=self._determine_category(skill_obj),
                            handler=getattr(skill_obj, "handler", skill_obj.run),
                            file_path=str(skill_file),
                            line_number=1,  # Instances don't have clear line numbers
                        )
                        self._skills[metadata.id] = metadata
                        discovered += 1
                        self._logger.debug(f"Discovered skill: {metadata.id} in {skill_file.name}")

            except Exception as e:
                self._logger.debug(f"Failed to load skill from {skill_file}: {e}")

        return discovered

    def _determine_category(self, skill: Any) -> str:
        """Determine if skill is high-level or low-level."""
        # High-level skills have complex handlers or multiple steps
        try:
            handler = getattr(skill, "handler", None) or getattr(skill, "run", None)
            if not handler:
                return "low-level"

            source = inspect.getsource(handler)
            lines = len(source.split("\n"))

            if lines > 20 or "for " in source or "while " in source or "orchestrator" in source.lower():
                return "high-level"
        except Exception:
            pass

        return "low-level"

    def get_skill_metadata(self, skill_id: str) -> SkillMetadata | None:
        """Get metadata for a specific skill."""
        return self._skills.get(skill_id)

    def list_skills(self) -> list[SkillMetadata]:
        """List all discovered skills."""
        return list(self._skills.values())

    def get_skill_stats(self) -> dict[str, int]:
        """Get skill statistics."""
        return {
            "total": len(self._skills),
            "high_level": sum(1 for s in self._skills.values() if s.category == "high-level"),
            "low_level": sum(1 for s in self._skills.values() if s.category == "low-level"),
        }


# Backward compatibility alias
SkillsDiscoveryEngine = SkillDiscoveryEngine
