"""
Spark - Universal Morphable Invoker ⚡

A single spark ignites a thousand possibilities.

Usage:
    from grid.spark import spark

    # Basic invocation
    result = spark("diagnose import errors")

    # With persona
    result = spark("find skills", persona="agentic")

    # Context manager
    with spark.as_navigator() as nav:
        issues = nav.diagnose("path/to/file.py")
"""

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, ContextManager

from .core import Spark, SparkPhase, SparkResult
from .personas import AgenticPersona, NavigatorPersona, Persona, ReasoningPersona, ResonancePersona

if TYPE_CHECKING:
    from .personas import Persona


class SparkFunction:
    """Invoker class to allow function-like call and convenience methods."""

    def __init__(self, instance: Spark):
        self._instance = instance
        self.parallel = instance.parallel

    def __call__(
        self,
        request: str,
        persona: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> SparkResult:
        """Universal invoker - the main entry point."""
        return self._instance.invoke(request, persona=persona, context=context)

    def as_navigator(self) -> ContextManager[Persona]:
        return self._instance.as_persona("navigator")

    def as_resonance(self) -> ContextManager[Persona]:
        return self._instance.as_persona("resonance")

    def as_agentic(self) -> ContextManager[Persona]:
        return self._instance.as_persona("agentic")

    def as_reasoning(self) -> ContextManager[Persona]:
        return self._instance.as_persona("reasoning")


# Global spark instance
_spark_instance = Spark()
spark = SparkFunction(_spark_instance)


__all__ = [
    "spark",
    "Spark",
    "SparkResult",
    "SparkPhase",
    "Persona",
    "NavigatorPersona",
    "ResonancePersona",
    "AgenticPersona",
    "ReasoningPersona",
]
