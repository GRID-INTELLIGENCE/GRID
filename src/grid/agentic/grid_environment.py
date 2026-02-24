"""GRID Environmental Intelligence Engine.

A homeostatic middleware that governs the round table's atmosphere by
dynamically adjusting LLM generation parameters based on conversational
triad balance.  Implements Le Chatelier's Principle applied to
computational linguistics — when one dimension dominates, the engine
alters adjacent factors to steer the conversation back toward equilibrium.

The GRID Triad:
    **Practical** (R) — revenue, execution, market, speed
    **Legal** (Z) — defense, ownership, compliance, protection
    **Psychological** (Ψ) — wellness, mindset, impact, collective balance

The engine operates as a passive listener: it does not explicitly command
topic changes.  Instead, it modifies the LLM's temperature, penalty, and
focus constraints so that the AI naturally gravitates toward neglected
dimensions.

Theoretical foundations:
    - Le Chatelier's Principle (concentration → counter-shift)
    - Cybernetic negative feedback loop (output → sensor → restoring force)
    - Attractor basins in dynamical systems (triad center = equilibrium)
"""

from __future__ import annotations

import logging
from collections import Counter
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from tools.rag.llm.base import BaseLLMProvider

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Core dimensions
# ---------------------------------------------------------------------------


class GridDimension(StrEnum):
    """The three pillars of the GRID triad."""

    PRACTICAL = "practical"
    LEGAL = "legal"
    PSYCHOLOGICAL = "psychological"


# ---------------------------------------------------------------------------
# Atmospheric state
# ---------------------------------------------------------------------------


class ArenaAmbiance(BaseModel):
    """The current atmospheric constraints governing AI generation.

    These map to LLM API parameters:
        reverb_temperature → temperature  (creativity / exploration)
        quantization_drift → presence_penalty & top_p  (unpredictability)
        hologram_density   → top_k  (logical focus / constraint)
        active_nudge       → system instruction injection
    """

    reverb_temperature: float = Field(default=0.5, ge=0.0, le=1.0)
    quantization_drift: float = Field(default=0.2, ge=0.0, le=1.0)
    hologram_density: float = Field(default=0.5, ge=0.0, le=1.0)
    active_nudge: str = Field(
        default="Synthesize points to maintain global GRID structure.",
        description="System instruction nudge injected into LLM calls",
    )


class EnvironmentalShift(BaseModel):
    """Records a single recalibration event for auditability."""

    trigger: str
    dominant_dimension: str
    temperature: float
    top_p: float
    presence_penalty: float
    top_k: int
    nudge: str


# ---------------------------------------------------------------------------
# Lexicons (keyword → dimension mapping)
# ---------------------------------------------------------------------------

_DEFAULT_LEXICONS: dict[GridDimension, set[str]] = {
    GridDimension.PRACTICAL: {
        "app",
        "launch",
        "revenue",
        "market",
        "liquid",
        "users",
        "fast",
        "ship",
        "execute",
        "mvp",
        "scale",
        "growth",
        "deploy",
        "product",
        "monetize",
        "iterate",
        "traction",
        "kpi",
        "metric",
        "pipeline",
    },
    GridDimension.LEGAL: {
        "protect",
        "legal",
        "ownership",
        "defend",
        "ip",
        "secure",
        "lock",
        "compliance",
        "regulation",
        "patent",
        "trademark",
        "license",
        "liability",
        "contract",
        "audit",
        "enforce",
        "governance",
        "policy",
    },
    GridDimension.PSYCHOLOGICAL: {
        "wellness",
        "mindset",
        "routine",
        "impact",
        "collective",
        "balance",
        "empathy",
        "burnout",
        "trust",
        "safety",
        "morale",
        "culture",
        "autonomy",
        "motivation",
        "wellbeing",
        "resilience",
        "inclusion",
        "harmony",
        "purpose",
        "fulfillment",
    },
}


# ---------------------------------------------------------------------------
# Environmental engine
# ---------------------------------------------------------------------------


