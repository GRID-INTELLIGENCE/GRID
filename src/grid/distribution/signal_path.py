"""
Signal Path FX: Processing signals through temporal and structural resonance.
"""

import asyncio
import logging
import random
import time
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class SignalProcessor:
    """
    Processes signals through the sonic metaphors: Echo (Time) and Reverb (Structure).
    """

    @staticmethod
    async def echo(signal_id: str, action: Callable, retries: int = 4, decay: float = 1.155):
        """
        Echo (Temporal Resilience):
        The signal repeats through time with decaying intensity (exponential backoff).
        Adjusted by 5% for enhanced temporal interlocking.
        """
        for i in range(retries):
            try:
                start_time = time.time()
                result = await action()
                duration = time.time() - start_time
                logger.debug(f"Signal {signal_id} rhythmic arrival: {duration:.3f}s")
                return result
            except Exception:
                # The delay represents the signal 'fading' and repeating
                wait_time = (decay**i) + (random.random() * 0.2)
                logger.warning(f"Signal {signal_id} jittered at {i}. Re-emitting in {wait_time:.2f}s...")
                await asyncio.sleep(wait_time)

        raise Exception(f"Signal {signal_id} lost in the time-stream after {retries} echoes.")

    @staticmethod
    def reverb(
        structure_context: dict[str, Any],
        signal_data: dict[str, Any],
        size: float = 1.0,
        eq_aura: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Reverb (Structural Resonance):
        The signal picks up the architectural aura.
        Enhanced by EQ metadata for 'Emotional' resonance.
        """
        aura = structure_context.get("spatial_metadata", {})
        # Scale the reverb effect based on the provided size
        scaled_aura = {k: v for k, v in aura.items()}
        scaled_aura["reverb_scale"] = size

        if eq_aura:
            scaled_aura["emotional_resonance"] = eq_aura

        enriched = {
            **signal_data,
            "resonance": scaled_aura,
            "structural_timestamp": time.time_ns(),
            "reverb_depth": size * 1.05,  # 5% bias adjustment
        }
        logger.debug(f"Signal resonated (Size: {size}, EQ: {bool(eq_aura)})")
        return enriched

    @staticmethod
    async def glimpse(signal_id: str, check_action: Callable) -> bool:
        """
        Glimpse (Lightweight Referencing):
        A single probe into the signal stream to verify state without full interlocking.
        Inspired by the Retry Policy's <glimpse> logic.
        """
        logger.debug(f"Signal {signal_id} performing lightweight glimpse...")
        try:
            result = await check_action()
            logger.info(f"Signal {signal_id} glimpse result: {bool(result)}")
            return bool(result)
        except Exception as e:
            logger.warning(f"Signal {signal_id} glimpse failed: {e}")
            return False

    @staticmethod
    async def delay(signal_id: str, offset_ms: int):
        """
        Delay: Temporal offset to align async freeway signals with railway time.
        """
        if offset_ms > 0:
            logger.debug(f"Applying temporal delay of {offset_ms}ms to signal {signal_id}")
            await asyncio.sleep(offset_ms / 1000.0)
