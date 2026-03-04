"""
Pathways Integration Adapter
=============================
Integrates Pathways/Networks semantic resonance with unified fabric.

Features:
- Safety-validated resonance signal processing
- Event-driven resonance broadcasting
- Temporal connection awareness

Security: Safety and audit identity are never taken from signal.metadata
to prevent spoofing; they use a fixed system identity ("pathways-system")
or a caller-provided trusted_user_id when the adapter is invoked from an
authenticated context.
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from . import Event, EventDomain, get_event_bus
from .safety_bridge import SafetyContext, get_safety_bridge

logger = logging.getLogger(__name__)


@dataclass
class ResonanceSignal:
    """A semantic resonance signal from Pathways."""

    trigger_content: str
    resonating_content: str
    connection_strength: float  # 0.0–1.0
    semantic_similarity: float = 0.0  # 0.0–1.0
    emotional_amplification: float = 0.0  # 0.0–1.0
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    signal_id: str = field(
        default_factory=lambda: f"res_{datetime.now(UTC).timestamp():.0f}"
    )
    metadata: dict[str, Any] = field(default_factory=dict)


class PathwaysIntegrationAdapter:
    """
    Adapter for integrating Pathways/Networks with unified fabric.

    Connects:
    - Semantic resonance signals → Safety validation → Event bus
    - Knowledge queries → Event bus relay → Pathways ScopedRAG
    """

    def __init__(self) -> None:
        self._safety_bridge = get_safety_bridge()
        self._event_bus = get_event_bus()
        self._signal_handlers: list = []
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the adapter and subscribe to pathways events."""
        if self._initialized:
            return

        self._event_bus.subscribe(
            "pathways.resonance.*", self._handle_resonance_event, domain="pathways"
        )
        self._event_bus.subscribe(
            "pathways.knowledge.*", self._handle_knowledge_event, domain="pathways"
        )

        self._initialized = True
        logger.info("PathwaysIntegrationAdapter initialized")

    async def process_resonance(
        self,
        signal: ResonanceSignal,
        trusted_user_id: str | None = None,
    ) -> bool:
        """
        Process a resonance signal with safety validation.

        Safety and audit identity are not taken from signal.metadata to prevent
        spoofing. Use trusted_user_id only when the caller has already
        authenticated the user (e.g. API layer or internal Pathways service);
        otherwise the system identity "pathways-system" is used.

        Args:
            signal: Semantic resonance signal from Pathways
            trusted_user_id: Optional user id from trusted caller context. Must
                only be set by code that has already authenticated the user;
                signal.metadata is never used for safety/audit attribution.

        Returns:
            True if signal was processed and broadcast successfully
        """
        # user_id is never taken from signal.metadata to prevent spoofing
        user_id = trusted_user_id if trusted_user_id is not None else "pathways-system"
        # Safety validation
        report = await self._safety_bridge.validate(
            f"Resonance signal: strength={signal.connection_strength} "
            f"similarity={signal.semantic_similarity}",
            SafetyContext(
                project="pathways",
                domain="resonance",
                user_id=user_id,
                metadata={"signal_id": signal.signal_id},
            ),
        )

        if report.should_block:
            logger.warning("Resonance signal blocked by safety: %s", signal.signal_id)
            return False

        # Dispatch to registered handlers
        for handler in self._signal_handlers:
            try:
                await handler(signal)
            except Exception as e:
                logger.error("Resonance handler error: %s", e)

        # Broadcast on event bus
        await self._broadcast_resonance_event(signal)

        return True

    def register_signal_handler(self, handler: Any) -> None:
        """Register a handler for resonance signals."""
        self._signal_handlers.append(handler)

    async def _broadcast_resonance_event(self, signal: ResonanceSignal) -> None:
        """Broadcast a resonance event on the event bus."""
        event = Event(
            event_type="pathways.resonance.detected",
            payload={
                "signal_id": signal.signal_id,
                "trigger_content": signal.trigger_content,
                "resonating_content": signal.resonating_content,
                "connection_strength": signal.connection_strength,
                "semantic_similarity": signal.semantic_similarity,
                "emotional_amplification": signal.emotional_amplification,
                "timestamp": signal.timestamp,
            },
            source_domain=EventDomain.PATHWAYS.value,
            target_domains=["all"],
        )
        await self._event_bus.publish(event)

    async def _handle_resonance_event(self, event: Event) -> None:
        """Handle incoming resonance events."""
        logger.debug("Received resonance event: %s", event.event_type)

    async def _handle_knowledge_event(self, event: Event) -> None:
        """Handle incoming knowledge events."""
        logger.debug("Received knowledge event: %s", event.event_type)


# Singleton instance
_pathways_adapter: PathwaysIntegrationAdapter | None = None


def get_pathways_adapter() -> PathwaysIntegrationAdapter:
    """Get the singleton Pathways adapter."""
    global _pathways_adapter
    if _pathways_adapter is None:
        _pathways_adapter = PathwaysIntegrationAdapter()
    return _pathways_adapter


async def init_pathways_adapter() -> PathwaysIntegrationAdapter:
    """Initialize the Pathways adapter."""
    adapter = get_pathways_adapter()
    await adapter.initialize()
    return adapter
