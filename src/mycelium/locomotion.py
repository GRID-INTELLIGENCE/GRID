"""
MYCELIUM Locomotion — Traversing the Leased Navigation State.

Locomotion is the act of stepping through a sequence of nodes (like a traceback)
while using the Lamp to see the boundaries and the JungleEngine to ensure
concurrency balance.
"""

from __future__ import annotations

import logging
import time
from typing import List, Optional

from mycelium.concurrency import JungleEngine
from mycelium.domains import DomainResolver
from mycelium.lamp import DomainLamp, IlluminatedPath

logger = logging.getLogger(__name__)


class TracebackLocomotion:
    """The mechanical actuator for moving safely across the filesystem."""

    def __init__(self, engine: JungleEngine, resolver: Optional[DomainResolver] = None):
        self.engine = engine
        self.resolver = resolver or DomainResolver(root="e:\\GRID-main")
        self.lamp = DomainLamp(self.resolver)

    def traverse(self, traceback_nodes: List[str]) -> dict:
        """
        Executes a contiguous walk down a traceback sequence.
        Will Halt if the Lamp reveals a fatal hazard or if the
        JungleEngine detects a deadlock storm.
        """
        logger.info(f"🚂 Initiating Locomotion Sequence for {len(traceback_nodes)} nodes.")

        walked_path = []
        aborted = False
        reason = ""
        current_domain = None

        for node in traceback_nodes:
            # 1. Lamp: Illuminate before stepping
            illumination: IlluminatedPath = self.lamp.illuminate(node, current_domain)

            if illumination.warnings:
                for w in illumination.warnings:
                    logger.warning(w)

            # 2. Safety Check (Beta Column)
            if not self.engine.is_path_safe(node, walked_path):
                # Try to improve the neighborhood before giving up
                logger.info(f"Locomotion paused at {node}: Requesting balance restoration.")
                self.engine.improve_neighborhood()

                # Double-check
                if not self.engine.is_path_safe(node, walked_path):
                    aborted = True
                    reason = f"Fatal Concurrency Block at {node}. Altitude or loop hazard too high."
                    break

            # 3. Step forward securely (Acquire lock/context)
            with self.engine.acquire_jungle_context(node):
                z_axis = self.engine.get_z_axis_telemetry()

                # Simulate the "friction" logic (Refractive Index)
                # Engine = high density (fast but strict computation)
                time.sleep(0.01 * illumination.refractive_index)

                walked_path.append(node)
                current_domain = illumination.domain
                logger.info(f"📍 Stepped -> {node} [Z-Axis: {z_axis}]")

        status = "Completed" if not aborted else "Aborted"

        return {
            "status": status,
            "nodes_traversed": len(walked_path),
            "walked_path": walked_path,
            "abort_reason": reason
        }
