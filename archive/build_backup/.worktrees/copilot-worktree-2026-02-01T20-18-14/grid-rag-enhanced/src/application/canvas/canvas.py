"""Main Canvas - User-centric routing interface orchestrator."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .integration_state import IntegrationStateManager
from .interfaces import InterfaceBridge
from .relevance import RelevanceEngine
from .resonance_adapter import ResonanceAdapter
from .router import UnifiedRouter
from .schemas import CanvasRoutingResult
from .wheel import EnvironmentWheel, WheelZone

logger = logging.getLogger(__name__)


class Canvas:
    """
    Main Canvas - User-centric routing interface.

    Orchestrates comprehensive routing through GRID's multi-directory
    structure with similarity matching, metrics-driven relevance,
    motivational adaptation, and integration state management.
    """

    def __init__(
        self,
        workspace_root: Path,
        integration_json_path: Path | None = None,
    ):
        """Initialize canvas.

        Args:
            workspace_root: Root path of the workspace
            integration_json_path: Optional path to integration.json
        """
        self.workspace_root = Path(workspace_root)
        self.router = UnifiedRouter(self.workspace_root)
        self.relevance_engine = RelevanceEngine()
        self.interface_bridge = InterfaceBridge()
        self.resonance_adapter = ResonanceAdapter()

        # Default integration.json path
        if integration_json_path is None:
            integration_json_path = (
                self.workspace_root / ".windsurf" / "structural-intelligence" / "state" / "integration.json"
            )

        self.integration_state = IntegrationStateManager(integration_json_path)

        # Initialize environment wheel for visual representation
        self.wheel = EnvironmentWheel(rotation_speed=0.05, auto_rotate=True)

        # Track routing as agent movement
        self._agent_tracking: dict[str, dict[str, Any]] = {}

    async def route(
        self,
        query: str,
        context: dict[str, Any] | None = None,
        max_results: int = 5,
        enable_motivation: bool = True,
    ) -> CanvasRoutingResult:
        """Comprehensive routing with similarity, relevance, and motivation.

        Args:
            query: Query string to route
            context: Optional context dictionary
            max_results: Maximum number of results
            enable_motivation: Whether to enable motivational adaptation

        Returns:
            CanvasRoutingResult with comprehensive routing information
        """
        # 1. Route query using similarity matching
        route_result = await self.router.route_query(
            query=query,
            context=context,
            max_results=max_results,
        )

        # 2. Calculate relevance scores for each route
        relevance_scores = []
        for route in route_result.routes:
            relevance = self.relevance_engine.calculate_relevance(
                route=route.path,
                query=query,
                context=context,
            )

            # Update integration alignment from state manager
            integration_alignment = self.integration_state.check_integration_alignment(route.path)
            relevance.metrics.integration_alignment = integration_alignment

            # Recalculate final score with updated alignment
            relevance.final_score = (
                relevance.metrics.semantic_similarity * 0.35
                + (1.0 - relevance.metrics.path_complexity) * 0.15
                + relevance.metrics.context_match * 0.25
                + relevance.metrics.usage_frequency * 0.15
                + integration_alignment * 0.10
            )

            relevance_scores.append(relevance)

            # Record usage
            self.relevance_engine.record_usage(route.path)

        # 3. Apply motivational adaptation (if enabled)
        motivated_routing = None
        if enable_motivation and route_result.routes:
            try:
                motivated_routing = await self.resonance_adapter.motivate_routing(
                    query=query,
                    routes=route_result.routes,
                    context=context,
                )
            except Exception as e:
                logger.warning(f"Motivational routing failed: {e}")

        # 4. Update integration state
        if route_result.routes:
            primary_route = route_result.routes[0].path
            await self.integration_state.update_state(
                updates={
                    "last_routing_query": query,
                    "last_routing_timestamp": datetime.now().isoformat(),
                    "route_count": len(route_result.routes),
                },
                route_path=primary_route,
            )

        # 5. Calculate overall integration alignment
        primary_route_path = route_result.routes[0].path if route_result.routes else None
        integration_alignment = self.integration_state.check_integration_alignment(primary_route_path)

        # 6. Track routing movement on the wheel
        self._track_routing_movement(query, route_result.routes, context)

        # 7. Return comprehensive result
        return CanvasRoutingResult(
            query=query,
            routes=route_result.routes,
            relevance_scores=relevance_scores,
            motivated_routing=motivated_routing,
            confidence=route_result.confidence,
            integration_alignment=integration_alignment,
        )

    def get_integration_state(self) -> dict[str, Any]:
        """Get current integration state.

        Returns:
            Integration state dictionary
        """
        return self.integration_state.get_state()

    def _track_routing_movement(
        self,
        query: str,
        routes: list[Any],
        context: dict[str, Any] | None,
    ) -> None:
        """Track routing as agent movement on the wheel.

        Args:
            query: Routing query
            routes: List of routes found
            context: Optional context
        """

        # Create or get routing agent
        routing_id = f"routing_{hash(query) % 10000}"

        # Determine primary zone from routes
        primary_zone = WheelZone.CANVAS
        if routes:
            route_path = str(routes[0].path).lower()
            if "grid/agentic" in route_path:
                primary_zone = WheelZone.AGENTIC
            elif "grid/interfaces" in route_path:
                primary_zone = WheelZone.INTERFACES
            elif "grid/" in route_path:
                primary_zone = WheelZone.CORE
            elif "light_of_the_seven" in route_path or "cognitive" in route_path:
                primary_zone = WheelZone.COGNITIVE
            elif "application/" in route_path:
                primary_zone = WheelZone.APPLICATION
            elif "tools/" in route_path:
                primary_zone = WheelZone.TOOLS
            elif "arena" in route_path or "the_chase" in route_path:
                primary_zone = WheelZone.ARENA

        # Add or move agent on wheel
        if routing_id in self.wheel.state.agents:
            self.wheel.move_agent(routing_id, primary_zone)
        else:
            self.wheel.add_agent(
                agent_id=routing_id,
                agent_name=f"Route: {query[:30]}",
                zone=primary_zone,
                metadata={
                    "query": query,
                    "route_count": len(routes),
                    "context": context,
                },
            )

        # Track in routing history
        self._agent_tracking[routing_id] = {
            "query": query,
            "zone": primary_zone.value,
            "route_count": len(routes),
            "timestamp": datetime.now().isoformat(),
        }

    def get_wheel_visualization(self, format: str = "json") -> Any:
        """Get environment wheel visualization.

        Args:
            format: Output format - "json", "text", or "state"

        Returns:
            Visualization data in requested format
        """
        if format == "text":
            return self.wheel.get_text_visualization()
        elif format == "state":
            return self.wheel.state
        else:
            return self.wheel.get_visualization()

    def spin_wheel(self, delta_time: float | None = None) -> Any:
        """Spin the environment wheel.

        Args:
            delta_time: Optional delta time for update

        Returns:
            Updated wheel state
        """
        return self.wheel.spin(delta_time)
