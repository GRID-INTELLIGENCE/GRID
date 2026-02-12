"""
Signal Ghost FX: Friction, Drift, and Crosstalk.
The subterranean counterpart to the surface FX.
"""

import asyncio
import logging
import random
import time
from typing import Any

logger = logging.getLogger(__name__)


class GhostProcessor:
    """
    Processes signals through the subterranean metaphors: Friction and Drift.
    """

    @staticmethod
    async def apply_friction(signal_id: str, load_factor: float):
        """
        Friction (Structural Resistance):
        The cost of moving across the iron. Induces a deliberate delay
        proportional to the structural weight of the path.
        """
        burn_time = (load_factor * 0.525) + (random.random() * 0.1)
        logger.debug(f"Signal {signal_id} generating friction: {burn_time:.3f}s")
        await asyncio.sleep(burn_time)

    @staticmethod
    def calculate_drift(signal_data: dict[str, Any]) -> dict[str, Any]:
        """
        Drift (Temporal Decay):
        As the signal moves through the Freeway of Time, its precision decays.
        Injects 'Temporal Noise' into the signal to reflect its age.
        """
        original_ts = signal_data.get("structural_timestamp", time.time_ns())
        age_ns = time.time_ns() - original_ts
        # Drift increases with age
        drift_factor = min(1.0, age_ns / 1_000_000_000.0)

        signal_data["drift_variance"] = drift_factor
        logger.debug(f"Signal drift calculated: {drift_factor:.6f}")
        return signal_data
