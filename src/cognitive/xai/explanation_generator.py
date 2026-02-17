from typing import Any


class ExplanationGenerator:
    """
    Generates human-readable explanations for cognitive engine decisions.
    Provides transparency for adaptive responses and routing decisions.
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