class GridEnvironment:
    """Homeostatic environmental intelligence for the round table.

    Acts as a cybernetic governor: senses dimensional imbalance in the
    discussion and recalibrates LLM parameters to restore triad equilibrium.
    The recalibration follows Le Chatelier's Principle — excess concentration
    in one dimension triggers a counter-shift in adjacent factors.

    Usage::

        env = GridEnvironment()
        payload = env.process_wave("We need to launch fast for revenue")
        # payload contains adjusted LLM params + system nudge
    """

    # Threshold above which a dimension is considered dominant
    IMBALANCE_THRESHOLD: float = 0.2

    # How much each keyword hit shifts the weight
    WEIGHT_INCREMENT: float = 0.1

    def __init__(
        self,
        lexicons: dict[GridDimension, set[str]] | None = None,
        threshold: float | None = None,
    ) -> None:
        self._ambiance = ArenaAmbiance()
        self._weights: dict[GridDimension, float] = dict.fromkeys(GridDimension, 0.0)
        self._lexicons = lexicons or _DEFAULT_LEXICONS
        self._shifts: list[EnvironmentalShift] = []

        if threshold is not None:
            self.IMBALANCE_THRESHOLD = threshold

    # -- Public API --------------------------------------------------------

    def process_wave(self, text: str) -> dict:
        """Sense the conversational current and recalibrate.

        Args:
            text: The latest statement or text chunk to analyse.

        Returns:
            A dict with ``llm_parameters``, ``system_instruction``,
            and ``internal_state_weights``.
        """
        self._scan_lexicon(text)
        self._recalibrate()
        return self._generate_api_output()

    def get_weights(self) -> dict[str, float]:
        """Current triad weights for visualization."""
        return {dim.value: round(w, 3) for dim, w in self._weights.items()}

    def get_shifts(self) -> list[EnvironmentalShift]:
        """Ordered list of recalibration events."""
        return list(self._shifts)

    def reset(self) -> None:
        """Return to baseline equilibrium."""
        self._ambiance = ArenaAmbiance()
        self._weights = dict.fromkeys(GridDimension, 0.0)
        self._shifts.clear()

    # -- Internal mechanics ------------------------------------------------

    def _scan_lexicon(self, text: str) -> None:
        """Parse text and accumulate dimension weights."""
        words = text.lower().split()
        counts = Counter(words)

        for dim, keywords in self._lexicons.items():
            for kw in keywords:
                if kw in counts:
                    self._weights[dim] += self.WEIGHT_INCREMENT * counts[kw]

    def _recalibrate(self) -> None:
        """Apply Le Chatelier's Principle to adjacent factors.

        When one dimension dominates beyond the threshold, the engine
        adjusts the *other* factors to steer the LLM toward the
        neglected dimensions.
        """
        w = self._weights
        t = self.IMBALANCE_THRESHOLD

        p = w[GridDimension.PRACTICAL]
        l = w[GridDimension.LEGAL]  # noqa: E741
        y = w[GridDimension.PSYCHOLOGICAL]

        if l > y + t and l > p + t:
            # Legal dominance → increase creativity, nudge toward wellness
            self._ambiance.reverb_temperature = 0.7
            self._ambiance.quantization_drift = 0.4
            self._ambiance.hologram_density = 0.5
            self._ambiance.active_nudge = (
                "Shift focus: How does this legal structure impact the user's mental routine and practical execution?"
            )
            self._record_shift("legal_dominance", GridDimension.LEGAL)

        elif p > l + t and p > y + t:
            # Practical dominance → tighten focus, nudge toward defense + wellness
            self._ambiance.reverb_temperature = 0.5
            self._ambiance.quantization_drift = 0.1
            self._ambiance.hologram_density = 0.8
            self._ambiance.active_nudge = (
                "Pause execution. Visualize defensive vulnerabilities and psychological impact before proceeding."
            )
            self._record_shift("practical_dominance", GridDimension.PRACTICAL)

        elif y > p + t and y > l + t:
            # Psychological dominance → ground into action, add legal structure
            self._ambiance.reverb_temperature = 0.3
            self._ambiance.quantization_drift = 0.15
            self._ambiance.hologram_density = 0.9
            self._ambiance.active_nudge = (
                "Ground the psychological theory into a liquid, executable market step with legal safeguards."
            )
            self._record_shift("psychological_dominance", GridDimension.PSYCHOLOGICAL)

        else:
            # Equilibrium — restore baseline
            self._ambiance = ArenaAmbiance()

    def _record_shift(self, trigger: str, dominant: GridDimension) -> None:
        """Append a recalibration event to the audit trail."""
        payload = self._generate_api_output()
        params = payload["llm_parameters"]
        self._shifts.append(
            EnvironmentalShift(
                trigger=trigger,
                dominant_dimension=dominant.value,
                temperature=params["temperature"],
                top_p=params["top_p"],
                presence_penalty=params["presence_penalty"],
                top_k=params["top_k"],
                nudge=self._ambiance.active_nudge,
            )
        )
        logger.info(
            "Environmental shift: %s (dominant=%s, temp=%.2f)",
            trigger,
            dominant.value,
            params["temperature"],
        )

    def _generate_api_output(self) -> dict:
        """Format current atmospheric state as LLM-compatible parameters.

        Returns:
            Dict with ``llm_parameters``, ``system_instruction``,
            and ``internal_state_weights``.
        """
        a = self._ambiance
        return {
            "llm_parameters": {
                "temperature": round(a.reverb_temperature, 2),
                "top_p": round(max(0.1, 1.0 - a.quantization_drift), 2),
                "presence_penalty": round(a.quantization_drift * 2.0, 2),
                "top_k": int(40 * (1.1 - a.hologram_density)),
            },
            "system_instruction": (f"Current room constraint: {a.active_nudge}"),
            "internal_state_weights": self.get_weights(),
        }


