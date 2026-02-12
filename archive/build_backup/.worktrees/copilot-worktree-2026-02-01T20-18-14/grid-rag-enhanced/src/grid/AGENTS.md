# Core Layer Agent Guidelines

This document provides agent behavior guidelines specific to the GRID core layer (`src/grid/`).

## Core Layer Principles

### Layer Isolation
- **No dependencies on upper layers**: Core layer must not import from `application/`, `tools/`, or API layers
- **Stateless design**: Core components should be stateless when possible
- **Pure functions**: Prefer pure functions over stateful classes
- **Interface-based**: Define interfaces, not implementations

### Module Organization
- `grid/core/` - Core intelligence (essence, patterns, awareness, evolution, interfaces)
- `grid/knowledge/` - Knowledge graph and multi-model orchestration
- `grid/skills/` - Skill registry and execution
- `grid/services/` - Service implementations (can depend on core)
- `grid/security/` - Security and secrets management
- `grid/organization/` - Organization and toggle management

## Core Layer Patterns

### Essence Pattern
- Core entities should define their essence (fundamental properties)
- Use Pydantic models for essence definitions
- Maintain immutability where possible

### Pattern Recognition
- Use 9 cognition patterns in core logic:
  - Flow & Motion - Data streams
  - Spatial Relationships - Architecture
  - Natural Rhythms - Concurrency
  - Color & Light - Observability
  - Repetition & Habit - Standardization
  - Deviation & Surprise - Error handling
  - Cause & Effect - Event-driven
  - Temporal Patterns - State history
  - Combination Patterns - Integration

### Knowledge Graph Integration
- Use `grid/knowledge/` for knowledge graph operations
- Maintain traceability with `event_id`, `chunk_id`, `doc_id`
- Use multi-model orchestrator for complex queries

### Skills Registry
- Register skills in `grid/skills/`
- Follow skill interface patterns
- Maintain skill metadata

## Implementation Guidelines

### Type Safety
- All functions must have type hints
- Use `Optional[T]` for nullable types
- Prefer Pydantic models over dicts
- Use type checking via mypy

### Error Handling
- Use project's exception hierarchy from `grid.core.exceptions`
- Provide clear, actionable error messages
- Log errors with context
- Fail fast for configuration errors

### Testing
- Unit tests for all core logic
- Mock external dependencies
- Test edge cases
- Maintain ≥80% coverage

## Dependencies

### Allowed
- Standard library
- Pydantic v2
- Type hints (typing, typing_extensions)
- Local utilities from `grid/` itself

### Prohibited
- FastAPI (API layer concern)
- Database ORMs (database layer concern)
- Application-specific code
- External API clients

## When Working in Core Layer

1. **Check Layer Boundaries**: Ensure no imports from upper layers
2. **Maintain Statelessness**: Prefer stateless functions/classes
3. **Use Patterns**: Apply 9 cognition patterns where relevant
4. **Test Thoroughly**: Core layer is critical - test extensively
5. **Document Interfaces**: Clear interfaces for upper layers

## Examples

### Correct (Core Layer)
```python
from typing import Optional
from pydantic import BaseModel

class CoreEntity(BaseModel):
    """Core entity definition."""
    id: str
    essence: dict

def process_entity(entity: CoreEntity) -> Optional[CoreEntity]:
    """Process entity (stateless)."""
    # Implementation
    pass
```

### Incorrect (Violates Layer Boundaries)
```python
from fastapi import APIRouter  # ❌ API layer import
from application.mothership import Service  # ❌ Application layer import
```

## Notes

- Core layer is the foundation - keep it clean and well-tested
- No business logic in core - that belongs in application layer
- Focus on reusable, generic patterns
- Maintain backward compatibility
