"""Application layer orchestrating the pipeline."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from grid.awareness.context import Context
from grid.essence.core_state import EssentialState
from grid.evolution.version import VersionState
from grid.interfaces.bridge import QuantumBridge
from grid.interfaces.sensory import SensoryProcessor
from grid.patterns.recognition import PatternRecognition


@dataclass
class ApplicationConfig:
    enable_pattern_tracking: bool = True
    enable_context_evolution: bool = True
    max_patterns: int = 10


class IntelligenceApplication:
    """Orchestrates state, context, pattern recognition, bridge, and sensory processing."""

    def __init__(self, config: ApplicationConfig | None = None):
        self.config = config or ApplicationConfig()
        self.pattern_recognizer = PatternRecognition()
        self.sensory_processor = SensoryProcessor()
        self.bridge = QuantumBridge()
        self.current_state: EssentialState | None = None
        self.current_context: Context | None = None
        self.interaction_log: list[dict[str, Any]] = []

    async def process_input(
        self,
        data: dict[str, Any],
        context_params: dict[str, Any],
        include_evidence: bool = False,
    ) -> dict[str, Any]:
        """Process input through the full intelligence pipeline."""
        t0 = time.perf_counter() if include_evidence else 0.0
        ctx = Context(
            temporal_depth=context_params.get("temporal_depth", 1.0),
            spatial_field=context_params.get("spatial_field", {}),
            relational_web=context_params.get("relational_web", {}),
            quantum_signature=context_params.get("quantum_signature", "ctx"),
        )
        t_ctx = time.perf_counter() if include_evidence else 0.0
        self.current_context = ctx

        self.current_state = EssentialState(
            pattern_signature=f"sig_{len(self.interaction_log)}",
            quantum_state=data,
            context_depth=ctx.temporal_depth,
            coherence_factor=context_params.get("coherence", 0.5),
        )
        t_state = time.perf_counter() if include_evidence else 0.0

        recognition = await self.pattern_recognizer.recognize(self.current_state)
        # normalize to list
        patterns = recognition if isinstance(recognition, list) else [recognition]
        t_recognition = time.perf_counter() if include_evidence else 0.0

        bridge_result = await self.bridge.transfer(self.current_state, ctx)
        t_bridge = time.perf_counter() if include_evidence else 0.0

        entry = {
            "patterns": patterns,
            "coherence_level": bridge_result.get("coherence_level", self.current_state.coherence_factor),
            "context_depth": ctx.temporal_depth,
        }
        if include_evidence:
            entry["bridge"] = bridge_result
            entry["state_signature"] = self.current_state.pattern_signature
            entry["context_signature"] = ctx.quantum_signature
            entry["timings_ms"] = {
                "context_create_ms": (t_ctx - t0) * 1000.0,
                "state_create_ms": (t_state - t_ctx) * 1000.0,
                "pattern_recognition_ms": (t_recognition - t_state) * 1000.0,
                "bridge_transfer_ms": (t_bridge - t_recognition) * 1000.0,
                "total_ms": (t_bridge - t0) * 1000.0,
            }
        self.interaction_log.append(entry)
        return entry

    def get_interaction_summary(self) -> dict[str, Any]:
        count = len(self.interaction_log)
        avg_coherence = sum(item.get("coherence_level", 0) for item in self.interaction_log) / count if count else 0.0
        return {"total_interactions": count, "average_coherence": avg_coherence}

    def reset(self) -> None:
        self.current_state = None
        self.current_context = None
        self.interaction_log.clear()

    async def evolve_version(self) -> VersionState:
        """Placeholder for model/logic version evolution."""
        if self.current_state is None or self.current_context is None:
            self.current_context = Context(
                temporal_depth=1.0, spatial_field={}, relational_web={}, quantum_signature="ctx"
            )
            self.current_state = EssentialState(
                pattern_signature="init", quantum_state={}, context_depth=1.0, coherence_factor=0.5
            )
        return VersionState(
            essential_state=self.current_state,
            context=self.current_context,
            quantum_signature="v1",
            transform_history=[],
        )
