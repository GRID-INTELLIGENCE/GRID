"""Skill registry with automated discovery and dependency validation.

Replaces hardcoded skill list with SkillDiscoveryEngine integration.
Validates dependencies before registration.
"""

from __future__ import annotations

import builtins
import importlib
import logging
import os

from .base import Skill

logger = logging.getLogger(__name__)


class SkillRegistry:
    """Registry of available skills with automated discovery."""

    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        """Register a skill."""
        if not getattr(skill, "id", None):
            raise ValueError("Skill.id is required")
        self._skills[skill.id] = skill

    def get(self, skill_id: str) -> Skill | None:
        """Get a skill by ID."""
        return self._skills.get(skill_id)

    def list(self) -> builtins.list[Skill]:
        """List all registered skills."""
        return [self._skills[k] for k in sorted(self._skills.keys())]

    def count(self) -> int:
        """Get count of registered skills."""
        return len(self._skills)

    def unregister(self, skill_id: str) -> bool:
        """Unregister a skill. Returns True if found and removed."""
        if skill_id in self._skills:
            del self._skills[skill_id]
            return True
        return False


def _load_builtin_skills(registry: SkillRegistry) -> None:
    """Load built-in skills using automated discovery.

    Uses SkillDiscoveryEngine for discovery and DependencyValidator
    for validation before registration.
    """
    from pathlib import Path

    use_legacy = os.getenv("GRID_SKILLS_LEGACY_LOADER", "false").lower() == "true"

    if use_legacy:
        _load_builtin_skills_legacy(registry)
        return

    # Use automated discovery
    try:
        from .dependency_validator import DependencyValidator
        from .discovery_engine import SkillDiscoveryEngine

        discovery_engine = SkillDiscoveryEngine()
        validator = DependencyValidator()

        discovered_count = discovery_engine.discover_skills(base_package="grid.skills")
        logger.info(f"Discovered {discovered_count} skills via automated discovery")

        # Track registration stats
        registered = 0
        skipped = 0
        failed = 0

        # Get all discovered skill metadata
        for metadata in discovery_engine.list_skills():
            skill_file = Path(metadata.file_path)

            # Validate dependencies
            validation = validator.validate_dependencies(str(skill_file), metadata.id)

            if not validation.valid:
                logger.warning(f"Skipping {metadata.id}: {validation.errors}")
                skipped += 1
                continue

            if validation.warnings:
                for warning in validation.warnings:
                    logger.debug(f"Skill {metadata.id}: {warning}")

            # Register the skill
            try:
                module_name = f"grid.skills.{skill_file.stem}"
                module = importlib.import_module(module_name)
                skill = getattr(module, skill_file.stem, None)

                if skill and hasattr(skill, "id"):
                    registry.register(skill)
                    registered += 1
                    logger.debug(f"Registered skill: {metadata.id}")
                else:
                    logger.debug(f"No skill object in {module_name}")

            except Exception as e:
                logger.error(f"Failed to register {metadata.id}: {e}")
                failed += 1

        logger.info(f"Skill registration complete: {registered} registered, " f"{skipped} skipped, {failed} failed")

        # Register skills with intelligence inventory if persistence is enabled
        if os.getenv("GRID_SKILLS_PERSIST", "true").lower() == "true":
            try:
                from .intelligence_inventory import IntelligenceInventory

                inventory = IntelligenceInventory.get_instance()

                # Use discovery metadata directly (extraction engine has import issues)
                for metadata in discovery_engine.list_skills():
                    try:
                        inventory.register_skill(
                            skill_id=metadata.id,
                            name=metadata.name,
                            description=metadata.description,
                            version=metadata.version,
                            category=metadata.category,
                            file_path=metadata.file_path,
                        )
                    except Exception as e:
                        logger.debug(f"Could not persist metadata for {metadata.id}: {e}")

                logger.info(f"Persisted {len(discovery_engine.list_skills())} skills to inventory")

            except ImportError as e:
                logger.debug(f"Intelligence inventory not available: {e}")

    except ImportError as e:
        logger.warning(f"Discovery engine not available, falling back to legacy: {e}")
        _load_builtin_skills_legacy(registry)


def _load_builtin_skills_legacy(registry: SkillRegistry) -> None:
    """Legacy skill loader with hardcoded list (fallback)."""

    skills_to_load = [
        ("youtube_transcript_analyze", ".youtube_transcript_analyze"),
        ("intelligence_git_analyze", ".intelligence_git_analyze"),
        ("rag_query_knowledge", ".rag_query_knowledge"),
        ("patterns_detect_entities", ".patterns_detect_entities"),
        ("analysis_process_context", ".analysis_process_context"),
        ("cross_reference_explain", ".cross_reference_explain"),
        ("compress_articulate", ".compress_articulate"),
        ("context_refine", ".context_refine"),
        ("transform_schema_map", ".transform_schema_map"),
        ("topic_extractor", ".topic_extractor"),
        ("knowledge_capture", ".knowledge_capture"),
    ]

    for name, relative_path in skills_to_load:
        try:
            module = importlib.import_module(relative_path, package="grid.skills")
            skill = getattr(module, name)
            registry.register(skill)
        except Exception as e:
            error_msg = f"Failed to load skill '{name}': {type(e).__name__}: {e}"
            logger.error(error_msg)


# Initialize default registry
default_registry = SkillRegistry()
_load_builtin_skills(default_registry)

# Backward compatibility alias
SkillsRegistry = SkillRegistry
