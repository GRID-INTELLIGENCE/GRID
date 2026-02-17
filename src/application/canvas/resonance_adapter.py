"""Resonance Adapter - Adapts resonance patterns for motivational canvas routing."""

from __future__ import annotations

import logging
from typing import Any

from application.resonance.activity_resonance import ActivityResonance
from application.resonance.adsr_envelope import ADSREnvelope
from application.resonance.path_visualizer import PathVisualizer

from .schemas import MotivatedRoute, MotivatedRouting, ScoredRoute

logger = logging.getLogger(__name__)


class ResonanceAdapter:
    """Adapts resonance patterns for motivational canvas routing."""

    def __init__(
        self,
        activity_resonance: ActivityResonance | None = None,
    ):
        """Initialize resonance adapter.

        Args:
            activity_resonance: Optional ActivityResonance instance
        """
        self.activity_resonance = activity_resonance or ActivityResonance()
        self._envelope = ADSREnvelope()
        self._path_visualizer = PathVisualizer()

    async def motivate_routing(
        self,
        query: str,
        routes: list[ScoredRoute],
        context: dict[str, Any] | None = None,
    ) -> MotivatedRouting:
        """Apply motivational adaptation from resonance patterns.

        Args:
            query: Query string
            routes: List of scored routes
            context: Optional context

        Returns:
            MotivatedRouting with envelope and path triage
        """
        # Trigger envelope for motivational feedback
        self._envelope.trigger()

        # Get path triage (adapts from resonance system)
        enhanced_context = context.copy() if context else {}
        enhanced_context["routes"] = [str(r.path) for r in routes]

        path_triage = self._path_visualizer.triage_paths(
            goal=query,
            context=enhanced_context,
            max_options=min(len(routes), 4),
        )

        # Map routes to path options
        motivated_routes: list[MotivatedRoute] = []
        for i, route in enumerate(routes):
            path_option = path_triage.options[i].__dict__ if i < len(path_triage.options) else None

            motivated_routes.append(
                MotivatedRoute(
                    route=route,
                    path_option=path_option,
                    envelope_amplitude=self._envelope.get_metrics().amplitude,
                    motivation_score=self._calculate_motivation_score(route, path_option),
                )
            )

        # Update envelope
        envelope_metrics = self._envelope.update()
        envelope_dict = {
            "phase": envelope_metrics.phase.value,
            "amplitude": envelope_metrics.amplitude,
            "velocity": envelope_metrics.velocity,
            "time_in_phase": envelope_metrics.time_in_phase,
        }

        # Path triage dict
        path_triage_dict = {
            "goal": path_triage.goal,
            "total_options": path_triage.total_options,
            "glimpse_summary": path_triage.glimpse_summary,
            "recommended": (path_triage.recommended.__dict__ if path_triage.recommended else None),
        }

        return MotivatedRouting(
            routes=motivated_routes,
            envelope_metrics=envelope_dict,
            path_triage=path_triage_dict,
            urgency=self._calculate_urgency(envelope_metrics, path_triage),
        )

    def _calculate_motivation_score(self, route: ScoredRoute, path_option: dict[str, Any] | None) -> float:
        """Calculate motivation score combining route relevance and path appeal.

        Args:
            route: Scored route
            path_option: Optional path option from triage

        Returns:
            Motivation score (0.0 to 1.0)
        """
        base_score = route.final_score * 0.6

        if path_option:
            recommendation_score = path_option.get("recommendation_score", 0.5)
            base_score += recommendation_score * 0.4

        return min(1.0, base_score)

    def _calculate_urgency(
        self,
        envelope_metrics: Any,
        path_triage: Any,
    ) -> float:
        """Calculate urgency from envelope and path triage.

        Args:
            envelope_metrics: ADSR envelope metrics
            path_triage: Path triage result

        Returns:
            Urgency score (0.0 to 1.0)
        """
        # Urgency from envelope amplitude
        envelope_urgency = envelope_metrics.amplitude * 0.5

        # Urgency from path complexity
        path_urgency = 0.0
        if path_triage.recommended:
            complexity = path_triage.recommended.complexity.value
            if complexity == "very_complex":
                path_urgency = 0.8
            elif complexity == "complex":
                path_urgency = 0.6
            elif complexity == "moderate":
                path_urgency = 0.4
            else:
                path_urgency = 0.2

        return min(1.0, envelope_urgency + path_urgency * 0.5)

    def complete_routing(self) -> None:
        """Complete routing and trigger envelope release."""
        self._envelope.release()
