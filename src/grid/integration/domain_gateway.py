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
            from grid.services.llm.llm_client import OllamaNativeClient

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
            # Use the client's generate method with available parameters
            generate_fn = getattr(self._llm_client, "generate", None)
            if generate_fn is None:
                return await GhostIntelligence().generate(request)

            result = await generate_fn(prompt=request.prompt)
            # Extract response content - handle different response types
            content = getattr(result, "text", str(result)) if result else ""
            tokens_used = getattr(result, "tokens_used", 0) if result else 0
            return IntelligenceResponse(
                content=content, model_used=request.model, tokens_used=tokens_used, success=True
            )
        except Exception as e:
            return IntelligenceResponse(content="", model_used=request.model, success=False, error=str(e))

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not self._embedding_client:
            self._load_embeddings()
        if not self._embedding_client:
            return await GhostIntelligence().embed(texts)

        # Try different embedding methods - API may vary
        if hasattr(self._embedding_client, "embed_batch"):
            embed_batch_fn = getattr(self._embedding_client, "embed_batch")
            return await embed_batch_fn(texts)
        elif hasattr(self._embedding_client, "embed"):
            embed_fn = getattr(self._embedding_client, "embed")
            results = []
            for text in texts:
                emb = await embed_fn(text)
                results.append(emb)
            return results
        else:
            return await GhostIntelligence().embed(texts)


class GridOrchestrationAdapter:
    """Adapter connecting to grid.agentic for Orchestration operations."""

    def __init__(self):
        self._event_bus = None
        self._skill_registry = None

    def _load_event_bus(self) -> None:
        try:
            from grid.agentic.event_bus import get_event_bus

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

        # Check if skill registry has the action using hasattr pattern
        has_action = False
        if self._skill_registry:
            try:
                # Try __contains__ first (for dict-like registries)
                has_action = command.action in self._skill_registry  # type: ignore[operator]
            except TypeError:
                # Fallback to has_skill method if available
                has_skill_fn = getattr(self._skill_registry, "has_skill", None)
                if has_skill_fn and callable(has_skill_fn):
                    has_action = has_skill_fn(command.action)

        if self._skill_registry and has_action:
            try:
                execute_fn = getattr(self._skill_registry, "execute", None)
                if execute_fn and callable(execute_fn):
                    result = execute_fn(command.action, command.payload)
                    # Handle both sync and async execute methods
                    import asyncio

                    if asyncio.iscoroutine(result):
                        result = await result
                    result_data: dict[str, Any] = result if isinstance(result, dict) else {"result": result}
                    return OrchestrationResult(action=command.action, status="success", data=result_data)
            except Exception as e:
                return OrchestrationResult(action=command.action, status="failed", error=str(e))

        # Fallback to event emission
        if not self._event_bus:
            self._load_event_bus()

        if self._event_bus:
            emit_fn = getattr(self._event_bus, "emit", None)
            if emit_fn and callable(emit_fn):
                import asyncio

                emit_result = emit_fn(command.action, command.payload)
                # Handle both sync and async emit methods
                if asyncio.iscoroutine(emit_result):
                    await emit_result
            return OrchestrationResult(action=command.action, status="dispatched")

        return await GhostOrchestration().dispatch(command)

    async def subscribe(self, event_type: str, handler: Callable) -> None:
        if not self._event_bus:
            self._load_event_bus()

        if self._event_bus:
            subscribe_fn = getattr(self._event_bus, "subscribe", None)
            if subscribe_fn and callable(subscribe_fn):
                subscribe_fn(event_type, handler)
        else:
            await GhostOrchestration().subscribe(event_type, handler)


