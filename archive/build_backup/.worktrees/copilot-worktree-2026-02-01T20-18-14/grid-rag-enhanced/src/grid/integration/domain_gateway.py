"""
GRID Decoupling Layer - Domain Bounded Contexts
================================================

This module implements a Domain-Driven Design (DDD) Anti-Corruption Layer (ACL)
following modern Python decoupling patterns from community best practices (2024).

Domain Categories:
------------------
1. **Intelligence Domain** - LLM, embeddings, reasoning (grid.services, grid.knowledge)
2. **Orchestration Domain** - Events, skills, agentic flow (grid.agentic, grid.skills)
3. **Persistence Domain** - Data, caching, state (grid.database, grid.io)
4. **Observation Domain** - Tracing, monitoring, logging (grid.tracing, grid.logs)

Design Patterns Applied:
------------------------
- Facade: Single entry point per domain
- Adapter: Protocol-based contracts with runtime binding
- Translator: Data Transfer Objects (DTOs) for cross-domain communication
- Factory: Lazy instantiation with graceful degradation

References:
- Microsoft ACL Pattern: https://learn.microsoft.com/en-us/azure/architecture/patterns/anti-corruption-layer
- DDD Practitioners: https://ddd-practitioners.com
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Protocol

logger = logging.getLogger(__name__)

# =============================================================================
# Data Transfer Objects (DTOs) - Cross-Domain Communication
# =============================================================================


@dataclass(frozen=True)
class IntelligenceRequest:
    """DTO for intelligence domain requests."""

    prompt: str
    model: str = "default"
    temperature: float = 0.7
    max_tokens: int = 512
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class IntelligenceResponse:
    """DTO for intelligence domain responses."""

    content: str
    model_used: str
    tokens_used: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: str | None = None


@dataclass(frozen=True)
class OrchestrationCommand:
    """DTO for orchestration domain commands."""

    action: str
    payload: dict[str, Any]
    correlation_id: str | None = None


@dataclass
class OrchestrationResult:
    """DTO for orchestration domain results."""

    action: str
    status: str  # "success", "pending", "failed"
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class DomainCategory(Enum):
    """Bounded context categories."""

    INTELLIGENCE = auto()
    ORCHESTRATION = auto()
    PERSISTENCE = auto()
    OBSERVATION = auto()


# =============================================================================
# Protocols (Contracts) - Interface Segregation
# =============================================================================


class IntelligencePort(Protocol):
    """Port for Intelligence domain operations."""

    async def generate(self, request: IntelligenceRequest) -> IntelligenceResponse: ...
    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class OrchestrationPort(Protocol):
    """Port for Orchestration domain operations."""

    async def dispatch(self, command: OrchestrationCommand) -> OrchestrationResult: ...
    async def subscribe(self, event_type: str, handler: Callable) -> None: ...


class PersistencePort(Protocol):
    """Port for Persistence domain operations."""

    async def store(self, key: str, value: Any, ttl: int | None = None) -> bool: ...
    async def retrieve(self, key: str) -> Any | None: ...
    async def delete(self, key: str) -> bool: ...


class ObservationPort(Protocol):
    """Port for Observation domain operations."""

    def trace(self, operation: str, data: dict[str, Any]) -> None: ...
    def metric(self, name: str, value: float, tags: dict[str, str] | None = None) -> None: ...


# =============================================================================
# Null Object Adapters (Ghost Implementations)
# =============================================================================


class GhostIntelligence:
    """Null object for Intelligence domain."""

    async def generate(self, request: IntelligenceRequest) -> IntelligenceResponse:
        logger.debug(f"[Ghost] Intelligence generate: {request.prompt[:50]}...")
        return IntelligenceResponse(
            content="[Simulated response - Intelligence domain not connected]", model_used="ghost", success=True
        )

    async def embed(self, texts: list[str]) -> list[list[float]]:
        logger.debug(f"[Ghost] Intelligence embed: {len(texts)} texts")
        return [[0.0] * 384 for _ in texts]  # Mock 384-dim embeddings


class GhostOrchestration:
    """Null object for Orchestration domain."""

    _handlers: dict[str, list[Callable]] = {}

    async def dispatch(self, command: OrchestrationCommand) -> OrchestrationResult:
        logger.debug(f"[Ghost] Orchestration dispatch: {command.action}")
        return OrchestrationResult(action=command.action, status="simulated")

    async def subscribe(self, event_type: str, handler: Callable) -> None:
        logger.debug(f"[Ghost] Orchestration subscribe: {event_type}")
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)


class GhostPersistence:
    """Null object for Persistence domain - in-memory fallback."""

    _store: dict[str, Any] = {}

    async def store(self, key: str, value: Any, ttl: int | None = None) -> bool:
        logger.debug(f"[Ghost] Persistence store: {key}")
        self._store[key] = value
        return True

    async def retrieve(self, key: str) -> Any | None:
        logger.debug(f"[Ghost] Persistence retrieve: {key}")
        return self._store.get(key)

    async def delete(self, key: str) -> bool:
        logger.debug(f"[Ghost] Persistence delete: {key}")
        return self._store.pop(key, None) is not None


class GhostObservation:
    """Null object for Observation domain - console logging."""

    def trace(self, operation: str, data: dict[str, Any]) -> None:
        logger.debug(f"[Ghost] Trace: {operation} -> {data}")

    def metric(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        logger.debug(f"[Ghost] Metric: {name}={value} tags={tags}")


# =============================================================================
# Real Adapters (Connecting to GRID)
# =============================================================================


class GridIntelligenceAdapter:
    """Adapter connecting to grid.services for Intelligence operations."""

    def __init__(self):
        self._llm_client = None
        self._embedding_client = None

    def _load_llm(self) -> None:
        try:
            from grid.services.llm.llm_client import LLMConfig, OllamaNativeClient

            self._llm_client = OllamaNativeClient()
            logger.info("Connected to GRID LLM service")
        except ImportError as e:
            logger.warning(f"GRID LLM not available: {e}")

    def _load_embeddings(self) -> None:
        try:
            from grid.services.embeddings.embedding_client import OllamaEmbeddingClient

            self._embedding_client = OllamaEmbeddingClient()
            logger.info("Connected to GRID Embedding service")
        except ImportError as e:
            logger.warning(f"GRID Embeddings not available: {e}")

    async def generate(self, request: IntelligenceRequest) -> IntelligenceResponse:
        if not self._llm_client:
            self._load_llm()
        if not self._llm_client:
            return await GhostIntelligence().generate(request)

        try:
            result = await self._llm_client.generate(
                prompt=request.prompt, temperature=request.temperature, max_tokens=request.max_tokens
            )
            return IntelligenceResponse(
                content=result.text, model_used=request.model, tokens_used=result.tokens_used, success=True
            )
        except Exception as e:
            return IntelligenceResponse(content="", model_used=request.model, success=False, error=str(e))

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not self._embedding_client:
            self._load_embeddings()
        if not self._embedding_client:
            return await GhostIntelligence().embed(texts)

        return await self._embedding_client.embed_batch(texts)


class GridOrchestrationAdapter:
    """Adapter connecting to grid.agentic for Orchestration operations."""

    def __init__(self):
        self._event_bus = None
        self._skill_registry = None

    def _load_event_bus(self) -> None:
        try:
            from grid.agentic.event_bus import EventBus, get_event_bus

            self._event_bus = get_event_bus()
            logger.info("Connected to GRID EventBus")
        except ImportError as e:
            logger.warning(f"GRID EventBus not available: {e}")

    def _load_skills(self) -> None:
        try:
            from grid.skills.registry import default_registry

            self._skill_registry = default_registry
            logger.info("Connected to GRID SkillRegistry")
        except ImportError as e:
            logger.warning(f"GRID Skills not available: {e}")

    async def dispatch(self, command: OrchestrationCommand) -> OrchestrationResult:
        # Try skill execution first
        if not self._skill_registry:
            self._load_skills()

        if self._skill_registry and command.action in self._skill_registry:
            try:
                result = await self._skill_registry.execute(command.action, command.payload)
                return OrchestrationResult(action=command.action, status="success", data=result)
            except Exception as e:
                return OrchestrationResult(action=command.action, status="failed", error=str(e))

        # Fallback to event emission
        if not self._event_bus:
            self._load_event_bus()

        if self._event_bus:
            await self._event_bus.emit(command.action, command.payload)
            return OrchestrationResult(action=command.action, status="dispatched")

        return await GhostOrchestration().dispatch(command)

    async def subscribe(self, event_type: str, handler: Callable) -> None:
        if not self._event_bus:
            self._load_event_bus()

        if self._event_bus:
            self._event_bus.subscribe(event_type, handler)
        else:
            await GhostOrchestration().subscribe(event_type, handler)


# =============================================================================
# Domain Facade (Main Entry Point)
# =============================================================================


class DomainGateway:
    """
    Main facade for accessing all domain bounded contexts.

    Usage:
        gateway = DomainGateway()

        # Intelligence
        response = await gateway.intelligence.generate(IntelligenceRequest(prompt="Hello"))

        # Orchestration
        result = await gateway.orchestration.dispatch(OrchestrationCommand(action="process", payload={}))
    """

    _instance: DomainGateway | None = None

    def __new__(cls) -> DomainGateway:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._intelligence: IntelligencePort | None = None
        self._orchestration: OrchestrationPort | None = None
        self._persistence: PersistencePort | None = None
        self._observation: ObservationPort | None = None

        self._hooks: dict[str, list[Callable]] = {}
        self._initialized = True

        logger.info("DomainGateway initialized")

    # --- Hook System ---
    def register_hook(self, event: str, callback: Callable) -> None:
        """Register a debug/observation hook."""
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(callback)

    def _trigger_hook(self, event: str, *args, **kwargs) -> None:
        """Trigger registered hooks."""
        for callback in self._hooks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Hook error ({event}): {e}")

    # --- Domain Accessors ---
    @property
    def intelligence(self) -> IntelligencePort:
        """Get Intelligence domain port."""
        if self._intelligence is None:
            try:
                self._intelligence = GridIntelligenceAdapter()
                self._trigger_hook("domain_connected", DomainCategory.INTELLIGENCE)
            except Exception:
                self._intelligence = GhostIntelligence()
                self._trigger_hook("domain_fallback", DomainCategory.INTELLIGENCE)
        assert self._intelligence is not None
        return self._intelligence

    @property
    def orchestration(self) -> OrchestrationPort:
        """Get Orchestration domain port."""
        if self._orchestration is None:
            try:
                self._orchestration = GridOrchestrationAdapter()
                self._trigger_hook("domain_connected", DomainCategory.ORCHESTRATION)
            except Exception:
                self._orchestration = GhostOrchestration()
                self._trigger_hook("domain_fallback", DomainCategory.ORCHESTRATION)
        assert self._orchestration is not None
        return self._orchestration

    @property
    def persistence(self) -> PersistencePort:
        """Get Persistence domain port."""
        if self._persistence is None:
            # TODO: Implement GridPersistenceAdapter when grid.database is available
            self._persistence = GhostPersistence()
            self._trigger_hook("domain_fallback", DomainCategory.PERSISTENCE)
        assert self._persistence is not None
        return self._persistence

    @property
    def observation(self) -> ObservationPort:
        """Get Observation domain port."""
        if self._observation is None:
            # TODO: Implement GridObservationAdapter when grid.tracing is stable
            self._observation = GhostObservation()
            self._trigger_hook("domain_fallback", DomainCategory.OBSERVATION)
        assert self._observation is not None
        return self._observation

    # --- Connection Status ---
    def get_status(self) -> dict[str, str]:
        """Get connection status for all domains."""
        return {
            "intelligence": "ghost" if isinstance(self._intelligence, GhostIntelligence) else "connected",
            "orchestration": "ghost" if isinstance(self._orchestration, GhostOrchestration) else "connected",
            "persistence": "ghost" if isinstance(self._persistence, GhostPersistence) else "connected",
            "observation": "ghost" if isinstance(self._observation, GhostObservation) else "connected",
        }


# =============================================================================
# Module-Level Convenience Functions
# =============================================================================

_gateway: DomainGateway | None = None


def get_gateway() -> DomainGateway:
    """Get the singleton DomainGateway instance."""
    global _gateway
    if _gateway is None:
        _gateway = DomainGateway()
    return _gateway


def get_intelligence() -> IntelligencePort:
    """Shortcut to get Intelligence domain port."""
    return get_gateway().intelligence


def get_orchestration() -> OrchestrationPort:
    """Shortcut to get Orchestration domain port."""
    return get_gateway().orchestration


# =============================================================================
# Demo / Testing
# =============================================================================

if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s | %(name)s | %(message)s")

    async def demo() -> None:
        gateway = get_gateway()

        # Register debug hook
        gateway.register_hook("domain_connected", lambda cat: print(f"✓ Connected: {cat.name}"))
        gateway.register_hook("domain_fallback", lambda cat: print(f"⚠ Fallback: {cat.name}"))

        # Test Intelligence
        print("\n--- Intelligence Domain ---")
        response = await gateway.intelligence.generate(IntelligenceRequest(prompt="What is the capital of France?"))
        print(f"Response: {response.content[:100]}...")

        # Test Orchestration
        print("\n--- Orchestration Domain ---")
        result = await gateway.orchestration.dispatch(
            OrchestrationCommand(action="test.event", payload={"key": "value"})
        )
        print(f"Result: {result.status}")

        # Status
        print("\n--- Gateway Status ---")
        print(gateway.get_status())

    asyncio.run(demo())
