"""
Highway Router: The interface between Temporal Coherence and Structural Scaling.
"""

import hashlib
import logging
import random

logger = logging.getLogger(__name__)


class HighwayRouter:
    """
    Handles dual-mode distribution based on the Railway/Time and Freeway/Structure bridges.
    """

    def __init__(self, high_capacity_tracks: list[str], scalable_lanes: list[str]):
        # Railway = Temporal Interlocking nodes (Strict Ordering)
        self.railway_tracks = high_capacity_tracks
        # Freeway = Structural Partitioned lanes (High Throughput)
        self.freeway_lanes = scalable_lanes
        # Partitions for Category-relevant batches (Mapped to 7 Primary GRID Domains)
        self.partitions = {
            "CORE_INTEL": ["railway-alpha", "railway-beta"],
            "APP_SERVICE": ["lane-1", "lane-2"],
            "COGNITIVE": ["lane-3"],
            "TOOLS_INFRA": ["lane-4"],
            "ARENA": ["lane-1", "lane-3"],
            "INTEGRATION": ["lane-2", "lane-4"],
            "RESEARCH_DOCS": ["railway-alpha"],
            "DEFAULT": scalable_lanes,
        }

    def route_by_category(self, category: str, affinity_key: str) -> str:
        """
        Structural Partitioning: Routes signals based on their category partition.
        Ensures category-relevant batches are clustered together.
        """
        lanes = self.partitions.get(category.upper(), self.partitions["DEFAULT"])
        # Deterministic clustering within the partition
        idx = int(hashlib.md5(affinity_key.encode()).hexdigest(), 16) % len(lanes)  # noqa: S324 non-cryptographic use
        target = lanes[idx]
        logger.info(f"Signal [PARTITION:{category}] clustered to: {target}")
        return target

    def route_signal(self, context_type: str, affinity_key: str) -> str:
        """
        Routes the signal through either a Temporal track or a Structural lane.
        """
        if context_type == "SEED" or context_type == "CORE_STATE":
            return self._temporal_interlock(affinity_key)
        else:
            return self._structural_partition(affinity_key)

    def _temporal_interlock(self, affinity_key: str) -> str:
        """
        Railway Mode: Time-ordered routing.
        Ensures a stable 'schedule' by consistently hashing signals to the same
        'interlocking' node for causal coherence.
        """
        # SHA-256 for high-fidelity deterministic ordering
        hash_val = int(hashlib.sha256(affinity_key.encode()).hexdigest(), 16)
        track_index = hash_val % len(self.railway_tracks)
        target = self.railway_tracks[track_index]
        logger.info(f"Signal [TIME] interlocked to Railway track: {target}")
        return target

    def _structural_partition(self, affinity_key: str) -> str:
        """
        Freeway Mode: Structurally organized routing.
        Distributes signals across available lanes to maximize spatial throughput.
        """
        # Simple load-aware or random distribution across the structure
        target = random.choice(self.freeway_lanes)  # noqa: S311 non-security random use
        logger.info(f"Signal [STRUCTURE] merged into Freeway lane: {target}")
        return target
