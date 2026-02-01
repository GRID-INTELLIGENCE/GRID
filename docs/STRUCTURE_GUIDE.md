# Grid Project Structure Guide

## Overview

This document outlines the standardized project structure following enterprise-grade patterns from aiu-trace-analyzer, ARES, and other production projects.

## Directory Structure

```
grid/
├── .github/
│   └── workflows/          # CI/CD pipelines
├── docs/
│   ├── source/            # Sphinx documentation source
│   ├── api/               # API documentation
│   ├── guides/            # User and development guides
│   └── Makefile           # Sphinx build configuration
├── src/
│   └── grid/              # Main package
│       ├── core/          # Core business logic and domain models
│       ├── services/      # Service layer components
│       ├── models/        # Data models and schemas
│       ├── api/           # REST API endpoints
│       ├── cli/           # Command-line interfaces
│       ├── plugins/       # Plugin architecture
│       ├── utils/         # Utility functions
│       ├── config.py      # Configuration management
│       ├── exceptions.py  # Custom exceptions
│       ├── logger.py      # Logging setup
│       └── __init__.py
├── tests/
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   ├── e2e/               # End-to-end tests
│   ├── conftest.py        # Pytest fixtures and configuration
│   └── __init__.py
├── config/
│   ├── production.yaml    # Production configuration
│   ├── development.yaml   # Development configuration
│   └── testing.yaml       # Testing configuration
├── scripts/               # Utility scripts
├── .flake8                # Flake8 configuration
├── .pylintrc              # Pylint configuration
├── .pre-commit-config.yaml  # Pre-commit hooks
├── mypy.ini               # Type checking configuration
├── pytest.ini             # Pytest configuration
├── pyproject.toml         # Project metadata and tool configuration
├── Makefile               # Build automation
└── README.md              # Project documentation
```

## Core Modules

### `src/grid/core/`
Contains core business logic:
- Domain models
- Business rules
- Main algorithms
- State management

### `src/grid/services/`
Service implementations:
- Workflow execution
- Security processing
- Event handling
- Data processing pipelines

### `src/grid/models/`
Data models and schemas:
- Pydantic models
- Database models
- Request/response schemas

### `src/grid/api/`
REST API layer:
- Route handlers
- Middleware
- Request/response processors

### `src/grid/cli/`
Command-line interfaces:
- Console commands
- Argument parsing
- User interactions

### `src/grid/plugins/`
Plugin system:
- Plugin interfaces
- Plugin registry
- Plugin loaders

### `src/grid/utils/`
Utility functions:
- Helpers
- Common operations
- Decorators
- Validators

## Testing Structure

### `tests/unit/`
Unit tests for individual components:
- Test one thing well
- Fast execution
- No external dependencies
- Mock external calls

### `tests/integration/`
Integration tests:
- Test component interactions
- May use real services
- Database integration
- API testing

### `tests/e2e/`
End-to-end tests:
- Full workflow testing
- Real environment simulation
- Business scenario validation

## Configuration

Configuration files in `config/`:
- YAML format for environment-specific settings
- Environment variables support
- Secrets management
- Database configuration

## Tool Configuration

### Black (Code Formatting)
```bash
black --line-length 88 src tests
```

### isort (Import Sorting)
```bash
isort --profile black src tests
```

### Flake8 (Linting)
```bash
flake8 src tests
```

### Mypy (Type Checking)
```bash
mypy src
```

### Pytest (Testing)
```bash
pytest tests/
pytest tests/ --cov=src --cov-report=html
```

## Quality Assurance

### Pre-commit Hooks
```bash
pre-commit install
pre-commit run --all-files
```

### GitHub Actions
- `testing.yml`: Run tests on pull requests
- `linting.yml`: Check code quality
- `docs-publish.yml`: Build and publish documentation

## Development Workflow

1. **Setup**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -e ".[dev]"
   pre-commit install
   ```

2. **Development**
   ```bash
   # Format code
   black src tests
   isort src tests

   # Check quality
   flake8 src
   mypy src

   # Run tests
   pytest tests/
   ```

3. **Before Commit**
   ```bash
   pre-commit run --all-files
   ```

## Best Practices

- Use type hints throughout
- Write docstrings for public APIs
- Keep modules focused and single-responsibility
- Use dependency injection
- Mock external services in tests
- Maintain >80% test coverage
- Document architecture decisions
- Follow naming conventions

## References

- [aiu-trace-analyzer](../aiu-trace-analyzer/)
- [ARES](../ares/)
- [OIC Agentic AI Tutorials](../oic-i-agentic-ai-tutorials/)