class GridPersistenceAdapter:
    """Adapter connecting to grid database and storage for Persistence operations."""

    def __init__(self):
        self._redis_client = None
        self._local_cache: dict[str, Any] = {}

    def _load_redis(self) -> None:
        """Attempt to connect to Redis for persistence."""
        try:
            import redis.asyncio as redis

            from grid.security.secrets_loader import get_secret

            redis_url = get_secret("REDIS_URL", required=False, default="redis://localhost:6379")
            if redis_url:
                self._redis_client = redis.from_url(str(redis_url), decode_responses=True)
                logger.info("Connected to Redis for persistence")
        except ImportError:
            logger.debug("Redis not available, using local cache")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")

    async def store(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Store a value with optional TTL in seconds."""
        if self._redis_client is None:
            self._load_redis()

        try:
            if self._redis_client:
                import json

                serialized = json.dumps(value)
                if ttl:
                    await self._redis_client.setex(key, ttl, serialized)
                else:
                    await self._redis_client.set(key, serialized)
                return True
        except Exception as e:
            logger.warning(f"Redis store failed, falling back to local: {e}")

        # Fallback to local cache
        self._local_cache[key] = {"value": value, "ttl": ttl}
        return True

    async def retrieve(self, key: str) -> Any | None:
        """Retrieve a value by key."""
        if self._redis_client is None:
            self._load_redis()

        try:
            if self._redis_client:
                import json

                data = await self._redis_client.get(key)
                if data:
                    return json.loads(data)
                return None
        except Exception as e:
            logger.warning(f"Redis retrieve failed, falling back to local: {e}")

        # Fallback to local cache
        entry = self._local_cache.get(key)
        if entry:
            return entry.get("value")
        return None

    async def delete(self, key: str) -> bool:
        """Delete a value by key."""
        if self._redis_client is None:
            self._load_redis()

        try:
            if self._redis_client:
                result = await self._redis_client.delete(key)
                return result > 0
        except Exception as e:
            logger.warning(f"Redis delete failed, falling back to local: {e}")

        # Fallback to local cache
        return self._local_cache.pop(key, None) is not None


class GridObservationAdapter:
    """Adapter connecting to grid.tracing for Observation operations."""

    def __init__(self):
        self._trace_manager = None
        self._metrics_buffer: list[dict[str, Any]] = []

    def _load_tracing(self) -> None:
        """Attempt to load the tracing system."""
        try:
            from grid.tracing import TraceManager, TraceOrigin, get_trace_manager

            self._trace_manager = get_trace_manager()
            logger.info("Connected to GRID tracing system")
        except ImportError as e:
            logger.warning(f"GRID tracing not available: {e}")

    def trace(self, operation: str, data: dict[str, Any]) -> None:
        """Record a trace for an operation."""
        if self._trace_manager is None:
            self._load_tracing()

        if self._trace_manager:
            try:
                trace = self._trace_manager.create_trace(
                    action_type="observation",
                    action_name=operation,
                    metadata=data,
                )
                logger.debug(f"Trace recorded: {trace.trace_id}")
            except Exception as e:
                logger.warning(f"Trace recording failed: {e}")
        else:
            # Fallback to console
            logger.debug(f"[Observation] {operation}: {data}")

    def metric(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """Record a metric with optional tags."""
        if self._trace_manager is None:
            self._load_tracing()

        metric_data = {"name": name, "value": value, "tags": tags or {}}

        if self._trace_manager:
            try:
                # Store metric in trace metadata
                trace = self._trace_manager.create_trace(
                    action_type="metric",
                    action_name=name,
                    metadata={"value": value, "tags": tags},
                )
                logger.debug(f"Metric recorded: {name}={value}")
            except Exception as e:
                logger.warning(f"Metric recording failed: {e}")
                self._metrics_buffer.append(metric_data)
        else:
            # Fallback to console and buffer
            self._metrics_buffer.append(metric_data)
            logger.debug(f"[Metric] {name}={value} tags={tags}")


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
            try:
                self._persistence = GridPersistenceAdapter()
                self._trigger_hook("domain_connected", DomainCategory.PERSISTENCE)
            except Exception:
                self._persistence = GhostPersistence()
                self._trigger_hook("domain_fallback", DomainCategory.PERSISTENCE)
        assert self._persistence is not None
        return self._persistence

    @property
    def observation(self) -> ObservationPort:
        """Get Observation domain port."""
        if self._observation is None:
            try:
                self._observation = GridObservationAdapter()
                self._trigger_hook("domain_connected", DomainCategory.OBSERVATION)
            except Exception:
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
