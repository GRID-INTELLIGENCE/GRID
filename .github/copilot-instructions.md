# AI Coding Agent Instructions

## Architecture Overview

This is a **multi-repository intelligence platform** with the following core subsystems:

- **`E:\grid`** - Cognitive framework with RAG & observability (Python, FastAPI) - PRIMARY
- **`E:\Coinbase`** - Crypto-focused application with GRID integration
- **`E:\analysis_outputs`** - Shared analysis artifacts repository

## Critical Architectural Patterns

### 1. GRID Framework Structure (`E:\grid`)

**Module Organization:**
- `src/grid/` - Core intelligence layer (skills, knowledge, security)
- `src/application/` - FastAPI application (mothership)
- `src/cognitive/` - Cognitive patterns and vision layer
- `src/tools/` - RAG system and utilities

### 2. Service Layer Pattern
Services are located in `src/application/mothership/services/`:

```python
# Service pattern
class ServiceName:
    def __init__(self, dependencies):
        self.deps = dependencies
    
    async def operation(self, inputs) -> OutputType:
        """Core business logic"""
        pass
```

Import pattern: `from application.mothership.services.{name} import {function_name}`

### 3. Cognitive Patterns & Event System
Located in `grid/src/cognitive/`:

**Event-Driven Architecture:**
```python
from grid.events import EventBus, Event, EventPriority

event = Event(
    type="cognitive:pattern_detected",
    data={"pattern": "analysis_complete"},
    source="rag_system",
    priority=EventPriority.NORMAL
)

bus = EventBus()
bus.emit(event)
```

### 4. RAG System
Local-first RAG with ChromaDB and Ollama:

```bash
# Query RAG system
python -m tools.rag.cli query "your question"

# Index documents
python -m tools.rag.cli index <path>
```

Key components:
- Vector store: ChromaDB in `.rag_db/`
- Embeddings: `nomic-embed-text-v2-moe` via Ollama
- LLM: `ministral` or local models

## Developer Workflows

### GRID Framework
```bash
cd E:\grid
uv venv --python 3.13 --clear
.\.venv\Scripts\Activate.ps1
uv sync --group dev --group test

# Run API server
python -m application.mothership.main

# Run tests
pytest tests/ -v
pytest tests/unit/test_specific.py  # Single file
pytest -k "test_name"               # By pattern
```

### Testing & Validation
```bash
# Python tests (pytest)
cd E:\grid && python -m pytest tests/ -v

# Linting
ruff check . && black . && mypy src/
```

## Code Style Conventions

### Python Style
- **Python Version**: 3.13.11 (enforced via `.python-version`)
- **Type Hints**: Required for all functions
- **Line Length**: 120 characters
- **Formatting**: black + ruff

### Async/Await Pattern
- Use `async def` for all I/O operations
- Use `asyncio.create_subprocess_exec()`, NOT `subprocess.run()` in async code
- Use `asyncio.gather()` for parallel operations

### Pydantic Schema Validation
All inputs/outputs validated via Pydantic v2:

```python
from pydantic import BaseModel

class RequestModel(BaseModel):
    name: str
    value: int
    optional_field: str | None = None
```

### Error Handling Pattern
```python
from fastapi import HTTPException

# Use custom exceptions
class GridError(Exception):
    """Base exception."""
    pass

# Handle with context
try:
    result = await operation()
except GridError as e:
    logger.error(f"Operation failed: {e}")
    raise HTTPException(status_code=400, detail=str(e))
```

## Local-First AI Integration

**CRITICAL**: Use local Ollama models, NOT external APIs unless explicitly requested.

```python
# Ollama integration (local models)
from ollama import Client

client = Client()
response = client.generate(model="ministral", prompt=prompt)
```

## Environment Setup

### Critical Env Vars
- `DATABASE_URL` - PostgreSQL connection (required, no defaults)
- `REDIS_URL` - Redis connection for Celery

### Python Path
Ensure `E:\grid\src` is in PYTHONPATH when running tests or scripts.

## Prohibited Practices

1. **No External APIs**: Don't use OpenAI, Anthropic, or other cloud APIs unless explicitly requested
2. **No Breaking Changes**: Don't remove functionality without approval
3. **No Untyped Code**: All functions must have type hints
4. **No Hardcoded Secrets**: Use environment variables
5. **No Direct Database Access**: Use repository pattern
6. **No Blocking Calls in Async**: Use async alternatives

## Common Pitfalls

1. **Path handling**: Use `pathlib.Path`, not string concatenation
2. **Async context**: Use `asyncio.create_subprocess_exec()`, not `subprocess.run()`
3. **Exception handling**: Use specific exceptions, not bare `except:`
4. **Type hints**: All functions need return type annotations

## Code Location Map

| Task | Location | Key File |
|------|----------|----------|
| Add API endpoint | `src/application/mothership/routers/` | Create or extend router |
| Add service logic | `src/application/mothership/services/` | Create service module |
| Add skill | `src/grid/skills/` | Follow existing patterns |
| RAG operations | `src/tools/rag/` | cli.py for commands |
| Security features | `src/grid/security/` | path_validator, secrets |