# ---------------------------------------------------------------------------
# Environmental LLM proxy
# ---------------------------------------------------------------------------


class EnvironmentalLLMProxy:
    """Wraps a ``BaseLLMProvider`` and auto-injects environment-adjusted parameters.

    Creates a closed feedback loop: each ``generate()`` call feeds the prompt
    through the environmental sensor before reaching the inner LLM.  The
    engine's recalibrated temperature and system nudge are injected
    transparently — callers interact with the same ``generate()`` signature.

    Stream and async methods delegate directly to the inner LLM without
    environmental adjustment to keep scope tight.

    Usage::

        from tools.rag.llm.gemini import GeminiLLM

        inner = GeminiLLM(model="gemini-2.5-flash-preview-09-2025")
        env = GridEnvironment()
        proxy = EnvironmentalLLMProxy(inner, env)
        result = proxy.generate("launch the app fast for revenue")
        # → temperature, system nudge adjusted by the environment engine
    """

    def __init__(self, llm: BaseLLMProvider, environment: GridEnvironment) -> None:
        self._llm = llm
        self._env = environment

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate text with environment-adjusted parameters.

        1. Feeds the prompt through ``process_wave`` to sense triad balance
        2. Overrides temperature with the engine's recalibrated value
        3. Prepends the active nudge to the system message
        4. Delegates to the inner LLM's ``generate``
        """
        payload = self._env.process_wave(prompt)
        adjusted_temp = payload["llm_parameters"]["temperature"]
        nudge = payload["system_instruction"]

        if system:
            combined_system = f"{nudge}\n\n{system}"
        else:
            combined_system = nudge

        return self._llm.generate(
            prompt,
            system=combined_system,
            temperature=adjusted_temp,
            max_tokens=max_tokens,
            **kwargs,
        )

    def stream(self, prompt: str, system: str | None = None, temperature: float = 0.7, **kwargs: Any) -> Any:
        """Stream text generation — passthrough to inner LLM."""
        return self._llm.stream(prompt, system=system, temperature=temperature, **kwargs)

    async def async_generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Async generate — passthrough to inner LLM."""
        return await self._llm.async_generate(
            prompt, system=system, temperature=temperature, max_tokens=max_tokens, **kwargs
        )

    async def async_stream(
        self, prompt: str, system: str | None = None, temperature: float = 0.7, **kwargs: Any
    ) -> Any:
        """Async stream — passthrough to inner LLM."""
        return await self._llm.async_stream(prompt, system=system, temperature=temperature, **kwargs)
