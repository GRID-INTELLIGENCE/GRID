# AGENTS.md - Development Guidelines for Coinbase Crypto Agentic System

This file contains essential development guidelines for agentic coding agents working in this repository.

## Build, Lint, and Test Commands

### Environment Setup
```bash
# Create virtual environment (Windows)
uv venv --python 3.13
.venv\Scripts\Activate.ps1

# Install dependencies
uv sync --group dev --group test
```

### Running Tests
```bash
# Run all tests
uv run pytest tests/ -v

# Run all tests with coverage
uv run pytest tests/ -v --cov=coinbase --cov-report=term-missing

# Run a single test file
uv run pytest tests/test_core_modules.py -v

# Run a single test function
uv run pytest tests/test_core_modules.py::test_module_initialization -v

# Run tests with specific markers
uv run pytest tests/ -v -m "unit"
uv run pytest tests/ -v -m "integration"
uv run pytest tests/ -v -m "smoke"
```

### Code Quality
```bash
# Linting
uv run ruff check .

# Auto-fix linting issues
uv run ruff check . --fix

# Formatting
uv run black .

# Type checking
uv run mypy coinbase/

# Run all quality checks
uv run ruff check . && uv run black --check . && uv run mypy coinbase/
```

### Pre-commit Hooks
```bash
# Install pre-commit hooks
pre-commit install

# Run all hooks manually
pre-commit run --all-files
```

## Code Style Guidelines

### Python Version and Dependencies
- **Python**: 3.13 only (no 3.14 features)
- **Line length**: 100 characters
- **Dependencies**: Minimal, only revenue-generating features
- **Async**: Strictly prohibited (no async/await, no asyncio)

### Import Organization
```python
# Standard library imports first
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

# Third-party imports next
import click
import pytest

# Local imports last
from coinbase.app import CoinbaseApp
from coinbase.exceptions import CoinbaseError
```

### Type Hints and Documentation
- **Type hints required** on all functions and methods
- **Docstrings required** on all public functions
- **Private functions** should have docstrings for clarity
- **Return types** must be explicitly specified

```python
def add_crypto_asset(
    self,
    symbol: str,
    name: str,
    asset_type: str,
    current_price: float,
    market_cap: float,
    volume_24h: float,
) -> None:
    """
    Add a crypto asset to the database.
    
    Args:
        symbol: Asset symbol (e.g., BTC)
        name: Asset name (e.g., Bitcoin)
        asset_type: Asset type (e.g., bitcoin)
        current_price: Current market price
        market_cap: Market capitalization
        volume_24h: 24-hour trading volume
    """
    pass
```

### Naming Conventions
- **Classes**: PascalCase (e.g., `CoinbaseApp`, `CryptoSkill`)
- **Functions/Methods**: snake_case (e.g., `add_crypto_asset`, `verify_price`)
- **Variables**: snake_case (e.g., `user_id`, `asset_symbol`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_RETRY_ATTEMPTS`)
- **Private members**: Prefix with underscore (e.g., `_register_core_skills`)

### Error Handling
- Use the comprehensive exception hierarchy from `coinbase.exceptions`
- Include error codes for categorization
- Provide context for debugging
- Use structured error responses

```python
try:
    result = self.database.add_position(user_id, asset_symbol, quantity)
except ValidationError as e:
    logger.error(f"Validation failed: {e.code.name}", extra={"error_code": e.code.value})
    raise
except CoinbaseError as e:
    logger.error(f"Database operation failed: {e.code.name}")
    raise
```

### Security and Privacy
- **User IDs**: Always hash with SHA-256 before storage
- **Sensitive data**: Mask in logs (e.g., `user_id: "hashed_123"`)
- **SQL queries**: Use parameterized queries only
- **Audit logging**: Required for all portfolio operations

### Architecture Layers
Follow the 7-layer architecture:
1. **User Layer**: CLI, entry points
2. **Orchestration Layer**: AgenticSystem, EventBus, AgentExecutor, CognitiveEngine
3. **Execution Layer**: RuntimeBehaviorTracer, RecoveryEngine, ErrorClassifier
4. **Learning Layer**: SkillGenerator, LearningCoordinator, Skill Store
5. **Analysis Layer**: CryptoSkillsRegistry, Skills
6. **Scoring Layer**: VersionScorer, VersionMetrics, Version History
7. **Output Layer**: Performance Metrics, Execution Results, Generated Skills

### Component Boundaries
- **Core modules**: 9 fixed modules (tracer.py, events.py, error_recovery.py, etc.)
- **Skills**: 8 fixed skills (data normalization, validation, trend analysis, etc.)
- **No new modules** without explicit approval
- **No new skills** without explicit approval

### Testing Requirements
- **100% test coverage** required
- **Synchronous tests only** (no async)
- **Test files**: `test_*.py` in `tests/` directory
- **Test classes**: `Test*` prefix
- **Test functions**: `test_*` prefix
- **Coverage threshold**: 75% minimum

### Logging Guidelines
- Use structured logging with JSON format
- Include correlation IDs for request tracking
- Mask sensitive data in logs
- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR)

```python
from coinbase.logging_config import get_logger, LogContext

logger = get_logger(__name__)

with LogContext(correlation_id="request-123"):
    logger.info("Processing portfolio analysis", extra={"user_id": "hashed_id"})
```

### Database Integration
- Use Databricks-backed database layer
- Follow Unity Catalog naming conventions
- Use managed tables for portfolio data
- Implement data quality checks
- Respect portfolio data classification (CRITICAL)

### Performance Considerations
- **Minimal dependencies**: Only revenue-generating features
- **Efficient queries**: Use parameterized queries
- **Caching**: Implement skill caching where appropriate
- **Resource limits**: Respect rate limits for external APIs

### Development Workflow
1. **Create feature branch**: `feature/description`
2. **Implement changes**: Follow all style guidelines
3. **Add tests**: Ensure 100% coverage for new code
4. **Run quality checks**: `ruff`, `black`, `mypy`
5. **Run tests**: `pytest` with coverage
6. **Commit changes**: Atomic commits with descriptive messages
7. **Create pull request**: For review and merge

### Emergency Override Process
In case of critical issues requiring rule violations:
1. Document the emergency situation
2. Explain why the rule must be broken
3. Get explicit user approval
4. Implement minimal change
5. Document the exception
6. Plan to restore compliance

## Prohibited Practices
- ❌ Adding async/await support
- ❌ Changing to Python 3.14
- ❌ Adding new core modules without approval
- ❌ Removing existing modules
- ❌ Adding new skills without approval
- ❌ Changing architecture layers
- ❌ Adding new dependencies
- ❌ Removing existing dependencies
- ❌ Changing test framework
- ❌ Removing tests

## Security Guardrails
- **PortfolioDataSecurity**: User ID hashing, data encryption, access control
- **PortfolioAISafety**: AI access validation, output sanitization
- **PortfolioAuditLogger**: Comprehensive audit logging
- **PortfolioDataPolicy**: Field-level sensitivity classification

## Coinbase-Specific Rules
- **Crypto Scope**: Respect `--crypto` flag for crypto operations
- **Analysis Workflow**: Follow the 6-step analysis process
- **Data Flow**: Follow the 5-step data flow rules
- **Testing Rules**: Synchronous tests with small delays for duration tracking

## CI/CD Pipeline
- **Lint**: Code quality checks with Ruff, Black, and MyPy
- **Test**: Runs test suite on Ubuntu, Windows, and macOS
- **Security**: Bandit security linter, Safety, and pip-audit
- **Benchmark**: Performance benchmarks on main branch pushes
- **Build**: Package building and validation
