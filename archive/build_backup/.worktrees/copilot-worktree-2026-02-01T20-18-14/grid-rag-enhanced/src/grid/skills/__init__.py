from .base import Skill
from .registry import SkillRegistry, default_registry

# Backward compatibility alias
SkillsRegistry = SkillRegistry

__all__ = ["Skill", "SkillRegistry", "SkillsRegistry", "default_registry"]
