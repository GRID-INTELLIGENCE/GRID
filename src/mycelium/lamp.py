"""
MYCELIUM Lamp — Illuminating the Tri-Domain Architecture.

You cannot safely walk the Tri-Domain Architecture in the dark.
The "Lamp" checks the boundaries before you cross them, turning
unpredictable jumps into a visible, walkable neighborhood.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from mycelium.domains import DomainResolver, DomainType, ResolvedDomain

logger = logging.getLogger(__name__)

@dataclass
class IlluminatedPath:
    path: str
    domain: DomainType
    is_protected: bool
    refractive_index: float  # High for ENGINE (dense logic), Low for DYNAMIC (chaotic context)
    accelerative_jump: str | None = None
    warnings: list[str] = None


class DomainLamp:
    """Shines light on a domain path before locomotion engages."""

    def __init__(self, resolver: DomainResolver):
        self.resolver = resolver

    def _calculate_friction(self, domain: DomainType) -> float:
        """Determines the refractive index/friction of the domain."""
        if domain == DomainType.ENGINE:
            return 1.5  # High density, fast execution, tight curves
        elif domain == DomainType.STATIC:
            return 1.0  # Ground truth, base friction
        else:
            return 0.5  # Dynamic context, highly variable, low density

    def illuminate(self, path: str, current_domain: DomainType | None = None) -> IlluminatedPath:
        """
        Projects light onto the path. Returns an IlluminatedPath outlining
        the domain, friction, and any boundary jumps required.
        """
        resolved: ResolvedDomain = self.resolver.resolve(path)

        jump = None
        warnings = []
        if current_domain and current_domain != resolved.domain:
            jump = self.resolver.get_accelerative_jump(current_domain, resolved.domain)
            if resolved.is_protected:
                warnings.append(f"BOUNDARY CROSSING: Entering protected {resolved.domain.value.upper()} territory.")

        friction = self._calculate_friction(resolved.domain)

        logger.info(f"💡 Lamp illuminated {path}: Domain={resolved.domain.value}, Friction/Refraction={friction}")

        return IlluminatedPath(
            path=path,
            domain=resolved.domain,
            is_protected=resolved.is_protected,
            refractive_index=friction,
            accelerative_jump=jump,
            warnings=warnings or []
        )
