from collections.abc import Callable
from typing import Any

from cognitive.temporal import with_temporal_context
from cognitive.xai.explanation_generator import ExplanationGenerator


class FunctionCallDispatcher:
    """
    Dispatches function calls with grid-specific context awareness.
    Integrates cognitive state, temporal context, and XAI explanations.
    """

    def __init__(self):
        self.function_registry: dict[str, Callable] = {}
        self.xai_generator = ExplanationGenerator()

    def register_function(self, name: str, func: Callable) -> None:
        """Register a function with the dispatcher."""
        self.function_registry[name] = func

    @with_temporal_context
    def dispatch(
        self,
        function_name: str,
        *args,
        cognitive_state: dict | None = None,
        temporal_context: dict | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Dispatch a function call with context awareness.

        Args:
            function_name: Name of registered function
            cognitive_state: Current cognitive state
            temporal_context: Temporal context information
            *args, **kwargs: Function arguments

        Returns:
            Result dictionary with output and metadata
        """
        if function_name not in self.function_registry:
            return {"success": False, "error": f"Function '{function_name}' not registered"}

        try:
            # Prepare context
            context = {"cognitive": cognitive_state or {}, "temporal": temporal_context or {}}

            # Execute function
            result = self.function_registry[function_name](*args, **kwargs, context=context)

            # Generate explanation
            explanation = self.xai_generator.explain_function_call(function_name, args, kwargs, result)

            return {"success": True, "result": result, "explanation": explanation, "context": context}
        except Exception as e:
            return {"success": False, "error": str(e), "context": context}
