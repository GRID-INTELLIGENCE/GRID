"""GRID Cognitive Engine Integration Bridge.

Bridges VECTION context emergence with GRID's cognitive engine,
providing enriched cognitive state with context establishment,
emergent patterns, and cognitive velocity tracking.

This is the key integration point that fills the gap:
context_establishment is no longer null.

Usage:
    from vection.interfaces.grid_bridge import GridVectionBridge

    bridge = GridVectionBridge()
    enriched_state = await bridge.enhance_cognitive_state(
        cognitive_state, session_id, event
    )
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@runtime_checkable
class CognitiveStateProtocol(Protocol):
    """Protocol for cognitive state objects."""

    estimated_load: float
    processing_mode: str
    context: dict[str, Any]


@dataclass
class EnrichedCognitiveState:
    """Cognitive state enriched with VECTION context.

    This fills the gap: context_establishment is no longer null.
    """

    # Original cognitive state fields
    estimated_load: float
    processing_mode: str
    mode_confidence: float
    mental_model_alignment: float
    context: dict[str, Any] = field(default_factory=dict)

    # VECTION enrichments (the gap fillers)
    context_establishment: dict[str, Any] | None = None
    emergent_patterns: list[dict[str, Any]] = field(default_factory=list)
    cognitive_velocity: dict[str, Any] | None = None
    session_anchors: list[dict[str, Any]] = field(default_factory=list)
    projections: list[str] = field(default_factory=list)

    # Metadata
    vection_session_id: str | None = None
    enriched_at: datetime = field(default_factory=datetime.now)

    @property
    def has_context_establishment(self) -> bool:
        """Check if context establishment is present (not null)."""
        return self.context_establishment is not None

    @property
    def has_velocity(self) -> bool:
        """Check if cognitive velocity is tracked."""
        return self.cognitive_velocity is not None

    @property
    def pattern_count(self) -> int:
        """Get number of emergent patterns."""
        return len(self.emergent_patterns)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "estimated_load": self.estimated_load,
            "processing_mode": self.processing_mode,
            "mode_confidence": round(self.mode_confidence, 3),
            "mental_model_alignment": round(self.mental_model_alignment, 3),
            "context": self.context,
            "context_establishment": self.context_establishment,
            "emergent_patterns": self.emergent_patterns,
            "cognitive_velocity": self.cognitive_velocity,
            "session_anchors": self.session_anchors,
            "projections": self.projections,
            "vection_session_id": self.vection_session_id,
            "enriched_at": self.enriched_at.isoformat(),
            "has_context_establishment": self.has_context_establishment,
            "has_velocity": self.has_velocity,
            "pattern_count": self.pattern_count,
        }


class GridVectionBridge:
    """Bridge between GRID cognitive engine and VECTION.

    Integrates VECTION's context emergence capabilities with GRID's
    cognitive state tracking, providing enriched cognitive state with:
    - Context establishment (no longer null)
    - Emergent patterns from request streams
    - Cognitive velocity tracking
    - Future context projections

    Usage:
        bridge = GridVectionBridge()
        enriched = await bridge.enhance_cognitive_state(state, session_id, event)
        hints = bridge.get_routing_hints(session_id)
    """

    def __init__(self, auto_start_workers: bool = False) -> None:
        """Initialize the GRID-VECTION bridge.

        Args:
            auto_start_workers: Whether to auto-start background workers.
        """
        self._vection_engine: Any = None
        self._workers_started = False
        self._auto_start_workers = auto_start_workers
        self._session_states: dict[str, EnrichedCognitiveState] = {}

        logger.info("GridVectionBridge initialized")

    async def _ensure_vection(self) -> Any:
        """Ensure VECTION engine is available."""
        if self._vection_engine is None:
            from vection.core.engine import Vection

            self._vection_engine = Vection.get_instance()
        return self._vection_engine

    async def enhance_cognitive_state(
        self,
        cognitive_state: Any,
        session_id: str,
        event: Any,
    ) -> EnrichedCognitiveState:
        """Enhance cognitive state with VECTION context.

        This is the primary integration point. It takes a GRID cognitive
        state and enriches it with VECTION context emergence data.

        Args:
            cognitive_state: GRID CognitiveState instance.
            session_id: Unique session identifier.
            event: The interaction event being processed.

        Returns:
            EnrichedCognitiveState with context establishment filled in.
        """
        engine = await self._ensure_vection()

        # Establish VECTION context
        vection_context = await engine.establish(session_id, event)

        # Query for emergent patterns
        query = self._extract_query(event)
        emergent_signals = await engine.query_emergent(session_id, query) if query else []

        # Get projections
        projections = await engine.project(session_id, steps=3)

        # Build enriched state
        enriched = self._build_enriched_state(
            cognitive_state=cognitive_state,
            vection_context=vection_context,
            emergent_signals=emergent_signals,
            projections=projections,
            session_id=session_id,
        )

        # Cache for later access
        self._session_states[session_id] = enriched

        logger.debug(
            f"Enhanced cognitive state for {session_id}: "
            f"context_established={enriched.has_context_establishment}, "
            f"patterns={enriched.pattern_count}, "
            f"has_velocity={enriched.has_velocity}"
        )

        return enriched

    async def get_context_only(
        self,
        session_id: str,
        event: Any,
    ) -> dict[str, Any]:
        """Get VECTION context without full cognitive state.

        Useful when you only need context establishment without
        the full cognitive state enrichment.

        Args:
            session_id: Session identifier.
            event: Event to process.

        Returns:
            Dictionary with context establishment data.
        """
        engine = await self._ensure_vection()
        vection_context = await engine.establish(session_id, event)
        return vection_context.to_dict()

    def get_routing_hints(self, session_id: str) -> dict[str, Any]:
        """Get routing hints based on VECTION projections.

        Useful for predictive routing decisions.

        Args:
            session_id: Session identifier.

        Returns:
            Dictionary with routing hints.
        """
        enriched = self._session_states.get(session_id)
        if enriched is None:
            return {"hint_available": False}

        hints: dict[str, Any] = {
            "hint_available": True,
            "session_id": session_id,
        }

        # Add velocity-based hints
        if enriched.cognitive_velocity:
            velocity = enriched.cognitive_velocity
            direction = velocity.get("direction", "unknown")

            # Map directions to service hints
            direction_hints = {
                "exploration": {"preload": "knowledge_retrieval", "priority": "breadth"},
                "investigation": {"preload": "analytics", "priority": "depth"},
                "execution": {"preload": "task_engine", "priority": "speed"},
                "synthesis": {"preload": "integration", "priority": "quality"},
                "reflection": {"preload": "summary", "priority": "completeness"},
            }

            hint = direction_hints.get(direction, {})
            hints.update(hint)
            hints["cognitive_direction"] = direction
            hints["momentum"] = velocity.get("momentum", 0.0)

        # Add projection-based hints
        if enriched.projections:
            hints["projected_needs"] = enriched.projections[:3]

            # Check for specific patterns in projections
            if any("ml" in p.lower() or "heavy" in p.lower() for p in enriched.projections):
                hints["resource_hint"] = "high_compute"
            if any("retrieval" in p.lower() or "knowledge" in p.lower() for p in enriched.projections):
                hints["resource_hint"] = "knowledge_intensive"

        return hints

    async def get_emergent_for_query(
        self,
        session_id: str,
        query: str,
    ) -> list[dict[str, Any]]:
        """Query emergent patterns for a specific query.

        Args:
            session_id: Session identifier.
            query: Query string for pattern matching.

        Returns:
            List of matching emergent signal dictionaries.
        """
        engine = await self._ensure_vection()
        signals = await engine.query_emergent(session_id, query)
        return [s.to_dict() for s in signals]

    async def dissolve_session(self, session_id: str) -> bool:
        """Dissolve a session's VECTION context.

        Args:
            session_id: Session to dissolve.

        Returns:
            True if session was dissolved.
        """
        engine = await self._ensure_vection()
        result = await engine.dissolve(session_id)

        if session_id in self._session_states:
            del self._session_states[session_id]

        return result

    def get_stats(self) -> dict[str, Any]:
        """Get bridge statistics."""
        return {
            "cached_sessions": len(self._session_states),
            "workers_started": self._workers_started,
            "vection_initialized": self._vection_engine is not None,
        }

    # =========================================================================
    # Internal Methods
    # =========================================================================

    def _build_enriched_state(
        self,
        cognitive_state: Any,
        vection_context: Any,
        emergent_signals: list[Any],
        projections: list[str],
        session_id: str,
    ) -> EnrichedCognitiveState:
        """Build enriched cognitive state from components."""
        # Extract base cognitive state fields
        estimated_load = getattr(cognitive_state, "estimated_load", 0.5)
        processing_mode = getattr(cognitive_state, "processing_mode", "unknown")
        mode_confidence = getattr(cognitive_state, "mode_confidence", 0.5)
        mental_model_alignment = getattr(cognitive_state, "mental_model_alignment", 0.5)
        context = getattr(cognitive_state, "context", {})

        # Build context establishment (THE GAP FILLER)
        context_establishment = vection_context.to_dict() if vection_context else None

        # Build emergent patterns
        emergent_patterns = [s.to_dict() for s in emergent_signals if hasattr(s, "to_dict")]

        # Build cognitive velocity
        cognitive_velocity = None
        if vection_context and vection_context.has_velocity:
            velocity = vection_context.cognitive_velocity
            if hasattr(velocity, "to_dict"):
                cognitive_velocity = velocity.to_dict()

        # Build session anchors
        session_anchors = [anchor.to_dict() for anchor in (vection_context.get_dominant_anchors(limit=5) if vection_context else []) if hasattr(anchor, "to_dict")]

        return EnrichedCognitiveState(
            estimated_load=estimated_load,
            processing_mode=processing_mode,
            mode_confidence=mode_confidence,
            mental_model_alignment=mental_model_alignment,
            context=context if isinstance(context, dict) else {},
            context_establishment=context_establishment,
            emergent_patterns=emergent_patterns,
            cognitive_velocity=cognitive_velocity,
            session_anchors=session_anchors,
            projections=projections,
            vection_session_id=session_id,
        )

    def _extract_query(self, event: Any) -> str:
        """Extract query string from event for pattern matching."""
        if isinstance(event, dict):
            return event.get("query") or event.get("content") or event.get("action") or ""

        for attr in ("query", "content", "action", "type"):
            value = getattr(event, attr, None)
            if value:
                return str(value)

        return ""


# Module-level singleton
_bridge: GridVectionBridge | None = None


def get_bridge() -> GridVectionBridge:
    """Get the global GridVectionBridge instance.

    Returns:
        GridVectionBridge singleton.
    """
    global _bridge
    if _bridge is None:
        _bridge = GridVectionBridge()
    return _bridge


async def enhance_with_vection(
    cognitive_state: Any,
    session_id: str,
    event: Any,
) -> EnrichedCognitiveState:
    """Convenience function to enhance cognitive state with VECTION.

    Args:
        cognitive_state: GRID CognitiveState instance.
        session_id: Session identifier.
        event: Interaction event.

    Returns:
        EnrichedCognitiveState with context establishment.
    """
    bridge = get_bridge()
    return await bridge.enhance_cognitive_state(cognitive_state, session_id, event)
