"""Interface Bridge - Bridges canvas with grid/interfaces (QuantumBridge, SensoryProcessor)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from grid.awareness.context import Context
from grid.essence.core_state import EssentialState
from grid.interfaces.bridge import QuantumBridge
from grid.interfaces.sensory import SensoryInput, SensoryProcessor

from .schemas import SensoryResult, TransferResult

logger = logging.getLogger(__name__)


class InterfaceBridge:
    """Bridges canvas with grid/interfaces (QuantumBridge, SensoryProcessor)."""

    def __init__(
        self,
        quantum_bridge: QuantumBridge | None = None,
        sensory_processor: SensoryProcessor | None = None,
    ):
        """Initialize interface bridge.

        Args:
            quantum_bridge: Optional QuantumBridge instance
            sensory_processor: Optional SensoryProcessor instance
        """
        self.quantum_bridge = quantum_bridge or QuantumBridge()
        self.sensory_processor = sensory_processor or SensoryProcessor()

    async def transfer_state(
        self,
        source_state: EssentialState,
        target_context: Context,
        route_path: Path | None = None,
    ) -> TransferResult:
        """Transfer state using QuantumBridge for coherent transfers.

        Args:
            source_state: Source essential state
            target_context: Target context
            route_path: Optional route path for tracking

        Returns:
            TransferResult with coherence and integrity information
        """
        try:
            # Use QuantumBridge for state transfer
            transfer_result = await self.quantum_bridge.transfer(state=source_state, context=target_context)

            success = transfer_result.get("coherence_level", 0.0) > 0.7

            return TransferResult(
                success=success,
                coherence_level=transfer_result.get("coherence_level", 0.0),
                transfer_signature=transfer_result.get("transfer_signature", ""),
                integrity_check=transfer_result.get("integrity_check", ""),
            )
        except Exception as e:
            logger.error(f"State transfer failed: {e}")
            return TransferResult(
                success=False,
                coherence_level=0.0,
                transfer_signature="",
                integrity_check="",
            )

    async def process_sensory_input(
        self,
        input_data: dict[str, Any],
        modality: str = "text",
    ) -> SensoryResult:
        """Process sensory input using SensoryProcessor.

        Args:
            input_data: Input data dictionary
            modality: Input modality (text, visual, audio, structured)

        Returns:
            SensoryResult with processed features
        """
        import time

        try:
            sensory_input = SensoryInput(
                source="canvas",
                data=input_data,
                timestamp=time.time(),
                modality=modality,
            )

            processed = await self.sensory_processor.process(sensory_input)

            return SensoryResult(
                features=processed.get("features", {}),
                coherence=processed.get("coherence", 0.5),
                modality=modality,
                processed=processed,
            )
        except Exception as e:
            logger.error(f"Sensory processing failed: {e}")
            return SensoryResult(
                features={},
                coherence=0.0,
                modality=modality,
                processed={},
            )
