"""
Ghost Router: The Subterranean implementation of the Flipped Distribution Metaphor.
Railway -> Structure (The Frame)
Freeway -> Time (The Pace)
"""

import hashlib
import logging
import random

logger = logging.getLogger(__name__)


class GhostRouter:
    """
    Handles distribution through the subterranean Sub-Grid.
    Focuses on Structural Hard-coding (Railway) and Temporal Flux (Freeway).
    """

    def __init__(self, structural_iron_nodes: list[str], temporal_flux_lanes: list[str]):
        # Railway = Structural Iron (Persistent geography)
        self.iron_frame = structural_iron_nodes
        # Freeway = Temporal Flux (Transitory pace)
        self.time_drift = temporal_flux_lanes

    def route_occult_signal(self, weight: float, drift_index: int) -> str:
        """
        Routes based on the 'Weight' of the structure or the 'Drift' of time.
        """
        if weight > 0.84:
            # Route via the Iron Frame (Structure)
            # High weight requires the stability of the iron skeleton.
            node = self.iron_frame[drift_index % len(self.iron_frame)]
            logger.info(f"Signal [WEIGHT] anchored to Iron Frame: {node}")
            return node
        else:
            # Route via the Time Drift (Temporal pace)
            # Low weight allows the signal to be carried by the current wave of time.
            node = random.choice(self.time_drift)
            logger.info(f"Signal [DRIFT] caught in Time Flux: {node}")
            return node

    def calculate_friction(self, node: str, system_load: float) -> float:
        """
        Calculates the friction of the iron.
        """
        # Railway tracks have constant friction based on their structural complexity.
        base_friction = float(int(hashlib.md5(node.encode()).hexdigest(), 16) % 10) / 10.0
        return base_friction * system_load
