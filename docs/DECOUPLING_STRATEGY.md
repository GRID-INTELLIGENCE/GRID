# GRID Decoupling Strategy - Community Guidelines & Patterns

## Overview

This document defines the **decoupling architecture** for GRID, following Domain-Driven Design (DDD) Anti-Corruption Layer (ACL) patterns based on community best practices (2024).

---

## Domain Bounded Contexts

| Domain | Purpose | GRID Modules | Entry Point |
|--------|---------|--------------|-------------|
| **Intelligence** | LLM, embeddings, reasoning | `grid.services.llm`, `grid.services.embeddings`, `grid.knowledge` | `get_intelligence()` |
| **Orchestration** | Events, skills, agentic flow | `grid.agentic`, `grid.skills`, `grid.distribution` | `get_orchestration()` |
| **Persistence** | Data, caching, state | `grid.database`, `grid.io`, `grid.essence` | `get_persistence()` |
| **Observation** | Tracing, monitoring, logging | `grid.tracing`, `grid.logs`, `grid.monitoring` | `get_observation()` |

---

## Decoupling Patterns Applied

### 1. **Facade Pattern** (Single Entry Point)
```python
# ❌ Tight Coupling (Anti-pattern)
from grid.agentic.event_bus import EventBus
from grid.skills.registry import default_registry
from grid.services.llm.llm_client import OllamaNativeClient

bus = EventBus()
registry = default_registry
llm = OllamaNativeClient(...)

# ✅ Loose Coupling (Recommended)
from grid.integration import get_gateway

gateway = get_gateway()
response = await gateway.intelligence.generate(IntelligenceRequest(prompt="..."))
result = await gateway.orchestration.dispatch(OrchestrationCommand(action="..."))
```

### 2. **Adapter Pattern** (Protocol-Based Contracts)
```python
# Define contract (Protocol)
class IntelligencePort(Protocol):
    async def generate(self, request: IntelligenceRequest) -> IntelligenceResponse: ...
    async def embed(self, texts: List[str]) -> List[List[float]]: ...

# Real implementation
class GridIntelligenceAdapter:
    async def generate(self, request): ...  # Connects to grid.services.llm

# Ghost implementation (fallback)
class GhostIntelligence:
    async def generate(self, request): ...  # Returns mock data
```

### 3. **Null Object Pattern** (Ghost Processes)
When a domain is unavailable, the system gracefully degrades to a "ghost" implementation that:
- Logs the operation (observability)
- Returns safe default values
- Never raises ImportError or crashes

```python
# Automatic fallback
gateway = get_gateway()
# If grid.services.llm is not installed, GhostIntelligence is used
response = await gateway.intelligence.generate(request)  # Works either way
```

### 4. **DTO Pattern** (Data Transfer Objects)
Cross-domain communication uses frozen dataclasses to prevent unintended mutations:

```python
@dataclass(frozen=True)
class IntelligenceRequest:
    prompt: str
    model: str = "default"
    temperature: float = 0.7
    max_tokens: int = 512
    context: Dict[str, Any] = field(default_factory=dict)
```

---

## Hook-Based Debugging

Register hooks to observe domain connections and operations:

```python
gateway = get_gateway()

# Debug hook
gateway.register_hook("domain_connected", lambda cat: print(f"✓ Connected: {cat.name}"))
gateway.register_hook("domain_fallback", lambda cat: print(f"⚠ Fallback: {cat.name}"))

# Check status
print(gateway.get_status())
# {'intelligence': 'connected', 'orchestration': 'ghost', ...}
```

---

## Migration Guide

### Before (Tight Coupling)
```python
# agents/personal_agent.py - BEFORE
from grid.agentic.event_bus import EventBus
from grid.skills.engine import SkillCallingEngine

class PersonalAgent:
    def __init__(self, event_bus=None, skill_engine=None):
        self.event_bus = event_bus or EventBus()  # Direct import
        self.skill_engine = skill_engine or SkillCallingEngine()
```

### After (Loose Coupling)
```python
# agents/personal_agent.py - AFTER
from grid.integration import get_gateway, OrchestrationCommand

class PersonalAgent:
    def __init__(self):
        self._gateway = get_gateway()

    async def process_query(self, query: str) -> AgentResponse:
        # Orchestration through gateway (decoupled)
        result = await self._gateway.orchestration.dispatch(
            OrchestrationCommand(action="skill.execute", payload={"query": query})
        )

        # Intelligence through gateway (decoupled)
        response = await self._gateway.intelligence.generate(
            IntelligenceRequest(prompt=query)
        )

        return AgentResponse(text=response.content)
```

---

## Directory Structure

```
e:/grid/src/grid/integration/
├── __init__.py              # Package exports
├── tools_bridge.py          # Original bridge (backward compatible)
└── domain_gateway.py        # NEW: DDD Anti-Corruption Layer
```

---

## Testing Decoupled Code

```python
import pytest
from unittest.mock import AsyncMock
from grid.integration import DomainGateway, IntelligenceRequest

@pytest.fixture
def mock_gateway():
    gateway = DomainGateway()
    gateway._intelligence = AsyncMock()
    gateway._intelligence.generate.return_value = IntelligenceResponse(
        content="Mocked response",
        model_used="test"
    )
    return gateway

async def test_agent_with_mock_gateway(mock_gateway):
    agent = PersonalAgent(gateway=mock_gateway)
    response = await agent.process_query("Test query")
    assert response.text == "Mocked response"
```

---

## Status Codes

| Status | Meaning |
|--------|---------|
| `connected` | Real GRID adapter is active |
| `ghost` | Null object fallback is active |
| `error` | Adapter failed to initialize |

---

## References

1. [Microsoft ACL Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/anti-corruption-layer)
2. [DDD Practitioners - ACL](https://ddd-practitioners.com/anti-corruption-layer/)
3. [Python DDD 2024](https://plainenglish.io/python-ddd)
4. [LSP Coupling Best Practices](file:///e:/LSP_COUPLING_BEST_PRACTICES.md)
