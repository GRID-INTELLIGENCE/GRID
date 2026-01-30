# Testing Guide

## Overview

This document describes how to run tests locally, understand test organization, add new tests, and troubleshoot test issues.

## Running Tests Locally

### Quick Start

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest -m unit          # Fast unit tests
pytest -m integration   # Integration tests
pytest -m e2e          # End-to-end tests
pytest -m fast         # Fast tests (<1s)
```

### Using Makefile

```bash
make test          # Run all tests
make test-cov      # Run tests with coverage
```

### Using Test Scripts

```bash
# Run tests with detailed reporting
python scripts/run_tests_local.py

# Run only fast tests
python scripts/run_tests_local.py --fast-only

# Collect test results for analysis
python scripts/test_collect_results.py

# Generate test context report
python scripts/test_context_report.py
```

## Test Organization

Tests are organized in the `tests/` directory:

```
tests/
├── unit/              # Unit tests (fast, isolated)
├── integration/       # Integration tests (may require services)
├── e2e/               # End-to-end tests (full system)
└── conftest.py        # Shared fixtures
```

### Test Markers

Tests are categorized using pytest markers:

- `@pytest.mark.unit` - Fast unit tests (<1s)
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.slow` - Tests taking >1 second
- `@pytest.mark.fast` - Tests taking <1 second
- `@pytest.mark.requires_db` - Tests requiring database
- `@pytest.mark.requires_api` - Tests requiring API server

## Adding New Tests

### 1. Choose the Right Location

- **Unit tests**: `tests/unit/` - Test individual functions/classes
- **Integration tests**: `tests/integration/` - Test component interactions
- **E2E tests**: `tests/e2e/` - Test full workflows

### 2. Use Appropriate Fixtures

Common fixtures available in `conftest.py`:

- `event_bus` - IntegrationPipeline event bus
- `physics_engine` - UBIPhysicsEngine
- `documentation_index` - DocumentationIndex
- `grid_system` - Full GridSystem instance
- `db_session` - Database session
- `client` - FastAPI test client

### 3. Mark Your Tests

```python
import pytest

@pytest.mark.unit
def test_something():
    """Test description."""
    assert True

@pytest.mark.integration
@pytest.mark.requires_db
def test_database_integration(db_session):
    """Test database integration."""
    # Test code
    pass
```

### 4. Follow Naming Conventions

- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

## Test Configuration

### Deterministic Execution

Tests run in deterministic order using:
- Random seed: `0` (fixed for reproducibility)
- Global bucket ordering
- Same order locally and in CI

### Coverage Requirements

- Target coverage: **80%**
- Coverage is enforced in CI
- Run `pytest --cov=src` to check coverage locally

### Test Timeouts

- Default timeout: 300 seconds per test
- Use `@pytest.mark.timeout(60)` for specific timeouts

## CI/CD Behavior

Tests run in CI with the same configuration as locally:

1. **Lint & Format** - Fast checks (fail early)
2. **Type Check** - mypy validation
3. **Tests** - Full test suite with coverage
4. **Security** - Safety and Bandit scans

See [CI_CD.md](CI_CD.md) for more details.

## Troubleshooting

### Tests Fail Locally But Pass in CI

1. Check Python version matches CI (3.10, 3.11, 3.12)
2. Run `python scripts/simulate_ci.py` to match CI environment
3. Ensure dependencies are installed: `pip install -e ".[dev,api,ml]"`

### Flaky Tests

1. Check for timing dependencies
2. Ensure proper test isolation
3. Use fixtures for cleanup
4. Check for shared state between tests

### Slow Tests

1. Identify slow tests: `pytest --durations=10`
2. Mark as `@pytest.mark.slow`
3. Consider optimization or mocking

### Coverage Issues

1. Check coverage report: `pytest --cov=src --cov-report=html`
2. Open `htmlcov/index.html` in browser
3. Add tests for uncovered code
4. Use `# pragma: no cover` for intentionally uncovered code

## Best Practices

1. **Keep tests fast** - Unit tests should run in <1s
2. **Test isolation** - Each test should be independent
3. **Use fixtures** - Don't duplicate setup code
4. **Clear assertions** - Make failures easy to understand
5. **Descriptive names** - Test names should explain what they test
6. **One assertion per test** - Focus each test on one behavior

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [Coverage.py documentation](https://coverage.readthedocs.io/)
- [CI/CD Guide](CI_CD.md)
