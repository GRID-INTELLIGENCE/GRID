"""
MYCELIUM Domains — Tri-Domain layout for high-altitude resolution.

Categorizes the pathing ecosystem into three immutable boundaries:
1. STATIC (Parentage/Ancestry) — Read-only ground truth.
2. DYNAMIC (Context/Memory) — Mutable state and user profiles.
3. ENGINE (The Pulse) — Private implementation logic.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import NamedTuple


class DomainType(StrEnum):
    STATIC = "static"
    DYNAMIC = "dynamic"
    ENGINE = "engine"


class ResolvedDomain(NamedTuple):
    domain: DomainType
    path: Path
    is_protected: bool


class DomainResolver:
    """Resolves filesystem paths into their functional domains."""

    def __init__(self, root: Path | str):
        self.root = Path(root).resolve()

        # Define Domain Boundaries
        self.static_roots = {self.root / "grid", self.root / "infrastructure"}
        self.dynamic_roots = {self.root / "data", self.root / ".memos", self.root / "workspace"}
        self.engine_roots = {self.root / "src" / "mycelium", self.root / "safety"}

    def resolve(self, path: Path | str) -> ResolvedDomain:
        """Categorizes a path and determines its protection level."""
        abs_path = Path(path).resolve()

        # Check Static Domain
        for sr in self.static_roots:
            if abs_path == sr or sr in abs_path.parents:
                return ResolvedDomain(DomainType.STATIC, abs_path, True)

        # Check Engine Domain
        for er in self.engine_roots:
            if abs_path == er or er in abs_path.parents:
                return ResolvedDomain(DomainType.ENGINE, abs_path, True)

        # Default to Dynamic if within workspace, or mark as outside
        return ResolvedDomain(DomainType.DYNAMIC, abs_path, False)

    def get_accelerative_jump(self, source: DomainType, target: DomainType) -> str:
        """Returns the high-speed resolution vector between domains."""
        if source == DomainType.STATIC and target == DomainType.ENGINE:
            return "Ref-Link (CAS Bypass)"
        return "Standard Path Traversal"
