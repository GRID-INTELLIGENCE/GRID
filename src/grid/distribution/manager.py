"""
Distribution Manager: The Central Interchange for GRID signals.
Orchestrates the conversion of state into routed signals.
"""

import logging
import time
from typing import Any

from .router import HighwayRouter
from .signal_path import SignalProcessor
from .worker_pool import DistributedWorkerPool

try:
    from EQ.integration import get_eq_integration  # type: ignore[import-not-found]
except ImportError:
    get_eq_integration = None

logger = logging.getLogger(__name__)


class DistributionManager:
    """
    Manages the 'Interchange' where temporal Railway tracks meet structural Freeway lanes.
    """

    def __init__(self, redis_url: str = "redis://redis:6379/0"):
        self.pool = DistributedWorkerPool(redis_url=redis_url)
        # Initialize the Highway architecture
        self.router = HighwayRouter(
            high_capacity_tracks=["railway-alpha", "railway-beta"],  # Stable Seed nodes
            scalable_lanes=["lane-1", "lane-2", "lane-3", "lane-4"],  # Agile Worker nodes
        )
        self.fx = SignalProcessor()

    async def emit_signal(
        self,
        task_type: str,
        payload: dict[str, Any],
        context_type: str = "AGILE",
        affinity_key: str = "global",
        reverb_size: float = 1.0,
        category: str | None = None,
    ):
        """
        Emits a signal with optimized reverb sizing and structural partitioning.
        """
        # 1. Spatial Phase (Reverb Size adjustment + EQ Enrichment)
        spatial_context = {"spatial_metadata": {"engine": "the_chase", "mode": "arcade"}}

        eq_aura = None
        if get_eq_integration:
            eq = get_eq_integration()
            if eq.is_available():
                # For now, we mock some emotional metadata or fetch real logic if available
                eq_aura = {"availability": "active", "integration": "EQ_MODULE"}

        processed_payload = self.fx.reverb(spatial_context, payload, size=reverb_size, eq_aura=eq_aura)

        # 2. Routing Phase (Category Partitioning)
        if category:
            target_node = self.router.route_by_category(category, affinity_key)
        else:
            target_node = self.router.route_signal(context_type, affinity_key)

        # 3. Temporal Phase (Resilience)
        async def submit_to_pool():
            return await self.pool.submit_task(
                task_type, {**processed_payload, "target": target_node, "category": category}
            )

        signal_id = f"sig_{int(time.time() * 1000)}_{affinity_key}"
        task_id = await self.fx.echo(signal_id, submit_to_pool)

        logger.info(f"Signal {signal_id} merged into {target_node} [Size: {reverb_size}]")
        return task_id

    async def emit_batch(self, category: str, tasks: list[dict[str, Any]], reverb_size: float = 1.2):
        """
        Dispatches category-relevant batches into assigned partitions.
        """
        logger.info(f"Dispatching batch of {len(tasks)} tasks into {category} partition...")
        batch_ids = []
        for i, task in enumerate(tasks):
            t_id = await self.emit_signal(
                task_type=task.get("type", "batch_task"),
                payload=task.get("payload", {}),
                affinity_key=f"batch_{category}_{i}",
                reverb_size=reverb_size,
                category=category,
            )
            batch_ids.append(t_id)
        return batch_ids

    async def start(self):
        await self.pool.connect()

    async def stop(self):
        await self.pool.stop()
