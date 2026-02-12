# GRID Workspace - AI Agent Guide

Guide for AI agents working in this multi-repository workspace. Python 3.13.11 enforced.

## Build/Lint/Test Commands

### GRID Framework (Python/FastAPI) - `E:\grid`
```bash
# Setup
uv venv --python 3.13 --clear && .\.venv\Scripts\Activate.ps1 && uv sync --group dev --group test

# Tests
pytest                                    # All tests
pytest tests/unit/test_specific.py        # Single test file
pytest tests/unit/test_file.py::test_name # Single test function
pytest -k "test_name"                     # Tests matching pattern
pytest -m "unit"                          # Only unit tests
pytest -m "not slow"                      # Exclude slow tests
pytest --timeout=300                      # With timeout

# Linting/Formatting
ruff check .                              # Lint
ruff check --fix .                        # Auto-fix
black .                                   # Format
mypy src/                                 # Type check

# Run services
python -m application.mothership.main     # API server
python -m tools.rag.cli query "question"  # RAG query
```

### Apps Frontend (React/TypeScript) - `E:\projects\Apps`
```bash
npm install && npm run dev                # Dev server (port 3000)
npm run test                              # Run tests
npm run test -- --filter="test name"      # Single test
npm run build                             # Production build
```

### Apps Backend (FastAPI) - `E:\projects\Apps\backend`
```bash
pip install -r requirements.txt
uvicorn main:app --reload                 # Dev server (port 8000)
alembic upgrade head                      # Apply migrations
```

## Code Style Guidelines

### Python Style
- **Line length**: 120 characters
- **Type hints**: Required for all functions/methods
- **Models**: Pydantic for API, dataclasses for internal
- **Strings**: f-strings for formatting
- **Paths**: Use `pathlib.Path`, not string concatenation

### Import Organization
```python
# 1. Standard library
import asyncio
from typing import Optional

# 2. Third-party
import httpx
from fastapi import FastAPI, Depends
from pydantic import BaseModel

# 3. Local (absolute imports)
from src.grid.core import SomeClass
from application.services import service_function
```

### Naming Conventions
- **Functions/variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: `_leading_underscore`
- **Files**: `snake_case.py`

### Error Handling
```python
# Custom exception hierarchy
class GridError(Exception):
    """Base exception."""
    pass

class ProcessingError(GridError):
    """Processing errors."""
    pass

# Handle with context
try:
    result = await process_data(data)
except ProcessingError as e:
    logger.error(f"Processing failed: {e}")
    raise HTTPException(status_code=400, detail=str(e))
```

### Function Signatures
```python
def process_data(
    input_data: DataModel,
    config: Optional[ConfigModel] = None,
    timeout: int = 30
) -> ResultModel:
    """Process input data.
    
    Args:
        input_data: The data to process
        config: Optional configuration
        timeout: Timeout in seconds
        
    Returns:
        Processed results
        
    Raises:
        ProcessingError: When processing fails
    """
```

### Testing Patterns
```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_feature():
    """Test description."""
    # Arrange
    mock_service = AsyncMock()
    mock_service.method.return_value = expected
    
    # Act
    result = await function_under_test(mock_service)
    
    # Assert
    assert result == expected
    mock_service.method.assert_called_once()
```

### Test Markers
```python
@pytest.mark.unit          # Fast, isolated
@pytest.mark.integration   # Cross-module
@pytest.mark.slow          # > 1 second
@pytest.mark.asyncio       # Async test
@pytest.mark.database      # Requires DB
```

## Architecture Rules

### Local-First AI
- Use local Ollama models, NOT external APIs (OpenAI, Anthropic)
- RAG: ChromaDB in `.rag_db/`, embeddings via `nomic-embed-text-v2-moe`
- LLM: `ministral` or local models via Ollama

### Async/Await
- Use `async def` for all I/O operations
- Use `asyncio.create_subprocess_exec()`, NOT `subprocess.run()`
- Use `asyncio.gather()` for parallel operations

### Service Layer Pattern
```python
# Services in backend/services/ or grid/src/services/
class UserService:
    def __init__(self, db: Database):
        self.db = db
    
    async def get_user(self, user_id: int) -> Optional[User]:
        return await self.db.get_user(user_id)
```

### FastAPI Endpoints
```python
router = APIRouter(prefix="/api/v1/resource")

@router.post("/", response_model=ResponseModel)
async def create_resource(
    request: RequestModel,
    service: Service = Depends(get_service)
) -> ResponseModel:
    return await service.create(request)
```

## Key Constraints from Cursor/Copilot Rules

### From `.cursorrules`
- Follow layered architecture: core -> API -> database -> CLI -> services
- Use dependency injection patterns
- Reference existing patterns before creating new ones
- Check cognitive layer (`light_of_the_seven/cognitive_layer/`) for decision support
- Maintain >= 80% test coverage

### From `.github/copilot-instructions.md`
- Run-based immutable snapshots: `Apps/data/harness/runs/{run_id}/`
- Service layer pattern: import functions from `services/{name}_service.py`
- Pydantic v2 for all input/output validation
- Event-driven patterns in cognitive layer

## Prohibited Practices

1. No external AI APIs without explicit request
2. No wildcard imports
3. No untyped functions
4. No hardcoded secrets (use env vars)
5. No direct DB access (use repository pattern)
6. No blocking calls in async contexts

## Module Organization

- `grid/src/grid/` - Core intelligence layer
- `grid/src/application/` - FastAPI application
- `grid/src/cognitive/` - Cognitive patterns, vision layer
- `grid/src/tools/` - RAG system, utilities
- `Apps/backend/routers/` - API endpoints
- `Apps/backend/services/` - Business logic
