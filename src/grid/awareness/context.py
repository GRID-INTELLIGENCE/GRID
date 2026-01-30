"""Context modeling for the awareness layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Optional import for domain tracking
try:
    from grid.awareness.domain_tracking import DomainTracker, TechnologyDomainTracker
except ImportError:
    DomainTracker = None  # type: ignore
    TechnologyDomainTracker = None  # type: ignore


@dataclass
class Context:
    """Lightweight context container with simple evolution logic.

    Enhanced with optional domain-specific tracking for the Embedded Agentic
    Knowledge System. Domain tracking is optional and maintains backward compatibility.
    """

    temporal_depth: float
    spatial_field: dict[str, Any]
    relational_web: dict[str, Any]
    quantum_signature: str
    domain_tracker: Any | None = field(default=None, repr=False)
    active_domain: str | None = field(default=None)

    async def evolve(self, state: EssentialState) -> Context:
        """Return a slightly evolved context informed by the given state."""
        new_temporal_depth = self.temporal_depth + 0.1
        sf_new = self.spatial_field.copy()
        new_rel = self.relational_web.copy()
        if state.pattern_signature not in new_rel:
            new_rel[state.pattern_signature] = {"coherence": state.coherence_factor}

        # Domain tracking integration (optional)
        if self.domain_tracker and self.active_domain:
            await self._track_domain_evolution(state, sf_new)

        return Context(
            temporal_depth=new_temporal_depth,
            spatial_field=sf_new,
            relational_web=new_rel,
            quantum_signature=(
                f"{self.quantum_signature}:{state.pattern_signature}"
                if self.quantum_signature
                else state.pattern_signature
            ),
            domain_tracker=self.domain_tracker,
            active_domain=self.active_domain,
        )

    async def _track_domain_evolution(self, state: EssentialState, spatial_field: dict[str, Any]) -> None:
        """Track domain evolution during context evolution."""
        if not self.domain_tracker or not self.active_domain:
            return

        # Extract patterns from state
        patterns = []
        if "patterns" in state.quantum_state:
            patterns = state.quantum_state["patterns"]
        elif isinstance(state.quantum_state, dict):
            # Try to infer patterns from quantum state structure
            patterns = [k for k in state.quantum_state.keys() if isinstance(k, str)]

        # Extract metrics from spatial field or quantum state
        metrics = spatial_field.get("domain_metrics", {})
        if not metrics and "domain_metrics" in state.quantum_state:
            metrics = state.quantum_state["domain_metrics"]

        # Extract structural changes
        structural_changes = spatial_field.get("structural_changes", {})
        if not structural_changes and "structural_changes" in state.quantum_state:
            structural_changes = state.quantum_state["structural_changes"]

        # Track domain changes - handle TechnologyDomainTracker specially
        if isinstance(self.domain_tracker, TechnologyDomainTracker):
            # Use technology-specific tracking
            if metrics:
                self.domain_tracker.track_technology_metrics(
                    platform_adoption=metrics.get("platform_adoption", 0.0),
                    infrastructure_capability=metrics.get("infrastructure_capability", 0.0),
                    innovation_index=metrics.get("innovation_index", 0.0),
                    patterns=patterns,
                    structural_changes=structural_changes if structural_changes else None,
                )
        elif hasattr(self.domain_tracker, "track_domain"):
            # Use general domain tracking
            self.domain_tracker.track_domain(
                domain=self.active_domain,
                metrics=metrics,
                patterns=patterns,
                structural_changes=structural_changes if structural_changes else None,
            )

    def enable_domain_tracking(self, domain: str, tracker_type: str = "general") -> Context:
        """Enable domain-specific tracking for this context.

        Args:
            domain: Domain name (e.g., "technology", "job_market", "healthcare")
            tracker_type: Type of tracker ("general" or "technology")

        Returns:
            New Context with domain tracking enabled
        """
        if DomainTracker is None:
            # Domain tracking not available
            return self

        if tracker_type == "technology" and TechnologyDomainTracker:
            tracker = TechnologyDomainTracker()
        else:
            tracker = DomainTracker() if DomainTracker else None

        return Context(
            temporal_depth=self.temporal_depth,
            spatial_field=self.spatial_field.copy(),
            relational_web=self.relational_web.copy(),
            quantum_signature=self.quantum_signature,
            domain_tracker=tracker,
            active_domain=domain,
        )

    def get_domain_evolution(self) -> Any | None:
        """Get domain evolution data if domain tracking is enabled."""
        if not self.domain_tracker or not self.active_domain:
            return None

        # Handle TechnologyDomainTracker specially
        if isinstance(self.domain_tracker, TechnologyDomainTracker):
            return self.domain_tracker.get_technology_evolution()

        # Use general domain tracking
        if hasattr(self.domain_tracker, "get_domain_evolution"):
            return self.domain_tracker.get_domain_evolution(self.active_domain)

        return None

    def detect_emerging_structures(self) -> list[dict[str, Any]]:
        """Detect emerging structures in the active domain."""
        if not self.domain_tracker or not self.active_domain:
            return []

        # Handle TechnologyDomainTracker specially
        if isinstance(self.domain_tracker, TechnologyDomainTracker):
            return self.domain_tracker.detect_technology_shifts()

        # Use general domain tracking
        if hasattr(self.domain_tracker, "detect_emerging_structures"):
            return self.domain_tracker.detect_emerging_structures(self.active_domain)

        return []


# Late import to avoid circular dependency
from grid.essence.core_state import EssentialState  # noqa: E402
