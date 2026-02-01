"""
Spark Core - ADSR lifecycle with persona morphing.

Inspired by:
- resonance/adsr_envelope.py (lifecycle phases)
- agentic/event_bus.py (event emission)
- knowledge/reasoning_orchestrator.py (multi-source reasoning)
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable, ContextManager
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .personas import Persona

logger = logging.getLogger(__name__)


class SparkPhase(str, Enum):
    """Spark lifecycle phases (ADSR-inspired)."""

    IDLE = "idle"
    ATTACK = "attack"  # Initial trigger, loading context
    SUSTAIN = "sustain"  # Main execution
    RELEASE = "release"  # Cleanup, returning results
    COMPLETE = "complete"


@dataclass
class SparkResult:
    """Result from a Spark invocation."""

    request: str
    output: Any
    persona: str
    phase: SparkPhase = SparkPhase.COMPLETE
    duration_ms: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        """Check if invocation was successful."""
        return self.output is not None and self.phase == SparkPhase.COMPLETE


class Spark:
    """
    Universal Morphable Invoker.

    Can take on personas to morph into different capabilities:
    - Navigator: Path resolution and import diagnostics
    - Resonance: Activity feedback with ADSR envelope
    - Agentic: Skill execution and case handling
    - Reasoning: Multi-source reasoning (web + KG + LLM)
    """

    def __init__(self, default_persona: str = "reasoning") -> None:
        """Initialize Spark.

        Args:
            default_persona: Default persona when none specified
        """
        self.default_persona = default_persona
        self._phase = SparkPhase.IDLE
        self._personas: dict[str, Persona] = {}
        self._persona_classes: dict[str, type[Persona]] = {}
        self._hooks: dict[str, list[Callable]] = {
            "attack": [],
            "sustain": [],
            "release": [],
        }

    def _get_persona(self, name: str) -> Persona | None:
        """Get or instantiate a persona."""
        if name in self._personas:
            return self._personas[name]

        if not self._persona_classes:
            self._register_default_personas()

        if name in self._persona_classes:
            persona_cls = self._persona_classes[name]
            self._personas[name] = persona_cls()
            return self._personas[name]

        return None

    def _register_default_personas(self) -> None:
        """Register built-in personas (classes only, no instantiation)."""
        from .personas import AgenticPersona, NavigatorPersona, ReasoningPersona, ResonancePersona, StaircasePersona

        self._persona_classes = {
            "navigator": NavigatorPersona,
            "resonance": ResonancePersona,
            "agentic": AgenticPersona,
            "reasoning": ReasoningPersona,
            "staircase": StaircasePersona,
        }

    def invoke(
        self,
        request: str,
        persona: str | None = None,
        context: dict | None = None,
    ) -> SparkResult:
        """
        Invoke Spark with a request.

        Args:
            request: Natural language request
            persona: Optional persona name
            context: Optional additional context

        Returns:
            SparkResult with output
        """
        start_time = time.time()
        persona_name = persona or self.default_persona

        # Attack phase - trigger and load context
        self._phase = SparkPhase.ATTACK
        self._run_hooks("attack")

        # Get persona
        active_persona = self._get_persona(persona_name)
        if not active_persona:
            logger.warning(f"Unknown persona '{persona_name}', using {self.default_persona}")
            active_persona = self._get_persona(self.default_persona)
            persona_name = self.default_persona

        if not active_persona:
            raise ValueError(f"Could not load persona: {persona_name}")

        # Sustain phase - execute
        self._phase = SparkPhase.SUSTAIN
        self._run_hooks("sustain")

        try:
            output = active_persona.execute(request, context)
        except Exception as e:
            logger.error(f"Spark execution failed: {e}")
            output = {"error": str(e)}

        # Release phase - cleanup
        self._phase = SparkPhase.RELEASE
        self._run_hooks("release")

        # Complete
        self._phase = SparkPhase.COMPLETE
        duration_ms = int((time.time() - start_time) * 1000)

        return SparkResult(
            request=request,
            output=output,
            persona=persona_name,
            phase=SparkPhase.COMPLETE,
            duration_ms=duration_ms,
        )

    async def parallel(
        self,
        requests: list[str],
        persona: str | None = None,
        mode: str = "kanye",  # "kanye" = all at once, "jay" = sequential
    ) -> list[SparkResult]:
        """
        Execute multiple requests in parallel or sequential.

        Args:
            requests: List of requests to execute
            persona: Optional persona for all requests
            mode: "kanye" (parallel) or "jay" (sequential)

        Returns:
            List of SparkResults
        """
        if mode == "jay":
            # Sequential execution
            return [self.invoke(req, persona=persona) for req in requests]

        # Parallel execution (Kanye mode!)
        async def invoke_async(req: str) -> SparkResult:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: self.invoke(req, persona=persona))

        tasks = [invoke_async(req) for req in requests]
        return await asyncio.gather(*tasks)

    @contextmanager
    def as_persona(self, persona_name: str) -> ContextManager[Persona]:
        """
        Context manager for using a specific persona.

        Args:
            persona_name: Name of persona to use

        Yields:
            Persona instance
        """
        persona = self._get_persona(persona_name)
        if not persona:
            raise ValueError(f"Unknown persona: {persona_name}")

        old_phase = self._phase
        self._phase = SparkPhase.ATTACK

        try:
            yield persona
        finally:
            self._phase = old_phase

    def on_attack(self, fn: Callable) -> Callable:
        """Decorator for attack phase hooks."""
        self._hooks["attack"].append(fn)
        return fn

    def on_sustain(self, fn: Callable) -> Callable:
        """Decorator for sustain phase hooks."""
        self._hooks["sustain"].append(fn)
        return fn

    def on_release(self, fn: Callable) -> Callable:
        """Decorator for release phase hooks."""
        self._hooks["release"].append(fn)
        return fn

    def _run_hooks(self, phase: str) -> None:
        """Run hooks for a phase."""
        for hook in self._hooks.get(phase, []):
            try:
                hook()
            except Exception as e:
                logger.warning(f"Hook error in {phase}: {e}")

    def register_persona(self, name: str, persona: Persona) -> None:
        """Register a custom persona.

        Args:
            name: Persona name
            persona: Persona instance
        """
        self._personas[name] = persona

    @property
    def phase(self) -> SparkPhase:
        """Get current phase."""
        return self._phase

    @property
    def available_personas(self) -> list[str]:
        """Get list of available personas."""
        if not self._persona_classes:
            self._register_default_personas()
        return sorted(list(set(self._personas.keys()) | set(self._persona_classes.keys())))
