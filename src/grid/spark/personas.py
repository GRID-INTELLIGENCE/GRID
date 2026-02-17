"""
Spark Personas - Morphable capability adapters.

Each persona wraps existing GRID components:
- Navigator: territory_map.py
- Resonance: activity_resonance.py
- Agentic: agentic_system.py (skills)
- Reasoning: reasoning_orchestrator.py
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class Persona(ABC):
    """Base class for Spark personas."""

    name: str = "base"
    description: str = "Abstract base persona"

    @abstractmethod
    def execute(self, request: str, context: dict[str, Any] | None = None) -> Any:
        """Execute a request.

        Args:
            request: Natural language request
            context: Optional additional context

        Returns:
            Execution result
        """
        pass


class NavigatorPersona(Persona):
    """
    Navigator Persona - Path resolution and import diagnostics.

    Uses: application/canvas/territory_map.py
    """

    name = "navigator"
    description = "Path resolution and import diagnostics"

    def __init__(self) -> None:
        self._map: Any | None = None

    def _get_map(self) -> Any:
        """Lazy load territory map."""
        if self._map is None:
            try:
                import importlib

                canvas_module = importlib.import_module("application.canvas.territory_map")
                self._map = canvas_module.get_grid_map()
            except ImportError:
                logger.warning("Territory map not available")
                self._map = None
        return self._map

    def execute(self, request: str, context: dict[str, Any] | None = None) -> Any:
        """Execute navigation request."""
        grid_map = self._get_map()

        if grid_map is None:
            return {"error": "Territory map not available"}

        request_lower = request.lower()

        # Diagnose import errors
        if "import" in request_lower or "diagnose" in request_lower:
            return self.diagnose(request)

        # Get zone map
        if "map" in request_lower or "zone" in request_lower:
            return grid_map.get_zone_map()

        # Get import guide
        if "guide" in request_lower or "pattern" in request_lower:
            return grid_map.get_import_guide()

        # Default: return zone map
        return grid_map.get_zone_map()

    def diagnose(self, error_message: str) -> dict[str, Any]:
        """Diagnose an import error."""
        grid_map = self._get_map()
        if grid_map is None:
            return {"error": "Territory map not available"}

        suggestion = grid_map.diagnose_import_error(error_message)
        return {
            "error": error_message,
            "suggestion": suggestion,
            "zones": list(grid_map.get_zone_map().keys()),
        }


class ResonancePersona(Persona):
    """
    Resonance Persona - Activity feedback with ADSR envelope.

    Uses: application/resonance/activity_resonance.py
    """

    name = "resonance"
    description = "Activity feedback with ADSR envelope"

    def __init__(self) -> None:
        self._resonance: Any | None = None

    def _get_resonance(self) -> Any:
        """Lazy load activity resonance."""
        if self._resonance is None:
            try:
                import importlib

                resonance_module = importlib.import_module("application.resonance.activity_resonance")
                self._resonance = resonance_module.ActivityResonance()
            except ImportError:
                logger.warning("Activity resonance not available")
                self._resonance = None
        return self._resonance

    def execute(self, request: str, context: dict[str, Any] | None = None) -> Any:
        """Execute resonance request."""
        resonance = self._get_resonance()

        if resonance is None:
            return {"error": "Activity resonance not available"}

        # Determine activity type
        activity_type = "general"
        if context and "type" in context:
            activity_type = context["type"]
        elif "code" in request.lower():
            activity_type = "code"
        elif "config" in request.lower():
            activity_type = "config"

        # Process activity
        feedback = resonance.process_activity(
            activity_type=activity_type,
            query=request,
            context=context,
        )

        return {
            "state": feedback.state.value,
            "message": feedback.message,
            "urgency": feedback.urgency,
            "envelope": (
                {
                    "phase": feedback.envelope.phase.value if feedback.envelope else None,
                    "amplitude": feedback.envelope.amplitude if feedback.envelope else 0,
                }
                if feedback.envelope
                else None
            ),
        }


class AgenticPersona(Persona):
    """
    Agentic Persona - Skill execution and retrieval.

    Uses: grid/agentic/skill_retriever.py
    """

    name = "agentic"
    description = "Skill execution and retrieval"

    def __init__(self) -> None:
        self._retriever: Any | None = None

    def _get_retriever(self) -> Any:
        """Lazy load skill retriever."""
        if self._retriever is None:
            try:
                from grid.agentic.skill_retriever import SkillRetriever

                # Load skill path from environment variable or use default in user home
                skill_path_env = os.environ.get("GRID_SKILL_KNOWLEDGE_PATH")
                if skill_path_env:
                    skill_path = Path(skill_path_env)
                else:
                    # Default to user's home directory (cross-platform)
                    skill_path = Path.home() / ".gemini" / "antigravity" / "knowledge"

                if skill_path.exists():
                    self._retriever = SkillRetriever(skill_path)
                else:
                    logger.debug(
                        f"Skill knowledge path not found: {skill_path}. "
                        "Set GRID_SKILL_KNOWLEDGE_PATH environment variable to configure."
                    )
            except ImportError:
                logger.warning("Skill retriever not available")
                self._retriever = None
        return self._retriever

    def execute(self, request: str, context: dict[str, Any] | None = None) -> Any:
        """Execute agentic request."""
        retriever = self._get_retriever()

        if retriever is None:
            return {"skills": [], "message": "Skill retriever not available"}

        # Extract keywords from request
        keywords = request.lower().split()
        # Filter common words
        stop_words = {"find", "get", "the", "a", "an", "for", "to", "with", "skills"}
        keywords = [w for w in keywords if w not in stop_words and len(w) > 2]

        # Find relevant skills
        skills = retriever.find_relevant_skills(keywords=keywords, limit=5)

        return {
            "request": request,
            "keywords": keywords,
            "skills": [
                {
                    "id": s["id"],
                    "score": s["score"],
                    "title": s["metadata"].get("title", ""),
                }
                for s in skills
            ],
            "count": len(skills),
        }


class ReasoningPersona(Persona):
    """
    Reasoning Persona - Multi-source reasoning (web + KG + LLM).

    Uses: grid/knowledge/reasoning_orchestrator.py
    """

    name = "reasoning"
    description = "Multi-source reasoning (web + KG + LLM)"

    def __init__(self) -> None:
        self._orchestrator: Any | None = None

    def _get_orchestrator(self) -> Any:
        """Lazy load reasoning orchestrator."""
        if self._orchestrator is None:
            try:
                from grid.knowledge.reasoning_orchestrator import ReasoningMode, ReasoningOrchestrator

                self._orchestrator = ReasoningOrchestrator(
                    mode=ReasoningMode.ADAPTIVE,
                    enable_web=False,  # Disable web for now (no search API)
                    enable_kg=True,
                    enable_llm=True,
                )
            except ImportError:
                logger.warning("Reasoning orchestrator not available")
                self._orchestrator = None
        return self._orchestrator

    def execute(self, request: str, context: dict[str, Any] | None = None) -> Any:
        """Execute reasoning request."""
        import asyncio

        orchestrator = self._get_orchestrator()

        if orchestrator is None:
            return {"error": "Reasoning orchestrator not available"}

        # Run async reasoning
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(orchestrator.reason(request, context))
            loop.close()
            return result
        except Exception as e:
            return {"error": str(e), "request": request}


class StaircasePersona(Persona):
    """
    Staircase Persona - Autonomous routing with literary intelligence.

    Uses: grid/spark/staircase.py (Hogwarts-inspired routing)
    """

    name = "staircase"
    description = "Autonomous routing inspired by Hogwarts moving staircases"

    def __init__(self) -> None:
        self._stairs: Any | None = None

    def _get_stairs(self) -> Any:
        """Lazy load staircase system."""
        if self._stairs is None:
            try:
                from grid.spark.staircase import create_hogwarts_topology

                self._stairs = create_hogwarts_topology()
            except ImportError:
                logger.warning("Staircase module not available")
                self._stairs = None
        return self._stairs

    def execute(self, request: str, context: dict[str, Any] | None = None) -> Any:
        """Execute routing request."""
        stairs = self._get_stairs()

        if stairs is None:
            return {"error": "Staircase system not available"}

        request_lower = request.lower()

        # Find route
        if "route" in request_lower or "path" in request_lower or "find" in request_lower:
            # Extract origin/destination from context or use defaults
            origin = context.get("origin", "great_hall") if context else "great_hall"
            dest = context.get("destination", "library") if context else "library"
            route = stairs.find_route(origin, dest)
            return {
                "route": route,
                "origin": origin,
                "destination": dest,
                "found": route is not None,
            }

        # Cycle (autonomous movement)
        if "cycle" in request_lower or "move" in request_lower:
            moved = stairs.cycle()
            return {
                "moved_count": len(moved),
                "moved_ids": moved,
                "message": f"{len(moved)} staircases moved autonomously",
            }

        # Health report
        if "health" in request_lower or "status" in request_lower:
            return stairs.get_health_report()

        # Default: show reference card
        from grid.spark.staircase import REFERENCE_CARD

        return {"reference": REFERENCE_CARD, "staircases": len(stairs.staircases)}


__all__ = [
    "Persona",
    "NavigatorPersona",
    "ResonancePersona",
    "AgenticPersona",
    "ReasoningPersona",
    "StaircasePersona",
]
