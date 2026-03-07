from __future__ import annotations

from typing import Any


class ExplanationGenerator:
    """
    Generates human-readable explanations for cognitive engine decisions.
    Provides transparency for adaptive responses, routing decisions,
    cognitive state transitions, and temporal reasoning outcomes.
    """

    def explain_adaptive_response(self, adaptations: list[dict[str, Any]]) -> str:
        """
        Generate explanation for adaptive response decisions.

        Args:
            adaptations: List of adaptation dictionaries

        Returns:
            Human-readable explanation
        """
        if not adaptations:
            return "No adaptations applied. Standard response provided."

        explanations = []
        for adapt in adaptations:
            adapt_type = adapt.get("type")
            if adapt_type == "simplify":
                reason = adapt.get("description", "due to high cognitive load")
                explanations.append(f"Simplified response {reason}")
            elif adapt_type == "concise":
                explanations.append("Provided concise response for fast processing mode")
            elif adapt_type == "expand":
                explanations.append("Provided detailed explanation for deliberate processing")
            elif adapt_type == "scaffold":
                expertise = adapt.get("parameters", {}).get("expertise", "novice")
                explanations.append(f"Added learning scaffolding for {expertise} user")
            elif adapt_type == "temporal_compression":
                factor = adapt.get("factor", 0.7)
                explanations.append(f"Compressed time-sensitive content by {factor}x")
            elif adapt_type == "temporal_expansion":
                factor = adapt.get("factor", 1.3)
                explanations.append(f"Expanded time-insensitive content by {factor}x")

        return ". ".join(explanations)

    def explain_routing_decision(self, route_decision: dict[str, Any]) -> str:
        """
        Generate explanation for routing decisions.

        Args:
            route_decision: Routing decision dictionary

        Returns:
            Human-readable explanation
        """
        route_type = route_decision.get("route_type", "standard")
        priority = route_decision.get("priority", "medium")
        coffee_mode = route_decision.get("coffee_mode", {}).get("name", "Balanced")

        base = (
            f"Routing decision: {route_type} processing with {priority} priority. "
            f"Using {coffee_mode} cognitive mode for optimal information processing."
        )

        adaptations = route_decision.get("temporal_adaptations", [])
        if "time_compression" in adaptations:
            base += " Applied time compression for urgent content."
        if "time_expansion" in adaptations:
            base += " Applied time expansion for comprehensive analysis."

        return base

    def explain_function_call(
        self, function_name: str, args: tuple[Any, ...], kwargs: dict[str, Any], result: Any
    ) -> str:
        """
        Generate explanation for function call execution.

        Args:
            function_name: Called function name
            args: Positional arguments
            kwargs: Keyword arguments
            result: Function result

        Returns:
            Human-readable explanation
        """
        arg_summary = ", ".join([str(a) for a in args])
        kwarg_summary = ", ".join([f"{k}={v}" for k, v in kwargs.items()])

        return (
            f"Executed function '{function_name}' with arguments ({arg_summary}) "
            f"and keyword arguments ({kwarg_summary}). "
            f"Returned result: {str(result)[:100]}"
        )

    def explain_cognitive_state(self, state: dict[str, Any]) -> str:
        """Generate explanation of the current cognitive state.

        Args:
            state: Cognitive state dictionary (from CognitiveState.model_dump()).

        Returns:
            Human-readable explanation of why the system is in this state.
        """
        load = state.get("estimated_load", 0.0)
        mode = state.get("processing_mode", "System_1")
        alignment = state.get("mental_model_alignment", 1.0)
        mismatches = state.get("model_mismatches", [])

        parts: list[str] = []

        # Load explanation
        if load > 8.0:
            parts.append(f"Cognitive load is critical ({load:.1f}/10) — task overload detected")
        elif load > 6.0:
            parts.append(f"Cognitive load is high ({load:.1f}/10) — scaffolding recommended")
        elif load > 3.0:
            parts.append(f"Cognitive load is moderate ({load:.1f}/10) — normal processing")
        else:
            parts.append(f"Cognitive load is low ({load:.1f}/10) — user is comfortable")

        # Processing mode explanation
        if mode == "System_2":
            parts.append("Operating in System 2 (deliberate, analytical) mode")
        else:
            parts.append("Operating in System 1 (fast, intuitive) mode")

        # Mental model alignment
        if alignment < 0.5:
            parts.append(f"Mental model alignment is low ({alignment:.0%})")
            if mismatches:
                parts.append(f"Issues: {'; '.join(mismatches)}")
        elif alignment < 0.7:
            parts.append(f"Mental model alignment is moderate ({alignment:.0%})")

        return ". ".join(parts)

    def explain_temporal_reasoning(self, reasoning_metrics: dict[str, Any]) -> str:
        """Generate explanation of temporal reasoning outcomes.

        Args:
            reasoning_metrics: Metrics from TemporalReasoning.get_performance_metrics().

        Returns:
            Human-readable explanation of temporal reasoning decisions.
        """
        facts = reasoning_metrics.get("temporal_facts_processed", 0)
        paths = reasoning_metrics.get("temporal_paths_constructed", 0)
        xrefs = reasoning_metrics.get("cross_references_generated", 0)
        confidence = reasoning_metrics.get("decision_confidence", 0.0)
        consistency = reasoning_metrics.get("temporal_consistency_score", 1.0)

        parts: list[str] = []

        if facts == 0:
            return "No temporal facts available for reasoning."

        parts.append(f"Analyzed {facts} temporal facts across {paths} causal paths")

        if xrefs > 0:
            parts.append(f"{xrefs} cross-domain references found")

        if confidence >= 0.7:
            parts.append(f"High decision confidence ({confidence:.0%})")
        elif confidence >= 0.4:
            parts.append(f"Moderate decision confidence ({confidence:.0%}) — additional evidence may help")
        else:
            parts.append(f"Low decision confidence ({confidence:.0%}) — insufficient temporal evidence")

        if consistency < 0.8:
            parts.append(f"Temporal consistency is degraded ({consistency:.0%}) — conflicting timelines detected")

        return ". ".join(parts)

    def explain_pattern_detection(self, patterns: dict[str, Any]) -> str:
        """Generate explanation of detected cognition patterns.

        Args:
            patterns: Pattern detection results keyed by pattern name.

        Returns:
            Human-readable explanation of which patterns were detected and why.
        """
        if not patterns:
            return "No cognition patterns detected in recent interactions."

        detected = []
        for pattern_name, result in patterns.items():
            if isinstance(result, dict) and result.get("detected", False):
                confidence = result.get("confidence", 0.0)
                detected.append(f"{pattern_name} ({confidence:.0%} confidence)")

        if not detected:
            return "Pattern analysis complete. No significant patterns detected."

        return f"Detected cognition patterns: {', '.join(detected)}"
